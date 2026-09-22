"""从这个人自己的作品封面上截一张脸当头像：图库给不出认得准的人像时的那一档。

整张封面装进圆框只剩一块背景（FC2 是十六比九的剧照，JAV 是双联封套），所以这里
不装封面，装的是封面上那张脸周围的一块方图——和挑图弹层里「作品画面」那一路人手
框出来的是同一种东西，只是框由 YuNet 的脸框定。

**挑哪一张封面按脸有多少像素，不按封面多大。** 同一个人的封面有 3360×1890 的官方原图，
也有 276×154 的缩略图；原图上戴着面具检不出脸时，那张原图对头像毫无用处。脸宽的像素
数同时回答了两件事：这张图上有没有能认的脸，放大进圆框之后清不清楚。缩略图上检出的
脸天然最窄，所以它只在别的封面都检不出脸时才轮得到——这一档最差就是缩略图。

只看单人作品：一部片挂着两个演员时，封面上那张脸是谁机器答不出来。单人作品也只是
「多半是她」，不是核实过的身份，所以来源记录标 `identity_verified: false`，这张图
永远排在图库与名录人像之后，出现那一档就被换掉（`avatar_followup`）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import images
from .avatar_face import face_px_width
from .catalog_rules import normalise_code_key

PROVIDER = "cover-face"
SOURCE_KIND = "cover_face_crop"
#: 批处理从整张封面装上的头像。它们同样没核实身份，还多半只剩一块背景，
#: 截出任何一张脸都比它强。
WHOLE_COVER_PROVIDERS = ("cover", "cover-fallback", "poster-fallback")
#: 方框边长是脸宽的几倍。YuNet 的框只框到额头和下巴，放到 2.4 倍才装得下头发和下巴
#: 下面一点；圆框再切掉四角，脸不贴边。
FACE_SPAN = 2.4


@dataclass(frozen=True)
class CoverFace:
    """一部作品的封面，连同在它上面检出的那张脸。"""

    asset_id: int
    code: str
    body: bytes
    width: int
    height: int
    record: dict

    @property
    def face_px(self) -> int:
        return face_px_width(self.record)


def single_performer_works(connection, entity_id: int) -> list[tuple[int, str]]:
    """这个人名下只有她一个演员的作品，`(asset_id, 番号)`，回收站里的不算。"""
    return [(int(asset_id), str(code)) for asset_id, code in connection.execute(
        "SELECT a.id,a.code FROM asset a JOIN asset_entity ae ON ae.asset_id=a.id "
        "WHERE ae.entity_id=? AND ae.role='performer' AND coalesce(a.code,'')<>'' "
        "AND (a.disposal IS NULL OR a.disposal<>'trash') "
        "AND NOT EXISTS(SELECT 1 FROM asset_entity other WHERE other.asset_id=a.id "
        "AND other.role='performer' AND other.entity_id<>ae.entity_id) "
        "ORDER BY a.id", (int(entity_id),))]


def best(connection, cover_root: Path, entity_id: int, probe) -> CoverFace | None:
    """脸最宽的那张封面；一张脸都检不出来就是 None。

    `probe` 是 `avatar_face.FaceProbe`：`on_bytes` 给出带 `px` 与脸框的记录。同一个番号
    分几段、或在两个目录各有一份时封面只有一张，只检一次。脸一样宽时取像素多的那张。
    """
    found: CoverFace | None = None
    seen: set[str] = set()
    for asset_id, code in single_performer_works(connection, entity_id):
        key = normalise_code_key(code)
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            body = (Path(cover_root) / f"{key}.jpg").read_bytes()
        except OSError:
            continue
        record = probe.on_bytes(body)
        px = (record or {}).get("px") or [0, 0]
        candidate = CoverFace(asset_id, key, body, int(px[0]), int(px[1]), record or {})
        if candidate.face_px <= 0:
            continue
        if found is None or ((candidate.face_px, candidate.width * candidate.height)
                             > (found.face_px, found.width * found.height)):
            found = candidate
    return found


def crop_box(face: CoverFace) -> tuple[int, int, int, int]:
    """脸周围那块方图在封面上的像素框。边长夹在封面短边以内，整块推回画面里。"""
    detail = face.record["face"]
    side = max(1, min(round(face.face_px * FACE_SPAN), face.width, face.height))
    left = round(float(detail["cx"]) * face.width - side / 2)
    top = round(float(detail["cy"]) * face.height - side / 2)
    left = max(0, min(left, face.width - side))
    top = max(0, min(top, face.height - side))
    return left, top, left + side, top + side


def cut(face: CoverFace) -> tuple[bytes, dict] | None:
    """切出方图，连同一份来源记录（形状与 `avatar_picker.install` 的 `origin` 一致）。"""
    box = crop_box(face)
    body = images.crop_to_box(face.body, box)
    if body is None:
        return None
    return body, {"source": "cover face", "provider": PROVIDER, "source_kind": SOURCE_KIND,
                  "external_id": face.code, "asset_id": face.asset_id,
                  "asset_code": face.code, "crop_box": list(box),
                  "crop_source_px": [face.width, face.height],
                  "face_px": face.face_px, "identity_verified": False}


def installed_face_px(avatar_root: Path, kind: str, entity_id: int) -> int | None:
    """装着的那张如果是这一档截的，返回它当时那张脸的像素宽；别的来源（或没有）是 None。

    只有从封面来的图才会被这一档换掉：整张封面装上的那种按 0 算，任何一张脸都比它宽。
    人挑的、图库装的，一律不碰。
    """
    from .previews import entity_image_key

    path = Path(avatar_root) / f"{entity_image_key(kind, int(entity_id))}.img.provenance.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict):
        return None
    if record.get("provider") in WHOLE_COVER_PROVIDERS:
        return 0
    if record.get("provider") != PROVIDER:
        return None
    try:
        return int(record.get("face_px") or 0)
    except (TypeError, ValueError):
        return 0
