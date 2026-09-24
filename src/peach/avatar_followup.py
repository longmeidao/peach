"""刮削登记了新实体之后，把认得准的那张头像补上（ADR-0040 第七条）。

刮削链每跑一轮都会往账本里登记新的女优和厂牌。它们刚建出来时没有头像：人物页那张圆图
退成作品抽帧，厂牌页退成首字母。补图的能力早就有，缺的是「刮完顺手补上」这一步——
在这之前它是一条人想起来才跑的命令行。

判据一个字都没新加：

* **女优**先走图库，规则与 `scripts/fill_portrait_gaps.py` 同一条——按她整条名字链在图库里
  只找出一张，且尺寸过 `acceptable_avatar` 那一档，才装。找出好几张一张都不装：`ななみ`
  这种单名在图库里命中二十几张，那是二十几个人，自动挑等于随便给她安一张别人的脸。
* 图库给不出那一张时，从她单人作品的封面上截脸（`avatar_cover_face`）：挑脸像素最宽的
  那张封面，最差是缩略图；其余检得出脸的封面也各截一张留作候选。这一档截的图、以及批处理用整张封面装上的头像，之后遇到更清楚的
  脸会自动换掉；图库装的、人挑的一律不碰。
* **厂牌**不走这条：官网和标识由补厂牌后继（`studio_followup`）按厂牌那套判据补。

这条后继是幂等的（ADR-0040 第六条要求）：第一件事就是看盘上有没有那张图，有就当场返回。
"""
from __future__ import annotations

import sqlite3

from . import avatar_cover_face, avatar_picker
from .avatar_provider import MIN_LONG_SIDE, MIN_SHORT_SIDE, acceptable_avatar
from .followups import Attempts, Followup, FollowupType, attempts_root, register

#: 这类后继在任务中心的身份，也是活动页上那一行的名字来源。
TASK_KEY = "entity-avatar"
TASK_LABEL = "补实体头像"

#: 会被派后继的实体种类。厂牌的图是标识，归 `studio_followup`；系列、标签没有头像位。
KINDS = ("performer",)

#: 一次刮削最多为这么多个新实体派后继。上限本身由 `task_runs.MAX_FOLLOWUPS` 判，
#: 这里先按作品数排好序再交出去：截断真的发生时，留下的该是库里出现得最多的那些。
PLAN_ORDER = "作品多的在前"

#: 封面人脸最多截几张：装上的一张，加上留进挑图弹层的几张。
MAX_KEPT_FACES = 8


def followup_key(kind: str, entity_id: int) -> str:
    return f"{TASK_KEY}:{kind}:{int(entity_id)}"


def parse_key(key: str) -> tuple[str, int]:
    """把后继 key 拆回实体身份。形状不对就抛——那说明排队的行不是这个版本写的。"""
    prefix, _, rest = str(key).partition(":")
    kind, _, raw = rest.partition(":")
    if prefix != TASK_KEY or kind not in KINDS or not raw.isdigit():
        raise ValueError(f"认不出这条补头像后继：{key}")
    return kind, int(raw)


def plan(connection: sqlite3.Connection, avatar_root, *,
         since_entity_id: int, covered_asset_ids=()) -> list[Followup]:
    """这一轮新登记、又没有头像的实体，一个一条后继。

    「新登记」按实体 id 的水位判：刮削开始前记一次 `max(id)`，比它大的就是这一轮建出来
    的。这比从落库结果里往回追要稳——实体可能由字段落库、别名归并或外部编号登记中的
    任何一条路建出来，而它们最终都表现为这张表上多了一行。

    `covered_asset_ids` 是这一轮换上了新封面的作品。它们的女优也派一条：没头像的现在
    可能截得出脸了，头像是从封面截的那些可能换得到更清楚的一张。
    """
    rows = connection.execute(
        "SELECT e.id,e.kind,e.canonical_name,"
        " (SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae"
        "  WHERE ae.entity_id=e.id) AS assets"
        " FROM entity e WHERE e.id>? AND e.kind='performer' ORDER BY e.id",
        (int(since_entity_id),)).fetchall()
    covered = [int(asset_id) for asset_id in covered_asset_ids]
    if covered:
        marks = ",".join("?" * len(covered))
        known = {int(row["id"]) for row in rows}
        rows += [row for row in connection.execute(
            "SELECT e.id,e.kind,e.canonical_name,"
            " (SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae"
            "  WHERE ae.entity_id=e.id) AS assets"
            " FROM entity e WHERE e.kind='performer' AND e.id IN"
            f" (SELECT entity_id FROM asset_entity WHERE asset_id IN ({marks}))"
            " ORDER BY e.id", covered).fetchall() if int(row["id"]) not in known]
    found = []
    for row in rows:
        entity_id, kind = int(row["id"]), str(row["kind"])
        if not _needs_avatar(avatar_root, kind, entity_id):
            continue
        found.append((int(row["assets"] or 0), entity_id, kind,
                      str(row["canonical_name"] or "")))
    found.sort(key=lambda item: (-item[0], item[1]))
    return [Followup(key=followup_key(kind, entity_id), task_key=TASK_KEY,
                     label=f"{TASK_LABEL}：{name}" if name else TASK_LABEL)
            for _assets, entity_id, kind, name in found]


