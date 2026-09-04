#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""同一家厂牌被记成两条实体的去重：写法变体与日文名／罗马字名两类。

`entity` 的唯一约束是 `(kind, normalized_name)`，所以 `AVS collector's` 与
`AVS collector’s` 可以并存，`Prestige`（425 部）与 `プレステージ`（9 部）也可以。
后果不是报错而是每一处都少一半：资产数被劈开，标识各装一份，筛选和资料页各算各的。

两类判据都不靠转写。罗马音回日文没有唯一解，反过来也一样，所以这里一条都不推：

**写法变体**（class A）——NFKC 之后把弯撇号、星号与全角符号折成同一个形，两个名字
逐字相等才算一对。`シロウトTV` 与 `ラグジュTV` 不会撞上，因为这个折叠一个假名都不丢；
只留 ASCII 的折法会把它们双双折成 `tv`，那是错的。

**日文名／罗马字名**（class B）——用番号前缀作证据。前缀属于厂牌，两条实体共用同一个
前缀就是同一家：`ムーディーズ` 的 MIDA／MIDV／MIRD 三个全部也出现在 `MOODYZ` 名下。
唯一命中才当候选，撞上两家以上交人工。

保留哪一边：写法变体保留纯 ASCII 的那一个（用户 2026-09-04 定的口径「统一为英文、
罗马音」），两边都是或都不是 ASCII 时保留作品多的一侧；日文名／罗马字名一律保留罗马字侧。
被丢弃的名字降为别名，扁平 `asset.studio` 一并改写成保留名（ADR-0005：兼容投影跟着
规范关系走）。只改实体不改投影的话，下一次刮削会照着投影里的旧名把实体再建一遍。

合并不可逆。默认只产出复核 CSV，`--apply` 才写 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR   # noqa: E402
from peach.entities import merge_entity   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.scripting import (   # noqa: E402
    add_ledger_write_args, counts_of, open_for_write, verify_after_write,
)

MERGE_ALIAS_SOURCE = "merge:studio-name-variant"

#: 同一个符号的不同写法。NFKC 已经处理了全角（`＆`→`&`），剩下这些它不动。
SYMBOL_FOLD = str.maketrans({
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "☆": "*", "★": "*", "♪": "*",
})
#: 假名、汉字与全角片假名。判「这个名字是日文写法」只看有没有这些字符。
JAPANESE = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")
#: 番号前缀：连字符前那一段字母数字。`336KBI-042` 的前缀是 `336KBI`。
CODE_PREFIX = re.compile(r"^([A-Za-z][A-Za-z0-9]*)-\d")

FIELDS = ("keep_id", "keep_name", "keep_assets", "drop_id", "drop_name", "drop_assets",
          "klass", "evidence")


def variant_key(name: str) -> str:
    """写法变体的比较键：折掉符号写法与大小写，一个字符都不丢。

    不能退化成「只留 ASCII 字母数字」。那样纯日文名全折成空串，`シロウトTV` 与
    `ラグジュTV` 都折成 `tv`，129 个厂牌会凭空长出一堆假的重复对。
    """
    folded = unicodedata.normalize("NFKC", name).translate(SYMBOL_FOLD)
    return re.sub(r"\s+", "", folded).casefold()


def studios(connection: sqlite3.Connection) -> dict[int, str]:
    return {int(row[0]): str(row[1]) for row in connection.execute(
        "SELECT id,canonical_name FROM entity WHERE kind='studio'")}


def asset_facts(connection: sqlite3.Connection
                ) -> tuple[dict[int, int], dict[int, set[str]]]:
    """每个厂牌实体挂了多少作品、这些作品用过哪些番号前缀。"""
    counts: dict[int, int] = defaultdict(int)
    prefixes: dict[int, set[str]] = defaultdict(set)
    for entity_id, code in connection.execute(
            "SELECT ae.entity_id,a.code FROM asset_entity ae"
            " JOIN asset a ON a.id=ae.asset_id"
            " JOIN entity e ON e.id=ae.entity_id WHERE e.kind='studio'"):
        counts[int(entity_id)] += 1
        shape = CODE_PREFIX.match(str(code or ""))
        if shape:
            prefixes[int(entity_id)].add(shape.group(1).upper())
    return counts, prefixes


def _pair(keep: int, drop: int, names: dict[int, str], counts: dict[int, int],
          klass: str, evidence: str) -> dict[str, object]:
    return {"keep_id": keep, "keep_name": names[keep], "keep_assets": counts.get(keep, 0),
            "drop_id": drop, "drop_name": names[drop], "drop_assets": counts.get(drop, 0),
            "klass": klass, "evidence": evidence}


