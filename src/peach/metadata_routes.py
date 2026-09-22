"""查询侧的来源路由：一个番号属于哪种内容，因此问哪几家、什么顺序、何时停。

分工先说清楚。本模块只管**问**：番号的内容类型、该类型的有序来源链、以及一档取到
必填标量字段之后不再问下一档。取回来的值怎么排序、怎么结算分歧、哪个字段听谁的，
在 `metadata_policy`（`FIELD_SOURCE_ORDER`、`PREFERRED_COMMUNITY_SOURCE`、
`FALLBACK_SOURCES`）与落库那一侧，两条轴不要混：javbus 在结算上是兜底
（ADR-0035），在查询上却排在 javdb 前面——javdb 按出口 IP 计配额、主机间隔 5 秒，
先问便宜的那两家不影响结算，只影响谁先撞上限流。

链的取舍参考 amane 的 `docs/dev/content-routes.md`（证据登记在
`docs/reference-sources.json` 的 `amane-content-routes`），原则照搬三条：类型专属源
靠前、综合索引垫后；对不匹配番号仍发 HTTP 的站不进默认链；会把无关番号拼成
「看起来像详情页」的站一概不进。成员只取 Peach 已经接好解析器的那几家，上游表里
kin8、mgstage、theporndb、getchu 这些 Peach 没有适配器，不写进来占位。

链上没有国产、欧美与里番三条：Peach 一家对应来源都没接，写一条空链只会让人以为
问过了。真要接的时候按同一张表加类型，判据写在这里。
"""
from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

from .catalog_rules import is_amateur_code, is_korean_mib_code, is_uncensored_code
from .metadata_policy import SOURCE_SPECS


#: 内容类型。`unknown` 是「番号认不出来」，不是一种内容。
CONTENT_TYPES = ("censored", "amateur", "uncensored", "fc2", "kmib", "unknown")

#: MGStage 素人系的字母前缀。三位数字前缀那一批由 `catalog_rules.is_amateur_code`
#: 认（`300MIUM-1239`、`259LUXU-1475`），这三种没有数字前缀，形态上和厂牌番号一样，
#: 只能按前缀列出来。它们和三位数字前缀一起写在 `catalog_rules._RELEASE_SYSTEM_SHAPE`
#: 里，那条判据已经把它们当作「发行体系自己的写法」，这里只是把同一批前缀用在路由上。
#: **`ABP` / `ABF` / `ABW` 不在此列**：那是 Prestige 的有码番号，mgstage 首页同时挂
#: 有码号与素人号，按站点归类会把整个 Prestige 判成素人。
MGS_AMATEUR_PREFIXES = ("SIRO", "STP", "STN")
_MGS_AMATEUR = re.compile(r"^(?:" + "|".join(MGS_AMATEUR_PREFIXES) + r")-?\d+$", re.I)

#: 每种内容类型问哪几家，从左到右。每条链后面的注释回答两件事：为什么是这个顺序，
#: 以及为什么某一家**不**在这条链上——后者才是省请求的地方。
ROUTES: dict[str, tuple[str, ...]] = {
    # 有码：官方镜像 r18.dev 先问，一次请求给标题、厂牌、系列、发行日与演员；它没有
    # 或出错才落到三家综合索引。AVBase 与 JavBus 各一次请求，javdb 两次且按出口 IP
    # 计配额（`SOURCE_INTERVALS` 里 5 秒一页），所以 javdb 排最后。
    # 不进这条链：1pondo（无码片商，有码番号一律 404）、fc2（商品号体系不同）。
    "censored": ("r18dev", "avbase", "javbus", "javdb"),
    # 素人：链和有码相同，理由是 Peach 这条采集路上**没有** mgstage 适配器——
    # mgstage 只在 Javinizer-Go 那一侧（`metadata_policy.PROFILE_SOURCES`）。
    # amane 把 MGS 放素人第一源、并且明确不让它进有码默认表（否则 MIDV 也会去问
    # MGS）；Peach 这里的等价做法是把素人单列成一种类型，等 mgstage 解析器接进来
    # 直接加在链首，而不是现在就往有码链里塞一个对多数番号必然落空的站。
    # r18.dev 留着：素人号在 DMM 数字版目录上有没有，本机没有实测，凭「大概没有」
    # 把官方那一档摘掉，省一次请求换来的是整类番号再也拿不到官方值。
    "amateur": ("r18dev", "avbase", "javbus", "javdb"),
    # 无码：发行方自己那份作品 JSON 先问，但只在本机证据指着一本道时才问
    # （见 `route_for_code`）——日期式番号不带片商，カリビアンコム 与一本道同形，
    # 问错一家答回来的是同一天发行的另一部片。
    # **不含 r18dev**：无码番号在 r18.dev 上没有（`docs/SOURCING.md`「一本道作品
    # 资料与封面」、`catalog_rules.is_uncensored_release` 的实测注释、
    # `metadata_policy.PROFILE_SOURCES['uncensored']` 同样不列它）。留着它等于每个
    # 无码番号白等一次主机间隔，再把「问了都没有」读成「上游没有」。
    # avsox 经 amane 桥（ADR-0043）垫在最后：它专收无码，但是转载索引，且要经 Cloudflare，
    # 三家综合索引都落空才轮到它。
    "uncensored": ("1pondo", "avbase", "javbus", "javdb", "avsox"),
    # FC2：发行方商品页 → 下架作品的镜像站 → JavArchive → FC2 专站 → javdb。JavArchive
    # 只给标题和一张转存封面，比官方原图差一档，所以排在两个存档站之后。fc2club 经
    # amane 桥问（ADR-0043），只收 FC2，所以排在综合索引 javdb 前面。
    # 不含 r18dev（实测 85 条全空）、不含 AVBase 与 JavBus（本机 1213 份来源证据里
    # 这两家对 FC2 番号一份都没给过，javdb 给了 166 份）。判据原文在
    # `community_catalog.community_sources_for` 与 `docs/SOURCING.md`。
    "fc2": ("fc2", "fc2cmadb", "javarchive", "fc2club", "javdb"),
    # 韩国 MIB 一家都不问：番号和日本番号同形，JAV 目录站按它去查返回的是别的作品，
    # 那份错值只能靠人一条条认出来。官网走 `scripts/harvest_kmib.py`，不在这条路上。
    "kmib": (),
    "unknown": (),
}