def _needs_avatar(avatar_root, kind: str, entity_id: int) -> bool:
    """没有头像，或者装着的是封面截的那一档（还可能换到更清楚的）。"""
    return (not avatar_picker.installed_digest(avatar_root, kind, entity_id)
            or avatar_cover_face.installed_face_px(avatar_root, kind, entity_id) is not None)


def fingerprint(connection: sqlite3.Connection, entity_id: int) -> str:
    """会让这条后继结论变的量：她名下的作品数。多一部就多一批封面可截。"""
    return str(connection.execute(
        "SELECT count(DISTINCT asset_id) FROM asset_entity WHERE entity_id=?",
        (int(entity_id),)).fetchone()[0])


def stock(connection: sqlite3.Connection, avatar_root, attempts, *, limit: int,
          skip=()) -> list[Followup]:
    """库里早就登记、至今缺头像的女优，作品多的在前，最多 `limit` 条（ADR-0053）。

    跑过一次、作品数也没变的不再派（`attempts`）：图库和封面都没变，结论也不会变。
    """
    if limit <= 0:
        return []
    skip = set(skip)
    found = []
    for row in connection.execute(
            "SELECT e.id,e.kind,e.canonical_name,count(DISTINCT ae.asset_id) AS assets"
            " FROM entity e JOIN asset_entity ae ON ae.entity_id=e.id"
            " WHERE e.kind='performer' GROUP BY e.id ORDER BY assets DESC, e.id"):
        entity_id, kind = int(row["id"]), str(row["kind"])
        key = followup_key(kind, entity_id)
        if (key in skip or not _needs_avatar(avatar_root, kind, entity_id)
                or attempts.settled(key, str(row["assets"]))):
            continue
        name = str(row["canonical_name"] or "")
        found.append(Followup(key=key, task_key=TASK_KEY,
                              label=f"{TASK_LABEL}：{name}" if name else TASK_LABEL))
        if len(found) >= limit:
            break
    return found


def run(contract, key: str, handle) -> dict:
    """跑一条补头像后继，再把实体当时的指纹记进 `Attempts`，存量补派按它判。"""
    summary = _run(contract, key, handle)
    _kind, entity_id = parse_key(key)
    with contract.database.read_connection() as connection:
        current = fingerprint(connection, entity_id)
    Attempts(attempts_root(contract.candidate_root)).record(
        key, current, str(summary.get("outcome", "")))
    return summary


