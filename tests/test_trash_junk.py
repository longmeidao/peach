"""高置信广告批量入回收站的隔离回归。"""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from support.ledger import fresh_ledger

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"peach_script_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    return module


class TrashJunkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trash_junk = load_script("trash_junk")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.db_path = fresh_ledger(self.root)
        self.out = self.root / "junk.csv"
        self.backup = self.root / "ledger.backup.db"

    def add(self, asset_id, location, path, medium, size=1000, duration=None):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,size,duration) "
                "VALUES(?,?,?,?,?,?,?)",
                (asset_id, location, path, path.rsplit("\\", 1)[-1], medium,
                 size, duration),
            )
            connection.commit()
        finally:
            connection.close()

    def disposal(self, asset_id):
        connection = sqlite3.connect(self.db_path)
        try:
            return connection.execute(
                "SELECT disposal FROM asset WHERE id=?", (asset_id,)).fetchone()[0]
        finally:
            connection.close()

    def test_dry_run_lists_without_writing(self):
        self.add(1, "115", r"B:\广告\tuu26.com.mp4", "video", 10 * 1024**2, 60)

        code = self.trash_junk.main(["--db", str(self.db_path), "--out", str(self.out)])

        self.assertEqual(code, 0)
        self.assertIsNone(self.disposal(1))
        self.assertTrue(self.out.is_file())

    def test_apply_trashes_only_candidates_at_or_above_the_bar(self):
        self.add(1, "115", r"B:\广告\tuu26.com.mp4", "video", 10 * 1024**2, 60)
        self.add(2, "115", r"B:\番号\正片.mp4", "video", 400 * 1024**2, 900)

        code = self.trash_junk.main([
            "--db", str(self.db_path), "--out", str(self.out),
            "--apply", "--backup", str(self.backup),
        ])

        self.assertEqual(code, 0)
        self.assertEqual(self.disposal(1), "trash")
        self.assertIsNone(self.disposal(2))
        self.assertTrue(self.backup.is_file())

    def test_apply_without_backup_is_rejected(self):
        self.add(1, "115", r"B:\广告\tuu26.com.mp4", "video", 10 * 1024**2, 60)

        with self.assertRaises(SystemExit):
            self.trash_junk.main([
                "--db", str(self.db_path), "--out", str(self.out), "--apply",
            ])

        self.assertIsNone(self.disposal(1))


if __name__ == "__main__":
    unittest.main()
