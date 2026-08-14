import importlib.util
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "rm-ledger.py"
SPEC = importlib.util.spec_from_file_location("rm_ledger", MODULE_PATH)
rm_ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rm_ledger)


class LedgerSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "ledger.db")
        self.old_db = rm_ledger.DB
        rm_ledger.DB = self.db

    def tearDown(self):
        rm_ledger.DB = self.old_db
        self.tmp.cleanup()

    def test_fresh_schema_matches_current_web_columns(self):
        with redirect_stdout(io.StringIO()):
            rm_ledger.cmd_init()
        con = sqlite3.connect(self.db)
        columns = {row[1] for row in con.execute("PRAGMA table_info(asset)")}
        con.close()
        self.assertTrue({"studio", "feedback", "disposal", "leave_ratio", "play_seconds",
                         "feedback_at", "seek_count", "max_reached"} <= columns)

    def test_stash_import_writes_studio_without_overwriting_creator(self):
        with redirect_stdout(io.StringIO()):
            rm_ledger.cmd_init()
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT INTO asset(location,path,name,medium,creator) VALUES('local',?,?,?,?)",
            (r"R:\Media\one.mp4", "one.mp4", "video", "Channel Owner"),
        )
        con.commit()
        con.close()
        response = {"findScenes": {"scenes": [{
            "id": "42", "title": "one", "rating100": 80, "o_counter": 2, "play_count": 3,
            "files": [{"path": r"R:\Media\one.mp4", "size": 10, "duration": 30,
                       "width": 1920, "height": 1080, "video_codec": "h264",
                       "frame_rate": 30, "audio_codec": "aac"}],
            "studio": {"name": "Studio A"},
            "performers": [{"name": "Performer A"}],
            "tags": [{"name": "Tag A"}],
        }]}}
        with patch.object(rm_ledger, "gq", return_value=response):
            with redirect_stdout(io.StringIO()):
                rm_ledger.cmd_stash()
        con = sqlite3.connect(self.db)
        row = con.execute(
            "SELECT creator,studio,stash_scene_id FROM asset WHERE path=?",
            (r"R:\Media\one.mp4",),
        ).fetchone()
        tags = {x[0] for x in con.execute(
            "SELECT tag FROM asset_tag WHERE asset_id=(SELECT id FROM asset WHERE path=?)",
            (r"R:\Media\one.mp4",),
        )}
        con.close()
        self.assertEqual(row, ("Channel Owner", "Studio A", 42))
        self.assertEqual(tags, {"Tag A", "演员:Performer A"})


if __name__ == "__main__":
    unittest.main()
