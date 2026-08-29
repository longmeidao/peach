import unittest

from peach import follow_providers
from peach.follow_cli import _RELEASE_PROVIDERS, _SOURCE_URL
from peach.follow_sources import CONNECTORS, _SEMANTICS
from peach.follow_stream import _PROVIDER_HOSTS
from peach.follow_variants import PROVIDER_PRIORITY
from peach.web_follow import (
    CREDENTIAL_GUIDE,
    PROVIDER_LABELS,
    SYNCABLE_FIELDS,
    _BACKFILL_PROVIDERS,
    _OFFICIAL_IDENTITY_PROVIDERS,
)


class ProviderRegistryTests(unittest.TestCase):
    def test_every_connector_is_registered_and_every_source_has_a_connector(self):
        """新增站点漏登记不会自己报错，只会在某个页面上少一行——所以这里挡住。

        有 `source_url` 的 spec 就是追更来源，必须有连接器；反过来每个连接器也必须
        有 spec，否则显示名、优先级、主机白名单都会静默走默认值。"""
        registered = {key for key, spec in follow_providers.PROVIDERS.items() if spec.source_url}
        self.assertEqual(
            registered, set(CONNECTORS),
            "追更来源与连接器必须一一对应；新增站点要同时写连接器和 follow_providers 登记",
        )

    def test_gofile_is_a_media_source_not_a_follow_source(self):
        """Gofile 只作为媒体来源出现在界面上，没有连接器也不该有作品页 URL。"""
        self.assertIn("gofile", PROVIDER_LABELS)
        self.assertNotIn("gofile", CONNECTORS)
        self.assertIsNone(follow_providers.PROVIDERS["gofile"].source_url)
        self.assertNotIn("gofile", _SOURCE_URL)

    def test_release_semantics_is_stated_once(self):
        """`_RELEASE_PROVIDERS` 与 `_SEMANTICS` 说的是同一件事，过去是两份手写清单。

        键必须相同、值只能是 release；改了一处忘了另一处，分组语义会和优先级排序
        对不上，而且两边都不抛错。现在两者都投影自同一个 spec，这条断言守住它。"""
        self.assertEqual(set(_RELEASE_PROVIDERS), set(_SEMANTICS))
        self.assertEqual(set(_SEMANTICS.values()), {"release"})
        for key in _RELEASE_PROVIDERS:
            self.assertEqual(follow_providers.PROVIDERS[key].semantics, "release")

    def test_projections_keep_their_original_shapes(self):
        """各模块的投影形状不变：调用方仍按原来的类型使用它们。"""
        self.assertIsInstance(_SOURCE_URL, dict)
        self.assertIsInstance(_PROVIDER_HOSTS, dict)
        self.assertIsInstance(PROVIDER_PRIORITY, dict)
        self.assertIsInstance(PROVIDER_LABELS, dict)
        self.assertIsInstance(_RELEASE_PROVIDERS, frozenset)
        self.assertIsInstance(_BACKFILL_PROVIDERS, frozenset)
        self.assertIsInstance(_OFFICIAL_IDENTITY_PROVIDERS, frozenset)
        for hosts in _PROVIDER_HOSTS.values():
            self.assertIsInstance(hosts, tuple)
            self.assertTrue(hosts, "登记了主机就不能是空元组，否则代理会全部拒绝")
        for template in _SOURCE_URL.values():
            self.assertIn("{ref}", template, "作品页模板必须能填入 ref")

    def test_priority_is_unique_so_primary_choice_is_deterministic(self):
        values = list(PROVIDER_PRIORITY.values())
        self.assertEqual(len(values), len(set(values)), "优先级重复会让选主条目结果不确定")

    def test_official_identity_providers_do_not_proxy_media(self):
        """官方三家走各自详情接口取媒体，不经本地代理，所以不该有主机白名单。"""
        for key in _OFFICIAL_IDENTITY_PROVIDERS:
            self.assertEqual(follow_providers.PROVIDERS[key].hosts, ())
            self.assertNotIn(key, _PROVIDER_HOSTS)

    def test_backfill_providers_are_archive_sites_with_real_paging(self):
        """只有支持真实历史分页的来源才显示「抓更早一页」；官方渠道不支持。"""
        self.assertTrue(_BACKFILL_PROVIDERS.isdisjoint(_OFFICIAL_IDENTITY_PROVIDERS))
        for key in _BACKFILL_PROVIDERS:
            self.assertIn(key, CONNECTORS)

    def test_registry_carries_no_credential_policy(self):
        """凭据同步策略必须留在 CREDENTIAL_GUIDE 里逐字段声明，不进这张通用表。

        收进来会让它更容易被顺手改错：今天 `api_key` 能同步、`cookie` 不能，
        明天新增 `session_token` 就会落到错误的一侧。新增来源时作者必须单独表态，
        这个摩擦是故意留的。"""
        spec_fields = set(vars(follow_providers.PROVIDERS["fanbox"]))
        for banned in ("syncable", "credential", "cookie", "token", "secret"):
            self.assertNotIn(
                banned, spec_fields, f"ProviderSpec 不得携带凭据相关字段：{banned}",
            )
        self.assertEqual(
            SYNCABLE_FIELDS,
            {provider: tuple(guide.get("syncable", ())) for provider, guide in CREDENTIAL_GUIDE.items()},
            "SYNCABLE_FIELDS 只能从 CREDENTIAL_GUIDE 派生",
        )

    def test_semantics_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            follow_providers.ProviderSpec(key="x", label="X", semantics="whatever")


if __name__ == "__main__":
    unittest.main()
