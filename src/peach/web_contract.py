"""Stable JSON contract used by the FastAPI application.

Database reads are read-only by default. Writes are limited to explicit activity and
feedback functions; schema changes belong to the migration runner.
"""
from __future__ import annotations

import os
import hashlib
import json
import random
import re
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Sequence
from urllib.parse import quote, urlsplit

from .config import (
    COVER_DIR, DATA_ROOT, GENERATED_DIR, LOCATION_ROOT_DECLARATIONS, SECRETS_DIR,
    SOURCES_DIR,
    SHARED_DATA_ROOT,
    STATE_DIR,
)
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
    resolve_entity,
    upsert_asset_entity,
)
from .media import remap_managed_path
from .metadata_policy import SOURCE_SPECS
from .platform import (
    is_unmapped,
    root_online,
    system_volume,
    translate_ledger_path,
)
from .repository import LedgerDatabase
from .taste_history import (
    analyze_history,
    build_taste_dashboard,
    discover_history_sources,
    refresh_history,
    remove_history_source,
    write_manifest,
)
from .web_follow import (
    q_follow, q_follow_credentials, q_follow_schedule, q_follow_tags,
    w_follow_check, w_follow_credential, w_follow_resolve, w_follow_schedule,
    w_follow_activity, w_follow_author_alias, w_follow_play, w_follow_save,
    w_follow_source, w_follow_status,
)
from .web_activity import (
    DEFAULT_PROFILE_ID,
    w_activity,
    w_feedback,
    w_play,
    w_preference,
    w_quality_goal,
    w_watch_later,
)
from .catalog_rules import (
    DUPLICATE_FLOOR_SECONDS,
    DUPLICATE_TOLERANCE,
    GENERIC_PHOTO_DIRS,
    LENGTH_TAGS,
    TECH_TAGS,
    dir_expr,
    duration_clusters,
    face_focus,
    is_jav_asset,
    is_jav_code,
    normalise_code_key,
    ordered_multipart_items,
    part_marker,
    photo_set_title,
    tag_cat,
)
from .web_playlists import q_playlist, q_playlists, w_playlist
from .web_review import q_review, w_review_auto_apply, w_review_decision
from .web_settings import q_settings, w_settings
from .web_resource_sync import (
    clean_resource_orphans,
    source_is_online,
    w_purge_missing,
    w_resource_sync_apply,
    w_resource_sync_scan,
)

COST = {"local": "free", "115": "free", "pikpak": "metered", "online": "metered"}

#: 卡片随每条记录返回的女优上限。共演作品必须带上全部出镜者，而不是只留第一位；
#: 但 BEST 合集实测有 41 位，全量下发会把列表响应撑大，所以截断并同时给出总数，
#: 由界面显示「等 N 人」。详情页走 q_item，不受这个上限影响。
CARD_PERFORMERS = 6

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0B0B0D"/><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF9A76"/><stop offset="1" stop-color="#F2557B"/></linearGradient></defs><path d="M16 28c-5.7 0-9.7-3.6-9.7-8.6 0-4.3 2.8-7.6 6.5-7.6 1.4 0 2.4.5 3.2 1.1.8-.6 1.8-1.1 3.2-1.1 3.7 0 6.5 3.3 6.5 7.6C25.7 24.4 21.7 28 16 28z" fill="url(#pg)"/><path d="M16 13.4V27" stroke="#0B0B0D" stroke-width="1.1" opacity=".3" stroke-linecap="round"/><path d="M17.1 11.7c.6-2.8 2.8-4.6 5.6-4.8-.2 2.8-2.2 4.7-5.6 4.8z" fill="#5FB95F"/><path d="M16 11.9c0-1.9.5-3.4 1.5-4.5" stroke="#8A5A3B" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>')

CACHE_TTL = 90

# 清空回收站时要一并清掉的资产引用表，物理删除的边界只写在这一处。
# `asset_search` 不在其中：0004 的 `asset_search_asset_delete` 触发器已经负责 FTS 行，
# 这里再删一遍只会重复，还会诱使测试库伪造一张同名普通表，把 has_fts() 骗成 True。
ASSET_REFERENCE_TABLES = (
    "asset_tag", "media_binding", "activity_event", "asset_entity",
    "watch_queue", "asset_preference", "asset_tag_preference", "asset_quality_goal",
    "playlist_item",
)


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
        # 共享副本只承载**声明为可同步**的凭据字段，见 web_follow.SYNCABLE_FIELDS。
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
        #: 每次 cache_bust 递增。在途计算据此判断自己出发后缓存是否失效过。
        self.cache_generation = 0
        self.follow_check_lock = threading.Lock()
        self.follow_scheduler = None
        self.resource_scan_lock = threading.Lock()
        self.resource_scan_state: dict | None = None
        self.resource_scan_thread: threading.Thread | None = None
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

    def cache_bust(self):
        with self.cache_lock:
            self.cache.clear()
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

    def has_cover(self, code: str | None) -> bool:
        return self.cover_path(code) is not None

    def cover_frame(self, code: str | None) -> dict | None:
        """封面的取景提示：宽高比和人脸中心。没算过或没检出就返回 None。

        只用来做纵向微调，横向仍由版式决定——横向靠几何规则已经稳定。
        取不到时前端退回固定取景，不影响显示。
        """
        path = self.cover_path(code)
        if path is None:
            return None
        sidecar = path.with_suffix(".face.json")
        if not sidecar.is_file():
            return None
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        face = data.get("face")
        return {"cy": face["cy"]} if isinstance(face, dict) and "cy" in face else None

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

# ────────────────────────────── 查询 ──────────────────────────────

def tag_is_not_a_performer_name(tag: str) -> str:
    """「这个标签不是某个女优的名字」的 SQL 判据。

    同名的标签和 performer 身份会互相冒充，所以标签榜要把它们排掉。这条同样写了
    四份，其中一份拿 `lower(trim(t.tag))` 去比 `performer.normalized_name`——后者
    是 Python casefold 写进去的，而 SQLite 的 lower() 只认 ASCII，于是西里尔或
    带罗马数字的名字永远排不掉。列一侧一律走 `peach_normalize()`。
    """
    return ("NOT EXISTS(SELECT 1 FROM entity performer WHERE performer.kind='performer' "
            f"AND performer.normalized_name={tag})")


def tag_not_hidden(asset: str, tag: str) -> str:
    """「这个标签没有被用户隐藏」的 SQL 判据。

    同一条规则此前在五处各写了一份裸 SQL。join 列和比较列因查询语境不同是正常的，
    但规则本体（默认档案、hidden=1、按归一化名比对）只该有一份：漏抄一处，被隐藏
    的标签就会从那个表面漏回来，而这属于语义契约。

    `tag` 传比较用的表达式。列一侧要用 `peach_normalize()`——SQLite 的 lower() 只认
    ASCII，拿它去比 Python casefold 写进去的值，非 ASCII 标签永远匹配不上。
    """
    return ("NOT EXISTS(SELECT 1 FROM asset_tag_preference p "
            f"WHERE p.asset_id={asset} AND p.profile_id='{DEFAULT_PROFILE_ID}' "
            f"AND p.hidden=1 AND p.normalized_tag={tag})")


