import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.sync import (
    LedgerSync,
    Marker,
    copy_database,
    local_dirty,
    plan,
    read_marker,
    write_marker,
)


def make_db(path: Path, rows: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS note(id INTEGER PRIMARY KEY, body TEXT)")
        connection.executemany(
            "INSERT INTO note(body) VALUES(?)", [(f"row-{i}",) for i in range(rows)]
        )
        connection.commit()
    finally:
        connection.close()


def count(path: Path) -> int:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return connection.execute("SELECT count(*) FROM note").fetchone()[0]
    finally:
        connection.close()


class MarkerTests(unittest.TestCase):
    def test_marker_round_trips_and_stamps_the_real_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.db"
            make_db(db, 3)
            written = write_marker(db, Marker(4, "mac", "2026-08-20T00:00:00+00:00", 0, 0))
            self.assertEqual((written.size, written.mtime_ns), (db.stat().st_size, db.stat().st_mtime_ns))
            self.assertEqual(read_marker(db), written)

    def test_a_write_after_the_marker_counts_as_dirty(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.db"
            make_db(db, 3)
            marker = write_marker(db, Marker(1, "mac", "", 0, 0))
            self.assertFalse(local_dirty(db, marker))
            make_db(db, 1)
            self.assertTrue(local_dirty(db, marker))

    def test_a_copy_with_no_marker_is_treated_as_dirty(self):
        """没有血缘的副本必须当成「动过」，否则会被静默覆盖。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.db"
            make_db(db, 1)
            self.assertTrue(local_dirty(db, None))


class CopyTests(unittest.TestCase):
    def test_backup_api_carries_committed_wal_transactions(self):
        """直接拷 `.db` 会漏掉 `-wal` 里已提交未 checkpoint 的事务。"""
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "a.db", Path(tmp) / "b.db"
            make_db(source, 2)
            live = sqlite3.connect(source)
            try:
                live.execute("PRAGMA journal_mode=WAL")
                live.execute("INSERT INTO note(body) VALUES('in-wal')")
                live.commit()
                copy_database(source, target)
            finally:
                live.close()
            self.assertEqual(count(target), 3)

    def test_copy_overwrites_an_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "a.db", Path(tmp) / "b.db"
            make_db(source, 5)
            make_db(target, 1)
            copy_database(source, target)
            self.assertEqual(count(target), 5)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.local = self.root / "local" / "ledger.db"
        self.shared = self.root / "shared" / "ledger.db"
        self.addCleanup(self._tmp.cleanup)

    def test_same_path_disables_replication(self):
        make_db(self.local, 1)
        self.assertEqual(plan(self.local, self.local).action, "disabled")

    def test_unreachable_share_is_offline_not_an_error(self):
        """硬盘不在时本地照常读写，这是脱盘模式的账本侧。"""
        make_db(self.local, 1)
        self.assertEqual(plan(self.local, self.root / "gone" / "ledger.db").action, "offline")

    def test_missing_share_is_seeded_from_local(self):
        make_db(self.local, 1)
        self.shared.parent.mkdir(parents=True)
        self.assertEqual(plan(self.local, self.shared).action, "push")

    def test_missing_local_pulls(self):
        make_db(self.shared, 1)
        self.local.parent.mkdir(parents=True)
        self.assertEqual(plan(self.local, self.shared).action, "pull")

    def test_newer_share_pulls_when_local_is_clean(self):
        make_db(self.local, 1)
        make_db(self.shared, 2)
        write_marker(self.local, Marker(3, "mac", "", 0, 0))
        write_marker(self.shared, Marker(4, "win", "", 0, 0))
        self.assertEqual(plan(self.local, self.shared).action, "pull")

    def test_both_sides_advanced_is_a_conflict(self):
        """两边都写过就没有安全的合并规则，只能报冲突让人选。"""
        make_db(self.local, 1)
        make_db(self.shared, 2)
        write_marker(self.local, Marker(3, "mac", "", 0, 0))
        write_marker(self.shared, Marker(4, "win", "", 0, 0))
        make_db(self.local, 1)                      # 本地在标记之后又写了
        decision = plan(self.local, self.shared)
        self.assertTrue(decision.conflict)
        self.assertEqual((decision.local_generation, decision.shared_generation), (3, 4))

    def test_missing_lineage_on_either_side_is_a_conflict(self):
        make_db(self.local, 1)
        make_db(self.shared, 2)
        self.assertTrue(plan(self.local, self.shared).conflict)

    def test_local_write_since_the_last_push_is_local_ahead(self):
        make_db(self.local, 1)
        make_db(self.shared, 1)
        write_marker(self.shared, Marker(2, "mac", "", 0, 0))
        write_marker(self.local, Marker(2, "mac", "", 0, 0))
        self.assertEqual(plan(self.local, self.shared).action, "in-sync")
        make_db(self.local, 1)
        self.assertEqual(plan(self.local, self.shared).action, "local-ahead")


class LedgerSyncTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.local = self.root / "local" / "ledger.db"
        self.shared = self.root / "shared" / "ledger.db"
        self.addCleanup(self._tmp.cleanup)

    def sync(self, device="mac") -> LedgerSync:
        return LedgerSync(self.local, self.shared, device, interval=0)

    def test_first_run_seeds_the_share_and_leaves_both_in_sync(self):
        make_db(self.local, 4)
        self.shared.parent.mkdir(parents=True)
        sync = self.sync()
        self.assertEqual(sync.startup().action, "push")
        self.assertEqual(sync.status, "in-sync")
        self.assertEqual(count(self.shared), 4)
        self.assertEqual(plan(self.local, self.shared).action, "in-sync")

    def test_second_machine_pulls_what_the_first_pushed(self):
        make_db(self.local, 4)
        self.shared.parent.mkdir(parents=True)
        self.sync("mac").startup()

        other_local = self.root / "win" / "ledger.db"
        other_local.parent.mkdir(parents=True)
        other = LedgerSync(other_local, self.shared, "win", interval=0)
        self.assertEqual(other.startup().action, "pull")
        self.assertEqual(count(other_local), 4)
        self.assertEqual(plan(other_local, self.shared).action, "in-sync")

    def test_generation_advances_on_every_push(self):
        make_db(self.local, 1)
        self.shared.parent.mkdir(parents=True)
        sync = self.sync()
        sync.startup()
        first = read_marker(self.shared).generation
        make_db(self.local, 1)
        self.assertEqual(sync.push_if_needed(), "pushed")
        self.assertEqual(read_marker(self.shared).generation, first + 1)

    def test_a_push_from_the_other_machine_turns_this_one_read_only(self):
        """回写前必须重新判定，绝不能盲目覆盖别人推上去的那一代。"""
        make_db(self.local, 1)
        self.shared.parent.mkdir(parents=True)
        sync = self.sync()
        sync.startup()
        self.assertFalse(sync.read_only)

        # 另一台机器推了新的一代，同时本机也有未回写的改动
        write_marker(self.shared, Marker(99, "win", "", 0, 0))
        make_db(self.local, 1)

        self.assertEqual(sync.push_if_needed(), "conflict")
        self.assertTrue(sync.read_only)
        self.assertEqual(count(self.shared), 1)      # 共享副本没有被覆盖

    def test_offline_share_keeps_local_writes_and_pushes_on_return(self):
        make_db(self.local, 2)
        self.shared.parent.mkdir(parents=True)
        sync = self.sync()
        sync.startup()

        detached = LedgerSync(self.local, self.root / "gone" / "ledger.db", "mac", interval=0)
        make_db(self.local, 1)
        self.assertEqual(detached.push_if_needed(), "offline")
        self.assertFalse(detached.read_only)

        self.assertEqual(sync.push_if_needed(), "pushed")
        self.assertEqual(count(self.shared), 3)

    def test_manual_sync_pulls_a_newer_shared_copy(self):
        make_db(self.local, 1)
        make_db(self.shared, 2)
        write_marker(self.local, Marker(3, "mac", "", 0, 0))
        write_marker(self.shared, Marker(4, "win", "", 0, 0))
        decision = self.sync().synchronize_now()
        self.assertEqual(decision.action, "pull")
        self.assertEqual(count(self.local), 2)
        self.assertEqual(plan(self.local, self.shared).action, "in-sync")

    def test_manual_sync_pushes_local_changes(self):
        make_db(self.local, 1)
        self.shared.parent.mkdir(parents=True)
        sync = self.sync()
        sync.startup()
        make_db(self.local, 1)
        self.assertEqual(sync.synchronize_now().action, "local-ahead")
        self.assertEqual(count(self.shared), 2)

    def test_manual_sync_refuses_a_conflict(self):
        make_db(self.local, 1)
        make_db(self.shared, 2)
        write_marker(self.local, Marker(3, "mac", "", 0, 0))
        write_marker(self.shared, Marker(4, "win", "", 0, 0))
        make_db(self.local, 1)
        sync = self.sync()
        self.assertTrue(sync.synchronize_now().conflict)
        self.assertEqual(count(self.shared), 2)


if __name__ == "__main__":
    unittest.main()
