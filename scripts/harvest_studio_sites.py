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
from peach.scripting import USER_AGENT, open_readonly   # noqa: E402

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
# 站点自述打不开的标题。实测 `bangbus.com` 与 `monstersofcock.com` 都返回 200、82 KB、
# 正文里成人词一应俱全，标题却只有 `Site Unavailable`——「域名由厂牌名推出且是成人站」
# 那条因此把它们判成 ok。一页自己说自己不可用，就不能拿来当官网证据；这类页面还常常
# 是 CDN 或地区封锁的产物，换个出口再取才有意义，写成 ok 只会把它固化成结论。
BROKEN_TITLE = re.compile(
    r"site unavailable|service unavailable|temporarily unavailable|access denied"
    r"|forbidden|not found|bad gateway|under construction|coming soon"
    r"|maintenance|メンテナンス|工事中|しばらく(?:お待ち|お待たせ)", re.I)
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

#: 用户当场确认的母公司官网。**这不是放宽通用判据，是补一条页面上没有的信息。**
#:
#: `SOD Create` 是 Soft On Demand 的厂牌。母公司官网 `www.sod.co.jp` 实测 200、是成人站，
#: 标题却是 `SOFT ON DEMAND（ソフト・オン・デマンド）`——标题和正文里都不会出现
#: `SOD Create` 这个串，所以「标题自述厂牌名」和「正文提到厂牌名」两条都不成立，通用
#: 判据只能判未取得。缺的那一条是「这个厂牌属于哪家公司」，它本来就不在页面上，只有人知道。
#:
#: 因此走显式白名单，不去放宽通用判据：把「标题没有厂牌名也算」松开，`hunter.com`
#: （四轮定位）、`bazooka.com`（车载音响）、`madonna.com`（歌手）那一整类同名站会跟着
#: 一起被确认成官网。白名单只影响列出来的这几行，每行写清谁确认的、为什么通用路径不成立。
CONFIRMED_SITES: dict[str, tuple[str, str]] = {
    "SOD Create": (
        "https://www.sod.co.jp/",
        "用户 2026-09-03 确认：SOD Create 是 Soft On Demand 的厂牌，"
        "sod.co.jp 是母公司官网",
    ),
}

#: 发行平台不是厂牌，「厂牌官网」这条路对它们本来就不成立。
#:
#: 用户判据（见 `docs/SOURCING.md`）：FC2-PPV、myfans 这类是把别人的作品卖出去的平台；
#: 页面上有实际卖主（seller／出品者）的那个账号才是 creator，账本里已标注或评论里提到的
#: 女优属于 performer。所以拿 `fc2ppv.com` 这类推导域名去试，试出什么都不能写成 official：
#: 要么是抢注页，要么是平台入口，两者都不是「这个厂牌的官网」。
#:
#: 判词单列而不是静默跳过：少扫一个和「扫过但没找到」在复核件上长得一模一样，
#: 那正是这个仓库最常见的那类缺陷。名字按 `normalise` 比，写法差异（`FC2-PPV`／`FC2 PPV`）
#: 不影响命中。
PLATFORM_ENTITIES = frozenset({"fc2ppv", "fc2", "myfans"})
PLATFORM_VERDICT = "不适用（发行平台）"