def q_items(contract: WebContract, args):
    trash = args.get("state") == "trash"
    # 普通馆藏仍是视频表面；回收站必须展示所有文件类型，否则从垃圾复核移入的
    # 图片、网址快捷方式等会变成不可见、不可恢复，只能被「清空回收站」直接删掉。
    where, par = ([] if trash else ["a.medium='video'"]), []
    if trash:
        where.append("a.disposal='trash'")
    else:
        where.append("(a.disposal IS NULL OR a.disposal <> 'trash')")
    if args.get("loc"):
        locs = [x for x in args["loc"].split(",") if x]
        where.append("a.location IN (%s)" % ",".join("?" * len(locs))); par += locs
    if args.get("creator"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='creator' AND e.canonical_name=?)"
        ); par.append(args["creator"])
    if args.get("performer"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='performer' AND e.canonical_name=?)"
        ); par.append(args["performer"])
    if args.get("studio"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='studio' AND e.canonical_name=?)"
        ); par.append(args["studio"])
    if args.get("series"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='series' AND e.canonical_name=?)"
        ); par.append(args["series"])
    if args.get("tag"):
        tags = [x for x in args["tag"].split(",") if x]
        tag_clause = (
            "((EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='tag' AND e.canonical_name=?) OR "
            "EXISTS(SELECT 1 FROM asset_tag t WHERE t.asset_id=a.id AND t.tag=?)) AND "
            + tag_not_hidden("a.id", "?") + ")"
        )
        if args.get("tag_match") == "any" and len(tags) > 1:
            where.append("(" + " OR ".join(tag_clause for _ in tags) + ")")
            for tag in tags:
                par.extend((tag, tag, normalize_entity_name(tag)))
        else:
            # 默认保持原有组合语义：逗号分隔的标签必须全部满足。
            for tag in tags:
                where.append(tag_clause)
                par.extend((tag, tag, normalize_entity_name(tag)))
    # 回收站是跨类型恢复入口。首页遗留的「只看有缩略图」、时长、画幅和 JAV
    # 条件只对视频成立，带进这里会再次把图片、网址快捷方式等资源藏起来。
    if not trash and args.get("len"):
        where.append("a.ctx_length = ?"); par.append(args["len"])
    if not trash and args.get("dur_min"):
        where.append("a.duration >= ?"); par.append(max(0, float(args["dur_min"])))
    if not trash and args.get("dur_max"):
        where.append("a.duration <= ?"); par.append(max(0, float(args["dur_max"])))
    if not trash and args.get("orient"):
        where.append("a.ctx_orient = ?"); par.append(args["orient"])
    elif not trash and args.get("exclude_vertical") == "1":
        where.append("(a.ctx_orient IS NULL OR a.ctx_orient <> '竖屏')")
    if not trash and args.get("jav") == "1":
        # 只有番号形态还不够：JI-103 这类 creator clip 没有任何发行证据。
        where.append(JAV_ASSET_PREDICATE)
    if args.get("q"):
        query = args["q"].strip()
        if len(query) >= 3 and contract.has_fts():
            where.append(
                "a.id IN (SELECT asset_id FROM asset_search WHERE asset_search MATCH ?)"
            )
            par.append('"' + query.replace('"', '""') + '"')
        else:
            # 短查询走 LIKE，必须和 FTS 覆盖同样的身份写法：规范名、别名和检索词。
            # 只比 canonical_name 会让「凉森」搜不到 `涼森れむ`——trigram 要求三字
            # 起步，两字查询永远落在这条分支上，补检索词也救不了。
            where.append(
                "(a.name LIKE ? OR a.code LIKE ? OR EXISTS("
                "SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=a.id AND e.kind IN ('creator','performer','studio') "
                "AND (e.canonical_name LIKE ? "
                "OR EXISTS(SELECT 1 FROM entity_alias al WHERE al.entity_id=e.id "
                "AND al.alias LIKE ?) "
                "OR EXISTS(SELECT 1 FROM entity_search_term st WHERE st.entity_id=e.id "
                "AND st.term LIKE ?))))"
            )
            pattern = f"%{query}%"
            par += [pattern] * 5
    state = state_predicate(str(args.get("state") or ""))
    if state:
        where.append(state)
    if not trash and args.get("thumb") == "1":
        # 已保存的关注条目只登记在线资产，不下载媒体或生成本地缩略图。
        # 它仍然是可筛选的真实资产；若沿用首页的缩略图门槛，来源 facet 会显示
        # 「在线 1」，点进去却永远是 0 条。
        where.append("(a.snapshot_path IS NOT NULL OR a.location = 'online')")

    order = {"new": "a.first_seen DESC, a.id DESC",
             "release": "a.release_date DESC, a.first_seen DESC, a.id DESC",
             "big": "a.size DESC",
             "short": "a.duration ASC",
             "long": "a.duration DESC",
             "played": "a.last_played DESC",
             "rating": "a.rating DESC NULLS LAST, a.o_count DESC NULLS LAST",
             "plays": "a.play_count DESC NULLS LAST, a.last_played DESC",
             "o": "a.o_count DESC NULLS LAST",
             "rand": "RANDOM()"}.get(args.get("sort"), None)
    if order is None:
        if args.get("sort") == "seed":
            sd = int(args.get("seed") or 1) % 99991 or 7
            order = f"((a.id * {sd}) % 99991)"
        elif args.get("sort") == "daily" or not args.get("sort"):
            # 每日轮换：用当天日期做种子打散，同一天顺序固定，隔天自动换一批。
            # 不用 RANDOM() —— 那样每次刷新都不同，翻页还会重复/漏掉。
            seed = int(time.strftime("%Y%m%d")) % 9973 or 7
            order = f"((a.id * {seed}) % 99991)"
        else:
            order = "a.id DESC"
    lim = min(int(args.get("limit", 60)), 200)
    off = int(args.get("offset", 0))
    include_total = args.get("count", "1") != "0"
    fetch_limit = lim if include_total else lim + 1
    sql = ("SELECT a.id,a.location,a.path,a.name,a.medium,a.creator,a.studio,a.code,a.release_date,a.size,"
           "a.duration,a.width,a.height,a.ctx_length,a.ctx_orient,a.snapshot_path,"
           "a.play_count,a.leave_ratio,a.feedback,a.disposal,a.rating,a.o_count,"
           "a.play_seconds,a.max_reached,a.seek_count,"
           "EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=a.id "
           f"AND w.profile_id='{DEFAULT_PROFILE_ID}') AS watch_later "
           "FROM asset a WHERE " + " AND ".join(where) + f" ORDER BY {order} LIMIT ? OFFSET ?")
    with contract.read_connection() as c:
        rows = [dict(r) for r in c.execute(sql, par + [fetch_limit, off])]
        has_more = len(rows) > lim if not include_total else None
        rows = rows[:lim]
        cnt = (c.execute("SELECT count(*) FROM asset a WHERE " + " AND ".join(where), par).fetchone()[0]
               if include_total else None)
    # 卡片要显示出镜者和高权重标签，不能只有番号 —— 一次批量取，别 N+1
    if rows:
        ids = [r["id"] for r in rows]
        qm = ",".join("?" * len(ids))
        tmap: dict[int, list[str]] = {}
        for aid, tag in con_tags(contract, ids, qm):
            tmap.setdefault(aid, []).append(tag)
        emap: dict[int, dict[str, list[str]]] = {}
        performer_refs: dict[int, list[dict[str, object]]] = {}
        for aid, entity_id, kind, name in con_entities(contract, ids, qm):
            emap.setdefault(aid, {}).setdefault(kind, []).append(name)
            if kind == "performer":
                performer_refs.setdefault(aid, []).append({"id": entity_id, "name": name})
        for r in rows:
            ts = tmap.get(r["id"], [])
            canonical = emap.get(r["id"], {})
            canonical_tags = canonical.get("tag", [])
            canonical_performers = canonical.get("performer", [])
            all_performers = canonical_performers or [
                tag[3:] for tag in ts if tag.startswith("演员:")
            ]
            performers = all_performers[:CARD_PERFORMERS]
            performer_names = {normalize_entity_name(name) for name in all_performers}
            visible_tags = canonical_tags or [t for t in ts if not t.startswith("演员:")]
            r["tags"] = [
                tag for tag in visible_tags
                if tag_cat(tag) in (
                    "general", "relationship", "role", "appearance", "scene", "story", "position",
                )
                and normalize_entity_name(tag) not in performer_names
            ][:4]
            r["performers"] = performers
            refs = performer_refs.get(r["id"], [])
            r["performer_entities"] = refs[:CARD_PERFORMERS]
            r["performer_total"] = len(refs) or len(all_performers)
            r["_entity_kinds"] = tuple(canonical)
    for r in rows:
        r["cost"] = COST.get(r["location"], "metered")
        r["has_thumb"] = contract.has_snapshot(r["snapshot_path"])
        r["has_cover"] = contract.has_cover(r.get("code"))
        # 卡片上的出镜者称谓要和详情页同一口径：番号形态加发行证据才叫 JAV。
        r["is_jav"] = is_jav_asset(
            r.get("code"), r.get("studio"), r.get("release_date"),
            r.pop("_entity_kinds", ()),
        )
        if r["has_cover"]:
            r["cover_frame"] = contract.cover_frame(r.get("code"))
        r.pop("snapshot_path", None)
        r.pop("path", None)                     # 路径不外发，串流走 id
    attach_multipart_groups(contract, rows)
    return {"total": cnt, "items": rows, "has_more": has_more}

def con_tags(contract: WebContract, ids, qm):
    with contract.read_connection() as c:
        return c.execute(
            f"SELECT asset_id, tag FROM asset_tag WHERE asset_id IN ({qm})", ids).fetchall()


def con_entities(contract: WebContract, ids, qm):
    with contract.read_connection() as connection:
        return connection.execute(
            f"SELECT DISTINCT ae.asset_id,e.id,e.kind,e.canonical_name "
            f"FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            f"WHERE ae.asset_id IN ({qm}) "
            f"AND e.kind IN ('tag','performer','creator','studio','series') "
            f"ORDER BY ae.asset_id,e.kind,e.canonical_name", ids,
        ).fetchall()


def q_search_history(contract: WebContract, limit: int = 10):
    with contract.read_connection() as connection:
        rows = connection.execute(
            "SELECT query FROM search_history ORDER BY last_used_at DESC, query LIMIT ?",
            (max(1, min(limit, 50)),),
        ).fetchall()
    return {"items": [row["query"] for row in rows]}


TASTE_WINDOWS = {"all": None, "90d": 90, "365d": 365}


def _taste_since(window: str) -> str | None:
    if window not in TASTE_WINDOWS:
        raise ValueError("invalid taste window")
    days = TASTE_WINDOWS[window]
    return (datetime.now(UTC) - timedelta(days=days)).isoformat() if days else None


def q_taste(contract: WebContract, args=None):
    args = args or {}
    window = str(args.get("window") or "all")
    with contract.read_connection() as connection:
        payload = build_taste_dashboard(
            contract.taste_history_store,
            connection,
            since=_taste_since(window),
        )
    updated_at = None
    try:
        manifest = json.loads(contract.taste_history_manifest.read_text(encoding="utf-8"))
        updated_at = manifest.get("updated_at")
    except (OSError, ValueError, TypeError):
        pass
    export_count = export_bytes = 0
    try:
        for path in contract.taste_history_import_root.iterdir():
            if path.is_file() and not path.name.endswith(".part"):
                export_count += 1
                export_bytes += path.stat().st_size
    except OSError:
        pass
    payload.update({
        "window": window,
        "updated_at": updated_at,
        "storage": {"exports": export_count, "bytes": export_bytes},
    })
    return payload


def w_taste_refresh(contract: WebContract, body):
    window = str(body.get("window") or "all")
    sources = discover_history_sources()
    results = refresh_history(sources, contract.taste_history_store) if sources else []
    if contract.taste_history_store.is_file():
        analysis = analyze_history(contract.taste_history_store, contract.taste_history_root)
        write_manifest(contract.taste_history_manifest, results, analysis)
    contract.cache_bust()
    return {"refresh": results, "dashboard": q_taste(contract, {"window": window})}


def w_taste_source(contract: WebContract, body):
    if body.get("operation") != "remove":
        raise ValueError("invalid taste source operation")
    source_key = str(body.get("source_key") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", source_key):
        raise ValueError("invalid taste source key")
    removed = remove_history_source(contract.taste_history_store, source_key)
    analysis = analyze_history(contract.taste_history_store, contract.taste_history_root)
    write_manifest(contract.taste_history_manifest, [{"removed": removed}], analysis)
    contract.cache_bust()
    return {
        "removed": removed,
        "dashboard": q_taste(contract, {"window": str(body.get("window") or "all")}),
    }


def w_search_history(contract: WebContract, body):
    operation = body.get("operation", "remember")
    query = str(body.get("query", "")).strip()
    if operation == "remove":
        if not query:
            raise ValueError("query is required")
        with contract.write_transaction() as connection:
            connection.execute("DELETE FROM search_history WHERE query=?", (query,))
        return {"ok": True, "operation": operation}
    if operation != "remember" or not query or len(query) > 200:
        raise ValueError("invalid search history request")
    with contract.write_transaction() as connection:
        connection.execute(
            "INSERT INTO search_history(query,used_count,last_used_at) VALUES(?,1,datetime('now')) "
            "ON CONFLICT(query) DO UPDATE SET used_count=used_count+1,last_used_at=excluded.last_used_at",
            (query,),
        )
    return {"ok": True, "operation": operation}


def attach_card_performers(contract: WebContract, rows):
    """给各类视频卡片补同一份表演者资料，避免首页/相关/复核卡片各说各话。"""
    if not rows:
        return
    ids = [row["id"] for row in rows]
    qm = ",".join("?" * len(ids))
    names: dict[int, list[str]] = {}
    refs: dict[int, list[dict[str, object]]] = {}
    for asset_id, entity_id, kind, name in con_entities(contract, ids, qm):
        if kind != "performer":
            continue
        names.setdefault(asset_id, []).append(name)
        refs.setdefault(asset_id, []).append({"id": entity_id, "name": name})
    for row in rows:
        row["performers"] = names.get(row["id"], [])[:CARD_PERFORMERS]
        row["performer_entities"] = refs.get(row["id"], [])[:CARD_PERFORMERS]
        row["performer_total"] = len(names.get(row["id"], []))


def _multipart_rows(contract: WebContract, codes) -> list[dict]:
    raw_codes = sorted({str(code) for code in codes if str(code or "").strip()})
    if not raw_codes:
        return []
    placeholders = ",".join("?" * len(raw_codes))
    with contract.read_connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT id,name,code,size,duration FROM asset "
            f"WHERE medium='video' AND code IN ({placeholders}) "
            "AND (disposal IS NULL OR disposal<>'trash')",
            raw_codes,
        )]
    return [row for row in rows if part_marker(str(row.get("name") or ""))]


