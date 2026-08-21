#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""女优高清头像缺口审计：只产 CSV，不写 ledger、不落任何头像文件。

交接背景（docs/OX-WINDOWS-JAV.md 第 4 节）：ledger 已完成中文规范名本地化，
界面请求 `generated/avatars/performer-<entity_id>.img`，缺文件时回落到视频抽帧。
本脚本回答两件事：

1. 哪些 performer 缺头像文件；Gfriends 图库里按质量档位排序的最优来源是什么，
   尺寸与完整性经逐张下载实测，不用索引推断冒充实测。
2. 实体合并后遗留在旧 ID 下的孤立头像文件：其 provenance 记录的名字能唯一命中
   当前实体、且当前目标文件不存在时，才列为 `orphan_relink` 复核候选；
   不覆盖、不删除旧文件。命中不唯一或目标已存在一律只记录原因。

名字匹配次序按交接单固定：canonical name → alias → metadata_json.name_localization.jp。
「已核实旧名」由 alias 承载——localize_performer_names.py 把改名前的日文名、罗马字、
假名全部写进了 entity_alias，无需另设存储。

从 `agent/claude/performer-portraits` 的 import_performer_portraits.py 迁入且语义
不变的部分：Gfriends Filetree 索引与目录名首字符质量档位排序、Pillow 完整校验、
长边 ≥500 / 短边 ≥300 门槛（竖构图人像不能套方图的短边 512 门槛）、provenance
字段口径、HostLimiter 按主机限速、网络异常降级为跳过而不是中断整批。

边界：
- ledger 以 SQLite 只读 URI 打开，本脚本没有任何写库路径；
- 判定只写入 CSV；`--resume` 跳过已判定行，重试 error 行（网络失败的固定记法）。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sqlite3
import threading
import time
import urllib.parse
import concurrent.futures as futures
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.http import HttpRequest, HttpTransport, HttpxTransport

GFRIENDS_RAW = "https://raw.githubusercontent.com/gfriends/gfriends/master/"
# 目录名首字符即质量档位；0 最优，z（DMM 官方小图）最次。
QUALITY_ORDER = "0123456789abcdefghijklmnopqrstuvwxyz"
AVATAR_FILE_RE = re.compile(r"^performer-(\d+)\.img$")
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
_LIMITER: "HostLimiter | None" = None

FIELDS = (
    "section", "entity_id", "current_name", "matched_name", "name_source",
    "gfriends_category", "gfriends_file", "width", "height", "url",
    "verdict", "note", "relink_old_id", "relink_target_id",
)
# 这些判定是结论；error 表示网络层失败，续跑时必须重试。
FINAL_VERDICTS = {
    "ok", "no_match", "rejected",
    "orphan_relink", "orphan_ambiguous", "orphan_target_exists", "orphan_no_provenance",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计女优头像缺口与孤立头像，产出复核 CSV")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--avatars", type=Path, default=GENERATED_DIR / "avatars")
    parser.add_argument("--out", type=Path,
                        default=GENERATED_DIR / "performer-portrait-audit.csv")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-candidates", type=int, default=6,
                        help="每位女优最多实测多少张候选图；按质量档位从优到劣")
    parser.add_argument("--min-long-side", type=int, default=500)
    parser.add_argument("--min-short-side", type=int, default=300)
    parser.add_argument("--resume", action="store_true",
                        help="跳过 CSV 里已判定的行；error 行重试")
    return parser


# ---------------------------------------------------------------- Gfriends


def load_gfriends(transport: HttpTransport) -> dict[str, list[tuple[str, str]]]:
    """日文名 -> [(来源目录, 文件名)]，按质量档位排序，最优在前。"""
    response = transport(
        HttpRequest("GET", GFRIENDS_RAW + "Filetree.json",
                    {"Accept": "application/json"}),
        60, 32 * 1024 * 1024,
    )
    if response.status != 200:
        raise RuntimeError(f"Gfriends 索引不可用：HTTP {response.status}")
    content = json.loads(response.body)["Content"]
    index: dict[str, list[tuple[str, str]]] = {}
    for category, items in content.items():
        for display_name, stored in items.items():
            # 键是展示名（可能是别名），值才是实际文件；两者未必相同。
            key = display_name.rsplit(".", 1)[0]
            index.setdefault(key, []).append((category, stored.split("?")[0]))
    for key in index:
        index[key].sort(key=lambda pair: QUALITY_ORDER.find(pair[0][0].lower()))
    return index


