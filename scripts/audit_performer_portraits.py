#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""女优高清头像缺口审计：只产候选与缓存证据，不写 ledger、不安装头像。

交接背景（docs/OX-WINDOWS-JAV.md 第 4 节）：ledger 已完成中文规范名本地化，
界面请求 `generated/avatars/performer-<entity_id>.img`，缺文件时回落到视频抽帧。
本脚本回答两件事：

1. 哪些 performer 缺头像文件；Gfriends 图库里按质量档位排序的最优来源是什么，
   尺寸、格式、完整性和 SHA-256 经逐张下载实测，不用索引推断冒充实测。
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
- 外部图只进入候选专用内容寻址缓存，不写 `generated/avatars`；
- 判定写入审计、`/review` 候选与来源健康 CSV；`--resume` 跳过已判定行，
  重试 error 和缺少 P2 缓存/provenance 的旧版 ok 行。
"""
from __future__ import annotations

import argparse
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

from peach.avatar_provider import (
    POLICY_VERSION,
    AvatarCandidateCache,
    acceptable_avatar,
    atomic_write,
    inspect_avatar,
    installed_avatar_hashes,
    mark_duplicate_candidates,
    provenance_now,
)
from peach.catalog_rules import is_jav_code
from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.http import HttpRequest, HttpTransport, HttpxTransport
from peach.review_csv import read_rows, write_rows

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
    "mime_type", "sha256", "cache_path", "provenance_path", "policy_version",
    "duplicate_of_entity_id", "verdict", "note", "relink_old_id", "relink_target_id",
)
# 这些判定是结论；error 表示网络层失败，续跑时必须重试。
FINAL_VERDICTS = {
    "ok", "no_match", "rejected",
    "duplicate", "orphan_relink", "orphan_ambiguous", "orphan_target_exists",
    "orphan_no_provenance",
}
CANDIDATE_FIELDS = (
    "entity_id", "current_name", "matched_name", "name_source", "provider",
    "source_kind", "source_url", "external_id", "gfriends_category",
    "gfriends_file", "width", "height", "mime_type", "sha256", "cache_path",
    "provenance_path", "policy_version", "verdict", "avatar_url", "evidence",
)
HEALTH_FIELDS = (
    "source", "profile", "policy_version", "index_cache_reused", "index_cache_stale",
    "index_fetched",
    "attempted", "snapshot_reused", "fetched", "succeeded", "no_match",
    "rejected", "duplicates", "errors", "bytes_fetched", "elapsed_ms",
    "last_error_kind", "last_error_status", "last_error_message",
)


def build_parser() -> argparse.ArgumentParser:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    parser = argparse.ArgumentParser(description="审计女优头像缺口与孤立头像，产出复核 CSV")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--avatars", type=Path, default=GENERATED_DIR / "avatars")
    parser.add_argument("--out", type=Path,
                        default=GENERATED_DIR / "performer-portrait-audit.csv")
    parser.add_argument(
        "--candidates", type=Path,
        default=GENERATED_DIR / f"performer-avatar-candidate-{stamp}.csv",
    )
    parser.add_argument(
        "--health", type=Path,
        default=GENERATED_DIR / f"performer-avatar-source-health-{stamp}.csv",
    )
    parser.add_argument(
        "--cache-dir", type=Path,
        default=GENERATED_DIR / "provider-cache" / "performer-avatars" / "gfriends",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-candidates", type=int, default=6,
                        help="每位女优最多实测多少张候选图；按质量档位从优到劣")
    parser.add_argument("--min-long-side", type=int, default=500)
    parser.add_argument("--min-short-side", type=int, default=300)
    parser.add_argument("--resume", action="store_true",
                        help="跳过 CSV 里已判定的行；error 行重试")
    parser.add_argument("--refresh", action="store_true",
                        help="忽略 Gfriends 索引和图片请求缓存")
    return parser


# ---------------------------------------------------------------- Gfriends


class SourceHealth:
    def __init__(self):
        self.started = time.perf_counter()
        self._lock = threading.Lock()
        self.row: dict[str, object] = {
            "source": "gfriends", "profile": "external_fallback",
            "policy_version": POLICY_VERSION,
            "index_cache_reused": 0, "index_cache_stale": 0, "index_fetched": 0,
            "attempted": 0,
            "snapshot_reused": 0, "fetched": 0, "succeeded": 0,
            "no_match": 0, "rejected": 0, "duplicates": 0, "errors": 0,
            "bytes_fetched": 0, "elapsed_ms": 0,
            "last_error_kind": "", "last_error_status": "",
            "last_error_message": "",
        }

    def add(self, field: str, amount: int = 1) -> None:
        with self._lock:
            self.row[field] = int(self.row[field]) + amount

    def error(self, kind: str, status: int | str = "", message: str = "") -> None:
        with self._lock:
            self.row["errors"] = int(self.row["errors"]) + 1
            self.row["last_error_kind"] = kind
            self.row["last_error_status"] = status
            self.row["last_error_message"] = message[:500]

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            row = dict(self.row)
        row["elapsed_ms"] = round((time.perf_counter() - self.started) * 1000)
        return row


def parse_gfriends(body: bytes) -> dict[str, list[tuple[str, str]]]:
    content = json.loads(body)["Content"]
    index: dict[str, list[tuple[str, str]]] = {}
    for category, items in content.items():
        for display_name, stored in items.items():
            # 键是展示名（可能是别名），值才是实际文件；两者未必相同。
            key = normalized(display_name.rsplit(".", 1)[0])
            index.setdefault(key, []).append((category, stored.split("?")[0]))
    for key in index:
        index[key].sort(key=lambda pair: quality_key(*pair))
    return index


def load_gfriends(transport: HttpTransport) -> dict[str, list[tuple[str, str]]]:
    """日文名 -> [(来源目录, 文件名)]，按质量档位排序，最优在前。"""
    response = transport(
        HttpRequest("GET", GFRIENDS_RAW + "Filetree.json",
                    {"Accept": "application/json"}),
        60, 32 * 1024 * 1024,
    )
    if response.status != 200:
        raise RuntimeError(f"Gfriends 索引不可用：HTTP {response.status}")
    return parse_gfriends(response.body)


#: 索引缓存的保鲜期。Gfriends 是持续增补的图库，而这份缓存原本永不过期——只要文件在
#: 就一直复用，于是快照那天没收录的人会被判成 `no_match`，此后每次重跑都照抄同一个
#: 结论，再也不会被重新审视。实测：2026-08-25 的缓存里没有「釈アリス」，当天之后
#: Gfriends 加了她（两份索引正好差这一条），但本地怎么跑都还是找不到。
#:
#: 一天是个折中：图库按天更新，而这个脚本是长跑批处理，不该每次启动都拉 6 MB。
INDEX_MAX_AGE_SECONDS = 24 * 3600


def _index_cache_age(cache_path: Path) -> float | None:
    try:
        return max(0.0, time.time() - cache_path.stat().st_mtime)
    except OSError:
        return None


def load_gfriends_cached(
    transport: HttpTransport, cache_dir: Path, refresh: bool, health: SourceHealth,
) -> dict[str, list[tuple[str, str]]]:
    cache_path = cache_dir / "gfriends-filetree.json"
    age = _index_cache_age(cache_path)
    stale = age is None or age > INDEX_MAX_AGE_SECONDS
    if not refresh and not stale and cache_path.is_file():
        try:
            index = parse_gfriends(cache_path.read_bytes())
            health.add("index_cache_reused")
            return index
        except (OSError, KeyError, TypeError, ValueError):
            health.error("invalid_index_cache", message=str(cache_path))
    if stale and cache_path.is_file():
        # 记下来：过期而去重取，和「本来就没有缓存」是两回事，健康报告要分得开。
        health.add("index_cache_stale")
    try:
        response = transport(
            HttpRequest("GET", GFRIENDS_RAW + "Filetree.json",
                        {"Accept": "application/json"}),
            60, 32 * 1024 * 1024,
        )
    except Exception as error:
        response = None
        health.error("index_transport", message=str(error))
    if response is not None and response.status == 200:
        try:
            index = parse_gfriends(response.body)
        except (KeyError, TypeError, ValueError) as error:
            health.error("index_payload", status=200, message=str(error))
        else:
            atomic_write(cache_path, response.body)
            health.add("index_fetched")
            health.add("bytes_fetched", len(response.body))
            return index
    elif response is not None:
        health.error("index_http", status=response.status,
                     message=f"Gfriends index HTTP {response.status}")
    if cache_path.is_file():
        try:
            index = parse_gfriends(cache_path.read_bytes())
            health.add("index_cache_reused")
            return index
        except (OSError, KeyError, TypeError, ValueError):
            pass
    raise RuntimeError("Gfriends 索引不可用，且没有有效本地缓存")


def gfriends_url(category: str, filename: str) -> str:
    return (GFRIENDS_RAW + "Content/" + urllib.parse.quote(category)
            + "/" + urllib.parse.quote(filename))


def quality_key(category: str, filename: str) -> tuple[int, str, str]:
    """已知质量档按约定排序；未知或空目录放最后，不能因 find=-1 抢到最前。"""
    prefix = category[:1].lower()
    rank = QUALITY_ORDER.find(prefix)
    return (rank if rank >= 0 else len(QUALITY_ORDER), category, filename)


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
    avatar = inspect_avatar(data)
    if avatar is None:
        return None
    return (avatar.width, avatar.height), avatar.mime_type


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
            "aliases": [], "jp": jp, "jav": True, "known_works": 0,
        }
    # 作品里有一个 JAV 番号就算 JAV。判据复用 catalog_rules.is_jav_code，不自己认番号
    # 形态——番号识别在别处已经统一过一次，这里再写一套只会两边漂。
    #
    # 「看不见作品」和「看得见但没有一个是 JAV」是两回事：前者是未知，后者才是证据。
    # 默认按未知处理（照查不误），只有拿到反面证据才跳过；把未知也当成非 JAV，
    # 任何一次取数疏漏都会静默地把人整批排除掉。
    for entity_id, total, codes in connection.execute(
            "SELECT ae.entity_id, count(*), group_concat(DISTINCT a.code) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE a.medium='video' GROUP BY ae.entity_id"):
        record = records.get(entity_id)
        if record is None:
            continue
        record["known_works"] = int(total or 0)
        record["jav"] = (not total) or any(
            is_jav_code(code) for code in str(codes or "").split(",") if code)
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
    """只选缺 performer-<id>.img 的 **JAV** performer；有作品多者优先。

    Gfriends 是 JAV 图库，拿非 JAV 的人去查必然落空。实测 567 位有作品的 performer 里
    26 位不是 JAV，缺头像的 72 位里有 19 位属于此类（`桉X`、`古河君`、`Cola酱` 这些
    中文素人创作者）。查它们不只是白费 19 次往返——更糟的是它们混进 `no_match`，把真正
    的 JAV 缺口盖住，让人以为图库覆盖比实际差。

    跳过不等于忽略：它们照样进审计表，只是判定写成 `skipped_not_jav`，说明「这个人需要
    另一个来源」而不是「这个人查不到」。悄悄丢掉才是最糟的处理。
    """
    counts = {entity_id: n for entity_id, n in connection.execute(
        "SELECT entity_id, count(*) FROM asset_entity GROUP BY entity_id")}
    targets = [record for record in load_performers(connection)
               if record.get("jav")
               and not (avatar_dir / f"performer-{record['entity_id']}.img").exists()]
    targets.sort(key=lambda record: (-counts.get(record["entity_id"], 0),
                                     record["entity_id"]))
    return targets[:limit] if limit else targets


def skipped_targets(connection: sqlite3.Connection, avatar_dir: Path) -> list[dict]:
    """缺头像但不走 JAV 图库的人。它们要出现在审计表里，不能凭空消失。"""
    return [record for record in load_performers(connection)
            if not record.get("jav")
            and not (avatar_dir / f"performer-{record['entity_id']}.img").exists()]


def audit_skipped(record: dict) -> dict:
    row = {field: "" for field in FIELDS}
    row["section"] = "missing"
    row["entity_id"] = record["entity_id"]
    row["current_name"] = record["canonical"]
    row["policy_version"] = POLICY_VERSION
    row["verdict"] = "skipped_not_jav"
    row["note"] = "作品里没有 JAV 番号；Gfriends 是 JAV 图库，需要另一个来源"
    return row


def audit_missing(
    record: dict, index: dict, transport: HttpTransport, args: argparse.Namespace,
    cache: AvatarCandidateCache | None = None, health: SourceHealth | None = None,
) -> dict:
    row = {field: "" for field in FIELDS}
    row["section"] = "missing"
    row["entity_id"] = record["entity_id"]
    row["current_name"] = record["canonical"]
    row["policy_version"] = POLICY_VERSION
    if health is not None:
        health.add("attempted")
    entries: list[tuple[str, str]] | None = None
    for name, source in lookup_chain(record):
        # load_gfriends 产出规范化键；保留精确键回退，方便复用旧缓存和单元调用。
        candidate = index.get(normalized(name)) or index.get(name.strip())
        if candidate:
            row["matched_name"] = name
            row["name_source"] = source
            entries = candidate
            break
    if not entries:
        row["verdict"] = "no_match"
        row["note"] = "Gfriends 未收录该名字链上的任何写法"
        if health is not None:
            health.add("no_match")
        return row
    tried = 0
    for category, filename in entries[:max(args.max_candidates, 1)]:
        url = gfriends_url(category, filename)
        data = None if cache is None or args.refresh else cache.lookup(url)
        if data is not None:
            if health is not None:
                health.add("snapshot_reused")
        else:
            response = fetch(transport, url, "image/*", 30, 16 * 1024 * 1024)
            if health is not None:
                health.add("fetched")
            if response is None or response.status != 200:
                if health is not None:
                    health.error(
                        "image_transport" if response is None else "image_http",
                        "" if response is None else response.status,
                        f"{category}/{filename}",
                    )
                if response is None:
                    # 与 fetch 的降级口径一致：网络失败可续跑，不算来源结论。
                    row["verdict"] = "error"
                    row["note"] = f"下载失败：{category}/{filename}"
                    return row
                tried += 1
                continue
            data = response.body
            if health is not None:
                health.add("bytes_fetched", len(data))
        inspected = inspect_avatar(data)
        if inspected is None:
            tried += 1
            continue
        if not acceptable_avatar(inspected, args.min_long_side, args.min_short_side):
            tried += 1
            continue
        cache_path = ""
        provenance_path = ""
        if cache is not None:
            object_path = cache.store(url, data, inspected)
            provenance = provenance_now(
                entity_id=int(record["entity_id"]), provider="gfriends",
                source_kind="external_media_library", matched_name=row["matched_name"],
                name_source=row["name_source"], external_id=f"{category}/{filename}",
                upstream_url=url, width=inspected.width, height=inspected.height,
                mime_type=inspected.mime_type, sha256=inspected.sha256,
                cache_path=str(object_path.relative_to(cache.root)),
            )
            provenance_path = str(cache.store_provenance(provenance))
            cache_path = str(object_path)
        row.update({
            "gfriends_category": category,
            "gfriends_file": filename,
            "width": inspected.width, "height": inspected.height,
            "mime_type": inspected.mime_type, "sha256": inspected.sha256,
            "cache_path": cache_path, "provenance_path": provenance_path,
            "url": url,
            "verdict": "ok",
            "note": f"{len(entries)} 个来源可选，实测第 {tried + 1} 张合格",
        })
        if health is not None:
            health.add("succeeded")
        return row
    row["verdict"] = "rejected"
    row["note"] = f"前 {tried} 张候选未过完整性或尺寸门槛"
    if health is not None:
        health.add("rejected")
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
        row["mime_type"] = provenance.get("mime_type", "")
        row["sha256"] = provenance.get("sha256", "")
        row["cache_path"] = str(avatar_dir / f"performer-{old_id}.img")
        row["provenance_path"] = str(provenance_path)
        row["policy_version"] = provenance.get("policy_version", "legacy")
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
    for old in read_rows(path):
            verdict = old.get("verdict")
            cache_complete = bool(old.get("sha256") and old.get("provenance_path"))
            # 旧版 ok 只有远端 URL，没有本地缓存、内容哈希与稳定 provenance；
            # --resume 必须重跑这些行，不能把旧审计误当成 P2 候选已完成。
            final = verdict in FINAL_VERDICTS and (verdict != "ok" or cache_complete)
            if old.get("section") == "missing" and final:
                done.add(int(old["entity_id"]))
            elif old.get("section") == "missing":
                continue  # error 行重试，不保留旧值
            kept.append(old)
    return kept, done


def write_csv(path: Path, rows: list[dict]) -> None:
    write_rows(path, FIELDS, rows, atomic=True, fill_missing=True)


def candidate_rows(rows: list[dict]) -> list[dict]:
    candidates = []
    for row in rows:
        if row.get("section") != "missing" or row.get("verdict") != "ok":
            continue
        candidates.append({
            "entity_id": row.get("entity_id", ""),
            "current_name": row.get("current_name", ""),
            "matched_name": row.get("matched_name", ""),
            "name_source": row.get("name_source", ""),
            "provider": "gfriends",
            "source_kind": "external_media_library",
            "source_url": row.get("url", ""),
            "external_id": f"{row.get('gfriends_category', '')}/{row.get('gfriends_file', '')}",
            "gfriends_category": row.get("gfriends_category", ""),
            "gfriends_file": row.get("gfriends_file", ""),
            "width": row.get("width", ""), "height": row.get("height", ""),
            "mime_type": row.get("mime_type", ""), "sha256": row.get("sha256", ""),
            # `/api/review` 会原样下发候选列；这里只给不含主机路径的稳定文件名。
            "cache_path": Path(str(row.get("cache_path") or "")).name,
            "provenance_path": Path(str(row.get("provenance_path") or "")).name,
            "policy_version": row.get("policy_version", POLICY_VERSION),
            "verdict": "ok", "avatar_url": row.get("url", ""),
            "evidence": (
                f"Gfriends {row.get('gfriends_category', '')} · "
                f"{row.get('width', '')}×{row.get('height', '')} · "
                f"SHA-256 {str(row.get('sha256', ''))[:12]}"
            ),
        })
    return candidates


def write_candidates(path: Path, rows: list[dict]) -> None:
    write_rows(path, CANDIDATE_FIELDS, candidate_rows(rows), atomic=True)


def write_health(path: Path, health: SourceHealth) -> None:
    write_rows(path, HEALTH_FIELDS, [health.snapshot()], atomic=True)


def run(args: argparse.Namespace, transport: HttpTransport | None = None) -> int:
    global _LIMITER
    # 静态图库走 GitHub raw，不限速；本脚本没有别的远端主机。
    _LIMITER = HostLimiter({"githubusercontent.com": 0.0})
    owned = transport is None
    client = transport or HttpxTransport()
    health = SourceHealth()
    cache = AvatarCandidateCache(args.cache_dir)
    try:
        print("拉取 Gfriends 索引…", flush=True)
        try:
            index = load_gfriends_cached(client, args.cache_dir, args.refresh, health)
        except RuntimeError as error:
            health.error("index_unavailable", message=str(error))
            write_health(args.health, health)
            print(str(error), flush=True)
            print(f"来源健康 → {args.health}", flush=True)
            return 2
        print(f"索引就绪：{len(index)} 个名字键", flush=True)

        connection = open_readonly(args.db)
        targets = missing_targets(connection, args.avatars, 0)
        live_entity_ids = {int(row[0]) for row in connection.execute(
            "SELECT id FROM entity WHERE kind='performer'"
        )}
        installed_hashes = installed_avatar_hashes(args.avatars, live_entity_ids)
        rows: list[dict] = []
        if args.resume:
            prior, done = read_prior(args.out)
            rows = prior
            targets = [t for t in targets if t["entity_id"] not in done]
            print(f"续跑：已判定 {len(done)} 位，跳过", flush=True)
        if args.limit:
            # limit 表示本轮新处理量；必须在续跑排除已完成对象后截取，否则永远卡在首批。
            targets = targets[:args.limit]

        # 孤立审计纯本地、确定性：每轮全量重算，替换旧轮的 orphan 行。
        rows = [row for row in rows if row.get("section") != "orphan"
                and row.get("verdict") != "skipped_not_jav"]
        orphan_rows = audit_orphans(connection, args.avatars)
        # 非 JAV 的人不查 JAV 图库，但要在表里留一行说明原因——悄悄消失最糟。
        skipped_rows = [audit_skipped(record)
                        for record in skipped_targets(connection, args.avatars)]
        print(f"缺口待审 {len(targets)} 位；非 JAV 跳过 {len(skipped_rows)} 位；"
              f"孤立头像 {len(orphan_rows)} 个", flush=True)

        guard = threading.Lock()
        finished = 0

        def process_one(record: dict) -> dict:
            return audit_missing(record, index, client, args, cache, health)

        with futures.ThreadPoolExecutor(max(1, args.workers)) as pool:
            for row in pool.map(process_one, targets):
                with guard:
                    rows.append(row)
                    finished += 1
                    # 边跑边落盘：断电或断网不该丢掉已完成的部分。
                    if finished % 20 == 0:
                        partial = [*rows, *orphan_rows, *skipped_rows]
                        mark_duplicate_candidates(partial, installed_hashes)
                        write_csv(args.out, partial)
                        write_candidates(args.candidates, partial)
                        write_health(args.health, health)
                        ok = sum(1 for r in rows if r.get("verdict") == "ok")
                        print(f"  {finished}/{len(targets)} 已判定，命中 {ok}", flush=True)
        rows.extend(orphan_rows)
        rows.extend(skipped_rows)
        mark_duplicate_candidates(rows, installed_hashes)
        duplicates = sum(1 for row in rows if row.get("verdict") == "duplicate")
        if duplicates:
            health.add("duplicates", duplicates)
        write_csv(args.out, rows)
        write_candidates(args.candidates, rows)
        write_health(args.health, health)
        connection.close()

        summary = Counter(row["verdict"] for row in rows)
        print(f"审计 CSV → {args.out}")
        print(f"复核候选 → {args.candidates}")
        print(f"来源健康 → {args.health}")
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