def is_platform(name: str) -> bool:
    """这个账本名是发行平台而不是厂牌吗。"""
    return normalise(name) in PLATFORM_ENTITIES


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
                 confirmed: str = "") -> tuple[str, str]:
    """这一页认不认自己是这个厂牌。

    四道都必须过：HTTP 200、不是空壳、不是停放页、标题里出现厂牌名且不只是域名回显。
    缺任何一道都写成未取得而不是「大概是」——一个错的官网会被下游当成社媒 handle 的
    来源，把别人的账号安到这个厂牌头上。

    `confirmed` 是 `CONFIRMED_SITES` 里那句理由：它只替掉最后一道「页面得自述厂牌名」，
    前面几道照旧要过。
    """
    if status != 200:
        return "未取得", f"HTTP {status}"
    if len(body) < MIN_BODY:
        return "未取得", f"页面只有 {len(body)} 字节，疑似空壳"
    if PARKED_TITLE.search(title):
        return "未取得", f"标题自述在出售域名（{title[:44]}）"
    if BROKEN_TITLE.search(title):
        return "未取得", f"站点自述不可用（{title[:44]}）"
    text = decode(body)
    # 不再截窗口。实测停放页把「domain for sale」写在第 81683 字节，任何固定窗口都会漏；
    # 整篇扫一遍在这个量级上不值得省。
    if PARKED.search(text):
        return "未取得", "停放页或域名出售页"
    # 标题不比域名多说任何东西，就等于没有自述身份。实测 `prestige.com` 返回 200、
    # 不是停放页、标题正好是 `prestige.com`——它因此通过了「标题含厂牌名」，被判成
    # Prestige 官网，而真站是 `prestige-av.com`，那是另一家公司。停放页规则拦不住它：
    # 它是个正常的站，只是不属于这个厂牌。
    # 判据是「标题原样打印了域名，且除域名之外什么都没说」。拿 normalise 后的标题去匹配
    # normalise 后的主机会把真站一起打掉：`www.naturalhigh.co.jp` 返回 200、
    # 标题正是 `NATURAL HIGH（ナチュラルハイ）`，normalise 成 naturalhigh，必然是
    # naturalhighcojp 的一部分——域名由厂牌名推出来时这两者永远互相包含，这条规则于是
    # 对整类真站失效。域名回显的真正特征是标题里带着 TLD，品牌名不带。
    host = (urlsplit(url).hostname or "").casefold().removeprefix("www.")
    printed = title.casefold().strip()
    if host and host in printed and not re.sub(r"\W|_", "", printed.replace(host, "")):
        return "未取得", f"标题只是域名回显，没有自述身份（{title[:40]}）"
    # 用户确认的母公司官网。上面四道（状态码、空壳、停放页／自述不可用、域名回显）照旧
    # 要过：确认的是「这个地址属于这家公司」，不是「这个地址此刻返回的任何东西都算数」。
    # 白名单换掉的只有「页面得自述厂牌名」这一条——`SOD Create` 这个串本来就不会出现在
    # 母公司官网上，那条信息不在页面里。
    if confirmed:
        return "ok", f"{confirmed}；实测标题：{title[:40] or '无'}"
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


def load_named_studios(connection: sqlite3.Connection, names: list[str]) -> list[dict]:
    """`--only` 指名的厂牌，不看作品数。

    默认路径按作品数筛，是为了不去扫只出现过一两次的厂牌。指名时那条门槛恰好挡住要补的
    目标：BangBus、BangBros18 各只有 1 部视频，OPPAI、MonstersOfCock 各 2 部，都低于默认的
    3，因此至今一次都没被扫过。作品数仍然取出来写进复核件，只是不再当门槛。

    名字对不上就直接失败。指名的用法下静悄悄少扫一个，和「扫过但没找到」在复核件上长得
    一模一样——那正是这个仓库最常见的那类缺陷。
    """
    found: list[dict] = []
    missing: list[str] = []
    for name in names:
        row = connection.execute(
            "SELECT e.id,(SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae "
            "JOIN asset a ON a.id=ae.asset_id "
            "WHERE ae.entity_id=e.id AND a.medium='video') "
            "FROM entity e WHERE e.kind='studio' AND e.canonical_name=?", (name,)).fetchone()
        if row is None:
            missing.append(name)
            continue
        found.append({"entity_id": row[0], "studio": name, "assets": row[1]})
    if missing:
        raise SystemExit(f"账本里没有这些厂牌：{'、'.join(missing)}")
    return found


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