def gfriends_url(category: str, filename: str) -> str:
    return (GFRIENDS_RAW + "Content/" + urllib.parse.quote(category)
            + "/" + urllib.parse.quote(filename))


class HostLimiter:
    """按主机分别限速：每个主机一把锁、一个下次可发时刻。"""

    def __init__(self, intervals: dict[str, float]):
        self._intervals = intervals
        self._locks = {host: threading.Lock() for host in intervals}
        self._next: dict[str, float] = {host: 0.0 for host in intervals}

    def _key(self, url: str) -> str | None:
        hostname = urllib.parse.urlsplit(url).hostname or ""
        for host in self._intervals:
            if host in hostname:
                return host
        return None

    def wait(self, url: str) -> None:
        key = self._key(url)
        if key is None:
            return
        with self._locks[key]:
            now = time.monotonic()
            delay = self._next[key] - now
            if delay > 0:
                time.sleep(delay)
                now = time.monotonic()
            self._next[key] = now + self._intervals[key]


def fetch(transport: HttpTransport, url: str, accept: str,
          timeout: float = 30, max_bytes: int = 4 * 1024 * 1024):
    """联网取一次；任何网络层异常都降级为 None，不让单条 TLS 抖动打断整批。"""
    active = limiter()
    if active is not None:
        active.wait(url)
    try:
        return transport(
            HttpRequest("GET", url, {"Accept": accept, "User-Agent": BROWSER_UA}),
            timeout, max_bytes)
    except Exception:
        return None


def limiter() -> "HostLimiter | None":
    return _LIMITER


# ---------------------------------------------------------------- 图像


def inspect_image(data: bytes) -> tuple[tuple[int, int], str] | None:
    """Pillow 完整校验并由解码格式定 MIME；SVG 与损坏数据一律拒绝。"""
    try:
        with Image.open(io.BytesIO(data)) as image:
            size = image.size
            image_format = (image.format or "").upper()
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        return None
    content_type = {"JPEG": "image/jpeg", "PNG": "image/png"}.get(image_format)
    return (size, content_type) if content_type else None


def acceptable(size: tuple[int, int], min_long: int, min_short: int) -> bool:
    """头像是竖构图，宽度天然小；用长短边分别判定，不能套方图的短边门槛。"""
    return max(size) >= min_long and min(size) >= min_short


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower()


# ---------------------------------------------------------------- ledger（只读）


def open_readonly(db_path: Path) -> sqlite3.Connection:
    # mode=ro 让「绝不写库」成为数据库层的硬保证，而不只是约定。
    uri = "file:" + urllib.parse.quote(db_path.resolve().as_posix()) + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def load_performers(connection: sqlite3.Connection) -> list[dict]:
    """全部 performer 及其名字链：canonical、alias（含已核实旧名）、本地化 jp。"""
    records: dict[int, dict] = {}
    for entity_id, canonical, raw_metadata in connection.execute(
            "SELECT id, canonical_name, metadata_json FROM entity WHERE kind='performer'"):
        jp = ""
        try:
            localization = (json.loads(raw_metadata or "{}")
                            .get("name_localization") or {})
            jp = localization.get("jp") or ""
        except (TypeError, ValueError):
            jp = ""
        records[entity_id] = {
            "entity_id": entity_id, "canonical": canonical or "",
            "aliases": [], "jp": jp,
        }
    for entity_id, alias in connection.execute(
            "SELECT entity_id, alias FROM entity_alias ORDER BY alias"):
        record = records.get(entity_id)
        if record is not None and alias.strip():
            record["aliases"].append(alias.strip())
    return list(records.values())


def lookup_chain(record: dict) -> list[tuple[str, str]]:
    """有序去重的 (名字, 来源档位)；次序即交接单规定的匹配次序。"""
    chain: list[tuple[str, str]] = [(record["canonical"], "canonical")]
    chain += [(alias, "alias") for alias in record["aliases"]]
    if record["jp"]:
        chain.append((record["jp"], "localization_jp"))
    seen: set[str] = set()
    ordered: list[tuple[str, str]] = []
    for name, source in chain:
        key = normalized(name)
        if key and key not in seen:
            seen.add(key)
            ordered.append((name, source))
    return ordered


