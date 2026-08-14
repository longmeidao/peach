#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
资源账本 —— 统一索引本地 / 115 / PikPak / 在线四处资源。

  python rm-ledger.py init                     建库
  python rm-ledger.py scan 115 B:\             扫一个挂载点（只读元数据）
  python rm-ledger.py scan pikpak A:\
  python scripts/ledger.py scan local R:\media\创作者
  python rm-ledger.py stash                    从 Stash 拉场景/标签/Studio/Performer
  python rm-ledger.py follow                   导入 X / Pixiv 关注列表（在线资产）
  python rm-ledger.py stats                    统计
  python rm-ledger.py dup [--min-mb 20]        按 hash / 名+大小 找重复

设计边界见项目根目录 docs/ARCHITECTURE.md 与 docs/adr/。
默认本地自托管。扫描只读元数据；在线关注同步是正式能力，按来源单独控频和授权。
"""
import os, sys, csv, json, sqlite3, time

from peach.stash import StashClient, StashError

DB = os.path.expandvars(r"R:\peach-data\database\ledger.db")
VIDEO = {".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".mov", ".ts", ".flv", ".rmvb", ".mpg", ".m2ts"}
IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
AUDIO = {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".opus"}
ARCHIVE = {".zip", ".rar", ".7z", ".tar", ".gz"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS source(
  id INTEGER PRIMARY KEY, batch_id TEXT, url TEXT, url_norm TEXT UNIQUE,
  title TEXT, password TEXT, platform TEXT, note TEXT,
  registered_at TEXT, status TEXT);

CREATE TABLE IF NOT EXISTS asset(
  id INTEGER PRIMARY KEY,
  location TEXT NOT NULL,          -- local / 115 / pikpak / online
  path TEXT NOT NULL,              -- 文件路径，或在线资源的 URL
  name TEXT, medium TEXT,          -- video/image/audio/archive/game/illustration/account
  size INTEGER, mtime TEXT,
  hash_kind TEXT, hash TEXT,
  creator TEXT, studio TEXT, series TEXT, code TEXT,
  duration REAL, width INTEGER, height INTEGER, vcodec TEXT, fps REAL, has_audio INTEGER,
  ctx_length TEXT, ctx_orient TEXT, ctx_quality TEXT, ctx_pace TEXT, ctx_people TEXT,
  play_count INTEGER DEFAULT 0, last_played TEXT, rating INTEGER, o_count INTEGER, watch_ratio REAL,
  source_id INTEGER, stash_scene_id INTEGER, snapshot_path TEXT,
  first_seen TEXT, last_seen TEXT,
  feedback TEXT, disposal TEXT, leave_ratio REAL, play_seconds REAL,
  feedback_at REAL, seek_count INTEGER, max_reached REAL,
  UNIQUE(location, path));

CREATE TABLE IF NOT EXISTS asset_tag(
  asset_id INTEGER, tag TEXT, confidence REAL DEFAULT 1.0, source TEXT,
  UNIQUE(asset_id, tag));

CREATE TABLE IF NOT EXISTS quest(
  id INTEGER PRIMARY KEY, keyword TEXT, origin TEXT,
  created_at TEXT, resolved_at TEXT, outcome TEXT);

CREATE TABLE IF NOT EXISTS media_binding(
  asset_id INTEGER NOT NULL REFERENCES asset(id),
  backend TEXT NOT NULL,
  external_id TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 100,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  last_synced_at TEXT,
  PRIMARY KEY(asset_id, backend),
  UNIQUE(backend, external_id));

CREATE INDEX IF NOT EXISTS ix_asset_hash ON asset(hash_kind, hash);
CREATE INDEX IF NOT EXISTS ix_asset_size ON asset(size);
CREATE INDEX IF NOT EXISTS ix_asset_loc  ON asset(location);
CREATE INDEX IF NOT EXISTS ix_asset_name ON asset(name);
CREATE INDEX IF NOT EXISTS ix_tag        ON asset_tag(tag);
"""


def conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("PRAGMA journal_mode=WAL")
    return c