def _multipart_groups(contract: WebContract, codes) -> dict[str, list[dict]]:
    candidates: dict[str, list[dict]] = {}
    for row in _multipart_rows(contract, codes):
        candidates.setdefault(normalise_code_key(row.get("code")), []).append(row)
    return {
        code: ordered
        for code, items in candidates.items()
        if (ordered := ordered_multipart_items(items))
    }


def attach_multipart_groups(contract: WebContract, rows) -> None:
    """Annotate list cards with one derived multipart release, without ledger writes."""
    if not rows:
        return
    groups = _multipart_groups(
        contract,
        [row.get("code") for row in rows if part_marker(str(row.get("name") or ""))],
    )
    for row in rows:
        code = normalise_code_key(row.get("code"))
        group = groups.get(code)
        if not group or not any(item["id"] == row["id"] for item in group):
            continue
        row["part_group"] = {
            "key": code,
            "title": code or str(row.get("code") or "分卷作品"),
            "count": len(group),
            "seed_id": group[0]["id"],
            "item_ids": [item["id"] for item in group],
            "total_duration": sum(float(item.get("duration") or 0) for item in group),
            "total_size": sum(int(item.get("size") or 0) for item in group),
        }


def q_parts(contract: WebContract, args):
    """Return an explicitly marked multipart release in playback order."""
    asset_id = int(args["id"])
    with contract.read_connection() as connection:
        seed = connection.execute(
            "SELECT id,code FROM asset WHERE id=? AND medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash')",
            (asset_id,),
        ).fetchone()
    if not seed or not seed["code"]:
        return {"error": "multipart release not found"}
    code = normalise_code_key(seed["code"])
    group = _multipart_groups(contract, [seed["code"]]).get(code, [])
    if not group or not any(item["id"] == asset_id for item in group):
        return {"error": "multipart release not found"}
    items = []
    for row in group:
        item = q_item(contract, row["id"])
        marker = part_marker(str(row.get("name") or ""))
        item["part_label"] = marker.upper() if marker.isalpha() else marker
        items.append(item)
    return {"title": code or str(seed["code"]), "count": len(items), "items": items}

def q_item(contract: WebContract, aid):
    """按 id 直取。
    ⚠️ 第一版没有这个接口，前端用「带筛选条件再查一遍然后 find」的绕法，
       limit 被覆盖成 1 → find 必然失败 → 走兜底 items[0]，
       于是**每次点击都打开同一个默认列表首项**（一个 12.6 GB 的 PikPak 文件），
       既显示错条目，又反复拉计费流量。教训：按 id 取就按 id 取。"""
    with contract.read_connection() as c:
        r = c.execute(
            "SELECT id,location,path,name,creator,studio,code,release_date,size,duration,width,height,"
            "ctx_length,ctx_orient,snapshot_path,play_count,leave_ratio,feedback,disposal,"
            "rating,o_count,play_seconds,max_reached,seek_count,"
            "COALESCE((SELECT p.liked FROM asset_preference p WHERE p.asset_id=asset.id "
            f"AND p.profile_id='{DEFAULT_PROFILE_ID}'),0) AS liked,"
            "COALESCE((SELECT p.reason FROM asset_preference p WHERE p.asset_id=asset.id "
            f"AND p.profile_id='{DEFAULT_PROFILE_ID}'),'') AS like_reason,"
            "COALESCE((SELECT g.wanted FROM asset_quality_goal g WHERE g.asset_id=asset.id "
            f"AND g.profile_id='{DEFAULT_PROFILE_ID}'),0) AS better_version,"
            "COALESCE((SELECT g.reason FROM asset_quality_goal g WHERE g.asset_id=asset.id "
            f"AND g.profile_id='{DEFAULT_PROFILE_ID}'),'') AS better_version_reason,"
            "EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=asset.id "
            f"AND w.profile_id='{DEFAULT_PROFILE_ID}') AS watch_later FROM asset WHERE id=?", (aid,)).fetchone()
        if not r:
            return {"error": "not found"}
        d = dict(r)
        legacy = [x[0] for x in c.execute(
            "SELECT t.tag FROM asset_tag t WHERE t.asset_id=? AND "
            + tag_not_hidden("t.asset_id", "peach_normalize(t.tag)")
            + " ORDER BY t.tag", (aid,),
        )]
        canonical = list(c.execute(
            "SELECT DISTINCT e.id,e.kind,e.canonical_name FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=? "
            "AND e.kind IN ('tag','performer','creator','studio','series') "
            "AND (e.kind<>'tag' OR "
            + tag_not_hidden("ae.asset_id", "e.normalized_name") + ") "
            "ORDER BY e.kind,e.canonical_name", (aid,),
        ))
    canonical_tags = [name for _, kind, name in canonical if kind == "tag"]
    canonical_performers = [name for _, kind, name in canonical if kind == "performer"]
    canonical_creators = {
        normalize_entity_name(name)
        for _, kind, name in canonical if kind == "creator"
    }
    performers = canonical_performers or [
        tag[3:] for tag in legacy
        if tag.startswith("演员:")
        and normalize_entity_name(tag[3:]) not in canonical_creators
    ]
    performer_names = {normalize_entity_name(name) for name in performers}
    tags = [tag for tag in (canonical_tags or [
        tag for tag in legacy if not tag.startswith("演员:")
    ]) if normalize_entity_name(tag) not in performer_names]
    d["tags"] = [{"k": tag, "cat": tag_cat(tag)} for tag in tags if tag not in LENGTH_TAGS]
    d["performers"] = performers
    d["entities"] = {
        kind: [name for _, item_kind, name in canonical if item_kind == kind]
        for kind in ("creator", "performer", "studio", "series")
    }
    d["entity_refs"] = {
        kind: [{"id": entity_id, "name": name}
               for entity_id, item_kind, name in canonical if item_kind == kind]
        for kind in ("creator", "performer", "studio", "series")
    }
    if d["entities"]["creator"]:
        d["creator"] = d["entities"]["creator"][0]
    if d["entities"]["studio"]:
        d["studio"] = d["entities"]["studio"][0]
    d["cost"] = COST.get(d["location"], "metered")
    d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
    # 「女优」是番号发行物的行业称谓；creator clip 即使长得像番号也仍是普通内容。
    d["is_jav"] = is_jav_asset(
        d.get("code"), d.get("studio"), d.get("release_date"),
        [kind for kind, values in d["entities"].items() if values],
    )
    d.pop("snapshot_path", None); d.pop("path", None)
    return d

# 只认联系方式与站点形态的推广套话。「微信」「成人游戏」这类词单独出现不算：
# 实测正片标题里就有（「还要微信跟老公汇报战果」是剧情，不是联系方式）。
PROMO_PHRASE = re.compile(
    r"(扫码|二维码|加微信|加微|威信\d|微信号|微信\s*[:：]|免费看|免费玩|福利群|最新地址|"
    r"永久(?:域名|地址|发布)|点击(?:观看|下载|进入)|下载APP|下载|签到|代币|领取|"
    r"强力推荐|国产大片|在线视频|大饱眼福|房间火爆|澳门|赌场|博彩|棋牌|加我|包养|约炮|"
    r"GAMES?\d*|APP)", re.I)
# 结尾不能用 \b：`uuc82.com_2` 里 `m` 和 `_` 都是词字符，构不成边界，域名会漏掉。
PROMO_DOMAIN = re.compile(
    r"(?:https?://)?(?:www\.)?[\w-]{2,}\.(?:com|net|me|la|xyz|cc|tv|top|vip|club|"
    r"info|org|pw|cn|app|site|online|shop)(?![a-z0-9])", re.I)
# 真番号带厂牌前缀和连字号（ABW-153、259LUXU-1141）。RAIKUN325 这类没有连字号的
# 是被误填进 code 的创作者账号名，不能拿来做「同番号有完整版」的比较，
# 判据与 `is_jav_code` 同源：分隔符正是番号与账号名的唯一线索。
REAL_CODE = re.compile(r"^(?:\d{2,3})?[A-Za-z]{2,8}-\d{2,5}$|^FC2", re.I)
PART_MARK = re.compile(r"(CD\d|part\d|分卷|-\d{1,2}$|\(\d+\)$)", re.I)
# 推广站目录的两种形态，与 `scripts/find_ads.py` 的判据 D/E 同源：
# 创作者位是旧导入器的目录名投影，`bbsxv.xyz-DOCP-324` 这类广告包会直接落在那里；
# 裸域名目录（98T.la@账号、huachishe.com@系列）是转载水印，不是广告，不能进判据。
AD_DOMAIN = re.compile(
    r"\b[0-9a-z][-0-9a-z]{1,20}\.(?:cc|xyz|com|net|la|me|top|vip|club|app|cn|pw|tv|gg)\b", re.I)
AD_DIRPACK = re.compile(
    r"[0-9a-z][-0-9a-z]{1,20}\.[a-z]{2,10}[ \-_]+\[?[A-Za-z]{2,6}-?\d{2,5}", re.I)
INTERNET_SHORTCUT_SUFFIXES = frozenset({".url"})
JUNK_KINDS = frozenset({"video", "image", "audio", "archive", "url", "other"})


def promo_residue(name: str) -> int:
    """剥掉域名和推广套话后，还剩多少实质描述字符。

    这是区分「广告」与「正片被打了站点水印」的关键：
    `点击观看 房间火爆` 剥完什么都不剩；
    `236953.xyz 推特新晋4年绿帽美腿淫妻网黄「一个ren」…` 剥完仍有大段内容描述。
    """
    text = PROMO_DOMAIN.sub(" ", name or "")
    text = PROMO_PHRASE.sub(" ", text)
    # 只数中日韩文字与字母，忽略编号、扩展名和标点。
    return len(re.findall(r"[一-鿿぀-ヿ가-힯 A-Za-z]", text))