# ---------------------------------------------------------------- 缺口审计


def missing_targets(connection: sqlite3.Connection, avatar_dir: Path,
                    limit: int) -> list[dict]:
    """只选缺 performer-<id>.img 的 performer；有作品多者优先。"""
    counts = {entity_id: n for entity_id, n in connection.execute(
        "SELECT entity_id, count(*) FROM asset_entity GROUP BY entity_id")}
    targets = [record for record in load_performers(connection)
               if not (avatar_dir / f"performer-{record['entity_id']}.img").exists()]
    targets.sort(key=lambda record: (-counts.get(record["entity_id"], 0),
                                     record["entity_id"]))
    return targets[:limit] if limit else targets


def audit_missing(record: dict, index: dict, transport: HttpTransport,
                  args: argparse.Namespace) -> dict:
    row = {field: "" for field in FIELDS}
    row["section"] = "missing"
    row["entity_id"] = record["entity_id"]
    row["current_name"] = record["canonical"]
    entries: list[tuple[str, str]] | None = None
    for name, source in lookup_chain(record):
        candidate = index.get(name.strip())
        if candidate:
            row["matched_name"] = name
            row["name_source"] = source
            entries = candidate
            break
    if not entries:
        row["verdict"] = "no_match"
        row["note"] = "Gfriends 未收录该名字链上的任何写法"
        return row
    tried = 0
    for category, filename in entries[:max(args.max_candidates, 1)]:
        response = fetch(transport, gfriends_url(category, filename), "image/*",
                         30, 16 * 1024 * 1024)
        if response is None or response.status != 200:
            if response is None:
                # 与 fetch 的降级口径一致：网络失败可续跑，不算来源结论。
                row["verdict"] = "error"
                row["note"] = f"下载失败：{category}/{filename}"
                return row
            tried += 1
            continue
        inspected = inspect_image(response.body)
        if not inspected:
            tried += 1
            continue
        size, _content_type = inspected
        if not acceptable(size, args.min_long_side, args.min_short_side):
            tried += 1
            continue
        row.update({
            "gfriends_category": category,
            "gfriends_file": filename,
            "width": size[0], "height": size[1],
            "url": gfriends_url(category, filename),
            "verdict": "ok",
            "note": f"{len(entries)} 个来源可选，实测第 {tried + 1} 张合格",
        })
        return row
    row["verdict"] = "rejected"
    row["note"] = f"前 {tried} 张候选未过完整性或尺寸门槛"
    return row


# ---------------------------------------------------------------- 孤立头像审计


def audit_orphans(connection: sqlite3.Connection, avatar_dir: Path) -> list[dict]:
    """performer-<已删除 ID>.img：provenance 名唯一命中且目标缺失才列 relink。"""
    disk_ids: set[int] = set()
    for path in avatar_dir.glob("performer-*.img"):
        matched = AVATAR_FILE_RE.match(path.name)
        if matched:
            disk_ids.add(int(matched.group(1)))
    live_ids = {record["entity_id"] for record in load_performers(connection)}
    # 当前实体的全部可解析名 -> 实体 ID 集合，用于 provenance 名的唯一性判定。
    name_index: dict[str, set[int]] = {}
    for record in load_performers(connection):
        for name, _source in lookup_chain(record):
            name_index.setdefault(normalized(name), set()).add(record["entity_id"])

    rows: list[dict] = []
    for old_id in sorted(disk_ids - live_ids):
        row = {field: "" for field in FIELDS}
        row["section"] = "orphan"
        row["relink_old_id"] = old_id
        provenance_path = avatar_dir / f"performer-{old_id}.img.provenance.json"
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            matched_name = (provenance.get("matched_name") or "").strip()
        except (OSError, ValueError):
            matched_name = ""
        if not matched_name:
            row["verdict"] = "orphan_no_provenance"
            row["note"] = f"provenance 不可读：{provenance_path.name}"
            rows.append(row)
            continue
        hits = name_index.get(normalized(matched_name), set())
        row["matched_name"] = matched_name
        row["name_source"] = "provenance"
        # provenance 原文字段原样保留进 CSV，复核通过后无需重新取源即可复制文件。
        row["gfriends_category"] = provenance.get("gfriends_category", "")
        row["gfriends_file"] = provenance.get("gfriends_file", "")
        row["url"] = provenance.get("upstream_url", "")
        row["width"] = provenance.get("width", "")
        row["height"] = provenance.get("height", "")
        if len(hits) > 1:
            row["verdict"] = "orphan_ambiguous"
            row["note"] = "provenance 名命中多个当前实体：" + "、".join(
                str(hit) for hit in sorted(hits))
        elif not hits:
            row["verdict"] = "orphan_no_provenance"
            row["note"] = "provenance 名在当前 ledger 无唯一命中"
        else:
            target_id = next(iter(hits))
            row["relink_target_id"] = target_id
            if (avatar_dir / f"performer-{target_id}.img").exists():
                row["verdict"] = "orphan_target_exists"
                row["note"] = f"目标 performer-{target_id}.img 已存在，不覆盖"
            else:
                row["verdict"] = "orphan_relink"
                row["note"] = f"可回链到实体 {target_id}；复制需主 agent 复核后执行"
        rows.append(row)
    return rows


