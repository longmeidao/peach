#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""同一个人被同时记成 creator 和 performer 的去重。

`entity` 的唯一约束是 `(kind, normalized_name)`，所以同名但 kind 不同的两条记录
可以并存。实际发生了 35 组：卡片上的头像和名字会一个跳 `/performers/x`、另一个跳
`/creators/x`，统计、筛选和资料页也各算各的。

两条来路很清楚：

    creator   ← source='legacy:asset'，从目录名投影出来（ADR-0013：目录名只是候选证据）
    performer ← source='r18:performer' / 'javbus:performer'（真实发行元数据）
                或 'performer'（Stash 扁平模型）

除了完全同名，还会处理一类高置信变体：两边关联的非空作品集合完全相同，且 performer
别名等于 creator 名，或 creator 名由 performer 本名和账号别名拼成。名字相似但作品集合
不同的不会自动合并。

**保留哪一边只看 provenance，不看数量**：

- performer 侧带 `r18:performer` / `javbus:performer` 的保留 performer。那是发行元数据，creator 侧只是
  网盘目录名恰好等于艺名，正是 ADR-0013 要防的那种误投影。
- 否则保留 creator。剩下的 performer 断言全部来自 Stash 的扁平 performer 模型——
  `docs/STASH.md` 已把它判为已知缺陷（把上传者、合集和演员塞进同一个平面）——而
  creator 侧往往对应一个真实的本地目录。

按数量投票会翻车：`小桃` 的 performer 侧有 151 条、creator 侧只有 15 条，但它是
本地 `media/创作者/小桃` 的上传者，不是女优。

合并不可逆。默认只产出复核 CSV，`--apply` 才写 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from collections import Counter
from pathlib import Path

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    merge_entity,
    normalize_entity_name,
)
from peach.migrations import sqlite_backup


#: 真实发行元数据的来源标记。只有这些能把一条断言判成「这是女优，不是上传者」。
RELEASE_SOURCES = frozenset({"r18:performer", "javbus:performer"})
MERGE_ALIAS_SOURCE = "merge:duplicate-identity"


def _fold(value: str) -> str:
    """与 entity 规范化一致，并忽略账号名前缀和多余空白。"""
    return " ".join(part.lstrip("@").casefold() for part in str(value).split())


def _fuzzy_evidence(
    creator_name: str, performer_name: str, performer_aliases: list[str],
) -> str | None:
    """返回可自动合并的名字证据；仅由作品集合相同的调用方使用。"""
    creator = _fold(creator_name)
    performer = _fold(performer_name)
    aliases = {_fold(alias) for alias in performer_aliases if _fold(alias)}
    if creator in aliases:
        return "performer 别名等于 creator 名"
    if creator != performer and performer in creator:
        account_aliases = {
            alias for alias in aliases
            if alias != performer and len(re.sub(r"\s+", "", alias)) >= 3
        }
        if any(alias in creator for alias in account_aliases):
            return "creator 名由 performer 本名与账号别名组成"
    return None


def _release_backed(sources: str) -> bool:
    return bool(RELEASE_SOURCES.intersection(filter(None, sources.split(","))))


