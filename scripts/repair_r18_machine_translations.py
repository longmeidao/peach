#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用已保存的 r18.dev 日文原文替换早期自动落库的英文回退值。

只处理归属仍为 ``auto:r18dev`` 的 ``catalog_title`` / ``series``，并要求当前值与
同一份原始快照里的英文值完全一致，且目标确实含日文。r18.dev 的机翻标记会漏标，
所以它只进入审计记录，不作为是否修复的门槛。用户填写、人工复核、快照缺失、番号
不一致或英文值已被改过的字段都只记入审计 CSV，不写 ledger。默认 dry-run；真实写入
必须同时给 ``--apply --backup``。
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR, SOURCES_DIR
from peach.field_owners import auto_owner, owner_of, write_owned_fields
from peach.review_csv import write_rows
from peach.scripting import add_ledger_write_args, counts_of, open_for_write, verify_after_write


SOURCE_OWNER = auto_owner("r18dev")
FIELDS = (
    "asset_id", "code", "field", "current", "target", "machine_translation", "owner", "snapshot",
    "action", "reason",
)


def _key(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def _contains_japanese(value: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", value))


def _snapshot(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _japanese(payload: dict[str, object], field: str) -> str:
    combined = payload.get("combined")
    if isinstance(combined, dict):
        key = "title_ja" if field == "catalog_title" else "series_name_ja"
        value = _text(combined.get(key))
        if value:
            return value
    key = "title" if field == "catalog_title" else "series"
    for translation in payload.get("translations") or []:
        if (isinstance(translation, dict)
                and str(translation.get("language") or "").lower().startswith("ja")):
            return _text(translation.get(key))
    return ""


def _english_machine_translation(payload: dict[str, object], field: str) -> tuple[str, bool]:
    combined = payload.get("combined")
    if not isinstance(combined, dict):
        return "", False
    value_key = "title_en" if field == "catalog_title" else "series_name_en"
    flag_key = value_key + "_is_machine_translation"
    return _text(combined.get(value_key)), combined.get(flag_key) is True


def _snapshot_code(payload: dict[str, object]) -> str:
    combined = payload.get("combined")
    if isinstance(combined, dict):
        value = combined.get("dvd_id")
        if value:
            return _key(value)
    return _key(payload.get("id"))


def snapshot_index(root: Path) -> dict[str, Path]:
    """把一层快照目录按番号索引；同番号多份时拒绝猜哪一份才是证据。"""
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in root.glob("*-r18dev.json"):
        grouped[_key(path.name.removesuffix("-r18dev.json"))].append(path)
    return {key: paths[0] for key, paths in grouped.items() if key and len(paths) == 1}


def collect(connection: sqlite3.Connection, snapshots: Path) -> list[dict[str, object]]:
    connection.row_factory = sqlite3.Row
    indexed = snapshot_index(snapshots)
    rows: list[dict[str, object]] = []
    assets = connection.execute(
        "SELECT id,code,catalog_title,series,field_owners FROM asset "
        "WHERE json_extract(COALESCE(field_owners,'{}'),'$.catalog_title')=? "
        "OR json_extract(COALESCE(field_owners,'{}'),'$.series')=? ORDER BY id",
        (SOURCE_OWNER, SOURCE_OWNER),
    )
    for asset in assets:
        code = str(asset["code"] or "").strip()
        code_key = _key(code)
        path = indexed.get(code_key)
        payload = _snapshot(path) if path else None
        for field in ("catalog_title", "series"):
            owner = owner_of(asset["field_owners"], field)
            if owner != SOURCE_OWNER:
                continue
            current = _text(asset[field])
            row: dict[str, object] = {
                "asset_id": int(asset["id"]), "code": code, "field": field,
                "current": current, "target": "", "machine_translation": "", "owner": owner,
                "snapshot": str(path.resolve()) if path else "", "action": "skip",
                "reason": "",
            }
            if not code_key:
                row["reason"] = "missing-code"
            elif not path:
                row["reason"] = "missing-unique-snapshot"
            elif payload is None:
                row["reason"] = "invalid-snapshot"
            elif _snapshot_code(payload) != code_key:
                row["reason"] = "snapshot-code-mismatch"
            else:
                english, machine = _english_machine_translation(payload, field)
                target = _japanese(payload, field)
                row["target"] = target
                row["machine_translation"] = "yes" if machine else "no"
                if not english or current != english:
                    row["reason"] = "current-no-longer-matches-snapshot-english"
                elif not target:
                    row["reason"] = "missing-japanese"
                elif not _contains_japanese(target):
                    row["reason"] = "target-has-no-japanese-script"
                elif target == current:
                    row["reason"] = "already-japanese"
                else:
                    row["action"] = "replace"
                    row["reason"] = ("verified-r18dev-japanese-machine" if machine
                                     else "verified-r18dev-japanese")
            rows.append(row)
    return rows


def apply_rows(connection: sqlite3.Connection, rows: list[dict[str, object]]) -> dict[str, int]:
    by_asset: dict[int, dict[str, object]] = defaultdict(dict)
    for row in rows:
        if row["action"] == "replace":
            by_asset[int(row["asset_id"])][str(row["field"])] = row["target"]
    repaired_fields = 0
    repaired_assets = 0
    for asset_id, values in by_asset.items():
        result = write_owned_fields(connection, [asset_id], values, SOURCE_OWNER)
        repaired_fields += len(result.written)
        repaired_assets += bool(result.written)
    return {"assets": repaired_assets, "fields": repaired_fields}


EXTRA_COUNTS = {
    "asset_tag": "SELECT count(*) FROM asset_tag",
    "r18_machine_fields": "SELECT count(*) FROM asset "
    "WHERE json_extract(COALESCE(field_owners,'{}'),'$.catalog_title')='auto:r18dev' "
    "OR json_extract(COALESCE(field_owners,'{}'),'$.series')='auto:r18dev'",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="修复 r18.dev 早期自动落库的英文回退值")
    add_ledger_write_args(parser)
    parser.add_argument(
        "--snapshots", type=Path,
        default=SOURCES_DIR / "library-metadata",
        help="scrape_codes.py 保存的 r18.dev 原始快照目录",
    )
    parser.add_argument(
        "--audit-csv", type=Path,
        default=GENERATED_DIR / "r18-machine-translation-repair.csv",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    connection = open_for_write(args)
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        rows = collect(connection, args.snapshots)
        write_rows(args.audit_csv, FIELDS, rows, atomic=True, fill_missing=True)
        distribution = Counter(str(row["action"]) for row in rows)
        reasons = Counter(str(row["reason"]) for row in rows if row["action"] != "replace")
        print(f"已审计 {len(rows)} 个 r18dev 字段；审计 CSV：{args.audit_csv}")
        print("  动作分布：", dict(distribution))
        if reasons:
            print("  跳过原因：", dict(reasons))
        if not args.apply:
            print("  未写 ledger（加 --apply --backup 才写）")
            return 0

        print(f"  已备份到 {args.backup}")
        before = counts_of(connection, EXTRA_COUNTS)
        with connection:
            changed = apply_rows(connection, rows)
        after = counts_of(connection, EXTRA_COUNTS)
        integrity, foreign_keys = verify_after_write(connection)
        print("  写入结果：", changed)
        for key in before:
            print(f"    {key}: {before[key]} -> {after[key]}")
        print(f"  integrity_check={integrity}；foreign_key_check={foreign_keys}")
        return 1 if integrity != "ok" or foreign_keys else 0
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
