"""FC2 内容市场（adult.contents.fc2.com）与镜像站 fc2cmadb 的作品页解析。

FC2 不是 JAV：番号是卖家自己的投稿号，JAV 目录站按它去查要么没有，要么撞上别的片。
r18.dev 对 FC2 实测 85 条问了 85 条全空；AVBase 与 JavBus 对本地这批番号一律回「没有
这个番号」；javdb 有页面但配额紧。发行方自己那一页才是这批番号的正主：不要凭据、
一次请求给全标题、说明、卖家、商品标签、时长、販売日和封面原图。

页面主体在 `<script type="application/ld+json">` 的 Product 里，正文 DOM 只补它没有的
那几项。下架的商品仍回 200，靠正文里没有 Product 判定，不当成抓取失败。

下架的商品在 fc2cmadb 上还留着：它是个 Laravel + Inertia 的镜像站，整棵 props 树放在
`<script type="application/json">` 里，免登录就能读，字段与商品页一一对得上——本地那批
没封面的 FC2 多半只能从这里取（实测 `FC2-PPV-3189161` 官方页已空，镜像给出 3456×1942
的原图）。两处的封面都指向 `storage*.contents.fc2.com` 上的同一个文件，镜像有时给的是
`contents-thumbnail*.fc2.com/w276/` 包装过的缩略图地址，`_storage_original` 把包装拆掉。

带分段后缀的番号（`FC2-PPV-3312576-1`）在这里一律认不出商品号，于是一处都不问。那是
对的：合集的封面套给每个分段，屏幕上就是 21 个不同内容顶着同一张图。

演员不取。商品页没有演员栏，标题里那个名字是卖家自己写的宣传语，`みお(19)` 这样的
写法既不是艺名也没有第二处可以印证；FC2 的演员线索在 fc2cmadb 的评论区，那是另一条路
（`scripts/fetch_fc2_metadata.py`）。

只解析传进来的 HTML，不联网：抓取由 `library_processing` 那一侧负责。
"""
from __future__ import annotations

import json
import re
import urllib.parse

from bs4 import BeautifulSoup

ROOT = "https://adult.contents.fc2.com"
SOURCE = "fc2"
ARTICLE_URL = ROOT + "/article/{video_id}/"
USER_URL = ROOT + "/users/{slug}/"

MIRROR_ROOT = "https://fc2cmadb.com"
MIRROR_SOURCE = "fc2cmadb"
MIRROR_URL = MIRROR_ROOT + "/articles/{video_id}"

ARCHIVE_ROOT = "https://javarchive.com"
ARCHIVE_SOURCE = "javarchive"
ARCHIVE_SEARCH_URL = ARCHIVE_ROOT + "/search?q={code}"

#: 账本里 FC2 一律记在这个厂牌下（库内既有的 561 条就是它），新抓的跟着走，免得同一批
#: 内容分裂成两个厂牌实体。卖家是另一回事，它走 `label`：那是只作证据的目录字段，
#: 归不归实体由复核页上的人判断，解析器不替他决定。
STUDIO = "FC2-PPV"

_VIDEO_ID = re.compile(r"^FC2(?:[-_. ]?PPV)?[-_. ]?(\d{5,})$", re.I)
#: `41:50` 与 `1:23:45` 两种都有。
_RUNTIME = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})$")
_SOLD_ON = re.compile(r"販売日\s*[:：]\s*(\d{4})/(\d{2})/(\d{2})")
#: `https://contents-thumbnail2.fc2.com/w276/storage92000.contents.fc2.com/file/…`
#: 前半截是缩放服务，后半截就是原件地址。
_THUMBNAIL_WRAPPER = re.compile(
    r"^https?://contents-thumbnail\d*\.fc2\.com/w\d+/(storage[\w.-]+\.fc2\.com/.+)$", re.I)
