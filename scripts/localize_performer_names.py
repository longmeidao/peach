#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""用经维护的中日姓名映射本地化番号体系女优名称。

只处理带 `r18:performer` / `javbus:performer` 发行来源的实体；账号型 performer 不翻译。
匹配按精确证据分层：既有人工复核日文名、当前日文名、既有别名，再到复核表里的旧名。
一条名字命中多个映射时不猜。多个 ledger 实体落到同一映射条目时，按同一人的旧名合并。

映射 XML 是外部复核来源，不随 Peach 分发。默认只产出全库 CSV；`--apply` 写真实 ledger
时必须同时提供 `--backup`。旧规范名、日文名、假名与繁体名都保留为别名。
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from peach.config import DATABASE_PATH, DATA_ROOT, GENERATED_DIR
from peach.entities import merge_entity, normalize_entity_name
from peach.migrations import sqlite_backup
from peach.review_csv import read_rows, write_rows


RELEASE_SOURCES = frozenset({"r18:performer", "javbus:performer"})
ALIAS_SOURCE_PREFIX = "avdb-actor-mapping"
MERGE_ALIAS_SOURCE = "merge:performer-localization"

# 该映射条目的 zh_cn 仍误填日文，但 keyword 同时给出简/繁中文；中文资料页也交叉确认。
# 只在外部条目确实携带这个候选时启用，避免脱离来源硬编码一个无法追溯的译名。
REVIEWED_CN_OVERRIDES = {"釈アリス": "释爱丽丝"}


@dataclass(frozen=True)
class ActorMapping:
    index: int
    jp: str
    zh_cn: str
    zh_tw: str
    keywords: tuple[str, ...]
    tmdb_id: str
    verified: str

    @property
    def key(self) -> str:
        return f"tmdb:{self.tmdb_id}" if self.tmdb_id else f"xml:{self.index}:{self.jp}"


def read_mapping(path: Path) -> list[ActorMapping]:
    root = ET.parse(path).getroot()
    rows = []
    for index, node in enumerate(root.iter("a")):
        keywords = tuple(
            dict.fromkeys(part.strip() for part in node.attrib.get("keyword", "").split(",")
                          if part.strip())
        )
        rows.append(ActorMapping(
            index=index,
            jp=node.attrib.get("jp", "").strip(),
            zh_cn=node.attrib.get("zh_cn", "").strip(),
            zh_tw=node.attrib.get("zh_tw", "").strip(),
            keywords=keywords,
            tmdb_id=node.attrib.get("tmdb_id", "").strip(),
            verified=node.attrib.get("verified", "").strip(),
        ))
    return rows


def read_identity_review(path: Path | None) -> dict[int, dict[str, str]]:
    if path is None or not path.is_file():
        return {}
    return {int(row["entity_id"]): row for row in read_rows(path)}


def _unique(values: list[int]) -> int | None:
    found = set(values)
    return next(iter(found)) if len(found) == 1 else None


def _contains_latin(value: str) -> bool:
    return bool(re.search(r"[A-Za-z]", value or ""))


