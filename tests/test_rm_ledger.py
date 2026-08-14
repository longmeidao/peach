import importlib.util
import io
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from contextlib import redirect_stdout


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ledger.py"
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
            (r"R:\media\one.mp4", "one.mp4", "video", "Channel Owner"),
        )
        con.commit()
        con.close()
        response = {"findScenes": {"scenes": [{
            "id": "42", "title": "one", "rating100": 80, "o_counter": 2, "play_count": 3,
            "files": [{"path": r"R:\media\one.mp4", "size": 10, "duration": 30,
                       "width": 1920, "height": 1080, "video_codec": "h264",
                       "frame_rate": 30, "audio_codec": "aac"}],
            "studio": {"name": "Studio A"},
            "performers": [{"name": "Performer A"}],
            "tags": [{"name": "Tag A"}],
        }]}}
        client = SimpleNamespace(graphql=lambda *_args, **_kwargs: response)
        with redirect_stdout(io.StringIO()):
            rm_ledger.cmd_stash(client)
        con = sqlite3.connect(self.db)
        row = con.execute(
            "SELECT creator,studio,stash_scene_id FROM asset WHERE path=?",
            (r"R:\media\one.mp4",),
        ).fetchone()
        tags = {x for x in con.execute(
            "SELECT tag,source FROM asset_tag WHERE asset_id=(SELECT id FROM asset WHERE path=?)",
            (r"R:\media\one.mp4",),
        )}
        binding = con.execute(
            "SELECT backend,external_id,metadata_json FROM media_binding WHERE asset_id=(SELECT id FROM asset WHERE path=?)",
            (r"R:\media\one.mp4",),
        ).fetchone()
        con.close()
        self.assertEqual(row, ("Channel Owner", "Studio A", 42))
        self.assertEqual(tags, {("Tag A", "stash:tag"),
                                ("演员:Performer A", "stash:performer")})
        self.assertEqual(binding[:2], ("stash", "42"))
        self.assertIn('"transport": "stash-graphql"', binding[2])


if __name__ == "__main__":
    unittest.main()
