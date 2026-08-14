#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账本对账 —— 重组之后必须跑这个。

背景：重扫脚本是**追加**不是对账，改名+移动后 ledger 里同时存在
      旧路径的死行和新路径的新行（pikpak 一度从 5.3 万涨到 9.5 万条）。
      而且归属原本绑在旧路径上，新行是空的。

做两件事：
  1. 用一次 os.walk 拿到磁盘真相，删掉 ledger 里已不存在的行
  2. **从新目录结构反推归属** —— 重组后 B:\创作者\{人}\… 这个路径本身就是归属，
     比原来靠文件名猜可靠得多

用法: python rm-reconcile.py [--dry]
"""
import os, re, sys, sqlite3, time
from collections import Counter

DB = r"R:\Resources\Intake\ledger.db"
DRIVES = [("115", "B:\\"), ("pikpak", "A:\\")]
DRY = "--dry" in sys.argv or "--apply" not in sys.argv
PASSES = int(sys.argv[sys.argv.index("--passes")+1]) if "--passes" in sys.argv else 3

con = sqlite3.connect(DB)
cur = con.cursor()

for loc, drive in DRIVES:
    t0 = time.time()
    print(f"\n{'='*58}\n  {loc}  ({drive})\n{'='*58}")
    # ── 1. 磁盘真相 ──
    # ⚠️ PikPak 经 CloudDrive2/WebDAV 列目录**不确定**：同一子树连数三遍得到
    #    41,601 / 38,497 / 41,728，波动 ±3,100（约 8%），且是**漏**不是多。
    #    第一版基于单次遍历就删死行，误删了约 3,000 条本该存在的记录。
    #    所以：多遍取并集，且再对每个候选死行单独 stat 复核一次。
    passes = PASSES if loc != "115" else 1
    live = set()
    for k in range(passes):
        n = 0
        for dp, dns, fns in os.walk(drive):
            for f in fns:
                live.add(os.path.join(dp, f).lower())
                n += 1
        print(f"  第 {k+1}/{passes} 遍：本遍 {n:,} 个，并集累计 {len(live):,} 个"
              f"（{time.time()-t0:.0f}s）")

    rows = cur.execute("SELECT id,path FROM asset WHERE location=?", (loc,)).fetchall()
    cand = [(i, p) for i, p in rows if p.lower() not in live]
    # 单独 stat 复核 —— 列目录漏的条目，直接 stat 往往还在
    dead, resurrected = [], 0
    for i, p in cand:
        if os.path.exists(p):
            resurrected += 1
        else:
            dead.append(i)
    print(f"  ledger {len(rows):,} 行 → 列目录未见 {len(cand):,}，"
          f"其中 stat 复核仍在的 {resurrected:,}（列目录漏报）→ 真死行 {len(dead):,}")

    if not DRY and dead:
        for k in range(0, len(dead), 500):
            ch = dead[k:k+500]
            qm = ",".join("?" * len(ch))
            cur.execute(f"DELETE FROM asset_tag WHERE asset_id IN ({qm})", ch)
            cur.execute(f"DELETE FROM asset WHERE id IN ({qm})", ch)
        con.commit()
        print(f"  已删 {len(dead):,} 死行")

    # ── 2. 从新结构反推归属 ──
    rows = cur.execute("SELECT id,path FROM asset WHERE location=?", (loc,)).fetchall()
    upd = {"creator": [], "studio_code": []}
    hitc = Counter(); hits = Counter()
    for i, p in rows:
        rel = p[len(drive):] if p.lower().startswith(drive.lower()) else p
        parts = [x for x in rel.split("\\") if x]
        if len(parts) < 2:
            continue
        top = parts[0]
        if top == "创作者":
            upd["creator"].append((parts[1], i)); hitc[parts[1]] += 1
        elif top == "西方" and len(parts) >= 2:
            upd["studio_code"].append((parts[1], "", i)); hits[parts[1]] += 1
        elif top == "番号" and len(parts) >= 3:
            # B:\番号\{厂牌}\{番号}\…
            studio = "" if parts[1].startswith("_") else parts[1]
            upd["studio_code"].append((studio, parts[2], i)); hits[parts[1]] += 1

    print(f"  可从路径反推：创作者 {len(upd['creator']):,} 个资产（{len(hitc)} 位）；"
          f"厂牌/番号 {len(upd['studio_code']):,} 个资产（{len(hits)} 家）")
    for k, v in hitc.most_common(6):
        print(f"     {v:>6}  创作者 {k}")
    for k, v in hits.most_common(6):
        print(f"     {v:>6}  厂牌 {k}")

    if not DRY:
        cur.executemany("UPDATE asset SET creator=? WHERE id=?", upd["creator"])
        cur.executemany("UPDATE asset SET studio=NULLIF(?,''), code=NULLIF(?,'') WHERE id=?",
                        upd["studio_code"])
        con.commit()
        print("  已写回")

# ── 汇总 ──
print(f"\n{'='*58}\n  汇总\n{'='*58}")
for loc, _ in DRIVES:
    a = cur.execute("SELECT count(*),sum(size) FROM asset WHERE location=?", (loc,)).fetchone()
    v = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video'", (loc,)).fetchone()[0]
    vc = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video' "
                     "AND creator IS NOT NULL AND creator<>''", (loc,)).fetchone()[0]
    vk = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video' "
                     "AND code IS NOT NULL AND code<>''", (loc,)).fetchone()[0]
    print(f"  {loc:<8} {a[0]:>7,} 个资产 / {(a[1] or 0)/1024**4:>5.2f} TB   "
          f"视频 {v:,}，其中有创作者 {vc:,}、有番号 {vk:,}")
if DRY:
    print("\n以上为预演，加 --apply 执行")
con.close()
