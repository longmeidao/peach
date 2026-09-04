"""编目规则：什么是番号、什么是分卷、标签属于哪一类、两条记录算不算重复。

不碰数据库、不碰 HTTP、不依赖任何 Peach 模块，是最底下那层纯策略。

文件名必须指着内容说话：这里没有一行是 web 的，而依赖它的四个模块里有三个不在
web 层——`repository`（数据层）取 `is_jav_code`，`taste_history` 取 `LENGTH_TAGS`，
`fc2_similarity` 取重复判据。数据层 import 一个叫 web 的模块，读代码的人会以为
分层反了。
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
    "剧情演绎", "偷拍偷窥", "出轨", "强制剧情", "剧情", "捆绑", "有剧情", "性教育",
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
_CODE_AMATEUR = re.compile(r"^\d{3}[A-Z]{2,8}-\d{2,5}$")
_CODE_DATE = re.compile(r"^\d{6}-\d{2,4}$")

#: 字母段 → 片商数字前缀。`259LUXU-1642` 与 `LUXU-1642` 是同一部作品的两种写法：
#: 前缀标的是 DMM 上的发行方，不属于作品身份，来源站点也只索引其中一种。
#:
#: 这张表按账本里实测出现过的字母段登记，不凭记忆扩展。补前缀会改变发给来源的查询，
#: 猜错就是拿别人的番号去查——这正是 2026-09-02 那批误匹配的成因。新增一行之前先在
#: 账本里确认该字母段只属于这一个发行方（`\d{3}[A-Z]+` 分组后看数字前缀是否唯一）。
MAKER_NUMBER_PREFIX = {
    "ARA": "261", "ENE": "550", "FKOS": "762", "GANA": "200", "GYAN": "278",
    "HHH": "451", "INST": "413", "JAC": "390", "JNT": "390", "KAI": "308",
    "KBI": "336", "LUXU": "259", "MAAN": "300", "MFC": "435", "MIUM": "300",
    "MLA": "476", "NTK": "300", "NTR": "348", "ORETD": "230", "OTIM": "393",
    "SIMM": "345", "SUKE": "428",
}
_CODE_MAKER_PREFIXED = re.compile(r"^(\d{3})([A-Z]{2,8})-(\d{2,5})$")
#: 来源返回的 id 允许带片商数字前缀、补零和重制尾字母；`h_` 是 DMM 的 label 标记。
_RELEASE_ID = re.compile(r"^(?:\d{1,4})?([A-Z]{2,8})0*(\d{1,5})[A-Z]?$")
_DMM_LABEL_PREFIX = re.compile(r"^H_(?=\d)")
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

#: 转载站与搬运渠道的域名标签（不含 TLD）。
#:
#: 这份名单拦的是一次具体误判，不是识别广告。域名剥掉 `.com` 之后就是「字母+数字」，
#: 和番号同形，于是 `normalise_code_key("HHD800")` 会补出连字符变成 `HHD-800`，
#: 一个水印域名在作品页、在 `JAV_ASSET_PREDICATE`、在 `clean_names` 的重命名提案里
#: 全都成了番号。实例 asset 31048：
#:
#:     B:\番号\_未知厂牌\HHD800\hhd800.com@ABW-132.mp4\ABW-132.mp4
#:
#: 真番号 ABW-132 就在文件名里，`code` 却是 `HHD800`。
#:
#: 形态本身分不开——真番号 `IPX219C`、`MEYD911`、`476MLA-179` 同样是字母紧贴数字，
#: 所以只能靠名单。这里每一条都有本机 ledger 的路径实证（`<label>.<tld>` 或
#: `<label>@` 水印链），`bei88` 是唯一例外：它只以 `bei88@sis001@…` 的搬运链出现，
#: 形态与 `www.98t.la@` 同类，但路径里没有 TLD。新增条目前先用
#: `scripts/audit_domain_codes.py` 在真实 ledger 上取路径证据，并确认它不撞真番号。
REPOST_SITE_LABELS = frozenset({
    "18my", "22sht", "7mmtv", "7sht", "91home", "98t", "aavv333", "bbsxv",
    "bei88", "big2048", "fuckbe", "gc2048", "hhd800", "hjd2048", "huachishe",
    "javday", "javme", "jitumi", "kfa11", "kfa33", "madoubt", "mtfdz",
    "nyap2p", "ses23", "supjav", "thz", "thzu", "u3c3", "yy2048",
})

#: 画质标记落在番号前面，剥掉才露出番号主体（`HD-abp-758` → `abp-758`）。
_QUALITY_HEAD = re.compile(r"^(?:hd|fhd|sd|uhd|4k|2160p?|1080p?|720p?)[-_. ]+", re.I)
#: 版本标记：`-C`/`-CH` 是中文字幕版，`-UC` 是无码流出，画质词也可能落在词尾。
_VERSION_TAIL = re.compile(r"[-_. ]?(?:ch|sub|uc|fhd|4k|hd|c|u)$", re.I)
#: 一本道、加勒比是「日期+序号」体系，没有字母番号主体。
_DATE_CODE = re.compile(r"(?<!\d)(\d{6})[-_](\d{3})(?!\d)")
#: UUID 首段长得像番号（`DCE7230C-730E-…` 会被拆成 `DCE`+`7230`），按整串形态排除。
_UUID_LIKE = re.compile(
    r"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}", re.I)
#: 目录名和文件名都可能带扩展名，图片也算：缩略图 `BNST033(2).jpg` 与正片同番号。
_ASSET_EXTENSION = re.compile(
    r"\.(?:mp4|mkv|avi|wmv|ts|mov|m4v|jpg|jpeg|png|webp)$", re.I)
#: 文件名尾部的分卷、画质和重复计数；剥掉才能和目录名对齐。
_FILE_NOISE = re.compile(
    r"(?:[-_. ]?(?:1080p?|720p?|2160p?|4k|fhd|hd|uc|sub|ch|c|u)"
    r"|[-_. ]\d{1,2}|\(\d{1,2}\)|[a-z])+$", re.I)
#: 番号主体：可选的三位素人前缀 + 字母厂牌 + 序号。
_CODE_BODY = re.compile(r"^(?:\d{3})?[A-Za-z]{2,8}[-_. ]?\d{2,5}$")
_FC2_ID = re.compile(r"^FC2(?:[-_. ]?PPV)?[-_. ]?(\d{5,})$", re.I)

#: 能证明「这是一次公开发行」的实体类型。`tag` 不在其中：口味标签谁都能挂，
#: 挂上了不代表这条记录对应某个发行物。
RELEASE_EVIDENCE_KINDS = frozenset({"performer", "studio", "series"})

#: 韩国 MIB 的番号前缀（用户 2026-09-04 指定）。这些是韩国内容，不是 JAV，拿它们去查
#: javbus／javdatabase 这类 JAV 目录站，取回的一定是**别的作品**。
#:
#: 形状上它们和厂牌番号毫无区别，所以 `is_jav_code` 认得它们，`is_jav_asset` 也只要求
#: 「有发行证据」——而那份证据恰恰是刮削自己写进去的，跑一轮就自我坐实了。2026-09-02 实测
#: `B:\MVP\MIB\` 下 68 次匹配有 58 次返回的番号根本不是查询的番号，整目录的厂牌、系列、
#: 标题因此全错，20 条 studio 无一例外全是误判（`peach-data/review/mib-studio-mismatch-20260902.md`）。
#: `_identity_mismatch` 只拦得住来源自报了番号的那部分，剩下的照样落进候选队列。
#:
#: 所以判据前移到刮削入口：这些番号一开始就不该被拿去问 JAV 来源。
#:
#: 前缀是 MIB 演员名的缩写，不是厂牌代号——`AR` 是 Ari、`JH` 是 Juhee、`SA` 是 Suah，
#: 一个演员一个前缀，所以表会随片源增加而变长，不要指望它收敛。2026-09-04 实测账本里
#: 两字母前缀番号共 24 种 75 条，其中 21 种全部位于 `B:\MVP\MIB\` 下、目录外零条。
#:
#: **不要退化成「两字母前缀就不是 JAV」这条形状判据。** 同一批实测里的三个例外正是反例：
#: `BF-366` 在 `B:\番号\BeFree\` 下，BeFree 是真实 JAV 厂牌；`TZ-105` 的 `TZ` 来自转载站
#: 水印 `[ThZu.Cc]`，压根不是番号（`is_repost_site_label` 那条路管它）；`FC-437689` 是 FC2
#: 的变体写法。按形状一刀切会把 BeFree 的真作品一起拦掉。
KOREAN_MIB_PREFIXES = frozenset({
    "WX", "AR", "JH", "CA", "IY", "JA", "MY", "SH", "HA", "MH", "DB", "JI",
    "ES", "SR", "SY", "CD", "YH", "UY", "NN", "SA", "JE", "YR",
})
_KOREAN_MIB_CODE = re.compile(r"^([A-Z]{2,4})-\d+$")

DUPLICATE_TOLERANCE = 0.005
DUPLICATE_FLOOR_SECONDS = 15.0
_PART_MARKER = re.compile(
    r"(?:^|[^a-z0-9])(?:part|pt|cd|disc|disk|dvd|vol)?[-_ ]?([1-9]\d?|[a-h])(?=\.[a-z0-9]{2,4}$)",
    re.I,
)


def compact_label(value: str | None) -> str:
    """把一串标识压成「无分隔符、序号不补零」的比较形。

    `BEI88`、`BEI-088`、`bei88` 说的是同一个东西，但 `normalise_code_key` 会把前两个
    都写成 `BEI-088`。不抹掉补零，名单就只拦得住其中一种写法——而界面显示的、
    SQL 谓词里比的、脚本重命名用的恰好是补过零的那一种。
    """
    text = re.sub(r"[^a-z0-9]", "", str(value or "").lower())
    shape = re.fullmatch(r"([a-z]+)(\d+)", text)
    return f"{shape.group(1)}{int(shape.group(2))}" if shape else text


def is_repost_site_label(value: str | None) -> bool:
    """True 表示这串字符是转载站／搬运渠道的水印标识，不是番号。

    两条判据：整串就是一个域名（`hhd800.com` 原样落进 `code` 的情况），或者压成
    比较形后命中 `REPOST_SITE_LABELS`（域名被剥掉 TLD、只剩标签的情况）。
    """
    text = str(value or "").strip()
    if not text:
        return False
    if _PROMO_DOMAIN.fullmatch(text):
        return True
    return compact_label(text) in REPOST_SITE_LABELS


def normalise_code_key(code: str | None) -> str:
    """Normalize a release code into the stable cover-cache key."""
    value = (code or "").upper().replace("_", "-").replace(" ", "-").strip()
    if not value:
        return ""
    if is_repost_site_label(value):
        # 水印域名原样返回：给它补出连字符就等于凭空造了一个番号，
        # 而作品页显示的 `display_code` 正是这个返回值。
        return value
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
    if not value or is_repost_site_label(value):
        return False
    if value.startswith("FC2"):
        return bool(re.search(r"\d{5,}", value))
    return bool(
        _CODE_STUDIO.match(value)
        or _CODE_AMATEUR.match(value)
        or _CODE_DATE.match(value)
    )


def is_korean_mib_code(code: str | None) -> bool:
    """True 表示这个番号属于韩国 MIB，不适用 JAV 规则。

    只认 `<字母>-<数字>` 这一种写法下的前缀。素人系的三位数字前缀（`300MIUM-1239`）
    和 FC2 都不在此列：它们的字母段虽然可能撞上，但发行体系本来就不是 MIB。
    """
    value = normalise_code_key(code)
    shape = _KOREAN_MIB_CODE.match(value)
    return bool(shape and shape.group(1) in KOREAN_MIB_PREFIXES)


def code_query_variants(code: str | None) -> tuple[str, ...]:
    """按可用程度排序的查询写法，第一个永远是账本的规范写法。

    同一发行方在账本里两种写法都有——`259LUXU-1004` 和 `LUXU-688`、`336KBI-010`
    和 `KBI-019`，共 6 个字母段 13 个裸写法。来源站点通常只索引一种，拿另一种查会
    落空。所以先查规范写法，落空再换另一种写法。

    两个方向不对称，是刻意的：**去掉**前缀只是丢掉番号里本来就有的一段，不会凭空
    编东西；**补上**前缀要填三位数字，只对 `MAKER_NUMBER_PREFIX` 里登记过的字母段做。
    """
    primary = normalise_code_key(code)
    if not primary:
        return ()
    if primary.startswith("FC2"):
        return (primary,)
    prefixed = _CODE_MAKER_PREFIXED.fullmatch(primary)
    if prefixed:
        return (primary, f"{prefixed.group(2)}-{prefixed.group(3)}")
    bare = _CODE_STUDIO.match(primary)
    if bare:
        letters = primary.split("-", 1)[0]
        prefix = MAKER_NUMBER_PREFIX.get(letters)
        if prefix:
            return (primary, f"{prefix}{primary}")
    return (primary,)


def release_identity(code: str | None) -> str:
    """把番号或来源返回的 id 收敛成可比对的作品身份。

    比对不能用裸字符串相等。全库扫描出的 281 个「不相等」里绝大多数是良性差异，
    四类各有实例：片商数字前缀（`390JAC-040` / `JAC-040`）、DMM 的 label 前缀
    （`BAZX-123` / `7BAZX-123`、`h_113sy00101`）、补零（`IQQQ-026` / `IQQQ-26`）、
    重制尾字母（`49ha102r`）。这些是同一部作品。

    认不出形态的值原样返回，只和自己相等：`20211103_JENNIFERMENDEZ` 这种关键词
    搜索结果不该和任何番号算成同一部。
    """
    raw = _DMM_LABEL_PREFIX.sub("", str(code or "").upper().strip())
    value = re.sub(r"[\s._\-]+", "", raw)
    if not value:
        return ""
    if value.startswith("FC2"):
        # 分隔符已经抹掉，取数字要从 `FC2` 之后开始：否则 `FC2-1812235` 会被读成
        # 一段 `21812235`，和 `FC2-PPV-1812235` 算成两部不同的作品。
        digits = re.search(r"(\d{5,})", value[3:])
        return f"FC2-{int(digits.group(1))}" if digits else value
    dated = re.fullmatch(r"(\d{6})(\d{2,4})", value)
    if dated:
        return f"{dated.group(1)}-{dated.group(2)}"
    shape = _RELEASE_ID.fullmatch(value)
    if shape:
        return f"{shape.group(1)}-{int(shape.group(2))}"
    return value


def same_release_code(left: str | None, right: str | None) -> bool:
    """两个写法是否指同一部作品。空值不算相等——没有证据不是证据。"""
    first, second = release_identity(left), release_identity(right)
    if not first or not second:
        return False
    if first == second:
        return True
    # FC2 的来源 id 是裸数字（`FC2-PPV-1812235` → `1812235`）。裸数字自己不是番号
    # 形态，所以这条不放进 `release_identity`：只有另一侧确实是 FC2 才按数字比。
    fc2 = next((value for value in (first, second) if value.startswith("FC2-")), "")
    other = first if second == fc2 else second
    return bool(fc2) and other.isdigit() and fc2 == f"FC2-{int(other)}"
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
        or RELEASE_EVIDENCE_KINDS.intersection(entity_kinds)
    )


def release_code_from_text(value: str | None) -> str | None:
    """从一段文字（目录名或文件名主干）里解析出规范番号；解析不出返回 None。

    和 `normalise_code_key` 的分工：那个只归一化「已经确认是番号」的字符串，这个负责
    判断一段文字里到底有没有番号。归一化仍然交给它，不在这里重写一遍——番号既是身份
    判定也是封面缓存键，两份实现漂移会让同一部片解析出两个键。

    `HHD800` 这类转载站标签一律返回 None：它形态上完全符合「字母+数字」，只有名单能
    把它和 `MEYD911` 分开。
    """
    text = str(value or "").strip()
    if not text or _UUID_LIKE.search(text):
        return None
    text = _ASSET_EXTENSION.sub("", text)
    if is_repost_site_label(text):
        return None
    fc2 = _FC2_ID.match(text)
    if fc2:
        return normalise_code_key(f"FC2-PPV-{fc2.group(1)}")
    date = _DATE_CODE.search(text)
    if date:
        return f"{date.group(1)}-{date.group(2)}"
    body = _VERSION_TAIL.sub("", _QUALITY_HEAD.sub("", text))
    if not _CODE_BODY.match(body):
        return None
    canonical = normalise_code_key(body)
    return canonical if is_jav_code(canonical) else None


def release_code_from_filename(name: str | None) -> str | None:
    """文件名带分卷、画质和重复计数，剥掉噪声后再解析。"""
    stem = _ASSET_EXTENSION.sub("", str(name or "").strip())
    return release_code_from_text(stem) or release_code_from_text(
        _FILE_NOISE.sub("", stem))


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


#: 无码厂商自己的编号法：Caribbeancom／1Pondo／10musume／Pacopacomama 用
#: `MMDDYY-nnn`，HEYZO 用 `HEYZO-1380`。有码厂商不用这两种形状。
UNCENSORED_CODE_SHAPES = (
    re.compile(r"^\d{6}-\d{2,4}$"),
    re.compile(r"^HEYZO-\d{2,5}$", re.I),
)
#: 文件名里的发行站标记。番号形状认不出来时（例如 Tokyo-Hot 的 `n1234`），
#: 这是另一条本机就能核验的证据。
_UNCENSORED_SITE = re.compile(
    r"(?i)(?<![A-Z0-9])(?:"
    r"carib(?:bean(?:com)?(?:pr)?)?|1pon(?:do)?|10mu(?:sume)?|heyzo|"
    r"pacopacomama|paco|muramura|tokyo[-_]?hot"
    r")(?![A-Z0-9])"
)
#: 版次标记有时和番号粘在一起，中间没有分隔符：`PPPD-937CH.mp4`、`MIDV-751CH.mp4`。
#: 只认带分隔符的写法，这些文件既拿不到「中字」徽章，番号本身还会被当标题显示。
_GLUED_EDITION = r"(?:CH|C|SUB|UC|U)"


def is_uncensored_code(code: str | None) -> bool:
    value = str(code or "").strip()
    return any(shape.fullmatch(value) for shape in UNCENSORED_CODE_SHAPES)


def is_uncensored_release(name: str | None, code: str | None) -> bool:
    """番号形状或文件名里的发行站，两者有一个成立就是无码厂商的片。

    这两条都是本机可核验的证据，不依赖抓取结果——`040221-001` 这类番号在
    r18.dev 永远 404，等元数据到齐再判，徽章就永远不会出现。
    """
    return is_uncensored_code(code) or bool(_UNCENSORED_SITE.search(str(name or "")))


def jav_edition_badges(name: str | None, code: str | None,
                       tags: tuple[str, ...] | list[str] = ()) -> list[str]:
    """Project filename/tag evidence into compact edition badges beside the code."""
    text = _MEDIA_EXTENSION.sub("", str(name or ""))
    tag_set = {str(tag).strip().casefold() for tag in tags if str(tag).strip()}
    code_pattern = _jav_code_pattern(code)
    after_code = (
        re.search(
            rf"(?:^|[^A-Z0-9]){code_pattern}((?:{_GLUED_EDITION})?(?:[^A-Z0-9].*)?)$",
            text, re.I,
        )
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
        # 无码厂商的片本身就是无码，不需要文件名里另有 `-U`／`Uncen` 标记。
        or is_uncensored_release(name, code)
        # `un` 和 `u`／`uc` 是同一个意思。此前它没进这张表，`ABF-158-UN.mp4`
        # 既拿不到徽章，`UN` 又被当标题显示；现在标题判空了，不认它就等于把
        # 这条信息整个丢掉。
        or bool(re.search(r"(?:^|[-_.\s\[])"
                          r"(?:uc|un|u|uncen(?:sored)?|uncensored|无码|無碼)"
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

    只认头尾，不认名字中间。删任意位置的带括号域名会把
    `Hazel Moore - [FootFetishDaily.com] - Hardcore` 里的厂牌一起删掉——欧美片的
    `[Vixen.com]`、`[StraplessDildo.com]` 是厂牌名，不是广告，删掉是丢真信息。
    真正的广告标记全在头或尾：`[44x.me]tre-080`、`MattieDoll - pornhub.com`。

    同样刻意不做的事：不压缩多余空格、不合并空括号。做了的话，
    `(12P+5V_1.28G) [12P-5V-1.28GB]` 会变成 `(12P+5V_1.28G12P-5V-1.28GB]`，
    没有广告的 `狗链  兔尾` 也跟着被改。

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


#: 无码片的文件名基本由「发行站 + 番号 + 画质/分卷」拼成，一个真标题词都没有：
#: `040221-001-carib-1080p.mp4`、`071213-625-1pon-whole1_hd.avi`、
#: `heyzo_hd_1380_full.mp4`。剥掉番号剩下的是发行残渣，不是标题——界面上却当
#: 标题显示成「040221-001 carib-1080p」。这些站名和画质标记是有限集合，日文
#: 标题里不会出现，可以按词剥。
_RELEASE_NOISE = re.compile(
    r"(?i)(?<![A-Z0-9])(?:"
    r"carib(?:bean(?:com)?(?:pr)?)?|1pon(?:do)?|10mu(?:sume)?|heyzo|"
    r"pacopacomama|paco|muramura|tokyo[-_]?hot|xxx[-_]?av|"
    r"\d{3,4}p|[0-9]?[fu]?hd\d*|sd|4k|2k|whole\d*|part\d*|full|lt|ch\d*"
    r")(?![A-Z0-9])"
)
#: 剥完之后判断剩下的还算不算标题：既没有中日文，也没有一个长度 ≥4 的字母词，
#: 那就是番号数字和零碎标记，不是名字。`Minah My new companion…` 留得住，
#: `1pon-092415-001-fhd2 (new)` 剥到只剩 `new` 就该判空。
_TITLE_CJK = re.compile(r"[぀-ヿ㐀-鿿]")
_TITLE_WORD = re.compile(r"[A-Za-z]{4,}")


def _is_release_residue(text: str) -> bool:
    return not (_TITLE_CJK.search(text) or _TITLE_WORD.search(text))


def jav_fallback_title(name: str | None, code: str | None) -> str:
    """Clean a filename-derived JAV title without changing the stored filename."""
    text = _MEDIA_EXTENSION.sub("", str(name or "").strip())
    text = _BRACKETED_PROMO_DOMAIN.sub(" ", text)
    text = _PROMO_DOMAIN.sub(" ", text)
    code_pattern = _jav_code_pattern(code)
    if code_pattern:
        repeated = re.compile(
            rf"^[\s._\-—]*(?:{code_pattern})(?:{_GLUED_EDITION})?(?=$|[\s._\-—\[])", re.I)
        while repeated.search(text):
            text = repeated.sub("", text, count=1)
        # 番号不总在开头：`1pon-092415-001-fhd1_(new).mp4` 把发行站放在了前面。
        # 只认前缀，整个番号就会留在「标题」里显示出来。
        text = re.sub(rf"(?<![A-Z0-9])(?:{code_pattern})(?:{_GLUED_EDITION})?(?![A-Z0-9])",
                      " ", text, flags=re.I)
    text = _EDITION_TAIL.sub("", text)
    text = _RELEASE_NOISE.sub(" ", text)
    text = re.sub(r"[\[\]【】()（）]+", " ", text)
    text = re.sub(r"[._]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -_—")
    return "" if _is_release_residue(text) else text


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
    靠对常量做字符串替换来凑另一种写法的话，改一次别名就会悄悄失配。
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
