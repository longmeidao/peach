"""编目规则：什么是番号、什么是分卷、标签属于哪一类、两条记录算不算重复。

不碰数据库、不碰 HTTP、不依赖任何 Peach 模块，是最底下那层纯策略。

这个文件曾经叫 `web_logic.py`，但里面没有一行是 web 的，而依赖它的四个模块里有
三个不是 web 层：`repository`（数据层）取 `is_jav_code`，`taste_history` 取
`LENGTH_TAGS`，`fc2_similarity` 取重复判据。数据层 import 一个叫 web 的模块，
读代码的人会以为分层反了——反的其实是名字。2026-08-29 改名，内容一行未动。
"""
from __future__ import annotations

import re


LENGTH_TAGS = {"短片-2分内", "中片-10分内", "长片-30分内", "超长片-30分上"}
TECH_TAGS = {
    "1080P", "720P", "4K", "2K", "2160P", "480P", "低画质", "高帧率",
    "横屏", "竖屏", "真人", "混合集", "身份待确认", "R-18", "有码", "无码",
}

# Hanime1 的筛选把可见标签按语义分组。Peach 只收录当前馆藏里确实存在的
# 分组；未命中的标签仍归「其他内容」，不凭名字臆造作品/角色实体。
ATTRIBUTE_TAGS = {
    "中文字幕", "内嵌字幕", "外挂字幕", "AI修复", "AI去码", "淫语ASMR",
    "日系同人", "游戏同人", "动漫同人", "3D动画", "VR", "60fps",
}
RELATIONSHIP_TAGS = {
    "母子设定", "近亲", "姐弟", "师生", "同事上司", "女友",
}
ROLE_TAGS = {
    "素人", "网红主播", "萝莉", "痴女", "人妻", "御姐", "学生", "秘书OL",
    "女仆", "熟女", "护士", "OL制服", "JK制服", "空姐", "老师", "教师",
    "探花", "男主频道",
}
APPEARANCE_TAGS = {
    "丝袜", "制服", "美臀", "乳系", "露脸", "情趣内衣", "美腿", "高跟",
    "眼镜", "洛丽塔", "苗条", "高颜值", "巨乳", "大腿", "白丝", "黑丝",
    "臀部", "泳装", "高跟鞋", "内衣情趣", "美乳", "肉丝", "旗袍汉服",
    "白虎", "双马尾", "婚纱", "裸足", "爆乳", "贫乳", "皮衣皮裙", "体操服",
    "兽耳兽装", "口罩遮脸", "和服浴衣", "瑜伽裤", "兔女郎", "腋", "丰满",
}
SCENE_TAGS = {
    "酒店", "浴室", "车震", "办公室", "户外露出", "线下约拍", "探花约炮",
    "教室学校", "厨房客厅", "户外", "车内",
}
STORY_TAGS = {
    "角色扮演", "反差", "绿帽NTR", "调教", "泄密流出", "NTR绿帽",
    "剧情演绎", "偷拍偷窥", "出轨", "强制剧情", "剧情", "捆绑", "有剧情",
    "偷窥", "定制", "百合", "慢热前戏", "榨精",
}
POSITION_TAGS = {
    "口交", "主观视角", "骑乘", "自慰", "后入", "多人", "中出内射", "足交",
    "手交", "潮吹", "打桩", "深喉", "射精", "乳交", "多女出镜",
    "颜射", "肛交", "射精特写", "3P多人", "女上位", "内射", "吞精", "足底足指",
    "素股隔丝", "足部射精", "马眼", "POV第一视角", "屁眼", "直接进入", "舔阴",
    "足控", "龟头责", "口爆", "舔脚", "毒龙", "传教士", "双洞齐插", "马眼尿道",
}

_CODE_STUDIO = re.compile(r"^[A-Z]{2,8}-\d{2,5}$")
_CODE_AMATEUR = re.compile(r"^\d{3}[A-Z]{2,6}-\d{2,5}$")
_CODE_FC2 = re.compile(r"^FC2-PPV-\d{5,}$")
_CODE_DATE = re.compile(r"^\d{6}-\d{2,4}$")

DUPLICATE_TOLERANCE = 0.005
DUPLICATE_FLOOR_SECONDS = 15.0
_PART_MARKER = re.compile(
    r"(?:^|[^a-z0-9])(?:part|pt|cd|disc|disk|dvd|vol)?[-_ ]?([1-9]\d?|[a-h])(?=\.[a-z0-9]{2,4}$)",
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


def is_jav_asset(code: str | None, studio: str | None = None,
                 release_date: str | None = None,
                 entity_kinds: tuple[str, ...] | list[str] = ()) -> bool:
    """Require release evidence in addition to a code-shaped string.

    Creator clips such as ``JI-103`` can look exactly like a studio code. They
    stay in ordinary browsing until a studio, performer, series, or release
    date ties them to a published JAV release. FC2 IDs are an explicit release
    system and do not need those projections.
    """
    if not is_jav_code(code):
        return False
    value = (code or "").upper().strip()
    if value.startswith("FC2"):
        return True
    return bool(
        str(studio or "").strip()
        or str(release_date or "").strip()
        or {"performer", "studio", "series"}.intersection(entity_kinds)
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
    if tag in LENGTH_TAGS or tag in TECH_TAGS or tag in ATTRIBUTE_TAGS:
        return "meta"
    if tag in RELATIONSHIP_TAGS:
        return "relationship"
    if tag in ROLE_TAGS:
        return "role"
    if tag in APPEARANCE_TAGS:
        return "appearance"
    if tag in SCENE_TAGS:
        return "scene"
    if tag in STORY_TAGS:
        return "story"
    if tag in POSITION_TAGS:
        return "position"
    return "general"


def part_marker(name: str) -> str:
    """Return a trailing multipart marker, if present."""
    match = _PART_MARKER.search(name or "")
    return match.group(1).lower() if match else ""


def ordered_multipart_items(items: list[dict]) -> list[dict]:
    """Return one unambiguous, contiguous multipart release in playback order.

    Bare A/B and numeric suffixes are both common in the existing library.  A
    repeated marker means that one part has duplicate encodes, while mixed
    letter/number markers are ambiguous; neither case is safe to collapse into
    one browsing card automatically.
    """
    marked = [(item, part_marker(str(item.get("name") or ""))) for item in items]
    if len(marked) < 2 or any(not marker for _, marker in marked):
        return []
    markers = [marker for _, marker in marked]
    if len(set(markers)) != len(markers):
        return []
    numeric = all(marker.isdigit() for marker in markers)
    alphabetic = all(len(marker) == 1 and marker.isalpha() for marker in markers)
    if not (numeric or alphabetic):
        return []
    positions = [int(marker) if numeric else ord(marker) - ord("a") + 1 for marker in markers]
    if sorted(positions) != list(range(1, len(positions) + 1)):
        return []
    return [item for _, item in sorted(zip(positions, (item for item, _ in marked)))]


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