def _run(contract, key: str, handle) -> dict:
    """跑一条补头像后继。返回的摘要就是活动页上那一行。

    实体身份不进摘要——它已经在这条后继的 key 里，写两遍只是让那一行更难读。
    """
    kind, entity_id = parse_key(key)
    avatar_root = contract.avatar_root
    providers_root = contract.candidate_root / "provider-cache" / "performer-avatars"
    # 装着的是封面截的那一档时还要往下走：图库可能有了人像，封面可能换了更清楚的。
    cropped_px = avatar_cover_face.installed_face_px(avatar_root, kind, entity_id)
    if avatar_picker.installed_digest(avatar_root, kind, entity_id) and cropped_px is None:
        # 重跑、或者这中间人自己换过图。两种都不该再装一次。
        return {"outcome": "已有头像"}
    with contract.database.read_connection() as connection:
        row = connection.execute(
            "SELECT canonical_name FROM entity WHERE id=? AND kind=?",
            (entity_id, kind)).fetchone()
        if row is None:
            # 实体被合并或删掉了。这不是失败：那件事已经不存在了。
            return {"outcome": "实体已不存在"}
        name = str(row[0] or "")
        # 图库索引只读本地缓存，这一步不联网；联网只发生在真的要装那一张的时候。
        listing = avatar_picker.choices(connection, providers_root, avatar_root,
                                        kind, entity_id)
        found = [choice for choice in listing["choices"]
                 if choice["source"] == "gfriends"]
        handle.progress(label=f"{TASK_LABEL}：{name}", throttle=0)
        if len(found) == 1:
            installed = _install(contract, connection, providers_root, avatar_root,
                                 kind, entity_id, name, found[0])
            if installed["outcome"] == "已装上":
                return installed
        gallery = ("图库里没有这个名字" if not found
                   else "图库里认不准" if len(found) > 1 else "图库那张太小")
        return _install_cover_face(contract, connection, providers_root, avatar_root,
                                   kind, entity_id, name, gallery, len(found), cropped_px)


def _install(contract, connection, providers_root, avatar_root, kind: str,
             entity_id: int, name: str, choice: dict) -> dict:
    """图库里只找出这一张，取来量一次再装。"""
    from .http import HttpxTransport

    transport = HttpxTransport()
    try:
        body, origin = avatar_picker.resolve(choice["ref"], connection,
                                             providers_root, entity_id, transport)
        inspected = avatar_picker.accept_image(body)
    finally:
        close = getattr(transport, "close", None)
        if close:
            close()
    size = f"{inspected.width}×{inspected.height}"
    if not acceptable_avatar(inspected, MIN_LONG_SIDE, MIN_SHORT_SIDE):
        return {"name": name, "outcome": "图太小", "matched": 1, "size": size}
    avatar_picker.install(providers_root, avatar_root, kind, entity_id, body, origin)
    contract.cache_bust()
    return {"name": name, "outcome": "已装上", "matched": 1, "size": size,
            "source": choice["label"]}


def _install_cover_face(contract, connection, providers_root, avatar_root, kind: str,
                        entity_id: int, name: str, gallery: str, matched: int,
                        cropped_px: int | None) -> dict:
    """图库给不出那一张时，从她单人作品的封面上截一张脸装上。

    `cropped_px` 是装着的那张封面截图当时的脸宽（没装、或不是这一档装的是 None）：
    新挑出来的脸不比它宽就不换，免得每跑一次都把同一张图重写一遍。
    """
    from .avatar_face import FaceProbe

    probe = FaceProbe()
    found = avatar_cover_face.faces(connection, contract.cover_root, entity_id, probe)
    summary = {"name": name, "matched": matched}
    if not found:
        reason = f"探针不可用：{probe.unavailable}" if probe.unavailable else "封面上没有能截的脸"
        return {**summary, "outcome": f"{gallery}，{reason}"}
    face = found[0]
    # 装的只有脸最宽那一张；其余几张也截好留进候选缓存，挑图弹层里一点就能换，
    # 不必再去整张封面上手框。
    for other in found[1:MAX_KEPT_FACES]:
        if (extra := avatar_cover_face.cut(other)) is not None:
            avatar_picker.keep(providers_root, entity_id, *extra)
    if cropped_px is not None and face.face_px <= cropped_px:
        return {**summary, "outcome": "已是最清楚的封面人脸", "source": face.code}
    cut = avatar_cover_face.cut(face)
    if cut is None:
        return {**summary, "outcome": "封面截不出这一块", "source": face.code}
    body, origin = cut
    inspected = avatar_picker.install(providers_root, avatar_root, kind, entity_id,
                                      body, origin)
    contract.cache_bust()
    return {**summary, "outcome": "已装上",
            "size": f"{inspected['width']}×{inspected['height']}",
            "source": f"作品封面 {face.code}"}


#: 不写账本：这条后继只往 `avatar_root` 与候选缓存里写文件。它照样一次只跑一条——
#: 通道按 task_key 分，同一种后继本来就共用一条。
TYPE = register(FollowupType(task_key=TASK_KEY, label=TASK_LABEL,
                             writes_ledger=False, run=run))
