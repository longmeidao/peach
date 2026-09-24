"""补女优别名后继：两站证据确定的艺名直接登记，不确定的不写，写下的能整批撤回（ADR-0055）。

全程临时账本；两站的取页层是真的（缓存、冷却、撞墙判定都走一遍），只把最底下的传输换成
按地址回页面的替身，不联网。页面是 minnano-av 699633 与 av_neme「雲母そら」「有本紗世」的
真实页面裁剪而成，只留解析会读到的那几块：夹具内联在这里而不是另开目录，新目录映射不到
任何测试域，会让每次改动都跑全量。
"""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.parse import quote

from peach import minnano_av
from peach import performer_alias_followup as alias
from peach.entities import normalize_entity_name
from peach.followups import Attempts, attempts_root
from peach.http import HttpResponse
from peach.repository import LedgerDatabase
from peach.review_csv import read_rows
from peach.scraping_access import paused_until
from peach.sources.base import Page
from peach.sources.seesaa import person_profile, search_results, split_names
from support.ledger import fresh_ledger

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-09-24T00:00:00.000Z"
PROFILE_URL = f"{minnano_av.SITE}actress699633.html"

MINNANO_PROFILE = """<!doctype html><html lang="ja"><head>
<link rel="canonical" href="https://www.minnano-av.com/actress699633.html">
</head><body>
<h1>雲母そら<span>きららそら / Kirara Sora</span></h1>
<div class="act-profile">
<table width="100%" cellspacing="0" cellpadding="0" border="0">
<tr><td><h2>雲母そら （きららそら / Kirara Sora）</h2></td></tr>
<tr><td><span>別名</span><p>未来ちゃん(FC2) （みらいちゃん / ）</p></td></tr>
<tr><td><span>別名</span><p>いちかちゃん(FC2) （いちかちゃん / ）</p></td></tr>
<tr><td><span>別名</span><p>雫つむぎ(FC2) （しずくつむぎ / SizukuTsumugi）</p></td></tr>
<tr><td><span>別名</span><p>神山ももか （かみやまももか / KamiyamaMomoka）</p></td></tr>
<tr><td><span>別名</span><p>朝霧いのり(着エロ) （あさぎりいのり / Asagiri Inori）</p></td></tr>
<tr><td><span>別名</span><p>神山ももか(天然むすめ) （かみやまももか / Kamiyama Momoka）</p></td></tr>
<tr><td><span>別名</span><p>雲母そら （きららそら / Kirara Sora）</p></td></tr>
<tr><td><span>別名</span><p>美雲そら【旧名】 （みくもそら / Mikumo Sora）</p></td></tr>
<tr><td><span>所属事務所</span><p><a href="actress_list.php?production=282">Bambi Promotion</a></p></td></tr>
</table></div>
<div class="comment"><table><tr><td><span>別名</span><p>コメント欄の誰か</p></td></tr></table></div>
</body></html>"""

MINNANO_SEARCH = """<!doctype html><html lang="ja"><body>
<table width="100%" cellspacing="0" cellpadding="0" border="0" class="tbllist actress">
<tr><th class="t9"></th><th class="t9" align="left">名前</th></tr>
<tr><td><a href="actress699633.html"><img alt="神山ももか"></a></td>
<td class="details"><h2 class="ttl"><a href="actress699633.html">神山ももか</a></h2>
<p class="furi">（雲母そら）</p></td></tr>
<tr><td><a href="actress699633.html"><img alt="神山ももか(天然むすめ)"></a></td>
<td class="details"><h2 class="ttl"><a href="actress699633.html">神山ももか(天然むすめ)</a></h2>
<p class="furi">（雲母そら）</p></td></tr>
</table>
<div class="recommend"><a href="actress111111.html">おすすめの誰か</a></div>
</body></html>"""

MINNANO_EMPTY = """<!doctype html><html lang="ja"><body>
<table class="tbllist actress"><tr><th>名前</th></tr></table></body></html>"""


def wiki_url(title: str) -> str:
    return alias.AV_NEME_ROOT + "d/" + quote(title.encode("euc_jp"))


def wiki_search_url(key: str) -> str:
    return alias.AV_NEME_ROOT + "search?keywords=" + quote(key.encode("euc_jp"))


def wiki_page(section: str, rest: str = "") -> str:
    return ('<html><body><div id="page-body"><div class="user-area">'
            f'{section}{rest}</div></div></body></html>')


