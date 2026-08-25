"""Explicit online-follow adapters.

Adapters discover remote candidates only. They do not write ledger truth; callers must
persist raw evidence and submit normalized entries through a review boundary.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import httpx
import feedparser
from bs4 import BeautifulSoup

from .http import HttpRequest, HttpResponse, HttpTransport, HttpxTransport


DEFAULT_MAX_BYTES = 5 * 1024 * 1024


class FollowSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class FollowEntry:
    external_id: str
    title: str
    url: str | None
    media_url: str | None
    published: str | None
    author: str | None
    summary: str | None


@dataclass(frozen=True)
class FollowResult:
    source_url: str
    entries: tuple[FollowEntry, ...]
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False
    raw_body: bytes | None = field(default=None, repr=False, compare=False)


class FollowSource(Protocol):
    def fetch(self, url: str, *, etag: str | None = None,
              last_modified: str | None = None) -> FollowResult: ...


def _plain_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = BeautifulSoup(value, "html.parser").get_text(" ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def _stable_id(*parts: str | None) -> str:
    material = "\n".join(part or "" for part in parts).encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def _validate_url(raw_url: str) -> str:
    parsed = urllib.parse.urlsplit(raw_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FollowSourceError("follow source must be an absolute HTTP(S) URL")
    if parsed.username is not None or parsed.password is not None:
        raise FollowSourceError("credentials are not allowed in follow source URLs")
    return urllib.parse.urlunsplit(parsed._replace(fragment=""))


class FeedAdapter:
    """RSS 2.0 and Atom discovery using mature public feed protocols."""

    def __init__(self, *, timeout: float = 15.0, max_bytes: int = DEFAULT_MAX_BYTES,
                 transport: HttpTransport | None = None):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.transport = transport or HttpxTransport()

    def fetch(self, url: str, *, etag: str | None = None,
              last_modified: str | None = None) -> FollowResult:
        source_url = _validate_url(url)
        headers = {
            "Accept": "application/atom+xml, application/rss+xml, application/xml;q=0.9",
            "User-Agent": "Peach/0.2 (+local self-hosted follow reader)",
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        request = HttpRequest("GET", source_url, headers)
        try:
            response = self.transport(request, self.timeout, self.max_bytes)
        except (OSError, httpx.HTTPError) as exc:
            raise FollowSourceError("follow source request failed") from exc
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        common = {
            "source_url": source_url,
            "etag": response_headers.get("etag"),
            "last_modified": response_headers.get("last-modified"),
        }
        if response.status == 304:
            return FollowResult(entries=(), not_modified=True, **common)
        if response.status != 200:
            raise FollowSourceError(f"follow source returned HTTP {response.status}")
        if len(response.body) > self.max_bytes:
            raise FollowSourceError("follow source exceeded response size limit")
        parsed = feedparser.parse(response.body)
        if not parsed.version or not (
            parsed.version.startswith("rss")
            or parsed.version.startswith("atom")
            or parsed.version.startswith("cdf")
        ):
            raise FollowSourceError("unsupported feed format")
        if parsed.bozo and not parsed.entries:
            raise FollowSourceError("follow source returned an invalid feed")
        entries = [self._normalize_entry(entry) for entry in parsed.entries]
        return FollowResult(entries=tuple(entries), raw_body=response.body, **common)

    @staticmethod
    def _normalize_entry(entry) -> FollowEntry:
        title = _plain_text(entry.get("title")) or "(untitled)"
        url = entry.get("link") or None
        published = entry.get("published") or entry.get("updated") or None
        author = _plain_text(entry.get("author"))
        summary_value = entry.get("summary") or entry.get("description")
        if not summary_value and entry.get("content"):
            summary_value = entry.content[0].get("value")
        media_url = None
        for enclosure in entry.get("enclosures") or ():
            media_url = enclosure.get("href") or enclosure.get("url")
            if media_url:
                break
        external_id = (
            entry.get("id") or entry.get("guid") or url
            or _stable_id(title, published, media_url)
        )
        return FollowEntry(
            external_id=str(external_id),
            title=title,
            url=str(url) if url else None,
            media_url=str(media_url) if media_url else None,
            published=str(published) if published else None,
            author=author,
            summary=_plain_text(summary_value),
        )


def write_immutable(path: Path, payload: bytes) -> None:
    """原始证据只写一次。同名不同内容说明取证边界被破坏，直接报错。"""
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise FollowSourceError("immutable follow snapshot collision")


@dataclass(frozen=True)
class FollowState:
    source_url: str
    etag: str | None = None
    last_modified: str | None = None
    checked_at: str | None = None
    snapshot: str | None = None


class FeedSnapshotStore:
    """Immutable feed evidence plus small replaceable conditional-request state."""

    def __init__(self, sources_root: Path, state_root: Path):
        self.sources_root = Path(sources_root) / "follow"
        self.state_root = Path(state_root) / "follow"

    @staticmethod
    def _source_key(source_url: str) -> str:
        return hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:20]

    def load(self, source_url: str) -> FollowState:
        source_url = _validate_url(source_url)
        path = self.state_root / f"{self._source_key(source_url)}.json"
        if not path.is_file():
            return FollowState(source_url)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FollowSourceError("follow state is unreadable") from exc
        if not isinstance(payload, dict) or payload.get("source_url") != source_url:
            raise FollowSourceError("follow state does not match source URL")
        return FollowState(
            source_url=source_url,
            etag=payload.get("etag"),
            last_modified=payload.get("last_modified"),
            checked_at=payload.get("checked_at"),
            snapshot=payload.get("snapshot"),
        )

    def persist(self, result: FollowResult, *, checked_at: datetime | None = None) -> FollowState:
        source_url = _validate_url(result.source_url)
        checked_at = checked_at or datetime.now(timezone.utc)
        if checked_at.tzinfo is None:
            raise FollowSourceError("follow check timestamp must be timezone-aware")
        checked_text = checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        previous = self.load(source_url)
        snapshot = previous.snapshot
        if not result.not_modified:
            if result.raw_body is None:
                raise FollowSourceError("feed result has no raw evidence")
            digest = hashlib.sha256(result.raw_body).hexdigest()
            stamp = checked_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            directory = self.sources_root / self._source_key(source_url)
            directory.mkdir(parents=True, exist_ok=True)
            raw_path = directory / f"{stamp}-{digest[:12]}.xml"
            metadata_path = raw_path.with_suffix(".json")
            write_immutable(raw_path, result.raw_body)
            metadata = {
                "source_url": source_url,
                "checked_at": checked_text,
                "sha256": digest,
                "entries": [asdict(entry) for entry in result.entries],
            }
            write_immutable(
                metadata_path,
                (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )
            snapshot = str(raw_path.relative_to(self.sources_root.parent))
        state = FollowState(
            source_url=source_url,
            etag=result.etag or previous.etag,
            last_modified=result.last_modified or previous.last_modified,
            checked_at=checked_text,
            snapshot=snapshot,
        )
        self.state_root.mkdir(parents=True, exist_ok=True)
        state_path = self.state_root / f"{self._source_key(source_url)}.json"
        self._write_state(state_path, asdict(state))
        return state


    @staticmethod
    def _write_state(path: Path, payload: dict) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        temporary.replace(path)