def q_ads(contract: WebContract, limit=200, offset=0, kind="", status="pending"):
    """疑似垃圾复核队列 —— **不自动删**，只排队让人看证据确认。

    没有可靠的单一判据（试过「同番号短版」会误伤 CD2/part1 分卷，
    试过「同名扩散」会误伤 001.mp4 这类通用名的真文件）。
    所以给的是**嫌疑分**，按分排序，人工看图定夺，确认的走既定 CSV 删除流程。

    2026-08-15 按用户标记的 21 条真广告重新标定：命中推广词本身不算证据，
    要看**剥掉推广词后还剩不剩内容**。三类实测误判据此排除：剧情里的「微信」、
    开头是盗版站域名但正文是真实描述、以及把创作者账号当成番号去比时长。

    物理资源的类型不能成为免检条件。视频保留时长、体积和同番号长版证据；图片、
    音频、压缩包和其它文件走共用的推广名／推广目录证据；Windows ``.url`` 是网址
    快捷方式，在媒体目录中直接进入人工复核。在线资产不是待清理的物理文件，排除。"""
    kind = str(kind or "").strip().casefold()
    status = str(status or "pending").strip().casefold()
    if kind and kind not in JUNK_KINDS:
        raise ValueError("invalid junk kind")
    if status not in {"pending", "dismissed"}:
        raise ValueError("invalid junk status")
    with contract.read_connection() as c:
        rows = c.execute(
            "SELECT id,location,name,medium,creator,code,size,duration,width,height,snapshot_path,"
            "feedback,disposal,play_count,leave_ratio,o_count,studio,ctx_orient,path "
            "FROM asset WHERE location IN ('local','115','pikpak') AND disposal IS NULL "
            "AND (COALESCE(medium,'other')<>'video' OR (size < 500*1024*1024 "
            "AND duration IS NOT NULL AND duration BETWEEN 15 AND 1200))").fetchall()
        # 同番号是否存在明显更长的版本；只在 code 是真番号时才有意义。
        longer = {r[0]: r[1] for r in c.execute(
            "SELECT code, max(duration) FROM asset WHERE medium='video' AND code IS NOT NULL "
            "AND code<>'' AND duration IS NOT NULL GROUP BY code")}
        dismissed_keys = [str(row[0]) for row in c.execute(
            "SELECT item_key FROM review_decision "
            "WHERE category='junk_file' AND status='rejected'"
        )]
        dismissed_ids = {int(key) for key in dismissed_keys if key.isdigit()}
    out = []
    for r in rows:
        d = dict(r)
        s, why = 0, []
        name = d.get("name") or PureWindowsPath(d.get("path") or "").name
        resource_path = PureWindowsPath(d.get("path") or name)
        name_path = PureWindowsPath(name)
        nm = name_path.stem
        suffix = name_path.suffix.casefold()
        d["junk_kind"] = (
            "url" if suffix in INTERNET_SHORTCUT_SUFFIXES
            else (d.get("medium") if d.get("medium") in JUNK_KINDS else "other")
        )
        residue = promo_residue(nm)
        promo = bool(PROMO_PHRASE.search(nm) or PROMO_DOMAIN.search(nm))
        if suffix in INTERNET_SHORTCUT_SUFFIXES:
            s += 60; why.append("网址快捷方式")
        # 目录维度的证据：广告包的文件名往往干净（`极道世界.mp4`），唯一线索在旧导入器
        # 从目录名投影出来的创作者位或路径里。creator 位本身是推广站域名时，它就不再是
        # 「有归属所以是正片」的证据，下面两处对 creator 的信任都必须先排除这种情况。
        owner = d.get("creator") or ""
        owner_is_promo = bool(AD_DOMAIN.search(owner))
        real_owner = bool(owner) and not owner_is_promo
        # ledger 路径在两个平台都是 Windows 形态；PureWindowsPath 才能让 macOS reader
        # 也识别反斜杠目录，os.path.dirname 在 macOS 会把整条路径当成文件名。
        folder = str(resource_path.parent)
        if promo and residue < 6:
            # 名字剥完只剩广告本身，这是最硬的信号。
            s += 60; why.append("整个名字都是推广语")
        elif promo and residue < 14 and not real_owner:
            s += 30; why.append("推广语占了名字主体")
        if owner_is_promo:
            s += 50; why.append("创作者位是推广站域名")
        elif AD_DIRPACK.search(folder):
            s += 45; why.append("目录是「域名+番号」的推广打包")
        if d.get("medium") == "video":
            code = (d["code"] or "").strip()
            mx = longer.get(code)
            if mx and REAL_CODE.match(code) and d["duration"] < mx * 0.2 \
                    and not PART_MARK.search(nm):
                # 分卷已排除，真番号下不到两成时长基本就是片段/预告，单独即可入队复核。
                # 用户标记的 `反抗不如享受.mp4`（ABW-220，244 秒）正好卡在旧的 35 分门外。
                s += 40; why.append(f"同番号有 {mx/60:.0f} 分完整版")
            if d["duration"] < 240:
                s += 15; why.append("不足 4 分钟")
            if (d["size"] or 0) < 120 * 1024**2:
                s += 10; why.append("小于 120 MB")
        # 有真实创作者归属、且名字剥完仍有实质描述的，是被打了水印的正片，不是广告。
        if real_owner and residue >= 14:
            s -= 45
        if s >= 40:
            d["score"] = s; d["why"] = " · ".join(why)
            d["cost"] = COST.get(d["location"], "metered")
            d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
            d.pop("snapshot_path", None)
            d.pop("path", None)
            out.append(d)
    out.sort(key=lambda x: (-x["score"], -(x["size"] or 0)))
    pending = [item for item in out if item["id"] not in dismissed_ids]
    dismissed = [item for item in out if item["id"] in dismissed_ids]
    pool = dismissed if status == "dismissed" else pending
    counts = {junk_kind: 0 for junk_kind in JUNK_KINDS}
    for item in pool:
        counts[item["junk_kind"]] += 1
    filtered = [item for item in pool if not kind or item["junk_kind"] == kind]
    items = filtered[offset:offset + limit]
    attach_card_performers(
        contract, [item for item in items if item.get("medium") == "video"])
    return {
        "total": len(filtered),
        "all_total": len(pool),
        "pending_total": len(pending),
        "dismissed_total": len(dismissed),
        "counts": counts,
        "kind": kind,
        "status": status,
        "items": items,
    }

def q_related(contract: WebContract, aid, limit=24):
    """接着看 —— 把口味接近的串成播放列表。
    优先级：同创作者 > 共享标签最多 > 同厂牌。全部排除已标记不合口味的。"""
    with contract.read_connection() as c:
        r = c.execute("SELECT id FROM asset WHERE id=?", (aid,)).fetchone()
        if not r:
            return {"items": []}
        entity_ids = {}
        for kind in ("creator", "tag", "studio"):
            entity_ids[kind] = [x[0] for x in c.execute(
                "SELECT DISTINCT ae.entity_id FROM asset_entity ae "
                "JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=? AND e.kind=?", (aid, kind),
            )]
        picked, seen = [], {aid}

        def take(sql, par, why):
            for row in c.execute(sql, par):
                d = dict(row)
                if d["id"] in seen or len(picked) >= limit:
                    continue
                seen.add(d["id"]); d["why"] = why; picked.append(d)

        COLS = ("id,location,name,creator,studio,code,size,duration,width,height,"
                "ctx_orient,snapshot_path,play_count,leave_ratio,feedback,disposal,o_count")
        base = (f"SELECT {COLS} FROM asset a WHERE a.medium='video' AND a.id<>? "
                "AND (a.feedback IS NULL OR a.feedback<>'dislike') AND a.disposal IS NULL")
        creators = entity_ids["creator"]
        if creators:
            qm = ",".join("?" * len(creators))
            take(base + f" AND EXISTS (SELECT 1 FROM asset_entity ae WHERE ae.asset_id=a.id "
                 f"AND ae.entity_id IN ({qm})) "
                 "ORDER BY (a.play_count IS NULL OR a.play_count=0) DESC, random() LIMIT ?",
                 tuple([aid] + creators + [limit]), "同创作者")
        tags = entity_ids["tag"]
        if tags and len(picked) < limit:
            qm = ",".join("?" * len(tags))
            take(f"SELECT {COLS} FROM asset a WHERE a.medium='video' AND a.id<>? "
                 f"AND (a.feedback IS NULL OR a.feedback<>'dislike') AND a.disposal IS NULL "
                 f"AND (SELECT count(DISTINCT ae.entity_id) FROM asset_entity ae "
                 f"WHERE ae.asset_id=a.id AND ae.entity_id IN ({qm})) >= "
                 f"{max(1, min(2, len(tags)))} "
                 "ORDER BY (a.play_count IS NULL OR a.play_count=0) DESC, random() LIMIT ?",
                 tuple([aid] + tags + [limit]), "标签接近")
        studios = entity_ids["studio"]
        if studios and len(picked) < limit:
            qm = ",".join("?" * len(studios))
            take(base + f" AND EXISTS (SELECT 1 FROM asset_entity ae WHERE ae.asset_id=a.id "
                 f"AND ae.entity_id IN ({qm})) ORDER BY random() LIMIT ?",
                 tuple([aid] + studios + [limit]), "同厂牌")
    attach_card_performers(contract, picked)
    for d in picked:
        d["cost"] = COST.get(d["location"], "metered")
        d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
        d.pop("snapshot_path", None)
    return {"items": picked[:limit]}

#: JAV 语境下的资产过滤片段。番号形态必须再有发行证据；否则 JI-103 这类
#: creator clip 会混入 JAV。FC2 本身就是明确的发行 ID，单独保留。
JAV_ASSET_PREDICATE = (
    "a.code IS NOT NULL AND a.code<>'' AND is_jav_code(a.code) AND ("
    "upper(trim(a.code)) LIKE 'FC2%' OR COALESCE(trim(a.studio),'')<>'' "
    "OR COALESCE(trim(a.release_date),'')<>'' OR EXISTS("
    "SELECT 1 FROM asset_entity jav_ae JOIN entity jav_e ON jav_e.id=jav_ae.entity_id "
    "WHERE jav_ae.asset_id=a.id AND jav_e.kind IN ('performer','studio','series')))"
)
JAV_ASSET_CLAUSE = "AND " + JAV_ASSET_PREDICATE + " "


#: 首页的状态筛选（新鲜 / 看过 / 已标记 / 稍后看）。作品列表、顶部三层和筛选面板
#: 必须用同一份口径：否则「已标记」页会列出全库的人物、厂牌和标签，点进去却是空的。
def state_predicate(state: str) -> str:
    """返回这个状态对应的 SQL 谓词（已加括号，不含 `AND`）；未知状态返回空串。"""
    if state == "fresh":
        return "((a.play_count IS NULL OR a.play_count=0) AND a.feedback IS NULL)"
    if state == "played":
        return "(a.play_count > 0)"
    if state == "flagged":
        return ("(COALESCE(a.o_count,0)>0 OR EXISTS(SELECT 1 FROM asset_preference p "
                f"WHERE p.asset_id=a.id AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.liked=1))")
    if state == "later":
        return ("(EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=a.id "
                f"AND w.profile_id='{DEFAULT_PROFILE_ID}'))")
    return ""


def state_clause(state: str) -> str:
    """同一个谓词的 `AND ...` 形式，给拼在 WHERE 后面的查询用。"""
    predicate = state_predicate(state)
    return f"AND {predicate} " if predicate else ""


#: 顶部三层的候选池相对展示位的倍数。严格取前 N 会让这一条永远是同一批人——
#: 「换一批」刷新后上面纹丝不动。放大候选池再按种子确定性抽样，既保持是常见身份，
#: 又能真的换一批。倍数太大就会开始出现只有一两部作品的冷门项。
TOPS_POOL_FACTOR = 4