#: JavArchive 的作品地址：`/926949-FC2-PPV-4137487-<标题>-pn.html`。开头那串是站内文章号，
#: 商品号夹在标题里，所以地址拼不出来，只能先搜。
_ARCHIVE_LINK = re.compile(r'href="(/\d+-[^"]+\.html)"')
#: 作品页上封面的两个位置：`div.fisrst_sc` 里那张排前，schema.org 的 `image` 排后。
#: 认位置不认文件名——转存者的命名没有统一：`4137487pl.jpg` 沿用 FC2 自己的 `pl`/`ps`，
#: `FC2PPV-4030617.jpg` 与 `FC2PPV-4030617-2.jpg` 是他自己起的，`FC2PPV835964-2.jpg`
#: 连连字符都省了。按名字认的话后两种一张都取不到（2026-09-22 实测 4 部里 3 部如此）。
_ARCHIVE_COVER_SLOTS = ("div.fisrst_sc img[src]", 'img[itemprop="image"][src]')
#: 多帧拼成的长条预览，正文里叫 `Preview(ビデオのサムネイル)`，不是封面。
_ARCHIVE_PREVIEW = re.compile(r"_s\.(?:jpe?g|png)$", re.I)
#: 正文那块资料：`标签：A｜B｜C`、`日期：2023/11/21`、`时长：50:03`，每项后面跟一个 `<br>`。
#: 只在 `div.news` 里搜：head 的 `<meta name="description">` 里有同样的字样，值被站方
#: 截断成 `…｜S級...`，跟着一串属性和标签，当成资料取回来就是一条坏值。
_ARCHIVE_ROWS = {
    "genres": re.compile(r"标签\s*[:：]\s*([^<]*)"),
    "release_date": re.compile(r"日期\s*[:：]\s*(\d{4})/(\d{2})/(\d{2})"),
    "runtime": re.compile(r"时长\s*[:：]\s*([\d:]+)"),
}


def video_id(code: str) -> str:
    """账本番号 → 商品号。认不出来的回空串，由调用方决定怎么处置。"""
    found = _VIDEO_ID.match(str(code or "").strip())
    return found.group(1) if found else ""


def canonical_code(video: str) -> str:
    """商品号 → 账本写法。"""
    digits = str(video or "").strip()
    return f"FC2-PPV-{digits}" if digits.isdigit() else ""


def article_url(code: str) -> str:
    """这个番号的商品页地址；认不出商品号时回空串。"""
    found = video_id(code)
    return ARTICLE_URL.format(video_id=found) if found else ""


def runtime_minutes(raw: str) -> float | None:
    match = _RUNTIME.match(str(raw or "").strip())
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    total = int(hours or 0) * 60 + int(minutes) + int(seconds) / 60
    return round(total, 2) if total > 0 else None


def _product(soup: BeautifulSoup) -> dict | None:
    """页面里那份 Product。下架的商品这一段整个不出现。"""
    for node in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(node.string or "")
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            return data
    return None


