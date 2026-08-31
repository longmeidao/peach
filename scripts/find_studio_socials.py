"""从厂牌官网找出其社交账号，穿过 18+ 年龄门。

只采信**厂牌自有域名页面上**的社交链接。维基外链里混着引用来源的新闻站，
直接抓会把新闻站自己的账号当成厂牌的——实测 `妄想族` 条目就抓出了
`@news_postseven` 与 `@taishurxjp`。

AV 厂牌官网普遍先给一个年龄确认页：肯定链接写「はい（入室する）」指向站内，
否定链接指向 dmm.com。不穿过它只能拿到约 10 KB 的空壳页。
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.http import HttpRequest, HttpxTransport   # noqa: E402
from peach.review_csv import read_rows, write_rows

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Peach/0.6"
SOCIAL = re.compile(r'https?://(?:www\.)?(twitter\.com|x\.com)/([A-Za-z0-9_]{2,30})', re.I)
# 平台自身的功能路径，不是账号。
NOT_A_HANDLE = {"share", "intent", "home", "hashtag", "explore", "search", "i", "privacy", "tos"}
ANCHOR = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S | re.I)
AFFIRMATIVE = re.compile(r"はい|入室|入る|同意|ENTER|YES|18\s*歳以上|over\s*18", re.I)
NEGATIVE = re.compile(r"いいえ|退出|戻る|NO\b|18\s*歳未満", re.I)
MAX_HOPS = 2


def affirmative_link(html: str, base: str) -> str | None:
    """返回年龄确认页的「进入」链接；不是年龄门就返回 None。

    判据是锚文本而不是 URL：否定链接通常指向站外（dmm.com），
    肯定链接指向站内，两者的 href 本身看不出区别。
    """
    host = urlsplit(base).hostname or ""
    for match in ANCHOR.finditer(html):
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if not AFFIRMATIVE.search(text) or NEGATIVE.search(text):
            continue
        target = urljoin(base, match.group(1))
        if (urlsplit(target).hostname or "") == host:
            return target
    return None


def handles_in(html: str) -> set[str]:
    return {
        match.group(2) for match in SOCIAL.finditer(html)
        if match.group(2).lower() not in NOT_A_HANDLE
    }


def scan(http, site: str, timeout: float) -> tuple[set[str], str, str]:
    """返回（找到的 handle, 最终 URL, 说明）。"""
    current, note = site, ""
    for hop in range(MAX_HOPS + 1):
        body = http(HttpRequest("GET", current, {"User-Agent": USER_AGENT}), timeout, 8 << 20).body
        html = body.decode("utf-8", "replace")
        found = handles_in(html)
        if found:
            return found, current, note or "官网页面直接给出社交链接"
        following = affirmative_link(html, current)
        if following is None or hop == MAX_HOPS:
            return set(), current, note or "页面无社交链接"
        note = f"穿过 {hop + 1} 层年龄门"
        current = following
    return set(), current, note


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="含 studio,site 两列的 CSV")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=25.0)
    args = parser.parse_args()

    rows = [row for row in read_rows(args.input) if (row.get("site") or "").strip()]

    results: list[dict[str, object]] = []
    http = HttpxTransport()
    last = 0.0
    try:
        for row in rows:
            studio, site = (row.get("studio") or "").strip(), (row["site"]).strip()
            wait = args.interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                found, final, note = scan(http, site, args.timeout)
            except Exception as exc:
                results.append({"studio": studio, "site": site, "final_url": "", "handles": "",
                                "note": f"取不到：{type(exc).__name__}"})
                continue
            results.append({"studio": studio, "site": site, "final_url": final,
                            "handles": "|".join(sorted(found)), "note": note})
            print(f"{studio:<20} {'|'.join(sorted(found)) or '未取得':<28} {note}")
    finally:
        http.close()

    write_rows(args.output, ("studio", "site", "final_url", "handles", "note"), results)
    print({"total": len(results), "with_handles": sum(1 for r in results if r["handles"]),
           "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
