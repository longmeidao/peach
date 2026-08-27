"""Resolve creator avatars from verified official profile endpoints."""
from __future__ import annotations

import json
import re
import urllib.parse

from bs4 import BeautifulSoup

from .follow import FollowSourceError
from .http import HttpRequest, HttpTransport, HttpxTransport


MAX_PROFILE_BYTES = 1024 * 1024
_USER_ID_RE = re.compile(r"^\d{1,20}$")
_CREATOR_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,80}$")


def resolve_official_avatar(service: str, user_id: str, *,
                            transport: HttpTransport | None = None) -> str:
    """Return a fixed-host official avatar URL for one supported creator service.

    FANBOX archive sources expose the Pixiv numeric user id.  The official creator
    page maps it to the public creator id; ``creator.get`` then returns the current
    ``user.iconUrl``.  Both requests and the returned image host are fixed here so a
    client cannot turn this endpoint into an SSRF or open redirect.
    """
    if service != "fanbox" or not _USER_ID_RE.fullmatch(str(user_id or "")):
        raise FollowSourceError("不支持这个官方头像来源")
    request = transport or HttpxTransport()
    profile_url = f"https://www.pixiv.net/fanbox/creator/{user_id}"
    page = request(
        HttpRequest("GET", profile_url, {
            "Accept": "text/html", "User-Agent": "Peach/0.2",
        }),
        15.0,
        MAX_PROFILE_BYTES,
    )
    if page.status != 200:
        raise FollowSourceError(f"FANBOX 官方页面返回 HTTP {page.status}")
    try:
        soup = BeautifulSoup(page.body, "html.parser")
        metadata_node = soup.find("meta", attrs={"name": "metadata"})
        metadata = json.loads(str(metadata_node.get("content"))) if metadata_node else {}
        creator_id = str(
            (((metadata.get("urlContext") or {}).get("host") or {}).get("creatorId"))
            or ""
        )
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise FollowSourceError("FANBOX 官方页面没有可用的创作者资料") from error
    if not _CREATOR_ID_RE.fullmatch(creator_id):
        raise FollowSourceError("FANBOX 官方页面没有可用的创作者 id")

    creator_origin = f"https://{creator_id}.fanbox.cc"
    api_url = "https://api.fanbox.cc/creator.get?" + urllib.parse.urlencode(
        {"creatorId": creator_id}
    )
    response = request(
        HttpRequest("GET", api_url, {
            "Accept": "application/json", "Origin": creator_origin,
            "Referer": creator_origin + "/", "User-Agent": "Peach/0.2",
        }),
        15.0,
        MAX_PROFILE_BYTES,
    )
    if response.status != 200:
        raise FollowSourceError(f"FANBOX 官方资料返回 HTTP {response.status}")
    try:
        body = (json.loads(response.body.decode("utf-8")) or {}).get("body") or {}
        user = body.get("user") or {}
        avatar = str(user.get("iconUrl") or "")
        returned_user_id = str(user.get("userId") or "")
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise FollowSourceError("FANBOX 官方资料格式不符") from error
    parsed = urllib.parse.urlsplit(avatar)
    if (returned_user_id != user_id or parsed.scheme != "https"
            or parsed.hostname != "pixiv.pximg.net"):
        raise FollowSourceError("FANBOX 官方资料没有可信的头像地址")
    return avatar
