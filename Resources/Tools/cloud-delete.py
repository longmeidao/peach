#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 CSV 清单删除网盘文件。带路径白名单校验和完整日志。

用法: python cloud-delete.py <csv1> [csv2 ...] --root B:\\ [--dry]

安全规则（任一不满足就跳过并计入拒绝）：
  1. 路径必须以 --root 指定的盘符开头
  2. 路径必须真实存在且是文件（不删目录）
  3. CSV 里「动作」列必须是「删除」
"""
import csv, os, sys, datetime

args = [a for a in sys.argv[1:]]
DRY = "--dry" in args
if DRY:
    args.remove("--dry")
ROOT = "B:\\"
if "--root" in args:
    i = args.index("--root")
    ROOT = args[i + 1]
    del args[i:i + 2]
CSVS = args
if not CSVS:
    print("用法: python cloud-delete.py <csv...> [--root B:\\] [--dry]")
    raise SystemExit(1)

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG = rf"R:\Resources\Migration_Logs\cloud-delete-{stamp}.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)
log = open(LOG, "w", encoding="utf-8")


def w(s):
    print(s)
    log.write(s + "\n")
    log.flush()


w(f"=== 网盘删除 {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ===")
w(f"root={ROOT}   dry_run={DRY}")

grand_ok = grand_bytes = grand_skip = grand_fail = 0
for c in CSVS:
    if not os.path.exists(c):
        w(f"[跳过] 文件不存在: {c}")
        continue
    with open(c, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    todo = [r for r in rows if (r.get("动作") or "").strip() == "删除"]
    w(f"\n--- {os.path.basename(c)}: 清单 {len(rows)} 行，待删 {len(todo)} ---")
    ok = fail = skip = 0
    nbytes = 0
    for r in todo:
        p = (r.get("路径") or "").strip()
        if not p or not p.upper().startswith(ROOT.upper()):
            skip += 1
            w(f"  [拒绝-越界] {p}")
            continue
        if not os.path.isfile(p):
            skip += 1
            continue
        try:
            sz = os.path.getsize(p)
            if not DRY:
                os.remove(p)
            ok += 1
            nbytes += sz
            w(f"  DEL {sz:>12,}  {p}")
        except OSError as e:
            fail += 1
            w(f"  [失败] {p} :: {e}")
    w(f"  小计: 删除 {ok}  跳过 {skip}  失败 {fail}  回收 {nbytes/1024**3:.2f} GB")
    grand_ok += ok
    grand_bytes += nbytes
    grand_skip += skip
    grand_fail += fail

w(f"\n=== 合计: 删除 {grand_ok}  跳过 {grand_skip}  失败 {grand_fail}  回收 {grand_bytes/1024**3:.2f} GB ===")
w(f"日志: {LOG}")
log.close()
