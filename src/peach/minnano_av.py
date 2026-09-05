r"""minnano-av 的页面解析：检索、女优资料表、事务所名册。

这个站是目前唯一能从女优名走到社媒、事务所和「这家事务所有哪些人」的入口
（`docs/reference-snapshots/minnano-av-official-portraits.md`）。解析规则本来长在
`scripts/harvest_performer_links.py` 里，名册采集要用同一套，所以搬到这里；
两个脚本共用一份，改站点结构时只有一处要改。

**只采信重定向。** `search_result.php?search_scope=actress&search_word=<名字>` 有三种
结果：唯一命中会跳到 `actressNNN.html`；多命中或无命中都停在检索页。检索页正文里同样
有一堆 `actressNNN.html`，那是「相关女优」，按正文解析会把别人的社媒安到这个人头上——
信号只在最终地址里。

**资料表的站内链接不是这个人的链接，却正是名册的入口。** 表里的值形如
`<td><span>标签</span><p>值</p></td>`；「所属事務所」那一格的 `<a>` 指向
`actress_list.php?production=134`，那个数字就是这家事务所在站内的编号。
`profile_fields` 按「绝对 URL 才算外链」把它挡在外面是对的——但编号得单独取出来
（`production_ref`），否则名册页根本无从进入。

**名册页读 JSON-LD，不读正文。** 页面自己带一份 `CollectionPage`：`numberOfItems`
是这家的总人数，`itemListElement` 每项给 `name` 和 `actressNNN.html`。正文里那几个
`<a>` 的文字是 `鈴北梨乃女優情報`——把「女優情報」当名字的一部分拿去和账本对名字，
一个都对不上。翻页也不猜 `&page=N`：`<link rel="next">` 就在头里，没有它就是最后一页。
"""
from __future__ import annotations

import html as html_entities
import json
import re
from urllib.parse import quote, urljoin, urlsplit

SEARCH = "https://www.minnano-av.com/search_result.php?search_scope=actress&search_word="
SITE = "https://www.minnano-av.com/"
ACTRESS_PAGE = re.compile(r"/actress(\d+)\.html")
FIELD = re.compile(r"<td[^>]*>\s*<span[^>]*>(.*?)</span>(.*?)</td>", re.S)
HREF = re.compile(r'href=["\']([^"\']+)["\']')
_PRODUCTION = re.compile(r'href=["\'][^"\']*production=(\d+)[^"\']*["\'][^>]*>(.*?)</a>', re.S)
_LD_JSON = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
_NEXT = re.compile(r'<link[^>]+rel=["\']next["\'][^>]+href=["\']([^"\']+)["\']', re.I)


def search_url(name: str) -> str:
    return SEARCH + quote(name, encoding="utf-8")


def roster_url(production: str | int, page: int = 1) -> str:
    """这家事务所的名册页。第一页不带 `page=`，和站点自己的 canonical 保持一致。"""
    tail = f"&page={page}" if page > 1 else ""
    return f"{SITE}actress_list.php?production={production}{tail}"


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


def production_ref(html: str) -> tuple[str, str]:
    """女优页的「所属事務所」→ (站内编号, 站上写的事务所名)；这一格没有链接就是 ("", "")。

    编号是名册页唯一的入口。名字一并取回来，用来核对这个编号确实是那家事务所——
    只凭一个数字装上去，装错了在复核件上看不出来。
    """
    for match in FIELD.finditer(html):
        if re.sub(r"<[^>]+>", "", match.group(1)).strip() != "所属事務所":
            continue
        found = _PRODUCTION.search(match.group(2))
        if not found:
            return "", ""
        return found.group(1), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", found.group(2))).strip()
    return "", ""


def roster_page(html: str, url: str = SITE) -> tuple[list[tuple[str, str]], int, str]:
    """名册页 → ([(女优名, 女优编号), ...], 这家的总人数, 下一页地址)。

    总人数是站点自己声明的 `numberOfItems`，用来对账：翻完所有页拿到的条数和它对不上，
    说明翻页断在中间，那是「没采全」而不是「这家就这么多人」。
    """
    people: list[tuple[str, str]] = []
    total = 0
    for block in _LD_JSON.findall(html or ""):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for node in data if isinstance(data, list) else [data]:
            if not isinstance(node, dict) or node.get("@type") != "CollectionPage":
                continue
            listing = node.get("mainEntity") or {}
            total = max(total, int(listing.get("numberOfItems") or 0))
            for item in listing.get("itemListElement") or []:
                person = (item or {}).get("item") or {}
                name = str(person.get("name") or "").strip()
                found = actress_id(str(person.get("url") or ""))
                if name:
                    people.append((name, found))
    following = _NEXT.search(html or "")
    if not following:
        return people, total, ""
    # 属性里的 `&amp;` 要还原成 `&`，否则下一页地址成了
    # `...production=134&amp;page=2`：服务端认不出 `amp;page`，照样回第一页，
    # 而每翻一次这段又长一截，看起来像在翻页，实际是同一页抄了七遍。
    return people, total, urljoin(url, html_entities.unescape(following.group(1)))
