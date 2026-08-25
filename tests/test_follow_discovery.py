"""从裸 id 或名字反查来源。全部注入 transport，测试不联网。"""
import json
import tempfile
import time
import unittest
from pathlib import Path

from peach.follow import FollowSourceError
from peach.follow_discovery import (
    CREATOR_INDEX_TTL_SECONDS, CreatorIndex, discover, search_variants,
)
from peach.follow_secrets import CredentialError
from peach.http import HttpResponse


CREATORS = json.dumps([
    {"id": "30917150", "name": "LazyProcrastinator", "service": "fanbox"},
    {"id": "109730638", "name": "EcchiWaffle", "service": "patreon"},
    {"id": "25775753", "name": "LazyMazer", "service": "patreon"},
]).encode()

F95_HIT = json.dumps({"status": "ok", "msg": {"data": [
    {"thread_id": 50685, "title": "Lazy Procrastinator Collection",
     "version": "2026-06-28"}]}}).encode()
F95_MISS = json.dumps({"status": "ok", "msg": {"data": []}}).encode()


def _router(routes, calls=None):
    """按 URL 片段派发的假 transport。没有匹配就回 404。"""
    def call(request, timeout, max_bytes):
        if calls is not None:
            calls.append(request.url)
        for fragment, response in routes.items():
            if fragment in request.url:
                return response
        return HttpResponse(404, {}, b"not found")
    return call


class _DiscoveryCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.secrets = self.root / "secrets"
        self.state = self.root / "state"

    def _discover(self, term, routes, providers=None, calls=None):
        return discover(term, secrets_root=self.secrets, state_root=self.state,
                        transport=_router(routes, calls), providers=providers)


class SearchVariantTests(unittest.TestCase):
    def test_camel_case_is_split_because_full_text_search_matches_words(self):
        # f95 搜 `lazyprocrastinator` 搜不到，搜 `lazy procrastinator` 能。
        self.assertEqual(search_variants("LazyProcrastinator"),
                         ("LazyProcrastinator", "Lazy Procrastinator"))

    def test_an_all_lowercase_run_has_no_reliable_split(self):
        # 全小写连写没有切分信号，就只用原词，不去猜词典。
        self.assertEqual(search_variants("lazyprocrastinator"), ("lazyprocrastinator",))

    def test_a_spaced_term_is_left_alone(self):
        self.assertEqual(search_variants("Lazy Procrastinator"), ("Lazy Procrastinator",))


class CreatorIndexTests(_DiscoveryCase):
    def _index(self, calls=None):
        return CreatorIndex(self.state, transport=_router(
            {"/api/v1/creators": HttpResponse(200, {}, CREATORS)}, calls))

    def test_the_index_is_downloaded_once_and_then_cached(self):
        calls = []
        index = self._index(calls)
        self.assertEqual(len(index.load("kemono")), 3)
        self.assertEqual(len(index.load("kemono")), 3)
        self.assertEqual(len(calls), 1, "第二次不该再下载")

    def test_a_stale_cache_is_refreshed(self):
        calls = []
        index = self._index(calls)
        index.load("kemono")
        # `now` 是墙钟时间，不是相对量：要比文件 mtime 晚过一个 TTL 才算过期。
        index.load("kemono", now=time.time() + CREATOR_INDEX_TTL_SECONDS * 2)
        self.assertEqual(len(calls), 2)

    def test_a_broken_payload_is_an_error_not_an_empty_index(self):
        index = CreatorIndex(self.state, transport=_router(
            {"/api/v1/creators": HttpResponse(200, {}, b'{"nope": 1}')}))
        with self.assertRaises(FollowSourceError):
            index.load("kemono")


