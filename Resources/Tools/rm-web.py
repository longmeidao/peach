#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网最小壳 —— 能播 + 埋点 + 反馈。

为什么这个要先做（见《项目进度总览》判断 #18/#19）：
  整套涌现推荐的燃料是消费数据，而消费数据只能从带埋点的播放器里来。
  Stash 里 2,551 个 scene 只有 5 个有播放记录 —— 反馈闭环是空的，
  且只要消费还发生在 PotPlayer / 双击文件，它就会永远是空的。

数据源是 ledger.db（唯一真相源），不是 Stash —— 因为 Stash 只索引了本地 2,552 个，
ledger 有全部 24,980 个（本地 + 115 + PikPak）。

边界：
  · 只绑局域网，带 token；Stash 仍只绑 127.0.0.1，本服务不碰它
  · 不上传任何东西到第三方，没有一个出网请求
  · 反馈只写 ledger 的列，可改可撤
  · **成本感知**：PikPak 是计费流量，界面显式标出，默认过滤掉

用法:
  python rm-web.py                      默认 0.0.0.0:8899
  python rm-web.py --port 8899 --token 自定义口令
"""
import os, re, sys, json, time, html, hmac, sqlite3, mimetypes, threading, subprocess, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie

DB = r"R:\Resources\Intake\ledger.db"
HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "rm-web.html")
SNAP_ROOT = r"R:\Resources\Intake\snapshots"
LOGO_ROOT = r"R:\Resources\Intake\logos"
AVA_ROOT = r"R:\Resources\Intake\avatars"
POSTER_ROOT = r"R:\Resources\Intake\posters"
FFPROBE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Stash", "ffmpeg-btbn",
                       "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffprobe.exe")
FFMPEG = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Stash", "ffmpeg-btbn",
                      "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")

A = sys.argv[1:]
def _o(n, d, c=str): return c(A[A.index(n) + 1]) if n in A else d
PORT = _o("--port", 80, int)
TOKEN = _o("--token", "")   # 空 = 不校验，局域网直接访问
MDNS_NAME = _o("--name", "peach")   # → peach.local
HOST = _o("--host", "0.0.0.0")

# 允许直接串流的根目录 —— 除此之外一律拒绝，防目录穿越
ALLOW_ROOTS = [r"R:\\", r"B:\\", r"A:\\"]
COST = {"local": "free", "115": "free", "pikpak": "metered", "online": "metered"}

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0B0B0D"/><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF9A76"/><stop offset="1" stop-color="#F2557B"/></linearGradient></defs><path d="M16 28c-5.7 0-9.7-3.6-9.7-8.6 0-4.3 2.8-7.6 6.5-7.6 1.4 0 2.4.5 3.2 1.1.8-.6 1.8-1.1 3.2-1.1 3.7 0 6.5 3.3 6.5 7.6C25.7 24.4 21.7 28 16 28z" fill="url(#pg)"/><path d="M16 13.4V27" stroke="#0B0B0D" stroke-width="1.1" opacity=".3" stroke-linecap="round"/><path d="M17.1 11.7c.6-2.8 2.8-4.6 5.6-4.8-.2 2.8-2.2 4.7-5.6 4.8z" fill="#5FB95F"/><path d="M16 11.9c0-1.9.5-3.4 1.5-4.5" stroke="#8A5A3B" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>')

_lock = threading.Lock()

# 聚合类查询（facets / tops / stats）是多个全表 GROUP BY，索引帮不上，
# 但它们的结果变化很慢 —— 缓存 90 秒，写入操作主动失效。
_CACHE, _CACHE_LOCK = {}, threading.Lock()
CACHE_TTL = 90
def cached(key, fn):
    now = time.time()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    val = fn()
    with _CACHE_LOCK:
        _CACHE[key] = (now, val)
    return val
def cache_bust():
    with _CACHE_LOCK:
        _CACHE.clear()

def db():
    c = sqlite3.connect(DB, timeout=30, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def ensure_columns():
    """反馈列 —— 幂等，已存在就跳过。"""
    c = db()
    have = {r[1] for r in c.execute("PRAGMA table_info(asset)")}
    for col, decl in (("feedback", "TEXT"),        # dislike / seen  （见方案 §5.4）
                      ("disposal", "TEXT"),        # pending 待删
                      ("leave_ratio", "REAL"),     # 离开位置 / 时长 —— 信息量最大的单个数字
                      ("play_seconds", "REAL"),    # 累计观看秒数
                      ("feedback_at", "REAL"),
                      ("seek_count", "INTEGER"),      # 拖动次数 —— 快进判断
                      ("max_reached", "REAL")):       # 到达过的最远位置比值
        if col not in have:
            c.execute(f"ALTER TABLE asset ADD COLUMN {col} {decl}")
    c.commit(); c.close()

def allowed(p):
    ap = os.path.abspath(p)
    return any(ap.upper().startswith(r.replace("\\\\", "\\").upper()) for r in ALLOW_ROOTS)

# ────────────────────────────── 查询 ──────────────────────────────

def q_items(args):
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
    c = db()
    rows = [dict(r) for r in c.execute(sql, par + [lim, off])]
    cnt = c.execute("SELECT count(*) FROM asset a WHERE " + " AND ".join(where), par).fetchone()[0]
    c.close()
    # 卡片要显示出镜者和高权重标签，不能只有番号 —— 一次批量取，别 N+1
    if rows:
        ids = [r["id"] for r in rows]
        qm = ",".join("?" * len(ids))
        tmap = {}
        for aid, tag in con_tags(ids, qm):
            tmap.setdefault(aid, []).append(tag)
        for r in rows:
            ts = tmap.get(r["id"], [])
            r["tags"] = [t for t in ts if tag_cat(t) in ("general", "character", "copyright")][:4]
            r["performers"] = [t[3:] for t in ts if t.startswith("演员:")][:3]
    for r in rows:
        r["cost"] = COST.get(r["location"], "metered")
        r["has_thumb"] = bool(r["snapshot_path"] and os.path.exists(r["snapshot_path"]))
        r.pop("snapshot_path", None)
        r.pop("path", None)                     # 路径不外发，串流走 id
    return {"total": cnt, "items": rows}

def con_tags(ids, qm):
    c = db()
    try:
        return c.execute(
            f"SELECT asset_id, tag FROM asset_tag WHERE asset_id IN ({qm})", ids).fetchall()
    finally:
        c.close()

def q_item(aid):
    """按 id 直取。
    ⚠️ 第一版没有这个接口，前端用「带筛选条件再查一遍然后 find」的绕法，
       limit 被覆盖成 1 → find 必然失败 → 走兜底 items[0]，
       于是**每次点击都打开同一个默认列表首项**（一个 12.6 GB 的 PikPak 文件），
       既显示错条目，又反复拉计费流量。教训：按 id 取就按 id 取。"""
    c = db()
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
    d["has_thumb"] = bool(d["snapshot_path"] and os.path.exists(d["snapshot_path"]))
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

def q_ads(limit=200):
    """疑似广告复核队列 —— **不自动删**，只排队让人看接触印相确认。

    没有可靠的单一判据（试过「同番号短版」会误伤 CD2/part1 分卷，
    试过「同名扩散」会误伤 001.mp4 这类通用名的真文件）。
    所以给的是**嫌疑分**，按分排序，人工看图定夺，确认的走既定 CSV 删除流程。"""
    c = db()
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
            d["has_thumb"] = bool(d["snapshot_path"] and os.path.exists(d["snapshot_path"]))
            d.pop("snapshot_path", None)
            out.append(d)
    c.close()
    out.sort(key=lambda x: (-x["score"], -(x["size"] or 0)))
    return {"total": len(out), "items": out[:limit]}

def q_related(aid, limit=24):
    """接着看 —— 把口味接近的串成播放列表。
    优先级：同创作者 > 共享标签最多 > 同厂牌。全部排除已标记不合口味的。"""
    c = db()
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
        d["has_thumb"] = bool(d["snapshot_path"] and os.path.exists(d["snapshot_path"]))
        d.pop("snapshot_path", None)
    return {"items": picked[:limit]}

def q_tops(n=28):
    """顶部三层用的数据：女优圆头像 / 厂牌 / 内容标签。

    头像不额外造图 —— 取该创作者一张有接触印相的代表作，
    前端用 background-position:50% 50% 裁中心格做圆头像。"""
    c = db()
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

def q_index(kind, q="", limit=600):
    """全部创作者 / 全部标签的索引页数据。"""
    c = db()
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

def q_stats():
    """统计页：库存 / 归属 / 标签 / 消费 / 磁盘。原来挤在顶栏右上角，信息量太小又碍眼。"""
    c = db()
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

def q_facets():
    c = db()
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

def w_activity(body):
    """播放埋点。

    「看完」不等于真看完 —— 快进扫过去也会到片尾。所以记两个互相独立的量：
      · play_seconds  真正播放过的秒数（前端只在 0<dt<2 时累加，拖动不计入）
      · max_reached   到达过的最远位置 / 时长
    两者一比就能分辨：max_reached 高但 play_seconds/duration 低 = 快进扫过，不是看完。
    另记 seek_count（拖动次数）作为佐证。"""
    aid = int(body["id"]); pos = float(body.get("position", 0))
    dur = float(body.get("duration", 0)); add = float(body.get("delta", 0))
    ended = bool(body.get("ended")); seeks = int(body.get("seeks", 0))
    with _lock:
        c = db()
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

def w_play(body):
    cache_bust()
    aid = int(body["id"])
    with _lock:
        c = db()
        c.execute("UPDATE asset SET play_count=COALESCE(play_count,0)+1, last_played=? "
                  "WHERE id=?", (time.time(), aid))
        c.commit(); c.close()
    return {"ok": True}

def w_feedback(body):
    cache_bust()
    """四级反馈，前三级只打标记（见方案 §5.4）。第四级删除不在本服务里。"""
    aid = int(body["id"]); kind = body.get("kind")
    with _lock:
        c = db()
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

# ────────────────────────────── HTTP ──────────────────────────────

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.close_connection = True

    def _auth(self, qs):
        if not TOKEN:                      # 没设口令就不校验
            return True
        supplied = qs.get("t", [None])[0]
        if supplied is not None and hmac.compare_digest(str(supplied), TOKEN):
            return True
        supplied = self.headers.get("X-Token")
        if supplied is not None and hmac.compare_digest(str(supplied), TOKEN):
            return True
        # Cookie 必须按字段解析；直接做子串匹配会把 notok=<口令>、
        # tok=<口令>extra 也误当成已登录。
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie") or "")
            supplied = cookie.get("tok").value if cookie.get("tok") else None
        except Exception:
            supplied = None
        return supplied is not None and hmac.compare_digest(str(supplied), TOKEN)

    def _send(self, code, body=b"", ctype="application/json; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # HTML 也必须 no-store —— 上一版给页面发了 max-age=86400，
        # 改完前端刷新还是旧版，白查半天
        cacheable = (ctype.startswith(("image/", "video/", "font/"))
                     and "svg" not in ctype)   # favicon 要能立刻更新
        self.send_header("Cache-Control", "max-age=86400" if cacheable else "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode())

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        p = u.path

        if p == "/":
            if not self._auth(qs):
                return self._send(401, "需要 ?t=口令".encode(), "text/plain; charset=utf-8")
            with open(PAGE, "rb") as f:
                body = f.read()
            extra = ({"Set-Cookie": f"tok={TOKEN}; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly"}
                     if TOKEN else None)
            return self._send(200, body, "text/html; charset=utf-8", extra)

        if p == "/favicon.svg":
            return self._send(200, FAVICON.encode(), "image/svg+xml")
        if not self._auth(qs):
            return self._json({"error": "unauthorized"}, 401)

        if p == "/api/items":
            return self._json(q_items({k: v[0] for k, v in qs.items()}))
        if p == "/api/item":
            return self._json(q_item(int(qs["id"][0])))
        if p == "/api/index":
            return self._json(q_index(qs.get("kind", ["tags"])[0], qs.get("q", [""])[0]))
        if p == "/api/stats":
            return self._json(cached("stats", q_stats))
        if p == "/api/tops":
            n = min(int(qs.get("n", ["28"])[0]), 60)
            return self._json(cached(f"tops{n}", lambda: q_tops(n)))
        if p == "/api/ads":
            return self._json(q_ads(min(int(qs.get("limit", ["200"])[0]), 400)))
        if p == "/api/related":
            return self._json(q_related(int(qs["id"][0]),
                                        min(int(qs.get("limit", ["24"])[0]), 60)))
        if p == "/api/facets":
            return self._json(cached("facets", q_facets))
        if p == "/favicon.svg":
            return self._send(200, FAVICON.encode(), "image/svg+xml")
        if p == "/poster":
            return self._poster(int(qs["id"][0]), int(qs.get("c", ["4"])[0]))
        if p == "/avatar":
            return self._avatar(int(qs["id"][0]))
        if p == "/logo":
            return self._logo(qs.get("studio", [""])[0])
        if p == "/thumb":
            return self._file_by_id(int(qs["id"][0]), thumb=True)
        if p == "/stream":
            return self._file_by_id(int(qs["id"][0]), thumb=False)
        return self._json({"error": "not found"}, 404)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if not self._auth(qs):
            return self._json({"error": "unauthorized"}, 401)
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json({"error": "bad json"}, 400)
        try:
            if u.path == "/api/activity":  return self._json(w_activity(body))
            if u.path == "/api/play":      return self._json(w_play(body))
            if u.path == "/api/feedback":  return self._json(w_feedback(body))
        except Exception as e:
            return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
        return self._json({"error": "not found"}, 404)

    def _avatar(self, aid):
        """头像：从接触印相里裁**最亮的那一格**。

        上一版固定裁中心格，遇到黑场就是个纯黑圆 —— 用户报的「还是有黑的」。
        现在按 [中心, 左上, 正中偏后, 右上, 左下] 顺序试，用 ffprobe 的 signalstats
        读平均亮度（YAVG），第一个够亮的就用；全都暗就用最亮的那个。裁完缓存。"""
        os.makedirs(AVA_ROOT, exist_ok=True)
        dst = os.path.join(AVA_ROOT, str(aid) + ".jpg")
        if not os.path.exists(dst):
            c = db()
            r = c.execute("SELECT snapshot_path FROM asset WHERE id=?", (aid,)).fetchone()
            c.close()
            src = r["snapshot_path"] if r else None
            if not src or not os.path.exists(src):
                return self._send(404, b"", "text/plain")
            best, best_y = None, -1.0
            for col, row in ((1, 1), (0, 0), (1, 2), (2, 0), (0, 2), (2, 2)):
                tmp = dst + f".{col}{row}.jpg"
                try:
                    subprocess.run(
                        [FFMPEG, "-y", "-v", "error", "-i", src,
                         "-vf", f"crop=iw/3:ih/3:iw/3*{col}:ih/3*{row},"
                                "scale=160:160:force_original_aspect_ratio=increase,crop=160:160",
                         "-q:v", "4", tmp], capture_output=True, timeout=25)
                    if not os.path.exists(tmp):
                        continue
                    # 把这一格缩成 1x1 灰度，读出那一个字节 = 平均亮度。
                    # 不用 ffprobe 的 movie= 滤镜 —— Windows 盘符里的冒号会被当成参数分隔符。
                    raw = subprocess.run(
                        [FFMPEG, "-v", "error", "-i", tmp, "-vf", "scale=1:1",
                         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                        capture_output=True, timeout=20).stdout
                    y = float(raw[0]) if raw else 0.0
                except Exception:
                    continue
                if y > best_y:
                    if best and os.path.exists(best):
                        try: os.remove(best)
                        except Exception: pass
                    best, best_y = tmp, y
                elif os.path.exists(tmp):
                    try: os.remove(tmp)
                    except Exception: pass
                if best_y >= 60:          # 够亮就不再试了
                    break
            if not best or best_y < 12:   # 全是黑场，别放一个黑圆上去
                if best and os.path.exists(best):
                    try: os.remove(best)
                    except Exception: pass
                return self._send(404, b"", "text/plain")
            try:
                os.replace(best, dst)
            except Exception:
                return self._send(404, b"", "text/plain")
        if not os.path.exists(dst):
            return self._send(404, b"", "text/plain")
        with open(dst, "rb") as f:
            return self._send(200, f.read(), "image/jpeg")

    def _poster(self, aid, cell):
        """预览图：从接触印相裁出**单独一格**，保持原始宽高比。

        前端框体固定 16:9，这张图用 object-fit:contain 放进去 —— 竖屏留黑边，
        既不拉伸也不把网格撑变形。上一版按素材比例改 tile 高度，竖屏直接把整行撑爆。"""
        cell = max(0, min(8, cell))
        col, row = cell % 3, cell // 3
        os.makedirs(POSTER_ROOT, exist_ok=True)
        dst = os.path.join(POSTER_ROOT, f"{aid}_{cell}.jpg")
        if not os.path.exists(dst):
            c = db()
            r = c.execute("SELECT snapshot_path FROM asset WHERE id=?", (aid,)).fetchone()
            c.close()
            src = r["snapshot_path"] if r else None
            if not src or not os.path.exists(src):
                return self._send(404, b"", "text/plain")
            try:
                subprocess.run(
                    [FFMPEG, "-y", "-v", "error", "-i", src,
                     "-vf", f"crop=iw/3:ih/3:iw/3*{col}:ih/3*{row},"
                            "scale='min(640,iw)':-2",
                     "-q:v", "4", dst], capture_output=True, timeout=25)
            except Exception:
                return self._send(404, b"", "text/plain")
        if not os.path.exists(dst):
            return self._send(404, b"", "text/plain")
        with open(dst, "rb") as f:
            return self._send(200, f.read(), "image/jpeg")

    def _logo(self, studio):
        """厂牌官网图标（已抓到本地，服务时不出网）。没有就 404，前端自动退回预览图裁切。"""
        if not studio:
            return self._send(404, b"", "text/plain")
        nm = re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]
        cand = [os.path.join(LOGO_ROOT, nm + ".img")]
        # 大小写不敏感兜底（库里 Faleno / FALENO 都有）
        try:
            low = nm.lower()
            for f in os.listdir(LOGO_ROOT):
                if f.lower() == low + ".img":
                    cand.append(os.path.join(LOGO_ROOT, f))
        except Exception:
            pass
        for path in cand:
            if os.path.exists(path):
                ct = "image/x-icon"
                try:
                    ct = open(path + ".ct", encoding="utf-8").read().strip() or ct
                except Exception:
                    pass
                with open(path, "rb") as f:
                    return self._send(200, f.read(), ct.split(";")[0])
        return self._send(404, b"", "text/plain")

    # ── 按 id 取文件；路径不出网，且限制在白名单根目录内 ──
    def _file_by_id(self, aid, thumb):
        c = db()
        r = c.execute("SELECT path,snapshot_path FROM asset WHERE id=?", (aid,)).fetchone()
        c.close()
        if not r:
            return self._json({"error": "no such id"}, 404)
        path = r["snapshot_path"] if thumb else r["path"]
        if not path or not allowed(path) or not os.path.exists(path):
            return self._json({"error": "unavailable"}, 404)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        size = os.path.getsize(path)
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            if m:
                if m.group(1): start = int(m.group(1))
                if m.group(2): end = int(m.group(2))
                end = min(end, size - 1)
        length = max(end - start + 1, 0)
        code = 206 if rng else 200
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "max-age=86400" if thumb else "no-store")
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = length
                while left > 0:
                    chunk = f.read(min(262144, left))
                    if not chunk: break
                    self.wfile.write(chunk); left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass          # 播放器 seek / 关标签页会中断流，属正常，不刷栈


# ── mDNS：发布 peach.local，全设备免配置访问 ────────────────────
# Mac / iOS / iPadOS 原生支持 .local；Windows 10+ 内置；Android 部分版本支持。
# 名字、访问口令、域名三者统一：Peach / peach / peach.local
_zc = None
def publish_mdns(ip, port, name):
    """注册 A 记录 name.local → ip。失败不影响服务本身。"""
    global _zc
    try:
        from zeroconf import Zeroconf, ServiceInfo
        import socket as _s
        _zc = Zeroconf()
        info = ServiceInfo(
            "_http._tcp.local.",
            f"{name}._http._tcp.local.",
            addresses=[_s.inet_aton(ip)],
            port=port,
            properties={"path": "/"},
            server=f"{name}.local.",
        )
        _zc.register_service(info, allow_name_change=True)
        return True
    except Exception as e:
        print(f"  （mDNS 发布失败，不影响用 IP 访问：{type(e).__name__}: {e}）")
        return False

def lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("223.5.5.5", 80)); return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

if __name__ == "__main__":
    ensure_columns()
    srv = None
    for port in ([PORT] + ([8899] if PORT != 8899 else [])):
        try:
            srv = ThreadingHTTPServer((HOST, port), H)
            PORT = port
            break
        except OSError as e:
            print(f"  端口 {port} 绑定失败（{e}），换下一个")
    if srv is None:
        raise SystemExit("没有可用端口")

    ip = lan_ip()
    ok = publish_mdns(ip, PORT, MDNS_NAME)
    suffix = "" if PORT == 80 else f":{PORT}"
    q = f"?t={TOKEN}" if TOKEN else ""
    print("Peach · 蜜桃  已启动")
    if ok:
        print(f"  域名   http://{MDNS_NAME}.local{suffix}/{q}   ← 手机/平板/Mac 直接用这个")
    print(f"  局域网 http://{ip}{suffix}/{q}")
    print(f"  本机   http://127.0.0.1{suffix}/{q}")
    print(f"  账本   {DB}")
    print("  Ctrl+C 停止")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        if _zc:
            try:
                _zc.unregister_all_services(); _zc.close()
            except Exception:
                pass
