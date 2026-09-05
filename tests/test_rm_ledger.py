import importlib.util
import io
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch


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
        tables = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_schema WHERE type='table'"
        )}
        con.close()
        self.assertTrue({"studio", "feedback", "disposal", "leave_ratio", "play_seconds",
                         "feedback_at", "seek_count", "max_reached"} <= columns)
        self.assertTrue({"entity", "entity_alias", "entity_external_ref", "asset_entity"} <= tables)

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
            "studio": {"id": "7", "name": "Studio A"},
            "performers": [{"id": "8", "name": "Performer A"}],
            "tags": [{"id": "9", "name": "Tag A"}],
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
        entities = set(con.execute(
            "SELECT kind,canonical_name FROM entity ORDER BY kind,canonical_name"
        ))
        external_refs = set(con.execute(
            "SELECT e.kind,r.external_id FROM entity_external_ref r "
            "JOIN entity e ON e.id=r.entity_id"
        ))
        relations = set(con.execute(
            "SELECT e.kind,ae.role,ae.source FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id"
        ))
        con.close()
        self.assertEqual(row, ("Channel Owner", "Studio A", 42))
        self.assertEqual(tags, {("Tag A", "stash:tag"),
                                ("演员:Performer A", "stash:performer")})
        self.assertEqual(binding[:2], ("stash", "42"))
        self.assertIn('"transport": "stash-graphql"', binding[2])
        self.assertEqual(entities, {("studio", "Studio A"), ("tag", "Tag A"),
                                    ("performer", "Performer A")})
        self.assertEqual(external_refs, {("studio", "7"), ("performer", "8"),
                                         ("tag", "9")})
        self.assertEqual(relations, {("studio", "studio", "stash:studio"),
                                     ("performer", "performer", "stash:performer"),
                                     ("tag", "tag", "stash:tag")})


class ScanTargetTests(unittest.TestCase):
    """写入侧门槛：`scan <location> <root>` 的两个参数必须对得上（ADR-0023 第 2 阶段）。

    location 是挂载点 ID，`[media.locations]` 给出它的账本口径根。对不上时写进去的行
    既翻译不出本机路径、也通不过授权根，而且要等到有人点开那个资产才会发现。
    """

    def setUp(self):
        from peach import settings_file

        config = settings_file.load_config(environ={}, strict=False)
        fixed = replace(config, locations={"local": (r"R:\media",), "115": ("B:/",)})
        patcher = patch.object(settings_file, "active", lambda: fixed)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_declared_root_and_its_subdirectories_are_accepted(self):
        self.assertIsNone(rm_ledger.check_scan_target("local", r"R:\media"))
        self.assertIsNone(rm_ledger.check_scan_target("local", r"R:\media\创作者"))
        self.assertIsNone(rm_ledger.check_scan_target("115", "B:/x"))

    def test_a_root_belonging_to_another_source_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            rm_ledger.check_scan_target("115", r"R:\media\创作者")
        self.assertIn("115", str(caught.exception))
        self.assertIn("local", str(caught.exception))

    def test_a_root_outside_every_declared_root_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            rm_ledger.check_scan_target("local", r"R:\Resources\Intake")
        self.assertIn(r"R:\media", str(caught.exception))

    def test_an_undeclared_source_is_refused_and_lists_the_known_ones(self):
        with self.assertRaises(SystemExit) as caught:
            rm_ledger.check_scan_target("nas", "N:/")
        self.assertIn("nas", str(caught.exception))
        self.assertIn("local", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
