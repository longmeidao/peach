"""从裸 id 或名字反查来源。全部注入 transport，测试不联网。"""
import json
import tempfile
import time
import unittest
from pathlib import Path

from peach.follow import FollowSourceError
from peach.follow_discovery import (
    CREATOR_INDEX_TTL_SECONDS, CreatorIndex, discover, identity_key,
    search_variants, spelling_variants,
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
F95_SEARCH_FORM = b"""<html><body><input type="hidden" name="_xfToken" value="1,a" /></body></html>"""
F95_SEARCH_RESULTS = b"""<html><body><h3 class="contentRow-title">
<a href="/threads/ria-collection-2026-08-03-ria_neearts.146348/"><span class="label">Collection</span>Ria Collection [2026-08-03] [<em class="textHighlight">Ria_neearts</em>]</a>
</h3></body></html>"""
# 2026-09-01 实测：站上的写法是 `ria-neearts`，补全按字面前缀匹配，所以
# `Ria_neearts` 查出来是空的，`Ria-neearts` 才命中。
R34_AUTOCOMPLETE_HIT = json.dumps(
    [{"label": "ria-neearts (248)", "value": "ria-neearts"},
     {"label": "riahri (156)", "value": "riahri"}]).encode()
FANBOX_PROFILE = ("<html><meta name='metadata' content='"
                  + json.dumps({"urlContext": {"host": {"creatorId": "lazyprocrast"}}})
                    .replace("'", "&#39;")
                  + "'></html>").encode()
FANBOX_CREATOR = json.dumps({"body": {"user": {
    "userId": "30917150", "name": "LazyProcrastinator",
    "iconUrl": "https://pixiv.pximg.net/icon.jpeg",
}}}).encode()


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

    def _write_credential(self, provider, values):
        path = self.secrets / "follow" / f"{provider}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(values), encoding="utf-8")

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

    def test_an_underscored_name_is_also_tried_as_words(self):
        self.assertEqual(search_variants("initial_a"), ("initial_a", "initial a"))

    def test_a_handle_is_also_tried_with_the_other_separators(self):
        # 手柄写作 `Ria_neearts`，rule34.xxx 上的标签是 `ria-neearts`。
        self.assertEqual(spelling_variants("Ria_neearts"),
                         ("Ria_neearts", "Ria-neearts", "Rianeearts", "Ria neearts"))

    def test_a_handle_without_separators_has_only_itself(self):
        self.assertEqual(spelling_variants("lazyprocrastinator"), ("lazyprocrastinator",))

    def test_the_identity_key_ignores_separators_and_case(self):
        self.assertEqual(identity_key("Ria_neearts"), identity_key("ria-neearts"))
        self.assertNotEqual(identity_key("Ria_neearts"), identity_key("riahri"))

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
        "/fanbox/creator/30917150": HttpResponse(200, {}, FANBOX_PROFILE),
        "creator.get?creatorId=lazyprocrast": HttpResponse(200, {}, FANBOX_CREATOR),
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

    def test_archive_identity_resolves_to_the_official_fanbox_page(self):
        found = self._discover("LazyProcrastinator", self.ROUTES,
                               providers=("kemono", "fanbox"))
        official = next(c for c in found.candidates if c.provider == "fanbox")
        self.assertEqual(official.ref, "lazyprocrast")
        self.assertEqual(official.url, "https://lazyprocrast.fanbox.cc/")
        self.assertEqual(official.label, "LazyProcrastinator")
        self.assertIn("官方资料", official.evidence)

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

    def test_an_f95_miss_offers_google_without_guessing_a_thread(self):
        found = self._discover(
            "initial_a", {"latest_data.php": HttpResponse(200, {}, F95_MISS)},
            providers=("f95zone",))
        self.assertEqual(found.candidates, ())
        self.assertEqual(len(found.external_searches), 1)
        search = found.external_searches[0]
        self.assertEqual(search.provider, "f95zone")
        self.assertEqual(search.query, "initial_a f95zone")
        self.assertEqual(search.url,
                         "https://www.google.com/search?q=initial_a+f95zone")
        self.assertIn("真实线程链接", search.evidence)

    def test_an_f95_hit_does_not_add_a_redundant_google_link(self):
        found = self._discover("LazyProcrastinator", self.ROUTES,
                               providers=("f95zone",))
        self.assertTrue(found.candidates)
        self.assertEqual(found.external_searches, ())

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

    def test_a_handle_finds_the_tag_spelled_differently_on_the_site(self):
        # 站上是 `ria-neearts`，手边的手柄是 `Ria_neearts`。按手柄逐字查是零命中，
        # 补全把两种写法对上，登记的是站上的那个写法。
        routes = {"autocomplete.php?q=Ria_neearts": HttpResponse(200, {}, b"[]"),
                  "autocomplete.php?q=Ria-neearts": HttpResponse(200, {}, R34_AUTOCOMPLETE_HIT)}
        found = self._discover("Ria_neearts", routes, providers=("rule34xxx",))
        self.assertEqual([c.ref for c in found.candidates], ["ria-neearts"])
        self.assertIn("248", found.candidates[0].evidence)
        self.assertIn("tags=ria-neearts", found.candidates[0].url)

    def test_the_tag_search_needs_no_credentials_of_its_own(self):
        routes = {"autocomplete.php": HttpResponse(200, {}, R34_AUTOCOMPLETE_HIT)}
        found = self._discover("ria-neearts", routes, providers=("rule34xxx",))
        self.assertEqual([c.ref for c in found.candidates], ["ria-neearts"])
        self.assertEqual(found.failures, {})

    def test_a_tag_that_merely_starts_with_the_term_is_not_a_hit(self):
        # 补全按前缀返回，`riahri` 也在结果里。名字不同就不是这个人，不能拿来登记。
        routes = {"autocomplete.php": HttpResponse(200, {}, R34_AUTOCOMPLETE_HIT)}
        found = self._discover("ria", routes, providers=("rule34xxx",))
        self.assertEqual(found.candidates, ())

    def test_an_f95_collection_thread_is_found_by_the_forum_search(self):
        # `latest_data.php` 只索引 Latest Updates，艺术家的 Collection 帖不在里面。
        self._write_credential("f95zone", {"cookie": "xf_user=1"})
        routes = {"latest_data.php": HttpResponse(200, {}, F95_MISS),
                  "/search/search": HttpResponse(200, {}, F95_SEARCH_RESULTS),
                  "f95zone.to/search/": HttpResponse(200, {}, F95_SEARCH_FORM)}
        found = self._discover("Ria_neearts", routes, providers=("f95zone",))
        self.assertEqual([c.ref for c in found.candidates], ["146348"])
        self.assertEqual(found.candidates[0].label,
                         "Ria Collection [2026-08-03] [Ria_neearts]")
        self.assertEqual(found.external_searches, ())

    def test_without_a_cookie_the_forum_search_is_skipped_not_guessed(self):
        calls = []
        found = self._discover("Ria_neearts", {"latest_data.php": HttpResponse(200, {}, F95_MISS)},
                               providers=("f95zone",), calls=calls)
        self.assertEqual(found.candidates, ())
        self.assertEqual(found.failures, {})
        self.assertEqual([search.provider for search in found.external_searches], ["f95zone"])
        self.assertFalse([url for url in calls if "/search/" in url])

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
