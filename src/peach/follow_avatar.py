"""Resolve creator avatars from verified official profile endpoints."""
from __future__ import annotations
from .user_agent import USER_AGENT

import json
import re
import urllib.parse
from dataclasses import dataclass

from bs4 import BeautifulSoup

from .follow import FollowSourceError
from .http import HttpRequest, HttpTransport, HttpxTransport


MAX_PROFILE_BYTES = 1024 * 1024
_USER_ID_RE = re.compile(r"^\d{1,20}$")
_CREATOR_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,80}$")


@dataclass(frozen=True)
class OfficialProfile:
    user_id: str
    creator_id: str
    name: str
    url: str
    avatar_url: str


def resolve_official_profile(service: str, user_id: str, *,
                             transport: HttpTransport | None = None) -> OfficialProfile:
    """Return the verified official profile behind one archive identity.

    ``user_id`` accepts either identity FANBOX publishes.  Archive sources expose the
    Pixiv numeric user id, and the official creator page maps it to the public creator
    id.  A forum profile link only carries that creator id (``jul3dnsfw.fanbox.cc``),
    which ``creator.get`` already accepts, so that shape skips the lookup page.  Either
    way ``creator.get`` returns the current name and ``user.iconUrl``.  Hosts and the
    returned identity are fixed here so a client cannot turn discovery or the avatar
    endpoint into an SSRF/open redirect.
    """
    identity = str(user_id or "")
    if service != "fanbox":
        raise FollowSourceError("不支持这个官方头像来源")
    request = transport or HttpxTransport()
    if _USER_ID_RE.fullmatch(identity):
        expected_user_id = identity
        creator_id = _creator_id_for_user(identity, request)
    elif _CREATOR_ID_RE.fullmatch(identity):
        # 创作者 id 这条路没有可核对的数字 id，身份就以 `creator.get` 回的为准。
        expected_user_id = ""
        creator_id = identity
    else:
        raise FollowSourceError("不支持这个官方头像来源")

    creator_origin = f"https://{creator_id}.fanbox.cc"
    api_url = "https://api.fanbox.cc/creator.get?" + urllib.parse.urlencode(
        {"creatorId": creator_id}
    )
    response = request(
        HttpRequest("GET", api_url, {
            "Accept": "application/json", "Origin": creator_origin,
            "Referer": creator_origin + "/", "User-Agent": USER_AGENT,
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
        name = str(user.get("name") or creator_id).strip()
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise FollowSourceError("FANBOX 官方资料格式不符") from error
    parsed = urllib.parse.urlsplit(avatar)
    if ((expected_user_id and returned_user_id != expected_user_id)
            or not _USER_ID_RE.fullmatch(returned_user_id)
            or parsed.scheme != "https"
            or parsed.hostname != "pixiv.pximg.net"):
        raise FollowSourceError("FANBOX 官方资料没有可信的头像地址")
    return OfficialProfile(
        user_id=returned_user_id, creator_id=creator_id, name=name,
        url=creator_origin + "/", avatar_url=avatar,
    )


def _creator_id_for_user(user_id: str, request: HttpTransport) -> str:
    """Map a Pixiv numeric user id to the public FANBOX creator id."""
    profile_url = f"https://www.pixiv.net/fanbox/creator/{user_id}"
    page = request(
        HttpRequest("GET", profile_url, {
            "Accept": "text/html", "User-Agent": USER_AGENT,
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
    return creator_id


def resolve_official_avatar(service: str, user_id: str, *,
                            transport: HttpTransport | None = None) -> str:
    """Return a fixed-host official avatar URL for one supported creator service."""
    return resolve_official_profile(
        service, user_id, transport=transport,
    ).avatar_url