def spelling_variants(names: dict[int, str], counts: dict[int, int]) -> list[dict]:
    """同一个名字的两种写法。保留纯 ASCII 的那一个。"""
    grouped: dict[str, list[int]] = defaultdict(list)
    for entity_id, name in names.items():
        grouped[variant_key(name)].append(entity_id)
    rows = []
    for key, ids in sorted(grouped.items()):
        if len(ids) != 2:
            continue
        ascii_ids = [i for i in ids if names[i].isascii()]
        if len(ascii_ids) == 1:
            keep = ascii_ids[0]
            why = "同名不同写法，保留纯 ASCII 的一侧"
        else:
            keep = max(ids, key=lambda i: (counts.get(i, 0), -i))
            why = "同名不同写法，两侧同为 ASCII 或同为非 ASCII，保留作品多的一侧"
        drop = next(i for i in ids if i != keep)
        rows.append(_pair(keep, drop, names, counts, "写法变体", why))
    return rows


def script_variants(names: dict[int, str], counts: dict[int, int],
                    prefixes: dict[int, set[str]], taken: set[int]) -> list[dict]:
    """日文名与罗马字名各存一条。证据是共用的番号前缀，不是转写。"""
    latin = [i for i, name in names.items()
             if not JAPANESE.search(name) and i not in taken]
    rows = []
    for entity_id, name in sorted(names.items(), key=lambda item: item[1]):
        if not JAPANESE.search(name) or entity_id in taken or not prefixes.get(entity_id):
            continue
        shared = [(other, sorted(prefixes[entity_id] & prefixes.get(other, set())))
                  for other in latin]
        hits = [item for item in shared if item[1]]
        if len(hits) != 1:
            # 一个前缀都不共用说明证据不足；共用到两家以上说明前缀本身分不开，
            # 两种都交人工——这条捷径唯一的身份保证就是前缀，它不成立就没有别的。
            continue
        other, common = hits[0]
        rows.append(_pair(other, entity_id, names, counts, "日文名／罗马字名",
                          f"共用番号前缀 {'、'.join(common)}"))
    return rows


def collect(connection: sqlite3.Connection) -> list[dict]:
    names = studios(connection)
    counts, prefixes = asset_facts(connection)
    rows = spelling_variants(names, counts)
    taken = {int(row["keep_id"]) for row in rows} | {int(row["drop_id"]) for row in rows}
    return rows + script_variants(names, counts, prefixes, taken)


def apply_rows(connection: sqlite3.Connection, rows: list[dict]) -> dict[str, int]:
    """逐对合并，并把扁平 `asset.studio` 改写成保留名。"""
    counts = Counter()
    for row in rows:
        moved = merge_entity(
            connection, target_id=int(row["keep_id"]), source_id=int(row["drop_id"]),
            source_name=str(row["drop_name"]), alias_source=MERGE_ALIAS_SOURCE)
        counts["merged"] += 1
        for key in ("assets", "aliases", "links", "terms", "dropped_refs"):
            counts[key] += moved[key]
        connection.execute("UPDATE asset SET studio=? WHERE studio=?",
                           (row["keep_name"], row["drop_name"]))
        counts["flat_rewritten"] += connection.execute("SELECT changes()").fetchone()[0]
    return dict(counts)


EXTRA_COUNTS = {
    "studio_entities": "SELECT count(*) FROM entity WHERE kind='studio'",
    "studio_aliases": "SELECT count(*) FROM entity_alias a JOIN entity e"
                      " ON e.id=a.entity_id WHERE e.kind='studio'",
    "studio_asset_links": "SELECT count(*) FROM asset_entity ae JOIN entity e"
                          " ON e.id=ae.entity_id WHERE e.kind='studio'",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="合并写法变体与日文名／罗马字名重复的厂牌实体")
    add_ledger_write_args(parser)
    parser.add_argument("--review-csv", type=Path,
                        default=GENERATED_DIR / "studio-name-variant-merge.csv")
    return parser


def run(args: argparse.Namespace) -> int:
    connection = open_for_write(args)
    try:
        rows = collect(connection)
        write_rows(args.review_csv, FIELDS, rows)
        print(f"重复厂牌 {len(rows)} 组，复核 CSV：{args.review_csv}")
        print("  判据分布：", dict(Counter(str(row["klass"]) for row in rows)))
        for row in rows:
            print(f"    {row['drop_name']}（{row['drop_assets']} 部）"
                  f" -> {row['keep_name']}（{row['keep_assets']} 部）  {row['evidence']}")
        if not args.apply:
            print("  未写 ledger（加 --apply --backup 才写）")
            return 0

        print(f"  已备份到 {args.backup}")
        before = counts_of(connection, EXTRA_COUNTS)
        with connection:
            moved = apply_rows(connection, rows)
        after = counts_of(connection, EXTRA_COUNTS)
        _integrity, violations = verify_after_write(connection)
        print("  合并结果：", moved)
        for key in before:
            mark = "" if before[key] == after[key] else "  <-- 变化"
            print(f"    {key}: {before[key]} -> {after[key]}{mark}")
        print(f"  foreign_key_check 违规 {violations} 条")
        return 1 if violations else 0
    finally:
        connection.close()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