def q_tops(contract: WebContract, n=28, jav=False, seed="", state=""):
    """顶部三层用的数据：女优圆头像 / 厂牌 / 内容标签。

    缓存的人物肖像由前端优先使用；缺失时才回退到代表作接触印相裁切。

    `state` 跟作品列表同一份口径：在「已标记」这类页面上，上面这排头像
    只应该出现真的有已标记作品的人，否则点进去是空的。"""
    with contract.read_connection() as c:
        scope = (JAV_ASSET_CLAUSE if jav else "") + state_clause(state)
        base = (
            "SELECT e.id,e.canonical_name,count(DISTINCT ae.asset_id) n,"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE ae2.entity_id=e.id AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY (a2.play_count IS NULL),a2.size DESC LIMIT 1) rep "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id "
            "WHERE a.medium='video' AND e.kind=? " + scope +
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT ?"
        )

        def pick(kind):
            """按数量取候选池，再按种子确定性抽样。种子为空时退回严格前 N。"""
            pool = [{"id": entity_id, "k": k, "n": cnt, "rep": representative}
                    for entity_id, k, cnt, representative
                    in c.execute(base, (kind, n * TOPS_POOL_FACTOR if seed else n))]
            if not seed or len(pool) <= n:
                return pool[:n]
            # 同一个种子必须给出同一批人：翻页和重绘之间不能抖动。
            digest = hashlib.blake2b(f"{seed}:{kind}".encode(), digest_size=8).digest()
            rng = random.Random(int.from_bytes(digest, "big"))
            chosen = rng.sample(pool, n)
            # 抽完仍按数量排序，免得常见身份被排到末尾。
            return sorted(chosen, key=lambda row: -row["n"])

        out = {}
        out["performers"] = pick("performer")
        out["studios"] = pick("studio")
    return out


def q_entity(contract: WebContract, args):
    """女优、厂牌、创作者等实体的资料页。

    `source_reference` 是私人馆藏来源证据：API 只返回站点名和备注，不把敏感下载
    地址变成可点击链接。官方、社交和资料库链接可直接访问。
    """
    kind = args.get("kind", "")
    name = args.get("name", "")
    if kind not in {"performer", "studio", "creator", "series"} or not name:
        return {"error": "invalid entity"}
    with contract.read_connection() as c:
        row = resolve_entity(c, kind, name)
        if not row:
            return {"error": "not found"}
        d = dict(row)
        try:
            metadata = json.loads(d.pop("metadata_json") or "{}")
        except (TypeError, ValueError):
            metadata = {}
        d["summary"] = metadata.get("summary") or ""
        d["metadata"] = {k: v for k, v in metadata.items() if k != "summary"}
        d["aliases"] = [r[0] for r in c.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=? ORDER BY confidence DESC,alias",
            (d["id"],),
        )]
        # 罗马字仍是检索和旧链接的重要身份键，但中文/日文规范名下面再把英文全列一遍
        # 只会像名称没有本地化。展示契约单独收窄，身份契约 `aliases` 保持完整。
        d["display_aliases"] = _display_entity_aliases(
            d["canonical_name"], d["aliases"])
        links = []
        for link in c.execute(
            "SELECT link_kind,label,url,hostname,is_sensitive,metadata_json "
            "FROM entity_link WHERE entity_id=? ORDER BY link_kind,label", (d["id"],),
        ):
            item = dict(link)
            host = item["hostname"] or urlsplit(item["url"]).hostname or ""
            sensitive = bool(item.pop("is_sensitive")) or item["link_kind"] == "source_reference"
            item["hostname"] = host
            item["clickable"] = not sensitive
            if sensitive:
                item["url"] = None
            try:
                item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            except (TypeError, ValueError):
                item["metadata"] = {}
            links.append(item)
        d["links"] = links
        d["search_terms"] = [dict(r) for r in c.execute(
            "SELECT term,purpose,source FROM entity_search_term WHERE entity_id=? "
            "ORDER BY purpose,term", (d["id"],),
        )]
        d["external_refs"] = [dict(r) for r in c.execute(
            "SELECT provider,external_kind,external_id,last_synced_at "
            "FROM entity_external_ref WHERE entity_id=? ORDER BY provider,external_kind",
            (d["id"],),
        )]
        count, rep = c.execute(
            "SELECT count(DISTINCT ae.asset_id),"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE ae2.entity_id=? AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY a2.size DESC LIMIT 1) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE ae.entity_id=? AND a.medium='video'", (d["id"], d["id"]),
        ).fetchone()
        d["asset_count"] = count
        d["representative_asset_id"] = rep
        d["avatar_focus"] = contract.avatar_focus(kind, d["id"])
        d["tags"] = [dict(r) for r in c.execute(
            "SELECT tag.id,tag.canonical_name k,count(DISTINCT scope.asset_id) n "
            "FROM asset_entity scope "
            "JOIN asset_entity tagged ON tagged.asset_id=scope.asset_id "
            "JOIN entity tag ON tag.id=tagged.entity_id "
            "JOIN asset a ON a.id=scope.asset_id "
            "WHERE scope.entity_id=? AND a.medium='video' AND tag.kind='tag' "
            "AND " + tag_is_not_a_performer_name("tag.normalized_name") + " "
            f"AND tag.canonical_name NOT IN ({','.join('?' for _ in LENGTH_TAGS)}) "
            "AND " + tag_not_hidden("scope.asset_id", "tag.normalized_name") + " "
            "GROUP BY tag.id,tag.canonical_name ORDER BY n DESC,tag.canonical_name LIMIT 36",
            (d["id"], *sorted(LENGTH_TAGS)),
        )]
        related = []
        for performer in c.execute(
            "SELECT person.id,person.canonical_name k,count(DISTINCT scope.asset_id) n,"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE ae2.entity_id=person.id AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY COALESCE(a2.play_count,0) DESC,COALESCE(a2.play_seconds,0) DESC,"
            " COALESCE(a2.width,0)*COALESCE(a2.height,0) DESC,a2.size DESC LIMIT 1) rep "
            "FROM asset_entity scope "
            "JOIN asset_entity co ON co.asset_id=scope.asset_id "
            "JOIN entity person ON person.id=co.entity_id "
            "JOIN asset a ON a.id=scope.asset_id "
            "WHERE scope.entity_id=? AND a.medium='video' AND person.kind='performer' "
            "AND person.id<>? "
            "GROUP BY person.id,person.canonical_name ORDER BY n DESC,person.canonical_name LIMIT 18",
            (d["id"], d["id"]),
        ):
            related.append(dict(performer))
        d["related_performers"] = related
    return d

# ────────────────────────────── 照片 ──────────────────────────────
# 图集就是目录：账本没有图集实体，一个目录下的图片本来就是一份图集，
# `<作品目录>\P\001.jpg` 这种约定在 A:/B: 上到处都是。图集的 id 用目录里最小的
# 资产 id，既稳定又不用把真实路径发给前端（`q_item` 同样不发 `path`）。

#: 图集查询一律带 `a.` 别名。
PHOTO_DIR = dir_expr()


def _display_entity_aliases(canonical_name: str, aliases: list[str]) -> list[str]:
    """本地化规范名不重复展示纯拉丁转写；原始别名仍完整保留在 API。"""
    east_asian = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
    canonical_key = normalize_entity_name(canonical_name)
    unique_aliases = [alias for alias in aliases
                      if normalize_entity_name(alias) != canonical_key]
    if not east_asian.search(canonical_name or ""):
        return unique_aliases
    return [alias for alias in unique_aliases
            if east_asian.search(alias or "") or not re.search(r"[A-Za-z]", alias or "")]


def q_entity_photos(contract: WebContract, args):
    """实体名下的图片瀑布流；目录分组只保留为兼容元数据。"""
    kind, name = args.get("kind", ""), args.get("name", "")
    if kind not in {"performer", "studio", "creator", "series"} or not name:
        return {"error": "invalid entity"}
    try:
        limit = max(1, min(int(args.get("limit") or 120), 600))
        offset = max(0, int(args.get("offset") or 0))
    except (TypeError, ValueError):
        return {"error": "invalid pagination"}
    with contract.read_connection() as c:
        row = resolve_entity(c, kind, name)
        if not row:
            return {"error": "not found"}
        sets = [{
            "id": item["id"],
            "title": photo_set_title(item["dir"]),
            "n": item["n"],
            "bytes": item["bytes"] or 0,
            "location": item["location"],
            "cost": COST.get(item["location"], "metered"),
        } for item in c.execute(
            f"SELECT {PHOTO_DIR} dir,min(a.id) id,count(*) n,sum(a.size) bytes,a.location "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE ae.entity_id=? AND a.medium='image' AND a.name IS NOT NULL "
            "AND (a.disposal IS NULL OR a.disposal<>'trash') "
            f"GROUP BY {PHOTO_DIR},a.location ORDER BY n DESC,dir",
            (row["id"],),
        )]
        total = c.execute(
            "SELECT count(DISTINCT a.id) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE ae.entity_id=? AND a.medium='image' AND a.name IS NOT NULL "
            "AND (a.disposal IS NULL OR a.disposal<>'trash')",
            (row["id"],),
        ).fetchone()[0]
        items = [{"id": item["id"], "name": item["name"], "size": item["size"] or 0,
                  "location": item["location"]}
                 for item in c.execute(
                     f"SELECT a.id,a.name,a.size,a.location,{PHOTO_DIR} dir "
                     "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
                     "WHERE ae.entity_id=? AND a.medium='image' AND a.name IS NOT NULL "
                     "AND (a.disposal IS NULL OR a.disposal<>'trash') "
                     f"GROUP BY a.id,a.name,a.size,a.location,{PHOTO_DIR} "
                     "ORDER BY dir,a.name,a.id LIMIT ? OFFSET ?",
                     (row["id"], limit, offset),
                 )]
        return {
            "kind": kind, "name": row["canonical_name"], "entity_id": row["id"],
            "sets": sets, "total": total, "items": items,
            "has_more": offset + len(items) < total,
        }


def q_photo_set(contract: WebContract, args):
    """一个图集里的图片。按文件名排，`001.jpg` 这类编号才不会乱序。"""
    try:
        set_id = int(args.get("id", ""))
    except (TypeError, ValueError):
        return {"error": "invalid id"}
    limit = max(1, min(int(args.get("limit") or 120), 600))
    offset = max(0, int(args.get("offset") or 0))
    with contract.read_connection() as c:
        anchor = c.execute(
            "SELECT id,location,path,name FROM asset "
            "WHERE id=? AND medium='image' AND name IS NOT NULL", (set_id,),
        ).fetchone()
        if not anchor:
            return {"error": "not found"}
        directory = anchor["path"][: len(anchor["path"]) - len(anchor["name"]) - 1]
        par = (directory, anchor["location"])
        total = c.execute(
            f"SELECT count(*) FROM asset a WHERE a.medium='image' AND a.name IS NOT NULL "
            f"AND {PHOTO_DIR}=? AND a.location=? "
            "AND (a.disposal IS NULL OR a.disposal<>'trash')", par,
        ).fetchone()[0]
        items = [{"id": item["id"], "name": item["name"], "size": item["size"] or 0,
                  "location": item["location"]}
                 for item in c.execute(
                     f"SELECT a.id,a.name,a.size,a.location FROM asset a WHERE a.medium='image' "
                     f"AND a.name IS NOT NULL AND {PHOTO_DIR}=? AND a.location=? "
                     "AND (a.disposal IS NULL OR a.disposal<>'trash') "
                     "ORDER BY a.name,a.id LIMIT ? OFFSET ?",
                     (*par, limit, offset),
                 )]
        return {
            "id": anchor["id"], "title": photo_set_title(directory),
            "location": anchor["location"], "cost": COST.get(anchor["location"], "metered"),
            "total": total, "items": items, "has_more": offset + len(items) < total,
        }