def wiki_section(title: str, body: str, level: int = 1) -> str:
    return (f'<div class="wiki-section-{level}"><div class="title-{level}"><h3>{title}</h3></div>'
            f'<div class="wiki-section-body-{level}">{body}</div></div>')


AV_NEME_KIRARA = wiki_page(
    wiki_section("プロフィール", """<pre class="BOX">
名前(女優名)：雲母そら（きららそら）
旧名義&amp;別名：美雲そら（みくもそら）・朝霧いのり（あさぎりいのり）・雫つむぎ・神山ももか
生年月日：
</pre>"""),
    # 作品小节里的名义是那一部片给她起的，不是她的艺名，不读。
    wiki_section("smuc170| 素人ムクムク-夢中-",
                 "別名：みく 18歳 本屋の店員<br />仮名：そらちゃん<br />", level=3))

AV_NEME_MOVED = wiki_page(wiki_section(
    "女優名(名前)変更", "女優名が【神山ももか】から【美雲そら】へ変更になりました。"))

AV_NEME_ARIMOTO = wiki_page(wiki_section("プロフィール", (
    "<table><tbody><tr><th><b><div>ナンバー</div></b></th><td>347</td></tr>"
    "<tr><th><b><div>名前(別名)</div></b></th>"
    "<td>有本紗世（ありもとさよ）／有本沙耶／有本紗也／元木小夜（もときさよ）</td></tr>"
    "</tbody></table>")))


def wiki_search(*titles: str) -> str:
    hits = "".join(f'<div class="body"><h3 class="keyword"><a href="{wiki_url(title)}">{title}'
                   '</a></h3><p class="text">…</p></div>' for title in titles)
    return f'<html><body><div class="result-box">{hits}</div></body></html>'


class Transport:
    """按地址回页面的传输替身；没登记的检索回一张空结果页，其余回 404。"""

    def __init__(self, pages: dict, empty_search: bytes):
        self.pages, self.empty_search, self.calls = pages, empty_search, []

    def __call__(self, request, _timeout, _limit):
        self.calls.append(request.url)
        if request.url in self.pages:
            status, body = self.pages[request.url]
        elif "search" in request.url:
            status, body = 200, self.empty_search
        else:
            status, body = 404, b""
        return HttpResponse(status, {}, body, request.url)

    def close(self):
        pass


class NoWait:
    def wait(self, _url):
        pass


class Case(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.db = fresh_ledger(self.root)
        self.database = LedgerDatabase(self.db)
        self.generated = self.root / "generated"
        self.cooldown = self.root / "secrets"
        self.busted = []
        self.contract = SimpleNamespace(
            database=self.database, candidate_root=self.generated,
            follow_secrets_root=self.cooldown, cache_bust=lambda: self.busted.append(1))
        self.minnano = Transport({
            minnano_av.search_url("神山ももか"): (200, MINNANO_SEARCH.encode("utf-8")),
            PROFILE_URL: (200, MINNANO_PROFILE.encode("utf-8")),
        }, MINNANO_EMPTY.encode("utf-8"))
        self.av_neme = Transport({
            wiki_search_url("神山ももか"): (200, wiki_search("雲母そら", "神山ももか").encode("euc_jp")),
            wiki_url("雲母そら"): (200, AV_NEME_KIRARA.encode("euc_jp")),
            wiki_url("神山ももか"): (200, AV_NEME_MOVED.encode("euc_jp")),
        }, wiki_search().encode("euc_jp"))

    def entity(self, name: str, *aliases: str, kind: str = "performer") -> int:
        with self.database.write_transaction(notify=False) as connection:
            cursor = connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES(?,?,?,?,?)", (kind, name, normalize_entity_name(name), STAMP, STAMP))
            entity_id = int(cursor.lastrowid)
            for written in aliases:
                connection.execute(
                    "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source)"
                    " VALUES(?,?,?,'manual')", (entity_id, written, normalize_entity_name(written)))
        return entity_id

    def work(self, asset_id: int, *performers: int) -> None:
        with self.database.write_transaction(notify=False) as connection:
            connection.execute("INSERT INTO asset(id,location,path,name,medium)"
                               " VALUES(?,'local',?,?,'video')",
                               (asset_id, f"R:\\media\\{asset_id}.mp4", f"{asset_id}.mp4"))
            for entity_id in performers:
                connection.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source)"
                                   " VALUES(?,?,'performer','test')", (asset_id, entity_id))

    def aliases(self, entity_id: int) -> dict[str, str]:
        with self.database.read_connection() as connection:
            return {str(row[0]): str(row[1]) for row in connection.execute(
                "SELECT alias,source FROM entity_alias WHERE entity_id=?", (entity_id,))}

    def sites(self) -> dict:
        cache = self.generated / "provider-cache"
        return {alias.MINNANO: alias.MinnanoPages(cache / "minnano", self.cooldown, self.minnano,
                                                  limiter=NoWait()),
                alias.AV_NEME: alias.AvNemePages(cache / "seesaa", self.cooldown, self.av_neme)}

    def run_followup(self, entity_id: int, run_id: int = 7) -> dict:
        handle = SimpleNamespace(run_id=run_id, progress=lambda **_kwargs: None)
        with mock.patch.object(alias, "open_sites", side_effect=lambda _contract: self.sites()), \
                mock.patch.object(alias, "_LIMITER", NoWait()):
            return alias.run(self.contract, alias.followup_key(entity_id), handle)

    def review(self) -> list[dict]:
        return read_rows(self.generated / alias.REVIEW_FILE)


