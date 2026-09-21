"""一本道（1pondo.tv）官网作品 JSON 的解析。

无码番号在 JAV 目录站上要么没有、要么给的是转售商的上架日：`092415_001` javdb 报
2016-06-16，而番号自己写着 2015-09-24。发行方自己那一页才是正主，而且不用解析 HTML——
站点前端读的就是 `dyn/phpauto/movie_details/movie_id/<id>.json`，一次请求给标题、说明、
女优（日文与罗马字）、系列、发行日、时长和站内标签，不要凭据。

番号的分隔符是片商标识（`catalog_rules.normalise_code_key`）：一本道写 `112312_478`，
カリビアンコム 写 `040221-001`。两家都按 `MMDDYY_nnn` 编号，光看番号分不出是谁家的，
所以问哪一家由调用方按这一行的证据决定（`library_processing._sources_for`），本模块只
负责把番号写成官网认的形状并核对返回的 `MovieID`。

封面只有站点自己那张 16:9 剧照（`str.jpg`，实测 960×540）。无码片商不出封套，`thum_b.jpg`
是 120×197 的列表缩略图，两者都不是 JAV 那种竖版封面；取大的那张。

只解析传进来的 JSON，不联网：抓取由 `library_processing` 那一侧负责。
"""
from __future__ import annotations

import json
import re

from .catalog_rules import is_uncensored_code

ROOT = "https://www.1pondo.tv"
SOURCE = "1pondo"
DETAIL_URL = ROOT + "/dyn/phpauto/movie_details/movie_id/{movie_id}.json"
PAGE_URL = ROOT + "/movies/{movie_id}/"

#: 账本里这批作品的厂牌就叫这个（`一本道`），新抓的跟着走，免得同一家分裂成两个实体。
STUDIO = "一本道"

#: 站上的作品名写作 `112312_478`；账本里同一部片可能写成 `112312-478`，那是压制组的
#: 文件名带进来的。
_DATED = re.compile(r"^(\d{6})[-_](\d{2,4})$")
#: 一本道自己在页面上标着「1pon」，作品目录、文件名与账本的 studio 都用得上这几个写法。
_OWN_MARKS = ("1pon", "一本道", "1pondo")


def movie_id(code: str) -> str:
    """账本番号 → 官网作品号。不是日期式番号的回空串。"""
    found = _DATED.match(str(code or "").strip())
    if not found or not is_uncensored_code(f"{found.group(1)}_{found.group(2)}"):
        return ""
    return f"{found.group(1)}_{found.group(2)}"


def detail_url(code: str) -> str:
    """这个番号的作品 JSON 地址；认不出作品号时回空串。"""
    found = movie_id(code)
    return DETAIL_URL.format(movie_id=found) if found else ""


def names_this_studio(*evidence: str) -> bool:
    """这几段文字（路径、文件名、账本厂牌）里有没有说这部片是一本道的。

    日期式番号本身不带片商，拿另一家的番号去问官网，答回来的是同一天发行的另一部片。
    所以只在本机已有证据指着一本道时才问它，问不着的照旧走社区来源。
    """
    text = " ".join(str(item or "") for item in evidence).lower()
    return any(mark.lower() in text for mark in _OWN_MARKS)


def _actresses(raw: dict) -> list[dict]:
    """女优。日文名是账本的身份写法，罗马字作别名跟着走。"""
    japanese = [str(name).strip() for name in raw.get("ActressesJa") or [] if str(name).strip()]
    english = [str(name).strip() for name in raw.get("ActressesEn") or []]
    if not japanese:
        japanese = [name for name in [str(raw.get("Actor") or "").strip()] if name]
    found = []
    for index, name in enumerate(japanese):
        romaji = english[index] if index < len(english) else ""
        found.append({"japanese_name": name, "name_romaji": romaji})
    return found


def _cover(raw: dict) -> str:
    """站上那张剧照。四个 Thumb 字段实测同一个地址，按大到小取第一个给出来的。"""
    for field in ("ThumbUltra", "ThumbHigh", "ThumbMed", "ThumbLow", "MovieThumb"):
        url = str(raw.get(field) or "").strip()
        if url:
            return url
    return ""


def parse_details(document: str | bytes | dict, code: str) -> dict | None:
    """作品 JSON → 与 `extract_peach_fields` 兼容的 payload；对不上番号回 None。

    下架的作品官网直接回 404，那一档由抓取那侧判成「没有」。
    """
    wanted = movie_id(code)
    if not wanted:
        return None
    raw = document if isinstance(document, dict) else json.loads(document or "null")
    if not isinstance(raw, dict) or str(raw.get("MovieID") or "").strip() != wanted:
        return None
    duration = raw.get("Duration")
    return {
        "id": wanted,
        "content_id": wanted,
        "source_url": PAGE_URL.format(movie_id=wanted),
        "title": str(raw.get("Title") or "").strip(),
        "description": str(raw.get("Desc") or "").strip(),
        "release_date": str(raw.get("Release") or "").strip(),
        # 官网按秒记时长，账本按分钟。
        "runtime": round(duration / 60, 2) if isinstance(duration, (int, float)) and duration > 0 else None,
        "actresses": _actresses(raw),
        "maker": STUDIO,
        "series": str(raw.get("Series") or "").strip(),
        "genres": [str(name).strip() for name in raw.get("UCNAME") or [] if str(name).strip()],
        "cover_url": _cover(raw),
        "cover_urls": [url for url in [_cover(raw)] if url],
    }