#: 发行方与专站那一档。链上排在综合索引前面，取到必填标量字段就短路。FC2 的两个存档站
#: 按来源分级是 community，但在链上属于这一档：它们只收 FC2，不是综合索引。
OFFICIAL_STAGE = ("r18dev", "1pondo", "fc2", "fc2cmadb", "javarchive")
#: 综合索引那一档。这一档**不**逐家短路：免复核要两家取值一致（ADR-0030、
#: ADR-0034），封面互证要两个不同图源（ADR-0032），问到第一家就停等于把这两条
#: 判据的样本降到一家。
COMMUNITY_STAGE = ("avbase", "javbus", "javdb")
#: 经 amane 桥问的那一档（`metadata_amane.SITES`，ADR-0043）。一次子进程并发问链上属于
#: 这一档的几站，所以合成一档 `amane`；分级上都是社区来源，但不占 `COMMUNITY_STAGE`
#: 的 `LIST_FIELD_DEPTH` 名额——那三家的互证样本不该被转载站挤掉。链上放在综合索引之前
#: 还是之后由各类型的链自己定：FC2 专站在 javdb 前，无码的 avsox 在最后。
AMANE_STAGE = ("fc2club", "freejavbt", "airav", "avsox")

#: 必填标量字段。一档把这几项（在这一行还缺的范围内）都给全了就不问下一档。
SCALAR_FIELDS = ("title", "performers", "studio", "release_date")
#: 列表字段：一档给了也不算「够了」，因为多一家就多一批标签与一个图源。
LIST_FIELDS = ("tags", "cover_url")
#: 列表字段在综合索引那一档最多问到第几家。3 是下限不是上限：两家一致才免复核、
#: 两个图源才算互证，砍到 2 家就等于任何一家缺席都退回人工复核。
LIST_FIELD_DEPTH = 3


def classify(code: str | None, *hints: str | None) -> str:
    """这个番号属于哪种内容。`hints` 是本机证据（路径、文件名、账本厂牌）。

    只看番号形状与本机证据，不依赖任何抓取结果：一旦改成「先拿到元数据再判断」，
    没有元数据的番号就永远轮不到该问的那个来源。

    「文件名被读成番号的创作者作品」不是一种内容类型：那道门在更前面，由
    `catalog_rules.scrapes_as_jav` 拦（`docs/SOURCING.md`「哪些行不该进 JAV 刮削」），
    过不了那道门的行根本不会走到路由这一步。
    """
    value = str(code or "").strip()
    if not value:
        return "unknown"
    if is_korean_mib_code(value):
        return "kmib"
    # `FC-437689` 这类变体由 `catalog_rules.normalise_code_key` 在入库前统一成
    # `FC2-PPV-…`，所以这里只认 `FC2` 开头。
    if value.upper().startswith("FC2"):
        return "fc2"
    if is_uncensored_code(value):
        return "uncensored"
    if is_amateur_code(value) or _MGS_AMATEUR.match(value.upper()):
        return "amateur"
    return "censored"


def parse_route_overrides(raw: str | Mapping[str, Sequence[str] | str] | None):
    """用户给的每类型覆盖。文本写法 `censored=r18dev,javdb;fc2=fc2`。

    形状与用途跟 `metadata_policy.parse_sources` 同一套：来源名必须在
    `SOURCE_SPECS` 里登记过，类型名必须是 `CONTENT_TYPES` 之一，不认识的直接报错
    而不是静默忽略——静默忽略的表现是「设置改了没生效」，比报错难查得多。
    空链合法，意思是这类内容一家都不问。
    """
    if raw is None:
        return {}
    items: Iterable[tuple[str, Sequence[str] | str]]
    if isinstance(raw, str):
        items = [tuple(part.split("=", 1)) for part in raw.split(";") if part.strip()]  # type: ignore[misc]
    else:
        items = list(raw.items())
    overrides: dict[str, tuple[str, ...]] = {}
    for entry in items:
        if len(entry) != 2:
            raise ValueError("来源链覆盖要写成 `类型=来源,来源`")
        name, value = entry
        content = str(name).strip()
        if content not in CONTENT_TYPES:
            raise ValueError("未知内容类型：" + content)
        parts = value.split(",") if isinstance(value, str) else list(value)
        sources = tuple(dict.fromkeys(
            str(part).strip() for part in parts if str(part).strip()))
        unknown = [source for source in sources if source not in SOURCE_SPECS]
        if unknown:
            raise ValueError("未知来源：" + "、".join(unknown))
        overrides[content] = sources
    return overrides