def collect(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """找出高置信跨 kind 重复实体，并按 provenance 定出保留哪一边。"""
    connection.row_factory = sqlite3.Row
    entity_rows = connection.execute(
        """
        SELECT e.id, e.kind, e.canonical_name, e.normalized_name,
               (SELECT count(*) FROM asset_entity ae WHERE ae.entity_id=e.id) AS links,
               (SELECT group_concat(DISTINCT ae.source) FROM asset_entity ae
                 WHERE ae.entity_id=e.id) AS sources
        FROM entity e
        WHERE e.kind IN ('creator','performer')
        ORDER BY e.id
        """
    ).fetchall()

    aliases: dict[int, list[str]] = {}
    for row in connection.execute(
        "SELECT entity_id,alias FROM entity_alias ORDER BY entity_id,alias"
    ):
        aliases.setdefault(int(row["entity_id"]), []).append(str(row["alias"]))
    asset_members: dict[int, set[int]] = {}
    for row in connection.execute(
        "SELECT entity_id,asset_id FROM asset_entity ORDER BY entity_id,asset_id"
    ):
        asset_members.setdefault(int(row["entity_id"]), set()).add(int(row["asset_id"]))
    assets = {
        entity_id: frozenset(asset_ids)
        for entity_id, asset_ids in asset_members.items()
    }

    creators = [row for row in entity_rows if row["kind"] == "creator"]
    performers = [row for row in entity_rows if row["kind"] == "performer"]
    by_normalized_creator = {row["normalized_name"]: row for row in creators}
    by_normalized_performer = {row["normalized_name"]: row for row in performers}

    candidates: dict[tuple[int, int], tuple[sqlite3.Row, sqlite3.Row, str]] = {}
    for normalized in sorted(set(by_normalized_creator) & set(by_normalized_performer)):
        creator = by_normalized_creator[normalized]
        performer = by_normalized_performer[normalized]
        candidates[(int(creator["id"]), int(performer["id"]))] = (
            creator, performer, "规范名完全相同")

    performer_ids_by_name: dict[str, set[int]] = {}
    performer_by_id = {int(row["id"]): row for row in performers}
    for performer in performers:
        performer_id = int(performer["id"])
        values = [str(performer["canonical_name"]), *aliases.get(performer_id, [])]
        for value in values:
            performer_ids_by_name.setdefault(_fold(value), set()).add(performer_id)
    for creator in creators:
        repeated = collapse_repeated_entity_name(str(creator["canonical_name"]))
        if repeated == str(creator["canonical_name"]).strip():
            continue
        matched_ids = performer_ids_by_name.get(_fold(repeated), set())
        release_ids = {
            entity_id for entity_id in matched_ids
            if _release_backed(str(performer_by_id[entity_id]["sources"] or ""))
        }
        if len(release_ids) != 1:
            continue
        performer = performer_by_id[next(iter(release_ids))]
        candidates[(int(creator["id"]), int(performer["id"]))] = (
            creator, performer, "creator 规范名是完整重复串",
        )

    creators_by_assets: dict[frozenset[int], list[sqlite3.Row]] = {}
    performers_by_assets: dict[frozenset[int], list[sqlite3.Row]] = {}
    for creator in creators:
        asset_set = assets.get(int(creator["id"]), frozenset())
        if asset_set:
            creators_by_assets.setdefault(asset_set, []).append(creator)
    for performer in performers:
        asset_set = assets.get(int(performer["id"]), frozenset())
        if asset_set:
            performers_by_assets.setdefault(asset_set, []).append(performer)

    fuzzy: list[tuple[sqlite3.Row, sqlite3.Row, str]] = []
    for asset_set in set(creators_by_assets) & set(performers_by_assets):
        for creator in creators_by_assets[asset_set]:
            for performer in performers_by_assets[asset_set]:
                key = (int(creator["id"]), int(performer["id"]))
                if key in candidates:
                    continue
                evidence = _fuzzy_evidence(
                    str(creator["canonical_name"]), str(performer["canonical_name"]),
                    aliases.get(int(performer["id"]), []),
                )
                if evidence:
                    fuzzy.append((creator, performer, evidence))

    # 一方若同时命中多个候选，就留给人工复核，避免同作品集合内的连锁误并。
    fuzzy_counts = Counter(
        (side, entity_id)
        for creator, performer, _ in fuzzy
        for side, entity_id in (("creator", int(creator["id"])),
                                ("performer", int(performer["id"])))
    )
    for creator, performer, evidence in fuzzy:
        if (fuzzy_counts[("creator", int(creator["id"]))] == 1
                and fuzzy_counts[("performer", int(performer["id"]))] == 1):
            candidates[(int(creator["id"]), int(performer["id"]))] = (
                creator, performer, evidence)

    plan: list[dict[str, object]] = []
    for _, (creator, performer, match_evidence) in sorted(candidates.items()):
        release_backed = _release_backed(performer["sources"] or "")
        keep, drop = (performer, creator) if release_backed else (creator, performer)
        plan.append({
            "normalized_name": creator["normalized_name"],
            "match_evidence": match_evidence,
            "keep_kind": keep["kind"],
            "keep_id": keep["id"],
            "keep_name": keep["canonical_name"],
            "keep_links": keep["links"],
            "drop_kind": drop["kind"],
            "drop_id": drop["id"],
            "drop_name": drop["canonical_name"],
            "drop_links": drop["links"],
            "creator_sources": creator["sources"] or "",
            "performer_sources": performer["sources"] or "",
            "evidence": "发行元数据" if release_backed else "目录身份 + Stash 扁平 performer",
        })
    return plan


def apply_rows(
    connection: sqlite3.Connection, rows: list[dict[str, object]],
) -> dict[str, int]:
    """逐对合并，并同步兼容投影 `asset.creator` / `演员:` 标签。

    扁平字段必须跟着规范关系走（ADR-0005），否则资料页和卡片会各说各话：

    - 保留 creator：被并进来的资产可能原本没有 creator，补上；已有别的值不覆盖。
    - 保留 performer：creator 实体没了，等值的扁平字段一并清掉。
    """
    counts = Counter()
    for row in rows:
        keep_id, drop_id = int(row["keep_id"]), int(row["drop_id"])
        moving = [
            int(item[0]) for item in connection.execute(
                "SELECT asset_id FROM asset_entity WHERE entity_id=?", (drop_id,))
        ]
        moved = merge_entity(
            connection, target_id=keep_id, source_id=drop_id,
            source_name=str(row["drop_name"]), alias_source=MERGE_ALIAS_SOURCE,
        )
        counts["merged"] += 1
        counts["assets"] += moved["assets"]
        counts["aliases"] += moved["aliases"]
        counts["dropped_refs"] += moved["dropped_refs"]

        if row["keep_kind"] == "creator":
            for asset_id in moving:
                connection.execute(
                    "UPDATE asset SET creator=? WHERE id=? AND (creator IS NULL OR creator='')",
                    (row["keep_name"], asset_id))
                counts["flat_filled"] += connection.execute("SELECT changes()").fetchone()[0]
                connection.execute(
                    "DELETE FROM asset_tag WHERE asset_id=? AND tag=?",
                    (asset_id, f"演员:{row['drop_name']}"))
                counts["actor_tags_removed"] += connection.execute(
                    "SELECT changes()").fetchone()[0]
        else:
            connection.execute(
                "UPDATE asset SET creator=NULL WHERE creator=?", (row["drop_name"],))
            counts["flat_cleared"] += connection.execute("SELECT changes()").fetchone()[0]
            old_tag, new_tag = f"演员:{row['drop_name']}", f"演员:{row['keep_name']}"
            connection.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "SELECT asset_id,?,confidence,source FROM asset_tag WHERE tag=?",
                (new_tag, old_tag),
            )
            counts["actor_tags_inserted"] += connection.execute(
                "SELECT changes()"
            ).fetchone()[0]
            connection.execute("DELETE FROM asset_tag WHERE tag=?", (old_tag,))
            counts["actor_tags_rewritten"] += connection.execute(
                "SELECT changes()"
            ).fetchone()[0]
            if collapse_repeated_entity_name(str(row["drop_name"])) != str(row["drop_name"]):
                connection.execute(
                    "DELETE FROM entity_alias WHERE entity_id=? AND normalized_alias=?",
                    (keep_id, normalize_entity_name(str(row["drop_name"]))),
                )
                counts["bad_aliases_removed"] += connection.execute(
                    "SELECT changes()"
                ).fetchone()[0]
    return dict(counts)


