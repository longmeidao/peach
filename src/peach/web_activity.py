"""Profile activity and preference writes for the stable web contract."""
from __future__ import annotations

import time
from typing import Protocol


DEFAULT_PROFILE_ID = "local-default"


class ActivityContract(Protocol):
    def cache_bust(self) -> None: ...
    def write_transaction(self): ...


def w_activity(contract: ActivityContract, body):
    aid = int(body["id"])
    pos = float(body.get("position", 0))
    dur = float(body.get("duration", 0))
    add = float(body.get("delta", 0))
    ended = bool(body.get("ended"))
    seeks = int(body.get("seeks", 0))
    with contract.write_transaction() as connection:
        row = connection.execute(
            "SELECT play_seconds,max_reached,seek_count FROM asset WHERE id=?", (aid,),
        ).fetchone()
        secs = (row["play_seconds"] or 0) + max(add, 0)
        ratio = 1.0 if ended else (min(pos / dur, 1.0) if dur > 0 else None)
        maximum = max(row["max_reached"] or 0, ratio or 0)
        seek_count = (row["seek_count"] or 0) + max(seeks, 0)
        connection.execute(
            "UPDATE asset SET play_seconds=?, leave_ratio=COALESCE(?,leave_ratio), "
            "max_reached=?, seek_count=?, last_played=? WHERE id=?",
            (secs, ratio, maximum, seek_count, time.time(), aid),
        )
    real = (secs / dur) if dur > 0 else None
    return {
        "ok": True, "play_seconds": secs, "leave_ratio": ratio,
        "max_reached": maximum, "seek_count": seek_count, "real_ratio": real,
    }


def w_play(contract: ActivityContract, body):
    contract.cache_bust()
    aid = int(body["id"])
    with contract.write_transaction() as connection:
        connection.execute(
            "UPDATE asset SET play_count=COALESCE(play_count,0)+1, last_played=? WHERE id=?",
            (time.time(), aid),
        )
    return {"ok": True}


def w_feedback(contract: ActivityContract, body):
    contract.cache_bust()
    aid = int(body["id"])
    kind = body.get("kind")
    with contract.write_transaction() as connection:
        if kind in ("dislike", "seen"):
            current = connection.execute(
                "SELECT feedback FROM asset WHERE id=?", (aid,),
            ).fetchone()["feedback"]
            connection.execute(
                "UPDATE asset SET feedback=?, feedback_at=? WHERE id=?",
                (None if current == kind else kind, time.time(), aid),
            )
        elif kind == "dispose":
            current = connection.execute(
                "SELECT disposal FROM asset WHERE id=?", (aid,),
            ).fetchone()["disposal"]
            connection.execute(
                "UPDATE asset SET disposal=?, feedback_at=? WHERE id=?",
                (None if current == "trash" else "trash", time.time(), aid),
            )
        elif kind == "o":
            connection.execute(
                "UPDATE asset SET o_count=COALESCE(o_count,0)+1 WHERE id=?", (aid,),
            )
        elif kind == "o-undo":
            connection.execute(
                "UPDATE asset SET o_count=MAX(COALESCE(o_count,0)-1,0) WHERE id=?", (aid,),
            )
        elif kind == "rate":
            connection.execute(
                "UPDATE asset SET rating=? WHERE id=?", (int(body.get("value", 0)), aid),
            )
        result = dict(connection.execute(
            "SELECT feedback,disposal,rating,o_count FROM asset WHERE id=?", (aid,),
        ).fetchone())
    return {"ok": True, **result}


def w_watch_later(contract: ActivityContract, body):
    contract.cache_bust()
    aid = int(body["id"])
    with contract.write_transaction() as connection:
        exists = connection.execute(
            "SELECT 1 FROM watch_queue WHERE profile_id=? AND asset_id=?",
            (DEFAULT_PROFILE_ID, aid),
        ).fetchone()
        if exists:
            connection.execute(
                "DELETE FROM watch_queue WHERE profile_id=? AND asset_id=?",
                (DEFAULT_PROFILE_ID, aid),
            )
            queued = False
        else:
            connection.execute(
                "INSERT INTO watch_queue(profile_id,asset_id,added_at,source) "
                "VALUES(?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),'web')",
                (DEFAULT_PROFILE_ID, aid),
            )
            queued = True
    return {"ok": True, "watch_later": queued}


def w_preference(contract: ActivityContract, body):
    contract.cache_bust()
    aid = int(body["id"])
    liked = 1 if bool(body.get("liked")) else 0
    reason = body.get("reason", "")
    if not isinstance(reason, str):
        raise TypeError("reason must be a string")
    if len(reason) > 2000:
        raise ValueError("reason is limited to 2000 characters")
    with contract.write_transaction() as connection:
        if not connection.execute("SELECT 1 FROM asset WHERE id=?", (aid,)).fetchone():
            raise ValueError("asset not found")
        if not liked and not reason:
            connection.execute(
                "DELETE FROM asset_preference WHERE profile_id=? AND asset_id=?",
                (DEFAULT_PROFILE_ID, aid),
            )
        else:
            connection.execute(
                "INSERT INTO asset_preference(profile_id,asset_id,liked,reason,source,updated_at) "
                "VALUES(?,?,?,?,'web',strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
                "ON CONFLICT(profile_id,asset_id) DO UPDATE SET "
                "liked=excluded.liked,reason=excluded.reason,source=excluded.source,"
                "updated_at=excluded.updated_at",
                (DEFAULT_PROFILE_ID, aid, liked, reason),
            )
        row = connection.execute(
            "SELECT liked,reason FROM asset_preference WHERE profile_id=? AND asset_id=?",
            (DEFAULT_PROFILE_ID, aid),
        ).fetchone()
    return {
        "ok": True, "liked": bool(row["liked"]) if row else False,
        "like_reason": row["reason"] if row else "",
    }


def w_quality_goal(contract: ActivityContract, body):
    contract.cache_bust()
    aid = int(body["id"])
    wanted = 1 if bool(body.get("wanted")) else 0
    reason = body.get("reason", "")
    if not isinstance(reason, str):
        raise TypeError("reason must be a string")
    if len(reason) > 500:
        raise ValueError("reason is limited to 500 characters")
    with contract.write_transaction() as connection:
        if not connection.execute("SELECT 1 FROM asset WHERE id=?", (aid,)).fetchone():
            raise ValueError("asset not found")
        if not wanted:
            connection.execute(
                "DELETE FROM asset_quality_goal WHERE profile_id=? AND asset_id=?",
                (DEFAULT_PROFILE_ID, aid),
            )
        else:
            connection.execute(
                "INSERT INTO asset_quality_goal(profile_id,asset_id,wanted,reason,updated_at) "
                "VALUES(?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
                "ON CONFLICT(profile_id,asset_id) DO UPDATE SET "
                "wanted=excluded.wanted,reason=excluded.reason,updated_at=excluded.updated_at",
                (DEFAULT_PROFILE_ID, aid, wanted, reason),
            )
    return {
        "ok": True, "better_version": bool(wanted),
        "better_version_reason": reason if wanted else "",
    }