def _text(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node is not None else ""


def parse_article(html: str | bytes, code: str) -> dict | None:
    """商品页 → 与 `extract_peach_fields` 兼容的 payload；已下架或对不上番号回 None。

    番号要核：`article/<id>/` 取不到商品时 FC2 回的是一个 200 的「見つかりませんでした」页，
    而站上的商品号会被复用给别的投稿，不核就会把另一部片的资料写到这个番号头上。
    """
    wanted = video_id(code)
    if not wanted:
        return None
    soup = BeautifulSoup(html, "html.parser")
    product = _product(soup)
    if product is None or str(product.get("sku") or "").strip() != wanted:
        return None
    image = product.get("image")
    #: 商品图有两处：正文那张是 `w276` 缩略图，Product 里这个是存储原件（实测
    #: 2350×2352）。取原件，缩略图连封面的最低宽度都过不了。
    cover = _storage_original((image or {}).get("url")) if isinstance(image, dict) else ""
    brand = product.get("brand")
    seller = brand if isinstance(brand, dict) else {}
    tags = [_text(node) for node in soup.select(".items_article_TagArea a")]
    sold = _SOLD_ON.search(soup.get_text(" ", strip=True))
    return {
        "id": canonical_code(wanted),
        "content_id": wanted,
        "source_url": ARTICLE_URL.format(video_id=wanted),
        "title": str(product.get("name") or "").strip(),
        "description": str(product.get("description") or "").strip(),
        "release_date": "-".join(sold.groups()) if sold else "",
        "runtime": runtime_minutes(_text(soup.select_one("p.items_article_info"))),
        "actresses": [],
        "maker": STUDIO,
        # 卖家在站上既有名字也有主页；名字空着时退回主页地址，别把这一栏丢掉。
        "label": _seller_name(soup) or str(seller.get("url") or "").strip(),
        "seller_url": str(seller.get("url") or "").strip(),
        "genres": list(dict.fromkeys(tag for tag in tags if tag)),
        "cover_url": cover,
        "cover_urls": [cover] if cover else [],
    }


def _seller_name(soup: BeautifulSoup) -> str:
    """卖家名。Product 的 `brand.name` 实测常是 null，站上写在头部那个指向用户页的链接里。"""
    link = soup.select_one('.items_article_headerInfo a[href*="/users/"]')
    return _text(link)


def mirror_url(code: str) -> str:
    """这个番号在 fc2cmadb 上的地址；认不出商品号时回空串。"""
    found = video_id(code)
    return MIRROR_URL.format(video_id=found) if found else ""


def archive_search_url(code: str) -> str:
    """这个番号在 JavArchive 上的搜索地址；认不出商品号时回空串。"""
    found = video_id(code)
    return ARCHIVE_SEARCH_URL.format(code=urllib.parse.quote(canonical_code(found))) if found else ""


def archive_link(html: str | bytes, code: str) -> str:
    """搜索结果里这个商品号那一条的站内地址；没有回空串。

    商品号要按数字边界比：`4137487` 不能命中 `41374870`，站上两个号真的都有。搜索页的
    结果、侧栏的本周热门和归档菜单用的是同一种地址形状，所以只认地址里带着这个号的那条。
    """
    wanted = video_id(code)
    if not wanted:
        return ""
    text = html.decode("utf-8", "replace") if isinstance(html, bytes) else str(html)
    boundary = re.compile(rf"(?<!\d){re.escape(wanted)}(?!\d)")
    for href in _ARCHIVE_LINK.findall(text):
        if boundary.search(urllib.parse.unquote(href)):
            return href
    return ""


def _strip_code(title: str, wanted: str) -> str:
    """标题开头那截番号剥掉：站上 `FC2-PPV-4137487`、`FC2PPV 1863914` 两种写法都有。"""
    return re.sub(rf"^\s*FC2[-_. ]?(?:PPV)?[-_. ]?{re.escape(wanted)}\s*[-—:：]?\s*", "",
                  str(title or ""), flags=re.I)


def parse_archive(html: str | bytes, code: str) -> dict | None:
    """JavArchive 的作品页 → 同一份 payload 形状；对不上番号回 None。

    这一档给标题、封面，以及正文那块资料里转存者填了的标签、发行日和时长。填不填是他的
    自由：2026-09-22 实测 4 部里只有 `4030617` 三样齐全（10 个标签、2023/11/21、50:03），
    另外三部那一块整个空着。卖家和商品说明站上没有，正文余下几段是转载来的网盘链接，
    一概不取。封面比官方存储那份原图差一档，所以这一档排在 fc2cmadb 后面。

    封面认位置不认文件名。站上三种命名都有——`4137487pl.jpg` 沿用 FC2 自己的 `pl`/`ps`，
    `FC2PPV-4030617.jpg` 与 `FC2PPV835964-2.jpg` 是转存者自己起的——按名字认的话后两种
    一张都取不到，`4030617` 与 `2110084` 此前就是这样空着回来的。两个图位都收，去重后
    `div.fisrst_sc` 那张排前：实测它是作品自己的封面，schema.org 的 `image` 常是同一张的
    另一版本。`_s.jpg` 结尾的排除掉，那是正文里标着 `Preview` 的多帧长条拼图。

    标题以站内 `<h1>` 为准，开头那截番号剥掉：站上 `FC2-PPV-4137487`、`FC2PPV 1863914`
    两种写法都有，留着就把番号写进了标题。`<h1>` 里认不出这个商品号就当没有这一页——
    搜索结果挑错条、或者站点改版换了结构，两种都不该把别的片的标题安上来。
    """
    wanted = video_id(code)
    if not wanted:
        return None
    text = html.decode("utf-8", "replace") if isinstance(html, bytes) else str(html)
    soup = BeautifulSoup(text, "html.parser")
    heading = soup.select_one("h1")
    title = _text(heading)
    if not title or not re.search(rf"(?<!\d){re.escape(wanted)}(?!\d)", title):
        return None
    link = heading.select_one("a[href]")
    covers = []
    for slot in _ARCHIVE_COVER_SLOTS:
        for picture in soup.select(slot):
            url = str(picture.get("src") or "").strip()
            if url and not _ARCHIVE_PREVIEW.search(url) and url not in covers:
                covers.append(url)
    rows = _archive_rows(soup)
    return {
        "id": canonical_code(wanted),
        "content_id": wanted,
        "source_url": urllib.parse.urljoin(ARCHIVE_ROOT, link["href"]) if link else "",
        "title": _strip_code(title, wanted),
        "description": "",
        "release_date": rows["release_date"],
        "runtime": runtime_minutes(rows["runtime"]),
        "actresses": [],
        "maker": STUDIO,
        "label": "",
        "seller_url": "",
        "genres": rows["genres"],
        "cover_url": covers[0] if covers else "",
        "cover_urls": covers,
    }


def _archive_rows(soup: BeautifulSoup) -> dict:
    """正文那块资料：标签、发行日、时长。哪一样没填就回这一样的空值。

    只在 `div.news` 里搜。整页搜的话 head 里那条 `<meta name="description">` 会先命中：
    站方把同一段话截断成 `…｜S級...` 写进 `content`，取回来的是半截标签加一串属性。
    """
    block = soup.select_one("div.news")
    if block is None:
        return {"genres": [], "release_date": "", "runtime": ""}
    text = str(block)
    tags = _ARCHIVE_ROWS["genres"].search(text)
    sold = _ARCHIVE_ROWS["release_date"].search(text)
    runtime = _ARCHIVE_ROWS["runtime"].search(text)
    # 站上用全角竖线分隔；转存者留空时那一行写成 `--`，当成一个标签就入了库。
    names = [name.strip() for name in re.split(r"[｜|]", tags.group(1))] if tags else []
    return {
        "genres": list(dict.fromkeys(name for name in names if name and name != "--")),
        "release_date": "-".join(sold.groups()) if sold else "",
        "runtime": runtime.group(1) if runtime else "",
    }


def _storage_original(url: str) -> str:
    """缩略图地址 → 原件地址。已经是原件的原样返回。"""
    found = _THUMBNAIL_WRAPPER.match(str(url or "").strip())
    return f"https://{found.group(1)}" if found else str(url or "").strip()


def _inertia_props(soup: BeautifulSoup) -> dict:
    for node in soup.find_all("script", type="application/json"):
        try:
            data = json.loads(node.string or "")
        except ValueError:
            continue
        if isinstance(data, dict) and isinstance(data.get("props"), dict):
            return data["props"]
    return {}


def parse_mirror(html: str | bytes, code: str) -> dict | None:
    """fc2cmadb 的作品页 → 同一份 payload 形状；对不上番号回 None。

    站上没有的商品回 404，那一档由抓取那侧判成「没有」。演员同样不取：这一页正文里
    也没有演员栏，评论区那条线另走 `scripts/fetch_fc2_metadata.py`。
    """
    wanted = video_id(code)
    if not wanted:
        return None
    article = _inertia_props(BeautifulSoup(html, "html.parser")).get("article")
    if not isinstance(article, dict) or str(article.get("video_id") or "").strip() != wanted:
        return None
    writer = article.get("writer") if isinstance(article.get("writer"), dict) else {}
    slug = str(writer.get("slug") or "").strip()
    cover = _storage_original(article.get("image_url"))
    tags = [str((tag or {}).get("name") or "").strip() for tag in article.get("tags") or []]
    return {
        "id": canonical_code(wanted),
        "content_id": wanted,
        "source_url": MIRROR_URL.format(video_id=wanted),
        "title": str(article.get("title") or "").strip(),
        "description": "",
        "release_date": str(article.get("release_date") or "").strip(),
        "runtime": runtime_minutes(article.get("duration")),
        "actresses": [],
        "maker": STUDIO,
        "label": str(writer.get("name") or "").strip(),
        # 镜像的 slug 与官方用户页的 slug 是同一个（实测 `otonakamenz` 两处一致），
        # 所以这一栏指回发行方自己那一页，而不是镜像的作者页。
        "seller_url": USER_URL.format(slug=slug) if slug else "",
        "genres": list(dict.fromkeys(tag for tag in tags if tag)),
        "cover_url": cover,
        "cover_urls": [cover] if cover else [],
    }
