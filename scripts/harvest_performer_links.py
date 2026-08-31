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

from peach.catalog_rules import is_jav_code   # noqa: E402
from peach.config import STATE_DIR   # noqa: E402
from peach.http import HttpRequest, HttpxTransport   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402

SEARCH = "https://www.minnano-av.com/search_result.php?search_scope=actress&search_word="
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
ACTRESS_PAGE = re.compile(r"/actress(\d+)\.html")
FIELD = re.compile(r"<td[^>]*>\s*<span[^>]*>(.*?)</span>(.*?)</td>", re.S)
HREF = re.compile(r'href=["\']([^"\']+)["\']')
SOCIAL_HOSTS = ("x.com", "twitter.com", "instagram.com", "tiktok.com", "youtube.com")
# 博客也是本人的社交存在，但它没有 handle 概念，标签另算。
BLOG_HOSTS = ("ameblo.jp", "lineblog.me", "note.com", "livedoor.jp", "hatenablog.com")
LINK_LABELS = {"ブログ", "公式サイト", "Twitter", "SNS"}
FIELDS = ("entity_id", "kind", "name", "link_kind", "label", "url", "evidence",
          "actress_id", "agency", "verdict")


def search_url(name: str) -> str:
    return SEARCH + quote(name, encoding="utf-8")


KANA = re.compile(r"[぀-ゟ゠-ヿ]")
KANJI = re.compile(r"[一-鿿]")


def name_rank(name: str) -> int:
    """名字对日文站的可用程度，越小越先试。

    账本里 performer 的规范名是简体中文（`凉森玲梦`、`释爱丽丝`），日文站按它一个都搜不到；
    真正能用的日文写法在 `entity_alias` 里（`涼森れむ`、`釈アリス`）。实测 12 位只有 1 位
    命中，就是因为直接拿规范名去搜。

    汉字加假名混排的是艺名本身，最可靠；纯假名是读音，能搜到但更容易撞名；纯汉字既可能
    是日文也可能是简体中文，放在后面；罗马字对日文站基本无效，排最后。
    """
    kana, kanji = bool(KANA.search(name)), bool(KANJI.search(name))
    if kana and kanji:
        return 0
    if kana:
        return 1
    if kanji:
        return 2
    return 3


def name_chain(canonical: str, aliases: list[str]) -> list[str]:
    """去重后按可用程度排序的候选名字，罗马字不进链。

    罗马字留着只会白跑一次往返，并且它落空后混进未取得，看起来像是「这个人查不到」，
    而实际上是「我们从没用她的日文名查过」。
    """
    seen: list[str] = []
    for name in [canonical, *aliases]:
        name = (name or "").strip()
        if name and name not in seen and name_rank(name) < 3:
            seen.append(name)
    return sorted(seen, key=name_rank)


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


def under(host: str, domains: tuple[str, ...]) -> bool:
    """host 是否就是这些域名之一或它们的子域。

    直接用 `endswith` 会把 `notx.com` 判成 x.com——后缀匹配必须落在点边界上，
    否则任何人注册一个以平台名结尾的域名就能让链接被标成官方社交账号。
    """
    return any(host == domain or host.endswith("." + domain) for domain in domains)


PLATFORM_NAMES = {("x.com", "twitter.com"): "X", ("instagram.com",): "Instagram",
                  ("tiktok.com",): "TikTok", ("youtube.com",): "YouTube"}


def classify(url: str, agency: str = "") -> tuple[str, str]:
    """(link_kind, label)。label 就是资料页上那行链接文字，所以要说清点过去是什么。

    事务所页面用事务所名当标签（`T-POWERS` 而不是通用的「官方网站」）：用户要的正是
    厂商链接，而这个名字资料表里已经给了，退回通用词等于把取到的信息扔掉。
    """
    host = (urlsplit(url).hostname or "").casefold().removeprefix("www.")
    if under(host, SOCIAL_HOSTS):
        handle = urlsplit(url).path.strip("/").split("/")[0]
        platform = next((name for hosts, name in PLATFORM_NAMES.items() if under(host, hosts)),
                        host)
        return "social", (f"{platform} @{handle}" if handle else platform)
    if under(host, BLOG_HOSTS):
        return "social", "博客"
    return "official", (agency.strip() or "官方网站")


def load_performers(connection: sqlite3.Connection, minimum: int) -> list[dict]:
    """有作品的 performer，跳过确定不是 JAV 的。

    minnano-av 是 JAV 资料库，拿中文素人创作者去查必然落空，还会把真正的缺口盖住——
    和 `audit_performer_portraits.py` 跳过非 JAV 是同一条理由，判据复用同一个函数。
    看不见作品是未知不是反面证据，照查；看得见但没有一个 JAV 番号才跳过。
    """
    codes: dict[int, list[str]] = {}
    counts: dict[int, int] = {}
    for entity_id, total, joined in connection.execute(
            "SELECT ae.entity_id, count(*), group_concat(DISTINCT a.code) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE a.medium='video' GROUP BY ae.entity_id"):
        counts[entity_id] = int(total or 0)
        codes[entity_id] = [code for code in str(joined or "").split(",") if code]
    aliases: dict[int, list[str]] = {}
    for entity_id, alias in connection.execute(
            "SELECT entity_id, alias FROM entity_alias ORDER BY confidence DESC, alias"):
        aliases.setdefault(entity_id, []).append(alias)
    out = []
    for entity_id, name in connection.execute(
            "SELECT id, canonical_name FROM entity WHERE kind='performer'"):
        total = counts.get(entity_id, 0)
        if total < minimum:
            continue
        # 「作品可见却一个 JAV 番号都没有」是非 JAV 的反面证据（中文素人创作者正是这个
        # 形态）；「一个作品都看不见」只是未知，照查不误。按非空番号判会把前者也当成未知，
        # 查一遍落空后混进未取得，把真正查不到的 JAV 女优盖住。
        if total and not any(is_jav_code(code) for code in codes.get(entity_id, ())):
            continue
        out.append({"entity_id": entity_id, "name": name, "assets": total,
                    "chain": name_chain(name, aliases.get(entity_id, []))})
    return sorted(out, key=lambda record: -record["assets"])


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
