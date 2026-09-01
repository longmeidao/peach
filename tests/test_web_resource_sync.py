"""资源对账域的隔离测试。

随 `web_resource_sync` 从 `web_contract` 一同拆出：测试巨石镜像代码巨石没有意义。
patch 目标必须指向真正执行的模块——这批用例大量 patch `source_is_online` 与
`translate_ledger_path`，拆分时若仍打在 `web_contract` 上，patch 会静默失效，
测试照样「通过」到断言才炸。
"""
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from peach import web_contract as rm_web
from peach import web_resource_sync as rm_sync

from test_rm_web import BASE_SCHEMA


class PurgeMissingTests(unittest.TestCase):
    """按目录对账：磁盘上已删掉的，账本行一并删掉。

    这条路径不可恢复，所以测试重点全在「什么时候**不该**删」。
    """

    LEDGER_DIR = r"B:\creator\P"
    OTHER_DIR = r"B:\creator\V"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = str(self.root / "ledger.db")
        con = sqlite3.connect(self.db_path)
        con.executescript(BASE_SCHEMA)
        sep = chr(92)
        rows = [
            (1, "115", self.LEDGER_DIR + sep + "001.jpg", "001.jpg"),
            (2, "115", self.LEDGER_DIR + sep + "002.jpg", "002.jpg"),
            (3, "115", self.LEDGER_DIR + sep + "003.jpg", "003.jpg"),
            # 同来源但另一个目录，任何情况下都不该被这次对账碰到。
            (4, "115", self.OTHER_DIR + sep + "a.mp4", "a.mp4"),
        ]
        con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,size) "
            "VALUES(?,?,?,?,'image',10)", rows)
        con.executemany("INSERT INTO asset_tag(asset_id,tag,source) VALUES(?,?,'t')",
                        [(2, "标签"), (4, "标签")])
        con.executemany(
            "INSERT INTO asset_preference(profile_id,asset_id,liked,reason) "
            "VALUES('default',?,1,'')", [(2,), (4,)])
        con.commit()
        con.close()
        self.contract = rm_web.WebContract(Path(self.db_path))
        # 只有 001 和 a.mp4 还在盘上；002、003 当作已被手动删除。
        for name in ("001.jpg", "a.mp4"):
            (self.root / name).write_bytes(b"x")

    def tearDown(self):
        self.tmp.cleanup()

    def _translate(self, raw):
        """把账本的 Windows 路径映射到临时目录里的同名文件。"""
        return self.root / str(raw).rsplit(chr(92), 1)[-1]

    def _run(self, online=True):
        patch_translate = mock.patch.object(
            rm_sync, "translate_ledger_path", self._translate)
        patch_online = mock.patch.object(
            rm_sync, "source_is_online", lambda _loc: online)
        with patch_translate, patch_online:
            return rm_sync.w_purge_missing(self.contract, {"id": 1})

    def ids(self):
        con = sqlite3.connect(self.db_path)
        try:
            return [r[0] for r in con.execute("SELECT id FROM asset ORDER BY id")]
        finally:
            con.close()

    def test_offline_source_refuses_instead_of_deleting_everything(self):
        """盘没挂上时，整目录都会 stat 失败——那不是「文件被删」。

        R: 实测掉线过；若不拦，2,552 条本地资产会一次全部消失。
        """
        result = self._run(online=False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "source offline")
        self.assertEqual(self.ids(), [1, 2, 3, 4])

    def test_missing_files_move_to_trash_without_losing_metadata(self):
        result = self._run()
        self.assertTrue(result["ok"])
        self.assertEqual(result["checked"], 3)
        self.assertEqual(result["removed"], 2)
        self.assertEqual(sorted(x["id"] for x in result["items"]), [2, 3])
        # 另一个目录的 4 必须原样留下；缺失项先进入回收站，恢复源文件后仍可还原。
        self.assertEqual(self.ids(), [1, 2, 3, 4])
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT disposal FROM asset WHERE id=2").fetchone()[0], "trash")
            self.assertEqual(
                con.execute("SELECT disposal FROM asset WHERE id=3").fetchone()[0], "trash")
            # 元数据等到清空回收站才随账本行一起删。
            self.assertEqual(
                [r[0] for r in con.execute("SELECT asset_id FROM asset_tag")], [2, 4])
            self.assertEqual(
                [r[0] for r in con.execute("SELECT asset_id FROM asset_preference")], [2, 4])
        finally:
            con.close()

    def test_full_sync_scans_all_online_assets_and_cleans_only_rebuildable_caches(self):
        roots = {}
        for name in ("snapshots", "posters", "photo-thumbs", "transcodes",
                     "stream-segments", "avatars", "covers"):
            roots[name] = self.root / name
            roots[name].mkdir()
        cache_files = [
            roots["snapshots"] / "2.jpg",
            roots["posters"] / "2_4.jpg",
            roots["photo-thumbs"] / "2.jpg",
            roots["transcodes"] / "2-10-20.mp4",
            roots["stream-segments"] / "2" / "10-20-6" / "0.ts",
            roots["avatars"] / "2.jpg",
            roots["covers"] / "hey-002.jpg",
        ]
        for path in cache_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"cache")
        evidence = self.root / "candidate.csv"
        evidence.write_text("review evidence", encoding="utf-8")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='HEY-002',snapshot_path=? WHERE id=2",
                    (str(cache_files[0]),))
        con.commit();con.close()
        self.contract.snapshot_root = roots["snapshots"]
        self.contract.poster_root = roots["posters"]
        self.contract.photo_root = roots["photo-thumbs"]
        self.contract.transcode_root = roots["transcodes"]
        self.contract.stream_root = roots["stream-segments"]
        self.contract.avatar_root = roots["avatars"]
        self.contract.cover_root = roots["covers"]
        self.contract.resource_cleanup_enabled = True

        def online(location):
            return location == "115"
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", online):
            preview = rm_sync.w_resource_sync_scan(self.contract)
            self.assertEqual(preview["missing"], 2)
            self.assertEqual(preview["cache"]["files"], len(cache_files))
            result = rm_sync.w_resource_sync_apply(
                self.contract, {"confirm": True, "clean_cache": True})

        self.assertEqual(result["moved_to_trash"], 2)
        self.assertEqual(result["cache_removed"], len(cache_files))
        self.assertTrue(all(not path.exists() for path in cache_files))
        self.assertTrue(evidence.is_file(), "候选证据不属于可删除缓存")
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM asset WHERE disposal='trash'").fetchone()[0], 2)
        finally:
            con.close()

    def test_full_sync_lists_each_directory_once_instead_of_stating_every_file(self):
        real_scandir = os.scandir
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", lambda loc: loc == "115"), \
             mock.patch.object(rm_sync.os, "scandir", wraps=real_scandir) as scandir:
            preview = rm_sync.w_resource_sync_scan(self.contract)

        self.assertEqual(preview["missing"], 2)
        self.assertEqual(scandir.call_count, 1)
        source = next(row for row in preview["sources"] if row["location"] == "115")
        self.assertEqual(source["checked"], 4)
        self.assertEqual(source["unreadable"], 0)

    def test_full_sync_skips_an_unreadable_directory_instead_of_trashing_it(self):
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", lambda loc: loc == "115"), \
             mock.patch.object(rm_sync.os, "scandir", side_effect=PermissionError("offline")):
            preview = rm_sync.w_resource_sync_scan(self.contract)

        self.assertEqual(preview["missing"], 0)
        source = next(row for row in preview["sources"] if row["location"] == "115")
        self.assertEqual(source["checked"], 0)
        self.assertEqual(source["unreadable"], 4)

    def test_background_sync_polls_then_rechecks_only_missing_candidates(self):
        idle = rm_sync.w_resource_sync_scan(
            self.contract, {"background": True, "status_only": True})
        self.assertEqual(idle["status"], "idle")
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", lambda loc: loc == "115"):
            started = rm_sync.w_resource_sync_scan(
                self.contract, {"background": True, "restart": True})
            self.assertEqual(started["status"], "running")
            deadline = time.time() + 2
            while True:
                status = rm_sync.w_resource_sync_scan(
                    self.contract, {"background": True})
                if status["status"] != "running":
                    break
                self.assertLess(time.time(), deadline)
                time.sleep(0.01)
            self.assertEqual(status["status"], "complete")
            self.assertEqual(status["missing"], 2)
            resumed = rm_sync.w_resource_sync_scan(
                self.contract, {"background": True, "status_only": True})
            self.assertEqual(resumed["scan_id"], status["scan_id"])
            result = rm_sync.w_resource_sync_apply(self.contract, {
                "confirm": True, "clean_cache": False, "scan_id": status["scan_id"],
            })

        self.assertEqual(result["moved_to_trash"], 2)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM asset WHERE disposal='trash'").fetchone()[0], 2)
        finally:
            con.close()

    def test_full_sync_keeps_a_cover_shared_by_an_active_asset(self):
        covers = self.root / "covers"
        covers.mkdir()
        shared = covers / "hey-002.jpg"
        shared.write_bytes(b"cover")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='HEY-002' WHERE id IN (1,2)")
        con.commit();con.close()
        self.contract.cover_root = covers
        self.contract.avatar_root = self.root / "avatars"
        self.contract.poster_root = self.root / "posters"
        self.contract.photo_root = self.root / "photo-thumbs"
        self.contract.transcode_root = self.root / "transcodes"
        self.contract.stream_root = self.root / "stream-segments"
        self.contract.resource_cleanup_enabled = True
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", lambda loc: loc == "115"):
            preview = rm_sync.w_resource_sync_scan(self.contract)
        self.assertEqual(preview["missing"], 2)
        self.assertTrue(shared.is_file())
        self.assertNotIn("covers", preview["cache"]["by_kind"])

    def test_cache_cleanup_never_crosses_the_database_data_root(self):
        """临时数据库漏配缓存根时，宁可不清理，也不能越界碰真实 generated。"""
        with tempfile.TemporaryDirectory() as outside_tmp:
            outside = Path(outside_tmp)
            cover = outside / "covers" / "orphan-001.jpg"
            segment = outside / "stream-segments" / "999" / "0.ts"
            cover.parent.mkdir()
            segment.parent.mkdir(parents=True)
            cover.write_bytes(b"cover")
            segment.write_bytes(b"segment")
            self.contract.cover_root = cover.parent
            self.contract.stream_root = outside / "stream-segments"
            self.contract.resource_cleanup_enabled = True

            result = rm_sync.clean_resource_orphans(self.contract)

            self.assertEqual(result["cache_removed"], 0)
            self.assertTrue(cover.is_file())
            self.assertTrue(segment.is_file())

    def test_intact_directory_reports_no_change(self):
        for name in ("002.jpg", "003.jpg"):
            (self.root / name).write_bytes(b"x")
        result = self._run()
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["checked"], 3)
        self.assertEqual(self.ids(), [1, 2, 3, 4])

    def test_purge_lists_the_directory_once_instead_of_statting_every_file(self):
        """逐条 is_file() 在云挂载上每条都是一次往返；已删路径没有负缓存，最贵。"""
        real_scandir = os.scandir
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", lambda loc: loc == "115"), \
             mock.patch.object(rm_sync.os, "scandir", wraps=real_scandir) as scandir:
            result = rm_sync.w_purge_missing(self.contract, {"id": 1})
        self.assertEqual(result["removed"], 2)
        self.assertEqual(scandir.call_count, 1)

    def test_purge_keeps_rows_when_the_directory_cannot_be_read(self):
        """目录暂时读不了不是「文件被删」：与全量扫描同款语义。

        改动前这里逐条 `is_file()`，读不了会被当成全部缺失、整目录误入回收站。
        """
        with mock.patch.object(rm_sync, "translate_ledger_path", self._translate), \
             mock.patch.object(rm_sync, "source_is_online", lambda loc: loc == "115"), \
             mock.patch.object(rm_sync.os, "scandir", side_effect=PermissionError("busy")):
            result = rm_sync.w_purge_missing(self.contract, {"id": 1})
        self.assertEqual(result["removed"], 0)
        self.assertEqual(result["unreadable"], 3)
        self.assertEqual(self.ids(), [1, 2, 3, 4])