class ParsingTests(unittest.TestCase):
    def test_minnano_profile_reads_only_the_alias_rows_of_her_own_table(self):
        main, names = minnano_av.profile_names(MINNANO_PROFILE)
        self.assertEqual(main, "雲母そら")
        self.assertEqual(len(names), 8)
        self.assertNotIn("コメント欄の誰か", names)
        self.assertEqual(minnano_av.profile_names(MINNANO_SEARCH), ("", []))

    def test_minnano_search_counts_people_not_rows(self):
        hits = minnano_av.search_hits(MINNANO_SEARCH)
        self.assertEqual({found for found, _shown in hits}, {"699633"})
        self.assertEqual(len(hits), 2)

    def test_av_neme_reads_the_name_fields_in_both_layouts(self):
        self.assertEqual(person_profile(Page(wiki_url("雲母そら"), AV_NEME_KIRARA.encode("euc_jp"))),
                         ("雲母そら", ["雲母そら", "美雲そら", "朝霧いのり", "雫つむぎ", "神山ももか"]))
        self.assertEqual(person_profile(Page(wiki_url("有本紗世"), AV_NEME_ARIMOTO.encode("euc_jp"))),
                         ("有本紗世", ["有本紗世", "有本沙耶", "有本紗也", "元木小夜"]))

    def test_av_neme_a_page_not_named_after_her_is_not_her_page(self):
        body = AV_NEME_KIRARA.encode("euc_jp")
        self.assertEqual(person_profile(Page(wiki_url("2023年03月"), body)), ("", []))
        self.assertEqual(person_profile(Page(wiki_url("神山ももか"),
                                             AV_NEME_MOVED.encode("euc_jp"))), ("", []))

    def test_av_neme_search_lists_hits_in_order(self):
        body = wiki_search("雲母そら", "神山ももか").encode("euc_jp")
        self.assertEqual([title for _url, title in search_results(body)], ["雲母そら", "神山ももか"])

    def test_a_middle_dot_between_katakana_stays_inside_one_name(self):
        self.assertEqual(split_names("キラ・クィーン・美雲そら"), ["キラ・クィーン", "美雲そら"])

    def test_names_that_would_hit_someone_else_are_rejected(self):
        for name in ("そら", "みく", "Kirara Sora", "いちかちゃん", "未来ちゃん", "名前不明", "145cm色白お嬢様"):
            self.assertTrue(alias.rejection(alias.clean(name)), name)
        for name in ("雫つむぎ(FC2)", "美雲そら【旧名】", "有本紗世（ありもとさよ）", "キラ・クィーン"):
            self.assertEqual(alias.rejection(alias.clean(name)), "", name)


