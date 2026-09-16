"""口径变了之后已经过期的资料候选。

候选文件是抓取那一刻的产物。抓取口径改了——genre 现在取 r18 combined 页的日文原词，
不再取它译过一层的英文——之前写下的那些候选不会自己跟上，它们记的仍是英文词。表里
补词也救不了：`Sex Toy`、`Ahegao` 这些词根本不在任何一张表里，要日文只能重抓一次。

判据只认一件事：这条候选的未收录 genre 里有没有整串 ASCII 的词。日文原词永远不是
ASCII，所以这一条既认得出「英文那层留下的」，又不会误伤「日文里确实还没收录的」。
"""
from __future__ import annotations

import json
from typing import Iterable

#: 会给出英文 genre 的来源。别的来源（javbus、dmm、mgstage）本来就返回日文。
ENGLISH_GENRE_SOURCES = frozenset({"r18dev"})


def _is_english(word: str) -> bool:
    return bool(word) and word.isascii()


def stale_genre_rows(rows: Iterable[dict]) -> list[dict]:
    """这些候选行的 genre 还停在英文那一层，重抓一次才会变成日文原词。"""
    stale = []
    for row in rows:
        if row.get("field") != "tags":
            continue
        try:
            candidates = json.loads(row.get("candidates_json") or "[]")
        except ValueError:
            continue
        if any(candidate.get("source") in ENGLISH_GENRE_SOURCES
               and any(_is_english(word) for word in candidate.get("unmapped_genres") or [])
               for candidate in candidates):
            stale.append(row)
    return stale


def without(rows: Iterable[dict], dropped: Iterable[dict]) -> list[dict]:
    """去掉这些行之后的候选表。按 `item_key` 认，CSV 里它就是这一行的身份。"""
    keys = {row["item_key"] for row in dropped}
    return [row for row in rows if row["item_key"] not in keys]