def medium_of(name):
    e = os.path.splitext(name)[1].lower()
    if e in VIDEO: return "video"
    if e in IMAGE: return "image"
    if e in AUDIO: return "audio"
    if e in ARCHIVE: return "archive"
    return "other"


def ctx_from(size, w=None, h=None, dur=None):
    orient = quality = length = None
    if w and h:
        orient = "竖屏" if h > w else "横屏"
        m = max(w, h)
        quality = "4K" if m >= 3000 else "2K" if m >= 1900 else "1080P" if m >= 1300 else "720P" if m >= 900 else "低画质"
    if dur:
        length = "速食" if dur < 300 else "短" if dur < 900 else "中" if dur < 2400 else "长"
    return length, orient, quality


def cmd_init():
    c = conn(); c.executescript(SCHEMA); c.commit(); c.close()
    print(f"✓ 建库完成 {DB}")


def cmd_scan(location, root):
    c = conn(); c.executescript(SCHEMA)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.time(); n = 0; tot = 0
    batch = []
    for dp, dn, fns in os.walk(root, onerror=lambda e: None):
        for f in fns:
            p = os.path.join(dp, f)
            try:
                st = os.stat(p)
                sz, mt = st.st_size, time.strftime("%Y-%m-%d", time.localtime(st.st_mtime))
            except OSError:
                continue
            batch.append((location, p, f, medium_of(f), sz, mt, now, now))
            n += 1; tot += sz
            if len(batch) >= 2000:
                c.executemany("""INSERT INTO asset(location,path,name,medium,size,mtime,first_seen,last_seen)
                                 VALUES(?,?,?,?,?,?,?,?)
                                 ON CONFLICT(location,path) DO UPDATE SET
                                   size=excluded.size, mtime=excluded.mtime, last_seen=excluded.last_seen""", batch)
                c.commit(); batch.clear()
                print(f"  {time.time()-t0:5.0f}s  {n:,} 文件  {tot/1024**4:.2f} TB", flush=True)
    if batch:
        c.executemany("""INSERT INTO asset(location,path,name,medium,size,mtime,first_seen,last_seen)
                         VALUES(?,?,?,?,?,?,?,?)
                         ON CONFLICT(location,path) DO UPDATE SET
                           size=excluded.size, mtime=excluded.mtime, last_seen=excluded.last_seen""", batch)
    # 标记本次没扫到的（= 已删除）
    c.execute("UPDATE asset SET last_seen=last_seen WHERE location=?", (location,))
    c.commit()
    gone = c.execute("SELECT COUNT(*) FROM asset WHERE location=? AND last_seen<?", (location, now)).fetchone()[0]
    print(f"✓ {location}: {n:,} 文件 / {tot/1024**4:.2f} TB / 耗时 {time.time()-t0:.0f}s；清单中已消失 {gone:,} 个")
    c.close()


