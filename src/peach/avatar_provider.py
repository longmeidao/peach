"""Candidate-only cache and evidence rules for external performer avatars."""
from __future__ import annotations

import hashlib
import io
import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError


POLICY_VERSION = "performer-avatar-provider-v1"
SUPPORTED_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
}


@dataclass(frozen=True)
class InspectedAvatar:
    width: int
    height: int
    mime_type: str
    extension: str
    sha256: str


@dataclass(frozen=True)
class AvatarProvenance:
    entity_id: int
    provider: str
    source_kind: str
    matched_name: str
    name_source: str
    external_id: str
    upstream_url: str
    width: int
    height: int
    mime_type: str
    sha256: str
    cache_path: str
    cached_at: str
    policy_version: str = POLICY_VERSION


def inspect_avatar(data: bytes) -> InspectedAvatar | None:
    """Decode the whole raster and derive type from bytes, never URL suffixes."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            image_format = (image.format or "").upper()
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        return None
    media = SUPPORTED_FORMATS.get(image_format)
    if media is None:
        return None
    mime_type, extension = media
    return InspectedAvatar(
        width=width,
        height=height,
        mime_type=mime_type,
        extension=extension,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def acceptable_avatar(avatar: InspectedAvatar, min_long: int, min_short: int) -> bool:
    return max(avatar.width, avatar.height) >= min_long and min(
        avatar.width, avatar.height
    ) >= min_short


def file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


class AvatarCandidateCache:
    """URL snapshots and immutable content objects outside the installed avatar tree."""

    def __init__(self, root: Path):
        self.root = root
        self._lock = threading.Lock()

    def _request_path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.root / "requests" / f"{key}.json"

    def lookup(self, url: str) -> bytes | None:
        try:
            request = json.loads(self._request_path(url).read_text(encoding="utf-8"))
            content = self.root / "objects" / request["object_name"]
            data = content.read_bytes()
            if hashlib.sha256(data).hexdigest() != request["sha256"]:
                return None
            return data
        except (OSError, KeyError, TypeError, ValueError):
            return None

    def store(self, url: str, data: bytes, avatar: InspectedAvatar) -> Path:
        object_path = self.root / "objects" / f"{avatar.sha256}{avatar.extension}"
        request_path = self._request_path(url)
        with self._lock:
            if not object_path.is_file():
                atomic_write(object_path, data)
            request = {
                "url": url,
                "sha256": avatar.sha256,
                "object_name": object_path.name,
                "mime_type": avatar.mime_type,
                "width": avatar.width,
                "height": avatar.height,
            }
            atomic_write(
                request_path,
                (json.dumps(request, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )
        return object_path

    def store_provenance(self, provenance: AvatarProvenance) -> Path:
        path = self.root / "evidence" / (
            f"performer-{provenance.entity_id}-{provenance.sha256}.json"
        )
        with self._lock:
            # entity + content hash makes this evidence immutable. Cache reuse must not
            # rewrite cached_at and make identical upstream evidence look like a new fact.
            if not path.is_file():
                atomic_write(
                    path,
                    (json.dumps(asdict(provenance), ensure_ascii=False, indent=2) + "\n").encode(
                        "utf-8"
                    ),
                )
        return path


def provenance_now(**values) -> AvatarProvenance:
    return AvatarProvenance(
        **values,
        cached_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def installed_avatar_hashes(
    avatar_dir: Path, live_entity_ids: set[int] | None = None,
) -> dict[str, int]:
    hashes: dict[str, int] = {}
    for path in sorted(avatar_dir.glob("performer-*.img")):
        try:
            entity_id = int(path.stem.split("-", 1)[1])
            if live_entity_ids is not None and entity_id not in live_entity_ids:
                continue
            hashes.setdefault(file_sha256(path), entity_id)
        except (OSError, ValueError):
            continue
    return hashes


def mark_duplicate_candidates(rows: list[dict], installed: dict[str, int]) -> None:
    """Reject exact byte duplicates deterministically; never guess perceptual identity."""
    owners = dict(installed)
    for row in rows:
        if row.get("section") != "missing" or row.get("verdict") != "ok":
            continue
        digest = str(row.get("sha256") or "")
        if not digest:
            row["verdict"] = "rejected"
            row["note"] = "缺少内容哈希，不能进入复核候选"
            continue
        owner = owners.get(digest)
        if owner is not None and owner != int(row["entity_id"]):
            row["verdict"] = "duplicate"
            row["duplicate_of_entity_id"] = owner
            row["note"] = f"与 performer-{owner} 的头像内容完全相同"
            continue
        owners[digest] = int(row["entity_id"])
