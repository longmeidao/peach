"""一个应用实例的库连接、聚合缓存与后台任务句柄。

`WebContract` 是 web 层唯一的可变状态载体，刻意不用模块级全局：测试和真实服务在
同一个解释器里各建自己的实例，任何一个全局都会让它们串到同一个库上。

它单独成一个模块，是为了把依赖方向钉死成一个走法——**它不认识任何域处理器**。
`web_catalog`、`web_entity`、`web_stats`、`web_batch` 全都 import 它，所以它一旦反
过来 import 其中任何一个，整层立刻循环。判据就是这个文件里不许出现 `from .web_`。

`CACHE_TTL` 归这里是因为使用者只有本文件的 `cached()`／`cached_lru()`。内联 favicon 也放这里：它是
唯一一个没有磁盘文件的静态资源，而 `api` 一直从契约模块取它，这次只搬位置。
"""
from __future__ import annotations

import json
import os
import threading
import time

from collections import OrderedDict
from pathlib import Path
from typing import Sequence

from .catalog_rules import normalise_code_key
from .config import (
    COVER_DIR,
    DATA_ROOT,
    GENERATED_DIR,
    SECRETS_DIR,
    SHARED_DATA_ROOT,
    SOURCES_DIR,
    STATE_DIR,
)
from .jobs import BackgroundJob
from .media import remap_managed_path
from .repository import LedgerDatabase


FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0B0B0D"/><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF9A76"/><stop offset="1" stop-color="#F2557B"/></linearGradient></defs><path d="M16 28c-5.7 0-9.7-3.6-9.7-8.6 0-4.3 2.8-7.6 6.5-7.6 1.4 0 2.4.5 3.2 1.1.8-.6 1.8-1.1 3.2-1.1 3.7 0 6.5 3.3 6.5 7.6C25.7 24.4 21.7 28 16 28z" fill="url(#pg)"/><path d="M16 13.4V27" stroke="#0B0B0D" stroke-width="1.1" opacity=".3" stroke-linecap="round"/><path d="M17.1 11.7c.6-2.8 2.8-4.6 5.6-4.8-.2 2.8-2.2 4.7-5.6 4.8z" fill="#5FB95F"/><path d="M16 11.9c0-1.9.5-3.4 1.5-4.5" stroke="#8A5A3B" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>')

CACHE_TTL = 90


