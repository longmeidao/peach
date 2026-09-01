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
    "丝袜", "制服", "美臀", "乳系", "足系", "露脸", "情趣内衣", "美腿", "高跟",
    "眼镜", "洛丽塔", "苗条", "高颜值", "巨乳", "大腿", "白丝", "黑丝",
    "臀部", "泳装", "高跟鞋", "内衣情趣", "美乳", "肉丝", "旗袍汉服",
    "白虎", "双马尾", "婚纱", "裸足", "爆乳", "贫乳", "皮衣皮裙", "体操服",
    "兽耳兽装", "口罩遮脸", "和服浴衣", "瑜伽裤", "兔女郎", "腋", "丰满",
}

# 文件名／视觉模型早期只会给「乳系」「足系」这种宽泛品味标签；官方元数据一旦
# 给出更具体的身体特征或行为，宽泛标签就不再增加信息。只做单向取代：没有具体
# 标签时仍保留宽泛标签，避免把已有检索能力一并抹掉。
TAG_SUPERSESSION = {
    "乳系": frozenset({"美乳", "巨乳", "爆乳", "贫乳", "乳交"}),
    "足系": frozenset({"美腿", "足交", "足底足指", "足部射精", "足控", "舔脚", "裸足"}),
}
SCENE_TAGS = {
    "酒店", "浴室", "车震", "办公室", "户外露出", "线下约拍", "探花约炮",
    "教室学校", "厨房客厅", "户外", "车内", "按摩",
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
_CODE_DATE = re.compile(r"^\d{6}-\d{2,4}$")
_MEDIA_EXTENSION = re.compile(
    r"\.(?:mp4|mkv|avi|wmv|mov|m4v|webm|ts|m2ts|mts|mpg|mpeg|flv|rm|rmvb|iso)$",
    re.I,
)
_PROMO_DOMAIN = re.compile(
    r"(?:www\.)?[a-z0-9][a-z0-9-]{1,30}\."
    r"(?:com|net|la|xyz|cc|me|top|vip|club|info|org|tv|app|co|pw|gg|cn)",
    re.I,
)
_BRACKETED_PROMO_DOMAIN = re.compile(
    r"[\[【(（]\s*" + _PROMO_DOMAIN.pattern + r"\s*[\]】)）]", re.I,
)
_EDITION_TAIL = re.compile(
    r"(?:[-_.\s]+(?:c|ch|sub|uc|u|uncen(?:sored)?|uncensored|中字|中文字幕|无码|无码破解|破解))+$",
    re.I,
)

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


def is_amateur_code(code: str | None) -> bool:
    """三位数字前缀的素人系番号：`259LUXU-1475`、`300MIUM-1239`。

    这类番号由 MGS 发行，不进 DMM 数字版目录，也查不到 r18.dev 与 Prestige
    官方 API。判定只看形状：一旦改成「先拿到元数据再判断」，没有元数据的番号
    就永远轮不到该问的那个来源。
    """
    return bool(_CODE_AMATEUR.match((code or "").upper().strip()))


def code_letter_stem(code: str | None) -> str:
    """番号的字母段，用来和 DMM `content_id` 对照：`ABW-232` -> `abw`。"""
    value = normalise_code_key(code)
    if not value or value.startswith("FC2"):
        return ""
    return re.sub(r"[^A-Z]", "", value.split("-", 1)[0]).lower()


def is_jav_asset(code: str | None, studio: str | None = None,
                 release_date: str | None = None,
                 entity_kinds: tuple[str, ...] | list[str] = ()) -> bool:
    """Require release evidence in addition to a code-shaped string.

    Creator clips such as ``JI-103`` can look exactly like a studio code. They
    stay in ordinary browsing until a studio, performer, series, or release
    date ties them to a published JAV release. FC2 IDs are an explicit release
    system and do not need those projections.
    """
    # 历史 ledger 里有 PBD390、IPVR00296 这类缺连字符但带片商／出演者证据的真发行物。
    # 裸 `RAIKUN325` 仍不能单凭形态升级；只有规范化后像番号且同时有发行证据才接受。
    normalized = normalise_code_key(code)
    if not is_jav_code(code) and not is_jav_code(normalized):
        return False
    value = normalized.upper().strip()
    if value.startswith("FC2"):
        return True
    return bool(
        str(studio or "").strip()
        or str(release_date or "").strip()
        or {"performer", "studio", "series"}.intersection(entity_kinds)
    )


def _jav_code_pattern(code: str | None) -> str:
    """Return one regex fragment matching compact and separated forms of a canonical code."""
    canonical = normalise_code_key(code)
    fc2 = re.fullmatch(r"FC2-PPV-(\d+)", canonical)
    if fc2:
        return rf"FC2(?:[-_ ]?PPV)?[-_ ]*0*{re.escape(fc2.group(1))}"
    amateur = re.fullmatch(r"(\d{3})?([A-Z]+)-(\d+)", canonical)
    if amateur:
        prefix, letters, digits = amateur.groups()
        return (
            rf"{re.escape(prefix or '')}{re.escape(letters)}"
            rf"[-_ ]*0*{re.escape(str(int(digits)))}"
        )
    dated = re.fullmatch(r"(\d{6})-(\d{2,4})", canonical)
    if dated:
        return rf"{re.escape(dated.group(1))}[-_ ]*{re.escape(dated.group(2))}"
    return ""


def jav_edition_badges(name: str | None, code: str | None,
                       tags: tuple[str, ...] | list[str] = ()) -> list[str]:
    """Project filename/tag evidence into compact edition badges beside the code."""
    text = _MEDIA_EXTENSION.sub("", str(name or ""))
    tag_set = {str(tag).strip().casefold() for tag in tags if str(tag).strip()}
    code_pattern = _jav_code_pattern(code)
    after_code = (
        re.search(rf"(?:^|[^A-Z0-9]){code_pattern}([^A-Z0-9].*)?$", text, re.I)
        if code_pattern else None
    )
    suffix = after_code.group(1) if after_code and after_code.group(1) else ""
    cracked = (
        bool(re.search(r"无码\s*破解|無碼\s*破解|AI\s*去码|"
                       r"(?:^|[-_.\s\[])破解(?:$|[-_.\s\]])", text, re.I))
        or "ai去码" in tag_set or "无码破解" in tag_set
    )
    uncensored = (
        cracked
        or "无码" in tag_set
        or bool(re.search(r"(?:^|[-_.\s\[])"
                          r"(?:uc|u|uncen(?:sored)?|uncensored|无码|無碼)"
                          r"(?:$|[-_.\s\]])", suffix, re.I))
    )
    subtitled = (
        bool({"中文字幕", "内嵌字幕", "外挂字幕", "中字"}.intersection(tag_set))
        or bool(re.search(r"(?:^|[-_.\s\[])(?:c|ch|sub|中字|中文字幕)"
                          r"(?:$|[-_.\s\]])", suffix, re.I))
    )
    badges = []
    if subtitled:
        badges.append("中字")
    if cracked:
        badges.append("无码破解")
    elif uncensored:
        badges.append("无码")
    return badges


#: 头尾的裸域名不允许标签里带连字符：`ABP-762-fuckbe.com` 整串都符合「标签+.com」，
#: 按通用形态删前缀会把番号一起吃掉，只剩 `mp4`。带方括号那种由括号定界，不受此限。
_BARE_PROMO = r"(?:www\.)?[a-z0-9]{2,31}\.(?:com|net|la|xyz|cc|me|top|vip|club|info|org|tv|app|co|pw|gg|cn)"
_PROMO_PREFIX = re.compile(
    r"^(?:[\[【(（]\s*(?:" + _PROMO_DOMAIN.pattern + r")\s*[\]】)）]|(?:"
    + _BARE_PROMO + r"))[-_@.\s]*", re.I)
_PROMO_SUFFIX = re.compile(
    r"[-_@.\s]*(?:[\[【(（]\s*(?:" + _PROMO_DOMAIN.pattern + r")\s*[\]】)）]|(?:"
    + _BARE_PROMO + r"))$", re.I)


def strip_promo_markers(name: str | None) -> str:
    """摘掉名字**头尾**的推广域名标记，其余部分一个字都不动。

    只认头尾，不认名字中间。第一版删任意位置的带括号域名，结果把
    `Hazel Moore - [FootFetishDaily.com] - Hardcore` 里的厂牌删了——欧美片的
    `[Vixen.com]`、`[StraplessDildo.com]` 是厂牌名，不是广告，删掉是丢真信息。
    真正的广告标记全在头或尾：`[44x.me]tre-080`、`MattieDoll - pornhub.com`。

    同样刻意不做的事：不压缩多余空格、不合并空括号。第一版做了，把
    `(12P+5V_1.28G) [12P-5V-1.28GB]` 改成 `(12P+5V_1.28G12P-5V-1.28GB]`，
    把没有广告的 `狗链  兔尾` 也改了。

    头尾各剥到不动为止，`[98t.tv][98t.tv]ABW-251` 这种叠了两层的才能剥干净。
    """
    original = str(name or "")
    text = original
    while True:
        stripped = _PROMO_SUFFIX.sub("", _PROMO_PREFIX.sub("", text, count=1), count=1)
        if stripped == text:
            break
        text = stripped
    if text == original:
        # 没摘掉任何广告就原样返回：末尾那次 strip 会把 `@9ririsuamano` 这种
        # 本来就带前缀符号的账号名改掉，而它不是广告。
        return original
    return text.strip(" ._-—@")


def promo_free_key(name: str | None) -> str:
    r"""摘广告后再抹掉大小写与分隔符，用来判断两个目录名是不是同一个名字。

    实测的冗余层是 `TRE-080\[44x.me]tre-080`：大小写不同、还挂着广告前缀，
    直接比字符串会漏掉。分隔符也一起抹掉，`TRE080` 与 `TRE-080` 才算同名。
    """
    return re.sub(r"[\s._\-—]+", "", strip_promo_markers(name)).casefold()


def jav_fallback_title(name: str | None, code: str | None) -> str:
    """Clean a filename-derived JAV title without changing the stored filename."""
    text = _MEDIA_EXTENSION.sub("", str(name or "").strip())
    text = _BRACKETED_PROMO_DOMAIN.sub(" ", text)
    text = _PROMO_DOMAIN.sub(" ", text)
    code_pattern = _jav_code_pattern(code)
    if code_pattern:
        repeated = re.compile(rf"^[\s._\-—]*(?:{code_pattern})(?=$|[\s._\-—\[])", re.I)
        while repeated.search(text):
            text = repeated.sub("", text, count=1)
    text = _EDITION_TAIL.sub("", text)
    text = re.sub(r"[\[\]【】()（）]+", " ", text)
    text = re.sub(r"[._]+", " ", text)
    return re.sub(r"\s+", " ", text).strip(" -_—")


def jav_display_metadata(name: str | None, code: str | None,
                         tags: tuple[str, ...] | list[str] = ()) -> dict[str, object]:
    """Safe display projection; raw name/code remain untouched for file operations."""
    return {
        "display_code": normalise_code_key(code),
        "display_title": jav_fallback_title(name, code),
        "edition_badges": jav_edition_badges(name, code, tags),
    }


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


def superseded_taste_tags(tags: list[str] | tuple[str, ...]) -> frozenset[str]:
    """Return broad taste tags made redundant by more specific tags."""
    present = {str(tag).strip() for tag in tags if str(tag).strip()}
    return frozenset(
        broad for broad, specifics in TAG_SUPERSESSION.items()
        if specifics.intersection(present)
    )


def collapse_superseded_taste_tags(tags: list[str] | tuple[str, ...]) -> list[str]:
    """Keep input order while removing only semantically superseded broad tags."""
    obsolete = superseded_taste_tags(tags)
    return [tag for tag in tags if tag not in obsolete]


def part_marker(name: str) -> str:
    """Return a trailing multipart marker, if present."""
    match = _PART_MARKER.search(name or "")
    return match.group(1).lower() if match else ""


#: 首卷裸名（`TRE-080.mp4`）、后续卷带 `-2`/`-3` 时，裸名那份的时长必须落在其他卷的
#: 这个倍数之内。完整版至少是各卷之和，必然超出；几十秒的广告片又远低于下限。
PART_DURATION_SPREAD = 1.5


def _bare_first_part_plausible(bare: dict, parts: list[dict]) -> bool:
    durations = [float(item.get("duration") or 0) for item in [bare, *parts]]
    if any(value <= 0 for value in durations):
        return False                      # 没有时长证据就不替裸名下结论
    own, rest = durations[0], durations[1:]
    return min(rest) / PART_DURATION_SPREAD <= own <= max(rest) * PART_DURATION_SPREAD


def ordered_multipart_items(items: list[dict]) -> list[dict]:
    """Return one unambiguous, contiguous multipart release in playback order.

    Bare A/B and numeric suffixes are both common in the existing library.  A
    repeated marker means that one part has duplicate encodes, while mixed
    letter/number markers are ambiguous; neither case is safe to collapse into
    one browsing card automatically.

    盗版站常把第一卷留成裸名、后续卷才加 `-2`/`-3`（TRE-080 实测：9163/11255/8530 秒）。
    裸名也可能是整部完整版，所以只在数字标记、标记正好从 2 连续排起、且裸名时长与
    其他卷相差不大时，才把它当第 1 卷；字母卷缺 A 时无从判断裸名是不是 A，不猜。
    """
    marked = [(item, part_marker(str(item.get("name") or ""))) for item in items]
    if len(marked) < 2:
        return []
    bare = [item for item, marker in marked if not marker]
    if len(bare) > 1:
        return []
    numbered = [(item, marker) for item, marker in marked if marker]
    markers = [marker for _, marker in numbered]
    if len(set(markers)) != len(markers):
        return []
    numeric = all(marker.isdigit() for marker in markers)
    alphabetic = all(len(marker) == 1 and marker.isalpha() for marker in markers)
    if not (numeric or alphabetic):
        return []
    positions = [int(marker) if numeric else ord(marker) - ord("a") + 1 for marker in markers]
    ordered = list(zip(positions, (item for item, _ in numbered)))
    if bare:
        if not numeric or sorted(positions) != list(range(2, len(positions) + 2)):
            return []
        if not _bare_first_part_plausible(bare[0], [item for item, _ in numbered]):
            return []
        ordered.append((1, bare[0]))
    elif sorted(positions) != list(range(1, len(positions) + 1)):
        return []
    return [item for _, item in sorted(ordered, key=lambda pair: pair[0])]


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


def dir_expr(alias: str = "a.") -> str:
    """从 `path` 去掉 `name` 和分隔符，剩下的就是所在目录。

    表别名做成参数，是因为图集查询用 `a.`、按目录对账时直接查 `asset` 不带别名；
    早先靠对常量做字符串替换来凑另一种写法，改一次别名就会悄悄失配。
    """
    return (f"substr({alias}path,1,"
            f"length({alias}path)-length({alias}name)-1)")


#: 只写「这是图片」的通用目录名。它们做标题没有信息量，改用上一级目录名。
GENERIC_PHOTO_DIRS = frozenset({
    "p", "photo", "photos", "pic", "pics", "picture", "pictures",
    "image", "images", "img", "图片", "写真", "照片",
})


def photo_set_title(directory: str) -> str:
    """图集标题：叶子目录名；叶子只是 `P`、`图片` 这类通用名时用上一级。"""
    parts = [part for part in str(directory).replace("/", "\\").split("\\") if part]
    if not parts:
        return "未命名图集"
    leaf = parts[-1]
    if leaf.casefold() in GENERIC_PHOTO_DIRS and len(parts) > 1:
        return parts[-2]
    return leaf