def cmd_stash(client=None):
    c = conn(); c.executescript(SCHEMA)
    client = client or StashClient(timeout=120)
    try:
        d = client.graphql("""{findScenes(filter:{per_page:-1}){scenes{
            id title rating100 o_counter play_count
            files{path size duration width height video_codec frame_rate audio_codec}
            studio{name} performers{name} tags{name}}}}""")
    except StashError as exc:
        print("Stash 错误:", exc)
        c.close()
        return
    if not d:
        c.close()
        return
    scenes = d["findScenes"]["scenes"]
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    nt = 0
    for s in scenes:
        if not s.get("files"): continue
        f = s["files"][0]
        dur = float(f.get("duration") or 0); w = int(f.get("width") or 0); h = int(f.get("height") or 0)
        L, O, Q = ctx_from(f.get("size"), w, h, dur)
        c.execute("""INSERT INTO asset(location,path,name,medium,size,duration,width,height,vcodec,fps,
                             has_audio,ctx_length,ctx_orient,ctx_quality,studio,
                             play_count,rating,o_count,stash_scene_id,first_seen,last_seen)
                           VALUES('local',?,?,'video',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(location,path) DO UPDATE SET
                             duration=excluded.duration,width=excluded.width,height=excluded.height,
                             vcodec=excluded.vcodec,fps=excluded.fps,has_audio=excluded.has_audio,
                             ctx_length=excluded.ctx_length,ctx_orient=excluded.ctx_orient,
                             ctx_quality=excluded.ctx_quality,studio=excluded.studio,
                             play_count=excluded.play_count,rating=excluded.rating,o_count=excluded.o_count,
                             stash_scene_id=excluded.stash_scene_id,last_seen=excluded.last_seen""",
                        (f["path"], os.path.basename(f["path"]), f.get("size"), dur, w, h,
                         f.get("video_codec"), f.get("frame_rate"),
                         1 if f.get("audio_codec") else 0, L, O, Q,
                         (s.get("studio") or {}).get("name"),
                         s.get("play_count") or 0, s.get("rating100"), s.get("o_counter") or 0,
                         int(s["id"]), now, now))
        aid = c.execute("SELECT id FROM asset WHERE location='local' AND path=?", (f["path"],)).fetchone()[0]
        provenance = {
            "transport": "stash-graphql",
            "studio": (s.get("studio") or {}).get("name"),
            "performers": [p["name"] for p in s.get("performers") or []],
            "tags": [t["name"] for t in s.get("tags") or []],
        }
        c.execute("""INSERT INTO media_binding(asset_id,backend,external_id,metadata_json,last_synced_at)
                     VALUES(?,'stash',?,?,?)
                     ON CONFLICT(asset_id,backend) DO UPDATE SET
                       external_id=excluded.external_id,
                       metadata_json=excluded.metadata_json,
                       last_synced_at=excluded.last_synced_at""",
                  (aid, str(s["id"]), json.dumps(provenance, ensure_ascii=False), now))
        for t in s.get("tags") or []:
            c.execute("""INSERT INTO asset_tag(asset_id,tag,confidence,source)
                         VALUES(?,?,1.0,'stash:tag')
                         ON CONFLICT(asset_id,tag) DO UPDATE SET
                           confidence=excluded.confidence,source=excluded.source""",
                      (aid, t["name"])); nt += 1
        for p in s.get("performers") or []:
            c.execute("""INSERT INTO asset_tag(asset_id,tag,confidence,source)
                         VALUES(?,?,1.0,'stash:performer')
                         ON CONFLICT(asset_id,tag) DO UPDATE SET
                           confidence=excluded.confidence,source=excluded.source""",
                      (aid, "演员:" + p["name"]))
    c.commit()
    print(f"✓ Stash: {len(scenes):,} 个场景，{nt:,} 条标签关联")
    c.close()


def cmd_follow():
    """把 X / Pixiv 关注列表作为 online 资产登记（作者级，不到单件作品）。"""
    c = conn(); c.executescript(SCHEMA)
    dl = os.path.expandvars(r"%USERPROFILE%\Downloads")
    now = time.strftime("%Y-%m-%d %H:%M:%S"); n = 0
    px = os.path.join(dl, "pixiv-following.json")
    if os.path.exists(px):
        for u in json.load(open(px, encoding="utf-8")):
            c.execute("""INSERT OR IGNORE INTO asset(location,path,name,medium,creator,first_seen,last_seen)
                         VALUES('online',?,?,'illustration',?,?,?)""",
                      (u.get("homepage"), u.get("name"), u.get("name"), now, now)); n += 1
            aid = c.execute("SELECT id FROM asset WHERE location='online' AND path=?", (u.get("homepage"),)).fetchone()
            if aid:
                c.execute("INSERT OR IGNORE INTO asset_tag(asset_id,tag,source) VALUES(?,'来源:Pixiv','follow')", (aid[0],))
                for wk in (u.get("recentWorks") or []):
                    for t in (wk.get("tags") or [])[:8]:
                        c.execute("INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,0.6,'pixiv_tag')", (aid[0], t))
    xf = os.path.join(dl, "x-following.json")
    if os.path.exists(xf):
        for a in json.load(open(xf, encoding="utf-8")):
            c.execute("""INSERT OR IGNORE INTO asset(location,path,name,medium,creator,first_seen,last_seen)
                         VALUES('online',?,?,'account',?,?,?)""",
                      (a.get("url"), a.get("name"), a.get("handle"), now, now)); n += 1
            aid = c.execute("SELECT id FROM asset WHERE location='online' AND path=?", (a.get("url"),)).fetchone()
            if aid:
                c.execute("INSERT OR IGNORE INTO asset_tag(asset_id,tag,source) VALUES(?,'来源:X','follow')", (aid[0],))
    c.commit(); print(f"✓ 在线关注: {n:,} 条")
    c.close()


