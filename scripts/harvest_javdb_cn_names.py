#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""从 javdb 资料页取女优的中文写法，产出可喂给 `localize_performer_names.py` 的映射。

账本里 95 位女优的规范名还卡在假名上（`深田えいみ`、`河合あすな`、`長谷川るい`），
按中文名一个都搜不到。`localize_performer_names.py` 靠的那份 avdb 映射 XML 不在这台
机器上，而且它对假名名字本来就只能等收录——逐字转写不成立，`飯岡かなこ` 换出来是
`饭冈かなこ`，半中半日比原样留着更糟。

**中文名是查出来的，不是转写出来的。** 这里查的是 javdb 的资料页：它是中文站，页面
顶部把现名的中文写法与日文写法并列在同一个 `actor-section-name` 里，两者**同页共现**，
所以对上的是这个人而不是同名的另一个人。判据见 `peach.javdb`。

    <span class="actor-section-name">深田詠美, 深田えいみ</span>
    <span class="section-meta">天海こころ</span>          ← 旧艺名，不参与配对

三条闸：

1. **账本的名字必须出现在「现名」那一栏。** 只出现在旧艺名里说明站上已经改了名，
   用哪个名字当规范名是人要决定的事（`京香じゅりあ` 那页现名是 `JULIA`），记 `旧名`。
2. **中文写法只认整名汉字、无假名无拉丁的那一个。** 有两个就是站上把别的名字也并进
   了同一栏，记 `多义`，不猜。
3. **搜索命中多页时全部记下来**，不取第一个——取第一个是默默替用户挑了一位。

`?locale=zh-CN` 只切界面语言，女优名是数据不跟着变（2026-09-04 实测：简体界面下
`愛音麻里亞` 仍是繁体）。所以不带这个参数——带上只会让缓存键变一套、把已经取回的
页面再取一遍——繁转简由 opencc 做，它已经是本项目声明的依赖。

只产出映射 CSV，不写账本。落库走 `localize_performer_names.py --mapping-csv`，
那边有重名冲突判定、旧名保留和演员标签改写。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urljoin

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach import javdb   # noqa: E402
from peach.config import STATE_DIR   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.social_links import name_key   # noqa: E402

#: 发行元数据来源。账号型 performer 不是女优，不翻译。
RELEASE_SOURCES = ("r18:performer", "javbus:performer")
KANA = re.compile(r"[぀-ヿ]")
HAN = re.compile(r"[㐀-䶿一-鿿]")
LATIN = re.compile(r"[A-Za-z]")

OK, FORMER, AMBIGUOUS, SAME_SHAPE, LOGIN, MISSING, FAILED = (
    "ok", "旧名", "多义", "同形（站上只有日文名）", "要登录", "未取得", "取页失败")

FIELDS = ("entity_id", "current_name", "assets", "actor_id", "url",
          "jp", "zh_cn", "zh_tw", "keywords", "verdict", "evidence")


def _simplify():
    """繁转简。opencc 是 `naming` 这个可选依赖，缺了就明说，不静默产出繁体。"""
    try:
        import opencc
    except ImportError as exc:   # pragma: no cover - 取决于安装方式
        raise SystemExit("需要 opencc：pip install -e .[naming]") from exc
    return opencc.OpenCC("t2s").convert


def targets(connection: sqlite3.Connection) -> list[dict]:
    """规范名还带假名、且有发行来源的 performer，连它的名字链。"""
    connection.row_factory = sqlite3.Row
    aliases: dict[int, list[str]] = {}
    for row in connection.execute(
            "SELECT entity_id,alias FROM entity_alias ORDER BY entity_id,alias"):
        aliases.setdefault(int(row["entity_id"]), []).append(str(row["alias"]))
    out = []
    for row in connection.execute(
        "SELECT e.id,e.canonical_name,"
        " (SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae WHERE ae.entity_id=e.id) n,"
        " (SELECT group_concat(DISTINCT ae.source) FROM asset_entity ae"
        "   WHERE ae.entity_id=e.id) sources"
        " FROM entity e WHERE e.kind='performer' ORDER BY e.id"
    ):
        name = str(row["canonical_name"])
        sources = set(filter(None, str(row["sources"] or "").split(",")))
        if not KANA.search(name) or not sources.intersection(RELEASE_SOURCES):
            continue
        chain = list(dict.fromkeys([name, *aliases.get(int(row["id"]), [])]))
        out.append({"entity_id": int(row["id"]), "name": name,
                    "assets": int(row["n"]), "chain": chain})
    return out


def chinese_name(current: list[str]) -> tuple[str, str]:
    """现名那一栏里的中文写法与判据。整名汉字、无假名无拉丁的才算。"""
    han = [value for value in current
           if HAN.search(value) and not KANA.search(value) and not LATIN.search(value)]
    if len(han) == 1:
        return han[0], ""
    if not han:
        return "", SAME_SHAPE
    return "", AMBIGUOUS


