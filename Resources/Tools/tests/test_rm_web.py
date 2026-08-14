import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "rm-web.py"
SPEC = importlib.util.spec_from_file_location("rm_web", MODULE_PATH)
rm_web = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rm_web)


BASE_SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY,
  location TEXT NOT NULL,
  path TEXT NOT NULL,
  name TEXT,
  medium TEXT,
  size INTEGER,
  creator TEXT,
  studio TEXT,
  series TEXT,
  code TEXT,
  duration REAL,
  width INTEGER,
  height INTEGER,
  ctx_length TEXT,
  ctx_orient TEXT,
  ctx_quality TEXT,
  play_count INTEGER DEFAULT 0,
  last_played TEXT,
  rating INTEGER,
  o_count INTEGER,
  snapshot_path TEXT,
  first_seen TEXT,
  UNIQUE(location, path)
);
CREATE TABLE asset_tag(
  asset_id INTEGER,
  tag TEXT,
  confidence REAL DEFAULT 1.0,
  source TEXT,
  UNIQUE(asset_id, tag)
);
"""


class WebDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
        con = sqlite3.connect(self.db_path)
        con.executescript(BASE_SCHEMA)
        con.executemany(
            """INSERT INTO asset(
                 id,location,path,name,medium,size,creator,studio,code,duration,
                 width,height,ctx_length,ctx_orient,ctx_quality,first_seen)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                (1, "local", r"R:\\Media\\one.mp4", "one.mp4", "video", 100,
                 "Alice", "Studio A", "ABC-001", 100, 1920, 1080, "速食", "横屏", "2K", "2026-08-14"),
                (2, "115", r"B:\\two.mp4", "two.mp4", "video", 200,
                 "Bob", None, None, 200, 1080, 1920, "速食", "竖屏", "1080P", "2026-08-13"),
                (3, "local", r"R:\\Media\\cover.jpg", "cover.jpg", "image", 10,
                 "Alice", None, None, None, None, None, None, None, None, "2026-08-12"),
            ],
        )
        con.executemany(
            "INSERT INTO asset_tag(asset_id,tag,source) VALUES(?,?,?)",
            [(1, "足交", "name"), (1, "演员:Alice", "performer"), (2, "竖屏", "probe")],
        )
        con.commit()
        con.close()
        self.old_db = rm_web.DB
        rm_web.DB = self.db_path
        rm_web.ensure_columns()

    def tearDown(self):
        rm_web.DB = self.old_db
        self.tmp.cleanup()

    def row(self, aid=1):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM asset WHERE id=?", (aid,)).fetchone()
        con.close()
        return row

    def test_ensure_columns_is_idempotent(self):
        rm_web.ensure_columns()
        con = sqlite3.connect(self.db_path)
        columns = {row[1] for row in con.execute("PRAGMA table_info(asset)")}
        con.close()
        self.assertTrue({"feedback", "disposal", "leave_ratio", "play_seconds",
                         "feedback_at", "seek_count", "max_reached"} <= columns)

    def test_items_are_filtered_and_do_not_expose_paths(self):
        result = rm_web.q_items({"loc": "local", "sort": "new", "limit": "10"})
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], 1)
        self.assertEqual(result["items"][0]["performers"], ["Alice"])
        self.assertNotIn("path", result["items"][0])
        self.assertNotIn("snapshot_path", result["items"][0])

    def test_activity_accumulates_real_play_time_and_max_position(self):
        first = rm_web.w_activity({"id": 1, "position": 50, "duration": 100,
                                   "delta": 12, "seeks": 2})
        second = rm_web.w_activity({"id": 1, "position": 20, "duration": 100,
                                    "delta": 3, "seeks": 1})
        self.assertEqual(first["max_reached"], 0.5)
        self.assertEqual(second["play_seconds"], 15)
        self.assertEqual(second["max_reached"], 0.5)
        self.assertEqual(second["seek_count"], 3)

    def test_feedback_and_disposal_toggle_independently(self):
        self.assertEqual(rm_web.w_feedback({"id": 1, "kind": "dislike"})["feedback"], "dislike")
        self.assertEqual(rm_web.w_feedback({"id": 1, "kind": "dispose"})["disposal"], "pending")
        self.assertEqual(self.row()["feedback"], "dislike")
        self.assertIsNone(rm_web.w_feedback({"id": 1, "kind": "dislike"})["feedback"])
        self.assertEqual(self.row()["disposal"], "pending")


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.old_token = rm_web.TOKEN
        rm_web.TOKEN = "secret"
        self.handler = rm_web.H.__new__(rm_web.H)

    def tearDown(self):
        rm_web.TOKEN = self.old_token

    def check(self, cookie="", header=None, query=None):
        self.handler.headers = {"Cookie": cookie}
        if header is not None:
            self.handler.headers["X-Token"] = header
        return self.handler._auth(query or {})

    def test_cookie_name_and_value_must_match_exactly(self):
        self.assertTrue(self.check(cookie="tok=secret"))
        self.assertFalse(self.check(cookie="notok=secret"))
        self.assertFalse(self.check(cookie="tok=secretextra"))

    def test_query_and_header_tokens(self):
        self.assertTrue(self.check(query={"t": ["secret"]}))
        self.assertTrue(self.check(header="secret"))
        self.assertFalse(self.check(header="wrong"))


if __name__ == "__main__":
    unittest.main()
