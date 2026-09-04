import unittest

from peach.metadata_policy import (
    is_uncensored_code,
    FIELD_SOURCE_ORDER,
    POLICY_VERSION,
    PROFILE_SOURCES,
    REGISTERED_SOURCES,
    resolve_policy,
    sort_candidates,
)


class MetadataPolicyTests(unittest.TestCase):
    def test_registry_matches_pinned_javinizer_v151_sources(self):
        self.assertEqual(set(REGISTERED_SOURCES), {
            "r18dev", "libredmm", "dmm", "javlibrary", "javdb", "javbus",
            "jav321", "mgstage", "tokyohot", "aventertainment",
            "caribbeancom", "dlgetchu", "fc2", "javstash",
        })
        self.assertTrue(POLICY_VERSION.startswith("metadata-source-policy-"))

    def test_default_and_named_profiles_are_explicit(self):
        self.assertEqual(resolve_policy().sources, ("r18dev",))
        for profile in ("baseline", "censored", "uncensored", "fc2"):
            self.assertEqual(resolve_policy(profile=profile).sources, PROFILE_SOURCES[profile])

    def test_unknown_source_and_conflicting_inputs_fail_early(self):
        with self.assertRaisesRegex(ValueError, "未知 Javinizer-Go source"):
            resolve_policy(sources="r18dev,imaginary")
        with self.assertRaisesRegex(ValueError, "不能同时"):
            resolve_policy(profile="baseline", sources="r18dev")

    def test_fc2_scope_is_never_guessed_for_other_profiles(self):
        baseline = resolve_policy(profile="baseline")
        self.assertFalse(baseline.allows_code("FC2-PPV-1234567"))
        self.assertTrue(resolve_policy(profile="fc2").allows_code("FC2-PPV-1234567"))
        self.assertFalse(resolve_policy(profile="fc2").allows_code("ABW-232"))
        custom = resolve_policy(sources="r18dev,fc2")
        self.assertTrue(custom.allows_code(
            "FC2-PPV-1234567", explicit_sources=True,
        ))

    def test_korean_mib_codes_are_refused_by_every_profile(self):
        """韩国 MIB 不适用 JAV 规则，任何 profile、任何 `--sources` 都不问。

        这些番号的形状和厂牌番号一样，只有前缀能把它们分出来。放行一次的代价是
        整批错值落进候选队列，再靠人一条条认出来。
        """
        for profile in ("baseline", "censored", "uncensored", "fc2"):
            policy = resolve_policy(profile=profile)
            for code in ("WX-017", "AR-301", "JI-103", "SA-104", "MY-102",
                         "ar-301", "AR301"):
                self.assertFalse(policy.allows_code(code), f"{profile} 放行了 {code}")
        # 显式点名来源也不能绕过：这不是「这次不想问」，是「问了必错」。
        self.assertFalse(resolve_policy(sources="javbus").allows_code(
            "AR-301", explicit_sources=True,
        ))

    def test_two_letter_prefix_alone_never_blocks_a_real_jav_studio(self):
        """判据是实测出来的前缀表，不是「两字母前缀就不是 JAV」那条形状。

        2026-09-04 实测的 24 种两字母前缀里有三个例外：BeFree 的 `BF-366` 是真作品，
        `TZ` 来自转载站水印 `[ThZu.Cc]`，`FC-437689` 是 FC2 变体。按形状一刀切会
        把 BeFree 一起拦掉，而它的片子就在 `B:\\番号\\BeFree\\` 下。
        """
        baseline = resolve_policy(profile="baseline")
        for code in ("BF-366", "ARM-123", "JILL-002", "300MIUM-1239", "ABW-232"):
            self.assertTrue(baseline.allows_code(code), f"baseline 误拦了 {code}")

    def test_every_field_uses_policy_order_and_explicit_official_metadata(self):
        policy = resolve_policy(profile="censored")
        candidates = [
            {"source": "javbus", "confidence": 0.99},
            {"source": "r18dev", "confidence": 0.8},
            {"source": "dmm", "confidence": 0.7},
        ]
        for field in FIELD_SOURCE_ORDER:
            ordered = sort_candidates(field, candidates, policy)
            self.assertEqual(ordered[0]["source"], "dmm", field)
            self.assertEqual(
                [row["field_rank"] for row in ordered],
                sorted(row["field_rank"] for row in ordered),
            )

    def test_tag_backfill_profile_stays_official_and_reachable(self):
        # 这个 profile 的成本全在网络往返上。放宽任何一条都要有实测支撑：
        # 加社区来源等于让未经复核的值排进官方前面；加无码来源等于给每个有码
        # 番号多两次稳定 404。
        policy = resolve_policy(profile="official-backfill")
        self.assertEqual(policy.sources, (
            "mgstage", "dmm", "libredmm", "aventertainment",
        ))
        for source in policy.sources:
            self.assertTrue(policy.source(source).official, source)
        self.assertNotIn("tokyohot", policy.sources)
        self.assertNotIn("caribbeancom", policy.sources)
        self.assertNotIn("dlgetchu", policy.sources)

    def test_tags_prefer_mgstage_over_the_dmm_dvd_page(self):
        # ABW-220 实测：mgstage 给 8 项内容标签，dmm/libredmm/r18dev 都只给
        # 「AV女優・単体作品・サンプル動画」。厂牌与日期仍以 dmm 为准。
        policy = resolve_policy(profile="censored")
        candidates = [{"source": "dmm"}, {"source": "mgstage"}, {"source": "r18dev"}]
        self.assertEqual(sort_candidates("tags", candidates, policy)[0]["source"], "mgstage")
        self.assertEqual(sort_candidates("studio", candidates, policy)[0]["source"], "dmm")
        self.assertEqual(sort_candidates("release_date", candidates, policy)[0]["source"], "dmm")

    def test_uncensored_codes_are_routed_to_sources_that_carry_them(self):
        """番号形状就能确定发行面，不必先有元数据证明。

        语料实测 8 个无码番号（carib 2、1pon 4、HEYZO 2），官方 tag 全为 0：
        它们一直按有码番号去问 mgstage/dmm，那几家根本不发行这些片，
        「问了都没有」于是被读成「上游没有」。
        """
        self.assertTrue(is_uncensored_code("040221-001"))
        self.assertTrue(is_uncensored_code("HEYZO-1380"))
        self.assertFalse(is_uncensored_code("ABW-220"))
        self.assertFalse(is_uncensored_code("259LUXU-1475"))
        policy = resolve_policy(profile="backfill")
        self.assertEqual(policy.sources_for_code("040221-001"),
                         ("caribbeancom", "tokyohot", "javbus"))
        self.assertEqual(policy.sources_for_code("HEYZO-1380"),
                         ("caribbeancom", "tokyohot", "javbus"))
        self.assertEqual(policy.sources_for_code("ABW-220"),
                         ("mgstage", "dmm", "libredmm", "aventertainment"))
        # 来源健康表要覆盖两边，所以 sources 是并集。
        self.assertEqual(set(policy.sources), {
            "caribbeancom", "tokyohot", "javbus",
            "mgstage", "dmm", "libredmm", "aventertainment"})

    def test_unrouted_profiles_keep_asking_every_source(self):
        for profile in ("baseline", "censored", "uncensored", "fc2", "official-backfill"):
            policy = resolve_policy(profile=profile)
            self.assertEqual(policy.sources_for_code("ABW-220"), policy.sources, profile)

    def test_javbus_stays_community_so_its_values_need_review(self):
        # 1Pondo 与 HEYZO 没有官方 adapter，javbus 是唯一问得到的一家；
        # 它取到的值只能进人工复核，不能走免复核写入。
        policy = resolve_policy(profile="backfill")
        self.assertFalse(policy.source("javbus").official)
        self.assertTrue(policy.source("caribbeancom").official)

    def test_publisher_outranks_the_overseas_reseller(self):
        """aventertainment 是转售商，不是发行方。

        实测 `071213-625`：它答 2017-12-28（自己的上架日），而番号本身就是
        发行日 2013-07-12，javbus 与番号一致；`092415-001` 差了 9 个月。
        标签同理——`040221-001` 它给的是英文页的改写版，caribbeancom 给的是
        发行方原页。
        """
        policy = resolve_policy(profile="censored")
        candidates = [{"source": "aventertainment"}, {"source": "caribbeancom"}]
        for field in ("tags", "release_date"):
            self.assertEqual(
                sort_candidates(field, candidates, policy)[0]["source"],
                "caribbeancom", field)


if __name__ == "__main__":
    unittest.main()
