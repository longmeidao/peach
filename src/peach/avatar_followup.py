"""刮削登记了新实体之后，把认得准的那张头像补上（ADR-0040 第七条）。

刮削链每跑一轮都会往账本里登记新的女优和厂牌。它们刚建出来时没有头像：人物页那张圆图
退成作品抽帧，厂牌页退成首字母。补图的能力早就有，缺的是「刮完顺手补上」这一步——
在这之前它是一条人想起来才跑的命令行。

判据：

* **女优**先走图库。按她整条名字链在图库里只找出一张、且尺寸过 `acceptable_avatar` 那一档，
  就装，规则与 `scripts/fill_portrait_gaps.py` 同一条。
* 找出好几张时按脸认人（ADR-0056）：同一个名字下 S1、Ideapocket 几家各存一张的多半是同一
  个人，`ななみ` 这种单名命中的二十几张却是二十几个人，名字答不了这件事。所以拿每张候选上的
  脸和她单人作品封面上截到的脸比（`face_match`，SFace），和 `MATCH_REQUIRED` 张封面（封面
  只截得出一张时就是那一张）都过官方阈值的才算她本人；过尺寸门槛的候选照图库先后比，第一张
  认定是她的装上。模型取不到、没有单人封面、封面检不出脸，一张都不比，照下一条退回。
* 图库给不出认得准的那一张时，从她单人作品的封面上截脸（`avatar_cover_face`）：挑脸像素最宽的
  那张封面，最差是缩略图；其余检得出脸的封面也各截一张留作候选。这一档截的图、以及批处理用整张封面装上的头像，之后遇到更清楚的
  脸会自动换掉；图库装的、人挑的一律不碰。
* **厂牌**不走这条：官网和标识由补厂牌后继（`studio_followup`）按厂牌那套判据补。

这条后继是幂等的（ADR-0040 第六条要求）：第一件事就是看盘上有没有那张图，有就当场返回。
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field

from . import avatar_cover_face, avatar_picker, face_match
from .avatar_provider import (
    MIN_LONG_SIDE, MIN_SHORT_SIDE, AvatarCandidateCache, InspectedAvatar, acceptable_avatar,
)
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

#: 比对拿几张封面上的脸作参照：脸最宽的那几张。
MATCH_COVERS = 3
#: 候选要和这么多张参照都过线才算她本人；参照只截得出一张时降到一张。
MATCH_REQUIRED = 2
#: 一个人最多拿这么多张图库候选去比，每张都要取一次图。
MAX_MATCH_CANDIDATES = 24


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


#: 指纹里的两个量：作品数与别名数。别名 SQL 与 `stock` 那条共用。
_ALIAS_COUNT = "(SELECT count(*) FROM entity_alias al WHERE al.entity_id=e.id)"


def fingerprint(connection: sqlite3.Connection, entity_id: int) -> str:
    """会让这条后继结论变的量：她名下的作品数与别名数，写成 `作品数:别名数`。

    多一部作品就多一张封面可截、可比；多一个别名就多一个名字去图库里找（`神山ももか`
    补上别名后才命中 `美雲そら` 与 `朝霧いのり` 两张）。
    """
    row = connection.execute(
        "SELECT (SELECT count(DISTINCT asset_id) FROM asset_entity WHERE entity_id=e.id),"
        f" {_ALIAS_COUNT} FROM entity e WHERE e.id=?", (int(entity_id),)).fetchone()
    works, aliases = (row[0], row[1]) if row else (0, 0)
    return f"{int(works or 0)}:{int(aliases or 0)}"


def stock(connection: sqlite3.Connection, avatar_root, attempts, *, limit: int,
          skip=()) -> list[Followup]:
    """库里早就登记、至今缺头像的女优，作品多的在前，最多 `limit` 条（ADR-0053）。

    跑过一次、指纹也没变的不再派（`attempts`）：作品和别名都没变，封面和图库命中也不会变。
    """
    if limit <= 0:
        return []
    skip = set(skip)
    found = []
    for row in connection.execute(
            "SELECT e.id,e.kind,e.canonical_name,count(DISTINCT ae.asset_id) AS assets,"
            f" {_ALIAS_COUNT} AS aliases"
            " FROM entity e JOIN asset_entity ae ON ae.entity_id=e.id"
            " WHERE e.kind='performer' GROUP BY e.id ORDER BY assets DESC, e.id"):
        entity_id, kind = int(row["id"]), str(row["kind"])
        key = followup_key(kind, entity_id)
        current = f"{int(row['assets'] or 0)}:{int(row['aliases'] or 0)}"
        if (key in skip or not _needs_avatar(avatar_root, kind, entity_id)
                or attempts.settled(key, current)):
            continue
        name = str(row["canonical_name"] or "")
        found.append(Followup(key=key, task_key=TASK_KEY,
                              label=f"{TASK_LABEL}：{name}" if name else TASK_LABEL))
        if len(found) >= limit:
            break
    return found


def run(contract, key: str, handle) -> dict:
    """跑一条补头像后继，再把实体当时的指纹记进 `Attempts`，存量补派按它判。

    该比对却取不到比对模型的那一次不记：结论取决于那天有没有网，不取决于她的作品和
    名字，记下来就要等到她多一部作品才会再试。
    """
    summary = _run(contract, key, handle)
    if summary.get("face_match_unavailable"):
        return summary
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
        # 图库索引只读本地缓存，这一步不联网；联网只发生在要量、要比、要装那几张的时候。
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
        from .avatar_face import FaceProbe

        probe = FaceProbe()
        covers = avatar_cover_face.faces(connection, contract.cover_root, entity_id, probe)
        extra: dict = {}
        if len(found) > 1:
            matched = _install_matched(contract, connection, providers_root, avatar_root,
                                       kind, entity_id, name, found, covers)
            if matched["outcome"] == "已装上":
                return matched
            gallery = matched["outcome"]
            extra = {key: value for key, value in matched.items()
                     if key == "face_match_unavailable"}
        else:
            gallery = "图库里没有这个名字" if not found else "图库那张太小"
        return {**_install_cover_face(contract, providers_root, avatar_root, kind,
                                      entity_id, name, gallery, len(found), cropped_px,
                                      covers, probe), **extra}


@dataclass(frozen=True)
class Candidate:
    """一张取来、量过的图库候选。"""

    choice: dict
    body: bytes
    origin: dict
    inspected: InspectedAvatar


@dataclass
class GalleryMatch:
    """图库多张候选按脸比对的结论。`winner` 是 None 时 `reason` 说为什么没选出来。"""

    winner: Candidate | None = None
    reason: str = ""
    #: 该比对却取不到比对模型。这一次的结论取决于有没有网，不作数。
    unavailable: bool = False
    #: 记进头像边车的比对证据（`face_match` 字段）。
    evidence: dict = field(default_factory=dict)
    #: 每张比过的候选各自的分数，`ref → [与每张参照的余弦]`。只读估计与测试看它。
    scores: dict = field(default_factory=dict)


def match_gallery(found: list[dict], covers: list, matcher,
                  fetch: Callable[[dict], Candidate | None]) -> GalleryMatch:
    """图库里这几张候选，哪一张是她本人（ADR-0056）。只读：取图交给 `fetch`，不写任何东西。

    参照是她单人作品封面上截到的脸，按脸宽取前 `MATCH_COVERS` 张；候选要和其中
    `MATCH_REQUIRED` 张（参照只有一张时就是那一张）的余弦都过 `face_match.COSINE_THRESHOLD`
    才算她。只要一张参照的话，一张认错人的封面就能让她装上别人的脸；要两张，封面和
    候选得在两部不同的作品上都对得上。

    挑哪一张：没过尺寸门槛的不比（认出来了也装不上），照图库的先后比，第一张过线的就是
    她，后面的不再取。不按像素挑：图库靠后的大库（`y-Minnano`、`z-DMM(骑)`）原图只有两三百
    像素、靠 AI 放大到五百以上，按像素排它们反而抢到前面；片商与事务所的原生图排在前头
    （`gfriends` 模块头）。
    """
    if not covers:
        return GalleryMatch(reason=f"图库 {len(found)} 张认不准")
    references = []
    for face in covers:
        if len(references) >= MATCH_COVERS:
            break
        cut = avatar_cover_face.cut(face)
        vector = matcher.embedding(cut[0]) if cut is not None else None
        if matcher.unavailable:
            return GalleryMatch(reason=f"图库 {len(found)} 张，比对模型不可用："
                                       f"{matcher.unavailable}", unavailable=True)
        if vector is not None:
            references.append((face, vector))
    if not references:
        return GalleryMatch(reason=f"图库 {len(found)} 张，封面人脸提不出特征")
    required = min(MATCH_REQUIRED, len(references))
    threshold = face_match.COSINE_THRESHOLD
    scores: dict = {}
    for choice in found[:MAX_MATCH_CANDIDATES]:
        candidate = fetch(choice)
        if candidate is None or not acceptable_avatar(candidate.inspected, MIN_LONG_SIDE,
                                                      MIN_SHORT_SIDE):
            continue
        vector = matcher.embedding(candidate.body)
        if matcher.unavailable:
            return GalleryMatch(reason=f"图库 {len(found)} 张，比对模型不可用："
                                       f"{matcher.unavailable}", unavailable=True)
        if vector is None:
            continue
        row = [round(face_match.cosine(vector, reference), 3)
               for _face, reference in references]
        scores[choice["ref"]] = row
        if sum(score >= threshold for score in row) >= required:
            evidence = {
                "model": face_match.MODEL_NAME, "threshold": threshold, "required": required,
                "covers": [{"code": face.code, "asset_id": face.asset_id, "score": score}
                           for (face, _vector), score in zip(references, row)],
                "candidates": len(found), "compared": len(scores),
            }
            return GalleryMatch(winner=candidate, evidence=evidence, scores=scores)
    return GalleryMatch(reason=f"图库 {len(found)} 张里比不出她", scores=scores)


def gallery_fetcher(connection, providers_root, entity_id: int, transport,
                    store: bool = True) -> Callable[[dict], Candidate | None]:
    """按候选的 `ref` 取图并量一次；取不到、不是图的当没有这一张。

    `store` 时把取来的图按地址留进图库缓存（只存对象，不写这个人的证据）：下一轮不必
    再下一次，挑图弹层也就量得出每一格的尺寸。落选的多半是别人，不该记成她取过的图。
    """
    cache = AvatarCandidateCache(providers_root / avatar_picker.GFRIENDS_CACHE)

    def fetch(choice: dict) -> Candidate | None:
        try:
            body, origin = avatar_picker.resolve(choice["ref"], connection,
                                                 providers_root, entity_id, transport)
            inspected = avatar_picker.accept_image(body)
        except avatar_picker.PickerError:
            return None
        if store and origin.get("upstream_url"):
            cache.store(str(origin["upstream_url"]), body, inspected)
        return Candidate(choice, body, origin, inspected)

    return fetch


def _install_matched(contract, connection, providers_root, avatar_root, kind: str,
                     entity_id: int, name: str, found: list[dict], covers: list) -> dict:
    """图库里找出好几张时，按脸比出是她的那一张装上。"""
    from .http import HttpxTransport

    summary = {"name": name, "matched": len(found)}
    transport = HttpxTransport()
    try:
        result = match_gallery(found, covers, face_match.FaceMatcher(),
                               gallery_fetcher(connection, providers_root, entity_id,
                                               transport))
    finally:
        close = getattr(transport, "close", None)
        if close:
            close()
    if result.winner is None:
        flag = {"face_match_unavailable": True} if result.unavailable else {}
        return {**summary, "outcome": result.reason, **flag}
    winner = result.winner
    origin = {**winner.origin, "source_kind": "gallery_face_matched",
              "name_source": "face-match", "face_match": result.evidence}
    avatar_picker.install(providers_root, avatar_root, kind, entity_id, winner.body, origin)
    contract.cache_bust()
    return {**summary, "outcome": "已装上",
            "size": f"{winner.inspected.width}×{winner.inspected.height}",
            "source": f"{winner.choice['label']}（按封面人脸认定）"}


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


def _install_cover_face(contract, providers_root, avatar_root, kind: str,
                        entity_id: int, name: str, gallery: str, matched: int,
                        cropped_px: int | None, found: list, probe) -> dict:
    """图库给不出那一张时，从她单人作品的封面上截一张脸装上。

    `found` 是 `avatar_cover_face.faces` 的结果，按脸宽排好；图库比对用的也是这一份。
    `cropped_px` 是装着的那张封面截图当时的脸宽（没装、或不是这一档装的是 None）：
    新挑出来的脸不比它宽就不换，免得每跑一次都把同一张图重写一遍。装着的那张上检不出
    脸时按 0 算：那是从打了模糊的封面上截的，脸再宽也认不出是谁。
    """
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
    if cropped_px and not avatar_cover_face.installed_face_readable(avatar_root, kind, entity_id, probe):
        cropped_px = 0
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
