"""追更来源的单点登记表。

新增一个站点只改这张表。同一份知识散成六处的话——`follow_cli` 的 URL 模板与 release
集合、`follow_sources` 的语义表、`follow_stream` 的主机白名单、`follow_variants` 的
优先级、`web_follow` 的显示名与两个能力集合——漏掉任何一张都不会报错，只会在某个页面上
少一行、某个媒体代理拒绝一条链接，或者选主条目时排到最后。

更糟的是其中两张表说的是同一件事：`_RELEASE_PROVIDERS` 是集合、`_SEMANTICS` 是
映射，键必须完全一致，值只能是 `release`。谁改了一处忘了另一处，分组语义就会和
优先级排序对不上，而且两边都不会抛错。

所以这里只登记一次，各模块从这张表派生自己那份投影，形状保持不变。

**不包含凭据。**哪些字段可以跨机同步由 `follow_secrets.CREDENTIAL_GUIDE` 逐字段声明，
`SYNCABLE_FIELDS` 已经是它的派生视图。那是安全语义，收进这张通用表只会让它更容易
被顺手改错——新增来源时作者必须在凭据表里单独表态，这个摩擦是故意的。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSpec:
    """一个追更来源在各层的全部登记信息。

    `source_url` 为 None 表示它不是追更来源，只是会出现在界面上的媒体来源（如 Gofile）。
    `hosts` 为空表示它的媒体不经本地代理取回（官方三家走各自的详情接口）。
    """

    key: str
    label: str
    source_url: str | None = None
    semantics: str = "work"
    hosts: tuple[str, ...] = ()
    priority: int = 99
    backfill: bool = False
    official_identity: bool = False
    #: 用户明确点名要隐藏的既有条目（站内 id）。只影响浏览面，不删 ledger 行。
    excluded_external_ids: tuple[str, ...] = ()
    #: 粘一条链接时，哪些站点主机认成这个来源。子域也算（`x.fanbox.cc`、
    #: `api.rule34.xxx`），所以这里只写注册域那一截。**不是** `hosts`：那是媒体
    #: 代理的白名单，值可能完全不同（paheal 的站点是 `rule34.paheal.net`，
    #: 媒体在 `paheal-cdn.net`）。
    url_hosts: tuple[str, ...] = ()
    #: 这个来源的每个条目都是一次独立发布，即使标题相同。
    #: F95 的线程标题只是容器名，每个带资源的楼层各自成组。
    release_key_per_post: bool = False

    def __post_init__(self) -> None:
        if self.semantics not in ("work", "release"):
            raise ValueError(f"{self.key} 的 semantics 只能是 work 或 release")
        if self.source_url and not self.url_hosts:
            raise ValueError(f"{self.key} 是追更来源，必须登记至少一个 url_hosts")


def _spec(key: str, label: str, **kwargs) -> ProviderSpec:
    return ProviderSpec(key=key, label=label, **kwargs)


#: 唯一登记处。priority 越小越优先做主条目；未列出的来源排在最后。
PROVIDERS: dict[str, ProviderSpec] = {
    spec.key: spec
    for spec in (
        # 官方渠道：只读公开免费发布，身份可信，所以优先做主条目；媒体走各自详情接口，
        # 不经本地代理，因此没有 hosts。
        _spec("fanbox", "FANBOX", source_url="https://{ref}.fanbox.cc/",
              url_hosts=("fanbox.cc",), priority=1, official_identity=True),
        _spec("subscribestar", "SubscribeStar", source_url="https://{ref}",
              url_hosts=("subscribestar.adult", "subscribestar.com"),
              priority=2, official_identity=True),
        _spec("patreon", "Patreon", source_url="https://www.patreon.com/cw/{ref}",
              url_hosts=("patreon.com",), priority=3, official_identity=True),
        # 归档站：同一套代码的姊妹站，支持真实历史分页所以可回填。
        _spec("kemono", "Kemono", source_url="https://kemono.cr/{ref}",
              hosts=("kemono.cr",), url_hosts=("kemono.cr",),
              priority=10, backfill=True),
        _spec("pawchive", "Pawchive", source_url="https://pawchive.pw/{ref}",
              hosts=("pawchive.pw",), url_hosts=("pawchive.pw",),
              priority=15, backfill=True),
        _spec("coomer", "Coomer", source_url="https://coomer.st/{ref}",
              hosts=("coomer.st",), url_hosts=("coomer.st",),
              priority=20, backfill=True),
        # 标签／模特站。
        # `excluded_external_ids` 是用户明确点名的那个既有超大合集。连接器现在按
        # 详情页署名作者数拦截同类条目；这一条只让已经入库的旧候选立即从浏览面消失。
        _spec("rule34video", "Rule34Video",
              source_url="https://rule34video.com/models/{ref}/",
              # 正片不在站内：详情页给的 `/get_file/…` 会 302 到 `*.boomio-cdn.com`
              # （2026-09-04 实测 eu-cdn05／06／08／11-prem 四个节点，最终一跳才是
              # 206 `video/mp4`）。少了这个后缀，媒体代理会在跳出白名单那一步拒收，
              # 整站的视频一条都放不出来。
              hosts=("rule34video.com", "boomio-cdn.com"),
              url_hosts=("rule34video.com",),
              priority=30, backfill=True,
              excluded_external_ids=("4533145",)),
        _spec("rule34xxx", "Rule34.xxx",
              source_url="https://rule34.xxx/index.php?page=post&s=list&tags={ref}",
              hosts=("rule34.xxx",), url_hosts=("rule34.xxx",),
              priority=40, backfill=True),
        _spec("rule34paheal", "Rule34 Paheal",
              source_url="https://rule34.paheal.net/post/list/{ref}/1",
              hosts=("paheal.net", "paheal-cdn.net"),
              url_hosts=("rule34.paheal.net",), priority=45, backfill=True),
        # 论坛：每个条目是同一作品的一次发布，不是独立作品。
        _spec("f95zone", "F95zone", source_url="https://f95zone.to/threads/{ref}/",
              semantics="release", hosts=("f95zone.to",), url_hosts=("f95zone.to",),
              priority=50, release_key_per_post=True),
        _spec("simpcity", "SimpCity", source_url="https://simpcity.cr/threads/{ref}/",
              semantics="release", url_hosts=("simpcity.cr",), priority=60),
        # 文件站：不是追更来源，只作为媒体来源出现在界面上，所以没有 source_url。
        _spec("gofile", "Gofile"),
    )
}


def source_urls() -> dict[str, str]:
    """登记订阅时按 provider 拼作品页 URL；只用于展示与去重，不参与抓取。"""
    return {key: spec.source_url for key, spec in PROVIDERS.items() if spec.source_url}


def release_providers() -> frozenset[str]:
    """条目是同一作品历次发布、而非独立作品的来源。"""
    return frozenset(key for key, spec in PROVIDERS.items() if spec.semantics == "release")


def semantics() -> dict[str, str]:
    """非默认语义的来源；`work` 是默认值，不登记。"""
    return {key: spec.semantics for key, spec in PROVIDERS.items() if spec.semantics != "work"}


def labels() -> dict[str, str]:
    """界面上给每个来源的短名。没登记的 provider 直接显示原名。"""
    return {key: spec.label for key, spec in PROVIDERS.items()}


def hosts() -> dict[str, tuple[str, ...]]:
    """媒体代理允许的主机；不在表里的 provider 一律拒绝。"""
    return {key: spec.hosts for key, spec in PROVIDERS.items() if spec.hosts}


def priorities() -> dict[str, int]:
    """同一 `release_key` 下选主条目时的来源优先级；越小越优先。"""
    return {key: spec.priority for key, spec in PROVIDERS.items() if spec.source_url}


def backfill_providers() -> frozenset[str]:
    """支持真实历史分页、因此可以「抓更早一页」的来源。"""
    return frozenset(key for key, spec in PROVIDERS.items() if spec.backfill)


def official_identity_providers() -> frozenset[str]:
    """作者显示名与头像可信的官方渠道；归档站只作回退。"""
    return frozenset(key for key, spec in PROVIDERS.items() if spec.official_identity)


def url_hosts() -> dict[str, str]:
    """站点主机 → 来源键。解析粘进来的链接时用它替代一串 if/elif。

    键只写注册域那一截；子域由 `provider_for_host` 按后缀匹配，所以
    `creator.fanbox.cc` 和 `api.rule34.xxx` 都不必单独登记。
    """
    return {host: key for key, spec in PROVIDERS.items() for host in spec.url_hosts}


def provider_for_host(host: str) -> str:
    """这个主机属于哪个来源。认不出来返回空串。

    先精确匹配，再按最长后缀匹配——后缀更长的登记更具体，必须赢：
    `rule34.paheal.net` 不能被将来某个 `paheal.net` 登记抢走。
    """
    bare = str(host or "").strip().lower().removeprefix("www.")
    table = url_hosts()
    if bare in table:
        return table[bare]
    matched = [registered for registered in table
               if bare.endswith(f".{registered}")]
    return table[max(matched, key=len)] if matched else ""


def release_key_per_post() -> frozenset[str]:
    """每个条目都是一次独立发布的来源；同名条目不合并。"""
    return frozenset(key for key, spec in PROVIDERS.items()
                     if spec.release_key_per_post)


def excluded_external_ids() -> dict[str, frozenset[str]]:
    """按来源列出要从浏览面隐藏的既有条目。没有要隐藏的来源不出现在结果里。"""
    return {key: frozenset(spec.excluded_external_ids)
            for key, spec in PROVIDERS.items() if spec.excluded_external_ids}