def collect_repeated_projections(
    connection: sqlite3.Connection,
) -> list[dict[str, object]]:
    """审计 person 名称的完整重复串及其所有兼容投影。"""
    connection.row_factory = sqlite3.Row
    names: set[str] = set()
    names.update(str(row[0]) for row in connection.execute(
        "SELECT DISTINCT creator FROM asset WHERE creator IS NOT NULL AND creator<>''"
    ))
    names.update(str(row[0])[3:] for row in connection.execute(
        "SELECT DISTINCT tag FROM asset_tag WHERE tag LIKE '演员:%'"
    ))
    names.update(str(row[0]) for row in connection.execute(
        "SELECT DISTINCT alias FROM entity_alias a JOIN entity e ON e.id=a.entity_id "
        "WHERE e.kind IN ('creator','performer')"
    ))
    names.update(str(row[0]) for row in connection.execute(
        "SELECT canonical_name FROM entity WHERE kind IN ('creator','performer')"
    ))

    plan: list[dict[str, object]] = []
    for bad_name in sorted(names, key=str.casefold):
        collapsed = collapse_repeated_entity_name(bad_name)
        cleaned = canonicalize_entity_name("performer", bad_name)
        if collapsed == bad_name.strip() and cleaned:
            continue
        normalized = {normalize_entity_name(bad_name)}
        if cleaned:
            normalized.add(normalize_entity_name(cleaned))
        marks = ",".join("?" * len(normalized))
        targets = connection.execute(
            "SELECT e.id,e.canonical_name,"
            "(SELECT group_concat(DISTINCT ae.source) FROM asset_entity ae "
            " WHERE ae.entity_id=e.id) sources "
            "FROM entity e WHERE e.kind='performer' AND (e.normalized_name IN (" + marks + ") "
            "OR e.id IN (SELECT a.entity_id FROM entity_alias a "
            "WHERE a.normalized_alias IN (" + marks + "))) GROUP BY e.id ORDER BY e.id",
            tuple(normalized) + tuple(normalized),
        ).fetchall()
        release_targets = [row for row in targets if _release_backed(str(row["sources"] or ""))]
        asset_ids = {
            int(row[0]) for row in connection.execute(
                "SELECT id FROM asset WHERE creator=? UNION "
                "SELECT asset_id FROM asset_tag WHERE tag=?",
                (bad_name, f"演员:{bad_name}"),
            )
        }
        linked_target_ids = {
            int(row["id"]) for row in release_targets
            if asset_ids and connection.execute(
                "SELECT 1 FROM asset_entity WHERE entity_id=? AND asset_id IN ("
                + ",".join("?" * len(asset_ids)) + ") LIMIT 1",
                (int(row["id"]), *sorted(asset_ids)),
            ).fetchone()
        }
        alias_owner_ids = {
            int(row[0]) for row in connection.execute(
                "SELECT DISTINCT e.id FROM entity_alias a JOIN entity e ON e.id=a.entity_id "
                "WHERE e.kind='performer' AND a.alias=?",
                (bad_name,),
            )
            if any(int(target["id"]) == int(row[0]) for target in release_targets)
        }
        chosen = None
        if len(alias_owner_ids) == 1:
            chosen_id = next(iter(alias_owner_ids))
            chosen = next(row for row in release_targets if int(row["id"]) == chosen_id)
        elif len(linked_target_ids) == 1:
            chosen_id = next(iter(linked_target_ids))
            chosen = next(row for row in release_targets if int(row["id"]) == chosen_id)
        elif len(release_targets) == 1:
            chosen = release_targets[0]
        action = "remove-invalid" if not cleaned else "review"
        if chosen is not None:
            action = "use-performer"
        plan.append({
            "bad_name": bad_name,
            "collapsed_name": cleaned,
            "action": action,
            "target_id": int(chosen["id"]) if chosen else "",
            "target_name": str(chosen["canonical_name"]) if chosen else "",
            "flat_assets": connection.execute(
                "SELECT count(*) FROM asset WHERE creator=?", (bad_name,)
            ).fetchone()[0],
            "actor_tags": connection.execute(
                "SELECT count(*) FROM asset_tag WHERE tag=?", (f"演员:{bad_name}",)
            ).fetchone()[0],
            "aliases": connection.execute(
                "SELECT count(*) FROM entity_alias WHERE alias=?", (bad_name,)
            ).fetchone()[0],
            "canonical_entities": connection.execute(
                "SELECT count(*) FROM entity WHERE canonical_name=? AND kind IN ('creator','performer')",
                (bad_name,),
            ).fetchone()[0],
            "evidence": (
                "重复别名所属 performer" if alias_owner_ids
                else "已关联的发行 performer" if linked_target_ids
                else "唯一发行 performer" if chosen
                else "已知页面控件文字" if not cleaned
                else "目标不唯一或未取得"
            ),
        })
    return plan


