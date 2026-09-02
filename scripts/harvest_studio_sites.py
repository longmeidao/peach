"""为厂牌找出官网，并留下足以复核的证据。

这是 `find_studio_socials.py` 缺的输入端：那个脚本能从官网穿过 18+ 年龄门取到社交
handle，但它要求先有一份 `studio,site` 的表，而账本里 114 个有作品的厂牌一个官网都没有。

**猜域名不是证据，验证才是。** 候选域名由厂牌名按固定规则推出来（`MOODYZ` → `moodyz.com`），
这一步只负责提出假设；能不能采信取决于取回的页面自己认不认这个身份——标题里必须出现厂牌名。
`moodyz.com` 若是抢注页，标题只会是域名或「域名出售」，过不了这一关。规则化推域名的好处是
可复现：换个人跑同样的输入得到同样的候选，而不是凭记忆写一张表。

推不出来的（`无码厂标`、`Fetish Box / Mousouzoku` 这类）通过 `--seeds` 单独喂，
让人工查到的地址和自动推出来的走同一条验证，而不是绕过验证直接采信。
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import httpx   # noqa: E402

from peach.config import STATE_DIR   # noqa: E402
from peach.http import HttpRequest, HttpxTransport   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.review_csv import read_rows, write_rows   # noqa: E402
from peach.scripting import USER_AGENT   # noqa: E402

TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
# 抢注页与停放页的自述。它们同样会 200，也同样会在标题里回显域名，
# 只有这些词能把它们和真站区分开。
#
# 标题单独判，而且判得更松。实测两次漏判都出在这上面：`kawaii.com - domain for sale`
# 的关键词在正文第 81683 字节，早已超出任何合理的正文扫描窗口，可它就写在标题里；
# `Attackers - The Domain Name Attackers.com is Now For Sale.` 则是中间插了词，
# 逐字匹配「domain for sale」全文都对不上。标题只有几十个字符，真站的标题不会说
# 自己在出售，所以这里可以放心用最宽的判据。
PARKED_TITLE = re.compile(
    r"for sale|domain name|buy this domain|このドメイン|ドメイン(?:の)?販売", re.I)
PARKED = re.compile(
    r"domain (?:is )?for sale|buy this domain|parked (?:free )?at|このドメイン(?:は|を)"
    r"|ドメイン(?:の)?販売|sedo\.com|afternic|godaddy\.com/domain|hugedomains",
    re.I)
# 空壳页也会 200。真站首页（含年龄门）实测都在 10 KB 以上，取一半做下限。
MIN_BODY = 5000
# 「标题里有厂牌名」证明不了这是**这个**厂牌的站——同名的无关公司照样通过。实测四例：
# `madonna.com` 是歌手麦当娜、`hunter.com` 是 Hunter Engineering（四轮定位）、
# `bazooka.com` 是车载音响、`marrion.com` 是一个 Google Sites 页面。它们都 200、
# 都不是停放页、标题里都有厂牌名。
#
# 缺的那一半是「这一页是不是 AV 厂牌站」。这不是补丁：我们要找的就是 AV 厂牌官网，
# 成人语境本来就是判据的一部分。日站首页普遍带年龄门，这些词因此极稳；同时留下英文
# 写法，免得把西方厂牌一律打成待复核。
ADULT = re.compile(
    r"年齢認証|年齢チェック|AVメーカー|アダルトビデオ|アダルトDVD|18歳未満|成人向"
    r"|adult video|adult dvd|porn|18\+|over 18", re.I)
FIELDS = ("entity_id", "studio", "assets", "candidate_url", "final_url", "status",
          "bytes", "sha256", "title", "verdict", "note")


def normalise(text: str) -> str:
    """只留 ASCII 字母数字。

    厂牌名和网页标题的分隔符、括号、全角字符、日文注音全都对不齐（`Idea Pocket` 对
    `【IDEAPOCKET (アイデアポケット）】公式サイト`），逐字比必然失败。剥到只剩字母数字
    之后两边才可比，而这一步不会把不同厂牌压成同一个串——`moodyz` 和 `madonna` 剥完仍然不同。
    """
    return re.sub(r"[^0-9a-z]", "", text.lower())


def slugs(name: str) -> list[str]:
    """厂牌名 → 候选域名主体，长的在前。"""
    words = [w for w in re.split(r"[^0-9A-Za-z]+", name) if w]
    if not words:
        return []
    joined = "".join(words).lower()
    hyphened = "-".join(words).lower()
    out = [joined]
    if hyphened != joined:
        out.append(hyphened)
    return out


def candidate_urls(name: str) -> list[str]:
    """按 JAV 厂牌官网的实际域名习惯排序：`.com` 最常见，其次 `.jp`、`-av`、`.tv`。

    不再为每个域名各试一遍 `www.` 前缀。两个 transport 都开着 `follow_redirects`，
    只用 `www.` 的站会从裸域跳过来；而裸域连不上时 `www.` 基本也连不上，多出来的那一半
    候选几乎只在**失败**路径上产生开销——首轮实测正是这样：57 个厂牌 × 8 个候选，
    死域名每个吃掉 connect 与 read 各一份超时，整批跑了三个多小时还没完。
    候选减半后同一批是分钟级。
    """
    urls: list[str] = []
    for slug in slugs(name):
        for host in (f"{slug}.com", f"{slug}.jp", f"{slug}-av.com", f"{slug}.tv"):
            url = f"https://{host}/"
            if url not in urls:
                urls.append(url)
    return urls


def decode(body: bytes) -> str:
    """按日站的实际编码分布解码。

    UTF-8 之外仍有相当一部分老厂牌站是 Shift_JIS。用 `errors="replace"` 硬解只会把标题
    变成一串 U+FFFD——那不会报错，只会让「标题里没有厂牌名」这条判定误杀掉真官网。
    所以先试 UTF-8，出现替换字符再按 cp932、euc-jp 依次重试，取替换字符最少的那个。
    """
    best, best_bad = "", None
    for encoding in ("utf-8", "cp932", "euc-jp"):
        try:
            text = body.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
        bad = text.count("�")
        if bad == 0:
            return text
        if best_bad is None or bad < best_bad:
            best, best_bad = text, bad
    return best or body.decode("utf-8", "replace")


def page_title(body: bytes) -> str:
    match = TITLE.search(decode(body))
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", " ", match.group(1))
    return re.sub(r"\s+", " ", text).strip()[:120]


def site_verdict(name: str, status: int, body: bytes, title: str,
                 url: str = "", derived_hosts: frozenset[str] = frozenset(),
                 ) -> tuple[str, str]:
    """这一页认不认自己是这个厂牌。

    四道都必须过：HTTP 200、不是空壳、不是停放页、标题里出现厂牌名且不只是域名回显。
    缺任何一道都写成未取得而不是「大概是」——一个错的官网会被下游当成社媒 handle 的
    来源，把别人的账号安到这个厂牌头上。
    """
    if status != 200:
        return "未取得", f"HTTP {status}"
    if len(body) < MIN_BODY:
        return "未取得", f"页面只有 {len(body)} 字节，疑似空壳"
    if PARKED_TITLE.search(title):
        return "未取得", f"标题自述在出售域名（{title[:44]}）"
    text = decode(body)
    # 不再截窗口。实测停放页把「domain for sale」写在第 81683 字节，任何固定窗口都会漏；
    # 整篇扫一遍在这个量级上不值得省。
    if PARKED.search(text):
        return "未取得", "停放页或域名出售页"
    # 标题不比域名多说任何东西，就等于没有自述身份。实测 `prestige.com` 返回 200、
    # 不是停放页、标题正好是 `prestige.com`——它因此通过了「标题含厂牌名」，被判成
    # Prestige 官网，而真站是 `prestige-av.com`，那是另一家公司。停放页规则拦不住它：
    # 它是个正常的站，只是不属于这个厂牌。
    host = (urlsplit(url).hostname or "").casefold().removeprefix("www.")
    title_token = normalise(title)
    if host and title_token and title_token in normalise(host):
        return "未取得", f"标题只是域名回显，没有自述身份（{title[:40]}）"
    token = normalise(name)
    if not token:
        return "未取得", "厂牌名里没有可比对的字母数字"
    adult = bool(ADULT.search(text))
    if token in normalise(title):
        if adult:
            return "ok", "标题自述厂牌名，且页面是成人站"
        # 同名的无关公司到这里为止和真站没有任何可区分之处，所以只能交给人看，
        # 不能算已确认——一条错的官网会被下游当成社媒 handle 的来源。
        return "weak", f"标题有厂牌名但页面不像成人站；需人工确认（{title[:40]}）"
    # 日站普遍把品牌名写成假名：`本中`、`無垢`、`ダスッ`、`グローリークエスト`。拿账本里的
    # 拉丁名去比标题，对这一整类真站必然对不上——`honnaka.jp` 的标题是
    # 「年齢チェック | 全作品、本物中出しのAVメーカー【本中】公式サイト」。这是系统性漏判，
    # 不是个别情况。
    #
    # 这时两个独立信号同样成立：域名是由厂牌名按固定规则推出来的（不是人喂的），
    # 且这一页确实是成人站。`bazooka.com`、`madonna.com` 恰好卡在第二条上——
    # 域名同样推得出，但它们不是成人站。
    # 判据落在**最终**主机上。实测 `Natural High` 的一个推导域名重定向去了
    # `linkedin.com/in/fareedkhan`，按请求地址判就成了「域名由厂牌名推出」，
    # 一个 LinkedIn 个人主页因此被确认成厂牌官网。跳走之后这条证据就不再成立。
    if host in derived_hosts and adult:
        return "ok", "域名由厂牌名推出，且页面是成人站（标题用假名写品牌名）"
    if token in normalise(text[:20000]):
        return "weak", "标题未自述，但正文出现厂牌名；需人工看图确认"
    return "未取得", f"标题与正文都没有厂牌名（标题：{title[:40] or '无'}）"


def load_studios(connection: sqlite3.Connection, minimum: int) -> list[dict]:
    return [{"entity_id": row[0], "studio": row[1], "assets": row[2]}
            for row in connection.execute(
                "SELECT e.id,e.canonical_name,count(DISTINCT ae.asset_id) n "
                "FROM entity e JOIN asset_entity ae ON ae.entity_id=e.id "
                "JOIN asset a ON a.id=ae.asset_id "
                "WHERE e.kind='studio' AND a.medium='video' "
                "GROUP BY e.id HAVING n>=? ORDER BY n DESC", (minimum,))]


def crawler_client() -> "httpx.Client":
    """本作业专用 client。**每个请求新建一个，用完立刻关掉**，见 `probe`。

    共享 `HttpxTransport` 的默认池是给反复访问同几个来源的连接器调的；本脚本要打
    两百多个**互不相同**的主机，其中大多数根本不存在。实测这种形态下失败的连接会漏掉
    池槽：下面这段真实序列里，第 4 个请求之后同一个 client 上的一切都 `PoolTimeout`，
    连第 13 个 `moodyz.com` 这种 0.3 秒就能取到 200 的站也一样。

        1 fc2ppv.com    ConnectError     4 fc2ppv.tv  200      13 moodyz.com  PoolTimeout
        2 fc2ppv.jp     ConnectTimeout   6 fc2-ppv.jp PoolTimeout

    把这种失败当结论，就会得出「一半厂牌没有官网」——前两轮 49/53 和 44/50 条失败
    全是它。调大或调小池子只决定它第几个请求崩，不解决问题；换成每请求一个新 client
    后同一段序列 7 成功 9 失败、`PoolTimeout` 为 0，失败全是真实的连接结果。

    代价只是每次多建一个 client，在 0.8 秒的请求间隔下可以忽略。不改共享默认值——
    那会伤到真正需要复用连接的连接器。
    """
    return httpx.Client(
        follow_redirects=True,
        limits=httpx.Limits(max_connections=4, max_keepalive_connections=0),
        headers={"User-Agent": USER_AGENT},
    )


def probe(url: str, timeout: float) -> tuple[int, bytes, str]:
    """取一个候选。连接池不跨请求存活，理由见 `crawler_client`。"""
    http = HttpxTransport(crawler_client())
    try:
        response = http(HttpRequest("GET", url, {"User-Agent": USER_AGENT}), timeout, 4 << 20)
        return response.status, response.body, response.url or url
    finally:
        http.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=Path, help="人工查到的 studio,site 表，优先于推导域名")
    parser.add_argument("--min-assets", type=int, default=3)
    parser.add_argument("--interval", type=float, default=1.2)
    # httpx 把这个标量同时用作 connect 与 read 超时，死域名因此最多吃两份。首轮用 20
    # 秒的代价是整批三个多小时；真站实测都在 2 秒内响应，8 秒已经宽裕得多。
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--limit", type=int, default=0)
    # `job_main` 直接读 args.lock，没有这一行会在拿锁时才 AttributeError。
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".studio-sites.lock")
    return parser


def run(args) -> int:
    import hashlib

    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    try:
        studios = load_studios(connection, args.min_assets)
    finally:
        connection.close()
    if args.limit:
        studios = studios[:args.limit]

    seeds: dict[str, list[str]] = {}
    if args.seeds:
        for row in read_rows(args.seeds):
            site = (row.get("site") or "").strip()
            if site:
                seeds.setdefault((row.get("studio") or "").strip(), []).append(site)

    results: list[dict[str, object]] = []
    last = 0.0
    for record in studios:
        name = record["studio"]
        row = {field: "" for field in FIELDS}
        row.update(record)
        row["verdict"], row["note"] = "未取得", "没有可推导的候选域名"
        # 人工喂的种子和规则推出来的候选走同一条验证，但要分得清哪个是哪个：
        # 「域名由厂牌名推出」只有在域名真的是推出来的时候才算一个独立信号。
        derived_urls = candidate_urls(name)
        derived_hosts = frozenset(
            (urlsplit(u).hostname or "").casefold().removeprefix("www.") for u in derived_urls)
        for url in seeds.get(name, []) + derived_urls:
            wait = args.interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                status, body, final = probe(url, args.timeout)
            except Exception as exc:
                row.update(candidate_url=url, verdict="未取得",
                           note=f"取不到：{type(exc).__name__}")
                continue
            title = page_title(body)
            verdict, note = site_verdict(name, status, body, title, final,
                                         derived_hosts=derived_hosts)
            row.update(candidate_url=url, final_url=final, status=status,
                       bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                       title=title, verdict=verdict, note=note)
            if verdict in {"ok", "weak"}:
                break
        results.append(row)
        print(f"{name[:22]:<22} {row['verdict']:<6} {str(row['final_url'])[:38]:<38} "
              f"{str(row['title'])[:34]}")

    write_rows(args.output, FIELDS, results)
    counts: dict[str, int] = {}
    for row in results:
        counts[str(row["verdict"])] = counts.get(str(row["verdict"]), 0) + 1
    print({"total": len(results), **counts, "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(job_main(build_parser, run))