def _is_non_latin_east_asian(value: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", value or "")) \
        and not _contains_latin(value)


def _target_name(mapping: ActorMapping) -> tuple[str, str]:
    override = REVIEWED_CN_OVERRIDES.get(mapping.jp)
    if override and override in mapping.keywords:
        return override, "reviewed-keyword-cn"
    return mapping.zh_cn or mapping.jp, "zh_cn" if mapping.zh_cn else "jp-fallback"


def collect(
    connection: sqlite3.Connection,
    mappings: list[ActorMapping],
    identity_review: dict[int, dict[str, str]],
    revision: str,
) -> list[dict[str, object]]:
    """审计全部 performer，返回可重放计划；未命中与非发行来源也进入 CSV。"""
    connection.row_factory = sqlite3.Row
    by_jp: dict[str, list[int]] = defaultdict(list)
    by_keyword: dict[str, list[int]] = defaultdict(list)
    by_cn: dict[str, list[int]] = defaultdict(list)
    for mapping in mappings:
        if mapping.jp:
            by_jp[normalize_entity_name(mapping.jp)].append(mapping.index)
        for keyword in mapping.keywords:
            by_keyword[normalize_entity_name(keyword)].append(mapping.index)
        for value in (mapping.zh_cn, mapping.zh_tw):
            if value:
                by_cn[normalize_entity_name(value)].append(mapping.index)

    aliases: dict[int, list[str]] = defaultdict(list)
    for entity_id, alias in connection.execute(
        "SELECT entity_id,alias FROM entity_alias ORDER BY entity_id,alias"
    ):
        aliases[int(entity_id)].append(str(alias))

    entities = connection.execute(
        """
        SELECT e.id,e.canonical_name,e.normalized_name,
               (SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae
                 WHERE ae.entity_id=e.id) assets,
               (SELECT group_concat(DISTINCT ae.source) FROM asset_entity ae
                 WHERE ae.entity_id=e.id) sources,
               (SELECT x.external_id FROM entity_external_ref x
                 WHERE x.entity_id=e.id AND x.provider='r18'
                   AND x.external_kind IN ('performer','performer_name')
                 ORDER BY CASE x.external_kind WHEN 'performer_name' THEN 0 ELSE 1 END
                 LIMIT 1) release_name
        FROM entity e WHERE e.kind='performer' ORDER BY e.id
        """
    ).fetchall()
    by_id = {int(entity["id"]): entity for entity in entities}

    rows: list[dict[str, object]] = []
    resolved_groups: dict[int, list[dict[str, object]]] = defaultdict(list)
    for entity in entities:
        entity_id = int(entity["id"])
        sources = str(entity["sources"] or "")
        source_set = set(filter(None, sources.split(",")))
        base: dict[str, object] = {
            "entity_id": entity_id,
            "current_name": str(entity["canonical_name"]),
            "target_name": str(entity["canonical_name"]),
            "assets": int(entity["assets"]),
            "sources": sources,
            "mapping_key": "",
            "mapping_jp": "",
            "mapping_zh_cn": "",
            "resolution": "",
            "action": "",
            "merge_target_id": "",
            "revision": revision,
            "_aliases": set(aliases.get(entity_id, [])),
            "_mapping_index": None,
        }
        if not RELEASE_SOURCES.intersection(source_set):
            base.update(resolution="non-release performer", action="keep-non-release")
            rows.append(base)
            continue

        review = identity_review.get(entity_id, {})
        ordered: list[tuple[str, str]] = []
        if review.get("japanese_name"):
            ordered.append(("review-jp", review["japanese_name"]))
        ordered.append(("canonical-jp", str(entity["canonical_name"])))
        ordered.extend(("alias-jp", alias) for alias in aliases.get(entity_id, []))

        mapping_index = None
        resolution = ""
        for label, name in ordered:
            candidate = _unique(by_jp.get(normalize_entity_name(name), []))
            if candidate is not None:
                mapping_index, resolution = candidate, label
                break
        if mapping_index is None and review.get("japanese_name"):
            candidate = _unique(by_keyword.get(
                normalize_entity_name(review["japanese_name"]), []))
            if candidate is not None:
                mapping_index, resolution = candidate, "review-jp-keyword"
        if mapping_index is None and review.get("current_name"):
            candidate = _unique(by_keyword.get(
                normalize_entity_name(review["current_name"]), []))
            if candidate is not None:
                mapping_index, resolution = candidate, "review-romaji-keyword"
        if mapping_index is None:
            candidate = _unique(by_cn.get(
                normalize_entity_name(str(entity["canonical_name"])), []))
            if candidate is not None:
                mapping_index, resolution = candidate, "canonical-cn"

        review_aliases = {
            value.strip()
            for value in (
                review.get("current_name", ""), review.get("japanese_name", ""),
                review.get("kana", ""), *(review.get("former_names", "").split("|")),
            ) if value.strip()
        }
        base["_aliases"].update(review_aliases)
        if mapping_index is None:
            fallback = review.get("japanese_name", "").strip()
            if (fallback and _contains_latin(str(entity["canonical_name"]))
                    and normalize_entity_name(fallback) != entity["normalized_name"]):
                base.update(
                    target_name=fallback,
                    resolution="reviewed Japanese fallback",
                    action="localize-jp-fallback",
                )
            else:
                base.update(resolution="no unique mapping", action="keep-unresolved")
            rows.append(base)
            continue

        mapping = mappings[mapping_index]
        target, target_source = _target_name(mapping)
        # 外部映射偶有把 `zh_cn` 填成罗马字。不能因此把已有的日文/中文规范名
        # 倒退成英文；已发生倒退时，仅用同时出现在该映射条目中的 r18 发行名恢复。
        if _contains_latin(target):
            release_name = str(entity["release_name"] or "").strip()
            mapping_names = {
                normalize_entity_name(value)
                for value in (mapping.jp, *mapping.keywords) if value
            }
            if (_is_non_latin_east_asian(release_name)
                    and normalize_entity_name(release_name) in mapping_names):
                target, target_source = release_name, "r18-nonlatin-release-name"
            elif _is_non_latin_east_asian(str(entity["canonical_name"])):
                target, target_source = str(entity["canonical_name"]), "preserve-nonlatin"
        base.update(
            target_name=target,
            mapping_key=mapping.key,
            mapping_jp=mapping.jp,
            mapping_zh_cn=mapping.zh_cn,
            resolution=f"{resolution}/{target_source}",
            action="localize" if target != entity["canonical_name"] else "keep-localized",
            _mapping_index=mapping_index,
        )
        base["_aliases"].update(
            value for value in (mapping.jp, mapping.zh_tw, str(entity["canonical_name"]))
            if value
        )
        rows.append(base)
        resolved_groups[mapping_index].append(base)

    # 同一映射条目命中多个实体，就是同一人的旧名分裂。保留作品多的一侧。
    for group in resolved_groups.values():
        if len(group) < 2:
            continue
        keeper = max(group, key=lambda row: (int(row["assets"]), -int(row["entity_id"])))
        keeper["action"] = "merge-and-localize"
        all_aliases = set().union(*(row["_aliases"] for row in group))
        all_aliases.update(str(row["current_name"]) for row in group)
        keeper["_aliases"] = all_aliases
        for row in group:
            if row is keeper:
                continue
            row["action"] = "merge-drop"
            row["merge_target_id"] = keeper["entity_id"]

    # 名字唯一约束最后守门。只有同一 mapping group 的 merge-drop 可以与目标重名。
    active_targets: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["action"] not in {"merge-drop", "keep-non-release", "keep-unresolved"}:
            active_targets[normalize_entity_name(str(row["target_name"]))].append(row)
    existing = {
        str(entity["normalized_name"]): int(entity["id"])
        for entity in entities
    }
    dropping_into = {
        int(row["entity_id"]): int(row["merge_target_id"])
        for row in rows if row["action"] == "merge-drop"
    }
    for normalized, target_rows in active_targets.items():
        target_ids = {int(row["entity_id"]) for row in target_rows}
        owner = existing.get(normalized)
        owner_merges_here = (
            owner is not None and len(target_ids) == 1
            and dropping_into.get(owner) == next(iter(target_ids))
        )
        conflict = len(target_rows) > 1 or (
            owner is not None and owner not in target_ids and not owner_merges_here)
        if conflict:
            for row in target_rows:
                row["action"] = "conflict"
                row["resolution"] = str(row["resolution"]) + "/target-name-conflict"
    return rows


def _insert_aliases(
    connection: sqlite3.Connection, entity_id: int, names: set[str], source: str,
) -> int:
    written = 0
    canonical = connection.execute(
        "SELECT normalized_name FROM entity WHERE id=?", (entity_id,)
    ).fetchone()[0]
    for name in sorted(names, key=str.casefold):
        normalized = normalize_entity_name(name)
        if not normalized or normalized == canonical:
            continue
        if connection.execute(
            "SELECT 1 FROM entity_alias WHERE entity_id=? AND normalized_alias=? LIMIT 1",
            (entity_id, normalized),
        ).fetchone():
            continue
        connection.execute(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
            "VALUES(?,?,?,?,1.0)", (entity_id, name, normalized, source))
        written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def _rewrite_actor_tags(
    connection: sqlite3.Connection, entity_id: int, old_names: set[str], target: str,
) -> int:
    rewritten = 0
    asset_ids = [int(row[0]) for row in connection.execute(
        "SELECT DISTINCT asset_id FROM asset_entity WHERE entity_id=?", (entity_id,))]
    target_tag = f"演员:{target}"
    for asset_id in asset_ids:
        for old_name in old_names:
            old_tag = f"演员:{old_name}"
            if old_tag == target_tag:
                continue
            connection.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "SELECT asset_id,?,confidence,source FROM asset_tag "
                "WHERE asset_id=? AND tag=?", (target_tag, asset_id, old_tag))
            connection.execute(
                "DELETE FROM asset_tag WHERE asset_id=? AND tag=?", (asset_id, old_tag))
            if connection.execute("SELECT changes()").fetchone()[0]:
                rewritten += 1
    return rewritten