def apply_repeated_projections(
    connection: sqlite3.Connection, rows: list[dict[str, object]],
) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        if row["action"] == "review":
            counts["review_left"] += 1
            continue
        bad_name = str(row["bad_name"])
        connection.execute("UPDATE asset SET creator=NULL WHERE creator=?", (bad_name,))
        counts["flat_cleared"] += connection.execute("SELECT changes()").fetchone()[0]
        old_tag = f"演员:{bad_name}"
        if row["action"] == "use-performer":
            new_tag = f"演员:{row['target_name']}"
            connection.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "SELECT asset_id,?,confidence,source FROM asset_tag WHERE tag=?",
                (new_tag, old_tag),
            )
            counts["actor_tags_inserted"] += connection.execute(
                "SELECT changes()"
            ).fetchone()[0]
        connection.execute("DELETE FROM asset_tag WHERE tag=?", (old_tag,))
        counts["actor_tags_removed"] += connection.execute("SELECT changes()").fetchone()[0]

        alias_rows = connection.execute(
            "SELECT a.entity_id,a.source,a.confidence,e.normalized_name "
            "FROM entity_alias a JOIN entity e ON e.id=a.entity_id WHERE a.alias=?",
            (bad_name,),
        ).fetchall()
        for alias in alias_rows:
            cleaned = str(row["collapsed_name"] or "")
            if cleaned and normalize_entity_name(cleaned) != str(alias["normalized_name"]):
                connection.execute(
                    "INSERT OR IGNORE INTO entity_alias("
                    "entity_id,alias,normalized_alias,source,confidence) VALUES(?,?,?,?,?)",
                    (int(alias["entity_id"]), cleaned, normalize_entity_name(cleaned),
                     str(alias["source"]), float(alias["confidence"])),
                )
                counts["aliases_inserted"] += connection.execute(
                    "SELECT changes()"
                ).fetchone()[0]
            connection.execute(
                "DELETE FROM entity_alias WHERE entity_id=? AND normalized_alias=? AND source=?",
                (int(alias["entity_id"]), normalize_entity_name(bad_name), str(alias["source"])),
            )
            counts["aliases_removed"] += connection.execute("SELECT changes()").fetchone()[0]
    return dict(counts)


