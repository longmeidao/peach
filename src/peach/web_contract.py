"""Stable JSON contract used by the FastAPI application.

Database reads are read-only by default. Writes are limited to explicit activity and
feedback functions; schema changes belong to the migration runner.
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Sequence

from .media import remap_managed_path

COST = {"local": "free", "115": "free", "pikpak": "metered", "online": "metered"}

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0B0B0D"/><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF9A76"/><stop offset="1" stop-color="#F2557B"/></linearGradient></defs><path d="M16 28c-5.7 0-9.7-3.6-9.7-8.6 0-4.3 2.8-7.6 6.5-7.6 1.4 0 2.4.5 3.2 1.1.8-.6 1.8-1.1 3.2-1.1 3.7 0 6.5 3.3 6.5 7.6C25.7 24.4 21.7 28 16 28z" fill="url(#pg)"/><path d="M16 13.4V27" stroke="#0B0B0D" stroke-width="1.1" opacity=".3" stroke-linecap="round"/><path d="M17.1 11.7c.6-2.8 2.8-4.6 5.6-4.8-.2 2.8-2.2 4.7-5.6 4.8z" fill="#5FB95F"/><path d="M16 11.9c0-1.9.5-3.4 1.5-4.5" stroke="#8A5A3B" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>')

CACHE_TTL = 90


class WebContract:
    """单个应用实例的数据库、写锁和聚合缓存；不共享模块级可变状态。"""

    def __init__(self, db_path: Path, snapshot_root: Path | None = None,
                 legacy_snapshot_roots: Sequence[Path] = ()):
        self.db_path = Path(db_path)
        self.snapshot_root = Path(snapshot_root) if snapshot_root is not None else None
        self.legacy_snapshot_roots = tuple(Path(path) for path in legacy_snapshot_roots)
        self.write_lock = threading.Lock()
        self.cache: dict[str, tuple[float, object]] = {}
        self.cache_lock = threading.Lock()

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
        target = (str(self.db_path) if write else
                  self.db_path.resolve().as_uri() + "?mode=ro")
        connection = sqlite3.connect(
            target, timeout=30, check_same_thread=False, uri=not write,
        )
        connection.row_factory = sqlite3.Row
        return connection

    def has_snapshot(self, raw_path: str | None) -> bool:
        if not raw_path:
            return False
        path = (remap_managed_path(
            raw_path, self.snapshot_root, self.legacy_snapshot_roots,
        ) if self.snapshot_root is not None else Path(raw_path))
        return path.is_file()

# ────────────────────────────── 查询 ──────────────────────────────

def q_items(contract: WebContract, args):
    where, par = ["a.medium='video'"], []
    if args.get("loc"):
        locs = [x for x in args["loc"].split(",") if x]
        where.append("a.location IN (%s)" % ",".join("?" * len(locs))); par += locs
    if args.get("creator"):
        where.append("a.creator = ?"); par.append(args["creator"])
    if args.get("studio"):
        where.append("a.studio = ?"); par.append(args["studio"])
    if args.get("tag"):
        # 逗号分隔 = 组合筛选，全部满足（Beeg 的 /PinkLoving+Anal）
        for tg in [x for x in args["tag"].split(",") if x]:
            where.append("EXISTS(SELECT 1 FROM asset_tag t WHERE t.asset_id=a.id AND t.tag=?)")
            par.append(tg)
    if args.get("len"):
        where.append("a.ctx_length = ?"); par.append(args["len"])
    if args.get("orient"):
        where.append("a.ctx_orient = ?"); par.append(args["orient"])
    if args.get("q"):
        where.append("(a.name LIKE ? OR a.creator LIKE ? OR a.code LIKE ?)")
        s = f"%{args['q']}%"; par += [s, s, s]
    if args.get("state") == "fresh":
        where.append("(a.play_count IS NULL OR a.play_count=0) AND a.feedback IS NULL")
    elif args.get("state") == "played":
        where.append("a.play_count > 0")
    elif args.get("state") == "flagged":
        where.append("a.feedback IS NOT NULL OR a.disposal IS NOT NULL")
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
    sql = ("SELECT a.id,a.location,a.path,a.name,a.creator,a.studio,a.code,a.size,"
           "a.duration,a.width,a.height,a.ctx_length,a.ctx_orient,a.snapshot_path,"
           "a.play_count,a.leave_ratio,a.feedback,a.disposal,a.rating,a.o_count,""a.play_seconds,a.max_reached,a.seek_count "
           "FROM asset a WHERE " + " AND ".join(where) + f" ORDER BY {order} LIMIT ? OFFSET ?")
    c = contract.db()
    rows = [dict(r) for r in c.execute(sql, par + [lim, off])]
    cnt = c.execute("SELECT count(*) FROM asset a WHERE " + " AND ".join(where), par).fetchone()[0]
    c.close()
    # 卡片要显示出镜者和高权重标签，不能只有番号 —— 一次批量取，别 N+1
    if rows:
        ids = [r["id"] for r in rows]
        qm = ",".join("?" * len(ids))
        tmap = {}
        for aid, tag in con_tags(contract, ids, qm):
            tmap.setdefault(aid, []).append(tag)
        for r in rows:
            ts = tmap.get(r["id"], [])
            r["tags"] = [t for t in ts if tag_cat(t) in ("general", "character", "copyright")][:4]
            r["performers"] = [t[3:] for t in ts if t.startswith("演员:")][:3]
    for r in rows:
        r["cost"] = COST.get(r["location"], "metered")
        r["has_thumb"] = contract.has_snapshot(r["snapshot_path"])
        r.pop("snapshot_path", None)
        r.pop("path", None)                     # 路径不外发，串流走 id
    return {"total": cnt, "items": rows}

def con_tags(contract: WebContract, ids, qm):
    c = contract.db()
    try:
        return c.execute(
            f"SELECT asset_id, tag FROM asset_tag WHERE asset_id IN ({qm})", ids).fetchall()
    finally:
        c.close()

def q_item(contract: WebContract, aid):
    """按 id 直取。
    ⚠️ 第一版没有这个接口，前端用「带筛选条件再查一遍然后 find」的绕法，
       limit 被覆盖成 1 → find 必然失败 → 走兜底 items[0]，
       于是**每次点击都打开同一个默认列表首项**（一个 12.6 GB 的 PikPak 文件），
       既显示错条目，又反复拉计费流量。教训：按 id 取就按 id 取。"""
    c = contract.db()
    r = c.execute(
        "SELECT id,location,path,name,creator,studio,code,size,duration,width,height,"
        "ctx_length,ctx_orient,snapshot_path,play_count,leave_ratio,feedback,disposal,"
        "rating,o_count,play_seconds,max_reached,seek_count FROM asset WHERE id=?", (aid,)).fetchone()
    if not r:
        c.close(); return {"error": "not found"}
    d = dict(r)
    _ts = [x[0] for x in c.execute("SELECT tag FROM asset_tag WHERE asset_id=? ORDER BY tag", (aid,))]
    d["tags"] = [{"k": t, "cat": tag_cat(t)} for t in _ts]
    d["performers"] = [t[3:] for t in _ts if t.startswith("演员:")]
    c.close()
    d["cost"] = COST.get(d["location"], "metered")
    d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
    d.pop("snapshot_path", None); d.pop("path", None)
    return d

# ── 标签分级（配色用，参考 rule34 的分类着色）──
TECH_TAGS = {"1080P", "720P", "4K", "2K", "2160P", "480P", "低画质", "高帧率",
             "短片-2分内", "中片-10分内", "长片-30分内", "超长片", "横屏", "竖屏",
             "真人", "混合集", "身份待确认", "R-18", "有码", "无码"}
COPYRIGHT_HINT = re.compile(
    r"(ブルーアーカイブ|崩壊|崩坏|原神|勝利の女神|NIKKE|アークナイツ|明日方舟|"
    r"FGO|Fate|東方|东方|艦これ|舰娘|ウマ娘|赛马娘|ポケモン|宝可梦|"
    r"サイバーパンク|Honkai|Genshin|Blue Archive|VTuber|hololive|にじさんじ)", re.I)

def tag_cat(t):
    """rule34 式分级：meta 规格 / artist 创作者 / character 角色 / copyright 作品 / general 内容"""
    if t.startswith("演员:"):  return "artist"
    if t in TECH_TAGS:         return "meta"
    if COPYRIGHT_HINT.search(t): return "copyright"
    if re.search(r"(ちゃん|さん|酱|娘)$", t) and len(t) <= 8: return "character"
    return "general"

def q_ads(contract: WebContract, limit=200):
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
    return {"total": len(out), "items": out[:limit]}

def q_related(contract: WebContract, aid, limit=24):
    """接着看 —— 把口味接近的串成播放列表。
    优先级：同创作者 > 共享标签最多 > 同厂牌。全部排除已标记不合口味的。"""
    c = contract.db()
    r = c.execute("SELECT creator,studio,code,ctx_orient FROM asset WHERE id=?", (aid,)).fetchone()
    if not r:
        c.close(); return {"items": []}
    tags = [x[0] for x in c.execute("SELECT tag FROM asset_tag WHERE asset_id=?", (aid,))]
    picked, seen = [], {aid}

    def take(sql, par, why):
        for row in c.execute(sql, par):
            d = dict(row)
            if d["id"] in seen or len(picked) >= limit:
                continue
            seen.add(d["id"]); d["why"] = why; picked.append(d)

    COLS = ("id,location,name,creator,studio,code,size,duration,width,height,"
            "ctx_orient,snapshot_path,play_count,leave_ratio,feedback,disposal,o_count")
    base = (f"SELECT {COLS} FROM asset WHERE medium='video' AND id<>? "
            "AND (feedback IS NULL OR feedback<>'dislike') AND (disposal IS NULL)")
    if r["creator"]:
        take(base + " AND creator=? ORDER BY (play_count IS NULL OR play_count=0) DESC, random() LIMIT ?",
             (aid, r["creator"], limit), "同创作者")
    if tags and len(picked) < limit:
        qm = ",".join("?" * len(tags))
        take(f"SELECT {COLS} FROM asset a WHERE a.medium='video' AND a.id<>? "
             f"AND (a.feedback IS NULL OR a.feedback<>'dislike') AND a.disposal IS NULL "
             f"AND (SELECT count(*) FROM asset_tag t WHERE t.asset_id=a.id AND t.tag IN ({qm})) >= "
             f"{max(1, min(2, len(tags)))} "
             "ORDER BY (a.play_count IS NULL OR a.play_count=0) DESC, random() LIMIT ?",
             tuple([aid] + tags + [limit]), "标签接近")
    if r["studio"] and len(picked) < limit:
        take(base + " AND studio=? ORDER BY random() LIMIT ?", (aid, r["studio"], limit), "同厂牌")
    c.close()
    for d in picked:
        d["cost"] = COST.get(d["location"], "metered")
        d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
        d.pop("snapshot_path", None)
    return {"items": picked[:limit]}

def q_tops(contract: WebContract, n=28):
    """顶部三层用的数据：女优圆头像 / 厂牌 / 内容标签。

    头像不额外造图 —— 取该创作者一张有接触印相的代表作，
    前端用 background-position:50% 50% 裁中心格做圆头像。"""
    c = contract.db()
    def rep(field, val):
        r = c.execute(f"SELECT id FROM asset WHERE medium='video' AND {field}=? "
                      "AND snapshot_path IS NOT NULL "
                      "ORDER BY (play_count IS NULL), size DESC LIMIT 1", (val,)).fetchone()
        return r[0] if r else None
    out = {}
    out["performers"] = []
    for k, cnt in c.execute(
            "SELECT creator, count(*) n FROM asset WHERE medium='video' "
            "AND creator IS NOT NULL AND creator<>'' GROUP BY creator ORDER BY n DESC LIMIT ?", (n,)):
        out["performers"].append({"k": k, "n": cnt, "rep": rep("creator", k)})
    out["studios"] = []
    for k, cnt in c.execute(
            "SELECT studio, count(*) n FROM asset WHERE medium='video' "
            "AND studio IS NOT NULL AND studio<>'' GROUP BY studio ORDER BY n DESC LIMIT ?", (n,)):
        out["studios"].append({"k": k, "n": cnt, "rep": rep("studio", k)})
    c.close()
    return out

def q_index(contract: WebContract, kind, q="", limit=600):
    """全部创作者 / 全部标签的索引页数据。"""
    c = contract.db()
    if kind == "creators":
        sql = ("SELECT creator k, count(*) n FROM asset WHERE medium='video' "
               "AND creator IS NOT NULL AND creator<>'' ")
        par = []
        if q: sql += "AND creator LIKE ? "; par.append(f"%{q}%")
        sql += "GROUP BY creator ORDER BY n DESC LIMIT ?"; par.append(limit)
        rows = [dict(r) for r in c.execute(sql, par)]
        for r in rows:
            g = c.execute("SELECT id FROM asset WHERE medium='video' AND creator=? "
                          "AND snapshot_path IS NOT NULL ORDER BY size DESC LIMIT 1",
                          (r["k"],)).fetchone()
            r["rep"] = g[0] if g else None
    else:
        sql = ("SELECT t.tag k, count(*) n FROM asset_tag t JOIN asset a ON a.id=t.asset_id "
               "WHERE a.medium='video' ")
        par = []
        if q: sql += "AND t.tag LIKE ? "; par.append(f"%{q}%")
        sql += "GROUP BY t.tag ORDER BY n DESC LIMIT ?"; par.append(limit)
        rows = [dict(r, cat=tag_cat(r["tag"] if "tag" in r.keys() else r["k"])) 
                for r in c.execute(sql, par)]
    c.close()
    return {"kind": kind, "items": rows}

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
        "creator": one("SELECT count(*) FROM asset WHERE medium='video' AND creator IS NOT NULL AND creator<>''"),
        "code": one("SELECT count(*) FROM asset WHERE medium='video' AND code IS NOT NULL AND code<>''"),
        "studio": one("SELECT count(*) FROM asset WHERE medium='video' AND studio IS NOT NULL AND studio<>''"),
        "thumb": one("SELECT count(*) FROM asset WHERE medium='video' AND snapshot_path IS NOT NULL"),
        "duration": one("SELECT count(*) FROM asset WHERE medium='video' AND duration IS NOT NULL"),
    }
    out["tag_source"] = [dict(r) for r in c.execute(
        "SELECT source k, count(*) n, count(DISTINCT asset_id) assets "
        "FROM asset_tag GROUP BY source ORDER BY n DESC")]
    out["tag_cov"] = one("SELECT count(DISTINCT asset_id) FROM asset_tag "
                         "WHERE source IN ('name','r18','vision','vision-creator')")
    out["top_tags"] = [dict(r, cat=tag_cat(r["k"])) for r in c.execute(
        "SELECT t.tag k, count(*) n FROM asset_tag t JOIN asset a ON a.id=t.asset_id "
        "WHERE a.medium='video' AND t.source IN ('name','r18','vision','vision-creator') "
        "GROUP BY t.tag ORDER BY n DESC LIMIT 30")]
    out["consumption"] = {
        "played": one("SELECT count(*) FROM asset WHERE play_count>0"),
        "play_seconds": one("SELECT COALESCE(sum(play_seconds),0) FROM asset"),
        "o_total": one("SELECT COALESCE(sum(o_count),0) FROM asset"),
        "dislike": one("SELECT count(*) FROM asset WHERE feedback='dislike'"),
        "seen": one("SELECT count(*) FROM asset WHERE feedback='seen'"),
        "pending": one("SELECT count(*) FROM asset WHERE disposal='pending'"),
        "skimmed": one("SELECT count(*) FROM asset WHERE duration>0 AND play_seconds>0 "
                       "AND max_reached>0.6 AND play_seconds/duration < max_reached-0.25"),
    }
    out["recent"] = [dict(r) for r in c.execute(
        "SELECT id,name,creator,play_seconds,duration,max_reached,leave_ratio,o_count "
        "FROM asset WHERE last_played IS NOT NULL ORDER BY last_played DESC LIMIT 12")]
    c.close()
    try:
        import shutil
        du = shutil.disk_usage("C:" + chr(92))
        out["disk_c"] = {"free": du.free, "total": du.total}
    except Exception:
        out["disk_c"] = None
    return out

def q_facets(contract: WebContract):
    c = contract.db()
    out = {}
    out["locations"] = [dict(r) for r in c.execute(
        "SELECT location AS k, count(*) AS n, "
        "SUM(CASE WHEN play_count>0 THEN 1 ELSE 0 END) AS played "
        "FROM asset WHERE medium='video' GROUP BY location ORDER BY n DESC")]
    out["creators"] = [dict(r) for r in c.execute(
        "SELECT creator AS k, count(*) AS n FROM asset WHERE medium='video' "
        "AND creator IS NOT NULL AND creator<>'' GROUP BY creator ORDER BY n DESC LIMIT 60")]
    # 标签要分层 —— 原来一锅端，结果「演员:一个ren」和「1080P」「足交」混在一起。
    # 三类分开：技术规格（画质/时长/画幅，筛选价值低）、内容维度（真正有用的）、演员（另立一栏）。
    TECH = ("1080P", "720P", "4K", "2160P", "480P", "低画质", "高帧率",
            "短片-2分内", "中片-10分内", "长片-30分内", "超长片", "横屏", "竖屏",
            "真人", "混合集", "身份待确认", "R-18")
    rows = [dict(r) for r in c.execute(
        "SELECT t.tag AS k, count(*) AS n FROM asset_tag t JOIN asset a ON a.id=t.asset_id "
        "WHERE a.medium='video' GROUP BY t.tag ORDER BY n DESC LIMIT 400")]
    out["tags"] = [dict(r, cat=tag_cat(r["k"])) for r in rows
                   if not r["k"].startswith("演员:") and r["k"] not in TECH][:44]
    out["tech"] = [r for r in rows if r["k"] in TECH][:14]
    out["tagperformers"] = [{"k": r["k"][3:], "n": r["n"]}
                            for r in rows if r["k"].startswith("演员:")][:20]
    st = c.execute(
        "SELECT count(*) total, COALESCE(sum(size),0) bytes, "
        "SUM(CASE WHEN play_count>0 THEN 1 ELSE 0 END) played, "
        "SUM(CASE WHEN feedback IS NOT NULL OR disposal IS NOT NULL THEN 1 ELSE 0 END) flagged, "
        "SUM(CASE WHEN creator IS NOT NULL AND creator<>'' THEN 1 ELSE 0 END) attributed "
        "FROM asset WHERE medium='video'").fetchone()
    out["stats"] = dict(st)
    c.close()
    return out

# ────────────────────────────── 写入 ──────────────────────────────

def w_activity(contract: WebContract, body):
    """播放埋点。

    「看完」不等于真看完 —— 快进扫过去也会到片尾。所以记两个互相独立的量：
      · play_seconds  真正播放过的秒数（前端只在 0<dt<2 时累加，拖动不计入）
      · max_reached   到达过的最远位置 / 时长
    两者一比就能分辨：max_reached 高但 play_seconds/duration 低 = 快进扫过，不是看完。
    另记 seek_count（拖动次数）作为佐证。"""
    aid = int(body["id"]); pos = float(body.get("position", 0))
    dur = float(body.get("duration", 0)); add = float(body.get("delta", 0))
    ended = bool(body.get("ended")); seeks = int(body.get("seeks", 0))
    with contract.write_lock:
        c = contract.db(write=True)
        row = c.execute("SELECT play_seconds,max_reached,seek_count FROM asset WHERE id=?",
                        (aid,)).fetchone()
        secs = (row["play_seconds"] or 0) + max(add, 0)
        ratio = 1.0 if ended else (min(pos / dur, 1.0) if dur > 0 else None)
        mx = max(row["max_reached"] or 0, ratio or 0)
        sk = (row["seek_count"] or 0) + max(seeks, 0)
        c.execute("UPDATE asset SET play_seconds=?, leave_ratio=COALESCE(?,leave_ratio), "
                  "max_reached=?, seek_count=?, last_played=? WHERE id=?",
                  (secs, ratio, mx, sk, time.time(), aid))
        c.commit(); c.close()
    real = (secs / dur) if dur > 0 else None
    return {"ok": True, "play_seconds": secs, "leave_ratio": ratio,
            "max_reached": mx, "seek_count": sk, "real_ratio": real}

def w_play(contract: WebContract, body):
    contract.cache_bust()
    aid = int(body["id"])
    with contract.write_lock:
        c = contract.db(write=True)
        c.execute("UPDATE asset SET play_count=COALESCE(play_count,0)+1, last_played=? "
                  "WHERE id=?", (time.time(), aid))
        c.commit(); c.close()
    return {"ok": True}

def w_feedback(contract: WebContract, body):
    contract.cache_bust()
    """四级反馈，前三级只打标记（见方案 §5.4）。第四级删除不在本服务里。"""
    aid = int(body["id"]); kind = body.get("kind")
    with contract.write_lock:
        c = contract.db(write=True)
        if kind in ("dislike", "seen"):
            cur = c.execute("SELECT feedback FROM asset WHERE id=?", (aid,)).fetchone()["feedback"]
            c.execute("UPDATE asset SET feedback=?, feedback_at=? WHERE id=?",
                      (None if cur == kind else kind, time.time(), aid))
        elif kind == "dispose":
            cur = c.execute("SELECT disposal FROM asset WHERE id=?", (aid,)).fetchone()["disposal"]
            c.execute("UPDATE asset SET disposal=?, feedback_at=? WHERE id=?",
                      (None if cur == "pending" else "pending", time.time(), aid))
        elif kind == "o":
            c.execute("UPDATE asset SET o_count=COALESCE(o_count,0)+1 WHERE id=?", (aid,))
        elif kind == "rate":
            c.execute("UPDATE asset SET rating=? WHERE id=?", (int(body.get("value", 0)), aid))
        c.commit()
        r = dict(c.execute("SELECT feedback,disposal,rating,o_count FROM asset WHERE id=?",
                           (aid,)).fetchone())
        c.close()
    return {"ok": True, **r}


def dispatch_api_get(contract: WebContract, path, args):
    """Dispatch the stable JSON read contract used by the current web client."""
    if path == "/api/items":
        return q_items(contract, args)
    if path == "/api/item":
        return q_item(contract, int(args["id"]))
    if path == "/api/index":
        return q_index(contract, args.get("kind", "tags"), args.get("q", ""))
    if path == "/api/stats":
        return contract.cached("stats", lambda: q_stats(contract))
    if path == "/api/tops":
        n = min(int(args.get("n", "28")), 60)
        return contract.cached(f"tops{n}", lambda: q_tops(contract, n))
    if path == "/api/ads":
        return q_ads(contract, min(int(args.get("limit", "200")), 400))
    if path == "/api/related":
        return q_related(contract, int(args["id"]), min(int(args.get("limit", "24")), 60))
    if path == "/api/facets":
        return contract.cached("facets", lambda: q_facets(contract))
    raise KeyError(path)


def dispatch_api_post(contract: WebContract, path, body):
    if path == "/api/activity":
        return w_activity(contract, body)
    if path == "/api/play":
        return w_play(contract, body)
    if path == "/api/feedback":
        return w_feedback(contract, body)
    raise KeyError(path)