def q_index(contract: WebContract, kind, q="", limit=600, offset=0, category=""):
    """全部艺人 / 创作者 / 标签的索引页数据。"""
    with contract.read_connection() as c:
        if kind in {"creators", "performers"}:
            entity_kind = "creator" if kind == "creators" else "performer"
            sql = ("SELECT e.id entity_id,e.canonical_name k,count(DISTINCT ae.asset_id) n,"
                   "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
                   " WHERE ae2.entity_id=e.id AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
                   " ORDER BY COALESCE(a2.play_count,0) DESC,COALESCE(a2.play_seconds,0) DESC,"
                   " COALESCE(a2.width,0)*COALESCE(a2.height,0) DESC,a2.size DESC LIMIT 1) rep "
                   "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                   "JOIN asset a ON a.id=ae.asset_id "
                   "WHERE a.medium='video' AND e.kind=? ")
            par = [entity_kind]
            if q: sql += "AND e.canonical_name LIKE ? "; par.append(f"%{q}%")
            sql += "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT ? OFFSET ?"
            par.extend((limit + 1, offset))
            rows = [dict(r) for r in c.execute(sql, par)]
            has_more = len(rows) > limit
            rows = rows[:limit]
        else:
            sql = ("SELECT e.canonical_name k, count(DISTINCT ae.asset_id) n "
                   "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                   "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='tag' "
                   f"AND e.canonical_name NOT IN ({','.join('?' for _ in LENGTH_TAGS)}) "
                   "AND " + tag_is_not_a_performer_name("e.normalized_name") + " "
                   "AND " + tag_not_hidden("ae.asset_id", "e.normalized_name") + " ")
            par = sorted(LENGTH_TAGS)
            if q: sql += "AND e.canonical_name LIKE ? "; par.append(f"%{q}%")
            sql += "GROUP BY e.id,e.canonical_name ORDER BY n DESC"
            all_rows = [dict(r, cat=tag_cat(r["k"])) for r in c.execute(sql, par)]
            category_counts: dict[str, int] = {}
            for row in all_rows:
                category_counts[row["cat"]] = category_counts.get(row["cat"], 0) + 1
            if category and category != "all":
                all_rows = [row for row in all_rows if row["cat"] == category]
            rows = all_rows[offset:offset + limit]
            has_more = offset + limit < len(all_rows)
    result = {"kind": kind, "items": rows, "has_more": has_more}
    if kind == "tags":
        result["categories"] = category_counts
    return result

_STORAGE_LABELS = {
    "system": "系统盘",
    "local": "资源盘",
    "115": "115 网盘",
    "pikpak": "PikPak 网盘",
}


def _storage_volumes() -> list[dict[str, object]]:
    """返回当前主机可验证的系统卷、资源盘和网盘容量。"""
    declarations = [("system", system_volume(), True)] + [
        (location, translate_ledger_path(root), False)
        for location, root in LOCATION_ROOT_DECLARATIONS.items()
    ]
    volumes: list[dict[str, object]] = []
    for kind, root, is_system in declarations:
        mounted = not is_unmapped(root) and (is_system or root_online(root))
        row: dict[str, object] = {
            "kind": kind,
            "label": _STORAGE_LABELS[kind],
            "root": str(root) if not is_unmapped(root) else None,
            "online": mounted,
            "free": None,
            "used": None,
            "total": None,
        }
        if mounted:
            try:
                usage = shutil.disk_usage(root)
                row.update(
                    free=usage.free,
                    used=max(usage.total - usage.free, 0),
                    total=usage.total,
                )
            except OSError:
                pass
        volumes.append(row)
    return volumes


def q_stats(contract: WebContract):
    """统计页：库存 / 归属 / 标签 / 本地与在线播放 / 各存储卷。"""
    with contract.read_connection() as c:
        out = {}
        out["by_loc"] = [dict(r) for r in c.execute(
            "SELECT location k, count(*) n, COALESCE(sum(size),0) bytes, "
            "SUM(CASE WHEN medium='video' THEN 1 ELSE 0 END) videos "
            "FROM asset GROUP BY location ORDER BY bytes DESC")]
        out["by_medium"] = [dict(r) for r in c.execute(
            "SELECT medium k, count(*) n, COALESCE(sum(size),0) bytes "
            "FROM asset GROUP BY medium ORDER BY bytes DESC")]
        v = c.execute("SELECT count(*) FROM asset WHERE medium='video'").fetchone()[0]
        def one(sql, *a):
            r = c.execute(sql, a).fetchone()
            return r[0] if r else 0
        out["attribution"] = {
            "videos": v,
            "creator": one("SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae "
                           "JOIN entity e ON e.id=ae.entity_id JOIN asset a ON a.id=ae.asset_id "
                           "WHERE a.medium='video' AND e.kind='creator'"),
            "code": one("SELECT count(*) FROM asset WHERE medium='video' AND code IS NOT NULL AND code<>''"),
            "studio": one("SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae "
                          "JOIN entity e ON e.id=ae.entity_id JOIN asset a ON a.id=ae.asset_id "
                          "WHERE a.medium='video' AND e.kind='studio'"),
            "thumb": one("SELECT count(*) FROM asset WHERE medium='video' AND snapshot_path IS NOT NULL"),
            "duration": one("SELECT count(*) FROM asset WHERE medium='video' AND duration IS NOT NULL"),
        }
        out["tag_source"] = [dict(r) for r in c.execute(
            "SELECT source k, count(*) n, count(DISTINCT asset_id) assets "
            "FROM asset_tag GROUP BY source ORDER BY n DESC")]
        out["tag_cov"] = one("SELECT count(DISTINCT asset_id) FROM asset_tag "
                             "WHERE source IN ('name','r18','vision','vision-creator',"
                             "'vision_creator','vision_creator_review')")
        out["top_tags"] = [dict(r, cat=tag_cat(r["k"])) for r in c.execute(
            "SELECT t.tag k, count(*) n FROM asset_tag t JOIN asset a ON a.id=t.asset_id "
            "WHERE a.medium='video' AND t.source IN ('name','r18','vision','vision-creator',"
            "'vision_creator','vision_creator_review') "
            "AND " + tag_is_not_a_performer_name("peach_normalize(t.tag)") + " "
            "GROUP BY t.tag ORDER BY n DESC LIMIT 30")]
        tables = {row[0] for row in c.execute(
            "SELECT name FROM sqlite_schema WHERE type='table'"
        )}
        library_played = one("SELECT count(*) FROM asset WHERE play_count>0")
        library_seconds = one("SELECT COALESCE(sum(play_seconds),0) FROM asset")
        online_played = 0
        online_seconds = 0
        if "follow_playback" in tables:
            online_played = one(
                "SELECT count(*) FROM follow_playback fp JOIN follow_item fi "
                "ON fi.id=fp.follow_item_id WHERE fp.play_count>0 AND (fi.asset_id IS NULL OR "
                "NOT EXISTS(SELECT 1 FROM asset a WHERE a.id=fi.asset_id AND a.play_count>0))"
            )
            online_seconds = one(
                "SELECT COALESCE(sum(play_seconds),0) FROM follow_playback"
            )
        out["consumption"] = {
            "played": library_played + online_played,
            "library_played": library_played,
            "online_played": online_played,
            "play_seconds": library_seconds + online_seconds,
            "library_play_seconds": library_seconds,
            "online_play_seconds": online_seconds,
            "o_total": one("SELECT COALESCE(sum(o_count),0) FROM asset"),
            "dislike": one("SELECT count(*) FROM asset WHERE feedback='dislike'"),
            "seen": one("SELECT count(*) FROM asset WHERE feedback='seen'"),
            "trash": one("SELECT count(*) FROM asset WHERE disposal='trash'"),
            "skimmed": one("SELECT count(*) FROM asset WHERE duration>0 AND play_seconds>0 "
                           "AND max_reached>0.6 AND play_seconds/duration < max_reached-0.25"),
        }
        recent = [dict(r, kind="library") for r in c.execute(
            "SELECT id,name,creator,play_seconds,duration,max_reached,leave_ratio,o_count,"
            "CAST(last_played AS REAL) last_played FROM asset WHERE last_played IS NOT NULL "
            "ORDER BY CAST(last_played AS REAL) DESC LIMIT 12")]
        if "follow_playback" in tables:
            recent.extend(dict(r, kind="online", leave_ratio=None, o_count=0) for r in c.execute(
                "SELECT fi.id,fi.title name,fs.label creator,fp.play_seconds,fi.duration,"
                "fp.max_reached,fp.last_played FROM follow_playback fp "
                "JOIN follow_item fi ON fi.id=fp.follow_item_id "
                "JOIN follow_source fs ON fs.id=fi.source_id WHERE fp.last_played IS NOT NULL "
                "ORDER BY fp.last_played DESC LIMIT 12"
            ))
        out["recent"] = sorted(
            recent, key=lambda row: float(row.get("last_played") or 0), reverse=True,
        )[:12]
    out["storage_volumes"] = _storage_volumes()
    measured = [row for row in out["storage_volumes"] if row["total"] is not None]
    out["storage_summary"] = {
        "volumes": len(out["storage_volumes"]),
        "online": sum(1 for row in out["storage_volumes"] if row["online"]),
        "measured": len(measured),
        "free": sum(int(row["free"]) for row in measured),
        "used": sum(int(row["used"]) for row in measured),
        "total": sum(int(row["total"]) for row in measured),
    }
    system = next((row for row in out["storage_volumes"] if row["kind"] == "system"), None)
    out["system_disk"] = (
        {"root": system["root"], "free": system["free"], "total": system["total"]}
        if system and system["total"] is not None else None
    )
    out["disk_c"] = out["system_disk"]  # 0.6.x 客户端兼容别名
    return out