def write_projection_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["bad_name", "collapsed_name", "action", "target_id", "target_name",
              "flat_assets", "actor_tags", "aliases", "canonical_entities", "evidence"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["normalized_name", "match_evidence", "keep_kind", "keep_name", "keep_id", "keep_links",
              "drop_kind", "drop_name", "drop_id", "drop_links",
              "creator_sources", "performer_sources", "evidence"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def counts_of(connection: sqlite3.Connection) -> dict[str, int]:
    query = {
        "asset": "SELECT count(*) FROM asset",
        "entity": "SELECT count(*) FROM entity",
        "creator_entities": "SELECT count(*) FROM entity WHERE kind='creator'",
        "performer_entities": "SELECT count(*) FROM entity WHERE kind='performer'",
        "asset_entity": "SELECT count(*) FROM asset_entity",
        "asset_tag": "SELECT count(*) FROM asset_tag",
        "entity_alias": "SELECT count(*) FROM entity_alias",
    }
    return {key: connection.execute(sql).fetchone()[0] for key, sql in query.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="合并同名的 creator / performer 重复身份")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--review-csv", type=Path,
                        default=GENERATED_DIR / "duplicate-identity-merge.csv")
    parser.add_argument("--projection-review-csv", type=Path,
                        default=GENERATED_DIR / "repeated-identity-name-repair.csv")
    parser.add_argument("--apply", action="store_true", help="写 ledger；默认只出 CSV")
    parser.add_argument("--backup", type=Path, help="--apply 必需：写库前的 SQLite 备份路径")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    connection = sqlite3.connect(args.db)
    try:
        rows = collect(connection)
        projection_rows = collect_repeated_projections(connection)
        write_csv(args.review_csv, rows)
        write_projection_csv(args.projection_review_csv, projection_rows)
        print(f"高置信跨 kind 的重复身份 {len(rows)} 组，复核 CSV：{args.review_csv}")
        print("  保留方分布：", dict(Counter(str(row["keep_kind"]) for row in rows)))
        print(f"重复 person 名称/投影 {len(projection_rows)} 组，复核 CSV："
              f"{args.projection_review_csv}")
        print("  处理动作：", dict(Counter(str(row["action"]) for row in projection_rows)))
        if not args.apply:
            print("  未写 ledger（加 --apply --backup 才写）")
            return 0

        before = counts_of(connection)
        sqlite_backup(args.db, args.backup)
        print(f"  已备份到 {args.backup}")
        with connection:
            moved = apply_rows(connection, rows)
            projections = apply_repeated_projections(connection, projection_rows)
        after = counts_of(connection)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()

        print("  合并结果：", moved)
        print("  重复名称投影：", projections)
        for key in before:
            mark = "" if before[key] == after[key] else "  <-- 变化"
            print(f"    {key}: {before[key]} -> {after[key]}{mark}")
        print(f"  foreign_key_check 违规 {len(violations)} 条")
        return 1 if violations else 0
    finally:
        connection.close()


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
