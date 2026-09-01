"""Pure Javinizer-Go source policy owned by Peach."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


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
    }.items()
}

PROFILE_SOURCES = {
    "baseline": ("r18dev",),
    "censored": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "dlgetchu", "javlibrary", "javdb", "javbus", "jav321", "javstash",
    ),
    "uncensored": (
        "tokyohot", "caribbeancom", "javdb", "javlibrary", "javstash",
    ),
    "fc2": ("fc2",),
    # 官方与官方镜像的补抓组合，用于 r18dev 落空或只给泛化类别的番号。
    # 只列 javinizer config 当前启用的 scraper：没启用的来源不会返回「查无此片」，
    # 而是返回 unknown 错误，一旦落进快照就会被当成确定失败长期复用。
    "official-backfill": (
        "mgstage", "dmm", "libredmm", "aventertainment", "dlgetchu",
        "tokyohot", "caribbeancom",
    ),
}

FIELD_SOURCE_ORDER = {
    "title": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "tokyohot", "fc2", "javdb", "javlibrary",
        "javbus", "javstash", "jav321", "dlgetchu",
    ),
    "original_title": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "tokyohot", "fc2", "javdb", "javlibrary",
        "javbus", "javstash", "jav321", "dlgetchu",
    ),
    "performers": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "tokyohot", "fc2", "javdb", "javbus",
        "javlibrary", "javstash", "jav321", "dlgetchu",
    ),
    "studio": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "tokyohot", "fc2", "javdb", "javbus",
        "javlibrary", "javstash", "jav321", "dlgetchu",
    ),
    "series": (
        "dmm", "libredmm", "r18dev", "mgstage", "aventertainment",
        "caribbeancom", "tokyohot", "fc2", "javdb", "javlibrary",
        "javbus", "javstash", "jav321", "dlgetchu",
    ),
    "release_date": (
        "dmm", "libredmm", "mgstage", "tokyohot", "aventertainment",
        "caribbeancom", "dlgetchu", "fc2", "r18dev", "javdb",
        "javlibrary", "javbus", "jav321", "javstash",
    ),
    # tag 单独把 mgstage 提到 dmm 之前。ABW-220 实测：mgstage 商品页给
    # 「性教育・中出し・巨乳・スレンダー」等 8 项，dmm 走的 mono/dvd 页和
    # libredmm 都只给「AV女優・単体作品・サンプル動画」3 项泛化类别，r18dev
    # 同样只有 3 项。厂牌、系列、日期这些字段仍以 dmm 为准，不跟着改。
    "tags": (
        "mgstage", "dmm", "libredmm", "tokyohot", "aventertainment",
        "caribbeancom", "dlgetchu", "fc2", "r18dev", "javstash",
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

    def allows_code(self, code: str, *, include_fc2: bool = False,
                    explicit_sources: bool = False) -> bool:
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