def judge(record: dict, html: str, url: str) -> dict:
    """一页资料页对一位账本女优的判定。"""
    current, former = javdb.current_names(html), javdb.former_names(html)
    wanted = {name_key(value) for value in record["chain"]}
    row = {"entity_id": record["entity_id"], "current_name": record["name"],
           "assets": record["assets"], "actor_id": javdb.actor_id(html), "url": url,
           "jp": "", "zh_cn": "", "zh_tw": "", "keywords": "|".join(current),
           "verdict": "", "evidence": f"现名 {'、'.join(current) or '未取得'}"}
    if not wanted & {name_key(value) for value in current}:
        row["verdict"] = FORMER
        row["evidence"] = (f"账本名只出现在旧艺名里；站上现名 {'、'.join(current) or '未取得'}")
        return row
    zh_tw, why = chinese_name(current)
    if not zh_tw:
        row["verdict"] = why
        return row
    jp = next((value for value in current if KANA.search(value)), record["name"])
    row.update(jp=jp, zh_tw=zh_tw, verdict=OK,
               evidence=f"资料页现名一栏同时写着 {zh_tw} 与 {jp}")
    return row


def harvest(connection: sqlite3.Connection, site, limit: int) -> list[dict]:
    rows: list[dict] = []
    for record in targets(connection)[:limit] if limit else targets(connection):
        wanted = {name_key(value) for value in record["chain"]}
        hits: list[str] = []
        search = ""
        error = None
        for name in record["chain"]:
            search = javdb.SEARCH.format(quote(name))
            try:
                hits = javdb.search_hits(site.get(search), wanted)
            except Exception as exc:   # noqa: BLE001 - 取页失败要落进 CSV，不能中断整批
                error = f"{type(exc).__name__}: {exc}"
                break
            if hits:
                break
        if error:
            rows.append({"entity_id": record["entity_id"], "current_name": record["name"],
                         "assets": record["assets"], "url": search, "verdict": FAILED,
                         "evidence": error})
            continue
        if not hits:
            rows.append({"entity_id": record["entity_id"], "current_name": record["name"],
                         "assets": record["assets"], "url": search, "verdict": MISSING,
                         "evidence": f"搜过名字链的 {len(record['chain'])} 个写法，站上没有这个人"})
            continue
        for path in hits:
            url = urljoin(javdb.BASE, path)
            try:
                html = site.get(url)
            except Exception as exc:   # noqa: BLE001
                rows.append({"entity_id": record["entity_id"], "current_name": record["name"],
                             "assets": record["assets"], "url": url, "verdict": FAILED,
                             "evidence": f"{type(exc).__name__}: {exc}"})
                continue
            if javdb.LOGIN.search(html):
                rows.append({"entity_id": record["entity_id"], "current_name": record["name"],
                             "assets": record["assets"], "url": url, "verdict": LOGIN,
                             "evidence": "这一页要登录才给，不注册账号"})
                continue
            rows.append(judge(record, html, url))
    return rows


def localize(rows: list[dict]) -> list[dict]:
    """给判成 `ok` 的行填简体写法。繁体原样留在 `zh_tw`，复核时要看得出转了什么。"""
    convert = _simplify()
    for row in rows:
        # 没判成 `ok` 的行也要有这一列且为空：复核件里空格与「这一格不存在」在人眼里
        # 一样，在按列取值的代码里不一样。
        row["zh_cn"] = convert(str(row["zh_tw"])) if row.get("verdict") == OK else ""
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 javdb 资料页取女优中文名，产出映射 CSV")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    # javdb 按出口 IP 自己封速率。5 秒是 `harvest_directory_links.SOURCE_INTERVAL`
    # 定下的那一档，两处必须一致：换个脚本就换个速度等于没有速度约束。
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--cache-dir", type=Path, default=STATE_DIR / "directory-links")
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".javdb-cn-names.lock")
    parser.add_argument("--refresh", action="store_true")
    return parser


def run(args: argparse.Namespace) -> int:
    from peach.page_cache import Site

    site = Site(args.cache_dir / "javdb", max(args.interval, 5.0), args.timeout,
                refresh=args.refresh, via_proxy=True)
    connection = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    try:
        rows = localize(harvest(connection, site, args.limit))
    finally:
        connection.close()
    write_rows(args.out, FIELDS, rows, fill_missing=True)
    counts = Counter(str(row.get("verdict")) for row in rows)
    print(f"javdb 中文名 {len(rows)} 行，映射 CSV：{args.out}")
    print("  判定分布：", dict(counts))
    for row in rows:
        if row.get("verdict") == OK:
            print(f"    {row['current_name']} -> {row['zh_cn']}  ({row['evidence']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(job_main(build_parser, run))
