"""Stable JSON contract used by the FastAPI application.

Database reads are read-only by default. Writes are limited to explicit activity and
feedback functions; schema changes belong to the migration runner.
"""
from __future__ import annotations

import os
import csv
import hashlib
import json
import random
import re
import threading
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Sequence
from urllib.parse import quote, urlsplit

from .config import (
    COVER_DIR, GENERATED_DIR, LOCATION_ROOT_DECLARATIONS, SECRETS_DIR, SOURCES_DIR,
)
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
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
from .web_follow import (
    q_follow, q_follow_credentials, w_follow_check, w_follow_save, w_follow_source,
    w_follow_status,
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
from .web_logic import (
    DUPLICATE_FLOOR_SECONDS,
    DUPLICATE_TOLERANCE,
    LENGTH_TAGS,
    TECH_TAGS,
    duration_clusters,
    face_focus,
    is_jav_asset,
    is_jav_code,
    normalise_code_key,
    part_marker,
    tag_cat,
)
from .web_playlists import q_playlist, q_playlists, w_playlist

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
                 follow_sources_root: Path | None = None,
                 follow_secrets_root: Path | None = None,
                 database: LedgerDatabase | None = None):
        # 候选 CSV 的目录做成实例属性而不是模块常量，复核层才能在临时目录里被测试。
        self.candidate_root = Path(candidate_root) if candidate_root is not None else GENERATED_DIR
        self.cover_root = Path(cover_root) if cover_root is not None else COVER_DIR
        self.avatar_root = Path(avatar_root) if avatar_root is not None else GENERATED_DIR / "avatars"
        # `/logo` 就是从这里读；批准候选等于把图装进这个目录。
        self.logo_root = Path(logo_root) if logo_root is not None else GENERATED_DIR / "logos"
        # 追更的原始证据与本机凭据目录同样做成实例属性，测试才能落在临时目录里。
        self.follow_sources_root = (Path(follow_sources_root)
                                    if follow_sources_root is not None else SOURCES_DIR)
        self.follow_secrets_root = (Path(follow_secrets_root)
                                    if follow_secrets_root is not None else SECRETS_DIR)
        self.database = database or LedgerDatabase(db_path)
        self.db_path = self.database.db_path
        self.snapshot_root = Path(snapshot_root) if snapshot_root is not None else None
        self.legacy_snapshot_roots = tuple(Path(path) for path in legacy_snapshot_roots)
        self.write_lock = self.database.write_lock
        self.cache: dict[str, tuple[float, object]] = {}
        self.cache_lock = threading.Lock()
        self._fts_available: bool | None = None

    def cached(self, key, fn):
        now = time.time()
        with self.cache_lock:
            hit = self.cache.get(key)
            if hit and now - hit[0] < CACHE_TTL:
                return hit[1]
        value = fn()
        with self.cache_lock:
            self.cache[key] = (now, value)
        return value

    def cache_bust(self):
        with self.cache_lock:
            self.cache.clear()

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
            connection = self.db()
            try:
                self._fts_available = connection.execute(
                    "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='asset_search'"
                ).fetchone() is not None
            finally:
                connection.close()
        return self._fts_available

# ────────────────────────────── 查询 ──────────────────────────────

