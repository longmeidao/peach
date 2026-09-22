"""番号发现源：解析、两层去重、已读与忽略、空壳与真实资产的边界（ADR-0042）。"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import feeds  # noqa: E402
from peach.migrations import upgrade  # noqa: E402
from peach.repository import LedgerDatabase  # noqa: E402

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Sukebei - Home - Torrent File RSS</title>
  <item>
    <title>HMN-071 \xe6\x96\xb0\xe4\xba\xba \xe6\x88\xb6\xe5\xb7\x9d\xe6\xad\xa5[\xe6\x9c\x89\xe7\xa2\xbc]</title>
    <link>https://sukebei.nyaa.si/download/4719097.torrent</link>
    <guid>https://sukebei.nyaa.si/view/4719097</guid>
    <pubDate>Tue, 22 Sep 2026 10:36:13 -0000</pubDate>
  </item>
  <item>
    <title>[H265 1080p] DSOD-114 \xe8\x8a\xb1\xe5\xae\xae\xe4\xba\xac\xe5\xad\x90</title>
    <link>https://sukebei.nyaa.si/download/4719080.torrent</link>
    <guid>https://sukebei.nyaa.si/view/4719080</guid>
    <pubDate>Tue, 22 Sep 2026 09:12:00 -0000</pubDate>
  </item>
  <item>
    <title>\xe5\x90\x88\xe9\x9b\x86 30 \xe9\x83\xa8\xe6\x89\x93\xe5\x8c\x85</title>
    <link>https://sukebei.nyaa.si/download/4719001.torrent</link>
    <guid>https://sukebei.nyaa.si/view/4719001</guid>
    <pubDate>Tue, 22 Sep 2026 08:00:00 -0000</pubDate>
  </item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>example</title>
  <entry>
    <id>tag:example,2026:1</id>
    <title>SSIS-950 sample</title>
    <link href="https://example.test/a"/>
    <published>2026-09-20T03:00:00Z</published>
  </entry>
</feed>"""

JAVDB_ACTOR = """
<div class="movie-list h cols-4 vcols-8">
  <div class="item">
    <a href="/v/5nr8mp" class="box" title="ignored">
      <div class="cover"><img src="x.jpg" /></div>
      <div class="video-title"><strong>PBD-528</strong> 気高きお姉さん達</div>
      <div class="score"><span class="value">4.0分</span></div>
      <div class="meta">
        2026-10-20
      </div>
    </a>
  </div>
  <div class="item">
    <a href="/v/RkPb5z" class="box" title="ignored">
      <div class="cover"><img src="y.jpg" /></div>
      <div class="video-title"><strong>BBSS-106</strong> 別の作品</div>
      <div class="meta">
        2026-10-13
      </div>
    </a>
  </div>
</div>
"""


def _database(root: Path) -> LedgerDatabase:
    path = root / "ledger.db"
    upgrade(path, MIGRATIONS)
    return LedgerDatabase(path)


class FeedParsingTest(unittest.TestCase):
    def test_rss_entries_take_guid_as_item_key(self):
        parsed = feeds.parse_feed(RSS)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.title, "Sukebei - Home - Torrent File RSS")
        self.assertEqual([entry.item_key for entry in parsed.entries],
                         ["https://sukebei.nyaa.si/view/4719097",
                          "https://sukebei.nyaa.si/view/4719080",
                          "https://sukebei.nyaa.si/view/4719001"])
        self.assertEqual(parsed.entries[0].published_at, "2026-09-22T10:36:13.000Z")

    def test_atom_entries_take_id_and_link(self):
        parsed = feeds.parse_feed(ATOM)
        self.assertEqual(len(parsed.entries), 1)
        self.assertEqual(parsed.entries[0].item_key, "tag:example,2026:1")
        self.assertEqual(parsed.entries[0].link, "https://example.test/a")
        self.assertEqual(parsed.entries[0].code, "SSIS-950")

    def test_not_a_feed_is_none(self):
        self.assertIsNone(feeds.parse_feed(b"<html><body>hi</body></html>"))
        self.assertIsNone(feeds.parse_feed(b""))

    def test_code_is_found_inside_a_title_full_of_prose(self):
        # 整段丢给 `release_code_from_text` 认不出来，词元扫描才认得出。
        title = "HMN-071 新人 帶來超稀有妹子 戶川步[有碼高清中文字幕]"
        self.assertEqual(feeds.scan_code(title), "HMN-071")
        self.assertEqual(feeds.scan_code("[H265 1080p] DSOD-114 花宮京子"), "DSOD-114")
        self.assertIsNone(feeds.scan_code("合集 30 部打包"))

    def test_javdb_actor_page_reads_code_and_release_date(self):
        parsed = feeds.parse_javdb_actor(JAVDB_ACTOR, "https://javdb.com/actors/pRMq")
        self.assertEqual([entry.item_key for entry in parsed.entries],
                         ["/v/5nr8mp", "/v/RkPb5z"])
        self.assertEqual(parsed.entries[0].code, "PBD-528")
        self.assertEqual(parsed.entries[0].link, "https://javdb.com/v/5nr8mp")
        self.assertEqual(parsed.entries[0].published_at, "2026-10-20T00:00:00.000Z")

    def test_a_page_without_any_work_is_a_failure_not_an_empty_poll(self):
        # 带查询串的演员页会回一份不含作品的页面。当成「这次没有新作」会让一个坏掉的
        # 订阅永远不报错。
        self.assertIsNone(feeds.parse_javdb_actor("<html>nothing</html>",
                                                  "https://javdb.com/actors/pRMq"))


class FeedStoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.database = _database(self.root)
        self.addCleanup(self._tmp.cleanup)

    def _source(self, **kwargs) -> int:
        with self.database.write_transaction() as connection:
            return feeds.add_source(connection, kind=feeds.KIND_RSS,
                                    url=kwargs.pop("url", "https://example.test/rss"),
                                    **kwargs)

    def _poll(self, source_id: int, body: bytes = RSS) -> dict:
        parsed = feeds.parse_feed(body)
        with self.database.write_transaction() as connection:
            source = connection.execute("SELECT * FROM feed_source WHERE id=?",
                                        (source_id,)).fetchone()
            return feeds.poll(connection, source, parsed)

    def test_https_only(self):
        with self.assertRaises(ValueError):
            feeds.normalize_url("http://example.test/rss")

    def test_same_url_twice_is_refused(self):
        self._source()
        with self.assertRaises(ValueError):
            self._source()

    def test_first_poll_records_every_entry_and_shells_the_coded_ones(self):
        source_id = self._source()
        outcome = self._poll(source_id)
        self.assertEqual(outcome["seen"], 3)
        self.assertEqual(outcome["fresh"], 3)
        # 解不出番号的条目照样记一行，只是不建壳。
        self.assertEqual(outcome["without_code"], 1)
        self.assertEqual(sorted(code for _id, code in outcome["created"]),
                         ["DSOD-114", "HMN-071"])
        with self.database.read_connection() as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM feed_item").fetchone()[0], 3)

    def test_second_poll_of_the_same_document_creates_nothing(self):
        source_id = self._source()
        self._poll(source_id)
        outcome = self._poll(source_id)
        self.assertEqual(outcome["fresh"], 0)
        self.assertEqual(outcome["created"], [])

    def test_two_sources_reporting_one_code_share_a_single_shell(self):
        first = self._source(url="https://example.test/a.xml")
        second = self._source(url="https://example.test/b.xml")
        self._poll(first)
        outcome = self._poll(second)
        # 源内那一层是各自的，所以第二个源仍然把三条都记成新条目……
        self.assertEqual(outcome["fresh"], 3)
        # ……但全局那一层只认番号，壳一个都不再建。
        self.assertEqual(outcome["created"], [])
        with self.database.read_connection() as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM feed_discovery").fetchone()[0], 2)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM feed_item").fetchone()[0], 6)

    def test_a_code_already_in_the_library_gets_no_shell(self):
        with self.database.write_transaction() as connection:
            connection.execute(
                "INSERT INTO asset(location,path,name,medium,code) "
                "VALUES('R','R:\\\\media\\\\hmn071.mp4','hmn071.mp4','video','hmn00071')")
        source_id = self._source()
        outcome = self._poll(source_id)
        # 归一化之后 `hmn00071` 与 `HMN-071` 是同一部片。
        self.assertEqual([code for _id, code in outcome["created"]], ["DSOD-114"])

    def test_read_and_ignore_are_independent_and_do_not_touch_dedupe(self):
        source_id = self._source()
        created = self._poll(source_id)["created"]
        discovery_id = created[0][0]
        with self.database.write_transaction() as connection:
            connection.execute("UPDATE feed_discovery SET read_at=? WHERE id=?",
                               (feeds.stamp(), discovery_id))
            connection.execute("UPDATE feed_discovery SET ignored_at=? WHERE id=?",
                               (feeds.stamp(), discovery_id))
            row = connection.execute(
                "SELECT read_at,ignored_at FROM feed_discovery WHERE id=?",
                (discovery_id,)).fetchone()
        self.assertIsNotNone(row["read_at"])
        self.assertIsNotNone(row["ignored_at"])
        # 忽略之后再拉一轮，这条既不重建也不变回未忽略。
        outcome = self._poll(source_id)
        self.assertEqual(outcome["created"], [])
        with self.database.read_connection() as connection:
            row = connection.execute(
                "SELECT ignored_at FROM feed_discovery WHERE id=?",
                (discovery_id,)).fetchone()
        self.assertIsNotNone(row["ignored_at"])

    def test_settle_writes_the_next_time_on_every_path(self):
        source_id = self._source(interval_minutes=60)
        with self.database.write_transaction() as connection:
            feeds.settle(connection, source_id, error="来源回了 HTTP 503",
                         interval_minutes=60)
        with self.database.read_connection() as connection:
            row = connection.execute("SELECT * FROM feed_source WHERE id=?",
                                     (source_id,)).fetchone()
        self.assertEqual(row["last_error"], "来源回了 HTTP 503")
        self.assertIsNotNone(row["next_fetch_at"])
        self.assertGreater(row["next_fetch_at"], row["last_fetched_at"])

    def test_disabled_sources_are_never_due(self):
        source_id = self._source()
        with self.database.write_transaction() as connection:
            feeds.set_enabled(connection, source_id, False)
        with self.database.read_connection() as connection:
            self.assertEqual(feeds.due_sources(connection), [])

    def test_performer_names_match_existing_entities_only(self):
        with self.database.write_transaction() as connection:
            connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES('performer','深田えいみ',peach_normalize('深田えいみ'),?,?)",
                (feeds.stamp(), feeds.stamp()))
        with self.database.read_connection() as connection:
            found = feeds.match_performers(connection, ["深田えいみ", "查无此人"])
        self.assertEqual(len(found), 1)


