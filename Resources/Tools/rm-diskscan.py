#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁盘占用扫描 —— **不跟随重解析点**（junction / symlink / 挂载点）。

为什么要专门写：用 PowerShell 的 Get-ChildItem -Recurse 量 C 盘，
两次都被污染 —— 一次报 CloudDrive.WinUI 有 8,508 GB（C 盘总共才 1.9 TB，
是遍历钻进了 B:\\ A:\\ 挂载点），一次报 0。
Windows 的 junction 用 os.path.islink() 也认不全，要看 FILE_ATTRIBUTE_REPARSE_POINT 位。

用法: python rm-diskscan.py [--root C:\\] [--top 30] [--depth 3] [--min 0.5]
"""
import os, sys, stat, time
from collections import defaultdict

A = sys.argv[1:]
def _o(n, d, c=str): return c(A[A.index(n) + 1]) if n in A else d
ROOT = _o("--root", "C:\\")
TOP = _o("--top", 30, int)
DEPTH = _o("--depth", 3, int)
MIN_GB = _o("--min", 0.5, float)

REPARSE = 0x400

def is_reparse(entry):
    try:
        return bool(entry.stat(follow_symlinks=False).st_file_attributes & REPARSE)
    except Exception:
        return False

sizes = defaultdict(int)      # 目录 → 自身及子树的字节（不含重解析点）
skipped = []
t0 = time.time()
nfiles = [0]

def walk(path, depth):
    total = 0
    try:
        with os.scandir(path) as it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if is_reparse(e):
                            skipped.append(e.path)
                            continue
                        total += walk(e.path, depth + 1)
                    elif e.is_file(follow_symlinks=False):
                        if is_reparse(e):
                            continue
                        total += e.stat(follow_symlinks=False).st_size
                        nfiles[0] += 1
                        if nfiles[0] % 200000 == 0:
                            print(f"  …已扫 {nfiles[0]:,} 个文件 ({time.time()-t0:.0f}s)",
                                  flush=True)
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        return 0
    if depth <= DEPTH:
        sizes[path] = total
    return total

print(f"扫描 {ROOT}（跳过挂载点/junction，深度 {DEPTH}）…")
grand = walk(ROOT, 0)
print(f"\n合计 {grand/1024**3:,.1f} GB / {nfiles[0]:,} 个文件，耗时 {time.time()-t0:.0f}s")
print(f"跳过的重解析点 {len(skipped)} 个" + (f"：{skipped[:6]}" if skipped else ""))

print(f"\n=== 占用最大的目录（≥{MIN_GB} GB，深度 ≤{DEPTH}）===")
rows = sorted(((v, k) for k, v in sizes.items() if v / 1024**3 >= MIN_GB), reverse=True)
seen_parent = []
shown = 0
for v, k in rows:
    # 父目录已经列过且占比 >85% 的子目录不再重复列，避免刷屏
    if any(k.startswith(p + os.sep) and v > pv * 0.85 for pv, p in seen_parent):
        continue
    print(f"  {v/1024**3:>9.2f} GB  {k}")
    seen_parent.append((v, k))
    shown += 1
    if shown >= TOP:
        break
