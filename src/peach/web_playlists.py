"""Profile 级持久播放列表的读写契约。"""
from __future__ import annotations

from typing import Protocol

from .web_activity import DEFAULT_PROFILE_ID


MAX_PLAYLIST_ITEMS = 200
SOURCE_COST = {"local": "free", "115": "free", "pikpak": "metered", "online": "metered"}


class PlaylistContract(Protocol):
    def cache_bust(self) -> None: ...
    def read_connection(self): ...
    def has_snapshot(self, value) -> bool: ...
    def write_transaction(self): ...


def _name(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("name must be a string")
    name = value.strip()
    if not name:
        raise ValueError("播放列表名称不能为空")
    if len(name) > 80:
        raise ValueError("播放列表名称最多 80 个字符")
    return name


def _ids(value: object, *, allow_empty: bool = True) -> list[int]:
    if not isinstance(value, list):
        raise TypeError("asset_ids must be a list")
    ids = list(dict.fromkeys(int(item) for item in value))
    if not allow_empty and not ids:
        raise ValueError("播放列表至少需要一个视频")
    if len(ids) > MAX_PLAYLIST_ITEMS:
        raise ValueError(f"播放列表最多 {MAX_PLAYLIST_ITEMS} 个视频")
    return ids


def _playlist(connection, playlist_id: int):
    row = connection.execute(
        "SELECT id,profile_id,name,source_kind,source_seed_asset_id,current_asset_id,"
        "created_at,updated_at FROM playlist WHERE id=? AND profile_id=?",
        (playlist_id, DEFAULT_PROFILE_ID),
    ).fetchone()
    if row is None:
        raise KeyError("playlist not found")
    return row


def _existing_video_ids(connection, ids: list[int]) -> list[int]:
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    found = {
        int(row[0]) for row in connection.execute(
            f"SELECT id FROM asset WHERE id IN ({marks}) AND medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash')",
            ids,
        )
    }
    missing = [asset_id for asset_id in ids if asset_id not in found]
    if missing:
        raise ValueError(f"播放列表含不可用视频：{missing[0]}")
    return ids


def _ordered_ids(connection, playlist_id: int) -> list[int]:
    return [int(row[0]) for row in connection.execute(
        "SELECT asset_id FROM playlist_item WHERE playlist_id=? ORDER BY position",
        (playlist_id,),
    )]


def _replace_order(connection, playlist_id: int, ids: list[int]) -> None:
    # UNIQUE(playlist_id,position) 使直接原位交换会短暂撞位；先整体移到临时高位区间，
    # 再按最终顺序写回，事务外永远看不到中间状态。
    connection.execute(
        "UPDATE playlist_item SET position=position+1000000 WHERE playlist_id=?",
        (playlist_id,),
    )
    connection.executemany(
        "UPDATE playlist_item SET position=? WHERE playlist_id=? AND asset_id=?",
        [(position, playlist_id, asset_id) for position, asset_id in enumerate(ids)],
    )


def q_playlists(contract: PlaylistContract, _args=None):
    with contract.read_connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT p.id,p.name,p.source_kind,p.source_seed_asset_id,p.current_asset_id,"
            "p.created_at,p.updated_at,count(pi.asset_id) item_count,"
            "COALESCE(p.current_asset_id,(SELECT first.asset_id FROM playlist_item first "
            "WHERE first.playlist_id=p.id ORDER BY first.position LIMIT 1)) preview_asset_id "
            "FROM playlist p LEFT JOIN playlist_item pi ON pi.playlist_id=p.id "
            "WHERE p.profile_id=? GROUP BY p.id ORDER BY p.updated_at DESC,p.id DESC",
            (DEFAULT_PROFILE_ID,),
        )]
    return {"items": rows}


def q_playlist(contract: PlaylistContract, args):
    playlist_id = int(args["id"])
    with contract.read_connection() as connection:
        playlist = dict(_playlist(connection, playlist_id))
        items = [dict(row) for row in connection.execute(
            "SELECT a.id,a.location,a.name,a.creator,a.studio,a.code,a.size,a.duration,"
            "a.width,a.height,a.ctx_orient,a.snapshot_path,a.play_count,a.leave_ratio,"
            "a.feedback,a.disposal,a.o_count,pi.position "
            "FROM playlist_item pi JOIN asset a ON a.id=pi.asset_id "
            "WHERE pi.playlist_id=? ORDER BY pi.position",
            (playlist_id,),
        )]
    for item in items:
        item["cost"] = SOURCE_COST.get(item["location"], "metered")
        item["has_thumb"] = contract.has_snapshot(item.pop("snapshot_path", None))
    playlist["items"] = items
    playlist["item_count"] = len(items)
    if playlist["current_asset_id"] not in {item["id"] for item in items}:
        playlist["current_asset_id"] = items[0]["id"] if items else None
    return playlist


