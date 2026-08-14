#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名净化 —— 去掉盗版站塞进文件名的推广域名与残留噪声。

只做可逆、无歧义的改写。刻意不做的几件事（都验证过会出事）：
  * 不删 " (3)" 这类序号：库里 16278 条，去掉后 1520 条与同目录文件直接撞名，
    Telegram 导出全靠它区分同秒落地的文件。
  * 不动 "xxx.mp4.jpg"：那是该 mp4 的缩略图，不是双后缀（真的双后缀只有 2 条）。
  * 不重排番号/不套命名模板：那依赖刮削完整度，属于另一件事。

先出 CSV 供人工核对，加 --apply 才落盘；改名同时同步 ledger 的 path/name。

用法:
    python scripts/clean_names.py [--location local|115|pikpak] [--apply]
"""
from __future__ import annotations

import csv
import argparse
from datetime import datetime
import os
import re
import sqlite3
import time

DEFAULT_DB = r"R:\peach-data\database\ledger.db"
DEFAULT_OUT = r"R:\peach-data\generated\name-clean.csv"
DEFAULT_LOG_DIR = r"R:\peach-data\logs"
DEFAULT_BACKUP_DIR = r"R:\peach-data\archive"
_logf = None


def configure_log(log_dir: str) -> None:
    global _logf
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, time.strftime("clean-names-%Y%m%d-%H%M%S.log"))
    _logf = open(path, "w", encoding="utf-8", buffering=1)


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if _logf is not None:
        _logf.write(line + "\n")


TLD = r"(?:com|net|la|xyz|cc|me|top|vip|club|info|org|tv|app|co|pw|gg|cn)"
VIDEO_EXT = {"mp4", "mkv", "avi", "wmv", "mov", "ts", "m4v", "flv", "rmvb"}

# 站点前缀：域名后面常跟 @ - _ 空格，或直接连着广告语
RE_PREFIX = re.compile(
    rf"^\s*[\[\【@]?\s*(?:www\.)?[0-9A-Za-z][-0-9A-Za-z]{{1,30}}\.{TLD}"
    rf"(?:\d{{6,}})?\s*[@\-_\]\】、,，]?\s*", re.I)
# 尾部域名：紧贴扩展名之前
RE_SUFFIX = re.compile(
    rf"[-_@\s]+(?:www\.)?[0-9A-Za-z][-0-9A-Za-z]{{2,25}}\.{TLD}\s*(?=\.[A-Za-z0-9]{{2,4}}$)", re.I)
# 中文推广尾巴（域名已被上面吃掉后剩下的宣传语）
RE_ADCOPY = re.compile(
    r"[-_\s]*(?:全网最火爆成人游戏|成人手游|最新地址|开车地址|每日更新|无码破解|"
    r"免费看片|请记住本站|更多资源|中文成人网站?)[^.]*(?=\.[A-Za-z0-9]{2,4}$)")


def propose(name: str) -> str:
    """返回净化后的文件名；无需改动则原样返回。"""
    stem, dot, ext = name.rpartition(".")
    if not dot or not stem:           # 没有扩展名、或形如 ".mp4" 的空主干，都不碰
        return name

    new = RE_PREFIX.sub("", name, count=1)
    new = RE_SUFFIX.sub("", new)
    new = RE_ADCOPY.sub("", new)

    # 同类双后缀 .mp4.mp4（.mp4.jpg 这种缩略图命名不算）
    dbl = re.search(r"\.([A-Za-z0-9]{2,4})\.([A-Za-z0-9]{2,4})$", new)
    if dbl and dbl.group(1).lower() == dbl.group(2).lower():
        new = new[: dbl.start()] + "." + dbl.group(2)

    # 首尾空白 / 扩展名前的空格和点
    new = re.sub(r"\s+(?=\.[A-Za-z0-9]{2,4}$)", "", new.strip())
    new = re.sub(r"^[\s._\-—]+", "", new)

    # 净化到只剩扩展名、或只剩 "(1)" 这种序号，说明规则吃过头了，放弃这条
    if not new or new.startswith(".") or new == name:
        return name
    body = os.path.splitext(new)[0]
    if not re.sub(r"[\s()\[\]【】.\-_—]", "", body):
        return name
    # 只剩 "(2)" 这种括号序号，等于把名字删没了
    if re.fullmatch(r"[\s\-_.]*\(\d+\)[\s\-_.]*", body):
        return name
    if os.path.splitext(new)[1].lower() != os.path.splitext(name)[1].lower():
        return name
    return new


FIELDS = ["id", "location", "dir", "old", "new", "status"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="preview or apply conservative filename cleanup")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--location", choices=("local", "115", "pikpak"))
    parser.add_argument("--apply", action="store_true")
    return parser


def write_plan(path: str, plan: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(plan)


def backup_database(db_path: str, backup_dir: str) -> str:
    if not os.path.isfile(db_path):
        raise FileNotFoundError(db_path)
    os.makedirs(backup_dir, exist_ok=True)
    destination = os.path.join(
        backup_dir, "ledger.pre-rename-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".db",
    )
    source = sqlite3.connect(db_path)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return destination


def main(argv: list[str] | None = None) -> int:
    args_ns = build_parser().parse_args(argv)
    configure_log(args_ns.log_dir)
    target = (args_ns.db if args_ns.apply else
              "file:" + os.path.abspath(args_ns.db).replace("\\", "/") + "?mode=ro")
    conn = sqlite3.connect(target, uri=not args_ns.apply)
    where = "WHERE name IS NOT NULL"
    sql_args: list = []
    if args_ns.location:
        where += " AND location = ?"
        sql_args.append(args_ns.location)
    rows = conn.execute(f"SELECT id, location, path, name FROM asset {where}", sql_args).fetchall()
    log(f"扫描 {len(rows)} 条" + (f"（location={args_ns.location}）" if args_ns.location else ""))

    # 同目录已占用的名字，用来挡撞名
    taken: dict[str, set[str]] = {}
    for _, _, path, name in rows:
        taken.setdefault(os.path.dirname(path).lower(), set()).add(name.lower())

    plan = []
    for aid, loc, path, name in rows:
        new = propose(name)
        if new == name:
            continue
        d = os.path.dirname(path)
        status = "collide" if new.lower() in taken[d.lower()] else "ready"
        plan.append({"id": aid, "location": loc, "dir": d,
                     "old": name, "new": new, "status": status})
        if status == "ready":
            taken[d.lower()].add(new.lower())

    ready = [p for p in plan if p["status"] == "ready"]
    log(f"待净化 {len(plan)} 条，其中可执行 {len(ready)}，撞名跳过 {len(plan) - len(ready)}")
    write_plan(args_ns.out, plan)

    if args_ns.apply:
        backup = backup_database(args_ns.db, args_ns.backup_dir)
        log(f"数据库备份 → {backup}")
        ok = fail = gone = 0
        for item in ready:
            src = os.path.join(item["dir"], item["old"])
            dst = os.path.join(item["dir"], item["new"])
            if not os.path.exists(src):
                item["status"] = "missing"
                gone += 1
                continue
            if os.path.exists(dst):
                item["status"] = "collide"
                fail += 1
                continue
            try:
                os.rename(src, dst)
            except Exception as exc:
                item["status"] = f"error:{type(exc).__name__}"
                log(f"  失败 {src} -> {item['new']} : {exc}")
                fail += 1
                continue
            try:
                conn.execute(
                    "UPDATE asset SET path=?, name=? WHERE id=?", (dst, item["new"], item["id"]),
                )
                conn.commit()
            except Exception as exc:
                conn.rollback()
                try:
                    os.rename(dst, src)
                    item["status"] = f"db-error-rolled-back:{type(exc).__name__}"
                except Exception:
                    item["status"] = f"db-error-manual-repair:{type(exc).__name__}"
                log(f"  数据库失败 {src} -> {item['new']} : {exc}")
                fail += 1
                continue
            item["status"] = "done"
            ok += 1
        log(f"改名完成 {ok}，失败 {fail}，源已不存在 {gone}")
    conn.close()

    write_plan(args_ns.out, plan)
    log(f"→ {args_ns.out}")
    if not args_ns.apply:
        log("未加 --apply，只出清单未改名。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
