from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "job_status.py"
SPEC = importlib.util.spec_from_file_location("peach_job_status", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class JobStatusTests(unittest.TestCase):
    def test_hook_event_is_sanitized_and_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            state = Path(root) / "state" / "handoff.json"
            MODULE.record_hook_event(state, {
                "hook_event_name": "StopFailure",
                "transcript_path": "secret transcript",
                "access_token": "never persist me",
            })
            saved = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(saved["agent"], "claude")
            self.assertEqual(saved["event"], "StopFailure")
            self.assertEqual(saved["outcome"], "failed")
            self.assertNotIn("access_token", saved)
            self.assertNotIn("transcript_path", saved)
            self.assertFalse(list(state.parent.glob("*.tmp")))

    def test_write_back_replaces_only_managed_block(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            tmp_path = Path(root)
            doc = tmp_path / "STATUS.md"
            doc.write_text("before\n\n<!-- job-status:start -->\nold\n<!-- job-status:end -->\n\nafter\n", encoding="utf-8")
            block = [MODULE.START, "fresh", MODULE.END]
            self.assertEqual(MODULE.write_back(doc, block), "替换了已有区块")
            self.assertEqual(doc.read_text(encoding="utf-8"), "before\n\n<!-- job-status:start -->\nfresh\n<!-- job-status:end -->\n\nafter\n")
            self.assertFalse(list(tmp_path.glob("*.tmp")))