class LandingTests(Case):
    def test_her_other_stage_names_are_registered_from_both_sites(self):
        momoka = self.entity("神山ももか")
        summary = self.run_followup(momoka)
        self.assertEqual(summary["outcome"], "登记 4 个别名")
        batch = f"{alias.SOURCE}@7"
        self.assertEqual(self.aliases(momoka), {
            "雲母そら": batch, "雫つむぎ": batch, "朝霧いのり": batch, "美雲そら": batch})
        self.assertTrue(summary["sites"][alias.MINNANO].startswith("命中 " + PROFILE_URL))
        self.assertTrue(summary["sites"][alias.AV_NEME].startswith("命中 " + wiki_url("雲母そら")))
        self.assertEqual(self.busted, [1])
        actions = {(row["site"], row["alias"]): row["action"] for row in self.review()}
        self.assertEqual(actions[(alias.MINNANO, "神山ももか")], alias.HAVE)
        self.assertEqual(actions[(alias.AV_NEME, "雲母そら")], alias.HAVE)

    def test_amateur_labels_and_one_off_names_are_not_registered(self):
        momoka = self.entity("神山ももか")
        self.run_followup(momoka)
        names = self.aliases(momoka)
        for name in ("未来ちゃん", "いちかちゃん", "みく", "そらちゃん"):
            self.assertNotIn(name, names)
        skipped = {row["alias"]: row["detail"] for row in self.review()
                   if row["action"] == alias.SKIP}
        self.assertEqual(skipped, {"未来ちゃん": "一次性称呼", "いちかちゃん": "一次性称呼"})

    def test_a_name_another_entity_already_uses_is_left_for_review(self):
        momoka = self.entity("神山ももか")
        other = self.entity("雫つむぎ")
        summary = self.run_followup(momoka)
        self.assertNotIn("雫つむぎ", self.aliases(momoka))
        self.assertEqual(summary["taken"], 2)
        taken = [row for row in self.review() if row["action"] == alias.TAKEN]
        self.assertEqual({row["alias"] for row in taken}, {"雫つむぎ"})
        self.assertIn(f"实体 {other}", taken[0]["detail"])
        self.assertEqual(self.aliases(other), {})

    def test_a_short_single_name_is_neither_searched_nor_registered(self):
        sora = self.entity("そら")
        with self.database.read_connection() as connection:
            self.assertFalse(alias.has_entry(connection, sora))
            self.assertEqual(alias.plan(connection, since_entity_id=0), [])
        momoka = self.entity("神山ももか")
        with self.database.write_transaction(notify=False) as connection:
            rows = alias.land(connection, momoka, "神山ももか", alias.AV_NEME, "page",
                              ["そら", "Kirara Sora", "美雲そら"], "batch@1")
        self.assertEqual([row["action"] for row in rows], [alias.SKIP, alias.SKIP, alias.WRITE])
        self.assertEqual(self.aliases(momoka), {"美雲そら": "batch@1"})

    def test_a_page_that_does_not_list_her_is_not_used(self):
        stranger = self.entity("佐々木ゆうか")
        self.minnano.pages[minnano_av.search_url("佐々木ゆうか")] = (
            200, MINNANO_PROFILE.encode("utf-8"))
        summary = self.run_followup(stranger)
        self.assertEqual(summary["outcome"], "两站都没对上她")
        self.assertEqual(self.aliases(stranger), {})

    def test_a_known_minnano_id_is_read_without_searching(self):
        momoka = self.entity("神山ももか")
        with self.database.write_transaction(notify=False) as connection:
            connection.execute(
                "INSERT INTO entity_external_ref(entity_id,provider,external_kind,external_id)"
                " VALUES(?,?,'performer','699633')", (momoka, alias.MINNANO))
        self.run_followup(momoka)
        self.assertNotIn(minnano_av.search_url("神山ももか"), self.minnano.calls)
        self.assertIn("雲母そら", self.aliases(momoka))

    def test_a_renamed_or_missing_entity_is_not_written(self):
        momoka = self.entity("神山ももか")
        with self.database.write_transaction(notify=False) as connection:
            stale = alias.land(connection, momoka, "別人", alias.MINNANO, "page", ["雲母そら"], "b")
            gone = alias.land(connection, 999, "神山ももか", alias.MINNANO, "page", ["雲母そら"], "b")
        self.assertEqual([row["action"] for row in stale + gone], [alias.STALE, alias.GONE])
        self.assertEqual(self.aliases(momoka), {})


