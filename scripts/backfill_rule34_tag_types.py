#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""给已入库的 rule34.xxx 追更条目补上标签类型。

rule34.xxx 的 posts DAPI 只回一串扁平标签，类型（general／artist／character／
copyright／metadata）只在帖子页的 `#tag-sidebar` 上。连接器早就会读它，但那是
后加的：2152 条里只有 40 条带 `tag_types`，其余 2112 条一条类型也没有。

这直接造成两个可见后果：

- 卡片上没有标签。`_item_tags` 只放行**明确标为 general** 的标签，没有类型就
  一个都不放行——而详情页用的是 `_item_all_tags`，所以「点进去里面是有的」。
- 详情标签全是中性色。按类型着色和按 rule34 分类排序都要有类型才成立。

常规「检查更新」只看第一页，补不到历史条目，所以要这一趟。抓取逻辑不重写，
直接复用连接器的 `_detail_tag_types`：判据只能有一处。

默认 dry-run。`--apply` 必须同时给 `--backup`，与本仓库其它真实写入脚本一致。
可反复运行：已经有类型的条目直接跳过，中断后接着跑就是。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.follow_sources import FollowSourceError, build_connector
from peach.review_csv import write_rows

FIELDS = ("item_id", "external_id", "url", "result", "tag_types", "note")

#: 同一主机的最小请求间隔。rule34.xxx 公布的口径是每 60 秒 60 次；留一倍余量。
DEFAULT_DELAY = 1.5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补齐 rule34.xxx 追更条目的标签类型")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--out", type=Path,
                        default=GENERATED_DIR / "rule34-tag-type-backfill.csv")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 条，0 为全部")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument("--apply", action="store_true", help="真正写入账本")
    parser.add_argument("--backup", type=Path, help="写入前的账本备份路径；--apply 必须给")
    return parser


def pending_rows(connection: sqlite3.Connection, limit: int) -> list[dict]:
    """待补条目：rule34xxx 来源、metadata 里还没有 tag_types 的。

    判据落在解析后的 JSON 上而不是 `LIKE '%tag_types%'`：空字典也算没有类型，
    而它在字符串里是命中的。
    """
    rows = []
    query = (
        "SELECT i.id, i.external_id, i.url, i.metadata_json FROM follow_item i"
        " JOIN follow_source s ON s.id=i.source_id"
        " WHERE s.provider='rule34xxx' ORDER BY i.id"
    )
    for row in connection.execute(query):
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except ValueError:
            metadata = {}
        if isinstance(metadata.get("tag_types"), dict) and metadata["tag_types"]:
            continue
        rows.append({"id": row["id"], "external_id": str(row["external_id"] or ""),
                     "url": row["url"], "metadata": metadata})
        if limit and len(rows) >= limit:
            break
    return rows


def backup_database(source: Path, target: Path) -> None:
    """用 SQLite 自己的备份 API，不要 `shutil.copy2`。

    账本是 WAL 模式：已提交但尚未 checkpoint 的事务在 `-wal` 里，只复制主库文件
    会得到一份**少了最近改动**的账本，而它看起来完全正常——恢复时才发现回退了
    一截。备份 API 会把 WAL 一并合进目标库。
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    with (sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as reader,
          sqlite3.connect(target) as writer):
        reader.backup(writer)


def merge_tag_types(metadata: dict, tag_types: dict[str, str]) -> str:
    merged = dict(metadata)
    merged["tag_types"] = dict(tag_types)
    return json.dumps(merged, ensure_ascii=False)


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        print("--apply 必须同时给 --backup", file=sys.stderr)
        return 2
    database = args.db.resolve()
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as reader:
        reader.row_factory = sqlite3.Row
        rows = pending_rows(reader, args.limit)
        total = reader.execute(
            "SELECT COUNT(*) FROM follow_item i JOIN follow_source s ON s.id=i.source_id"
            " WHERE s.provider='rule34xxx'").fetchone()[0]
    print(f"rule34xxx 共 {total} 条，待补 {len(rows)} 条", flush=True)
    if not rows:
        return 0

    writer: sqlite3.Connection | None = None
    before = after = 0
    if args.apply:
        # 备份先做，批量写入才敢分批落。整轮跑完再一次性写，中断一次就等于白跑
        # 五十分钟——而这一趟本来就是可反复运行的。
        backup_database(database, args.backup)
        print(f"备份：{args.backup}", flush=True)
        writer = sqlite3.connect(database)
        before = writer.execute("SELECT COUNT(*) FROM follow_item").fetchone()[0]

    connector = build_connector("rule34xxx")
    log: list[dict] = []
    pending_updates: list[tuple[str, int]] = []
    written = 0
    fetched = 0

    def flush() -> None:
        nonlocal written
        if writer is None or not pending_updates:
            return
        writer.executemany("UPDATE follow_item SET metadata_json=? WHERE id=?",
                           pending_updates)
        writer.commit()
        written += len(pending_updates)
        pending_updates.clear()

    for index, row in enumerate(rows, 1):
        post_id = row["external_id"]
        if not post_id.isdigit():
            log.append({"item_id": row["id"], "external_id": post_id, "url": row["url"],
                        "result": "跳过", "tag_types": "", "note": "external_id 不是帖子号"})
            continue
        try:
            tag_types = connector._detail_tag_types(post_id)
        except (FollowSourceError, OSError) as error:
            log.append({"item_id": row["id"], "external_id": post_id, "url": row["url"],
                        "result": "未取得", "tag_types": "",
                        "note": f"{type(error).__name__}: {error}"[:120]})
            time.sleep(args.delay)
            continue
        time.sleep(args.delay)
        if not tag_types:
            # 取不到不等于这条没有类型：留待下一轮，不写空字典冒充已补。
            log.append({"item_id": row["id"], "external_id": post_id, "url": row["url"],
                        "result": "未取得", "tag_types": "", "note": "帖子页没有解析出类型"})
            continue
        fetched += 1
        row["merged"] = merge_tag_types(row["metadata"], tag_types)
        pending_updates.append((row["merged"], row["id"]))
        log.append({"item_id": row["id"], "external_id": post_id, "url": row["url"],
                    "result": "取得", "tag_types": json.dumps(tag_types, ensure_ascii=False),
                    "note": ""})
        if index % 50 == 0:
            flush()
            print(f"{index}/{len(rows)}：已取得 {fetched}，已写入 {written}", flush=True)
            write_rows(args.out, FIELDS, log, atomic=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_rows(args.out, FIELDS, log, atomic=True)
    print(f"取得 {fetched} 条 → {args.out}", flush=True)

    if writer is None:
        print(f"dry-run：可写入 {fetched} 条；加 --apply --backup 才真正写入")
        return 0
    flush()
    after = writer.execute("SELECT COUNT(*) FROM follow_item").fetchone()[0]
    typed = writer.execute(
        "SELECT COUNT(*) FROM follow_item i JOIN follow_source s ON s.id=i.source_id"
        " WHERE s.provider='rule34xxx' AND i.metadata_json LIKE '%tag_types%'"
    ).fetchone()[0]
    writer.close()
    # 条数必须不变：这一趟只补 metadata，不新增也不删除条目。
    print(f"已更新 {written} 条；follow_item {before} → {after}；"
          f"rule34xxx 带类型 {typed}/{total}")
    return 0 if before == after else 1


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
