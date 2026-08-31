import unittest

from peach.related import rank_related


class RelatedRankerTests(unittest.TestCase):
    def test_rare_shared_tag_beats_common_shared_tag(self):
        source = {"id": 1, "entities": {"tag": {10, 20}}}
        common = {"id": 2, "entities": {"tag": {10}}}
        rare = {"id": 3, "entities": {"tag": {20}}}
        background = [
            {"id": asset_id, "entities": {"tag": {10}}}
            for asset_id in range(4, 14)
        ]
        ranked = rank_related(source, [common, rare, *background], 2, seed="fixed")
        self.assertEqual(ranked[0]["id"], 3)
        self.assertEqual(ranked[0]["why"], "标签接近")

    def test_result_is_stable_and_mmr_adds_variety(self):
        source = {"id": 1, "entities": {"creator": {7}, "tag": {10, 11}}}
        candidates = [
            {"id": 2, "entities": {"creator": {7}, "tag": {10, 11}}},
            {"id": 3, "entities": {"creator": {7}, "tag": {10, 11}}},
            {"id": 4, "entities": {"creator": {7}, "tag": {10}}},
        ]
        first = rank_related(source, candidates, 3, seed="fixed", diversity=0.4)
        second = rank_related(source, candidates, 3, seed="fixed", diversity=0.4)
        self.assertEqual([row["id"] for row in first], [row["id"] for row in second])
        self.assertEqual(first[0]["why"], "同创作者 · 标签接近")

    def test_unrelated_items_are_excluded(self):
        source = {"id": 1, "entities": {"tag": {10}}}
        ranked = rank_related(source, [{"id": 2, "entities": {"tag": {99}}}], 10)
        self.assertEqual(ranked, [])


if __name__ == "__main__":
    unittest.main()
