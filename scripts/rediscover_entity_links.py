"""死链里有多少只是站点改了结构、页面其实还在。

`install_entity_links.py --prune-dead` 只回答「这条打不开」，回答不了「它是没了还是搬走了」。
两者的处置完全相反：真没了该删，搬走了该改地址。用户由 T-POWERS 一例看出这个区别——
`/official/talent/涼森れむ` 回 404，而 `/talent/涼森れむ/` 好好地开着，同一个人、同一个站。

判据是**站点自己承认这个人**，不是我们拼出一个能打开的地址：

1. 拿这个人的日文名（账本规范名是简体中文，日文写法在 `entity_alias` 里）。
2. 在死链所在站点的索引页里找锚点——href 或锚文本含这个名字。索引页从死链的父级路径
   逐层上溯再加站点根，因为艺人页几乎总挂在某个列表下面。
3. 候选必须回 200 **且标题里有这个人的名字**。少了这一条，`/talent/` 这种列表页本身
   也会 200，然后 400 个人全被改写成同一个列表地址。

改地址是有风险的动作：一条指向别人的链接比一条死链更糟，因为它看起来是对的。所以这里
只产出复核表，不写账本；写入仍走 `install_entity_links.py`，再过一次可达性门槛。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.entities import name_chain   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.scripting import USER_AGENT   # noqa: E402

ANCHOR = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\']([^>]*)>(.*?)</a>', re.S | re.I)
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
FIELDS = ("entity_id", "kind", "name", "link_kind", "label", "url", "evidence",
          "old_url", "matched_name", "found_via", "verdict")


def fetch(url: str, timeout: float = 12.0) -> tuple[int, str, str]:
    """(status, 正文, 最终地址)。每个请求新建 client——失败的连接会漏池槽。"""
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout,
                          limits=httpx.Limits(max_connections=4,
                                              max_keepalive_connections=0)) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
    except Exception:
        return 0, "", url
    return response.status_code, response.text, str(response.url)


def registrable(host: str) -> str:
    """粗粒度的「同一个站」：取末两段，日本的二级后缀再多取一段。

    不引 publicsuffix 依赖——这里只需要把 `www.t-powers.co.jp` 和 `t-powers.co.jp` 判成
    一家、把 `x.com` 判成另一家，而不需要处理公共后缀列表的全部边角。
    """
    parts = host.casefold().split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "or", "ne", "ac", "go", "com", "net", "org"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def same_site(candidate: str, original: str) -> bool:
    a = registrable(urlsplit(candidate).hostname or "")
    b = registrable(urlsplit(original).hostname or "")
    return bool(a) and a == b


def index_candidates(url: str) -> list[str]:
    """从死链逐层上溯的索引页，最深的先试。

    艺人页几乎总挂在某个列表下面，而站点改版通常只动其中一层
    （`/official/talent/X` → `/talent/X/`），上一层的列表往往原地还在。
    """
    parts = urlsplit(url)
    root = f"{parts.scheme}://{parts.netloc}"
    out: list[str] = []
    segments = [s for s in parts.path.split("/") if s]
    for cut in range(len(segments) - 1, -1, -1):
        candidate = root + "/" + "/".join(segments[:cut]) + ("/" if cut else "")
        if candidate not in out:
            out.append(candidate)
    if root + "/" not in out:
        out.append(root + "/")
    return out[:4]


def anchors_naming(html: str, base: str, names: list[str]) -> list[tuple[str, str]]:
    """索引页里提到这些名字的链接，返回 (绝对地址, 命中的名字)。

    href 也要看：日文站的艺人页地址常常就是 URL 编码后的名字，而锚文本可能只是一张图。
    """
    found: list[tuple[str, str]] = []
    for match in ANCHOR.finditer(html):
        href = match.group(1)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(3))).strip()
        haystack = text + " " + unquote(href)
        for name in names:
            if name and name in haystack:
                target = urljoin(base, href)
                if urlsplit(target).scheme in {"http", "https"}:
                    found.append((target, name))
                break
    return found


def confirms(html: str, names: list[str]) -> str:
    """页面标题里有没有这个人的名字；有就返回命中的写法。

    列表页同样回 200。少了这一条，`/talent/` 本身会被当成每个人的新地址。
    """
    match = TITLE.search(html)
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(1))).strip() if match else ""
    # 站点常把姓与名之间加空格（`涼森 れむ`），逐字比会漏掉。
    squeezed = title.replace(" ", "").replace("　", "")
    for name in names:
        if name and (name in title or name.replace(" ", "") in squeezed):
            return title[:90]
    return ""


def rediscover(record: dict, interval: float, timeout: float) -> dict:
    """给一条死链找回它现在的地址。就地返回一行复核结果。"""
    names = record["chain"]
    row = {field: "" for field in FIELDS}
    row.update(entity_id=record["entity_id"], kind=record["kind"], name=record["name"],
               link_kind=record["link_kind"], label=record["label"],
               old_url=record["url"], verdict="未取得")
    if not names:
        row["evidence"] = "没有可用于日文站的名字"
        return row

    seen: set[str] = set()
    for index in index_candidates(record["url"]):
        status, html, final = fetch(index, timeout)
        time.sleep(interval)
        if status != 200 or not html:
            continue
        for target, matched in anchors_naming(html, final, names):
            if target in seen or target.rstrip("/") == record["url"].rstrip("/"):
                continue
            # 修复的定义是「在同一个站点上找到新地址」，不是「找到关于这个人的另一个链接」。
            # 实测 KRONE 的索引页里 `上川星空` 那一条指向她的 X 账号——人是对的（`天馬ゆい`
            # 就在账本别名里），但那不是事务所页面。照单收下会留下一条标着「KRONE(クローネ)」、
            # 点开却是 Twitter 的 official 链接，比一条死链更糟：它看起来是对的。
            if not same_site(target, record["url"]):
                continue
            seen.add(target)
            hit_status, hit_html, hit_final = fetch(target, timeout)
            time.sleep(interval)
            if hit_status != 200:
                continue
            title = confirms(hit_html, names)
            if title:
                row.update(url=hit_final, matched_name=matched, found_via=index,
                           verdict="ok",
                           evidence=f"站点索引 {index} 指向该页，标题自述「{title}」；"
                                    f"旧址 {record['url']} 回 404")
                return row
        if len(seen) > 30:
            break
    row["evidence"] = f"在 {len(seen)} 个候选里没有标题自述该人的页面"
    return row


def load_dead(connection: sqlite3.Connection) -> list[dict]:
    aliases: dict[int, list[str]] = {}
    for entity_id, alias in connection.execute(
            "SELECT entity_id, alias FROM entity_alias ORDER BY confidence DESC, alias"):
        aliases.setdefault(entity_id, []).append(alias)
    out = []
    for link_id, entity_id, kind, name, link_kind, label, url in connection.execute(
            "SELECT l.id, e.id, e.kind, e.canonical_name, l.link_kind, l.label, l.url "
            "FROM entity_link l JOIN entity e ON e.id=l.entity_id ORDER BY l.id"):
        out.append({"link_id": link_id, "entity_id": entity_id, "kind": kind, "name": name,
                    "link_kind": link_kind, "label": label, "url": url,
                    "chain": name_chain(name, aliases.get(entity_id, []))})
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dead-list", type=Path, required=True,
                        help="entity-link-check CSV，只处理其中 status 为 404/410 的行")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--interval", type=float, default=0.4)
    parser.add_argument("--timeout", type=float, default=12.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    from peach.review_csv import read_rows

    args = build_parser().parse_args(argv)
    gone = {row["url"] for row in read_rows(args.dead_list)
            if str(row.get("status") or "") in {"404", "410"}}
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    try:
        targets = [record for record in load_dead(connection)
                   if record["url"] in gone]
    finally:
        connection.close()
    if args.limit:
        targets = targets[:args.limit]
    print(f"待复查 {len(targets)} 条 404")

    results = []
    for index, record in enumerate(targets, 1):
        row = rediscover(record, args.interval, args.timeout)
        results.append(row)
        mark = "搬走了" if row["verdict"] == "ok" else "没找到"
        print(f"{index:>3}/{len(targets)} {record['name'][:10]:<10} {mark}  "
              f"{str(row['url'])[:56]}")

    write_rows(args.output, FIELDS, results)
    moved = [row for row in results if row["verdict"] == "ok"]
    print({"复查": len(results), "实际还在（换了地址）": len(moved),
           "确实没了": len(results) - len(moved), "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
