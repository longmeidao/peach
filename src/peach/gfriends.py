"""Gfriends 头像图库的索引：目录约定、候选排序和本地缓存的读法。

图库把每个人的图分散在几十个来源目录下，一个人常有十几张。`Filetree.json` 是那棵
文件树的快照，键是展示名（可能是别名），值才是实际文件——两者未必相同。

**目录前缀是来源优先级，不是清晰度。** 上游 README 把它写成「质量升序」，但对着
来源表逐个核下来，实际规律是小而精在前、大而全在后：`0-` 是网友人工上传，`1-` 到
`8-` 是写真机构、经纪事务所和片商官方的原生大图，`8-` 往后是 Warashi、Javrave、
Minnano、FANZA 这些大型数据库，收录量上万但原图常常只有两三百像素、靠 AI 放大补上。
所以 `quality_key` 排出来的第一张是「最该先试的一张」，不是「最好看的一张」——
`0-Hand-Storage` 里混着写真封面和带名字水印的图，排第一只是因为它是人工投稿。

文件名的 `AI-Fix-` 前缀是上游自己做的 AI 放大与去水印；去掉前缀能取到未处理的原件。
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path

#: 图库的 raw 根。索引和图片都挂在它下面。
GFRIENDS_RAW = "https://raw.githubusercontent.com/gfriends/gfriends/master/"
#: 目录名首字符的先后。未知前缀排在最后，不能因为 `find` 返回 -1 反而抢到最前。
QUALITY_ORDER = "0123456789abcdefghijklmnopqrstuvwxyz"
#: 索引缓存的保鲜期。图库持续增补，缓存不能永不过期：只要文件在就一直复用的话，
#: 快照那天没收录的人会被判成「查不到」，此后每次重跑都照抄同一个结论。
#: 一天是个折中——图库按天更新，而取一次索引要 6 MB。
INDEX_MAX_AGE_SECONDS = 24 * 3600
#: 索引在缓存目录里的文件名。
INDEX_NAME = "gfriends-filetree.json"


def normalized(value: str) -> str:
    """名字的比对形态。只折叠空白并转小写，不做假名或新旧字体归一。"""
    return re.sub(r"\s+", " ", value or "").strip().lower()


def quality_key(category: str, filename: str) -> tuple[int, str, str]:
    """按目录前缀排先后；未知或空目录放最后。"""
    prefix = category[:1].lower()
    rank = QUALITY_ORDER.find(prefix)
    return (rank if rank >= 0 else len(QUALITY_ORDER), category, filename)


def category_label(category: str) -> str:
    """目录名去掉排序前缀后的样子，给人看。

    前缀那一位是图库自己的优先级记号（`quality_key` 读的就是它），对着屏幕选图的人
    读不出意思：剩下的 `S1`、`GRAPHIS`、`Attackers` 才是图源本身的名字。
    去掉前缀后为空的（目录名就那一位）退回原样，不给一个空标签。
    """
    trimmed = re.sub(r"^[0-9a-z]-", "", (category or "").strip(), flags=re.IGNORECASE)
    return trimmed or (category or "").strip()


def image_url(category: str, filename: str) -> str:
    return (GFRIENDS_RAW + "Content/" + urllib.parse.quote(category)
            + "/" + urllib.parse.quote(filename))


def parse_filetree(body: bytes) -> dict[str, list[tuple[str, str]]]:
    """`Filetree.json` 字节 → 名字映射到 [(来源目录, 文件名)]，最该先试的在前。"""
    content = json.loads(body)["Content"]
    index: dict[str, list[tuple[str, str]]] = {}
    for category, items in content.items():
        for display_name, stored in items.items():
            key = normalized(display_name.rsplit(".", 1)[0])
            index.setdefault(key, []).append((category, stored.split("?")[0]))
    for key in index:
        index[key].sort(key=lambda pair: quality_key(*pair))
    return index


def index_age(cache_dir: Path) -> float | None:
    """本地索引缓存有多旧，秒。没有缓存返回 None。"""
    try:
        return max(0.0, time.time() - (cache_dir / INDEX_NAME).stat().st_mtime)
    except OSError:
        return None


def load_index(cache_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """只读本地缓存的索引。取不到或坏了都返回空。

    联网补索引是长跑批处理的事（`scripts/audit_performer_portraits.py`）。页面这一侧
    宁可少列几个候选，也不该在一次点击里同步拉 6 MB。
    """
    try:
        return parse_filetree((cache_dir / INDEX_NAME).read_bytes())
    except (OSError, KeyError, TypeError, ValueError):
        return {}


def candidates(index: dict[str, list[tuple[str, str]]],
               names: list[str]) -> tuple[str, list[tuple[str, str]]]:
    """按名字链依次查索引，返回 (命中的名字, 候选)。一个都不命中就是 ("", [])。

    次序即匹配次序：先 canonical、再别名、最后本地化写法，第一个命中的就定下来。
    大陆简体与日文字体是两个不同的键（`横宫七海` 与 `横宮七海`），所以名字链必须
    带上别名——只拿规范名去查，汉字简化过的那些人一个也找不到。
    """
    for name in names:
        found = index.get(normalized(name))
        if found:
            return name, list(found)
    return "", []
