"""批量修 MP4 头这一轮任务。

判定和修复都用替身：这里要验的是选谁、按什么顺序、哪些不必再问一遍，
真正重建头的算术在 `test_mp4repair` 里。
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock

from peach import web_contract as rm_web
from peach import web_media_repair as rm_repair

from support.ledger import fresh_ledger


class _Store:
    """`HeaderRepairStore` 的替身：记下被要求修的是谁。"""

    def __init__(self, existing=(), failing=()):
        self.existing = set(existing)
        self.failing = set(failing)
        self.repaired: list[int] = []

    def lookup(self, asset_id, source):
        return "头" if asset_id in self.existing else None

    def repair_now(self, asset_id, source):
        self.repaired.append(asset_id)
        if asset_id in self.failing:
            return False
        self.existing.add(asset_id)
        return True


class _Transcodes:
    """`TranscodeService` 的替身：只回答「是不是缺 ctts 的那一类」。"""

    def __init__(self, affected=()):
        self.affected = set(affected)
        self.asked: list[str] = []

    def decode_order_timestamps(self, source):
        self.asked.append(Path(source).name)
        return Path(source).name in self.affected


class MediaRepairRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.media = self.root / "media"
        self.media.mkdir()
        self.db_path = str(fresh_ledger(self.root))
        sep = chr(92)
        rows = [
            (1, "115", "B:" + sep + "seldom.mp4", "seldom.mp4", 0),
            (2, "115", "B:" + sep + "favourite.mp4", "favourite.mp4", 9),
            (3, "115", "B:" + sep + "fine.mp4", "fine.mp4", 1),
            (4, "pikpak", "A:" + sep + "metered.mp4", "metered.mp4", 5),
            (5, "115", "B:" + sep + "photo.jpg", "photo.jpg", 3),
        ]
        connection = sqlite3.connect(self.db_path)
        connection.executemany(
            "INSERT INTO asset(id,location,path,name,medium,size,play_count) "
            "VALUES(?,?,?,?,'video',10,?)", rows)
        connection.commit()
        connection.close()
        for _, _, _, name, _ in rows:
            (self.media / name).write_bytes(b"x" * 16)
        self.contract = rm_web.WebContract(Path(self.db_path), transcode_root=self.root / "cache")
        self.store = _Store()
        self.transcodes = _Transcodes({"favourite.mp4", "seldom.mp4"})
        self.contract.header_repairs = self.store
        self.contract.transcode_service = self.transcodes
        patch = mock.patch.object(
            rm_repair, "translate_ledger_path",
            lambda raw: self.media / PureWindowsPath(str(raw)).name)
        patch.start()
        self.addCleanup(patch.stop)

    def run_once(self, **body) -> dict:
        """跑完一轮再返回状态：后台任务在测试里没有别的事要抢。"""
        started = rm_repair.w_media_repair(self.contract, {"restart": True, **body})
        thread = self.contract.media_repair_job.thread
        if thread is not None:
            thread.join(timeout=30)
        return rm_repair.q_media_repair(self.contract) or started

    def test_only_the_files_that_are_actually_broken_get_repaired(self):
        state = self.run_once()

        self.assertEqual(self.store.repaired, [2, 1])
        self.assertEqual(state["status"], "complete")
        self.assertEqual((state["found"], state["repaired"], state["failed"]), (2, 2, 0))

    def test_the_most_played_ones_are_repaired_first(self):
        """一轮要跑几个钟头，中途停下也该已经换来体感：常看的先修好。"""
        self.run_once()

        self.assertEqual(self.store.repaired[0], 2, "放得最多的那部没排在最前面")

    def test_a_metered_source_is_left_alone_unless_it_is_asked_for(self):
        """PikPak 上一部片要整个拉下来才修得了，不能顺手就动。"""
        self.run_once()

        self.assertNotIn("metered.mp4", self.transcodes.asked)

    def test_asking_for_the_metered_source_reaches_it(self):
        self.transcodes.affected.add("metered.mp4")
        self.run_once(allow_metered=True)

        self.assertIn("metered.mp4", self.transcodes.asked)

    def test_a_file_that_already_has_a_header_is_not_probed_again(self):
        self.store.existing.add(2)
        self.run_once()

        self.assertNotIn("favourite.mp4", self.transcodes.asked)
        self.assertEqual(self.store.repaired, [1])

    def test_a_clean_verdict_is_remembered_for_the_next_run(self):
        """判一遍要把整个库的头读一遍，115 上那是几千次网络往返，不能每轮重来。"""
        self.run_once()
        self.transcodes.asked.clear()
        self.run_once()

        self.assertNotIn("fine.mp4", self.transcodes.asked)
        self.assertTrue((self.root / "cache" / rm_repair.SCAN_CACHE_NAME).exists())

    def test_a_file_that_cannot_be_repaired_is_not_tried_again(self):
        self.store.failing.add(2)
        first = self.run_once()
        self.run_once()

        self.assertEqual((first["repaired"], first["failed"]), (1, 1))
        self.assertEqual(self.store.repaired.count(2), 1)

    def test_a_changed_file_is_judged_again(self):
        """结论跟着文件的大小和改动时间走：换了内容，上一轮的结论就不作数。"""
        self.run_once()
        (self.media / "fine.mp4").write_bytes(b"y" * 32)
        self.transcodes.asked.clear()
        self.run_once()

        self.assertIn("fine.mp4", self.transcodes.asked)

    def test_images_are_never_in_the_list(self):
        self.run_once()

        self.assertNotIn("photo.jpg", self.transcodes.asked)

    def test_an_instance_without_the_playback_components_says_so(self):
        self.contract.header_repairs = None

        with self.assertRaises(ValueError):
            rm_repair.w_media_repair(self.contract, {})

    def test_an_idle_instance_reports_idle_instead_of_nothing(self):
        state = rm_repair.q_media_repair(self.contract)

        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["total"], 0)


if __name__ == "__main__":
    unittest.main()
