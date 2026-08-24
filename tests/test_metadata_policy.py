import unittest

from peach.metadata_policy import (
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


if __name__ == "__main__":
    unittest.main()