def w_playlist(contract: PlaylistContract, body):
    action = str(body.get("action") or "")
    contract.cache_bust()
    with contract.write_transaction() as connection:
        now = "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
        if action == "create":
            name = _name(body.get("name"))
            ids = _existing_video_ids(connection, _ids(body.get("asset_ids", [])))
            source_kind = "mix" if body.get("source_kind") == "mix" else "manual"
            seed_id = int(body["source_seed_asset_id"]) if body.get("source_seed_asset_id") else None
            if seed_id is not None and seed_id not in ids:
                raise ValueError("Mix 种子必须在播放列表中")
            cursor = connection.execute(
                f"INSERT INTO playlist(profile_id,name,source_kind,source_seed_asset_id,"
                f"current_asset_id,created_at,updated_at) VALUES(?,?,?,?,?,{now},{now})",
                (DEFAULT_PROFILE_ID, name, source_kind, seed_id, ids[0] if ids else None),
            )
            playlist_id = int(cursor.lastrowid)
            connection.executemany(
                f"INSERT INTO playlist_item(playlist_id,asset_id,position,added_at) "
                f"VALUES(?,?,?,{now})",
                [(playlist_id, asset_id, position) for position, asset_id in enumerate(ids)],
            )
        else:
            playlist_id = int(body["id"])
            row = _playlist(connection, playlist_id)
            if action == "rename":
                connection.execute(
                    f"UPDATE playlist SET name=?,updated_at={now} WHERE id=?",
                    (_name(body.get("name")), playlist_id),
                )
            elif action == "delete":
                # 运行时 sqlite 连接不依赖 PRAGMA foreign_keys；子表必须显式清理。
                connection.execute("DELETE FROM playlist_item WHERE playlist_id=?", (playlist_id,))
                connection.execute("DELETE FROM playlist WHERE id=?", (playlist_id,))
                return {"ok": True, "deleted": playlist_id}
            elif action == "add":
                additions = _existing_video_ids(
                    connection, _ids(body.get("asset_ids"), allow_empty=False),
                )
                current = _ordered_ids(connection, playlist_id)
                additions = [asset_id for asset_id in additions if asset_id not in current]
                connection.executemany(
                    f"INSERT INTO playlist_item(playlist_id,asset_id,position,added_at) "
                    f"VALUES(?,?,?,{now})",
                    [(playlist_id, asset_id, len(current) + offset)
                     for offset, asset_id in enumerate(additions)],
                )
                if row["current_asset_id"] is None and additions:
                    connection.execute(
                        "UPDATE playlist SET current_asset_id=? WHERE id=?",
                        (additions[0], playlist_id),
                    )
                connection.execute(f"UPDATE playlist SET updated_at={now} WHERE id=?", (playlist_id,))
            elif action == "remove":
                asset_id = int(body["asset_id"])
                connection.execute(
                    "DELETE FROM playlist_item WHERE playlist_id=? AND asset_id=?",
                    (playlist_id, asset_id),
                )
                remaining = _ordered_ids(connection, playlist_id)
                _replace_order(connection, playlist_id, remaining)
                current_id = row["current_asset_id"]
                if current_id == asset_id:
                    current_id = remaining[0] if remaining else None
                connection.execute(
                    f"UPDATE playlist SET current_asset_id=?,updated_at={now} WHERE id=?",
                    (current_id, playlist_id),
                )
            elif action == "reorder":
                ids = _ids(body.get("asset_ids"))
                current = _ordered_ids(connection, playlist_id)
                if len(ids) != len(current) or set(ids) != set(current):
                    raise ValueError("排序必须完整包含当前播放列表的所有视频")
                _replace_order(connection, playlist_id, ids)
                connection.execute(f"UPDATE playlist SET updated_at={now} WHERE id=?", (playlist_id,))
            elif action == "progress":
                asset_id = int(body["asset_id"])
                if asset_id not in _ordered_ids(connection, playlist_id):
                    raise ValueError("续播位置不在这个播放列表中")
                connection.execute(
                    f"UPDATE playlist SET current_asset_id=?,updated_at={now} WHERE id=?",
                    (asset_id, playlist_id),
                )
            else:
                raise ValueError("unknown playlist action")
    return {"ok": True, "playlist": q_playlist(contract, {"id": playlist_id})}