def cmd_stats():
    c = conn(); c.executescript(SCHEMA)
    q = lambda s, *a: c.execute(s, a).fetchall()
    print("=== 账本统计 ===")
    for loc, n, sz in q("SELECT location,COUNT(*),COALESCE(SUM(size),0) FROM asset GROUP BY location ORDER BY 3 DESC"):
        print(f"  {loc:<10}{n:>9,} 条   {sz/1024**4:>8.2f} TB")
    print("\n  按媒介：")
    for m, n, sz in q("SELECT medium,COUNT(*),COALESCE(SUM(size),0) FROM asset GROUP BY medium ORDER BY 2 DESC"):
        print(f"    {m or '?':<14}{n:>9,}   {sz/1024**3:>10.1f} GB")
    r = q("SELECT COUNT(*) FROM asset_tag")[0][0]
    print(f"\n  标签关联 {r:,} 条 / 不同标签 {q('SELECT COUNT(DISTINCT tag) FROM asset_tag')[0][0]:,}")
    print(f"  有时长的 {q('SELECT COUNT(*) FROM asset WHERE duration>0')[0][0]:,}")
    print(f"  有消费记录的 {q('SELECT COUNT(*) FROM asset WHERE play_count>0 OR o_count>0 OR rating IS NOT NULL')[0][0]:,}")
    print("\n  情境层覆盖：")
    for col in ("ctx_length", "ctx_orient", "ctx_quality"):
        rows = q(f"SELECT {col},COUNT(*) FROM asset WHERE {col} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
        print(f"    {col}: " + "  ".join(f"{k}={v:,}" for k, v in rows))
    c.close()


def cmd_dup(min_mb=20):
    c = conn(); lim = min_mb * 1024 * 1024
    print(f"=== 重复检测（>{min_mb} MB）===")
    rows = c.execute("""SELECT hash_kind,hash,COUNT(*),SUM(size) FROM asset
                        WHERE hash IS NOT NULL AND size>? GROUP BY 1,2 HAVING COUNT(*)>1""", (lim,)).fetchall()
    print(f"  按哈希: {len(rows)} 组，可回收 {sum(s-s/n for _,_,n,s in rows)/1024**3:.1f} GB" if rows
          else "  按哈希: 0 组（尚未灌入 SHA1/gcid，见方案 §四）")
    rows = c.execute("""SELECT name,size,COUNT(*) FROM asset WHERE size>? GROUP BY name,size HAVING COUNT(*)>1
                        ORDER BY size*(COUNT(*)-1) DESC LIMIT 30""", (lim,)).fetchall()
    tot = c.execute("""SELECT COALESCE(SUM(size*(c-1)),0) FROM
                       (SELECT size,COUNT(*) c FROM asset WHERE size>? GROUP BY name,size HAVING COUNT(*)>1)""", (lim,)).fetchone()[0]
    print(f"  按名+大小: 可回收 {tot/1024**3:.1f} GB，前 30 组：")
    for nm, sz, n in rows:
        print(f"    {n}份 x {sz/1024**3:6.2f}G  {nm[:60]}")
    c.close()


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    cmd = a[0]
    if cmd == "init": cmd_init()
    elif cmd == "scan": cmd_scan(a[1], a[2])
    elif cmd == "stash": cmd_stash()
    elif cmd == "follow": cmd_follow()
    elif cmd == "stats": cmd_stats()
    elif cmd == "dup": cmd_dup(int(a[a.index("--min-mb")+1]) if "--min-mb" in a else 20)
    else: print(__doc__)