def q_items(contract: WebContract, args):
    where, par = ["a.medium='video'"], []
    if args.get("state") == "trash":
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
        # 逗号分隔 = 组合筛选，全部满足。
        for tg in [x for x in args["tag"].split(",") if x]:
            where.append(
                "((EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=a.id AND e.kind='tag' AND e.canonical_name=?) OR "
                "EXISTS(SELECT 1 FROM asset_tag t WHERE t.asset_id=a.id AND t.tag=?)) AND "
                "NOT EXISTS(SELECT 1 FROM asset_tag_preference p WHERE p.asset_id=a.id "
                f"AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.hidden=1 "
                "AND p.normalized_tag=lower(trim(?))))"
            )
            par.extend((tg, tg, tg))
    if args.get("len"):
        where.append("a.ctx_length = ?"); par.append(args["len"])
    if args.get("dur_min"):
        where.append("a.duration >= ?"); par.append(max(0, float(args["dur_min"])))
    if args.get("dur_max"):
        where.append("a.duration <= ?"); par.append(max(0, float(args["dur_max"])))
    if args.get("orient"):
        where.append("a.ctx_orient = ?"); par.append(args["orient"])
    elif args.get("exclude_vertical") == "1":
        where.append("(a.ctx_orient IS NULL OR a.ctx_orient <> '竖屏')")
    if args.get("jav") == "1":
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
    if args.get("state") == "fresh":
        where.append("(a.play_count IS NULL OR a.play_count=0) AND a.feedback IS NULL")
    elif args.get("state") == "played":
        where.append("a.play_count > 0")
    elif args.get("state") == "flagged":
        where.append(
            "(COALESCE(a.o_count,0)>0 OR EXISTS(SELECT 1 FROM asset_preference p "
            f"WHERE p.asset_id=a.id AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.liked=1))"
        )
    elif args.get("state") == "later":
        where.append(
            "EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=a.id "
            f"AND w.profile_id='{DEFAULT_PROFILE_ID}')"
        )
    if args.get("thumb") == "1":
        where.append("a.snapshot_path IS NOT NULL")

    order = {"new": "a.first_seen DESC, a.id DESC",
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
    sql = ("SELECT a.id,a.location,a.path,a.name,a.creator,a.studio,a.code,a.release_date,a.size,"
           "a.duration,a.width,a.height,a.ctx_length,a.ctx_orient,a.snapshot_path,"
           "a.play_count,a.leave_ratio,a.feedback,a.disposal,a.rating,a.o_count,"
           "a.play_seconds,a.max_reached,a.seek_count,"
           "EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=a.id "
           f"AND w.profile_id='{DEFAULT_PROFILE_ID}') AS watch_later "
           "FROM asset a WHERE " + " AND ".join(where) + f" ORDER BY {order} LIMIT ? OFFSET ?")
    c = contract.db()
    rows = [dict(r) for r in c.execute(sql, par + [fetch_limit, off])]
    has_more = len(rows) > lim if not include_total else None
    rows = rows[:lim]
    cnt = (c.execute("SELECT count(*) FROM asset a WHERE " + " AND ".join(where), par).fetchone()[0]
           if include_total else None)
    c.close()
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
                if tag_cat(tag) in ("general", "character", "copyright")
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
    return {"total": cnt, "items": rows, "has_more": has_more}

def con_tags(contract: WebContract, ids, qm):
    c = contract.db()
    try:
        return c.execute(
            f"SELECT asset_id, tag FROM asset_tag WHERE asset_id IN ({qm})", ids).fetchall()
    finally:
        c.close()


def con_entities(contract: WebContract, ids, qm):
    connection = contract.db()
    try:
        return connection.execute(
            f"SELECT DISTINCT ae.asset_id,e.id,e.kind,e.canonical_name "
            f"FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            f"WHERE ae.asset_id IN ({qm}) "
            f"AND e.kind IN ('tag','performer','creator','studio','series') "
            f"ORDER BY ae.asset_id,e.kind,e.canonical_name", ids,
        ).fetchall()
    finally:
        connection.close()


def q_search_history(contract: WebContract, limit: int = 10):
    connection = contract.db()
    try:
        rows = connection.execute(
            "SELECT query FROM search_history ORDER BY last_used_at DESC, query LIMIT ?",
            (max(1, min(limit, 50)),),
        ).fetchall()
    finally:
        connection.close()
    return {"items": [row["query"] for row in rows]}


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

def q_item(contract: WebContract, aid):
    """按 id 直取。
    ⚠️ 第一版没有这个接口，前端用「带筛选条件再查一遍然后 find」的绕法，
       limit 被覆盖成 1 → find 必然失败 → 走兜底 items[0]，
       于是**每次点击都打开同一个默认列表首项**（一个 12.6 GB 的 PikPak 文件），
       既显示错条目，又反复拉计费流量。教训：按 id 取就按 id 取。"""
    c = contract.db()
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
        c.close(); return {"error": "not found"}
    d = dict(r)
    legacy = [x[0] for x in c.execute(
        "SELECT t.tag FROM asset_tag t WHERE t.asset_id=? AND NOT EXISTS("
        "SELECT 1 FROM asset_tag_preference p WHERE p.asset_id=t.asset_id "
        f"AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.hidden=1 "
        "AND p.normalized_tag=lower(trim(t.tag))) ORDER BY t.tag", (aid,),
    )]
    canonical = list(c.execute(
        "SELECT DISTINCT e.id,e.kind,e.canonical_name FROM asset_entity ae "
        "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=? "
        "AND e.kind IN ('tag','performer','creator','studio','series') "
        "AND (e.kind<>'tag' OR NOT EXISTS(SELECT 1 FROM asset_tag_preference p "
        f"WHERE p.asset_id=ae.asset_id AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.hidden=1 "
        "AND p.normalized_tag=e.normalized_name)) "
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
    c.close()
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


def q_ads(contract: WebContract, limit=200, offset=0):
    """疑似广告复核队列 —— **不自动删**，只排队让人看接触印相确认。

    没有可靠的单一判据（试过「同番号短版」会误伤 CD2/part1 分卷，
    试过「同名扩散」会误伤 001.mp4 这类通用名的真文件）。
    所以给的是**嫌疑分**，按分排序，人工看图定夺，确认的走既定 CSV 删除流程。

    2026-08-15 按用户标记的 21 条真广告重新标定：命中推广词本身不算证据，
    要看**剥掉推广词后还剩不剩内容**。三类实测误判据此排除：剧情里的「微信」、
    开头是盗版站域名但正文是真实描述、以及把创作者账号当成番号去比时长。"""
    c = contract.db()
    rows = c.execute(
        "SELECT id,location,name,creator,code,size,duration,width,height,snapshot_path,"
        "feedback,disposal,play_count,leave_ratio,o_count,studio,ctx_orient,path "
        "FROM asset WHERE medium='video' AND size < 500*1024*1024 "
        "AND duration IS NOT NULL AND duration BETWEEN 15 AND 1200 "
        "AND (disposal IS NULL)").fetchall()
    # 同番号是否存在明显更长的版本；只在 code 是真番号时才有意义。
    longer = {r[0]: r[1] for r in c.execute(
        "SELECT code, max(duration) FROM asset WHERE medium='video' AND code IS NOT NULL "
        "AND code<>'' AND duration IS NOT NULL GROUP BY code")}
    out = []
    for r in rows:
        d = dict(r)
        s, why = 0, []
        nm = os.path.splitext(d["name"])[0]
        residue = promo_residue(nm)
        promo = bool(PROMO_PHRASE.search(nm) or PROMO_DOMAIN.search(nm))
        # 目录维度的证据：广告包的文件名往往干净（`极道世界.mp4`），唯一线索在旧导入器
        # 从目录名投影出来的创作者位或路径里。creator 位本身是推广站域名时，它就不再是
        # 「有归属所以是正片」的证据，下面两处对 creator 的信任都必须先排除这种情况。
        owner = d.get("creator") or ""
        owner_is_promo = bool(AD_DOMAIN.search(owner))
        real_owner = bool(owner) and not owner_is_promo
        folder = os.path.dirname(d.get("path") or "")
        if promo and residue < 6:
            # 名字剥完只剩广告本身，这是最硬的信号。
            s += 60; why.append("整个名字都是推广语")
        elif promo and residue < 14 and not real_owner:
            s += 30; why.append("推广语占了名字主体")
        if owner_is_promo:
            s += 50; why.append("创作者位是推广站域名")
        elif AD_DIRPACK.search(folder):
            s += 45; why.append("目录是「域名+番号」的推广打包")
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
    c.close()
    out.sort(key=lambda x: (-x["score"], -(x["size"] or 0)))
    items = out[offset:offset + limit]
    attach_card_performers(contract, items)
    return {"total": len(out), "items": items}

def q_related(contract: WebContract, aid, limit=24):
    """接着看 —— 把口味接近的串成播放列表。
    优先级：同创作者 > 共享标签最多 > 同厂牌。全部排除已标记不合口味的。"""
    c = contract.db()
    r = c.execute("SELECT id FROM asset WHERE id=?", (aid,)).fetchone()
    if not r:
        c.close(); return {"items": []}
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
    c.close()
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


#: 顶部三层的候选池相对展示位的倍数。严格取前 N 会让这一条永远是同一批人——
#: 「换一批」刷新后上面纹丝不动。放大候选池再按种子确定性抽样，既保持是常见身份，
#: 又能真的换一批。倍数太大就会开始出现只有一两部作品的冷门项。
TOPS_POOL_FACTOR = 4


def q_tops(contract: WebContract, n=28, jav=False, seed=""):
    """顶部三层用的数据：女优圆头像 / 厂牌 / 内容标签。

    缓存的人物肖像由前端优先使用；缺失时才回退到代表作接触印相裁切。"""
    c = contract.db()
    scope = JAV_ASSET_CLAUSE if jav else ""
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
    c.close()
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
    c = contract.db()
    row = _resolve_entity(c, kind, name)
    if not row:
        c.close()
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
        "AND NOT EXISTS(SELECT 1 FROM entity performer WHERE performer.kind='performer' "
        "AND performer.normalized_name=tag.normalized_name) "
        f"AND tag.canonical_name NOT IN ({','.join('?' for _ in LENGTH_TAGS)}) "
        "AND NOT EXISTS(SELECT 1 FROM asset_tag_preference p "
        f" WHERE p.asset_id=scope.asset_id AND p.profile_id='{DEFAULT_PROFILE_ID}' "
        " AND p.hidden=1 AND p.normalized_tag=tag.normalized_name) "
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
    c.close()
    return d

# ────────────────────────────── 照片 ──────────────────────────────
# 图集就是目录：账本没有图集实体，一个目录下的图片本来就是一份图集，
# `<作品目录>\P\001.jpg` 这种约定在 A:/B: 上到处都是。图集的 id 用目录里最小的
# 资产 id，既稳定又不用把真实路径发给前端（`q_item` 同样不发 `path`）。

def dir_expr(alias: str = "a.") -> str:
    """从 `path` 去掉 `name` 和分隔符，剩下的就是所在目录。

    表别名做成参数，是因为图集查询用 `a.`、按目录对账时直接查 `asset` 不带别名；
    早先靠对常量做字符串替换来凑另一种写法，改一次别名就会悄悄失配。
    """
    return (f"substr({alias}path,1,"
            f"length({alias}path)-length({alias}name)-1)")


#: 图集查询一律带 `a.` 别名。
PHOTO_DIR = dir_expr()

#: 只写「这是图片」的通用目录名。它们做标题没有信息量，改用上一级目录名。
GENERIC_PHOTO_DIRS = frozenset({
    "p", "photo", "photos", "pic", "pics", "picture", "pictures",
    "image", "images", "img", "图片", "写真", "照片",
})


def _resolve_entity(c, kind, name):
    """按规范名或别名取实体。旧名进来也要能落到同一条身份上。"""
    return c.execute(
        "SELECT DISTINCT e.* FROM entity e LEFT JOIN entity_alias a ON a.entity_id=e.id "
        "WHERE e.kind=? AND (e.canonical_name=? OR a.alias=?) LIMIT 1",
        (kind, name, name),
    ).fetchone()


def photo_set_title(directory: str) -> str:
    """图集标题：叶子目录名；叶子只是 `P`、`图片` 这类通用名时用上一级。"""
    parts = [part for part in str(directory).replace("/", "\\").split("\\") if part]
    if not parts:
        return "未命名图集"
    leaf = parts[-1]
    if leaf.casefold() in GENERIC_PHOTO_DIRS and len(parts) > 1:
        return parts[-2]
    return leaf


def q_entity_photos(contract: WebContract, args):
    """实体名下的图集列表。封面用目录里第一张图，不另存封面文件。"""
    kind, name = args.get("kind", ""), args.get("name", "")
    if kind not in {"performer", "studio", "creator", "series"} or not name:
        return {"error": "invalid entity"}
    c = contract.db()
    try:
        row = _resolve_entity(c, kind, name)
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
        return {
            "kind": kind, "name": row["canonical_name"], "entity_id": row["id"],
            "sets": sets, "total": sum(item["n"] for item in sets),
        }
    finally:
        c.close()


def q_photo_set(contract: WebContract, args):
    """一个图集里的图片。按文件名排，`001.jpg` 这类编号才不会乱序。"""
    try:
        set_id = int(args.get("id", ""))
    except (TypeError, ValueError):
        return {"error": "invalid id"}
    limit = max(1, min(int(args.get("limit") or 120), 600))
    offset = max(0, int(args.get("offset") or 0))
    c = contract.db()
    try:
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
        items = [{"id": item["id"], "name": item["name"], "size": item["size"] or 0}
                 for item in c.execute(
                     f"SELECT a.id,a.name,a.size FROM asset a WHERE a.medium='image' "
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
    finally:
        c.close()


def q_index(contract: WebContract, kind, q="", limit=600, offset=0, category=""):
    """全部艺人 / 创作者 / 标签的索引页数据。"""
    c = contract.db()
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
               "AND NOT EXISTS(SELECT 1 FROM entity performer WHERE performer.kind='performer' "
               "AND performer.normalized_name=e.normalized_name) "
               "AND NOT EXISTS(SELECT 1 FROM asset_tag_preference p "
               f"WHERE p.asset_id=ae.asset_id AND p.profile_id='{DEFAULT_PROFILE_ID}' "
               "AND p.hidden=1 AND p.normalized_tag=e.normalized_name) ")
        par = sorted(LENGTH_TAGS)
        if q: sql += "AND e.canonical_name LIKE ? "; par.append(f"%{q}%")
        sql += "GROUP BY e.id,e.canonical_name ORDER BY n DESC"
        all_rows = [dict(r, cat=tag_cat(r["k"])) for r in c.execute(sql, par)]
        if category and category != "all":
            all_rows = [row for row in all_rows if row["cat"] == category]
        rows = all_rows[offset:offset + limit]
        has_more = offset + limit < len(all_rows)
    c.close()
    return {"kind": kind, "items": rows, "has_more": has_more}

def q_stats(contract: WebContract):
    """统计页：库存 / 归属 / 标签 / 消费 / 磁盘。原来挤在顶栏右上角，信息量太小又碍眼。"""
    c = contract.db()
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
        "AND NOT EXISTS(SELECT 1 FROM entity performer WHERE performer.kind='performer' "
        "AND performer.normalized_name=lower(trim(t.tag))) "
        "GROUP BY t.tag ORDER BY n DESC LIMIT 30")]
    out["consumption"] = {
        "played": one("SELECT count(*) FROM asset WHERE play_count>0"),
        "play_seconds": one("SELECT COALESCE(sum(play_seconds),0) FROM asset"),
        "o_total": one("SELECT COALESCE(sum(o_count),0) FROM asset"),
        "dislike": one("SELECT count(*) FROM asset WHERE feedback='dislike'"),
        "seen": one("SELECT count(*) FROM asset WHERE feedback='seen'"),
        "trash": one("SELECT count(*) FROM asset WHERE disposal='trash'"),
        "skimmed": one("SELECT count(*) FROM asset WHERE duration>0 AND play_seconds>0 "
                       "AND max_reached>0.6 AND play_seconds/duration < max_reached-0.25"),
    }
    out["recent"] = [dict(r) for r in c.execute(
        "SELECT id,name,creator,play_seconds,duration,max_reached,leave_ratio,o_count "
        "FROM asset WHERE last_played IS NOT NULL ORDER BY last_played DESC LIMIT 12")]
    c.close()
    try:
        import shutil
        volume = system_volume()
        du = shutil.disk_usage(volume)
        out["system_disk"] = {"root": str(volume), "free": du.free, "total": du.total}
        out["disk_c"] = out["system_disk"]  # 0.6.x 客户端兼容别名
    except Exception:
        out["system_disk"] = None
        out["disk_c"] = None
    return out


# 候选文件名带批次日期，代码里只认前缀并永远取目录里最新的一份；
# 把日期写死在源码里会让下一批候选生成后复核页静默变空。
CANDIDATE_PREFIX = {
    "metadata_fields": "metadata-field-candidates-",
    "creator_tags": "creator-tags-candidate-",
    "studio_logos": "studio-logo-candidate-",
    "performer_avatars": "performer-avatar-candidate-",
    # 这三类此前只落在 CSV 里没有界面入口，复核负担等于被丢回给用户去翻文件。
    "western_identity": "babepedia-candidates",
    "code_creators": "code-creator-review",
    "cover_sources": "cover-fetch-log",
    "fc2_markings": "fc2-candidate-log",
    "fc2_similarity": "fc2-similarity-candidate-",
    "video_endcards": "video-endcard-candidate-",
}
# 每类候选的稳定主键列。缺这一列的行直接跳过并计数，绝不退化成行号——
# 行号会在 CSV 重排后把历史决定悄悄挪到别的条目上。
CANDIDATE_KEY = {
    "metadata_fields": "item_key",
    "creator_tags": "board",
    "studio_logos": "studio",
    "performer_avatars": "entity_id",
    "western_identity": "entity_id",
    "code_creators": "entity_id",
    "cover_sources": "code",
    "fc2_markings": "code",
    "fc2_similarity": "pair_key",
    "video_endcards": "candidate_key",
}
def _needs_review(category: str, row: dict) -> bool:
    """已经有定论的行不该占复核页。

    babepedia 那批 168 条里有 143 条是「确认无档案」——站上确实没有这个人，
    没有可判断的东西，全列出来只会把真正要看的 25 条淹掉。封面同理：拿到 2184
    宽的高清图不需要人确认，未取得和仍停在 800 低清基线的才需要。
    """
    if category == "western_identity":
        return str(row.get("verdict") or "") in ("命中", "需人工确认")
    if category == "studio_logos":
        # 无 handle、无落盘图片和与现有 Logo 完全相同都没有人工可判断项。
        # 只有新的/变化的确认来源，或明确标 needs_confirmation 的图片才进队列。
        saved = bool(str(row.get("saved") or "").strip())
        state = str(row.get("content_state") or "").strip()
        accepted = str(row.get("accepted") or "").lower() in {"1", "true", "yes"}
        needs_confirmation = row.get("confirmation") == "needs_confirmation"
        return saved and state not in {"unchanged", "duplicate", "rejected"} and (
            accepted or needs_confirmation
        )
    if category == "cover_sources":
        # 封面抓取的成功、尺寸和缺失都是机械状态，不需要人工批准。旧界面把
        # 241 个未取得和 800 px 基线封面全塞进复核页，却没有可执行写入动作。
        return False
    if category == "fc2_markings":
        # FC2 大多数作品页评论区是空的，全列出来会把真正有标记的几十条淹掉。
        # 只有拿到演员名、等价关系或判成合集的才需要人看。
        return bool(row.get("performers") or row.get("equivalents")
                    or row.get("is_collection"))
    return True


REVIEW_PREVIEW_LIMIT = 60
REVIEW_APPLY_LIMIT = 500


def latest_candidate_file(category: str, root: Path | None = None) -> Path | None:
    prefix = CANDIDATE_PREFIX.get(category)
    if not prefix:
        return None
    matches = sorted((root or GENERATED_DIR).glob(f"{prefix}*.csv"))
    return matches[-1] if matches else None


def read_candidates(category: str, root: Path | None = None) -> tuple[list[dict], str | None, int]:
    """读取最新一批候选，返回（有稳定主键的行, 文件名, 被跳过的行数）。"""
    path = latest_candidate_file(category, root)
    if path is None or not path.is_file():
        return [], None, 0
    key_column = CANDIDATE_KEY[category]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        raw = list(csv.DictReader(handle))
    rows, skipped = [], 0
    for row in raw:
        key = str(row.get(key_column) or "").strip()
        if not key:
            skipped += 1
            continue
        row["item_key"] = key
        rows.append(row)
    return rows, path.name, skipped


def _creator_entity_ids(connection, creators: list[str]) -> dict[str, int]:
    """创作者名（含别名）-> 规范 creator 实体 id；一次查完，不按候选逐个查。"""
    wanted = [name for name in dict.fromkeys(creators) if name]
    if not wanted:
        return {}
    marks = ",".join("?" * len(wanted))
    found: dict[str, int] = {}
    for row in connection.execute(
        "SELECT e.id,e.canonical_name,alias.alias FROM entity e "
        "LEFT JOIN entity_alias alias ON alias.entity_id=e.id "
        f"WHERE e.kind='creator' AND (e.canonical_name IN ({marks}) "
        f"OR alias.alias IN ({marks}))",
        [*wanted, *wanted],
    ):
        for name in (row["canonical_name"], row["alias"]):
            if name in wanted:
                found.setdefault(name, row["id"])
    return found


def _creator_previews(connection, creators: list[str]) -> dict[str, list[dict]]:
    """一次查完所有候选创作者的预览作品；按候选逐个查是 N+1。"""
    wanted = [name for name in dict.fromkeys(creators) if name]
    if not wanted:
        return {}
    marks = ",".join("?" * len(wanted))
    rows = connection.execute(
        "SELECT a.id,a.name,a.duration,e.canonical_name,alias.alias,a.creator FROM asset a "
        "LEFT JOIN asset_entity ae ON ae.asset_id=a.id AND ae.role='creator' "
        "LEFT JOIN entity e ON e.id=ae.entity_id AND e.kind='creator' "
        "LEFT JOIN entity_alias alias ON alias.entity_id=e.id "
        "WHERE a.medium='video' AND (a.disposal IS NULL OR a.disposal<>'trash') "
        "AND a.snapshot_path IS NOT NULL "
        f"AND (e.canonical_name IN ({marks}) OR alias.alias IN ({marks}) OR a.creator IN ({marks})) "
        "ORDER BY a.id",
        [*wanted, *wanted, *wanted],
    ).fetchall()
    previews: dict[str, list[dict]] = {name: [] for name in wanted}
    seen: dict[str, set] = {name: set() for name in wanted}
    for row in rows:
        for candidate in (row["canonical_name"], row["alias"], row["creator"]):
            bucket = previews.get(candidate)
            if bucket is None or len(bucket) >= REVIEW_PREVIEW_LIMIT or row["id"] in seen[candidate]:
                continue
            seen[candidate].add(row["id"])
            bucket.append({"id": row["id"], "name": row["name"], "duration": row["duration"]})
    return previews


def _attach_review_asset_context(connection, rows: list[dict]) -> None:
    """Attach one representative original video without per-row SQL queries."""
    codes = [str(row.get("code") or row.get("query") or "").strip()
             for row in rows]
    codes = [code for code in dict.fromkeys(codes) if code]
    assets_by_code: dict[str, dict] = {}
    if codes:
        marks = ",".join("?" * len(codes))
        sql = (
            "SELECT id,name,code,snapshot_path FROM asset WHERE medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash') AND (code IN (" + marks + ")"
        )
        params: list[object] = list(codes)
        if any(code.upper().startswith("FC2") for code in codes):
            sql += " OR code LIKE 'FC2%'"
        sql += ") ORDER BY (snapshot_path IS NULL),id"
        for asset in connection.execute(sql, params):
            key = normalise_code_key(asset["code"])
            assets_by_code.setdefault(key, dict(asset))

    entity_ids = [int(row["entity_id"]) for row in rows
                  if str(row.get("entity_id") or "").isdigit()]
    assets_by_entity: dict[int, dict] = {}
    if entity_ids:
        marks = ",".join("?" * len(entity_ids))
        for asset in connection.execute(
            "SELECT ae.entity_id,a.id,a.name,a.code,a.snapshot_path "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            f"WHERE ae.entity_id IN ({marks}) AND a.medium='video' "
            "AND (a.disposal IS NULL OR a.disposal<>'trash') "
            "ORDER BY (a.snapshot_path IS NULL),a.id",
            entity_ids,
        ):
            assets_by_entity.setdefault(asset["entity_id"], dict(asset))

    explicit_ids = {
        int(row["asset_id"]) for row in rows
        if str(row.get("asset_id") or "").isdigit()
    }
    comparison_ids = {
        int(value) for row in rows
        for value in (row.get("left_asset_id"), row.get("right_asset_id"))
        if str(value or "").isdigit()
    }
    comparison_assets: dict[int, dict] = {}
    requested_ids = comparison_ids | explicit_ids
    if requested_ids:
        marks = ",".join("?" * len(requested_ids))
        for asset in connection.execute(
            f"SELECT id,name,code,snapshot_path FROM asset WHERE id IN ({marks})",
            sorted(requested_ids),
        ):
            comparison_assets[asset["id"]] = dict(asset)

    for row in rows:
        code = str(row.get("code") or row.get("query") or "").strip()
        asset = assets_by_code.get(normalise_code_key(code)) if code else None
        entity_id = str(row.get("entity_id") or "")
        if asset is None and entity_id.isdigit():
            asset = assets_by_entity.get(int(entity_id))
        explicit_id = str(row.get("asset_id") or "")
        if asset is None and explicit_id.isdigit():
            asset = comparison_assets.get(int(explicit_id))
        if asset is None and row.get("preview_assets"):
            first = row["preview_assets"][0]
            asset = {"id": first["id"], "name": first["name"], "code": code,
                     "snapshot_path": True}
        if asset is None:
            pass
        else:
            row["asset_id"] = asset["id"]
            row["asset_name"] = asset["name"]
            row["asset_code"] = asset.get("code") or code
            row["asset_has_snapshot"] = bool(asset.get("snapshot_path"))
        row["comparison_assets"] = [
            comparison_assets[int(value)]
            for value in (row.get("left_asset_id"), row.get("right_asset_id"))
            if str(value or "").isdigit() and int(value) in comparison_assets
        ]


def _review_rows(contract: WebContract, category: str) -> tuple[list[dict], str | None, int]:
    rows, source, skipped = read_candidates(category, contract.candidate_root)
    rows = [row for row in rows if _needs_review(category, row)]
    connection = contract.db()
    try:
        decisions = {
            row["item_key"]: dict(row) for row in connection.execute(
                "SELECT item_key,status,note,updated_at FROM review_decision WHERE category=?",
                (category,),
            )
        }
        if category == "creator_tags":
            names = [str(row.get("creator") or "").strip() for row in rows]
            previews = _creator_previews(connection, names)
            # 这批候选判的是「这位创作者的作品该打什么标签」，主体是创作者本人。
            # 页面要给出创作者入口（头像 + 作品数），所以这里得把规范实体解析出来。
            entities = _creator_entity_ids(connection, names)
            for row in rows:
                name = str(row.get("creator") or "").strip()
                row["preview_assets"] = previews.get(name, [])
                row["entity_id"] = entities.get(name, "")
        elif category == "metadata_fields":
            for row in rows:
                try:
                    candidates = json.loads(str(row.get("candidates_json") or "[]"))
                except (TypeError, ValueError):
                    candidates = []
                row["candidates"] = [candidate for candidate in candidates
                                     if isinstance(candidate, dict)
                                     and str(candidate.get("candidate_key") or "").strip()]
            # 和账本已有的值比一遍，只把真差异留在队列里。实测 43 条候选里 24 条
            # 没有任何新信息：17 条与当前值逐字相同、7 条标签只是顺序不同。
            rows = [row for row in rows if _metadata_row_adds_information(connection, row)]
        elif category == "performer_avatars":
            # 候选 CSV 里的 `current_name` 是抓取来源给的罗马音；账本早就有更好的
            # 规范名（`Alice Shaku` 的规范名是 `释爱丽丝`），罗马音本身也已经登记
            # 为别名。复核页该显示账本认的那个名字，来源写法降为副标题。
            _use_canonical_entity_names(connection, rows)
        _attach_review_asset_context(connection, rows)
    finally:
        connection.close()
    for row in rows:
        decision = decisions.get(row["item_key"], {})
        if category == "studio_logos" and row.get("content_state") == "changed":
            # 同一厂牌上游头像变化是新的事实；旧批次 approved 不得把变化静默藏掉。
            decision = {}
        row["decision"] = decision.get("status", "pending")
        row["decision_note"] = decision.get("note", "")
        row["preview_url"] = (row.get("resolved_url") or row.get("source_url")
                              or row.get("avatar_url") or row.get("portrait_url") or "")
        if category == "video_endcards":
            frame = PurePosixPath(str(row.get("frame_key") or ""))
            asset_id = str(row.get("asset_id") or "")
            if (asset_id.isdigit() and len(frame.parts) == 2
                    and frame.parts[0] == asset_id and frame.suffix.lower() == ".png"):
                row["preview_url"] = (
                    f"/endcard-frame?id={asset_id}&name={quote(frame.name)}"
                )
        if category == "cover_sources" and row.get("result") == "取得":
            # 封面已经在本机，直接看落盘的那张，不要回源站再拉一次。
            row["preview_url"] = f"/cover?code={quote(str(row.get('code') or ''))}"
        asset_code = str(row.get("asset_code") or row.get("code") or "")
        if row.get("asset_id"):
            if asset_code and contract.has_cover(asset_code):
                row["asset_preview_url"] = f"/cover?code={quote(asset_code)}"
            elif row.get("asset_has_snapshot"):
                row["asset_preview_url"] = f"/poster?id={row['asset_id']}&c=4"
            else:
                row["asset_preview_url"] = ""
        for comparison in row.get("comparison_assets") or []:
            comparison_code = str(comparison.get("code") or "")
            if comparison_code and contract.has_cover(comparison_code):
                comparison["preview_url"] = f"/cover?code={quote(comparison_code)}"
            elif comparison.get("snapshot_path"):
                comparison["preview_url"] = f"/poster?id={comparison['id']}&c=4"
            else:
                comparison["preview_url"] = ""
            comparison.pop("snapshot_path", None)
        if not row.get("reason"):
            row["reason"] = _review_evidence(category, row)
    return _pending_first(rows), source, skipped


#: 元数据里的多值字段用顿号分隔；比较时按集合而不是按字符串。
MULTI_VALUE_FIELDS = {"performers", "tags"}


def _split_multi(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[、,，/|]", value or "") if part.strip()]


def _performer_identity_keys(connection, names: list[str]) -> frozenset:
    """把演员名折成身份键：能解析到实体的用实体 id，解析不到的保留原名。

    r18dev 给的是日文名，而账本规范名多数已本地化成中文——`桃谷エリカ` 与
    `桃谷绘里香` 实测就是同一条实体（日文名早已登记为别名）。按字符串比会把
    这类候选全判成「有差异」，批准反而把规范名倒退成别名。
    """
    keys = set()
    for name in names:
        row = connection.execute(
            "SELECT e.id FROM entity e LEFT JOIN entity_alias a ON a.entity_id=e.id "
            "WHERE e.kind='performer' AND (e.canonical_name=? OR a.alias=?) LIMIT 1",
            (name, name),
        ).fetchone()
        keys.add(row["id"] if row else normalize_entity_name(name))
    return frozenset(keys)


def _metadata_row_adds_information(connection, row: dict) -> bool:
    """这一行候选相对账本现值有没有新东西；没有就不该占复核队列。

    复核的成本是人的注意力：把「和现在一模一样」的行混在里面，真正要判的那些
    就被淹掉了（`_needs_review` 已经对封面和 babepedia 做过同样的取舍）。
    """
    current = str(row.get("current_value") or "").strip()
    if not current:
        return True                      # 补空值总是有信息，例如发行日期
    field = str(row.get("field") or "").strip()
    candidates = row.get("candidates") or []
    if not candidates:
        return False
    if field in MULTI_VALUE_FIELDS:
        if field == "performers":
            current_key = _performer_identity_keys(connection, _split_multi(current))
            return any(
                _performer_identity_keys(
                    connection, _split_multi(str(c.get("display_value") or ""))
                ) != current_key
                for c in candidates
            )
        current_set = frozenset(_split_multi(current))
        return any(
            frozenset(_split_multi(str(c.get("display_value") or ""))) != current_set
            for c in candidates
        )
    return any(str(c.get("display_value") or "").strip() != current for c in candidates)


def _use_canonical_entity_names(connection, rows: list[dict]) -> None:
    """把候选行的显示名换成账本规范名，来源写法留在 `source_name`。"""
    ids = [int(row["entity_id"]) for row in rows
           if str(row.get("entity_id") or "").strip().isdigit()]
    if not ids:
        return
    marks = ",".join("?" * len(ids))
    canonical = {row["id"]: row["canonical_name"] for row in connection.execute(
        f"SELECT id,canonical_name FROM entity WHERE id IN ({marks})", ids)}
    for row in rows:
        raw = str(row.get("entity_id") or "").strip()
        name = canonical.get(int(raw)) if raw.isdigit() else None
        shown = str(row.get("current_name") or "").strip()
        if name and name != shown:
            row["source_name"] = shown
            row["current_name"] = name


#: 可以不经人判断直接落库的字段。只放「补空且来源唯一」时确实无可判断的那些。
#: 演员和标签不在其中：那两类来源与账本的分歧是真实的（见 33 条噪音的核对）。
AUTO_APPLY_FIELDS = frozenset({"release_date"})


def metadata_auto_apply_candidate(connection, row: dict) -> dict | None:
    """这一行能否不经复核直接落库；不能就返回 None。

    四项必须同时成立，缺一项就仍然走人工：

    1. 目标字段当前为空——只补空，永不覆盖既有真相字段；
    2. 只有一个候选——有第二个值就存在取舍，那正是复核要做的事；
    3. 来源在当前 policy 下是 official / official_mirror；
    4. 番号在该番号名下**每一条**资产的文件名里逐字出现。

    第 4 条是这条捷径唯一的身份保证。刮削按番号取值，番号错则值错；文件名里
    逐字出现是本机可核验的证据，而复核界面其实给不了这个保证——它只并排显示
    番号和日期，并不告诉你番号跟这个文件对不对得上。

    `official` 一律按当前 policy 解析，不读候选 CSV 里的同名字段：那是抓取当时
    的快照，实测 r18dev 在 CSV 里写着 False，而现行 policy 认它是 official_mirror。
    """
    if str(row.get("field") or "").strip() not in AUTO_APPLY_FIELDS:
        return None
    if str(row.get("current_value") or "").strip():
        return None
    candidates = row.get("candidates") or []
    if len(candidates) != 1:
        return None
    candidate = candidates[0]
    spec = SOURCE_SPECS.get(str(candidate.get("source") or "").strip())
    if spec is None or not spec.official:
        return None
    code = str(row.get("code") or "").strip()
    query = str(row.get("query") or code).strip()
    if not code:
        return None
    names = [r["name"] for r in connection.execute(
        "SELECT name FROM asset WHERE medium='video' AND (upper(trim(code))=upper(?) "
        "OR upper(trim(code))=upper(?)) AND (disposal IS NULL OR disposal<>'trash')",
        (code, query))]
    if not names:
        return None
    folded = code.casefold()
    if not all(folded in str(name or "").casefold() for name in names):
        return None
    return candidate


def _pending_first(rows: list[dict]) -> list[dict]:
    """判过的不再占复核队列。

    早先这里原样返回全部候选，只给每行挂一个 `decision`，靠前端在本地把判过的
    行 splice 掉——于是「点通过」当场消失、一刷新全回来（厂牌 logo 上最明显）。
    队列该由服务端定义，前端只负责画。

    `approved` / `rejected` 是终局，直接移出；`跳过` 按字面意思是「稍后再看」，
    留在队列里但排到最后，否则一次跳过就等于永久隐藏，而界面上没有任何入口
    能把它找回来。
    """
    return sorted(
        (row for row in rows if row.get("decision") not in ("approved", "rejected")),
        key=lambda row: row.get("decision") == "skipped",
    )


def _review_evidence(category: str, row: dict) -> str:
    """给本身没有 reason 列的候选拼一句可判断的证据，别让复核页只剩一个名字。"""
    if category == "metadata_fields":
        current = str(row.get("current_value") or "").strip() or "尚无"
        return (f"当前值：{current}；{row.get('videos') or 0} 个同番号资产；"
                f"{len(row.get('candidates') or [])} 个来源候选")
    if category == "western_identity":
        overlap = row.get("token_overlap") or "0"
        variant = row.get("matched_variant") or ""
        spelling = f"（写法 {variant}）" if variant and variant != row.get("creator") else ""
        return (f"{row.get('verdict', '')} → {row.get('babepedia_name', '')}"
                f"{spelling}；词元重合 {overlap}；{row.get('videos', '')} 部作品")
    if category == "cover_sources":
        if row.get("result") != "取得":
            return f"未取得：{row.get('note') or '所有渠道都没有候选'}"
        return (f"{row.get('source', '')} · {row.get('width', '')}×{row.get('height', '')}"
                f" · {row.get('kb', '')} KB")
    if category == "fc2_markings":
        if row.get("is_collection"):
            return (f"合集，{row.get('collection_parts', '')} 个分片各自独立；"
                    f"封面不下发，分片回落到自己的缩略图")
        bits = []
        if row.get("performer_votes"):
            # 票数就是「几条独立评论这么说」，是这批候选唯一的置信度信号。
            bits.append(f"评论标记 {row.get('performer_votes')}")
        if row.get("equivalents"):
            bits.append(f"等同于 {row.get('equivalents')}")
        if row.get("writer"):
            bits.append(f"卖家 {row.get('writer')}")
        return "；".join(bits)
    if category == "fc2_similarity":
        kinds = str(row.get("evidence_kinds") or "").replace(" ", "、")
        detail = [f"证据 {kinds}" if kinds else "候选证据不足"]
        if row.get("duration_delta_seconds") != "":
            detail.append(f"时长差 {row.get('duration_delta_seconds')} 秒")
        if row.get("size_delta_percent") != "":
            detail.append(f"体积差 {row.get('size_delta_percent')}%")
        if row.get("shared_performers"):
            detail.append(f"共同演员 {row.get('shared_performers')}")
        if row.get("warnings"):
            detail.append(str(row.get("warnings")))
        return "；".join(detail)
    return ""


def q_review(contract: WebContract):
    connection = contract.db()
    failures = [dict(row) for row in connection.execute(
        "SELECT id,name,location,path,duration FROM asset "
        "WHERE location='115' AND medium='video' AND snapshot_path IS NULL AND duration>2"
    )]
    decisions = {
        row["item_key"]: dict(row) for row in connection.execute(
            "SELECT item_key,status,note,updated_at FROM review_decision WHERE category='media_failure'"
        )
    }
    connection.close()
    for row in failures:
        decision = decisions.get(str(row["id"]), {})
        row["item_key"] = str(row["id"])
        row["decision"] = decision.get("status", "pending")
        row["decision_note"] = decision.get("note", "")
        row["asset_id"] = row["id"]
        row["asset_name"] = row["name"]
        row["asset_preview_url"] = ""
    failures = _pending_first(failures)
    sections, sources, skipped = {}, {}, {}
    for category in CANDIDATE_PREFIX:
        rows, source, dropped = _review_rows(contract, category)
        sections[category] = rows
        sources[category] = source
        skipped[category] = dropped
    sections["media_failure"] = failures
    sources["media_failure"] = "ledger"
    # 候选文件缺失和主键缺失都要说出来。静默的空列表会被读成「没有待复核项」。
    return {"sections": sections, "sources": sources, "skipped_rows": skipped,
            "counts": {key: len(value) for key, value in sections.items()}}


def _selected_metadata_candidate(contract: WebContract, item_key: str, candidate_key: str) -> tuple[dict, dict]:
    groups = {row["item_key"]: row
              for row in read_candidates("metadata_fields", contract.candidate_root)[0]}
    group = groups.get(item_key)
    if group is None:
        raise ValueError("字段候选不在当前批次，无法批准")
    if str(group.get("status") or "").strip() != "candidate":
        raise ValueError("只有 candidate 状态的字段候选可以批准")
    try:
        candidates = json.loads(str(group.get("candidates_json") or "[]"))
    except (TypeError, ValueError) as exc:
        raise ValueError("字段候选 JSON 无效") from exc
    selected = next((candidate for candidate in candidates
                     if isinstance(candidate, dict)
                     and str(candidate.get("candidate_key") or "") == candidate_key), None)
    if selected is None:
        raise ValueError("所选来源值不在当前字段候选中")
    return group, selected


def _approved_entity_name(value: object, kind: str) -> str:
    name = str(value or "").strip()
    cleaned = canonicalize_entity_name(kind, name)
    if kind not in {"creator", "performer"}:
        cleaned = collapse_repeated_entity_name(cleaned)
    if not name or not cleaned or cleaned != name:
        raise ValueError("候选仍含重复或未规范化的实体名，拒绝写入")
    return cleaned


def _apply_metadata_candidate(connection, group: dict, candidate: dict, now: str) -> int:
    field = str(group.get("field") or "").strip()
    if field not in {"performers", "studio", "series", "release_date", "tags"}:
        raise ValueError("该元数据字段没有 Peach 写入映射")
    code = str(group.get("code") or "").strip()
    query = str(group.get("query") or code).strip()
    assets = connection.execute(
        "SELECT id FROM asset WHERE medium='video' AND (upper(trim(code))=upper(?) "
        "OR upper(trim(code))=upper(?)) AND (disposal IS NULL OR disposal<>'trash')",
        (code, query),
    ).fetchall()
    asset_ids = sorted({int(row["id"]) for row in assets})
    if not asset_ids:
        raise ValueError("当前 ledger 已没有这个番号的可用资产")
    if len(asset_ids) > REVIEW_APPLY_LIMIT:
        raise ValueError(f"同番号资产 {len(asset_ids)} 条，超过单次批准上限 {REVIEW_APPLY_LIMIT}")
    source = str(candidate.get("source") or "").strip()
    candidate_key = str(candidate.get("candidate_key") or "").strip()
    if not re.fullmatch(r"[a-z0-9_-]+", source) or not candidate_key:
        raise ValueError("字段候选来源无效")
    try:
        confidence = float(candidate.get("confidence"))
    except (TypeError, ValueError) as exc:
        raise ValueError("字段候选置信度无效") from exc
    if not 0 <= confidence <= 1:
        raise ValueError("字段候选置信度越界")
    metadata = {
        "provider": "javinizer-go", "source": source, "source_url": candidate.get("source_url"),
        "raw_snapshot": candidate.get("raw_snapshot"), "review_item": group["item_key"],
        "candidate_key": candidate_key,
    }
    marks = ",".join("?" * len(asset_ids))

    if field == "release_date":
        value = str(candidate.get("value") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("发行日期候选必须是 YYYY-MM-DD")
        try:
            time.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("发行日期候选无效") from exc
        connection.execute(
            f"UPDATE asset SET release_date=? WHERE id IN ({marks})", (value, *asset_ids),
        )
        return len(asset_ids)

    if field in {"studio", "series"}:
        name = _approved_entity_name(candidate.get("value"), field)
        connection.execute(
            f"UPDATE asset SET {field}=? WHERE id IN ({marks})", (name, *asset_ids),
        )
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role=? "
            "AND source LIKE 'javinizer:%'",
            (*asset_ids, field),
        )
        for asset_id in asset_ids:
            upsert_asset_entity(
                connection, kind=field, name=name, asset_id=asset_id, role=field,
                source=f"javinizer:{source}:{field}", confidence=confidence,
                metadata=metadata, now=now,
            )
        return len(asset_ids)

    if field == "performers":
        raw_performers = candidate.get("value")
        if not isinstance(raw_performers, list):
            raise ValueError("演员候选必须是数组")
        performers: list[dict] = []
        seen: set[str] = set()
        for raw in raw_performers:
            if not isinstance(raw, dict):
                raise ValueError("演员候选条目无效")
            name = _approved_entity_name(raw.get("name"), "performer")
            normalized = normalize_entity_name(name)
            if normalized in seen:
                continue
            seen.add(normalized)
            performers.append({**raw, "name": name})
        if not performers:
            raise ValueError("演员候选为空")
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='performer' "
            "AND source LIKE 'javinizer:%'", asset_ids,
        )
        connection.execute(
            f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
            "AND source LIKE 'javinizer:%:performer'", asset_ids,
        )
        for asset_id in asset_ids:
            for performer in performers:
                name = performer["name"]
                external_id = str(performer.get("external_id") or "").strip()
                connection.execute(
                    "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)",
                    (asset_id, "演员:" + name, confidence, f"javinizer:{source}:performer"),
                )
                upsert_asset_entity(
                    connection, kind="performer", name=name, asset_id=asset_id,
                    role="performer", source=f"javinizer:{source}:performer",
                    confidence=confidence, external_provider=(source if external_id else None),
                    external_id=(external_id or None), metadata=metadata, now=now,
                )
        # 演员是 performer 真相，不回写 asset.creator；两种身份混写正是重复名称事故的来源之一。
        return len(asset_ids)

    raw_tags = candidate.get("value")
    if not isinstance(raw_tags, list):
        raise ValueError("标签候选必须是数组")
    tags = list(dict.fromkeys(_approved_entity_name(tag, "tag") for tag in raw_tags))
    if not tags:
        raise ValueError("标签候选为空")
    connection.execute(
        f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='tag' "
        "AND source LIKE 'javinizer:%'", asset_ids,
    )
    connection.execute(
        f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
        "AND source LIKE 'javinizer:%:tag'", asset_ids,
    )
    for asset_id in asset_ids:
        for tag in tags:
            connection.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)",
                (asset_id, tag, confidence, f"javinizer:{source}:tag"),
            )
            upsert_asset_entity(
                connection, kind="tag", name=tag, asset_id=asset_id, role="tag",
                source=f"javinizer:{source}:tag", confidence=confidence,
                metadata=metadata, now=now,
            )
    return len(asset_ids)


