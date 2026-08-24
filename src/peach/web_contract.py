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
from pathlib import Path
from typing import Sequence
from urllib.parse import quote, urlsplit

from .config import COVER_DIR, GENERATED_DIR
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
    upsert_asset_entity,
)
from .media import remap_managed_path
from .platform import system_volume
from .repository import LedgerDatabase
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
    is_jav_code,
    normalise_code_key,
    part_marker,
    tag_cat,
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
)


class WebContract:
    """单个应用实例的数据库、写锁和聚合缓存；不共享模块级可变状态。"""

    def __init__(self, db_path: Path, snapshot_root: Path | None = None,
                 legacy_snapshot_roots: Sequence[Path] = (),
                 candidate_root: Path | None = None,
                 cover_root: Path | None = None,
                 avatar_root: Path | None = None,
                 database: LedgerDatabase | None = None):
        # 候选 CSV 的目录做成实例属性而不是模块常量，复核层才能在临时目录里被测试。
        self.candidate_root = Path(candidate_root) if candidate_root is not None else GENERATED_DIR
        self.cover_root = Path(cover_root) if cover_root is not None else COVER_DIR
        self.avatar_root = Path(avatar_root) if avatar_root is not None else GENERATED_DIR / "avatars"
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
        # 只按 `code` 非空过滤会混进账号名与站点水印；判据必须看形态。
        where.append("a.code IS NOT NULL AND a.code<>'' AND is_jav_code(a.code)")
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
    for r in rows:
        r["cost"] = COST.get(r["location"], "metered")
        r["has_thumb"] = contract.has_snapshot(r["snapshot_path"])
        r["has_cover"] = contract.has_cover(r.get("code"))
        # 卡片上的出镜者称谓要和详情页同一口径：番号发行物才叫女优。
        r["is_jav"] = is_jav_code(r.get("code"))
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
    # 「女优」是番号发行物的行业称谓；其他内容里出镜者只是艺人。形态判据只有
    # `is_jav_code` 一份（分隔符规则是踩过坑换来的），不能在前端再写一遍。
    d["is_jav"] = is_jav_code(d.get("code"))
    d.pop("snapshot_path", None); d.pop("path", None)
    return d

def q_ads(contract: WebContract, limit=200, offset=0):
    """疑似广告复核队列 —— **不自动删**，只排队让人看接触印相确认。

    没有可靠的单一判据（试过「同番号短版」会误伤 CD2/part1 分卷，
    试过「同名扩散」会误伤 001.mp4 这类通用名的真文件）。
    所以给的是**嫌疑分**，按分排序，人工看图定夺，确认的走既定 CSV 删除流程。"""
    c = contract.db()
    rows = c.execute(
        "SELECT id,location,name,creator,code,size,duration,width,height,snapshot_path,"
        "feedback,disposal,play_count,leave_ratio,o_count,studio,ctx_orient "
        "FROM asset WHERE medium='video' AND size < 500*1024*1024 "
        "AND duration IS NOT NULL AND duration BETWEEN 15 AND 1200 "
        "AND (disposal IS NULL)").fetchall()
    # 同番号是否存在明显更长的版本
    longer = {r[0]: r[1] for r in c.execute(
        "SELECT code, max(duration) FROM asset WHERE medium='video' AND code IS NOT NULL "
        "AND code<>'' AND duration IS NOT NULL GROUP BY code")}
    out = []
    PROMO = re.compile(r"(扫码|二维码|加微|威信|微信|广告|推广|免费看|福利群|最新地址|"
                       r"永久|点击|下载APP|在线视频|强力推荐|国产大片|www\.|\.com|\.me|\.la|\.xyz)", re.I)
    PART = re.compile(r"(CD\d|part\d|分卷|-\d{1,2}$|\(\d+\)$)", re.I)
    for r in rows:
        d = dict(r)
        s, why = 0, []
        nm = os.path.splitext(d["name"])[0]
        if PROMO.search(nm):
            s += 50; why.append("名字含推广词")
        mx = longer.get(d["code"] or "")
        if mx and d["duration"] < mx * 0.2 and not PART.search(nm):
            s += 35; why.append(f"同番号有 {mx/60:.0f} 分完整版")
        if d["duration"] < 240:
            s += 15; why.append("不足 4 分钟")
        if (d["size"] or 0) < 120 * 1024**2:
            s += 10; why.append("小于 120 MB")
        if s >= 40:
            d["score"] = s; d["why"] = " · ".join(why)
            d["cost"] = COST.get(d["location"], "metered")
            d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
            d.pop("snapshot_path", None)
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

