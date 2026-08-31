#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""番号目录被投影成创作者的清理器。

旧导入器把发行目录名直接当创作者写进 ledger。当目录名本身就是番号时，
创作者索引里就会多出一个假身份。实测样例：

    B:\云下载\HD-abp-758\HD-abp-758.mp4      creator=HD-abp-758  code=NULL
    B:\云下载\pppd-937ch\PPPD-937CH.mp4      creator=pppd-937ch  code=PPPD-937
    B:\云下载\Carib-040221-001-FHD\040221-001-carib-1080p.mp4

`HD-` 前缀是画质标记，不是番号的一部分；`-CH`/`C` 是中文字幕版后缀。两者都会让
番号提取放弃，于是 `code` 留空、目录名留在创作者位上。

同一形态里混着真实上传者账号，绝不能一起删：

    A:\Pack From Shared\pen\banbi_555\18歳Eカップ...mp4       banbi_555 是账号
    https://www.pixiv.net/users/93812377                      AH18 是 pixiv 画师

因此判定不看名字形态，只看文件级证据：目录内的媒体文件名必须解析出同一个番号。
账号目录里的文件是作品标题，解析不出番号，天然不会命中；pixiv 行的 path 是 URL，
直接排除。

默认只产出复核 CSV，`--apply` 才写 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
from collections import Counter
from pathlib import Path

from peach.review_csv import write_rows
from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.migrations import sqlite_backup

#: 画质标记。它们出现在番号前面，剥掉才能拿到真正的番号主体。
QUALITY_PREFIX = r"(?:hd|fhd|sd|uhd|4k|2160p?|1080p?|720p?)"
#: 版本标记。`-C`/`-CH` 是中文字幕版，`-UC` 是无码流出，画质词同样可能落在词尾。
VERSION_SUFFIX = r"(?:ch|sub|uc|fhd|4k|hd|c|u)"

_QUALITY_HEAD = re.compile(rf"^{QUALITY_PREFIX}[-_. ]+", re.I)
_VERSION_TAIL = re.compile(rf"[-_. ]?{VERSION_SUFFIX}$", re.I)
_LETTER_CODE = re.compile(r"^([A-Za-z]{2,8})[-_. ]?(\d{2,5})$")
#: 一本道、加勒比是「日期 + 序号」体系，没有字母番号主体。
_DATE_CODE = re.compile(r"(?<!\d)(\d{6})[-_](\d{3})(?!\d)")
#: fantia 之类的站点作品号既不是番号也不是创作者，单独归类。
_SITE_POST = re.compile(r"^(fantia)[-_](\d{6,10})$", re.I)
#: UUID 首段长得像番号（`DCE7230C-730E-…` 会被拆成 `DCE`+`7230`），按整串形态排除。
_UUID_LIKE = re.compile(
    r"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}", re.I)
_EXTENSION = re.compile(r"\.(?:mp4|mkv|avi|wmv|ts|mov|m4v|jpg|jpeg|png|webp)$", re.I)
#: 文件名尾部的分卷、画质和重复计数；剥掉才能和目录名对齐。
_FILE_NOISE = re.compile(
    r"(?:[-_. ]?(?:1080p?|720p?|2160p?|4k|fhd|hd|uc|sub|ch|c|u)"
    r"|[-_. ]\d{1,2}|\(\d{1,2}\)|[a-z])+$", re.I)

VERDICT_CODE = "番号"
VERDICT_SITE = "站点作品号"
VERDICT_UNCLEAR = "存疑"
VERDICT_KEEP = "保留"


def canonical_code(value: str) -> str | None:
    """把番号的各种写法归一成 `ABC-123`；解析不出返回 None。"""
    text = (value or "").strip()
    if not text or _UUID_LIKE.search(text):
        return None
    text = _EXTENSION.sub("", text)
    date = _DATE_CODE.search(text)
    if date:
        return f"{date.group(1)}-{date.group(2)}"
    body = _VERSION_TAIL.sub("", _QUALITY_HEAD.sub("", text))
    shape = _LETTER_CODE.match(body)
    if not shape:
        return None
    return f"{shape.group(1).upper()}-{int(shape.group(2)):03d}"


def site_post_id(value: str) -> str | None:
    match = _SITE_POST.match(_EXTENSION.sub("", (value or "").strip()))
    return f"{match.group(1).lower()}-{match.group(2)}" if match else None


def code_from_filename(name: str) -> str | None:
    """文件名带分卷、画质和重复计数，剥掉噪声后再归一。"""
    stem = _EXTENSION.sub("", (name or "").strip())
    return canonical_code(stem) or canonical_code(_FILE_NOISE.sub("", stem))


def is_filesystem_path(path: str) -> bool:
    """pixiv 等在线身份的 path 是 URL，不参与目录投影判定。"""
    return bool(path) and not re.match(r"^[a-z][a-z0-9+.-]*://", path, re.I)