def apply_rows(
    connection: sqlite3.Connection, rows: list[dict[str, object]], revision: str,
) -> dict[str, int]:
    if any(row["action"] == "conflict" for row in rows):
        raise RuntimeError("复核计划仍有 target-name-conflict，拒绝写入")
    counts = Counter()
    source = f"{ALIAS_SOURCE_PREFIX}@{revision[:12]}"
    by_id = {int(row["entity_id"]): row for row in rows}

    for row in rows:
        if row["action"] != "merge-drop":
            continue
        source_id = int(row["entity_id"])
        target_id = int(row["merge_target_id"])
        moved = merge_entity(
            connection, target_id=target_id, source_id=source_id,
            source_name=str(row["current_name"]), alias_source=MERGE_ALIAS_SOURCE,
        )
        counts["merged"] += 1
        counts["relations_moved"] += moved["assets"]
        counts["dropped_refs"] += moved["dropped_refs"]
        by_id[target_id]["_aliases"].update(row["_aliases"])
        by_id[target_id]["_aliases"].add(str(row["current_name"]))

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for row in rows:
        if row["action"] not in {
            "localize", "merge-and-localize", "localize-jp-fallback", "keep-localized",
        }:
            continue
        entity_id = int(row["entity_id"])
        target = str(row["target_name"])
        old_names = set(row["_aliases"])
        old_names.add(str(row["current_name"]))
        connection.execute(
            "UPDATE entity SET canonical_name=?,normalized_name=?,updated_at=? WHERE id=?",
            (target, normalize_entity_name(target), stamp, entity_id),
        )
        if target != row["current_name"]:
            counts["renamed"] += connection.execute("SELECT changes()").fetchone()[0]
        counts["aliases"] += _insert_aliases(connection, entity_id, old_names, source)
        counts["actor_tags_rewritten"] += _rewrite_actor_tags(
            connection, entity_id, old_names, target)

        if row["mapping_key"]:
            raw = connection.execute(
                "SELECT metadata_json FROM entity WHERE id=?", (entity_id,)
            ).fetchone()[0]
            try:
                metadata = json.loads(raw or "{}")
            except (TypeError, ValueError):
                metadata = {}
            metadata["name_localization"] = {
                "source": ALIAS_SOURCE_PREFIX,
                "revision": revision,
                "mapping_key": row["mapping_key"],
                "jp": row["mapping_jp"],
                "zh_cn": target,
            }
            connection.execute(
                "UPDATE entity SET metadata_json=? WHERE id=?",
                (json.dumps(metadata, ensure_ascii=False, separators=(",", ":")), entity_id),
            )
            counts["provenance"] += 1
    return dict(counts)