#: JAV 语境下的资产过滤片段。顶部三层与筛选面板都要跟着收窄，否则在 JAV 模式里
#: 仍然列着只出现在创作者作品里的女优和厂牌，点进去却是空的。
JAV_ASSET_CLAUSE = "AND a.code IS NOT NULL AND a.code<>'' AND is_jav_code(a.code) "


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
    row = c.execute(
        "SELECT DISTINCT e.* FROM entity e LEFT JOIN entity_alias a ON a.entity_id=e.id "
        "WHERE e.kind=? AND (e.canonical_name=? OR a.alias=?) LIMIT 1",
        (kind, name, name),
    ).fetchone()
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
}
def _needs_review(category: str, row: dict) -> bool:
    """已经有定论的行不该占复核页。

    babepedia 那批 168 条里有 143 条是「确认无档案」——站上确实没有这个人，
    没有可判断的东西，全列出来只会把真正要看的 25 条淹掉。封面同理：拿到 2184
    宽的高清图不需要人确认，未取得和仍停在 800 低清基线的才需要。
    """
    if category == "western_identity":
        return str(row.get("verdict") or "") in ("命中", "需人工确认")
    if category == "cover_sources":
        if str(row.get("result") or "") != "取得":
            return True
        try:
            return int(row.get("width") or 0) < 1200
        except ValueError:
            return True
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
            previews = _creator_previews(
                connection, [str(row.get("creator") or "").strip() for row in rows],
            )
            for row in rows:
                row["preview_assets"] = previews.get(str(row.get("creator") or "").strip(), [])
        elif category == "metadata_fields":
            for row in rows:
                try:
                    candidates = json.loads(str(row.get("candidates_json") or "[]"))
                except (TypeError, ValueError):
                    candidates = []
                row["candidates"] = [candidate for candidate in candidates
                                     if isinstance(candidate, dict)
                                     and str(candidate.get("candidate_key") or "").strip()]
    finally:
        connection.close()
    for row in rows:
        decision = decisions.get(row["item_key"], {})
        row["decision"] = decision.get("status", "pending")
        row["decision_note"] = decision.get("note", "")
        row["preview_url"] = (row.get("resolved_url") or row.get("source_url")
                              or row.get("avatar_url") or row.get("portrait_url") or "")
        if category == "cover_sources" and row.get("result") == "取得":
            # 封面已经在本机，直接看落盘的那张，不要回源站再拉一次。
            row["preview_url"] = f"/cover?code={quote(str(row.get('code') or ''))}"
        if not row.get("reason"):
            row["reason"] = _review_evidence(category, row)
    return rows, source, skipped


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


def w_review_decision(contract: WebContract, body):
    category = str(body.get("category", "")).strip()
    item_key = str(body.get("item_key", "")).strip()
    status = str(body.get("status", "")).strip()
    if category not in {"metadata_fields", "creator_tags", "studio_logos", "performer_avatars", "media_failure"}:
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
    "/api/items": q_items,
    "/api/item": _get_item,
    "/api/entity": q_entity,
    "/api/index": _get_index,
    "/api/duplicates": q_duplicates,
    "/api/stats": _get_stats,
    "/api/tops": _get_tops,
    "/api/ads": _get_ads,
    "/api/related": _get_related,
    "/api/facets": _get_facets,
    "/api/search-history": _get_search_history,
    "/api/review": _get_review,
}

POST_HANDLERS = {
    "/api/activity": w_activity,
    "/api/play": w_play,
    "/api/feedback": w_feedback,
    "/api/watch-later": w_watch_later,
    "/api/preference": w_preference,
    "/api/quality-goal": w_quality_goal,
    "/api/item-tag": w_item_tag,
    "/api/batch": w_batch,
    "/api/search-history": w_search_history,
    "/api/trash/empty": _post_empty_trash,
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