def classify(name: str, assets: list) -> tuple[str, str, str]:
    """返回 (判定, 归一标识, 理由)。只有文件级证据成立才判为可清理。"""
    post = site_post_id(name)
    code = canonical_code(name)
    if not post and not code:
        return VERDICT_KEEP, "", "名字不是番号形态"
    if not all(is_filesystem_path(str(row["path"] or "")) for row in assets):
        return VERDICT_KEEP, "", "存在 URL 身份（如 pixiv 画师），不是发行目录"

    identity = post or code or ""
    hit = any(
        (site_post_id(str(row["name"] or "")) or code_from_filename(str(row["name"] or "")))
        == identity
        or str(row["code"] or "").upper() == identity
        for row in assets
    )
    if not hit:
        return (VERDICT_UNCLEAR, identity,
                "名字像番号，但目录内没有同番号文件；可能是真实账号名")
    if post:
        return VERDICT_SITE, identity, f"目录与文件同为站点作品号 {identity}"
    return VERDICT_CODE, identity, f"目录与文件同为番号 {identity}"


FIELDS = ("entity_id", "creator", "verdict", "identity", "assets", "sample_path",
          "code_action", "reason")


def collect(connection: sqlite3.Connection) -> list[dict[str, object]]:
    # 用独立 cursor 取具名列，不改调用方连接的 row_factory。
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row
    rows: list[dict[str, object]] = []
    creators = cursor.execute(
        "SELECT id,canonical_name FROM entity WHERE kind='creator' ORDER BY canonical_name"
    ).fetchall()
    for creator in creators:
        assets = cursor.execute(
            """SELECT a.id,a.name,a.path,a.code,a.medium FROM asset_entity ae
               JOIN asset a ON a.id=ae.asset_id
               WHERE ae.entity_id=? AND ae.role='creator' ORDER BY a.id""",
            (creator["id"],),
        ).fetchall()
        if not assets:
            continue
        verdict, identity, reason = classify(str(creator["canonical_name"]), assets)
        if verdict == VERDICT_KEEP:
            continue
        missing = sum(1 for row in assets if not str(row["code"] or "").strip())
        rows.append({
            "entity_id": int(creator["id"]),
            "creator": str(creator["canonical_name"]),
            "verdict": verdict,
            "identity": identity,
            "assets": len(assets),
            "sample_path": str(assets[0]["path"] or ""),
            "code_action": (f"补 code {identity}（{missing} 条为空）"
                            if verdict == VERDICT_CODE and missing else ""),
            "reason": reason,
        })
    return rows


def apply_rows(connection: sqlite3.Connection, rows: list[dict[str, object]]) -> dict[str, int]:
    """只清理有文件级证据的行；存疑一律留给人工。"""
    counts = {"links": 0, "entities": 0, "codes": 0, "flat": 0}
    for row in rows:
        if row["verdict"] not in (VERDICT_CODE, VERDICT_SITE):
            continue
        entity_id = int(row["entity_id"])
        identity = str(row["identity"])
        asset_ids = [
            int(item[0]) for item in connection.execute(
                "SELECT asset_id FROM asset_entity WHERE entity_id=? AND role='creator'",
                (entity_id,))
        ]
        # 番号是作品标识，写进 code；站点作品号不是番号，写进去只会污染刮削队列。
        if row["verdict"] == VERDICT_CODE:
            for asset_id in asset_ids:
                connection.execute(
                    "UPDATE asset SET code=? WHERE id=? AND (code IS NULL OR code='')",
                    (identity, asset_id))
                counts["codes"] += connection.execute("SELECT changes()").fetchone()[0]
        connection.execute(
            "DELETE FROM asset_entity WHERE entity_id=? AND role='creator'", (entity_id,))
        counts["links"] += connection.execute("SELECT changes()").fetchone()[0]
        for asset_id in asset_ids:
            connection.execute(
                "UPDATE asset SET creator=NULL WHERE id=? AND creator=?",
                (asset_id, row["creator"]))
            counts["flat"] += connection.execute("SELECT changes()").fetchone()[0]
        # 只删掉再无任何关系的实体，避免连带清掉别处仍在引用的身份。
        connection.execute(
            "DELETE FROM entity WHERE id=? AND kind='creator' "
            "AND NOT EXISTS(SELECT 1 FROM asset_entity WHERE entity_id=?)",
            (entity_id, entity_id))
        counts["entities"] += connection.execute("SELECT changes()").fetchone()[0]
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="清理被投影成创作者的番号目录名")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--review-csv", type=Path,
                        default=GENERATED_DIR / "code-creator-review.csv")
    parser.add_argument("--apply", action="store_true", help="写 ledger；默认只出 CSV")
    parser.add_argument("--backup", type=Path, help="--apply 必需：写库前的 SQLite 备份路径")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    connection = sqlite3.connect(args.db)
    rows = collect(connection)
    print(f"命中番号形态的创作者 {len(rows)} 个")
    print("  判定分布：", dict(Counter(str(row["verdict"]) for row in rows)))

    if args.apply:
        sqlite_backup(args.db, args.backup)
        print(f"已备份 → {args.backup}")
        connection.execute("BEGIN IMMEDIATE")
        try:
            counts = apply_rows(connection, rows)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        print(f"已写入：删创作者关系 {counts['links']} 条、删实体 {counts['entities']} 个、"
              f"补 code {counts['codes']} 条、清扁平字段 {counts['flat']} 条")
    connection.close()

    write_rows(args.review_csv, FIELDS, rows)
    print(f"复核 CSV → {args.review_csv}")
    if not args.apply:
        print("这是预览：未写 ledger。确认后再加 --apply --backup。")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
