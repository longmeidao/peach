"""把账本里的退役标签名改成规范名。

名单是 `catalog_rules.RETIRED_TAGS`，一件事只留一个名字。写这一步的入口是
`scripts/rename_retired_tags.py`，本模块只提供判定与写入。
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlite3 import Connection

from .catalog_rules import RETIRED_TAGS
from .entities import merge_entity, normalize_entity_name

#: 原样记录来源怎么说的命名空间，不参与改名。
#:
#: `pixiv_tag` 是作者自己打的标签，和策展词表不是一回事：把它改成 Peach 的规范名，
#: 等于事后修改来源的原话，以后再也分不清哪些词是 pixiv 上真有的。页面上因此会留下
#: 几条退役名的残影（本机 `足控`、`臀部`、`高跟鞋` 各 2 条），那是它们的真实出处。
RAW_TAG_SOURCES = frozenset({"pixiv_tag"})

FIELDS = ("old", "new", "assets", "merged", "raw_kept", "entity")


def _placeholders(values) -> str:
    return ",".join("?" * len(values))


def collect(connection: Connection) -> list[dict]:
    """每个退役名在账本里的实际存量，按改动量从多到少。

    `merged` 是那一侧资产上两个名字都有的条数：改名会撞上 `UNIQUE(asset_id, tag)`，
    这种行只能删掉旧的，不然一次改名就要报一次冲突。
    """
    raw = sorted(RAW_TAG_SOURCES)
    holes = _placeholders(raw)
    rows = []
    for old, new in sorted(RETIRED_TAGS.items()):
        curated = connection.execute(
            f"SELECT count(*) FROM asset_tag WHERE tag=? AND source NOT IN ({holes})",
            (old, *raw)).fetchone()[0]
        merged = connection.execute(
            "SELECT count(*) FROM asset_tag a WHERE a.tag=? "
            f"AND a.source NOT IN ({holes}) "
            "AND EXISTS(SELECT 1 FROM asset_tag b WHERE b.asset_id=a.asset_id AND b.tag=?)",
            (old, *raw, new)).fetchone()[0]
        kept = connection.execute(
            f"SELECT count(*) FROM asset_tag WHERE tag=? AND source IN ({holes})",
            (old, *raw)).fetchone()[0]
        source_id = _entity_id(connection, old)
        entity = ""
        if source_id is not None:
            entity = "合并" if _entity_id(connection, new) is not None else "改名"
        rows.append({"old": old, "new": new, "assets": curated - merged, "merged": merged,
                     "raw_kept": kept, "entity": entity})
    rows.sort(key=lambda row: (-(row["assets"] + row["merged"]), row["old"]))
    # 两个退役名指向同一个标签时，先改的那个把实体造出来，后改的那个就只能合并。
    # 预览按 `apply_rows` 的顺序推一遍，报出来的才是真会发生的事。
    claimed: set[str] = set()
    for row in rows:
        if row["entity"] == "改名" and row["new"] in claimed:
            row["entity"] = "合并"
        if row["entity"]:
            claimed.add(row["new"])
    return rows


def _entity_id(connection: Connection, name: str) -> int | None:
    found = connection.execute(
        "SELECT id FROM entity WHERE kind='tag' AND normalized_name=?",
        (normalize_entity_name(name),)).fetchone()
    return int(found[0]) if found else None


def apply_rows(connection: Connection, rows: list[dict], now: str | None = None) -> dict:
    """按 `collect` 的结果改名。调用方负责事务与备份。"""
    stamp = now or datetime.now(timezone.utc).isoformat()
    raw = sorted(RAW_TAG_SOURCES)
    holes = _placeholders(raw)
    counts = {"tags": 0, "dropped": 0, "entities": 0}
    for row in rows:
        old, new = row["old"], row["new"]
        connection.execute(
            f"UPDATE OR IGNORE asset_tag SET tag=? WHERE tag=? AND source NOT IN ({holes})",
            (new, old, *raw))
        counts["tags"] += connection.execute("SELECT changes()").fetchone()[0]
        # 改不动的就是两个名字都有的那一侧，旧的这条已经没有信息了。
        connection.execute(
            f"DELETE FROM asset_tag WHERE tag=? AND source NOT IN ({holes})", (old, *raw))
        counts["dropped"] += connection.execute("SELECT changes()").fetchone()[0]
        counts["entities"] += _rename_entity(connection, old, new, stamp)
    return counts


def _rename_entity(connection: Connection, old: str, new: str, stamp: str) -> int:
    """标签实体跟着改：目标已存在就并过去，否则原地换名。"""
    source_id = _entity_id(connection, old)
    if source_id is None:
        return 0
    target_id = _entity_id(connection, new)
    if target_id is None:
        connection.execute(
            "UPDATE entity SET canonical_name=?,normalized_name=?,updated_at=? WHERE id=?",
            (new, normalize_entity_name(new), stamp, source_id))
        return 1
    merge_entity(connection, target_id=target_id, source_id=source_id,
                 source_name=old, alias_source="tag-rename", now=stamp)
    return 1