class ShellBoundaryTest(unittest.TestCase):
    """壳不进 asset，所以整理、抽帧与馆藏统计看不到它（ADR-0042 第二条）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.database = _database(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def test_a_shell_adds_no_asset_row(self):
        with self.database.write_transaction() as connection:
            source_id = feeds.add_source(connection, kind=feeds.KIND_RSS,
                                         url="https://example.test/rss")
            feeds.poll(connection, connection.execute(
                "SELECT * FROM feed_source WHERE id=?", (source_id,)).fetchone(),
                feeds.parse_feed(RSS))
        with self.database.read_connection() as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM asset").fetchone()[0], 0)
            self.assertGreater(connection.execute(
                "SELECT count(*) FROM feed_discovery").fetchone()[0], 0)

    def test_the_shell_table_is_not_an_asset_reference(self):
        # 物理删除资产时要清的引用名单里没有它：壳不引用 asset，两者只按番号对上。
        from peach.web_batch import ASSET_REFERENCE_TABLES
        self.assertNotIn("feed_discovery", ASSET_REFERENCE_TABLES)
        self.assertNotIn("feed_item", ASSET_REFERENCE_TABLES)

    def test_deleting_a_source_takes_its_items_but_leaves_the_shell(self):
        # 壳是「这个番号还没入库」，它不该随着某个订阅被删而消失。
        with self.database.write_transaction() as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            source_id = feeds.add_source(connection, kind=feeds.KIND_RSS,
                                         url="https://example.test/rss")
            feeds.poll(connection, connection.execute(
                "SELECT * FROM feed_source WHERE id=?", (source_id,)).fetchone(),
                feeds.parse_feed(RSS))
            feeds.remove_source(connection, source_id)
        with self.database.read_connection() as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM feed_item").fetchone()[0], 0)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM feed_discovery").fetchone()[0], 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
