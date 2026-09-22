#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把历史证据里的 javdb 演员 id 与 minnano-av 女优 id 落成 `entity_external_ref`。

人物资料页的外部入口按 `entity_external_ref` 里的站点 id 拼地址，没有 id 的站点不出现。
采集作品页时 id 跟着名字一起回来（`community_catalog.javdb_actresses`）；账本里已有的
几百位女优，她们的 id 散在两处**已经取回来的**证据里：

- **javdb 的页面缓存**（`peach.page_cache.Site` 落盘的整页 HTML）。资料页里有
  `href="/actors/<id>/collect"`，解析走 `peach.javdb`，和取中文名那条路同一份判据。
- **复核 CSV**。`harvest_agency_rosters.py` 的名册件每行都带 `entity_id` 与
  `actress_id`，那就是 minnano-av 的女优 id；`harvest_javdb_cn_names.py` 的件带
  `actor_id`。

两处都是磁盘上现成的东西，这个脚本一次网都不出。默认 dry-run，只产出复核 CSV；
`--apply` 才写库，并且必须同时给 `--backup`。

名字对不上就不登记：javdb 页那一侧按整条名字链（规范名加别名）精确匹配，同一页对上两条
实体、或同一条实体对上两个 id 时都记 `冲突` 让人看，不挑一个。已经有同 provider 的 id 时
不覆盖——那是另一件事，要先判哪个对。
"""
from __future__ import annotations

import argparse
import collections
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach import javdb   # noqa: E402
from peach.config import STATE_DIR   # noqa: E402
from peach.entry_links import EXTERNAL_KIND   # noqa: E402
from peach.review_csv import read_rows, write_rows   # noqa: E402
from peach.scripting import add_ledger_write_args, open_for_write, verify_after_write   # noqa: E402
from peach.social_links import name_key   # noqa: E402

JAVDB, MINNANO = "javdb", "minnano-av"
#: 复核 CSV 里这两列就是站点 id，列名由产出它们的脚本定下。
CSV_COLUMNS = {"actor_id": JAVDB, "actress_id": MINNANO}

OK, HAVE, CONFLICT, NOT_PERFORMER = "ok", "已有", "冲突", "不是女优实体"

FIELDS = ("entity_id", "canonical_name", "provider", "external_id",
          "origin", "verdict", "evidence")


def name_owners(connection: sqlite3.Connection) -> dict[str, set[int]]:
    """折叠键 → 拥有这个写法的女优实体。一个键对上两条就是重名，不猜。"""
    owners: dict[str, set[int]] = collections.defaultdict(set)
    for entity_id, written in connection.execute(
            "SELECT e.id,e.canonical_name FROM entity e WHERE e.kind='performer'"
            " UNION SELECT a.entity_id,a.alias FROM entity_alias a"
            " JOIN entity e ON e.id=a.entity_id WHERE e.kind='performer'"):
        if written:
            owners[name_key(str(written))].add(int(entity_id))
    return owners


def from_page_cache(cache_dir: Path, owners: dict[str, set[int]]) -> dict:
    """缓存下来的 javdb 资料页 → 实体 → 演员 id 集合。"""
    found: dict[int, set[str]] = collections.defaultdict(set)
    for path in sorted(Path(cache_dir).glob("*.html")):
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        actor = javdb.actor_id(html)
        if not actor:
            continue
        for written in javdb.all_names(html):
            for entity_id in owners.get(name_key(written), ()):
                found[entity_id].add(actor)
    return found


def from_csv(paths, provider_of: dict[str, str]) -> dict:
    """复核 CSV → （provider, 实体）→ id 集合。列名决定这一列属于哪个站。"""
    found: dict[tuple[str, int], set[str]] = collections.defaultdict(set)
    for path in paths:
        try:
            rows = read_rows(path)
        except OSError:
            continue
        for row in rows:
            raw = str(row.get("entity_id") or "").strip()
            if not raw.isdigit():
                continue
            for column, provider in provider_of.items():
                value = str(row.get(column) or "").strip()
                if value:
                    found[(provider, int(raw))].add(value)
    return found


def _existing(connection: sqlite3.Connection) -> dict[tuple[str, int], str]:
    return {(str(provider), int(entity_id)): str(external_id)
            for entity_id, provider, external_id in connection.execute(
                "SELECT entity_id,provider,external_id FROM entity_external_ref"
                " WHERE external_kind=?", (EXTERNAL_KIND,))}


def plan(connection: sqlite3.Connection, args: argparse.Namespace) -> list[dict]:
    """每条候选一行。已有、冲突、实体不对的也留行：下一趟要看得出这一位查过。"""
    owners = name_owners(connection)
    candidates: dict[tuple[str, int], tuple[set[str], str]] = {}
    if args.javdb_cache and Path(args.javdb_cache).is_dir():
        for entity_id, ids in from_page_cache(Path(args.javdb_cache), owners).items():
            candidates[(JAVDB, entity_id)] = (ids, f"javdb 页面缓存 {args.javdb_cache}")
    for path in args.csv:
        for (provider, entity_id), ids in from_csv([path], CSV_COLUMNS).items():
            have, origin = candidates.get((provider, entity_id), (set(), ""))
            candidates[(provider, entity_id)] = (
                have | ids, f"{origin}；{Path(path).name}".strip("；"))
    names = {int(entity_id): str(written) for entity_id, written in connection.execute(
        "SELECT id,canonical_name FROM entity WHERE kind='performer'")}
    saved = _existing(connection)
    rows: list[dict] = []
    for (provider, entity_id), (ids, origin) in sorted(
            candidates.items(), key=lambda item: (item[0][0], item[0][1])):
        row = {"entity_id": entity_id, "canonical_name": names.get(entity_id, ""),
               "provider": provider, "external_id": "", "origin": origin,
               "verdict": OK, "evidence": ""}
        if entity_id not in names:
            row.update(verdict=NOT_PERFORMER, evidence="账本里这条实体不是女优")
        elif len(ids) > 1:
            row.update(verdict=CONFLICT,
                       evidence=f"同一位对上 {len(ids)} 个 id：{'、'.join(sorted(ids))}")
        elif (provider, entity_id) in saved:
            row.update(external_id=saved[(provider, entity_id)],
                       verdict=HAVE if saved[(provider, entity_id)] in ids else CONFLICT,
                       evidence=(f"账本已有 {saved[(provider, entity_id)]}，"
                                 f"证据给的是 {sorted(ids)[0]}"))
        else:
            row.update(external_id=sorted(ids)[0], evidence=f"{origin} 里只有这一个 id")
        rows.append(row)
    return rows


def apply_rows(connection: sqlite3.Connection, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        if row["verdict"] != OK or not row["external_id"]:
            continue
        connection.execute(
            "INSERT OR IGNORE INTO entity_external_ref"
            "(entity_id,provider,external_kind,external_id,metadata_json)"
            " VALUES(?,?,?,?,?)",
            (row["entity_id"], row["provider"], EXTERNAL_KIND, row["external_id"],
             '{"source": "backfill_performer_entry_ids"}'))
        written += connection.execute("SELECT changes()").fetchone()[0]
    connection.commit()
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把 javdb 演员 id 与 minnano-av 女优 id 落成 entity_external_ref")
    add_ledger_write_args(parser)
    parser.add_argument("--out", type=Path, required=True, help="复核 CSV 的落点")
    parser.add_argument("--javdb-cache", type=Path,
                        default=STATE_DIR / "directory-links" / "javdb",
                        help="javdb 的页面缓存目录")
    parser.add_argument("--csv", type=Path, action="append", default=[],
                        help="带 entity_id 与 actor_id／actress_id 的复核 CSV，可重复给")
    return parser


def run(args: argparse.Namespace) -> int:
    connection = open_for_write(args)
    try:
        rows = plan(connection, args)
        write_rows(args.out, FIELDS, rows, fill_missing=True)
        counts = collections.Counter(str(row["verdict"]) for row in rows)
        by_site = collections.Counter(
            str(row["provider"]) for row in rows if row["verdict"] == OK)
        print(f"外部入口 id 候选 {len(rows)} 行，复核 CSV：{args.out}")
        print("  判定分布：", dict(counts))
        print("  可补的人物：", dict(by_site))
        if args.apply:
            written = apply_rows(connection, rows)
            integrity, violations = verify_after_write(connection)
            print(f"已写入 {written} 条 entity_external_ref；"
                  f"integrity_check={integrity}、外键违规 {violations} 条")
            return 1 if violations or integrity != "ok" else 0
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
