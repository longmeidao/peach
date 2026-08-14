#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
115 SHA1 灌入 —— 用 p115client 拉全量文件清单（含服务端算好的 SHA1）写进 ledger。

为什么需要：现在账本的重复只能靠「文件名+大小」判断，改过名的重复抓不到。
            115 的秒传基于文件 SHA1，服务端早算好了，列目录接口直接返回，零下载成本。
            灌进来之后不管文件叫什么名字，同 SHA1 就是同一个文件。

前置（只需做一次）：
    pip install -U p115client
    然后首次运行会要求登录：本脚本用扫码登录，不需要你把密码给任何人。
    cookie 存在 %USERPROFILE%\\.115-cookies.txt，仅本机。

用法：
    python scripts/sync_sha1_115.py                 # 拉取并写入 ledger
    python scripts/sync_sha1_115.py --dupes         # 写入后直接出 SHA1 重复报告
"""
import os, sys, json, sqlite3, time
from collections import defaultdict

DB = r"R:\Resources\Intake\ledger.db"
COOKIE = os.path.expandvars(r"%USERPROFILE%\.115-cookies.txt")
LOG = r"R:\Resources\Migration_Logs\sha1-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))

try:
    from p115client import P115Client
    from p115client.tool.iterdir import iter_files
except ImportError:
    print("缺少依赖，先执行：")
    print(r'   "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m pip install -U p115client')
    sys.exit(1)

logf = open(LOG, "w", encoding="utf-8", buffering=1)
def log(s):
    print(s, flush=True); logf.write(s + "\n")

# ---------- 登录 ----------
if os.path.exists(COOKIE):
    client = P115Client(COOKIE)
    log(f"用已保存的 cookie 登录: {COOKIE}")
else:
    log("首次运行，需要扫码登录（用 115 手机 App 扫终端里的二维码）")
    client = P115Client(console_qrcode=True)
    open(COOKIE, "w", encoding="utf-8").write(client.cookies_str)
    log(f"cookie 已保存到 {COOKIE}（仅本机，勿外传）")

# ---------- 拉全量清单 ----------
log("开始拉取全量文件清单（只读元数据，不下载任何文件内容）…")
rows = []
t0 = time.time()
for i, f in enumerate(iter_files(client, 0, type=99, with_path=True), 1):
    sha = f.get("sha1") or f.get("sha")
    if not sha:
        continue
    rows.append((sha, f.get("path") or "", f.get("name") or "", int(f.get("size") or 0)))
    if i % 5000 == 0:
        log(f"  {i:,} 条  {time.time()-t0:.0f}s")
log(f"共 {len(rows):,} 条带 SHA1 的文件，耗时 {time.time()-t0:.0f}s")

# ---------- 写入 ledger ----------
# 115 的 path 是 /开头的云端路径；ledger 里存的是挂载后的 B:\ 路径。按 (文件名, 大小) 对齐。
conn = sqlite3.connect(DB, timeout=120)
have = defaultdict(list)
for aid, name, size in conn.execute(
        "SELECT id,name,size FROM asset WHERE location='115'"):
    have[(name, size)].append(aid)
log(f"账本里 115 的记录 {sum(len(v) for v in have.values()):,} 条")

upd, miss = [], 0
for sha, path, name, size in rows:
    ids = have.get((name, size))
    if ids:
        for aid in ids:
            upd.append(("sha1", sha, aid))
    else:
        miss += 1
conn.executemany("UPDATE asset SET hash_kind=?, hash=? WHERE id=?", upd)
conn.commit()
log(f"已写入 SHA1 {len(upd):,} 条；云端有但账本没匹配上的 {miss:,} 条（多为已删或路径不同）")

# ---------- 重复报告 ----------
if "--dupes" in sys.argv:
    OUT = os.path.expandvars(r"%USERPROFILE%\Desktop\115-sha1重复.csv")
    import csv
    g = defaultdict(list)
    for aid, p, s, h in conn.execute(
            "SELECT id,path,size,hash FROM asset WHERE location='115' AND hash IS NOT NULL"):
        g[h].append((aid, p, s))
    dup = {h: v for h, v in g.items() if len(v) > 1}
    waste = sum(v[0][2] * (len(v) - 1) for v in dup.values())
    log(f"SHA1 精确重复: {len(dup):,} 组，可回收 {waste/1024**3:.1f} GB")
    def score(p):
        s = 0
        if "\\云下载" in p: s -= 50
        if "auto_create@" in p.lower(): s -= 40
        s -= p.count("\\") * 2
        return s
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["组号", "动作", "大小GB", "路径", "SHA1"])
        for i, (h, items) in enumerate(
                sorted(dup.items(), key=lambda kv: -kv[1][0][2] * (len(kv[1]) - 1)), 1):
            items = sorted(items, key=lambda x: -score(x[1]))
            for j, (aid, p, s) in enumerate(items):
                w.writerow([i, "保留" if j == 0 else "删除", round(s / 1024**3, 3), p, h])
    log(f"→ {OUT}")

conn.close(); logf.close()
