#!/usr/bin/env python3
"""FC2 作品账本里已有的演员，与 fc2cmadb 那一栏对不上的，列成一张复核清单。

FC2 的演员栏在资料链上首选 fc2cmadb（`metadata_policy.FIELD_SOURCE_PRIORITY`），但社区来源
只补空、不替换现值（ADR-0033），所以账本里由 javdb 填上的称呼不会被自动换掉：
`FC2-PPV-1449453` 账本是 `Chisa`、fc2cmadb 是 `大村阿美香`；`FC2-PPV-2629971` 账本是
`安娜`、fc2cmadb 是日文原名 `あんな`。这类差异由人判，本脚本只出清单。

一个番号一行，主键 `<番号>:performers:fc2cmadb`，写进 `generated/fc2-cast-candidates.csv`，
复核页的「资料字段」读得到它（`review_csv.ADDITIONAL_CANDIDATE_FILES`）。批准时同番号的各个
分段一起改，只替换机器写入的演员关联，用户自己加的保留（`metadata_auto_apply`）。

只读账本。fc2cmadb 那一页优先取本机快照（`sources/library-metadata/<番号>-fc2cmadb.json`，
资料采集任务也读写这一份），没有才联网问，问到的照样存成快照，重跑不再发请求。站上说没有的
番号记在 `state/fc2-cast-misses.json`，一周内不再问。联网时两问之间停 `--interval` 秒：
2026-09-23 不停顿连问，第 19 个番号上被限流 15 分钟。`--offline` 只看快照。有一位演员关联不是机器写入的番号整条跳过：那是用户判断过的。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import DATABASE_PATH, GENERATED_DIR, SECRETS_DIR, SOURCES_DIR, STATE_DIR  # noqa: E402
from peach.entities import normalize_entity_name, resolve_entity  # noqa: E402
from peach.metadata import extract_catalog_evidence, extract_peach_fields  # noqa: E402
from peach.library_processing import (LibraryMetadataProvider, PROVIDER_NAMES,  # noqa: E402
                                      _candidate_identity, _MissCache, is_missing)
from peach.review_csv import write_rows  # noqa: E402
from peach.scripting import open_readonly  # noqa: E402

SOURCE = "fc2cmadb"
OUTPUT_NAME = "fc2-cast-candidates.csv"
FIELDS = (
    "item_key", "code", "query", "field", "field_label", "current_value",
    "candidates_json", "source_count", "source_profile", "policy_version",
    "status", "size_gb", "videos", "fetched_at",
)
#: 机器写入的演员关联：采集与自动落库都记成 `javinizer:<来源>:performer`。
MACHINE_SOURCE = "javinizer:"


def current_cast(connection) -> dict[str, list[str]]:
    """FC2 番号 → 账本里的演员名；有一条非机器写入的关联就整个番号不收。"""
    cast: dict[str, list[str]] = {}
    curated: set[str] = set()
    for row in connection.execute(
            "SELECT a.code, e.canonical_name, ae.source FROM asset a "
            "JOIN asset_entity ae ON ae.asset_id=a.id JOIN entity e ON e.id=ae.entity_id "
            "WHERE a.code LIKE 'FC2-PPV-%' AND ae.role='performer' ORDER BY a.code, e.canonical_name"):
        code, name, source = str(row[0]), str(row[1]), str(row[2] or "")
        if not source.startswith(MACHINE_SOURCE):
            curated.add(code)
        names = cast.setdefault(code, [])
        if name not in names:
            names.append(name)
    return {code: names for code, names in cast.items() if code not in curated}


def snapshot_path(snapshots: Path, code: str) -> Path:
    return snapshots / f"{code}-{SOURCE}.json"


def mirror_payload(code: str, snapshots: Path, provider=None, misses=None) -> dict | None:
    """fc2cmadb 那一页的快照；站上没有、离线且没存过时回 None。"""
    path = snapshot_path(snapshots, code)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    if provider is None or (misses is not None and misses.fresh(SOURCE, code)):
        return None
    try:
        payload = provider.site(SOURCE, code)
    except Exception as error:  # noqa: BLE001 - 「没有」之外的原因原样抛给调用方
        if is_missing(error):
            if misses is not None:
                misses.record(SOURCE, code)
            return None
        raise
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return payload


def same_people(connection, current: list[str], offered: list[str]) -> bool:
    """两边是不是同一组人：写法不同但账本已登记为同一条实体的不算分歧。"""
    def identities(names):
        found = set()
        for name in names:
            entity = resolve_entity(connection, "performer", name)
            found.add(f"id:{entity['id']}" if entity else "name:" + normalize_entity_name(name))
        return found
    return identities(current) == identities(offered)


def review_row(code: str, current: list[str], payload: dict, snapshot: Path) -> dict | None:
    """一个番号的复核行；fc2cmadb 没给演员时回 None。"""
    value = extract_peach_fields(payload).get("performers")
    if not value:
        return None
    candidate = {
        "candidate_key": _candidate_identity(SOURCE, value["value"]),
        "source": SOURCE, "provider": PROVIDER_NAMES[SOURCE],
        "value": value["value"], "display_value": value["display_value"],
        "warnings": value.get("warnings", []), "confidence": 0.6,
        "source_url": payload.get("source_url", ""), "raw_snapshot": str(snapshot),
        "provider_id": str(payload.get("id") or ""), "content_id": str(payload.get("content_id") or ""),
        "source_kind": "community", "official": False,
        "catalog_evidence": extract_catalog_evidence(payload),
    }
    return {
        "item_key": f"{code}:performers:{SOURCE}", "code": code, "query": code,
        "field": "performers", "field_label": "演员", "current_value": "、".join(current),
        "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": 1,
        "source_profile": "fc2-cast", "policy_version": "fc2-cast-v1", "status": "candidate",
        "size_gb": "", "videos": "", "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=DATABASE_PATH, help="账本路径（只读）")
    parser.add_argument("--snapshots", type=Path, default=SOURCES_DIR / "library-metadata",
                        help="来源快照目录")
    parser.add_argument("--output", type=Path, default=GENERATED_DIR / OUTPUT_NAME)
    parser.add_argument("--offline", action="store_true", help="只看本机快照，不联网")
    parser.add_argument("--limit", type=int, default=0, help="最多看几个番号，0 为不限")
    parser.add_argument("--misses", type=Path, default=STATE_DIR / "fc2-cast-misses.json",
                        help="站上说没有的番号记在这里，一周内不再问")
    parser.add_argument("--interval", type=float, default=5.0, help="两次联网询问之间停几秒")
    return parser


def run(args: argparse.Namespace, provider=None, sleep=time.sleep) -> dict:
    with closing(open_readonly(args.db)) as connection:
        cast = current_cast(connection)
        codes = sorted(cast)[:args.limit] if args.limit else sorted(cast)
        if provider is None and not args.offline:
            provider = LibraryMetadataProvider(SECRETS_DIR)
        misses = _MissCache(args.misses)
        rows, absent, agreed, stopped, asked = [], 0, 0, "", False
        for code in codes:
            live = (not args.offline and not snapshot_path(args.snapshots, code).is_file()
                    and not misses.fresh(SOURCE, code))
            if live and asked:
                sleep(args.interval)
            asked = asked or live
            try:
                payload = mirror_payload(code, args.snapshots, None if args.offline else provider, misses)
            except Exception as error:  # noqa: BLE001 - 冷却、限流或断网：停下，已问到的快照留着
                stopped = f"{code}：{error}"
                break
            if payload is None:
                absent += 1
                continue
            offered = (extract_peach_fields(payload).get("performers") or {}).get("value") or []
            if not offered or same_people(connection, cast[code],
                                          [person["name"] for person in offered]):
                agreed += 1
                continue
            rows.append(review_row(code, cast[code], payload, snapshot_path(args.snapshots, code)))
    write_rows(args.output, FIELDS, rows, atomic=True)
    return {"codes": len(codes), "review": len(rows), "agreed_or_empty": agreed,
            "not_on_mirror": absent, "stopped": stopped, "output": str(args.output)}


def main(argv: list[str] | None = None) -> int:
    result = run(build_parser().parse_args(argv))
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["stopped"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