class WebContract:
    """单个应用实例的数据库、写锁和聚合缓存；不共享模块级可变状态。"""

    def __init__(self, db_path: Path, snapshot_root: Path | None = None,
                 legacy_snapshot_roots: Sequence[Path] = (),
                 candidate_root: Path | None = None,
                 cover_root: Path | None = None,
                 avatar_root: Path | None = None,
                 logo_root: Path | None = None,
                 poster_root: Path | None = None,
                 photo_root: Path | None = None,
                 transcode_root: Path | None = None,
                 stream_root: Path | None = None,
                 follow_sources_root: Path | None = None,
                 follow_secrets_root: Path | None = None,
                 follow_state_root: Path | None = None,
                 follow_shared_root: Path | None = None,
                 taste_history_root: Path | None = None,
                 taste_history_store: Path | None = None,
                 taste_history_import_root: Path | None = None,
                 taste_history_manifest: Path | None = None,
                 database: LedgerDatabase | None = None):
        # 候选 CSV 的目录做成实例属性而不是模块常量，复核层才能在临时目录里被测试。
        self.candidate_root = Path(candidate_root) if candidate_root is not None else GENERATED_DIR
        self.cover_root = Path(cover_root) if cover_root is not None else COVER_DIR
        self.avatar_root = Path(avatar_root) if avatar_root is not None else GENERATED_DIR / "avatars"
        # `/logo` 就是从这里读；批准候选等于把图装进这个目录。
        self.logo_root = Path(logo_root) if logo_root is not None else GENERATED_DIR / "logos"
        self.poster_root = Path(poster_root) if poster_root is not None else GENERATED_DIR / "posters"
        self.photo_root = Path(photo_root) if photo_root is not None else GENERATED_DIR / "photo-thumbs"
        self.transcode_root = (Path(transcode_root) if transcode_root is not None
                               else GENERATED_DIR / "transcodes")
        self.stream_root = Path(stream_root) if stream_root is not None else GENERATED_DIR / "stream-segments"
        # API construction passes every managed cache root. A bare WebContract is also used
        # by isolated unit tests; it must never wander into the machine's real generated tree.
        self.resource_cleanup_enabled = any(
            root is not None for root in (poster_root, photo_root, transcode_root, stream_root))
        # 追更的原始证据与本机凭据目录同样做成实例属性，测试才能落在临时目录里。
        self.follow_sources_root = (Path(follow_sources_root)
                                    if follow_sources_root is not None else SOURCES_DIR)
        self.follow_secrets_root = (Path(follow_secrets_root)
                                    if follow_secrets_root is not None else SECRETS_DIR)
        self.follow_state_root = (Path(follow_state_root)
                                  if follow_state_root is not None else STATE_DIR)
        # 共享副本只承载**声明为可同步**的凭据字段，见 follow_secrets.SYNCABLE_FIELDS。
        self.follow_shared_root = (Path(follow_shared_root)
                                   if follow_shared_root is not None else SHARED_DATA_ROOT)
        # 浏览历史口味分析的产出目录，`scripts/taste_history.py --output` 的默认值。
        self.taste_history_root = (Path(taste_history_root)
                                   if taste_history_root is not None
                                   else DATA_ROOT / "review" / "taste-history")
        self.taste_history_store = (Path(taste_history_store)
                                    if taste_history_store is not None
                                    else SOURCES_DIR / "taste-history" / "history.sqlite")
        self.taste_history_import_root = (Path(taste_history_import_root)
                                          if taste_history_import_root is not None
                                          else SOURCES_DIR / "taste-history" / "imports")
        self.taste_history_manifest = (Path(taste_history_manifest)
                                       if taste_history_manifest is not None
                                       else STATE_DIR / "taste-history" / "manifest.json")
        self.database = database or LedgerDatabase(db_path)
        self.db_path = self.database.db_path
        self.snapshot_root = Path(snapshot_root) if snapshot_root is not None else None
        self.legacy_snapshot_roots = tuple(Path(path) for path in legacy_snapshot_roots)
        self.cache: dict[str, tuple[float, object]] = {}
        self.cache_lock = threading.Lock()
        #: 按资产取键的读缓存，LRU 限界。键空间不封闭的场景走这里，见 `cached_lru()`。
        self.keyed_cache: OrderedDict[str, tuple[float, object]] = OrderedDict()
        #: 每次 cache_bust 递增。在途计算据此判断自己出发后缓存是否失效过。
        self.cache_generation = 0
        self.follow_check_lock = threading.Lock()
        self.follow_scheduler = None
        # 两块后台任务的锁、状态和线程都归 BackgroundJob 管，契约上只留这两个字段。
        # 任务 id 的键名沿用各自原有的名字：它随公开投影下发，是前端契约。
        self.resource_scan = BackgroundJob("PeachResourceScanJob", id_key="scan_id")
        self.link_check = BackgroundJob("PeachLinkCheckJob", id_key="check_id")
        self._fts_available: bool | None = None

    def cached(self, key, fn):
        """带 TTL 的读缓存。`fn` 刻意在锁外算——它会读 CSV、查库，拿着锁算会把
        并发请求全串起来。

        代价是计算期间缓存可能被 `cache_bust()` 清掉，那份还没写回的值就是失效前的
        快照。复核页正是这个场景：`q_review` 在算，用户批准了一条候选，
        `w_review_decision` 调 `cache_bust`；旧实现照样把批准前的快照写回去，
        于是用户批准完刷新，看到的还是批准前的列表，而且持续整整一个 TTL。

        用代次挡住：写回前确认这期间没有失效过，否则丢弃这次结果。
        """
        now = time.time()
        with self.cache_lock:
            hit = self.cache.get(key)
            if hit and now - hit[0] < CACHE_TTL:
                return hit[1]
            generation = self.cache_generation
        value = fn()
        with self.cache_lock:
            if generation == self.cache_generation:
                # 时间戳沿用进入时的 now：算得比 TTL 还久的结果直接算过期，
                # 宁可下次重算，也不要把一份已经旧了的数据当新的用。
                self.cache[key] = (now, value)
        return value

    def cached_lru(self, key, fn, *, maxsize: int = 192, ttl: float = CACHE_TTL):
        """带 TTL 的 LRU 读缓存，给键空间不封闭的场景用（`/api/related` 按资产取键）。

        `cached()` 的字典只在 `cache_bust()` 时清空，所以它的键空间必须封闭——
        stats、tops 只有几个固定键，放得下；related 的键跟着浏览过的资料页数量走，
        不限界就是无上限的内存增长。LRU 驱逐之外，TTL 与代次失效的语义和
        `cached()` 逐字一致，包括「`fn` 在锁外算」和「失效过就丢弃这次结果」。
        """
        now = time.time()
        with self.cache_lock:
            hit = self.keyed_cache.get(key)
            if hit and now - hit[0] < ttl:
                self.keyed_cache.move_to_end(key)
                return hit[1]
            generation = self.cache_generation
        value = fn()
        with self.cache_lock:
            if generation == self.cache_generation:
                self.keyed_cache[key] = (now, value)
                self.keyed_cache.move_to_end(key)
                while len(self.keyed_cache) > maxsize:
                    self.keyed_cache.popitem(last=False)
        return value

    def stop_background_jobs(self) -> None:
        """服务关停时丢掉后台任务状态并等线程收工。

        谁在跑归契约自己知道，`api` 的 lifespan 不该再列一遍任务清单。
        """
        self.resource_scan.stop()
        self.link_check.stop()

    def cache_bust(self):
        with self.cache_lock:
            self.cache.clear()
            self.keyed_cache.clear()
            # 在途计算靠这个数认出「我出发之后缓存失效过」，从而放弃写回。
            self.cache_generation += 1

    def db(self, write=False):
        return self.database.connect(write=write)

    def read_connection(self):
        return self.database.read_connection()

    def write_transaction(self):
        return self.database.write_transaction()

    def has_snapshot(self, raw_path: str | None) -> bool:
        if not raw_path:
            return False
        path = (remap_managed_path(
            raw_path, self.snapshot_root, self.legacy_snapshot_roots,
        ) if self.snapshot_root is not None else Path(raw_path))
        return path.is_file()

    def cover_path(self, code: str | None) -> Path | None:
        """封面按归一番号存一份，多个文件共用同一张；没有就返回 None。"""
        key = normalise_code_key(code)
        if not key:
            return None
        path = self.cover_root / f"{key}.jpg"
        return path if path.is_file() else None

    def cover_index(self) -> dict[str, dict | None]:
        """封面目录扫一遍的索引：casefold(归一番号) → 取景 `{"cy": …}` 或 None。

        卡片列表逐行问「有封面吗」「取景是多少」，一页 60 行就是 120+ 次 stat 加
        读文件；封面目录一次 scandir 就覆盖全部番号，结果走 `cached()` 的 TTL。
        `/cover` 端点仍走 `cover_path()` 直读，取图不受索引影响。

        代价是刚落盘的封面最多一个 TTL 后才出现在卡片徽章上；刮削流程里复核确认
        本来就会 `cache_bust()`，所以用户自己的动作看得到即时效果。
        """
        return self.cached("cover-index", self._scan_cover_root)

    def _scan_cover_root(self) -> dict[str, dict | None]:
        """一次目录扫描同时收集封面存在性和 sidecar 取景。目录不存在就是空索引。"""
        scanned: dict[str, dict | None] = {}
        try:
            with os.scandir(self.cover_root) as entries:
                for entry in entries:
                    if not entry.name.endswith(".jpg"):
                        continue
                    scanned[entry.name[:-len(".jpg")].casefold()] = self._cover_focus(
                        entry.path[:-len(".jpg")] + ".face.json")
        except OSError:
            return {}
        return scanned

    @staticmethod
    def _cover_focus(sidecar: str) -> dict | None:
        """sidecar 里的人脸中心。没算过、读不出或没检出都是 None，页面退回固定取景。"""
        try:
            with open(sidecar, encoding="utf-8") as handle:
                face = (json.load(handle) or {}).get("face")
        except (OSError, ValueError):
            return None
        return {"cy": face["cy"]} if isinstance(face, dict) and "cy" in face else None

    def has_cover(self, code: str | None) -> bool:
        key = normalise_code_key(code)
        # 索引的键是 casefold 过的：`is_file()` 在 Windows 与 macOS 的默认文件系统上
        # 大小写不敏感，改走索引不能顺手把这层容错丢了。
        return bool(key) and key.casefold() in self.cover_index()

    def cover_frame(self, code: str | None) -> dict | None:
        """封面的取景提示：人脸中心。没算过或没检出就返回 None。

        只用来做纵向微调，横向仍由版式决定——横向靠几何规则已经稳定。
        取不到时前端退回固定取景，不影响显示。
        """
        key = normalise_code_key(code)
        return self.cover_index().get(key.casefold()) if key else None

    def avatar_focus(self, kind: str, entity_id: int) -> dict | None:
        """实体图的取景提示：人脸中心换算成的 object-position。

        sidecar 由 `scripts/detect_avatar_faces.py` 离线写入，与封面取景同一
        约定；没算过、读不出或没检出都返回 None，页面维持几何居中。
        """
        path = self.avatar_root / f"{kind}-{int(entity_id)}.face.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        focus = data.get("focus") if isinstance(data, dict) else None
        if not isinstance(focus, dict):
            return None
        axis = focus.get("axis")
        pct = focus.get("pct")
        if (axis not in {"x", "y"} or isinstance(pct, bool)
                or not isinstance(pct, (int, float)) or not 0 <= pct <= 100):
            return None
        return {"axis": axis, "pct": int(pct)}

    def has_fts(self) -> bool:
        if self._fts_available is None:
            with self.read_connection() as connection:
                self._fts_available = connection.execute(
                    "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='asset_search'"
                ).fetchone() is not None
        return self._fts_available