def route(content_type: str, *, overrides: Mapping[str, Sequence[str]] | None = None):
    """这种内容的有序来源链。用户覆盖整条替换，不做逐项合并。

    逐项合并的表现是「删不掉一家」：用户想摘掉 javdb 就得先知道内建表里有它。
    整条替换让设置里那一行自己就是答案。
    """
    if content_type not in ROUTES:
        raise ValueError("未知内容类型：" + str(content_type))
    resolved = parse_route_overrides(overrides)
    if content_type in resolved:
        return resolved[content_type]
    return ROUTES[content_type]


def route_for_code(code: str | None, *hints: str | None,
                   overrides: Mapping[str, Sequence[str]] | None = None):
    """这个番号的来源链，已按本机证据裁过。

    无码那条链上的 `1pondo` 要证据：日期式番号本身不带片商，只有路径、文件名或账本
    厂牌指着一本道时才问它，问不着的照旧落到综合索引（`metadata_1pondo`
    的模块说明）。
    """
    chain = route(classify(code, *hints), overrides=overrides)
    if "1pondo" in chain:
        from .metadata_1pondo import movie_id, names_this_studio
        if not (movie_id(str(code or "")) and names_this_studio(*hints)):
            chain = tuple(source for source in chain if source != "1pondo")
    return chain


def community_route(code: str | None, *hints: str | None,
                    overrides: Mapping[str, Sequence[str]] | None = None):
    """这个番号在综合索引那一档问哪几家，顺序同链，最多 `LIST_FIELD_DEPTH` 家。"""
    chain = route_for_code(code, *hints, overrides=overrides)
    return tuple(source for source in chain
                 if source in COMMUNITY_STAGE)[:LIST_FIELD_DEPTH]


def stages_for_code(code: str | None, *hints: str | None,
                    overrides: Mapping[str, Sequence[str]] | None = None):
    """链按「档」摊给采集任务：官方那几家逐个是一档，综合索引合成一档 `community`。

    综合索引合成一档是因为那一档不逐家短路（见 `COMMUNITY_STAGE`）；官方那几家
    逐个成档，取到必填标量就不问下一档。FC2 那三家是同一次
    `LibraryMetadataProvider.fc2()` 里先后问的三处，合成一档 `fc2`。
    """
    chain = route_for_code(code, *hints, overrides=overrides)
    stages: list[str] = []
    for source in chain:
        name = "fc2" if source in ("fc2", "fc2cmadb", "javarchive") else source
        if source in COMMUNITY_STAGE:
            name = "community"
        if source in AMANE_STAGE:
            name = "amane"
        if name not in stages:
            stages.append(name)
    return tuple(stages)


def stage_members(stage: str, chain: Sequence[str]):
    """这一档在链上对应哪几个来源名。缓存与证据文件都按来源名存，不按档名。"""
    if stage == "community":
        return tuple(source for source in chain if source in COMMUNITY_STAGE)
    if stage == "fc2":
        return tuple(source for source in chain
                     if source in ("fc2", "fc2cmadb", "javarchive"))
    if stage == "amane":
        return tuple(source for source in chain if source in AMANE_STAGE)
    return (stage,) if stage in chain else ()


def amane_route(code: str | None, *hints: str | None,
                overrides: Mapping[str, Sequence[str]] | None = None):
    """这个番号经 amane 桥问哪几站，顺序同链。一次子进程把它们并发问完。"""
    chain = route_for_code(code, *hints, overrides=overrides)
    return tuple(source for source in chain if source in AMANE_STAGE)


def official_route(code: str | None, *hints: str | None,
                   overrides: Mapping[str, Sequence[str]] | None = None):
    """链上属于官方／发行方那一档的成员，顺序同链。"""
    chain = route_for_code(code, *hints, overrides=overrides)
    return tuple(source for source in chain if source in OFFICIAL_STAGE)


def required_scalars(missing: Iterable[str]):
    """这一行还缺、且属于必填标量的那些字段。空集合表示没有可短路的目标。"""
    wanted = set(str(field) for field in missing)
    return tuple(field for field in SCALAR_FIELDS if field in wanted)


def settles(required: Sequence[str], provided: Iterable[str]) -> bool:
    """这一档给的字段够不够停手。

    `required` 空时任何一档只要给出资料就停——这一行要的本来就不是标量字段，
    再问下一档只会拿回一堆和账本现值相同的候选（ADR-0033）。
    """
    if not required:
        return True
    given = set(str(field) for field in provided)
    return all(field in given for field in required)