def probe(url: str, timeout: float, retries: int = 2, backoff: float = 2.0
          ) -> tuple[int, bytes, str]:
    """取一个候选。连接池不跨请求存活，理由见 `crawler_client`。

    传输层失败要重试，口径与 `page_cache.Site` 一致（两次、指数退避）。实测
    `www.naturalhigh.co.jp` 第一次 `ReadTimeout`、随后同一地址 200 且标题正是
    `NATURAL HIGH（ナチュラルハイ）`——一次抖动就被写成「这家没有官网」，而下游会把
    这个空结论当成事实。只重试传输层异常：HTTP 状态码是站点的回答，不是抖动。
    """
    for attempt in range(retries + 1):
        http = HttpxTransport(crawler_client(), owns_client=True)
        try:
            response = http(HttpRequest("GET", url, {"User-Agent": USER_AGENT}),
                            timeout, 4 << 20)
            return response.status, response.body, response.url or url
        except Exception:
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))
        finally:
            http.close()
    raise AssertionError("unreachable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="账本路径")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=Path, help="人工查到的 studio,site 表，优先于推导域名")
    parser.add_argument("--min-assets", type=int, default=3)
    parser.add_argument("--only", nargs="*", default=[],
                        help="只处理这几个厂牌，按 canonical_name 给；给了就不看作品数")
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

    connection = open_readonly(args.db)
    try:
        studios = (load_named_studios(connection, args.only) if args.only
                   else load_studios(connection, args.min_assets))
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
        if is_platform(name):
            # 一个请求都不发：这不是「查不到」，是这条路对发行平台本来就不成立。
            row["verdict"], row["note"] = PLATFORM_VERDICT, (
                "发行平台不是厂牌，没有「厂牌官网」可查；链接按平台登记，"
                "有实际卖主的账号才是 creator（docs/SOURCING.md）")
            results.append(row)
            print(f"{name[:22]:<22} {row['verdict']:<6}")
            continue
        confirmed = CONFIRMED_SITES.get(name)
        # 人工喂的种子和规则推出来的候选走同一条验证，但要分得清哪个是哪个：
        # 「域名由厂牌名推出」只有在域名真的是推出来的时候才算一个独立信号。
        derived_urls = candidate_urls(name)
        derived_hosts = frozenset(
            (urlsplit(u).hostname or "").casefold().removeprefix("www.") for u in derived_urls)
        # 每个候选的结果都记下来。让后一个候选覆盖前一个的话，一个厂牌试了六个地址、
        # 复核件上只剩最后那个的理由：`SOD Create` 写着「取不到：ConnectError」，
        # 而真正值得看的是被它盖掉的 `www.sod.co.jp` —— 200、成人站、标题
        # `SOFT ON DEMAND（ソフト・オン・デマンド）`。判成未取得可以，但要让人看得见
        # 是在哪几个地址上未取得。
        trail: list[str] = []
        # 确认过的地址排在最前：它是这家的答案，先试它就不必再把一串死域名走一遍。
        for url in ([confirmed[0]] if confirmed else []) + seeds.get(name, []) + derived_urls:
            wait = args.interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                status, body, final = probe(url, args.timeout)
            except Exception as exc:
                trail.append(f"{url} → 取不到：{type(exc).__name__}")
                if not row["candidate_url"]:
                    row.update(candidate_url=url, verdict="未取得",
                               note=f"取不到：{type(exc).__name__}")
                continue
            title = page_title(body)
            verdict, note = site_verdict(
                name, status, body, title, final, derived_hosts=derived_hosts,
                confirmed=confirmed[1] if confirmed and url == confirmed[0] else "")
            trail.append(f"{url} → {verdict}：{note}")
            # 取回了字节的候选比连不上的更值得留在行里：状态码、标题和 sha256 才是
            # 人能复核的证据。已经采信过一个 ok/weak 之后不再覆盖。
            if row["verdict"] not in {"ok", "weak"}:
                row.update(candidate_url=url, final_url=final, status=status,
                           bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                           title=title, verdict=verdict, note=note)
            if verdict in {"ok", "weak"}:
                break
        if row["verdict"] not in {"ok", "weak"} and len(trail) > 1:
            row["note"] = "；".join(trail)
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
    # 进度行里有日文标题，`ソフト・オン・デマンド` 的 `・` 在 GBK 控制台上编不出来，
    # 一个 print 就能把整批跑掀掉。证据在 CSV（UTF-8）里，进度行糊掉无所谓。
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(job_main(build_parser, run))
