"""Pure Javinizer-Go source policy owned by Peach."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .catalog_rules import is_korean_mib_code, is_uncensored_code


POLICY_VERSION = "metadata-source-policy-v4"
PEACH_FIELDS = (
    "title", "original_title", "performers", "studio", "series", "release_date", "tags",
)
REGISTERED_SOURCES = (
    "r18dev", "libredmm", "dmm", "javlibrary", "javdb", "javbus", "jav321",
    "mgstage", "tokyohot", "aventertainment", "caribbeancom", "dlgetchu",
    "fc2", "javstash",
)


@dataclass(frozen=True)
class SourceSpec:
    name: str
    kind: str

    @property
    def official(self) -> bool:
        return self.kind in {"official", "official_mirror"}


SOURCE_SPECS = {
    name: SourceSpec(name, kind) for name, kind in {
        "r18dev": "official_mirror", "libredmm": "official_mirror",
        "dmm": "official", "mgstage": "official", "tokyohot": "official",
        "aventertainment": "official", "caribbeancom": "official",
        "dlgetchu": "official", "fc2": "official",
        "javlibrary": "community", "javdb": "community", "javbus": "community",
        "jav321": "community", "javstash": "community",
        "sougouwiki": "community",
        # AVBase 汇总各店铺的商品条目，采集任务在官方渠道落空时直接请求它
        # （peach.community_catalog）。同样不走 Javinizer-Go。
        "avbase": "community",
        # 韩国 MIB 的官网（scripts/harvest_kmib.py）。不走 Javinizer-Go，所以不进
        # REGISTERED_SOURCES；登记在这里是为了复核与自动批准按官方来源对待它。
        "kmib": "official",
        # FC2 下架作品的镜像站。它转载的是发行方那一页，但标题和标签由站方用户维护，
        # 所以按社区来源对待：取值进复核，不当官方证据。同样不走 Javinizer-Go。
        "fc2cmadb": "community",
        # fc2cmadb 也没有的下架 FC2 的最后一档（`peach.metadata_fc2.parse_archive`）。
        # 转载站，标题由发布者写，封面是转存件，按社区来源对待。登记在这里还有一层作用：
        # 「没有」的记忆按 `sources_fingerprint` 作废，接上这一档，此前压着「三处都没有」
        # 的番号下一轮就会重问一遍，不必等 TTL 走完。
        "javarchive": "community",
        # 一本道的官网作品 JSON（`peach.metadata_1pondo`）。发行方自己那一份，不走
        # Javinizer-Go，所以同样不进 REGISTERED_SOURCES。
        "1pondo": "official",
    }.items()
}

#: 社区来源之间不一致时听这一家的。用户 2026-09-16 逐条核对过：javdb 比 javbus 准
#: （ADR-0034）。实测 `n0780` 的片长 javbus 报 36 分、javdb 报 96 分，盘里那条是 98 分。
PREFERRED_COMMUNITY_SOURCE = "javdb"

#: 兜底来源：同一个字段上还有别家可用时，它的取值不当证据（ADR-0035）。用户
#: 2026-09-16 逐条核对：javbus 的取值常常来自另一部片，`259LUXU-891` 它答的是
#: `259LUXU-1891`（ラグジュTV 1879，2026-07-29），而官方 mgstage 那页写的是
#: ラグジュTV 853、2017-11-26。只有一家都没有时才轮到它。
FALLBACK_SOURCES = ("javbus",)

#: 视频旁边那份 NFO。它不是联网来源，所以不进 `SOURCE_SPECS`，但字段优先级链
#: 要给它排一个位置（ADR-0029 起它就是补空证据），名字只能有一份。
LOCAL_NFO_SOURCE = "local_nfo"

#: 字段优先级链的层级，数字越小越先被采信（ADR-0038）。用户自己整理的 NFO 在最前，
#: 其次是发行方自己那页，再次是逐条核对过的 javdb，然后是其余社区站，最后是兜底。
#: 未登记的来源排在所有已知来源之后：它不构成证据，但也不该把整条链判成无解。
CHAIN_LOCAL_NFO, CHAIN_OFFICIAL, CHAIN_PREFERRED = 0, 1, 2
CHAIN_COMMUNITY, CHAIN_FALLBACK, CHAIN_UNKNOWN = 3, 4, 5

#: 稀疏例外：某个字段上把几家来源提到链首，顺序就是这里写的顺序（对应 amane 的
#: `field_priority`）。整条链已经按「谁更接近发行方」排好，这张表只用来记录逐条
#: 核对后发现的反例，不是第二份来源顺序表——每加一行都要能说出是哪个番号上看出来的。
#: 本机当前一条例外都没有，空表就是「链本身够用」的如实记录。
FIELD_SOURCE_PRIORITY: dict[str, tuple[str, ...]] = {}

#: 字段级黑名单（对应 amane 的 `field_blacklist`），优先于一切：列进来的来源在这个
#: 字段上连候选都不算，不参与取值比对，也不会因为「只剩它一家」而被采信。它和兜底
#: 来源不是一回事——兜底是「有别家就退开」，黑名单是「这个字段上它说什么都不听」。
FIELD_SOURCE_BLACKLIST: dict[str, frozenset[str]] = {}


def source_tier(source: str) -> int:
    """这家来源在字段优先级链上的层级。"""
    name = str(source or "").strip()
    if name == LOCAL_NFO_SOURCE:
        return CHAIN_LOCAL_NFO
    if name in FALLBACK_SOURCES:
        return CHAIN_FALLBACK
    spec = SOURCE_SPECS.get(name)
    if spec is None:
        return CHAIN_UNKNOWN
    if spec.official:
        return CHAIN_OFFICIAL
    if name == PREFERRED_COMMUNITY_SOURCE:
        return CHAIN_PREFERRED
    return CHAIN_COMMUNITY


def chain_rank(field: str, source: str) -> tuple[int, int, str]:
    """字段优先级链上的排序键，越小越先采信。

    层内用 `FIELD_SOURCE_ORDER` 再排一次：官方来源之间谁更接近这部片的发行方，
    那张表早就按字段排过，不必再写第二份。表里没有的来源排在同层末尾，名字兜底
    保证同分时顺序是确定的——不确定的顺序会让同一批候选在两次运行里落不同的值。
    """
    name = str(source or "").strip()
    priority = FIELD_SOURCE_PRIORITY.get(field, ())
    if name in priority:
        return (-1, priority.index(name), name)
    order = FIELD_SOURCE_ORDER.get(field, ())
    within = order.index(name) if name in order else len(order)
    return (source_tier(name), within, name)


def blacklisted(field: str, source: str) -> bool:
    """这个字段上这家来源是不是被判了不听。"""
    return str(source or "").strip() in FIELD_SOURCE_BLACKLIST.get(field, frozenset())

PROFILE_SOURCES = {
    "seesaa": ("sougouwiki",),
    "baseline": ("r18dev",),
    "censored": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "dlgetchu", "javlibrary", "javdb", "javbus", "jav321", "javstash",
    ),
    "uncensored": (
        "tokyohot", "caribbeancom", "javdb", "javlibrary", "javstash",
    ),
    "fc2": ("fc2",),
    # 官方与官方镜像的补抓组合，用于 r18dev 落空或只给泛化类别的有码番号。
    # 两条约束决定了这五个：
    # 一、只列 javinizer config 当前启用的 scraper。没启用的来源不返回「查无此片」，
    #     而是返回 unknown 错误，一旦落进快照就会被当成确定失败长期复用。
    # 二、不含 tokyohot 与 caribbeancom。它们只认无码番号形状，对有码番号是稳定
    #     404，放进来等于每个番号多两次白跑的网络请求；无码走 `uncensored`。
    # 三、不含 dlgetchu。它是同人商店，对 JAV 番号从来搜不到对应商品，却会把站内
    #     首条命中当结果返回——`identifies_code` 现在拦得住，但每个番号仍要为一次
    #     必然作废的往返付钱。
    "official-backfill": (
        "mgstage", "dmm", "libredmm", "aventertainment",
    ),
}

#: 番号形状就能确定发行面，不必先有元数据证明。判据本身是纯规则，和徽章共用
#: `catalog_rules.is_uncensored_code` 一份——两处各写一份迟早会漂移。
#: 语料实测：8 个这种番号——carib 2、1pon 4、HEYZO 2，官方 tag 全为 0。它们此前
#: 一直按有码番号去问 mgstage/dmm，那几家根本不发行这些片，于是「问了都没有」
#: 被读成「上游没有」。caribbeancom 实测取得到 `040221-001` 的完整标题、日期
#: 和 10 个 genre。

#: 按发行面分流的 profile。`sources` 是并集（来源健康表要覆盖全部），
#: 每个番号实际问哪几家由 `sources_for_code` 决定。
ROUTED_PROFILE_SOURCES = {
    "backfill": {
        # 1Pondo 与 HEYZO 没有官方 adapter，javdb/javlibrary 在本机被
        # Cloudflare 与 403 挡住（不绕机器人检测），javbus 是唯一问得到的一家；
        # 它是 community，取值只能进人工复核，不进免复核写入。
        "uncensored": ("caribbeancom", "tokyohot", "javbus"),
        "censored": ("mgstage", "dmm", "libredmm", "aventertainment", "javdb"),
    },
}
for _name, _routes in ROUTED_PROFILE_SOURCES.items():
    PROFILE_SOURCES[_name] = tuple(dict.fromkeys(
        source for group in _routes.values() for source in group))


FIELD_SOURCE_ORDER = {
    "title": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "1pondo", "tokyohot", "fc2", "javdb", "javlibrary",
        "javbus", "javstash", "jav321", "dlgetchu",
    ),
    "original_title": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "1pondo", "tokyohot", "fc2", "javdb", "javlibrary",
        "javbus", "javstash", "jav321", "dlgetchu",
    ),
    "performers": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "1pondo", "tokyohot", "fc2", "javdb", "javbus",
        "javlibrary", "javstash", "jav321", "dlgetchu",
    ),
    "studio": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "1pondo", "tokyohot", "fc2", "javdb", "javbus",
        "javlibrary", "javstash", "jav321", "dlgetchu",
    ),
    "series": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "1pondo", "tokyohot", "fc2", "javdb", "javlibrary",
        "javbus", "javstash", "jav321", "dlgetchu",
    ),
    # aventertainment 是面向海外的转售商，不是发行方，它给的是自己的上架日期：
    # `071213-625` 它答 2017-12-28，而这个番号本身就是发行日 2013-07-12
    # （javbus 与番号一致）；`092415-001` 同样差了 9 个月。发行方站点排在
    # 转售商前面，两个字段都要改——只改 tags 会留下一个照样写错日期的路径。
    "release_date": (
        "dmm", "libredmm", "mgstage", "tokyohot", "caribbeancom", "1pondo",
        "aventertainment", "dlgetchu", "fc2", "r18dev", "javdb",
        "javlibrary", "javbus", "jav321", "javstash",
    ),
    # tag 单独把 mgstage 提到 dmm 之前。ABW-220 实测：mgstage 商品页给
    # 「性教育・中出し・巨乳・スレンダー」等 8 项，dmm 走的 mono/dvd 页和
    # libredmm 都只给「AV女優・単体作品・サンプル動画」3 项泛化类别，r18dev
    # 同样只有 3 项。厂牌、系列、日期这些字段仍以 dmm 为准，不跟着改。
    "tags": (
        "mgstage", "dmm", "libredmm", "tokyohot", "caribbeancom", "1pondo",
        "aventertainment", "dlgetchu", "fc2", "r18dev", "javstash",
        "javdb", "javlibrary", "javbus", "jav321",
    ),
}


@dataclass(frozen=True)
class MetadataPolicy:
    profile: str
    sources: tuple[str, ...]
    version: str = POLICY_VERSION

    def field_rank(self, field: str, source: str) -> int:
        order = FIELD_SOURCE_ORDER[field]
        try:
            return order.index(source) + 1
        except ValueError:
            return len(order) + 1

    def source(self, name: str) -> SourceSpec:
        return SOURCE_SPECS[name]

    def sources_for_code(self, code: str) -> tuple[str, ...]:
        """这个番号该问哪几家。未分流的 profile 一律返回全部来源。"""
        routes = ROUTED_PROFILE_SOURCES.get(self.profile)
        if not routes:
            return self.sources
        group = "uncensored" if is_uncensored_code(code) else "censored"
        return tuple(source for source in self.sources if source in routes[group])

    def allows_code(self, code: str, *, include_fc2: bool = False,
                    explicit_sources: bool = False) -> bool:
        # 韩国 MIB 不适用 JAV 规则，任何 profile 都不问：JAV 目录站对这些番号只会
        # 返回别的作品，而那份错值一旦落进候选队列，就要靠人一条条认出来。
        # 这道拦截优先于 profile 与 `--sources`——它不是「这次不想问」，是「问了必错」。
        if is_korean_mib_code(code):
            return False
        is_fc2 = str(code or "").upper().startswith("FC2")
        if self.profile == "fc2":
            return is_fc2
        if not is_fc2:
            return True
        return include_fc2 or (explicit_sources and "fc2" in self.sources)


def parse_sources(raw: str | Sequence[str]) -> tuple[str, ...]:
    values = raw.split(",") if isinstance(raw, str) else list(raw)
    sources = tuple(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))
    if not sources:
        raise ValueError("至少指定一个 Javinizer-Go source")
    unknown = [source for source in sources if source not in SOURCE_SPECS]
    if unknown:
        raise ValueError("未知 Javinizer-Go source：" + ", ".join(unknown))
    return sources


def resolve_policy(*, profile: str | None = None,
                   sources: str | Sequence[str] | None = None) -> MetadataPolicy:
    if profile and sources is not None:
        raise ValueError("--profile 与 --sources 不能同时使用")
    if profile:
        if profile not in PROFILE_SOURCES:
            raise ValueError("未知 metadata source profile：" + profile)
        return MetadataPolicy(profile, PROFILE_SOURCES[profile])
    if sources is not None:
        return MetadataPolicy("custom", parse_sources(sources))
    return MetadataPolicy("baseline", PROFILE_SOURCES["baseline"])


def sort_candidates(field: str, candidates: Iterable[Mapping[str, object]],
                    policy: MetadataPolicy) -> list[dict]:
    if field not in PEACH_FIELDS:
        raise ValueError("未知 Peach 元数据字段：" + field)
    rows = [dict(candidate) for candidate in candidates]
    for row in rows:
        source = str(row.get("source") or "")
        row["field_rank"] = policy.field_rank(field, source)
    rows.sort(key=lambda row: (
        int(row["field_rank"]),
        -float(row.get("confidence") or 0),
        str(row.get("source") or ""),
    ))
    return rows
