#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按改名/移动日志迁移 ledger 里的 asset.path。

为什么必须做：ledger 的唯一键是 (location, path)，重扫时新路径会**插新行**，
旧行变孤儿 —— 我写在旧行上的 creator / code / studio / asset_tag（两万多条）就全丢了。
所以顺序是：先按日志改路径 → 再重扫（此时只会更新 size/mtime，不会造新行）。

吃两种日志:
  cleanname-*.log   OK<TAB>旧全路径<TAB>→<TAB>新文件名        （同目录改名）
  *reorg-*.log      OK<TAB>源<TAB>→<TAB>目标                  （目录或文件整体移动）

顺序敏感：净化在重组之前发生，所以必须先吃 cleanname 再吃 reorg。

用法: python rm-pathmigrate.py --loc 115 [--apply]
"""
import os, re, sys, glob, sqlite3

A = sys.argv[1:]
def _o(n, d=None): return A[A.index(n) + 1] if n in A else d
LOC = _o("--loc", "115")
APPLY = "--apply" in A
DB = r"R:\Resources\Intake\ledger.db"
LOGDIR = r"R:\Resources\Migration_Logs"

# 日志按 mtime 升序吃 —— 保证净化(先) → 重组(后) 的顺序
pats = {"115": ["cleanname-B-*.log", "115reorg-*.log"],
        "pikpak": ["cleanname-A-*.log", "pikpakreorg-*.log"],
        "local": ["cleanname-RMedia-*.log"]}[LOC]
logs = []
for p in pats:
    logs += glob.glob(os.path.join(LOGDIR, p))
logs.sort(key=os.path.getmtime)
if not logs:
    print("没有找到日志"); sys.exit(1)
print("将按顺序吃这些日志:")
for l in logs: print("  " + os.path.basename(l))

# 逐条构建映射；后一条日志的源要能接上前一条的结果，所以边走边应用
file_map = {}     # 精确路径映射
pref_map = []     # (旧前缀, 新前缀) —— 目录移动

def resolve(p):
    """把一个旧路径推到当前最新位置"""
    seen = 0
    while seen < 8:
        if p in file_map:
            p = file_map[p]; seen += 1; continue
        hit = False
        for old, new in pref_map:
            if p.lower().startswith(old.lower() + "\\"):
                p = new + p[len(old):]; hit = True; seen += 1; break
        if not hit:
            return p
    return p

n_rename = n_move = 0
for lg in logs:
    is_reorg = "reorg" in os.path.basename(lg)
    for line in open(lg, encoding="utf-8", errors="ignore"):
        if not line.startswith("OK\t"): continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4: continue
        src, dst = parts[1], parts[3]
        src = resolve(src)
        if is_reorg:
            pref_map.append((src, dst)); n_move += 1
        else:
            file_map[src] = os.path.join(os.path.dirname(src), dst); n_rename += 1

print(f"\n改名 {n_rename:,} 条，移动 {n_move:,} 条")

con = sqlite3.connect(DB); cur = con.cursor()
rows = cur.execute("SELECT id,path FROM asset WHERE location=?", (LOC,)).fetchall()
print(f"{LOC} 现有资产 {len(rows):,}")

updates, unchanged = [], 0
for aid, p in rows:
    np = resolve(p)
    if np != p: updates.append((np, aid))
    else: unchanged += 1
print(f"  需改路径 {len(updates):,}   不变 {unchanged:,}")

# 抽查
print("\n抽查 8 条:")
for np, aid in updates[:8]:
    old = dict((i, q) for i, q in rows)[aid]
    print(f"  {old[:74]}\n    → {np[:74]}")

# 冲突预检：改完之后有没有撞键
seen = {}
dup = 0
for np, aid in updates:
    k = np.lower()
    if k in seen: dup += 1
    seen[k] = aid
existing = {p.lower() for _, p in rows}
collide = sum(1 for np, aid in updates if np.lower() in existing and np.lower() not in
              {dict(((i, q) for i, q in rows))[aid].lower()})
print(f"\n新路径内部撞车 {dup}；与现有行撞车 {collide}")

if not APPLY:
    print("\n预演。确认后加 --apply 执行。")
    con.close(); sys.exit(0)

ok = err = 0
for np, aid in updates:
    try:
        cur.execute("UPDATE asset SET path=?, name=? WHERE id=?",
                    (np, os.path.basename(np), aid)); ok += 1
    except sqlite3.IntegrityError:
        err += 1        # 目标行已存在（撞键）→ 留着，重扫时按 last_seen 识别孤儿
con.commit()
print(f"已更新 {ok:,} 条，撞键跳过 {err}")
con.close()
print("\n下一步：python rm-ledger.py scan <loc> <drive>  （此时只会更新 size/mtime，不再造新行）")