#: 候选图的扩展名 -> content type。`/logo` 靠 `.ct` 边车决定回什么头。
LOGO_CONTENT_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".ico": "image/x-icon",
}


def studio_logo_key(studio: str) -> str:
    """和 `PreviewService.logo` 完全一致的落盘名，两边必须同一套规则。"""
    return re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]


def _install_studio_logo(contract: WebContract, studio: str) -> int:
    r"""把已批准的厂牌 logo 候选装进 `/logo` 真正读的目录。

    早先 `studio_logos` 只出现在分类白名单里，没有任何写入分支：点「通过」只往
    `review_decision` 记一笔，logo 一张也没装上——配合当时「队列不过滤已判项」的
    毛病，表现就是点完通过、一刷新原样又回来。

    候选 CSV 的 `saved` 列写的是 `R:\peach-data\...`，那是旧数据根；现在数据在
    `peach-data` 下，按绝对路径找必然落空。所以只取文件名，在当前候选目录里解析。
    """
    rows = {row["item_key"]: row
            for row in read_candidates("studio_logos", contract.candidate_root)[0]}
    candidate = rows.get(studio)
    if candidate is None:
        raise ValueError("候选不在当前批次，无法批准")
    saved = str(candidate.get("saved") or "").strip()
    if not saved:
        raise ValueError("该候选没有落盘的图片，无法装载")
    source = contract.candidate_root / "studio-logos" / PurePosixPath(
        saved.replace("\\", "/")).name
    if not source.is_file():
        raise ValueError(f"候选图片不在本机：{source.name}")
    key = studio_logo_key(studio)
    if not key:
        raise ValueError("厂牌名无法生成落盘名")
    content_type = LOGO_CONTENT_TYPES.get(source.suffix.lower())
    if content_type is None:
        raise ValueError(f"不支持的图片格式：{source.suffix}")
    contract.logo_root.mkdir(parents=True, exist_ok=True)
    destination = contract.logo_root / f"{key}.img"
    # 先写临时文件再原子替换：中途失败不会留下半张图被 `/logo` 读到。
    staging = destination.with_name(f"{destination.name}.{uuid.uuid4().hex}.tmp")
    staging.write_bytes(source.read_bytes())
    os.replace(staging, destination)
    Path(f"{destination}.ct").write_text(content_type, encoding="utf-8")
    Path(f"{destination}.provenance.json").write_text(json.dumps({
        "source": "studio logo review",
        "source_file": source.name,
        "resolved_url": candidate.get("resolved_url") or "",
        "handle": candidate.get("handle") or "",
        "platform": candidate.get("platform") or "",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "local studio identity cache",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1


def w_review_auto_apply(contract: WebContract, _body=None):
    """把确定的那部分直接落库，不占人工队列。

    ADR-0018：这是「刮削结果只作候选、不直接改写真相字段」的一个**窄例外**，
    不是废除该规则。判据见 `metadata_auto_apply_candidate`，四项缺一即回到人工。
    每条仍写 review_decision 留痕（note 里记来源与判据），所以事后可以追问
    「这个值是谁写的、凭什么」——留痕才是那条规则真正要保住的东西。
    """
    rows, _source, _skipped = read_candidates("metadata_fields", contract.candidate_root)
    applied, skipped = [], 0
    with contract.write_transaction() as connection:
        decided = {row["item_key"] for row in connection.execute(
            "SELECT item_key FROM review_decision WHERE category='metadata_fields'")}
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for row in rows:
            item_key = str(row.get("item_key") or "").strip()
            if not item_key or item_key in decided:
                continue
            if str(row.get("status") or "").strip() != "candidate":
                continue
            try:
                parsed = json.loads(str(row.get("candidates_json") or "[]"))
            except (TypeError, ValueError):
                continue
            row = dict(row)
            row["candidates"] = [c for c in parsed if isinstance(c, dict)
                                 and str(c.get("candidate_key") or "").strip()]
            candidate = metadata_auto_apply_candidate(connection, row)
            if candidate is None:
                skipped += 1
                continue
            try:
                count = _apply_metadata_candidate(connection, row, candidate, now)
            except ValueError:
                # 落库条件在这一刻不成立（例如资产已删）：回到人工，不记决定。
                skipped += 1
                continue
            connection.execute(
                "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                "VALUES('metadata_fields',?,'approved',?,?) "
                "ON CONFLICT(category,item_key) DO UPDATE SET status=excluded.status,"
                "note=excluded.note,updated_at=excluded.updated_at",
                (item_key, json.dumps({
                    "auto_applied": True, "rule": "adr-0018-empty-field-single-official-source",
                    "candidate_key": candidate.get("candidate_key"),
                    "source": candidate.get("source"),
                    "value": candidate.get("display_value"),
                }, ensure_ascii=False, separators=(",", ":")), now),
            )
            applied.append({"item_key": item_key, "field": row.get("field"),
                            "value": candidate.get("display_value"),
                            "assets": count})
    contract.cache_bust()
    return {"ok": True, "applied": len(applied), "left_to_review": skipped,
            "items": applied}


def w_review_decision(contract: WebContract, body):
    category = str(body.get("category", "")).strip()
    item_key = str(body.get("item_key", "")).strip()
    status = str(body.get("status", "")).strip()
    # 复核页展示的每个 tab 都必须能记录决定；漏掉一个，那一页的通过/跳过/拒绝就全部 400，
    # 前端静默时看起来就是「点了没反应」。`cover_sources` 曾这样漏掉。
    if category not in {
        "metadata_fields", "creator_tags", "studio_logos", "performer_avatars",
        "western_identity", "code_creators", "cover_sources", "fc2_markings",
        "fc2_similarity", "video_endcards", "media_failure",
    }:
        raise ValueError("invalid review category")
    if not item_key or status not in {"approved", "rejected", "skipped"}:
        raise ValueError("invalid review decision")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    note = str(body.get("note", "")).strip()[:2000]
    with contract.write_transaction() as connection:
        connection.execute(
            "INSERT INTO review_decision(category,item_key,status,note,updated_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(category,item_key) DO UPDATE SET status=excluded.status,note=excluded.note,updated_at=excluded.updated_at",
            (category, item_key, status, note, now),
        )
        applied = 0
        if category == "metadata_fields" and status == "approved":
            candidate_key = str(body.get("candidate_key") or "").strip()
            if not candidate_key:
                raise ValueError("批准字段候选时必须选择一个来源值")
            group, candidate = _selected_metadata_candidate(contract, item_key, candidate_key)
            applied = _apply_metadata_candidate(connection, group, candidate, now)
            provenance_note = json.dumps({
                "candidate_key": candidate_key, "source": candidate.get("source"),
                "user_note": note,
            }, ensure_ascii=False, separators=(",", ":"))
            connection.execute(
                "UPDATE review_decision SET note=? WHERE category=? AND item_key=?",
                (provenance_note, category, item_key),
            )
        elif category == "creator_tags" and status == "approved":
            # 权威值只能来自候选文件本身。早先版本直接采信请求体，于是「批准候选 X」
            # 可以写入与 X 无关的创作者和标签，而 review_decision 里留痕仍写着 X 通过。
            candidates = {row["item_key"]: row
                          for row in read_candidates(category, contract.candidate_root)[0]}
            candidate = candidates.get(item_key)
            if candidate is None:
                raise ValueError("候选不在当前批次，无法批准")
            if str(candidate.get("status") or "").strip() != "candidate":
                raise ValueError("只有 candidate 状态的复核项可以批准")
            creator = str(candidate.get("creator") or "").strip()
            tags = [tag.strip() for tag in str(candidate.get("tags") or "").split("|") if tag.strip()]
            claimed_creator = str(body.get("creator", "")).strip()
            claimed_tags = [tag.strip() for tag in str(body.get("tags", "")).split("|") if tag.strip()]
            if (claimed_creator and claimed_creator != creator) or (claimed_tags and claimed_tags != tags):
                raise ValueError("提交内容与候选不一致，拒绝写入")
            if not creator or not tags:
                raise ValueError("approved creator review requires creator and tags")
            entity = connection.execute(
                "SELECT e.id FROM entity e LEFT JOIN entity_alias a ON a.entity_id=e.id "
                "WHERE e.kind='creator' AND (e.canonical_name=? OR a.alias=?) LIMIT 1",
                (creator, creator),
            ).fetchone()
            if not entity:
                raise ValueError("creator entity not found")
            assets = connection.execute(
                "SELECT DISTINCT ae.asset_id FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
                "WHERE ae.entity_id=? AND ae.role='creator' AND a.medium='video' AND a.disposal IS NULL",
                (entity["id"],),
            ).fetchall()
            selected_ids = {int(value) for value in body.get("selected_ids") or []}
            available_ids = {asset["asset_id"] for asset in assets}
            if selected_ids:
                if not selected_ids <= available_ids:
                    raise ValueError("selected assets are outside the reviewed creator")
                asset_ids = sorted(selected_ids)
            else:
                # 没有勾选就是「整条候选通过」。早先版本在这里什么都不写，
                # 却照样把决定记成 approved——留痕说通过、实际没写是最糟的组合。
                asset_ids = sorted(available_ids)
                if len(asset_ids) > REVIEW_APPLY_LIMIT:
                    raise ValueError(
                        f"该创作者有 {len(asset_ids)} 条作品，超过单次批准上限 "
                        f"{REVIEW_APPLY_LIMIT}，请在页面上显式勾选后再通过"
                    )
            payload = json.dumps({"review_item": item_key}, ensure_ascii=False)
            connection.executemany(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "VALUES(?,?,0.6,'vision_creator_review')",
                [(asset_id, tag) for asset_id in asset_ids for tag in tags],
            )
            for tag in tags:
                # 标签实体只解析一次，关系走 executemany。
                # 逐条调用 upsert_asset_entity 会在持写锁期间跑上千次往返，把其它写入全挡住。
                normalized = normalize_entity_name(tag)
                connection.execute(
                    "INSERT INTO entity(kind,canonical_name,normalized_name,metadata_json,"
                    "created_at,updated_at) VALUES('tag',?,?,'{}',?,?) "
                    "ON CONFLICT(kind,normalized_name) DO UPDATE SET "
                    "canonical_name=excluded.canonical_name,updated_at=excluded.updated_at",
                    (tag, normalized, now, now),
                )
                entity_id = connection.execute(
                    "SELECT id FROM entity WHERE kind='tag' AND normalized_name=?", (normalized,),
                ).fetchone()[0]
                connection.executemany(
                    "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence,"
                    "metadata_json,first_seen_at,last_seen_at) "
                    "VALUES(?,?,'tag','vision_creator_review',0.6,?,?,?) "
                    "ON CONFLICT(asset_id,entity_id,role,source) DO UPDATE SET "
                    "confidence=excluded.confidence,metadata_json=excluded.metadata_json,"
                    "last_seen_at=excluded.last_seen_at",
                    [(asset_id, entity_id, payload, now, now) for asset_id in asset_ids],
                )
            applied = len(asset_ids)
        elif category == "studio_logos" and status == "approved":
            applied = _install_studio_logo(contract, item_key)
    contract.cache_bust()   # 标签写完，聚合缓存必须失效，否则 facets 最多 90 秒还是旧数
    return {"ok": True, "category": category, "item_key": item_key, "status": status, "applied_assets": applied}


def q_facets(
    contract: WebContract,
    jav: bool = False,
    scope_kind: str = "",
    scope_name: str = "",
    asset_id: int | None = None,
):
    """返回当前浏览集合真正存在的筛选项。

    首页不带 scope，维持全库口径；实体资料页按规范实体收窄，详情页按单个作品收窄。
    筛选项必须来自和作品列表相同的规范关系，不能让前端拿全库 facets 猜当前页面。
    """
    c = contract.db()
    scope = JAV_ASSET_CLAUSE if jav else ""
    scope_params: list[object] = []
    if asset_id is not None:
        scope += "AND a.id=? "
        scope_params.append(int(asset_id))
    elif scope_kind or scope_name:
        if scope_kind not in {"creator", "performer", "studio", "series"} or not scope_name:
            c.close()
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
        "AND NOT EXISTS(SELECT 1 FROM entity performer WHERE performer.kind='performer' "
        "AND performer.normalized_name=e.normalized_name) "
        "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 400", scope_params)]
    out["tags"] = [dict(r, cat=tag_cat(r["k"])) for r in rows
                   if r["k"] not in TECH_TAGS and r["k"] not in LENGTH_TAGS][:44]
    out["tech"] = [r for r in rows if r["k"] in TECH_TAGS][:16]
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
    c.close()
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
    with contract.write_lock:
        c = contract.db(write=True)
        if not c.execute("SELECT 1 FROM asset WHERE id=?", (aid,)).fetchone():
            c.close()
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
        c.commit(); c.close()
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
    return {"ok": True, "operation": "empty-trash", **_finish_purge(outcome)}


def source_is_online(location: str) -> bool:
    """这个来源整体在不在线。对账前的唯一闸门。"""
    declared = LOCATION_ROOT_DECLARATIONS.get(location)
    if not declared:
        return False
    resolved = translate_ledger_path(declared)
    return not is_unmapped(resolved) and root_online(resolved)


def w_purge_missing(contract: WebContract, body):
    """按目录对账：文件已经在磁盘上删掉的，账本行一并删掉。

    这条路径服务的是「我在资源管理器里整理网盘目录」——删掉的就是不要的，所以
    不进复核、不进回收站、不可恢复，播放历史等衍生行跟着一起走。

    真正危险的不是删得太干净，而是把「盘没挂上」误判成「文件没了」：R: 掉线时
    整条来源 2,552 行都会看起来像被删。所以先做来源级在线判定，整源不在线就
    一行都不碰。CloudDrive 掉线后挂载点目录仍然存在，`root_online` 因此判的是
    「能否列出一个条目」而不是「目录在不在」。
    """
    asset_id = int(body["id"])
    with contract.read_connection() as connection:
        anchor = connection.execute(
            "SELECT id,location,path,name FROM asset WHERE id=?", (asset_id,),
        ).fetchone()
        if not anchor:
            return {"error": "not found"}
        location, path, name = anchor["location"], anchor["path"], anchor["name"]
        if not path or not name:
            return {"error": "asset has no path"}
        if not source_is_online(location):
            # 不是失败，是拒绝：盘不在时无法区分「文件删了」和「盘没挂上」。
            return {"ok": False, "error": "source offline", "location": location}
        directory = path[: len(path) - len(name) - 1]
        rows = connection.execute(
            f"SELECT id,path,name FROM asset WHERE location=? "
            f"AND {dir_expr('')}=?",
            (location, directory),
        ).fetchall()

    missing = [
        {"id": row["id"], "name": row["name"]}
        for row in rows
        if not translate_ledger_path(row["path"]).is_file()
    ]
    if not missing:
        return {"ok": True, "directory": photo_set_title(directory),
                "checked": len(rows), "removed": 0, "items": []}

    contract.cache_bust()
    ids = [item["id"] for item in missing]
    marks = ",".join("?" * len(ids))
    with contract.write_transaction() as connection:
        connection.execute(
            f"UPDATE playlist SET current_asset_id=NULL WHERE current_asset_id IN ({marks})",
            ids,
        )
        connection.execute(
            f"UPDATE playlist SET source_seed_asset_id=NULL WHERE source_seed_asset_id IN ({marks})",
            ids,
        )
        for table in ASSET_REFERENCE_TABLES:
            connection.execute(
                f"DELETE FROM {table} WHERE asset_id IN ({marks})", ids)
        # asset_search 交给 0004 的删除触发器，这里再删一遍只会重复。
        connection.execute(f"DELETE FROM asset WHERE id IN ({marks})", ids)
    return {
        "ok": True, "directory": photo_set_title(directory),
        "checked": len(rows), "removed": len(missing), "items": missing,
    }


def w_batch(contract: WebContract, body):
    """Apply one explicit, reversible marker to a bounded selected set."""
    raw_ids = body.get("ids")
    if not isinstance(raw_ids, list):
        raise TypeError("ids must be a list")
    ids = list(dict.fromkeys(int(item) for item in raw_ids))
    if not ids or len(ids) > 200:
        raise ValueError("batch requires 1 to 200 assets")
    operation = body.get("operation")
    if operation not in {"like", "seen", "later", "dispose", "restore", "delete"}:
        raise ValueError("unsupported batch operation")
    marks = ",".join("?" * len(ids))
    contract.cache_bust()
    purge_outcome = None
    try:
        with contract.write_transaction() as connection:
            found = connection.execute(
                f"SELECT id,path,snapshot_path,disposal FROM asset WHERE id IN ({marks})", ids,
            ).fetchall()
            valid_ids = [row["id"] for row in found]
            if not valid_ids:
                raise ValueError("assets not found")
            if operation in {"restore", "delete"} and any(row["disposal"] != "trash" for row in found):
                raise ValueError("restore/delete is only allowed for recycle-bin assets")
            now = time.time()
            if operation == "restore":
                placeholders = ",".join("?" * len(valid_ids))
                connection.execute(
                    f"UPDATE asset SET disposal=NULL,feedback_at=? WHERE id IN ({placeholders})",
                    [now, *valid_ids],
                )
            elif operation == "delete":
                purge_outcome = purge_assets(connection, found)
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
        return {"ok": True, "operation": operation, **_finish_purge(purge_outcome)}
    return {"ok": True, "operation": operation, "changed": len(valid_ids)}


def q_duplicates(contract: WebContract, args):
    """按番号 + 时长找真重复；每簇标出最大与最长的那个。"""
    limit = min(max(int(args.get("limit", "60")), 1), 300)
    offset = max(int(args.get("offset", "0")), 0)
    connection = contract.db()
    try:
        rows = connection.execute(
            "SELECT id,code,location,path,name,size,duration,hash,disposal "
            "FROM asset WHERE medium='video' AND code IS NOT NULL AND code<>'' "
            "AND (disposal IS NULL OR disposal<>'trash')"
        ).fetchall()
    finally:
        connection.close()

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if not is_jav_code(row["code"]):
            continue
        item = dict(row)
        item["drive"] = str(item.pop("path") or "")[:2].upper()
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
    connection = contract.db()
    try:
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
    finally:
        connection.close()
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
    return contract.cached(
        f"tops{n}{'-jav' if jav else ''}:{seed}",
        lambda: q_tops(contract, n, jav=jav, seed=seed),
    )


def _get_ads(contract, args):
    return q_ads(
        contract,
        min(int(args.get("limit", "60")), 200),
        max(int(args.get("offset", "0")), 0),
    )


def _get_related(contract, args):
    return q_related(contract, int(args["id"]), min(int(args.get("limit", "24")), 60))


def _get_facets(contract, args):
    jav = args.get("jav") == "1"
    scope_kind = str(args.get("scope_kind", ""))
    scope_name = str(args.get("scope_name", ""))
    asset_id = int(args["id"]) if args.get("id") else None
    scope_key = f"{scope_kind}:{scope_name}:{asset_id or ''}"
    return contract.cached(
        f"facets{'-jav' if jav else ''}:{scope_key}",
        lambda: q_facets(
            contract,
            jav=jav, scope_kind=scope_kind, scope_name=scope_name, asset_id=asset_id,
        ),
    )


def _get_search_history(contract, args):
    return q_search_history(contract, int(args.get("limit", "10")))


def _get_review(contract, _args):
    return contract.cached("review", lambda: q_review(contract))


def _post_empty_trash(contract, _body):
    return w_empty_trash(contract)


GET_HANDLERS = {
    "/api/follow": q_follow,
    "/api/follow/credentials": q_follow_credentials,
    "/api/items": q_items,
    "/api/item": _get_item,
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
    "/api/review": _get_review,
}

POST_HANDLERS = {
    "/api/follow/check": w_follow_check,
    "/api/follow/source": w_follow_source,
    "/api/follow/status": w_follow_status,
    "/api/follow/save": w_follow_save,
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
    "/api/trash/empty": _post_empty_trash,
    "/api/purge-missing": w_purge_missing,
    "/api/review/auto-apply": w_review_auto_apply,
    "/api/review/decision": w_review_decision,
}


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
