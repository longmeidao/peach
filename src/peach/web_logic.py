"""Pure, database-free rules shared by Peach's web contract domains."""
from __future__ import annotations

import re


LENGTH_TAGS = {"短片-2分内", "中片-10分内", "长片-30分内", "超长片-30分上"}
TECH_TAGS = {
    "1080P", "720P", "4K", "2K", "2160P", "480P", "低画质", "高帧率",
    "横屏", "竖屏", "真人", "混合集", "身份待确认", "R-18", "有码", "无码",
}
COPYRIGHT_HINT = re.compile(
    r"(ブルーアーカイブ|崩壊|崩坏|原神|勝利の女神|NIKKE|アークナイツ|明日方舟|"
    r"FGO|Fate|東方|东方|艦これ|舰娘|ウマ娘|赛马娘|ポケモン|宝可梦|"
    r"サイバーパンク|Honkai|Genshin|Blue Archive|VTuber|hololive|にじさんじ)", re.I,
)

_CODE_STUDIO = re.compile(r"^[A-Z]{2,8}-\d{2,5}$")
_CODE_AMATEUR = re.compile(r"^\d{3}[A-Z]{2,6}-\d{2,5}$")
_CODE_FC2 = re.compile(r"^FC2-PPV-\d{5,}$")
_CODE_DATE = re.compile(r"^\d{6}-\d{2,4}$")

DUPLICATE_TOLERANCE = 0.005
DUPLICATE_FLOOR_SECONDS = 15.0
_PART_MARKER = re.compile(
    r"(?:^|[^a-z0-9])(?:part|cd|disc|vol)?[-_ ]?([1-9]\d?|[a-h])(?=\.[a-z0-9]{2,4}$)",
    re.I,
)


def normalise_code_key(code: str | None) -> str:
    """Normalize a release code into the stable cover-cache key."""
    value = (code or "").upper().replace("_", "-").replace(" ", "-").strip()
    if not value:
        return ""
    if value.startswith("FC2"):
        digits = re.search(r"(\d{5,})", value)
        return f"FC2-PPV-{digits.group(1)}" if digits else value
    shape = re.match(r"^(\d{3})?([A-Z]+)-?(\d+)$", value)
    if not shape:
        return value
    return f"{shape.group(1) or ''}{shape.group(2)}-{int(shape.group(3)):03d}"


def is_jav_code(code: str | None) -> bool:
    """Recognize only code shapes whose original value keeps its separator."""
    value = (code or "").upper().strip()
    if not value:
        return False
    if value.startswith("FC2"):
        return bool(re.search(r"\d{5,}", value))
    return bool(
        _CODE_STUDIO.match(value)
        or _CODE_AMATEUR.match(value)
        or _CODE_DATE.match(value)
    )


def face_focus(ratio: float, cx: float, cy: float) -> dict | None:
    """Convert a normalized face center into a circular-frame object position."""
    try:
        ratio = float(ratio)
        cx = float(cx)
        cy = float(cy)
    except (TypeError, ValueError):
        return None
    if ratio <= 0 or abs(1.0 - ratio) <= 0.05:
        return None
    if ratio < 1.0:
        pos = (cy - ratio / 2) / (1 - ratio)
    else:
        pos = (ratio * cx - 0.5) / (ratio - 1)
    pct = int(round(min(1.0, max(0.0, pos)) * 100))
    return {"axis": "y" if ratio < 1.0 else "x", "pct": pct}


def tag_cat(tag: str) -> str:
    """Classify one tag for the web surface."""
    if tag.startswith("演员:"):
        return "artist"
    if tag in LENGTH_TAGS or tag in TECH_TAGS:
        return "meta"
    if COPYRIGHT_HINT.search(tag):
        return "copyright"
    if re.search(r"(ちゃん|さん|酱|娘)$", tag) and len(tag) <= 8:
        return "character"
    return "general"


def part_marker(name: str) -> str:
    """Return a trailing multipart marker, if present."""
    match = _PART_MARKER.search(name or "")
    return match.group(1).lower() if match else ""


def duration_clusters(items: list[dict]) -> list[list[dict]]:
    """Cluster same-code files by tight duration and multipart evidence."""
    clusters: list[list[dict]] = []
    known = sorted(
        (item for item in items if (item.get("duration") or 0) > 0),
        key=lambda item: item["duration"],
    )
    for item in known:
        marker = part_marker(str(item.get("name") or ""))
        for cluster in clusters:
            reference = cluster[0]["duration"]
            if abs(item["duration"] - reference) > max(
                DUPLICATE_FLOOR_SECONDS, reference * DUPLICATE_TOLERANCE,
            ):
                continue
            existing = {part_marker(str(row.get("name") or "")) for row in cluster}
            if marker and existing - {"", marker}:
                continue
            cluster.append(item)
            break
        else:
            clusters.append([item])
    clusters.extend([item] for item in items if not (item.get("duration") or 0) > 0)
    return clusters
