"""从 minnano-av 取女优的社媒与事务所链接。

用户要的「参考 beeg 的社媒链接」在账本里没有来源：Stash 导入早已跑过，567 位 performer
只带出 2 条 URL，因为本机 Stash 根本没存这些字段。minnano-av 是目前唯一能从女优名走到
社媒和事务所的入口，`docs/reference-snapshots/minnano-av-official-portraits.md` 记的
就是这件事——那份记录里「从女优名定位页面的检索形态」当时写的是未取得，本脚本把它取到了。

**只采信重定向。** `search_result.php?search_scope=actress&search_word=<名字>` 有三种结果：
唯一命中会跳到 `actressNNN.html`；多命中或无命中都停在检索页，标题写
「「<查询>」のAV女優検索結果」。检索页正文里同样有一堆 `actressNNN.html`，那是「相关女优」，
按正文解析会把别人的社媒安到这个人头上——信号只在最终地址里。

资料表形如 `<td><span>标签</span><p>值</p></td>`。站内链接是相对路径
（`actress_list.php?...`），站外链接是绝对 URL，用这条区分外链，不猜标签集合。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.config import STATE_DIR   # noqa: E402
from peach.entities import name_chain   # noqa: E402,F401  测试从本模块取 name_chain
from peach.http import HttpRequest, HttpxTransport   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.scripting import USER_AGENT   # noqa: E402
# 平台判据与选人规则和目录型采集器共用，定义在 peach.social_links；这里只保留 minnano-av 的解析。
from peach.social_links import classify, load_performers, under   # noqa: E402,F401

SEARCH = "https://www.minnano-av.com/search_result.php?search_scope=actress&search_word="
ACTRESS_PAGE = re.compile(r"/actress(\d+)\.html")
FIELD = re.compile(r"<td[^>]*>\s*<span[^>]*>(.*?)</span>(.*?)</td>", re.S)
HREF = re.compile(r'href=["\']([^"\']+)["\']')
LINK_LABELS = {"ブログ", "公式サイト", "Twitter", "SNS"}
FIELDS = ("entity_id", "kind", "name", "link_kind", "label", "url", "evidence",
          "actress_id", "agency", "verdict")


def search_url(name: str) -> str:
    return SEARCH + quote(name, encoding="utf-8")


def actress_id(final_url: str) -> str:
    """唯一命中时最终地址里的女优编号；停在检索页就返回空。"""
    match = ACTRESS_PAGE.search(urlsplit(final_url).path)
    return match.group(1) if match else ""


def profile_fields(html: str) -> dict[str, list[str]]:
    """资料表 → {标签: [绝对 URL, ...]}，只留站外链接。

    站内链接（`actress_list.php?blood_type=A` 这类）是检索入口不是这个人的链接，
    混进来会让每位女优都挂上一串「A 型」「東京都」的站内跳转。
    """
    found: dict[str, list[str]] = {}
    for match in FIELD.finditer(html):
        label = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        external = [href for href in HREF.findall(match.group(2))
                    if urlsplit(href).scheme in {"http", "https"}]
        if external:
            found.setdefault(label, []).extend(external)
    return found


def profile_text(html: str, label: str) -> str:
    for match in FIELD.finditer(html):
        if re.sub(r"<[^>]+>", "", match.group(1)).strip() == label:
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(2))).strip()[:80]
    return ""


def scan(http, name: str, timeout: float) -> tuple[list[dict], str, str, str]:
    """返回（链接行, actress_id, 所属事务所, 判定说明）。"""
    response = http(HttpRequest("GET", search_url(name), {"User-Agent": USER_AGENT}),
                    timeout, 4 << 20)
    if response.status != 200:
        return [], "", "", f"未取得：HTTP {response.status}"
    found_id = actress_id(response.url or "")
    if not found_id:
        return [], "", "", "未取得：检索页未唯一命中，需人工消歧"
    html = response.body.decode("utf-8", "replace")
    agency = profile_text(html, "所属事務所")
    rows = []
    for label, urls in profile_fields(html).items():
        if label not in LINK_LABELS:
            continue
        for url in urls:
            link_kind, link_label = classify(url, agency)
            rows.append({"link_kind": link_kind, "label": link_label, "url": url,
                         "evidence": f"minnano-av actress{found_id} 资料表「{label}」"})
    note = (f"命中 actress{found_id}，{len(rows)} 条外链" if rows
            else f"命中 actress{found_id}，资料表没有外链")
    return rows, found_id, agency, note


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-assets", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".performer-links.lock")
    return parser


def run(args) -> int:
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    try:
        performers = load_performers(connection, args.min_assets)
    finally:
        connection.close()
    if args.limit:
        performers = performers[:args.limit]
    print(f"待查 {len(performers)} 位 performer")

    results: list[dict[str, object]] = []
    http = HttpxTransport()
    last = 0.0
    hit = 0
    try:
        for record in performers:
            rows, found_id, agency, note, used = [], "", "", "未取得：没有可用于日文站的名字", ""
            for candidate in record["chain"]:
                wait = args.interval - (time.monotonic() - last)
                if wait > 0:
                    time.sleep(wait)
                last = time.monotonic()
                try:
                    rows, found_id, agency, note = scan(http, candidate, args.timeout)
                except Exception as exc:
                    rows, found_id, agency, note = [], "", "", f"未取得：{type(exc).__name__}"
                used = candidate
                # 唯一命中就停：名字链后面的写法只是同一个人的别的叫法，再查是白跑。
                if found_id:
                    break
            if rows:
                hit += 1
            for row in rows:
                row["evidence"] += f"；账本名「{record['name']}」经「{used}」检索命中"
                results.append({"entity_id": record["entity_id"], "kind": "performer",
                                "name": record["name"], "actress_id": found_id,
                                "agency": agency, "verdict": "ok", **row})
            if not rows:
                blank = {field: "" for field in FIELDS}
                blank.update(entity_id=record["entity_id"], kind="performer",
                             name=record["name"], actress_id=found_id, agency=agency,
                             verdict="未取得",
                             evidence=f"{note}（试过 {'、'.join(record['chain']) or '无候选'}）")
                results.append(blank)
            print(f"{record['name'][:12]:<12} {used[:12]:<12} {note}")
    finally:
        http.close()

    write_rows(args.output, FIELDS, results)
    print({"performer": len(performers), "有链接的人": hit,
           "链接行": sum(1 for row in results if row["verdict"] == "ok"),
           "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(job_main(build_parser, run))