FIELDS = (
    "entity_id", "current_name", "target_name", "assets", "sources", "mapping_key",
    "mapping_jp", "mapping_zh_cn", "resolution", "action", "merge_target_id", "revision",
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    write_rows(path, FIELDS, rows, fill_missing=True)


def counts_of(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        "asset": connection.execute("SELECT count(*) FROM asset").fetchone()[0],
        "entity": connection.execute("SELECT count(*) FROM entity").fetchone()[0],
        "performer": connection.execute(
            "SELECT count(*) FROM entity WHERE kind='performer'").fetchone()[0],
        "asset_entity": connection.execute("SELECT count(*) FROM asset_entity").fetchone()[0],
        "asset_tag": connection.execute("SELECT count(*) FROM asset_tag").fetchone()[0],
        "entity_alias": connection.execute("SELECT count(*) FROM entity_alias").fetchone()[0],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="用中日映射本地化番号体系女优姓名")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--mapping-xml", type=Path, required=True)
    parser.add_argument("--mapping-revision", required=True)
    parser.add_argument(
        "--identity-review", type=Path,
        default=DATA_ROOT / "review" / "performer-identity-20260815.csv")
    parser.add_argument(
        "--review-csv", type=Path,
        default=GENERATED_DIR / "performer-name-localization.csv")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path, help="--apply 必需")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    mappings = read_mapping(args.mapping_xml)
    identity_review = read_identity_review(args.identity_review)
    connection = sqlite3.connect(args.db)
    try:
        rows = collect(connection, mappings, identity_review, args.mapping_revision)
        write_csv(args.review_csv, rows)
        print(f"已审计 performer {len(rows)} 位；复核 CSV：{args.review_csv}")
        print("  动作分布：", dict(Counter(str(row["action"]) for row in rows)))
        if not args.apply:
            print("  未写 ledger（加 --apply --backup 才写）")
            return 1 if any(row["action"] == "conflict" for row in rows) else 0

        before = counts_of(connection)
        sqlite_backup(args.db, args.backup)
        print(f"  已备份到 {args.backup}")
        with connection:
            changed = apply_rows(connection, rows, args.mapping_revision)
        after = counts_of(connection)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        print("  写入结果：", changed)
        for key in before:
            print(f"    {key}: {before[key]} -> {after[key]}")
        print(f"  integrity_check={integrity}；foreign_key_check={len(foreign_keys)}")
        return 1 if integrity != "ok" or foreign_keys else 0
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
