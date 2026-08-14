import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.jobs import (
    DiskSpaceDenied,
    JobAlreadyRunning,
    MeteredSourceDenied,
    PidFileLock,
    SourceAccessPolicy,
    require_free_space,
)


class JobPolicyTests(unittest.TestCase):
    def test_metered_source_requires_explicit_authorization(self):
        policy = SourceAccessPolicy()
        with self.assertRaises(MeteredSourceDenied):
            policy.sql_filter("pikpak", allow_metered=False)

    def test_unmetered_query_uses_parameters_and_excludes_metered_sources(self):
        sql, parameters = SourceAccessPolicy().sql_filter("115", allow_metered=False)
        self.assertEqual(sql, " AND location=? AND location NOT IN (?,?)")
        self.assertEqual(parameters, ("115", "online", "pikpak"))

    def test_authorized_metered_query_is_scoped_to_requested_source(self):
        sql, parameters = SourceAccessPolicy().sql_filter("pikpak", allow_metered=True)
        self.assertEqual(sql, " AND location=?")
        self.assertEqual(parameters, ("pikpak",))

    def test_disk_guard_fails_closed_when_usage_is_unavailable(self):
        with patch("peach.jobs.shutil.disk_usage", side_effect=OSError("offline")):
            with self.assertRaises(DiskSpaceDenied):
                require_free_space(Path("C:/"), 40)

    def test_disk_guard_accepts_real_temporary_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertGreaterEqual(require_free_space(tmp, 0), 0)

    def test_pid_lock_rejects_live_owner_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.lock"
            with PidFileLock(path):
                self.assertTrue(path.is_file())
                with self.assertRaises(JobAlreadyRunning):
                    PidFileLock(path).acquire()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