class DiscoverTests(_DiscoveryCase):
    ROUTES = {
        "/api/v1/creators": HttpResponse(200, {}, CREATORS),
        "rule34video.com/models/lazyprocrastinator/": HttpResponse(200, {}, b"<html/>"),
        "cat=animations": HttpResponse(200, {}, F95_HIT),
        "latest_data.php": HttpResponse(200, {}, F95_MISS),
    }

    def test_a_name_is_found_across_every_source_that_has_it(self):
        found = self._discover("LazyProcrastinator", self.ROUTES,
                               providers=("kemono", "rule34video", "f95zone"))
        by_provider = {c.provider: c for c in found.candidates}
        self.assertEqual(by_provider["kemono"].ref, "fanbox/30917150")
        self.assertEqual(by_provider["rule34video"].ref, "lazyprocrastinator")
        self.assertEqual(by_provider["f95zone"].ref, "50685")

    def test_every_candidate_says_why_it_matched(self):
        found = self._discover("LazyProcrastinator", self.ROUTES,
                               providers=("kemono", "rule34video", "f95zone"))
        self.assertTrue(all(c.evidence for c in found.candidates))
        kemono = next(c for c in found.candidates if c.provider == "kemono")
        self.assertEqual(kemono.evidence, "创作者名精确匹配")

    def test_a_numeric_term_matches_the_site_id_and_skips_name_only_sources(self):
        calls = []
        found = self._discover("30917150", self.ROUTES, calls=calls)
        self.assertEqual([c.ref for c in found.candidates if c.provider == "kemono"],
                         ["fanbox/30917150"])
        # 纯数字不去 rule34video / rule34.xxx 碰运气——那两个都是按名字/标签查的。
        self.assertFalse(any("/models/" in url for url in calls))

    def test_a_numeric_term_probes_the_thread_id(self):
        routes = {**self.ROUTES, "f95zone.to/threads/50685/": HttpResponse(200, {}, b"<html/>")}
        found = self._discover("50685", routes, providers=("f95zone",))
        self.assertEqual([c.ref for c in found.candidates], ["50685"])
        self.assertEqual(found.candidates[0].evidence, "线程存在")

    def test_a_missing_thread_yields_nothing_rather_than_a_guessed_link(self):
        found = self._discover("99999999", self.ROUTES, providers=("f95zone",))
        self.assertEqual(found.candidates, ())

    def test_a_partial_name_match_is_reported_as_partial(self):
        found = self._discover("Lazy", self.ROUTES, providers=("kemono",))
        evidence = {c.label: c.evidence for c in found.candidates}
        self.assertIn("LazyProcrastinator · fanbox", evidence)
        self.assertEqual(evidence["LazyProcrastinator · fanbox"], "创作者名包含该词")

    def test_one_source_failing_does_not_lose_the_others(self):
        routes = {**self.ROUTES}
        del routes["/api/v1/creators"]
        found = self._discover("LazyProcrastinator", routes,
                               providers=("kemono", "rule34video"))
        self.assertEqual([c.provider for c in found.candidates], ["rule34video"])
        self.assertIn("kemono", found.failures)

    def test_missing_rule34xxx_credentials_are_reported_not_raised(self):
        found = self._discover("LazyProcrastinator", self.ROUTES,
                               providers=("rule34xxx",))
        self.assertEqual(found.candidates, ())
        self.assertIn("api_key", found.failures["rule34xxx"])

    def test_junk_terms_are_refused_before_any_request(self):
        calls = []
        for term in ("", "   ", "../etc", "a" * 200, "<script>", "a?b", "a&b"):
            with self.assertRaises(FollowSourceError):
                self._discover(term, self.ROUTES, calls=calls)
        self.assertEqual(calls, [])

    def test_japanese_and_chinese_creator_names_are_accepted(self):
        # kemono 上大量创作者是日文或中文名，ASCII 白名单会把他们整批挡在门外。
        creators = json.dumps([
            {"id": "1", "name": "うるしばら", "service": "fanbox"},
            {"id": "2", "name": "冰鲜鱼子酱二代目", "service": "fanbox"},
        ]).encode()
        routes = {"/api/v1/creators": HttpResponse(200, {}, creators)}
        for term, expected in (("うるしばら", "1"), ("冰鲜鱼子酱二代目", "2")):
            found = self._discover(term, routes, providers=("kemono",))
            self.assertEqual([c.ref for c in found.candidates], [f"fanbox/{expected}"], term)

    def test_results_are_capped_per_source(self):
        many = json.dumps([{"id": str(i), "name": f"Lazy{i}", "service": "fanbox"}
                           for i in range(50)]).encode()
        found = self._discover("Lazy", {"/api/v1/creators": HttpResponse(200, {}, many)},
                               providers=("kemono",))
        self.assertEqual(len(found.candidates), 8)


if __name__ == "__main__":
    unittest.main()