def q_facets(
    contract: WebContract,
    jav: bool = False,
    scope_kind: str = "",
    scope_name: str = "",
    asset_id: int | None = None,
    state: str = "",
):
    """返回当前浏览集合真正存在的筛选项。

    首页不带 scope，维持全库口径；实体资料页按规范实体收窄，详情页按单个作品收窄。
    筛选项必须来自和作品列表相同的规范关系，不能让前端拿全库 facets 猜当前页面。
    """
    with contract.read_connection() as c:
        scope = (JAV_ASSET_CLAUSE if jav else "") + state_clause(state)
        scope_params: list[object] = []
        if asset_id is not None:
            scope += "AND a.id=? "
            scope_params.append(int(asset_id))
        elif scope_kind or scope_name:
            if scope_kind not in {"creator", "performer", "studio", "series"} or not scope_name:
                raise ValueError("invalid facet scope")
            scope += (
                "AND EXISTS(SELECT 1 FROM asset_entity scope_ae "
                "JOIN entity scope_e ON scope_e.id=scope_ae.entity_id "
                "WHERE scope_ae.asset_id=a.id AND scope_e.kind=? "
                "AND scope_e.canonical_name=?) "
            )
            scope_params.extend((scope_kind, scope_name))
        out = {}
        out["locations"] = [dict(r) for r in c.execute(
            "SELECT a.location AS k, count(*) AS n, "
            "SUM(CASE WHEN a.play_count>0 THEN 1 ELSE 0 END) AS played "
            "FROM asset a WHERE a.medium='video' " + scope +
            "GROUP BY a.location ORDER BY n DESC", scope_params)]
        out["orientations"] = [dict(r) for r in c.execute(
            "SELECT a.ctx_orient AS k,count(*) AS n FROM asset a "
            "WHERE a.medium='video' AND a.ctx_orient IS NOT NULL AND a.ctx_orient<>'' " + scope +
            "GROUP BY a.ctx_orient ORDER BY n DESC", scope_params)]
        out["creators"] = [dict(r) for r in c.execute(
            "SELECT e.canonical_name AS k,count(DISTINCT ae.asset_id) AS n "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='creator' " + scope +
        
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 60", scope_params)]
        # 标签要分层 —— 原来一锅端，结果「演员:一个ren」和「1080P」「足交」混在一起。
        # 三类分开：技术规格（画质/时长/画幅，筛选价值低）、内容维度（真正有用的）、演员（另立一栏）。
        rows = [dict(r) for r in c.execute(
            "SELECT e.canonical_name AS k, count(DISTINCT ae.asset_id) AS n "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='tag' " + scope +
            "AND " + tag_is_not_a_performer_name("e.normalized_name") + " "
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 400", scope_params)]
        classified = [
            dict(r, cat=tag_cat(r["k"]))
            for r in rows
            if r["k"] not in LENGTH_TAGS
        ]
        out["tags"] = [r for r in classified if r["cat"] != "meta"][:44]
        out["tech"] = [r for r in classified if r["cat"] == "meta"][:16]
        out["tagperformers"] = [dict(r) for r in c.execute(
            "SELECT e.canonical_name AS k,count(DISTINCT ae.asset_id) AS n "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='performer' " + scope +
        
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 20", scope_params)]
        st = c.execute(
            "SELECT count(*) total, COALESCE(sum(size),0) bytes, "
            "SUM(CASE WHEN duration IS NOT NULL THEN 1 ELSE 0 END) duration, "
            "SUM(CASE WHEN play_count>0 THEN 1 ELSE 0 END) played, "
            "SUM(CASE WHEN COALESCE(o_count,0)>0 OR EXISTS(SELECT 1 FROM asset_preference p "
            f"WHERE p.asset_id=a.id AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.liked=1) "
            "THEN 1 ELSE 0 END) flagged, "
            "SUM(EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='creator')) attributed "
            "FROM asset a WHERE a.medium='video' AND (a.disposal IS NULL OR a.disposal<>'trash') "
            + scope, scope_params).fetchone()
        out["stats"] = dict(st)
    return out

# ────────────────────────────── 写入 ──────────────────────────────

def w_item_tag(contract: WebContract, body):
    """新增或隐藏单条资源标签；隐藏不销毁刮削/识别来源证据。"""
    contract.cache_bust()
    aid = int(body["id"])
    operation = str(body.get("operation", "")).strip()
    tag = str(body.get("tag", "")).strip()
    if operation not in {"add", "remove"}:
        raise ValueError("operation must be add or remove")
    if not tag or len(tag) > 80 or tag.startswith("演员:"):
        raise ValueError("tag must be 1 to 80 characters and cannot be a performer marker")
    normalized = normalize_entity_name(tag)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # 事务边界只有一个入口：write_transaction 自己取 database.write_lock 并在异常时回滚。
    # 这里曾经手取同一把不可重入的锁再手动 commit/close，任何 execute 抛出都会漏掉
    # 回滚和关闭；也正因为那把锁是同一把，直接改调 write_transaction 而不撤掉外层
    # with 会自死锁。
    with contract.write_transaction() as c:
        if not c.execute("SELECT 1 FROM asset WHERE id=?", (aid,)).fetchone():
            raise ValueError("asset not found")
        if operation == "remove":
            c.execute(
                "INSERT INTO asset_tag_preference(profile_id,asset_id,normalized_tag,hidden,updated_at) "
                f"VALUES('{DEFAULT_PROFILE_ID}',?,?,1,?) ON CONFLICT(profile_id,asset_id,normalized_tag) "
                "DO UPDATE SET hidden=1,updated_at=excluded.updated_at",
                (aid, normalized, stamp),
            )
        else:
            c.execute(
                f"DELETE FROM asset_tag_preference WHERE profile_id='{DEFAULT_PROFILE_ID}' "
                "AND asset_id=? AND normalized_tag=?", (aid, normalized),
            )
            c.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "VALUES(?,?,1.0,'web-user')", (aid, tag),
            )
            upsert_asset_entity(
                c, kind="tag", name=tag, asset_id=aid, role="tag",
                source="web-user", confidence=1.0,
                metadata={"profile_id": DEFAULT_PROFILE_ID}, now=stamp,
            )
    return {"ok": True, "operation": operation, "tag": tag,
            "tags": [item["k"] for item in q_item(contract, aid)["tags"]]}


def _restore_staged_media(staged):
    """Undo same-directory quarantine moves after a database failure."""
    for original, quarantine in reversed(staged):
        if quarantine.exists() and not original.exists():
            os.replace(quarantine, original)


def _finish_purge(outcome):
    """Delete committed quarantine files; report any residue for explicit cleanup."""
    cleanup_pending = []
    for _original, quarantine in outcome.pop("_staged"):
        try:
            quarantine.unlink(missing_ok=True)
        except OSError as error:
            cleanup_pending.append({
                "path": str(quarantine), "reason": error.strerror or str(error),
            })
    for snapshot in outcome.pop("_snapshots"):
        try:
            snapshot.unlink(missing_ok=True)
        except OSError:
            pass
    outcome["cleanup_pending"] = cleanup_pending
    return outcome


def purge_assets(connection, rows):
    """Quarantine media, delete ledger rows, and leave final removal to the caller.

    Renaming beside the source is reversible and stays on the same filesystem. The
    caller restores the quarantined names if commit fails, then permanently removes
    them only after the SQLite transaction has committed.
    """
    purged, blocked, staged, snapshots = [], [], [], []
    for row in rows:
        media = row["path"]
        if media:
            original = Path(media)
            try:
                if original.exists() and not original.is_file():
                    raise OSError("not a regular file")
                if original.is_file():
                    quarantine = original.with_name(
                        f".{original.name}.peach-purge-{uuid.uuid4().hex}.tmp"
                    )
                    os.replace(original, quarantine)
                    staged.append((original, quarantine))
            except OSError as error:
                blocked.append({"id": row["id"], "path": media,
                                "reason": error.strerror or str(error)})
                continue
        snapshot = row["snapshot_path"]
        if snapshot:
            snapshots.append(Path(snapshot))
        purged.append(row["id"])
    try:
        if purged:
            marks = ",".join("?" * len(purged))
            connection.execute(
                f"UPDATE playlist SET current_asset_id=NULL WHERE current_asset_id IN ({marks})",
                purged,
            )
            connection.execute(
                f"UPDATE playlist SET source_seed_asset_id=NULL WHERE source_seed_asset_id IN ({marks})",
                purged,
            )
            for table in ASSET_REFERENCE_TABLES:
                connection.execute(f"DELETE FROM {table} WHERE asset_id IN ({marks})", purged)
            connection.execute(f"DELETE FROM asset WHERE id IN ({marks})", purged)
    except BaseException:
        _restore_staged_media(staged)
        raise
    return {
        "purged": len(purged), "blocked": blocked,
        "_staged": staged, "_snapshots": snapshots,
    }


def w_empty_trash(contract: WebContract):
    """永久清空回收站：只处理 disposal='trash' 的资产，其余一律不碰。"""
    contract.cache_bust()
    outcome = None
    try:
        with contract.write_transaction() as connection:
            rows = connection.execute(
                "SELECT id,path,snapshot_path FROM asset WHERE disposal='trash'",
            ).fetchall()
            outcome = purge_assets(connection, rows)
    except BaseException:
        if outcome is not None:
            _restore_staged_media(outcome["_staged"])
        raise
    result = {"ok": True, "operation": "empty-trash", **_finish_purge(outcome)}
    result.update(clean_resource_orphans(contract))
    return result




def w_batch(contract: WebContract, body):
    """Apply one explicit, reversible marker to a bounded selected set."""
    raw_ids = body.get("ids")
    if not isinstance(raw_ids, list):
        raise TypeError("ids must be a list")
    ids = list(dict.fromkeys(int(item) for item in raw_ids))
    if not ids or len(ids) > 200:
        raise ValueError("batch requires 1 to 200 assets")
    operation = body.get("operation")
    if operation not in {
        "like", "seen", "later", "dispose", "restore", "delete",
        "dismiss-junk", "reconsider-junk",
    }:
        raise ValueError("unsupported batch operation")
    marks = ",".join("?" * len(ids))
    contract.cache_bust()
    purge_outcome = None
    try:
        with contract.write_transaction() as connection:
            found = connection.execute(
                f"SELECT id,path,snapshot_path,disposal,location FROM asset WHERE id IN ({marks})", ids,
            ).fetchall()
            valid_ids = [row["id"] for row in found]
            if not valid_ids:
                raise ValueError("assets not found")
            if operation in {"restore", "delete"} and any(row["disposal"] != "trash" for row in found):
                raise ValueError("restore/delete is only allowed for recycle-bin assets")
            if operation in {"dismiss-junk", "reconsider-junk"} and any(
                    row["location"] not in {"local", "115", "pikpak"}
                    or row["disposal"] is not None for row in found):
                raise ValueError("junk decisions are only allowed for active physical assets")
            now = time.time()
            if operation == "restore":
                placeholders = ",".join("?" * len(valid_ids))
                connection.execute(
                    f"UPDATE asset SET disposal=NULL,feedback_at=? WHERE id IN ({placeholders})",
                    [now, *valid_ids],
                )
            elif operation == "delete":
                purge_outcome = purge_assets(connection, found)
            elif operation == "dismiss-junk":
                connection.executemany(
                    "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                    "VALUES('junk_file',?,'rejected','用户确认不是垃圾',?) "
                    "ON CONFLICT(category,item_key) DO UPDATE SET "
                    "status='rejected',note=excluded.note,updated_at=excluded.updated_at",
                    [(str(asset_id), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
                     for asset_id in valid_ids],
                )
            elif operation == "reconsider-junk":
                connection.executemany(
                    "DELETE FROM review_decision WHERE category='junk_file' AND item_key=?",
                    [(str(asset_id),) for asset_id in valid_ids],
                )
            elif operation in {"seen", "dispose"}:
                column, value = ("feedback", "seen") if operation == "seen" else ("disposal", "trash")
                placeholders = ",".join("?" * len(valid_ids))
                connection.execute(
                    f"UPDATE asset SET {column}=?,feedback_at=? WHERE id IN ({placeholders})",
                    [value, now, *valid_ids],
                )
            elif operation == "later":
                connection.executemany(
                    "INSERT OR IGNORE INTO watch_queue(profile_id,asset_id,added_at,source) "
                    f"VALUES('{DEFAULT_PROFILE_ID}',?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),'web-batch')",
                    [(asset_id,) for asset_id in valid_ids],
                )
            else:
                connection.executemany(
                    "INSERT INTO asset_preference(profile_id,asset_id,liked,reason,source,updated_at) "
                    f"VALUES('{DEFAULT_PROFILE_ID}',?,1,'','web-batch',strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
                    "ON CONFLICT(profile_id,asset_id) DO UPDATE SET liked=1,source='web-batch',"
                    "updated_at=excluded.updated_at",
                    [(asset_id,) for asset_id in valid_ids],
                )
    except BaseException:
        if purge_outcome is not None:
            _restore_staged_media(purge_outcome["_staged"])
        raise
    if purge_outcome is not None:
        result = {"ok": True, "operation": operation, **_finish_purge(purge_outcome)}
        result.update(clean_resource_orphans(contract))
        return result
    return {"ok": True, "operation": operation, "changed": len(valid_ids)}


def q_duplicates(contract: WebContract, args):
    """按番号 + 时长找真重复；每簇标出最大与最长的那个。"""
    limit = min(max(int(args.get("limit", "60")), 1), 300)
    offset = max(int(args.get("offset", "0")), 0)
    with contract.read_connection() as connection:
        rows = connection.execute(
            "SELECT id,code,location,path,name,size,duration,hash,disposal "
            "FROM asset WHERE medium='video' AND code IS NOT NULL AND code<>'' "
            "AND (disposal IS NULL OR disposal<>'trash')"
        ).fetchall()

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if not is_jav_code(row["code"]):
            continue
        item = dict(row)
        # 盘符只用于判定跨盘；重复项页面还要显示完整路径，不能在契约层丢掉。
        item["drive"] = str(item.get("path") or "")[:2].upper()
        grouped.setdefault(normalise_code_key(row["code"]), []).append(item)

    groups = []
    for code, items in grouped.items():
        if len(items) < 2:
            continue
        for cluster in duration_clusters(items):
            if len(cluster) < 2:
                continue
            largest = max(cluster, key=lambda x: x.get("size") or 0)
            longest = max(cluster, key=lambda x: x.get("duration") or 0)
            hashes_present = [x["hash"] for x in cluster if x["hash"]]
            hashes = set(hashes_present)
            for item in cluster:
                item["is_largest"] = item["id"] == largest["id"]
                item["is_longest"] = item["id"] == longest["id"]
                item.pop("hash", None)
                item.pop("disposal", None)
            groups.append({
                "code": code,
                "files": sorted(cluster, key=lambda x: -(x.get("size") or 0)),
                "count": len(cluster),
                # 必须每个文件都有 sha1 且完全相同才算确证字节一致。缺一个哈希
                # 就只是「时长相近」的推断，不能对外宣称已确证。
                "identical": len(hashes) == 1 and len(hashes_present) == len(cluster),
                "drives": sorted({x["drive"] for x in cluster}),
                "cross_drive": len({x["drive"] for x in cluster}) > 1,
                "reclaimable": sum(x.get("size") or 0 for x in cluster)
                - (largest.get("size") or 0),
            })
    groups.sort(key=lambda g: -g["reclaimable"])
    window = groups[offset:offset + limit]
    return {
        "total": len(groups),
        "files": sum(g["count"] for g in groups),
        "reclaimable": sum(g["reclaimable"] for g in groups),
        "groups": window,
        "has_more": offset + limit < len(groups),
    }


def q_quality_goals(contract: WebContract, args):
    """List explicit better-version targets for the management surface."""
    limit = min(max(int(args.get("limit", "60")), 1), 200)
    offset = max(int(args.get("offset", "0")), 0)
    with contract.read_connection() as connection:
        total = connection.execute(
            "SELECT count(*) FROM asset_quality_goal WHERE profile_id=? AND wanted=1",
            (DEFAULT_PROFILE_ID,),
        ).fetchone()[0]
        rows = [dict(row) for row in connection.execute(
            "SELECT a.id,a.name,a.code,a.location,a.size,a.duration,a.snapshot_path,"
            "g.reason,g.updated_at FROM asset_quality_goal g "
            "JOIN asset a ON a.id=g.asset_id "
            "WHERE g.profile_id=? AND g.wanted=1 "
            "ORDER BY g.updated_at DESC,a.id DESC LIMIT ? OFFSET ?",
            (DEFAULT_PROFILE_ID, limit, offset),
        )]
    for row in rows:
        row["cost"] = COST.get(row["location"], "metered")
        row["has_thumb"] = contract.has_snapshot(row["snapshot_path"])
        row["has_cover"] = contract.has_cover(row.get("code"))
        row.pop("snapshot_path", None)
    return {"total": total, "items": rows, "offset": offset,
            "has_more": offset + len(rows) < total}


class ContractRouteNotFound(KeyError):
    """The stable JSON contract has no handler for this path."""


def _get_item(contract, args):
    return q_item(contract, int(args["id"]))


def _get_index(contract, args):
    return q_index(
        contract,
        args.get("kind", "tags"),
        args.get("q", ""),
        min(max(int(args.get("limit", "180")), 1), 600),
        max(int(args.get("offset", "0")), 0),
        args.get("category", ""),
    )


def _get_stats(contract, _args):
    return contract.cached("stats", lambda: q_stats(contract))


def _get_tops(contract, args):
    n = min(int(args.get("n", "28")), 60)
    jav = args.get("jav") == "1"
    seed = str(args.get("seed", ""))[:32]
    state = str(args.get("state", ""))
    return contract.cached(
        f"tops{n}{'-jav' if jav else ''}:{seed}:{state}",
        lambda: q_tops(contract, n, jav=jav, seed=seed, state=state),
    )


def _get_ads(contract, args):
    return q_ads(
        contract,
        min(int(args.get("limit", "60")), 200),
        max(int(args.get("offset", "0")), 0),
        args.get("kind", ""),
        args.get("status", "pending"),
    )


def _get_related(contract, args):
    return q_related(contract, int(args["id"]), min(int(args.get("limit", "24")), 60))


def _get_facets(contract, args):
    jav = args.get("jav") == "1"
    scope_kind = str(args.get("scope_kind", ""))
    scope_name = str(args.get("scope_name", ""))
    asset_id = int(args["id"]) if args.get("id") else None
    state = str(args.get("state", ""))
    scope_key = f"{scope_kind}:{scope_name}:{asset_id or ''}:{state}"
    return contract.cached(
        f"facets{'-jav' if jav else ''}:{scope_key}",
        lambda: q_facets(
            contract,
            jav=jav, scope_kind=scope_kind, scope_name=scope_name, asset_id=asset_id,
            state=state,
        ),
    )


def _get_search_history(contract, args):
    return q_search_history(contract, int(args.get("limit", "10")))


def _get_taste(contract, args):
    window = str(args.get("window") or "all")
    return contract.cached(
        f"taste:{window}",
        lambda: q_taste(contract, {"window": window}),
    )


def _get_review(contract, _args):
    return contract.cached("review", lambda: q_review(contract))


def _post_empty_trash(contract, _body):
    return w_empty_trash(contract)


GET_HANDLERS = {
    "/api/settings": q_settings,
    "/api/follow": q_follow,
    "/api/follow/credentials": q_follow_credentials,
    "/api/follow/tags": q_follow_tags,
    "/api/follow/schedule": q_follow_schedule,
    "/api/items": q_items,
    "/api/item": _get_item,
    "/api/parts": q_parts,
    "/api/entity": q_entity,
    "/api/photos": q_entity_photos,
    "/api/photo-set": q_photo_set,
    "/api/index": _get_index,
    "/api/duplicates": q_duplicates,
    "/api/quality-goals": q_quality_goals,
    "/api/stats": _get_stats,
    "/api/tops": _get_tops,
    "/api/ads": _get_ads,
    "/api/related": _get_related,
    "/api/playlists": q_playlists,
    "/api/playlist": q_playlist,
    "/api/facets": _get_facets,
    "/api/search-history": _get_search_history,
    "/api/taste": _get_taste,
    "/api/review": _get_review,
}

POST_HANDLERS = {
    "/api/follow/check": w_follow_check,
    "/api/follow/schedule": w_follow_schedule,
    "/api/follow/source": w_follow_source,
    "/api/follow/author-alias": w_follow_author_alias,
    "/api/follow/resolve": w_follow_resolve,
    "/api/follow/credential": w_follow_credential,
    "/api/follow/status": w_follow_status,
    "/api/follow/save": w_follow_save,
    "/api/follow/play": w_follow_play,
    "/api/follow/activity": w_follow_activity,
    "/api/activity": w_activity,
    "/api/play": w_play,
    "/api/feedback": w_feedback,
    "/api/watch-later": w_watch_later,
    "/api/playlist": w_playlist,
    "/api/preference": w_preference,
    "/api/quality-goal": w_quality_goal,
    "/api/item-tag": w_item_tag,
    "/api/batch": w_batch,
    "/api/search-history": w_search_history,
    "/api/taste/refresh": w_taste_refresh,
    "/api/taste/source": w_taste_source,
    "/api/trash/empty": _post_empty_trash,
    "/api/purge-missing": w_purge_missing,
    "/api/resource-sync/scan": w_resource_sync_scan,
    "/api/resource-sync/apply": w_resource_sync_apply,
    "/api/review/auto-apply": w_review_auto_apply,
    "/api/review/decision": w_review_decision,
    "/api/settings": w_settings,
}


#: 这些 POST 不写 ledger，只是因为要带请求体才用 POST。写入端闸门管的是账本分叉，
#: 不该拦它们——「查找」只联网、「存凭据」只写本机 secrets 文件，都不碰账本。
#: 追更的「查找」在只读端被拦成 409 是实测踩到的。
READ_ONLY_POST_ROUTES = frozenset({
    "/api/follow/resolve", "/api/follow/credential",
    "/api/taste/refresh", "/api/taste/source", "/api/resource-sync/scan",
})


def dispatch_api_get(contract: WebContract, path, args):
    """Dispatch the stable JSON read contract used by the current web client."""
    try:
        handler = GET_HANDLERS[path]
    except KeyError as exc:
        raise ContractRouteNotFound(path) from exc
    return handler(contract, args)


def dispatch_api_post(contract: WebContract, path, body):
    try:
        handler = POST_HANDLERS[path]
    except KeyError as exc:
        raise ContractRouteNotFound(path) from exc
    return handler(contract, body)
