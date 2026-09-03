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
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR
from peach.follow_sources import FollowSourceError, build_connector
from peach.review_csv import write_rows
from peach.scripting import (
    BACKUP_REQUIRED, add_ledger_write_args, open_for_write, open_readonly,
)

FIELDS = ("item_id", "external_id", "url", "result", "tag_types", "note")

#: 同一主机的最小请求间隔。rule34.xxx 自己公布的口径是每 60 秒 60 次，也就是
#: 每次至少 1 秒；留一点余量。首轮按 0.35 秒跑过一次：400 条里 372 条「帖子页
#: 没有解析出类型」——不是这些帖子没有类型，是被限流挡了，`_detail_tag_types`
#: 把非 200 吞成了空字典。速度换来的全是白跑的请求。
DEFAULT_DELAY = 1.1
#: 连续这么多条取不到就认定是被限流，而不是这一段恰好都没类型。
MISS_STREAK_LIMIT = 8
#: 限流后的静默时长，按站方公布的窗口取满一格。
COOLDOWN_SECONDS = 60.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补齐 rule34.xxx 追更条目的标签类型")
    add_ledger_write_args(parser)
    parser.add_argument("--out", type=Path,
                        default=GENERATED_DIR / "rule34-tag-type-backfill.csv")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 条，0 为全部")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
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


def merge_tag_types(metadata: dict, tag_types: dict[str, str]) -> str:
    merged = dict(metadata)
    merged["tag_types"] = dict(tag_types)
    return json.dumps(merged, ensure_ascii=False)


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        print(BACKUP_REQUIRED, file=sys.stderr)
        return 2
    with open_readonly(args.db) as reader:
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
        # 五十分钟——而这一趟本来就是可反复运行的。备份由 `open_for_write` 落。
        writer = open_for_write(args)
        print(f"备份：{args.backup}", flush=True)
        before = writer.execute("SELECT COUNT(*) FROM follow_item").fetchone()[0]

    connector = build_connector("rule34xxx")
    log: list[dict] = []
    pending_updates: list[tuple[str, int]] = []
    written = 0
    fetched = 0
    miss_streak = 0

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
            miss_streak += 1
            log.append({"item_id": row["id"], "external_id": post_id, "url": row["url"],
                        "result": "未取得", "tag_types": "", "note": "帖子页没有解析出类型"})
            if miss_streak >= MISS_STREAK_LIMIT:
                # 连着这么多条都取不到，几乎不可能是内容碰巧都没类型。继续按原速
                # 跑下去只是把整个队列烧成「未取得」，下一轮还得从头再问一遍。
                print(f"连续 {miss_streak} 条取不到，按限流处理，静默 "
                      f"{COOLDOWN_SECONDS:.0f} 秒", flush=True)
                flush()
                write_rows(args.out, FIELDS, log, atomic=True)
                time.sleep(COOLDOWN_SECONDS)
                miss_streak = 0
            continue
        miss_streak = 0
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
