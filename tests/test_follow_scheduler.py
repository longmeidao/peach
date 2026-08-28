import tempfile
import unittest
from pathlib import Path

from peach.follow_scheduler import (
    FollowScheduleConfig,
    FollowScheduleStore,
    FollowUpdateScheduler,
)


class FollowScheduleStoreTests(unittest.TestCase):
    def test_defaults_are_enabled_hourly_and_updates_are_atomic(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = FollowScheduleStore(Path(temporary))
            self.assertEqual(store.load(), FollowScheduleConfig(True, 60))
            store.save(FollowScheduleConfig(False, 180))
            self.assertEqual(store.load(), FollowScheduleConfig(False, 180))

    def test_unbounded_intervals_are_rejected(self):
        with self.assertRaises(ValueError):
            FollowScheduleStore.validate(True, 14)
        with self.assertRaises(ValueError):
            FollowScheduleStore.validate(True, 10081)
        with self.assertRaises(ValueError):
            FollowScheduleStore.validate("false", 60)


class FollowUpdateSchedulerTests(unittest.TestCase):
    def test_interval_job_waits_one_interval_and_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            scheduler = FollowUpdateScheduler(Path(temporary), lambda: {"ok": True}, available=True)
            self.addCleanup(scheduler.stop)
            scheduler.start()
            status = scheduler.status()
            self.assertTrue(status["enabled"])
            self.assertIsNotNone(status["next_run_at"])
            status = scheduler.update(enabled=False, interval_minutes=60)
            self.assertFalse(status["enabled"])
            self.assertIsNone(status["next_run_at"])

    def test_run_status_reports_checked_sources_and_additions(self):
        result = {"ok": True, "checked": 2, "results": [
            {"ok": True, "added": 3}, {"ok": False, "added": 0},
        ]}
        with tempfile.TemporaryDirectory() as temporary:
            scheduler = FollowUpdateScheduler(Path(temporary), lambda: result, available=True)
            scheduler._run()
            status = scheduler.status()
            self.assertEqual(status["last_checked"], 2)
            self.assertEqual(status["last_added"], 3)
            self.assertEqual(status["last_error"], "1 个来源检查失败")
            self.assertIsNotNone(status["last_finished_at"])

    def test_reader_never_starts_or_accepts_schedule_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            scheduler = FollowUpdateScheduler(Path(temporary), lambda: {}, available=False)
            scheduler.start()
            self.assertFalse(scheduler.status()["available"])
            with self.assertRaises(ValueError):
                scheduler.update(enabled=True, interval_minutes=60)
