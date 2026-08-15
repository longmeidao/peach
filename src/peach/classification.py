from __future__ import annotations

import re


# These values were verified as legacy collection/folder labels, not creator
# identities. Keep this boundary centralized so board generation and review
# application cannot disagree again.
STRUCTURAL_CREATORS = frozenset({"门槛", "视频", "宣傳文件", "宣传文件", "asce"})

_EPISODE = re.compile(r"(?<![A-Za-z0-9])S\d{1,2}E\d{1,3}(?!\d)", re.IGNORECASE)
_MAINSTREAM_RELEASE = re.compile(
    r"WEB[ ._-]?(?:DL|Rip)|HDTV|BluRay|AppleTor|\[rartv\]",
    re.IGNORECASE,
)


def is_structural_creator(name: str | None) -> bool:
    if not name:
        return False
    folded = name.strip().casefold()
    return any(folded == candidate.casefold() for candidate in STRUCTURAL_CREATORS)


def is_probable_mainstream_release(name: str | None, path: str | None = None) -> bool:
    """Return only strong TV-release candidates; callers must still review them."""
    text = " ".join(part for part in (name, path) if part)
    return bool(_EPISODE.search(text) and _MAINSTREAM_RELEASE.search(text))
