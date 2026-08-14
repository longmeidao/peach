"""Explicit online-follow adapters.

Adapters discover remote candidates only. They do not write ledger truth; callers must
persist raw evidence and submit normalized entries through a review boundary.
"""
from __future__ import annotations

import hashlib
import html
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol


DEFAULT_MAX_BYTES = 5 * 1024 * 1024


class FollowSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


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


class FollowSource(Protocol):
    def fetch(self, url: str, *, etag: str | None = None,
              last_modified: str | None = None) -> FollowResult: ...


def _read_http(request: urllib.request.Request, timeout: float, max_bytes: int) -> HttpResponse:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return HttpResponse(
                status=response.status,
                headers=dict(response.headers.items()),
                body=response.read(max_bytes + 1),
            )
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return HttpResponse(304, dict(exc.headers.items()), b"")
        raise


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _child_text(element: ET.Element, *names: str) -> str | None:
    wanted = set(names)
    for child in element:
        if _local_name(child.tag) in wanted:
            value = "".join(child.itertext()).strip()
            if value:
                return value
    return None


def _plain_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = html.unescape(re.sub(r"<[^>]+>", " ", value))
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
                 transport: Callable[[urllib.request.Request, float, int], HttpResponse] = _read_http):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.transport = transport

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
        request = urllib.request.Request(source_url, headers=headers)
        try:
            response = self.transport(request, self.timeout, self.max_bytes)
        except (OSError, urllib.error.URLError) as exc:
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
        try:
            root = ET.fromstring(response.body)
        except ET.ParseError as exc:
            raise FollowSourceError("follow source returned invalid XML") from exc
        root_name = _local_name(root.tag)
        if root_name == "rss":
            entries = self._parse_rss(root)
        elif root_name == "feed":
            entries = self._parse_atom(root)
        else:
            raise FollowSourceError("unsupported feed format")
        return FollowResult(entries=tuple(entries), **common)

    @staticmethod
    def _parse_rss(root: ET.Element) -> list[FollowEntry]:
        channel = next((node for node in root if _local_name(node.tag) == "channel"), None)
        if channel is None:
            raise FollowSourceError("RSS feed has no channel")
        entries = []
        for item in _children(channel, "item"):
            title = _child_text(item, "title") or "(untitled)"
            url = _child_text(item, "link")
            published = _child_text(item, "pubdate", "date")
            author = _child_text(item, "author", "creator")
            summary = _plain_text(_child_text(item, "description", "summary"))
            guid = _child_text(item, "guid")
            enclosure = next((node for node in item if _local_name(node.tag) == "enclosure"), None)
            media_url = enclosure.get("url") if enclosure is not None else None
            entries.append(FollowEntry(
                external_id=guid or url or _stable_id(title, published, media_url),
                title=title, url=url, media_url=media_url, published=published,
                author=author, summary=summary,
            ))
        return entries

    @staticmethod
    def _parse_atom(root: ET.Element) -> list[FollowEntry]:
        entries = []
        for item in _children(root, "entry"):
            title = _child_text(item, "title") or "(untitled)"
            links = _children(item, "link")
            alternate = next((node for node in links if node.get("rel", "alternate") == "alternate"), None)
            enclosure = next((node for node in links if node.get("rel") == "enclosure"), None)
            author_node = next((node for node in item if _local_name(node.tag) == "author"), None)
            author = _child_text(author_node, "name") if author_node is not None else None
            url = alternate.get("href") if alternate is not None else None
            media_url = enclosure.get("href") if enclosure is not None else None
            published = _child_text(item, "published", "updated")
            external_id = _child_text(item, "id") or url or _stable_id(title, published, media_url)
            entries.append(FollowEntry(
                external_id=external_id, title=title, url=url, media_url=media_url,
                published=published, author=author,
                summary=_plain_text(_child_text(item, "summary", "content")),
            ))
        return entries