class RepeatTests(Case):
    def test_a_second_run_writes_nothing_and_asks_nobody(self):
        momoka = self.entity("神山ももか")
        self.run_followup(momoka, run_id=7)
        first = dict(self.aliases(momoka))
        requests = len(self.minnano.calls) + len(self.av_neme.calls)
        summary = self.run_followup(momoka, run_id=8)
        self.assertEqual(summary["outcome"], "没有新写法")
        self.assertEqual(self.aliases(momoka), first)
        self.assertEqual(len(self.minnano.calls) + len(self.av_neme.calls), requests)

    def test_stock_does_not_dispatch_her_again_until_her_names_change(self):
        momoka = self.entity("神山ももか")
        self.work(1, momoka)
        attempts = Attempts(attempts_root(self.generated))

        def planned():
            with self.database.read_connection() as connection:
                return [item.key for item in alias.stock(connection, attempts, limit=5)]

        self.assertEqual(planned(), [alias.followup_key(momoka)])
        self.run_followup(momoka)
        self.assertEqual(planned(), [])
        with self.database.write_transaction(notify=False) as connection:
            connection.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source)"
                               " VALUES(?,'新しい名前','新しい名前','manual')", (momoka,))
        self.assertEqual(planned(), [alias.followup_key(momoka)])

    def test_a_rate_limited_site_is_paused_and_not_asked_again(self):
        momoka = self.entity("神山ももか")
        self.minnano.pages[minnano_av.search_url("神山ももか")] = (429, b"")
        self.av_neme.pages[wiki_search_url("神山ももか")] = (429, b"")
        summary = self.run_followup(momoka)
        self.assertEqual(summary["outcome"], "未取得")
        self.assertIn("429", summary["sites"][alias.MINNANO])
        self.assertIn("429", summary["sites"][alias.AV_NEME])
        self.assertTrue(paused_until(self.cooldown, alias.MINNANO))
        self.assertTrue(paused_until(self.cooldown, alias.AV_NEME))
        requests = len(self.minnano.calls) + len(self.av_neme.calls)
        self.assertEqual(self.run_followup(momoka, run_id=8)["outcome"], "未取得")
        self.assertEqual(len(self.minnano.calls) + len(self.av_neme.calls), requests)
        self.assertEqual(self.aliases(momoka), {})

    def test_a_challenge_page_is_not_cached_as_her_profile(self):
        momoka = self.entity("神山ももか")
        self.minnano.pages[minnano_av.search_url("神山ももか")] = (
            200, b"<title>Just a moment...</title>")
        summary = self.run_followup(momoka)
        self.assertIn("未取得", summary["sites"][alias.MINNANO])
        self.assertFalse(list((self.generated / "provider-cache" / "minnano").glob("*.json")))


def load_revert():
    spec = importlib.util.spec_from_file_location(
        "revert_auto_landing_under_test", ROOT / "scripts" / "revert_auto_landing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevertTests(Case):
    def test_a_batch_is_reverted_and_not_landed_again(self):
        momoka = self.entity("神山ももか", "かみやまももか本人")
        self.work(1, momoka)
        self.run_followup(momoka, run_id=7)
        self.assertEqual(len(self.aliases(momoka)), 5)
        revert = load_revert()
        base = ["--db", str(self.db), "--logo-root", str(self.root / "logos"),
                "--source", alias.SOURCE]
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(revert.main([*base, "--batch", f"{alias.SOURCE}@8"]), 0)
        self.assertIn("'别名': 0", printed.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(revert.main(base), 0)
        self.assertIn("'别名': 4", printed.getvalue())
        self.assertEqual(len(self.aliases(momoka)), 5)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(revert.main(
                [*base, "--apply", "--backup", str(self.root / "backup.db")]), 0)
        self.assertEqual(self.aliases(momoka), {"かみやまももか本人": "manual"})
        # 撤回之后她的名字链与撤回前、这一批写入前一样，存量补派不会原样再落一遍。
        with self.database.read_connection() as connection:
            self.assertEqual(alias.stock(connection, Attempts(attempts_root(self.generated)),
                                         limit=5), [])


class AllocationTests(Case):
    def test_stock_aliases_get_their_share_of_the_round(self):
        from peach import library_processing, task_runs

        people = [self.entity(f"白石まり{index:02d}") for index in range(10)]
        for index, entity_id in enumerate(people, start=1):
            self.work(index, entity_id)
        config = SimpleNamespace(directory=lambda _name: self.generated)
        with mock.patch.object(task_runs, "MAX_FOLLOWUPS", 8), \
                mock.patch.object(alias, "STOCK_SHARE", 3):
            found = library_processing._entity_followups(self.database, config, max(people))
        kinds = [item["task_key"] for item in found]
        self.assertEqual(len(kinds), 8)
        self.assertEqual(kinds.count(alias.TASK_KEY), 3)

    def test_new_performers_get_an_alias_followup_ahead_of_stock(self):
        from peach import library_processing

        old = self.entity("古川ゆうな")
        self.work(1, old)
        new = self.entity("新田あおい")
        config = SimpleNamespace(directory=lambda _name: self.generated)
        found = library_processing._entity_followups(self.database, config, old)
        keys = [item["key"] for item in found if item["task_key"] == alias.TASK_KEY]
        self.assertEqual(keys, [alias.followup_key(new), alias.followup_key(old)])


if __name__ == "__main__":
    unittest.main()
