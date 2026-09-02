"""目录型来源的社媒采集：整站翻一遍，按名字对回账本，X 账号再验一次活。

minnano-av 采集器是「拿名字去搜」。laoshi.ink（686 位）和事务所官网 bstar-pro（22 位）
反过来：页面数有限，一次全部抓下来缓存在本地，再拿每页的名字去账本里找人。比对不花
网络，同一批页面能反复对比；「同名多人」「同平台另有账号」都能在离线阶段判出来，
不会静默装错人。

来源本身可能是旧数据（用户 2026-09-02 指出：抄来的 X / Instagram 账号点进去已经封停，
本人一般早换了新号）。所以采到的 X 账号逐个取登出页验活：有 og:title 且 og:image 指向
profile_images 才算活。Instagram / TikTok / YouTube 登出页给不出可靠信号，标「未验」。
只有「活」和「未验」的进安装队列；「疑似失效」只进复核表。冲突行两边都验，证据里写明
账本旧号是死是活——旧号死、新号活，就是用户说的「一般都会有新的」。

判定（verdict）：
    ok            账本唯一命中，该平台该账号账本还没有
    已有          同账号已在账本（twitter.com/x.com 视为同一主机，handle 不分大小写）
    conflict      同平台账本另有账号——用户要的「交叉对比」，只报不装
    需人工消歧    页面名字对上不止一位 performer
    未取得        页面抓不到，或命中的人页面上没有社交链接

输出两份 CSV：`<output>` 只含可装的 ok 行，直接喂 install_entity_links.py；
`<stem>-review.csv` 含全部判定，是复核产物。

laoshi.ink 与 bstar-pro.com 直连（经代理握手失败，站点本身可达）；x.com 走代理。
bstar-pro 的 models.html 有年龄门：同一会话先 `POST age_check=yes`，之后的 GET 才给列表。
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.config import STATE_DIR   # noqa: E402
from peach.http import HttpRequest, HttpxTransport   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.social_links import (   # noqa: E402
    canonical_url, classify, handle, load_performers, name_key, platform, under,
    x_profile_state,
)

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
HREF = re.compile(r'href=["\']([^"\']+)["\']')
TAG = re.compile(r"<[^>]+>")
FIELDS = ("entity_id", "kind", "name", "link_kind", "label", "url", "evidence",
          "source", "page", "matched_name", "verdict", "alive")
SOURCES = ("laoshi", "bstar")
ALIVE, GONE, UNVERIFIED, UNKNOWN = "活", "疑似失效", "未验", "未取得"

LAOSHI = "https://laoshi.ink/"
LAOSHI_OWN = ("laoshi.ink",)
LAOSHI_ACTOR = re.compile(r"https://laoshi\.ink/actresses/actor-\d+\.html")
LAOSHI_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
LAOSHI_FACT = re.compile(r"<span>([^<]+)</span>\s*<strong>(.*?)</strong>", re.S)
LAOSHI_NAME_FIELDS = ("中文名", "日文名", "别名")
LAOSHI_BLANK = {"", "待补充", "暂无", "-", "—", "无"}
LD_JSON = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

BSTAR = "https://bstar-pro.com/"
BSTAR_OWN = ("bstar-pro.com",)
BSTAR_MODELS = BSTAR + "models.html"
BSTAR_LABEL = "Bstar"
BSTAR_ENTRY = re.compile(r'<a href="(model\.html\?mid=\d+)"[^>]*>(.*?)</a>', re.S)
BSTAR_ALT = re.compile(r'alt="([^"]*)"')
BSTAR_SPAN = re.compile(r"<span[^>]*>(.*?)</span>", re.S)
BSTAR_GATE = re.compile(r'name=["\']age_check["\']')

X_PROFILE = "https://x.com/{}"
#: 对照账号：X 官方号，登出页永远有 og:image。用来区分「账号没了」和「我们被限流」。
X_CONTROL = "X"


# ---------------------------------------------------------------- 取页

class HttpStatusError(RuntimeError):
    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.status = status


class Site:
    """一个来源的取页器：本地缓存优先，未命中才走网络并按间隔限速。

    缓存按 URL 的 sha1 落在 `STATE_DIR/directory-links/<来源>/`。686 页抓一次要十来分钟，
    而名字比对规则改一行就得重跑；没有缓存，每次调规则都是一次完整重抓。
    """

    def __init__(self, cache_dir: Path, interval: float, timeout: float, *,
                 refresh: bool = False, via_proxy: bool = False, transport=None):
        self.cache_dir, self.interval, self.timeout, self.refresh = cache_dir, interval, timeout, refresh
        self.transport = transport or HttpxTransport(
            httpx.Client(trust_env=via_proxy, follow_redirects=True))
        self._last = 0.0
        self.fetched = self.cached = 0

    def request(self, method: str, url: str, body: bytes | None = None,
                headers: dict[str, str] | None = None) -> str:
        wait = self.interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        response = self.transport(
            HttpRequest(method, url, {"User-Agent": USER_AGENT, **(headers or {})}, body=body),
            self.timeout, 8 << 20)
        if response.status != 200:
            raise HttpStatusError(response.status)
        return response.body.decode("utf-8", "replace")

    def cache_path(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha1(url.encode("utf-8")).hexdigest()[:20] + ".html")

    def get(self, url: str, refresh: bool = False) -> str:
        path = self.cache_path(url)
        if not (refresh or self.refresh) and path.exists():
            self.cached += 1
            return path.read_text("utf-8")
        text = self.request("GET", url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")
        self.fetched += 1
        return text

    def close(self) -> None:
        self.transport.close()


# ---------------------------------------------------------------- 解析

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(TAG.sub(" ", text)).replace("\xa0", " ")).strip()


def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def split_names(text: str) -> list[str]:
    """`别名` 一栏可能塞好几个名字；分隔符不分中日文标点。不按空格拆——罗马字里有空格。"""
    return [part.strip() for part in re.split(r"[、,，/／|｜;；]", text)
            if part.strip() and part.strip() not in LAOSHI_BLANK]


def external_links(html: str, own_hosts: tuple[str, ...], base: str = "") -> list[str]:
    """页面上的站外绝对链接，去掉本站与相对路径。

    bstar-pro 的页脚有 `href="/https://x.com/bstar_pro/"` 这种写坏的相对路径，
    urljoin 之后落在本站主机上，正好被本站过滤掉——不必单独处理。
    """
    out = []
    for href in HREF.findall(html):
        url = html_lib.unescape(href).strip()
        if base:
            url = urljoin(base, url)
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            continue
        if under(parts.hostname.casefold(), own_hosts):
            continue
        out.append(url)
    return dedupe(out)


def laoshi_listing(sitemap_xml: str) -> list[str]:
    """sitemap 里的女优页；站内搜索是纯前端 JS，服务端没有可用的检索入口。"""
    return sorted(set(LAOSHI_ACTOR.findall(sitemap_xml)))


def laoshi_names(html: str) -> list[str]:
    """标题 `中文名（日文名 / Romaji）` 加「基本资料」里的中文名、日文名、别名。

    标题有时只有一种写法（`桃園怜奈`、`西田カリナ（Karina Nishida）`），所以两处都取；
    「待补充」这类占位词不是名字。
    """
    names: list[str] = []
    title = LAOSHI_TITLE.search(html)
    if title:
        head = clean(title.group(1)).split("｜")[0].split("|")[0]
        main, _, rest = (re.split(r"([（(])", head, maxsplit=1) if re.search(r"[（(]", head)
                         else (head, "", ""))
        names += split_names(main) + split_names(rest.rstrip("）)"))
    for label, value in LAOSHI_FACT.findall(html):
        if clean(label) in LAOSHI_NAME_FIELDS:
            names += split_names(clean(value))
    return dedupe(names)


def _same_as(node) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        same = node.get("sameAs")
        if isinstance(same, str):
            found.append(same)
        elif isinstance(same, list):
            found += [item for item in same if isinstance(item, str)]
        for value in node.values():
            found += _same_as(value)
    elif isinstance(node, list):
        for item in node:
            found += _same_as(item)
    return found


def laoshi_links(html: str) -> list[str]:
    """ld+json 的 sameAs 加正文外链。sameAs 是站方明确声明的「本人主页」，正文锚点作补充。"""
    urls: list[str] = []
    for block in LD_JSON.findall(html):
        try:
            urls += _same_as(json.loads(block))
        except ValueError:
            continue
    return dedupe(urls + external_links(html, LAOSHI_OWN))


def bstar_gated(html: str) -> bool:
    return bool(BSTAR_GATE.search(html)) and not BSTAR_ENTRY.search(html)


def bstar_listing(html: str) -> list[tuple[str, list[str]]]:
    """models.html → [(模特页 URL, [日文名, 罗马字])]。名字来自缩略图 alt 与两行说明。"""
    out: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for href, inner in BSTAR_ENTRY.findall(html):
        url = urljoin(BSTAR, html_lib.unescape(href))
        if url in seen:
            continue
        seen.add(url)
        names: list[str] = []
        alt = BSTAR_ALT.search(inner)
        if alt:
            names.append(clean(alt.group(1)))
        names += [clean(span) for span in BSTAR_SPAN.findall(inner)]
        out.append((url, dedupe(names)))
    return out


# ---------------------------------------------------------------- 采集

def page_record(source: str, url: str, names: list[str], links: list[str], *,
                official: tuple[str, str] | None = None, note: str = "") -> dict:
    return {"source": source, "page": url, "names": names, "links": links,
            "official": official, "note": note}


def failed(source: str, url: str, exc: Exception) -> dict:
    return page_record(source, url, [], [], note=f"未取得：{type(exc).__name__}: {exc}"[:160])


def collect_laoshi(site: Site, limit: int = 0) -> tuple[list[str], list[dict]]:
    """返回（站点自身的社交链接, 页面记录）。首页上的账号是站方的，不是任何女优的。"""
    site_links = [url for url in external_links(site.get(LAOSHI), LAOSHI_OWN) if platform(url)]
    urls = laoshi_listing(site.get(LAOSHI + "sitemap.xml"))
    if limit:
        urls = urls[:limit]
    pages = []
    for url in urls:
        try:
            html = site.get(url)
            pages.append(page_record("laoshi", url, laoshi_names(html), laoshi_links(html)))
        except Exception as exc:   # 单页失败只记未取得，不拖垮整批
            pages.append(failed("laoshi", url, exc))
    return site_links, pages


def bstar_pass_gate(site: Site) -> None:
    site.request("POST", BSTAR_MODELS, body=b"age_check=yes",
                 headers={"Content-Type": "application/x-www-form-urlencoded"})


def bstar_page(site: Site, url: str) -> str:
    html = site.get(url)
    if bstar_gated(html):
        bstar_pass_gate(site)
        html = site.get(url, refresh=True)
        if bstar_gated(html):
            raise RuntimeError("年龄门没过")
    return html


def collect_bstar(site: Site, limit: int = 0) -> tuple[list[str], list[dict]]:
    """事务所官网：列表页给名字，模特页给 SNS。列表页上的账号是事务所的，要从每页里减掉。"""
    listing = bstar_page(site, BSTAR_MODELS)
    site_links = [url for url in external_links(listing, BSTAR_OWN, BSTAR) if platform(url)]
    entries = bstar_listing(listing)
    if limit:
        entries = entries[:limit]
    pages = []
    for url, names in entries:
        try:
            html = bstar_page(site, url)
            pages.append(page_record("bstar", url, names, external_links(html, BSTAR_OWN, BSTAR),
                                     official=(url, BSTAR_LABEL)))
        except Exception as exc:
            pages.append(failed("bstar", url, exc))
    return site_links, pages


COLLECTORS = {"laoshi": collect_laoshi, "bstar": collect_bstar}


# ---------------------------------------------------------------- 判定

def row(**values) -> dict:
    record = {field: "" for field in FIELDS}
    record.update(values)
    return record


def index_names(performers: list[dict]) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {}
    for record in performers:
        for name in [record["name"], *record["chain"]]:
            key = name_key(name)
            if key:
                index.setdefault(key, set()).add(record["entity_id"])
    return index


def load_existing(connection: sqlite3.Connection) -> tuple[dict, dict]:
    """账本现有链接 → ({entity_id: {(平台, handle): url}}, {entity_id: {url}})。"""
    handles: dict[int, dict[tuple[str, str], str]] = {}
    urls: dict[int, set[str]] = {}
    for entity_id, url in connection.execute("SELECT entity_id, url FROM entity_link"):
        urls.setdefault(entity_id, set()).add(url)
        name, account = platform(url), handle(url)
        if name and account:
            handles.setdefault(entity_id, {})[(name, account)] = url
    return handles, urls


def judge(pages: list[dict], site_links: list[str], performers: list[dict],
          existing_handles: dict, existing_urls: dict) -> tuple[list[dict], Counter]:
    """页面记录 → 复核行。会把本轮判 ok 的账号记进 existing_handles，后来的来源据此判已有/冲突。

    冲突只对「进这页之前」账本已有的账号判：同一页上列两个 X 账号是主号加副号，
    不是两处资料打架。
    """
    by_id = {record["entity_id"]: record for record in performers}
    index = index_names(performers)
    ignore = {(platform(url), handle(url)) for url in site_links}
    rows: list[dict] = []
    stats: Counter = Counter()
    for page in pages:
        base = {"kind": "performer", "source": page["source"], "page": page["page"]}
        if page["note"]:
            rows.append(row(**base, verdict="未取得", evidence=page["note"]))
            stats["页面未取得"] += 1
            continue
        matched: set[int] = set()
        used: list[str] = []
        for name in page["names"]:
            ids = index.get(name_key(name))
            if ids:
                matched |= ids
                used.append(name)
        socials = []
        seen: set[tuple[str, str]] = set()
        for url in page["links"]:
            key = (platform(url), handle(url))
            if not key[0] or not key[1] or key in ignore or key in seen:
                continue
            seen.add(key)
            socials.append((canonical_url(url), *key))
        if not matched:
            stats["页面不在账本"] += 1
            continue
        matched_name = "、".join(used)
        if len(matched) > 1:
            names = "、".join(by_id[entity_id]["name"] for entity_id in sorted(matched))
            for url, _, _ in socials:
                link_kind, label = classify(url)
                rows.append(row(**base, link_kind=link_kind, label=label, url=url,
                                matched_name=matched_name, verdict="需人工消歧",
                                evidence=f"页面名「{matched_name}」对上多位：{names}"))
                stats["需人工消歧"] += 1
            continue
        entity_id = matched.pop()
        record = by_id[entity_id]
        base.update(entity_id=entity_id, name=record["name"], matched_name=matched_name)
        where = f"{page['source']} {page['page']}；页面名「{matched_name}」对上账本「{record['name']}」"
        if not socials and not page["official"]:
            rows.append(row(**base, verdict="未取得", evidence=f"{where}；页面上没有社交链接"))
            stats["命中但无社媒"] += 1
            continue
        held = existing_handles.setdefault(entity_id, {})
        prior = dict(held)
        for url, name, account in socials:
            link_kind, label = classify(url)
            item = row(**base, link_kind=link_kind, label=label, url=url)
            if (name, account) in prior:
                item.update(verdict="已有", evidence=f"{where}；账本已有 {prior[(name, account)]}")
            else:
                others = [held_url for (held_name, _), held_url in prior.items() if held_name == name]
                if others:
                    item.update(verdict="conflict",
                                evidence=f"{where}；账本同平台另有 {'、'.join(others)}，需交叉核对")
                else:
                    item.update(verdict="ok", evidence=where)
                    held[(name, account)] = url
            rows.append(item)
            stats[item["verdict"]] += 1
        if page["official"]:
            url, label = page["official"]
            if url in existing_urls.get(entity_id, set()):
                rows.append(row(**base, link_kind="official", label=label, url=url,
                                verdict="已有", evidence=f"{where}；账本已有此页"))
                stats["已有"] += 1
            else:
                rows.append(row(**base, link_kind="official", label=label, url=url,
                                verdict="ok", evidence=f"{where}；本人在事务所官网的页面"))
                existing_urls.setdefault(entity_id, set()).add(url)
                stats["ok"] += 1
    return rows, stats


# ---------------------------------------------------------------- 验活

def probe_x(site: Site, account: str, memo: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """X 账号活不活 → (状态, 显示名)。同一账号只查一次。"""
    key = account.casefold()
    if key not in memo:
        try:
            state, display = x_profile_state(site.get(X_PROFILE.format(account)))
            if state == "unknown":
                # 实测 2026-09-02：不存在的账号登出页也是 200，只是没有任何 og 标签——和限流
                # 回的 JS 壳长得一样。同一时刻不走缓存再取对照账号：对照有 og，这个就是真没了；
                # 对照也没有，是我们被限流，只能记未取得。
                control, _ = x_profile_state(site.get(X_PROFILE.format(X_CONTROL), refresh=True))
                state = "gone" if control == "alive" else "unknown"
                display = "登出页无资料，对照账号正常" if state == "gone" else "登出页无资料，对照账号也无（限流）"
            memo[key] = ({"alive": ALIVE, "gone": GONE}.get(state, UNKNOWN), display)
        except HttpStatusError as exc:
            memo[key] = (GONE if exc.status == 404 else UNKNOWN, f"HTTP {exc.status}")
        except Exception as exc:
            memo[key] = (UNKNOWN, type(exc).__name__)
    return memo[key]


def probe_rows(rows: list[dict], existing_handles: dict, site: Site | None) -> Counter:
    """给 ok / conflict 的社交行填 `alive`；冲突行连账本那边的旧号一起验，证据里写明。

    site 为 None 表示本轮不验（`--no-probe`），全部标未验——列不能空着，空着看不出
    是「没验」还是「验了没结论」。
    """
    memo: dict[str, tuple[str, str]] = {}
    stats: Counter = Counter()
    for item in rows:
        if item["verdict"] not in {"ok", "conflict"} or item["link_kind"] != "social":
            continue
        name = platform(item["url"])
        if name != "X" or site is None:
            item["alive"] = UNVERIFIED
            continue
        state, display = probe_x(site, handle(item["url"]), memo)
        item["alive"] = state
        stats[state] += 1
        if display:
            item["evidence"] += (f"；X 显示名「{display}」" if state == ALIVE else f"；X 验活：{display}")
        if item["verdict"] == "conflict":
            olds = [url for (held_name, _), url in existing_handles.get(item["entity_id"], {}).items()
                    if held_name == "X" and handle(url) != handle(item["url"])]
            for old in olds:
                old_state, _ = probe_x(site, handle(old), memo)
                item["evidence"] += f"；账本旧号 {old}：{old_state}"
    return stats


def installable(rows: list[dict]) -> list[dict]:
    """只有 ok 且没被验成失效的行进安装队列。"""
    return [item for item in rows if item["verdict"] == "ok" and item["alive"] != GONE]


# ---------------------------------------------------------------- 入口

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="安装队列 CSV；复核表写到同目录的 <stem>-review.csv")
    parser.add_argument("--source", choices=("all", *SOURCES), default="all")
    parser.add_argument("--min-assets", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0, help="每个来源最多看几页（试跑用）")
    parser.add_argument("--interval", type=float, default=1.2)
    parser.add_argument("--x-interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--refresh", action="store_true", help="忽略本地缓存重新抓")
    parser.add_argument("--no-probe", action="store_true", help="不去 x.com 验活")
    parser.add_argument("--cache-dir", type=Path, default=STATE_DIR / "directory-links")
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".directory-links.lock")
    return parser


def run(args) -> int:
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    try:
        performers = load_performers(connection, args.min_assets)
        existing_handles, existing_urls = load_existing(connection)
    finally:
        connection.close()
    print(f"账本可比对 performer {len(performers)} 位")

    rows: list[dict] = []
    totals: Counter = Counter()
    sources = SOURCES if args.source == "all" else (args.source,)
    for source in sources:
        site = Site(args.cache_dir / source, args.interval, args.timeout, refresh=args.refresh)
        try:
            site_links, pages = COLLECTORS[source](site, args.limit)
        except Exception as exc:
            print(f"[{source}] 未取得：{type(exc).__name__}: {exc}")
            continue
        finally:
            site.close()
        source_rows, stats = judge(pages, site_links, performers, existing_handles, existing_urls)
        rows += source_rows
        totals.update(stats)
        print(f"[{source}] 页面 {len(pages)}，网络 {site.fetched} / 缓存 {site.cached}，"
              f"站方账号 {len(site_links)} 条已剔除，{dict(stats)}")

    x_site = None if args.no_probe else Site(args.cache_dir / "x", args.x_interval, args.timeout,
                                              refresh=args.refresh, via_proxy=True)
    try:
        alive = probe_rows(rows, existing_handles, x_site)
    finally:
        if x_site is not None:
            x_site.close()
    print(f"X 验活 {dict(alive)}" if x_site is not None else "本轮未验活")

    order = {"conflict": 0, "ok": 1, "需人工消歧": 2, "已有": 3, "未取得": 4}
    rows.sort(key=lambda item: (order.get(item["verdict"], 9), str(item["name"]), item["url"]))
    review = args.output.with_name(args.output.stem + "-review.csv")
    queue = installable(rows)
    write_rows(args.output, FIELDS, queue)
    write_rows(review, FIELDS, rows)
    print({"安装队列": len(queue), "复核行": len(rows), **totals,
           "output": str(args.output), "review": str(review)})
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(job_main(build_parser, run))
