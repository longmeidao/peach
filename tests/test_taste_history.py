import csv
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from peach.taste_history import HistorySource, analyze_history, discover_history_sources, refresh_history


class TasteHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _firefox_db(self, path: Path) -> None:
        path.parent.mkdir(parents=True)
        with closing(sqlite3.connect(path)) as db:
            db.executescript(
                "CREATE TABLE moz_places(id INTEGER PRIMARY KEY, url TEXT, title TEXT);"
                "CREATE TABLE moz_historyvisits(id INTEGER PRIMARY KEY, place_id INTEGER, visit_date INTEGER);"
            )
            db.execute("INSERT INTO moz_places VALUES (1, ?, ?)", ("https://rule34.xxx/search?tags=feet+cosplay", "secret"))
            db.execute("INSERT INTO moz_historyvisits VALUES (1, 1, 1700000000000000)")
            db.commit()

    def _chrome_db(self, path: Path) -> None:
        path.parent.mkdir(parents=True)
        with closing(sqlite3.connect(path)) as db:
            db.executescript(
                "CREATE TABLE urls(id INTEGER PRIMARY KEY, url TEXT, title TEXT);"
                "CREATE TABLE visits(id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER);"
            )
            db.execute("INSERT INTO urls VALUES (1, ?, ?)", ("https://onlyfans.com/creator_name", "private title"))
            db.execute("INSERT INTO visits VALUES (2, 1, 13344473600000000)")
            db.commit()

    def _safari_db(self, path: Path) -> None:
        path.parent.mkdir(parents=True)
        with closing(sqlite3.connect(path)) as db:
            db.executescript(
                "CREATE TABLE history_items(id INTEGER PRIMARY KEY, url TEXT);"
                "CREATE TABLE history_visits(id INTEGER PRIMARY KEY, history_item INTEGER, visit_time REAL, title TEXT);"
            )
            db.execute("INSERT INTO history_items VALUES (1, ?)", ("https://rule34video.com/models/alice/",))
            db.execute("INSERT INTO history_visits VALUES (3, 1, 700000000, 'hidden')")
            db.commit()

    def test_discovers_windows_firefox_and_chrome_profiles(self):
        roaming = self.root / "Roaming"
        local = self.root / "Local"
        self._firefox_db(roaming / "Mozilla" / "Firefox" / "Profiles" / "default" / "places.sqlite")
        self._chrome_db(local / "Google" / "Chrome" / "User Data" / "Default" / "History")
        sources = discover_history_sources(
            home=self.root, appdata=roaming, localappdata=local, platform_name="windows"
        )
        self.assertEqual([source.browser for source in sources], ["chrome", "firefox"])

    def test_refresh_is_incremental_and_report_omits_urls_and_titles(self):
        firefox = self.root / "firefox" / "places.sqlite"
        chrome = self.root / "chrome" / "History"
        safari = self.root / "Safari" / "History.db"
        self._firefox_db(firefox)
        self._chrome_db(chrome)
        self._safari_db(safari)
        sources = [
            HistorySource("firefox", "default", firefox),
            HistorySource("chrome", "Default", chrome),
            HistorySource("safari", "iCloud", safari),
        ]
        store = self.root / "sources" / "history.sqlite"
        first = refresh_history(sources, store, host="test-host")
        second = refresh_history(sources, store, host="test-host")
        self.assertEqual(sum(item["added"] for item in first), 3)
        self.assertEqual(sum(item["added"] for item in second), 0)

        output = self.root / "review"
        result = analyze_history(store, output)
        report = Path(result["report"]).read_text(encoding="utf-8")
        self.assertIn("足系", report)
        self.assertIn("cosplay", report)
        self.assertIn("alice", report)
        self.assertNotIn("https://", report)
        self.assertNotIn("secret", report)
        self.assertNotIn("private title", report)
        with Path(result["creators"]).open(encoding="utf-8-sig", newline="") as handle:
            creators = {row["candidate"] for row in csv.DictReader(handle)}
        self.assertEqual(creators, {"alice", "creator_name"})


if __name__ == "__main__":
    unittest.main()