# ---------------------------------------------------------------- 汇总输出


def read_prior(path: Path) -> tuple[list[dict], set[int]]:
    """读上一轮 CSV：(保留的已判定行, 其中缺口区已判定实体)。"""
    kept: list[dict] = []
    done: set[int] = set()
    if not path.is_file():
        return kept, done
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for old in csv.DictReader(handle):
            if old.get("section") == "missing" and old.get("verdict") in FINAL_VERDICTS:
                done.add(int(old["entity_id"]))
            elif old.get("section") == "missing":
                continue  # error 行重试，不保留旧值
            kept.append(old)
    return kept, done


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDS})


def run(args: argparse.Namespace, transport: HttpTransport | None = None) -> int:
    global _LIMITER
    # 静态图库走 GitHub raw，不限速；本脚本没有别的远端主机。
    _LIMITER = HostLimiter({"githubusercontent.com": 0.0})
    owned = transport is None
    client = transport or HttpxTransport()
    try:
        print("拉取 Gfriends 索引…", flush=True)
        index = load_gfriends(client)
        print(f"索引就绪：{len(index)} 个名字键", flush=True)

        connection = open_readonly(args.db)
        targets = missing_targets(connection, args.avatars, args.limit)
        rows: list[dict] = []
        if args.resume:
            prior, done = read_prior(args.out)
            rows = prior
            targets = [t for t in targets if t["entity_id"] not in done]
            print(f"续跑：已判定 {len(done)} 位，跳过", flush=True)

        # 孤立审计纯本地、确定性：每轮全量重算，替换旧轮的 orphan 行。
        rows = [row for row in rows if row.get("section") != "orphan"]
        orphan_rows = audit_orphans(connection, args.avatars)
        print(f"缺口待审 {len(targets)} 位；孤立头像 {len(orphan_rows)} 个", flush=True)

        guard = threading.Lock()
        finished = 0

        def process_one(record: dict) -> dict:
            return audit_missing(record, index, client, args)

        with futures.ThreadPoolExecutor(max(1, args.workers)) as pool:
            for row in pool.map(process_one, targets):
                with guard:
                    rows.append(row)
                    finished += 1
                    # 边跑边落盘：断电或断网不该丢掉已完成的部分。
                    if finished % 20 == 0:
                        write_csv(args.out, [*rows, *orphan_rows])
                        ok = sum(1 for r in rows if r.get("verdict") == "ok")
                        print(f"  {finished}/{len(targets)} 已判定，命中 {ok}", flush=True)
        rows.extend(orphan_rows)
        write_csv(args.out, rows)
        connection.close()

        summary = Counter(row["verdict"] for row in rows)
        print(f"审计 CSV → {args.out}")
        print("判定分布：" + "、".join(f"{k} {v}" for k, v in summary.most_common()))
        relinks = summary.get("orphan_relink", 0)
        if relinks:
            print(f"其中 orphan_relink {relinks} 条：仅候选，复制文件须主 agent 复核后执行。")
        return 0
    finally:
        if owned:
            client.close()


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
