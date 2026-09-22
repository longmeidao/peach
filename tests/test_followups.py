"""任务后继（ADR-0040）：声明、去重、上限、串行、失败边界与重启续跑。"""
import json
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from peach import followups as followups_module
from peach import task_runs as task_runs_module
from peach.avatar_followup import TASK_KEY as AVATAR_TASK_KEY
from peach.avatar_followup import followup_key, parse_key, plan
from peach.followups import Followup, FollowupRunner, FollowupType, lanes
from peach.jav_cover_fetch import NotFound
from peach.jobs import BackgroundJob
from peach.library_processing import process_library
from peach.repository import LedgerDatabase
from peach.task_runs import MAX_FOLLOWUPS, TaskRunStore
from support.conditions import windows_ledger_roots
from support.ledger import fresh_ledger


@contextmanager
def registered(*types: FollowupType):
    """临时登记几种后继，出去时还原。登记表是模块级的，用例之间不能互相污染。"""
    previous = dict(followups_module.REGISTRY)
    followups_module.REGISTRY.clear()
    for followup_type in types:
        followups_module.REGISTRY[followup_type.task_key] = followup_type
    try:
        yield
    finally:
        followups_module.REGISTRY.clear()
        followups_module.REGISTRY.update(previous)


def echo_type(task_key: str, *, writes_ledger: bool = True, run=None) -> FollowupType:
    return FollowupType(task_key=task_key, label=task_key, writes_ledger=writes_ledger,
                        run=run or (lambda contract, key, handle: {"outcome": key}))


class LedgerTestCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.db = fresh_ledger(self.root)
        self.database = LedgerDatabase(self.db)
        self.store = TaskRunStore(self.database, host="test-host")

    def parent(self, task_key: str = "library-processing"):
        run = self.store.start(task_key, trigger="manual")
        self.assertIsNotNone(run)
        return run

    def wait_until_settled(self, parent_run_id: int, timeout: float = 10.0) -> None:
        """等这一批后继全部走到终态。

        `FollowupRunner.stop()` 不能当同步点用：它一置停止位，通道线程就不再认领下一条，
        队尾那几条会停在 `pending`，用例读到的是「还没轮到」而不是「串行跑完了」。
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rows = self.store.children(parent_run_id)
            if rows and all(row.finished_at for row in rows):
                return
            time.sleep(0.02)
        self.fail(f"后继没有在 {timeout} 秒内跑完")


class EnqueueTests(LedgerTestCase):
    def test_followups_become_pending_rows_under_their_parent(self):
        parent = self.parent()
        result = self.store.enqueue_followups(
            parent.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "补头像：甲")])
        self.assertEqual(len(result["queued"]), 1)
        child = self.store.get(result["queued"][0])
        self.assertEqual(child.status, "pending")
        self.assertEqual(child.parent_run_id, parent.id)
        self.assertEqual(child.root_run_id, parent.id)
        self.assertEqual(child.followup_depth, 1)
        self.assertEqual(child.followup_key, "entity-avatar:performer:1")
        # 触发方式继承父任务：这一条归根结底是那一次手动触发带出来的。
        self.assertEqual(child.trigger, "manual")
        self.assertEqual([row.id for row in self.store.children(parent.id)], [child.id])
        # 派出后继的那一轮自己就是这条链的根。
        self.assertEqual(self.store.get(parent.id).root_run_id, parent.id)

    def test_same_key_twice_in_one_declaration_only_queues_once(self):
        parent = self.parent()
        result = self.store.enqueue_followups(parent.id, [
            ("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲"),
            ("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲"),
            ("entity-avatar:performer:2", AVATAR_TASK_KEY, "乙"),
        ])
        self.assertEqual(len(result["queued"]), 2)
        self.assertEqual(result["duplicates"], 1)

    def test_a_key_already_queued_is_not_queued_again(self):
        first = self.parent()
        self.store.enqueue_followups(
            first.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])
        self.store.finish(first.id, "succeeded")
        second = self.store.start("scrape-codes", trigger="manual")
        result = self.store.enqueue_followups(
            second.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])
        self.assertEqual(result["queued"], [])
        self.assertEqual(result["duplicates"], 1)

    def test_a_key_whose_run_already_finished_can_be_queued_again(self):
        first = self.parent()
        queued = self.store.enqueue_followups(
            first.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])["queued"]
        self.store.finish(queued[0], "succeeded")
        second = self.store.start("scrape-codes", trigger="manual")
        result = self.store.enqueue_followups(
            second.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])
        self.assertEqual(len(result["queued"]), 1)

    def test_more_than_the_cap_is_truncated_and_counted(self):
        parent = self.parent()
        declared = [(f"entity-avatar:performer:{index}", AVATAR_TASK_KEY, "甲")
                    for index in range(MAX_FOLLOWUPS + 3)]
        result = self.store.enqueue_followups(parent.id, declared)
        self.assertEqual(len(result["queued"]), MAX_FOLLOWUPS)
        self.assertEqual(result["truncated"], 3)

    def test_depth_beyond_the_cap_queues_nothing(self):
        parent = self.parent()
        with mock.patch.object(task_runs_module, "MAX_FOLLOWUP_DEPTH", 1):
            child_id = self.store.enqueue_followups(
                parent.id, [("a:1", AVATAR_TASK_KEY, "甲")])["queued"][0]
            result = self.store.enqueue_followups(
                child_id, [("a:2", AVATAR_TASK_KEY, "乙")])
        self.assertEqual(result["queued"], [])
        self.assertEqual(result["depth_exceeded"], 1)


class RunnerTests(LedgerTestCase):
    def contract(self):
        return SimpleNamespace(task_runs=self.store)

    def test_drain_runs_queued_followups_and_settles_them(self):
        parent = self.parent()
        with registered(echo_type(AVATAR_TASK_KEY)):
            queued = self.store.enqueue_followups(
                parent.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])["queued"]
            self.assertEqual(FollowupRunner(self.contract()).drain(), 1)
        done = self.store.get(queued[0])
        self.assertEqual(done.status, "succeeded")
        self.assertEqual(done.result_summary["outcome"], "entity-avatar:performer:1")

    def test_ledger_writers_share_one_lane_and_never_overlap(self):
        live, peak = [0], [0]
        guard = threading.Lock()

        def slow(_contract, key, _handle):
            with guard:
                live[0] += 1
                peak[0] = max(peak[0], live[0])
            time.sleep(0.05)
            with guard:
                live[0] -= 1
            return {"outcome": key}

        parent = self.parent()
        first, second = (echo_type("ledger-a", run=slow), echo_type("ledger-b", run=slow))
        with registered(first, second):
            self.assertEqual(list(lanes()), [followups_module.LEDGER_LANE])
            self.store.enqueue_followups(parent.id, [
                ("ledger-a:1", "ledger-a", "甲"), ("ledger-a:2", "ledger-a", "乙"),
                ("ledger-b:1", "ledger-b", "丙"), ("ledger-b:2", "ledger-b", "丁"),
            ])
            runner = FollowupRunner(self.contract())
            runner.wake()
            self.wait_until_settled(parent.id)
            runner.stop(timeout=10)
        self.assertEqual(peak[0], 1)
        self.assertEqual(
            {row.status for row in self.store.children(parent.id)}, {"succeeded"})

    def test_types_that_do_not_write_the_ledger_get_their_own_lane(self):
        with registered(echo_type("ledger-a"), echo_type("cheap", writes_ledger=False)):
            self.assertEqual(sorted(lanes()), ["cheap", followups_module.LEDGER_LANE])

    def test_a_failed_followup_does_not_change_its_parent(self):
        def explode(_contract, _key, _handle):
            raise RuntimeError("取不到这张图")

        parent = self.parent()
        with registered(echo_type(AVATAR_TASK_KEY, run=explode)):
            queued = self.store.enqueue_followups(
                parent.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])["queued"]
            self.store.finish(parent.id, "succeeded", summary={"followups": 1})
            FollowupRunner(self.contract()).drain()
        child = self.store.get(queued[0])
        self.assertEqual(child.status, "failed")
        self.assertIn("取不到这张图", child.error)
        self.assertEqual(self.store.get(parent.id).status, "succeeded")
        self.assertEqual(self.store.get(parent.id).error, "")

    def test_an_unregistered_followup_fails_instead_of_holding_its_key(self):
        """账本里可能排着一种登记表里没有的后继。它得有个结局，否则互斥键一直占着。"""
        parent = self.parent()
        with registered(echo_type("ledger-a")):
            queued = self.store.enqueue_followups(
                parent.id, [("ledger-a:1", "ledger-a", "甲")])["queued"]
        runner = FollowupRunner(self.contract())
        with registered():
            runner._execute(self.store.get(queued[0]))
        failed = self.store.get(queued[0])
        self.assertEqual(failed.status, "failed")
        self.assertIn("ledger-a", failed.error)


class RestartTests(LedgerTestCase):
    def test_a_followup_left_running_is_queued_again_not_interrupted(self):
        parent = self.parent()
        queued = self.store.enqueue_followups(
            parent.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])["queued"]
        with self.database.write_transaction(notify=False) as connection:
            connection.execute(
                "UPDATE task_run SET status='running',started_at=? WHERE id=?",
                ("2026-09-22T00:00:00.000Z", queued[0]))
        # 先跑启动恢复：它必须放过后继，否则重排就再也没有机会。
        self.assertNotIn(queued[0], self.store.recover_interrupted(stale_after=0))
        self.assertEqual(self.store.requeue_followups(), queued)
        run = self.store.get(queued[0])
        self.assertEqual(run.status, "pending")
        self.assertIsNone(run.started_at)

    def test_a_queued_followup_survives_and_still_blocks_its_key(self):
        parent = self.parent()
        self.store.enqueue_followups(
            parent.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])
        self.store.recover_interrupted(stale_after=0)
        again = self.store.enqueue_followups(
            self.parent("scrape-codes").id,
            [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])
        self.assertEqual(again["duplicates"], 1)


class BackgroundJobDispatchTests(LedgerTestCase):
    def job(self, runner=None):
        return BackgroundJob("PeachTestJob", task_key="library-processing",
                             runs=self.store, followup_runner=runner)

    def declared(self):
        return [{"key": "entity-avatar:performer:1", "task_key": AVATAR_TASK_KEY,
                 "label": "补实体头像：甲"}]

    def test_a_successful_run_dispatches_what_it_declared(self):
        job = self.job()
        job.start(lambda job_id: job.update(
            job_id, status="complete", followups=self.declared()))
        job.thread.join(5)
        run = self.store.query(task_key="library-processing", limit=1)[0]
        self.assertEqual(run.status, "succeeded")
        self.assertEqual(run.result_summary["followups"], 1)
        # 声明本身是明细，不进摘要——摘要是活动页上一眼看完的那一行。
        self.assertNotIn("followups_declared", run.result_summary)
        self.assertEqual(len(self.store.children(run.id)), 1)

    def test_a_failed_run_dispatches_nothing(self):
        job = self.job()

        def work(job_id):
            job.update(job_id, followups=self.declared())
            raise RuntimeError("采集中断")

        job.start(work)
        job.thread.join(5)
        run = self.store.query(task_key="library-processing", limit=1)[0]
        self.assertEqual(run.status, "failed")
        self.assertEqual(self.store.children(run.id), [])

    def test_the_runner_is_woken_once_the_followups_are_queued(self):
        runner = mock.Mock()
        job = self.job(runner)
        job.start(lambda job_id: job.update(
            job_id, status="complete", followups=self.declared()))
        job.thread.join(5)
        runner.wake.assert_called_once_with()


class AvatarFollowupTests(LedgerTestCase):
    STAMP = "2026-09-22T00:00:00.000Z"

    def entity(self, kind: str, name: str) -> int:
        with self.database.write_transaction(notify=False) as connection:
            cursor = connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,"
                "created_at,updated_at) VALUES(?,?,?,?,?)",
                (kind, name, name.casefold(), self.STAMP, self.STAMP))
        return int(cursor.lastrowid)

    def test_the_key_round_trips(self):
        self.assertEqual(parse_key(followup_key("performer", 8022)), ("performer", 8022))
        with self.assertRaises(ValueError):
            parse_key("entity-avatar:series:1")

    def test_only_new_entities_without_an_avatar_are_planned(self):
        avatars = self.root / "avatars"
        avatars.mkdir()
        old = self.entity("performer", "旧人")
        fresh = self.entity("performer", "新人")
        studio = self.entity("studio", "新厂牌")
        dressed = self.entity("performer", "已有头像")
        (avatars / f"performer-{dressed}.img").write_bytes(b"jpeg")
        with self.database.read_connection() as connection:
            found = plan(connection, avatars, since_entity_id=old)
        self.assertEqual([item.key for item in found],
                         [followup_key("performer", fresh),
                          followup_key("studio", studio)])
        self.assertTrue(found[0].label.endswith("新人"))
        self.assertEqual({item.task_key for item in found}, {AVATAR_TASK_KEY})

    def test_an_entity_that_already_has_an_avatar_is_a_no_op(self):
        from peach.avatar_followup import run as avatar_run

        avatars = self.root / "avatars"
        avatars.mkdir()
        entity_id = self.entity("performer", "甲")
        (avatars / f"performer-{entity_id}.img").write_bytes(b"jpeg")
        contract = SimpleNamespace(
            avatar_root=avatars, candidate_root=self.root / "generated",
            database=self.database, task_runs=self.store, cache_bust=lambda: None)
        summary = avatar_run(contract, followup_key("performer", entity_id), None)
        self.assertEqual(summary, {"outcome": "已有头像"})

    def test_a_studio_is_only_recorded_never_installed(self):
        from peach.avatar_followup import run as avatar_run

        avatars = self.root / "avatars"
        avatars.mkdir()
        entity_id = self.entity("studio", "BAZOOKA")
        contract = SimpleNamespace(
            avatar_root=avatars, candidate_root=self.root / "generated",
            database=self.database, task_runs=self.store, cache_bust=lambda: None)
        summary = avatar_run(contract, followup_key("studio", entity_id), None)
        self.assertEqual(summary["outcome"], "等人复核")
        self.assertFalse((avatars / f"studio-{entity_id}.img").exists())

    def test_a_vanished_entity_is_not_a_failure(self):
        from peach.avatar_followup import run as avatar_run

        avatars = self.root / "avatars"
        avatars.mkdir()
        contract = SimpleNamespace(
            avatar_root=avatars, candidate_root=self.root / "generated",
            database=self.database, task_runs=self.store, cache_bust=lambda: None)
        summary = avatar_run(contract, followup_key("performer", 999), None)
        self.assertEqual(summary, {"outcome": "实体已不存在"})


class CoverFaceFollowupTests(LedgerTestCase):
    """图库给不出那一张时，从她单人作品的封面上截脸。

    人脸模型要下 ONNX，测试不出网：探针按封面宽度查一张表给出脸框，检脸本身由头像域
    的用例覆盖。
    """

    STAMP = AvatarFollowupTests.STAMP
    entity = AvatarFollowupTests.entity

    #: 封面宽 → 脸框（相对宽度）。没列的宽度是一张检不出脸的封面，比如戴着面具的原图。
    FACES = {600: 0.15, 276: 0.2, 1000: 0.3, 900: 0.5}

    def setUp(self):
        super().setUp()
        self.avatars = self.root / "avatars"
        self.avatars.mkdir()
        self.covers = self.root / "covers"
        self.covers.mkdir()
        self.person = self.entity("performer", "梨奈")
        faces = self.FACES

        class Probe:
            unavailable = ""

            def on_bytes(self, body):
                from peach.images import measure_image_size
                width, height = measure_image_size(body)
                share = faces.get(width)
                face = ({"cx": 0.5, "cy": 0.4, "w": share, "h": share, "score": 0.9}
                        if share else None)
                return {"ratio": width / height, "px": [width, height], "face": face}

        patcher = mock.patch("peach.avatar_face.FaceProbe", Probe)
        patcher.start()
        self.addCleanup(patcher.stop)
        # 装图那一步会顺手算人脸边车，同样不出网。
        sidecar = mock.patch("peach.avatar_provider.FaceProbe")
        sidecar.start().return_value.return_value = None
        self.addCleanup(sidecar.stop)

    def work(self, asset_id: int, code: str, size: tuple[int, int] | None,
             performers: tuple[int, ...] = ()) -> None:
        from PIL import Image

        if size:
            Image.new("RGB", size, "gray").save(self.covers / f"{code}.jpg", format="JPEG")
        with self.database.write_transaction(notify=False) as connection:
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,code,size) "
                "VALUES(?,'R:',?,?,'video',?,100)",
                (asset_id, f"R:\\media\\{code}.mp4", f"{code}.mp4", code))
            for entity_id in performers or (self.person,):
                connection.execute(
                    "INSERT INTO asset_entity(asset_id,entity_id,role,source) "
                    "VALUES(?,?,'performer','test')", (asset_id, entity_id))

    def contract(self):
        return SimpleNamespace(
            avatar_root=self.avatars, candidate_root=self.root / "generated",
            cover_root=self.covers, database=self.database, task_runs=self.store,
            cache_bust=lambda: None)

    def run_followup(self) -> dict:
        from peach.avatar_followup import run as avatar_run

        return avatar_run(self.contract(), followup_key("performer", self.person), mock.Mock())

    def provenance(self) -> dict:
        return json.loads((self.avatars / f"performer-{self.person}.img.provenance.json")
                          .read_text(encoding="utf-8"))

    def test_the_widest_face_wins_over_the_biggest_cover(self):
        """戴面具的大图检不出脸，对头像毫无用处；挑的是脸上有多少像素。"""
        self.work(1, "FC2-PPV-1", (1800, 1000))
        self.work(2, "FC2-PPV-2", (276, 154))
        self.work(3, "FC2-PPV-3", (600, 400))
        other = self.entity("performer", "别人")
        self.work(4, "FC2-PPV-4", (900, 600), performers=(self.person, other))
        summary = self.run_followup()
        self.assertEqual((summary["outcome"], summary["source"]),
                         ("已装上", "作品封面 FC2-PPV-3"))
        record = self.provenance()
        self.assertEqual((record["provider"], record["external_id"], record["face_px"]),
                         ("cover-face", "FC2-PPV-3", 90))
        self.assertFalse(record["identity_verified"])
        # 90 像素的脸放大 2.4 倍是 216 的方框，以脸心为中心。
        self.assertEqual(record["crop_box"], [192, 52, 408, 268])
        # 没装上的那张缩略图人脸也截好留作候选，挑图弹层里一点就换；双人作品照旧不碰。
        kept = [json.loads(path.read_text(encoding="utf-8"))
                for path in (self.root / "generated").rglob(f"evidence/performer-{self.person}-*.json")]
        self.assertEqual(sorted((one["provider"], one["external_id"]) for one in kept),
                         [("cover-face", "FC2-PPV-2"), ("cover-face", "FC2-PPV-3")])

    def test_a_thumbnail_is_the_floor_not_nothing(self):
        self.work(1, "FC2-PPV-1", (1800, 1000))
        self.work(2, "FC2-PPV-2", (276, 154))
        self.assertEqual(self.run_followup()["source"], "作品封面 FC2-PPV-2")
        self.assertEqual(self.provenance()["face_px"], 55)

    def test_a_clearer_cover_later_replaces_the_crop_and_nothing_else_does(self):
        self.work(2, "FC2-PPV-2", (276, 154))
        self.run_followup()
        self.assertEqual(self.run_followup()["outcome"], "已是最清楚的封面人脸")
        self.work(5, "FC2-PPV-5", (1000, 600))
        self.assertEqual(self.run_followup()["source"], "作品封面 FC2-PPV-5")
        self.assertEqual(self.provenance()["face_px"], 300)

    def test_a_whole_cover_installed_earlier_gives_way_to_any_face(self):
        self.work(2, "FC2-PPV-2", (276, 154))
        (self.avatars / f"performer-{self.person}.img").write_bytes(b"jpeg")
        (self.avatars / f"performer-{self.person}.img.provenance.json").write_text(
            json.dumps({"provider": "cover-fallback"}), encoding="utf-8")
        self.assertEqual(self.run_followup()["source"], "作品封面 FC2-PPV-2")
        self.assertEqual(self.provenance()["provider"], "cover-face")

    def test_a_picture_someone_chose_is_never_replaced(self):
        self.work(5, "FC2-PPV-5", (1000, 600))
        (self.avatars / f"performer-{self.person}.img").write_bytes(b"jpeg")
        (self.avatars / f"performer-{self.person}.img.provenance.json").write_text(
            json.dumps({"provider": "picker"}), encoding="utf-8")
        self.assertEqual(self.run_followup(), {"outcome": "已有头像"})

    def test_no_face_on_any_cover_installs_nothing(self):
        self.work(1, "FC2-PPV-1", (1800, 1000))
        summary = self.run_followup()
        self.assertEqual(summary["outcome"], "图库里没有这个名字，封面上没有能截的脸")
        self.assertFalse((self.avatars / f"performer-{self.person}.img").exists())

    def test_a_new_cover_plans_her_again_only_while_her_picture_is_a_crop(self):
        self.work(2, "FC2-PPV-2", (276, 154))
        chosen = self.entity("performer", "人挑过")
        self.work(6, "FC2-PPV-6", (600, 400), performers=(chosen,))
        (self.avatars / f"performer-{chosen}.img").write_bytes(b"jpeg")
        self.run_followup()
        watermark = chosen
        with self.database.read_connection() as connection:
            found = plan(connection, self.avatars, since_entity_id=watermark,
                         covered_asset_ids=[2, 6])
        self.assertEqual([item.key for item in found],
                         [followup_key("performer", self.person)])


class ProcessLibraryTests(LedgerTestCase):
    """一整条链走通：刮削登记新女优 → 声明后继 → 派出 → 真的跑完。

    这里不桩 `avatar_followup`：跑的就是补头像那条后继本身。图库索引在临时数据根下是空的，
    封面目录也是空的，于是它两档都给不出图并正常收尾——判不准不装图，本来就是这条后继的判据。
    """

    def sample(self):
        from peach.settings_file import PeachConfig

        media = self.root / 'media'
        media.mkdir()
        (media / 'ABW-358.mp4').write_bytes(b'video')
        (media / 'ABW-358.nfo').write_text(
            '<movie><title>作品</title><sorttitle>ABW-358</sorttitle></movie>',
            encoding='utf-8')
        return media, PeachConfig(self.root, self.root / 'config.toml', present=True,
                                  locations={'local': (str(media),)})

    def provider(self):
        provider = mock.Mock()
        provider.community.side_effect = NotFound('社区来源都没有这个番号')
        provider.cover.return_value = False
        provider.query.return_value = {
            'id': 'ABW-358',
            'actresses': [{'dmm_id': 1051912, 'japanese_name': '涼森れむ',
                           'profile_source': 'r18dev'}],
        }
        return provider

    @windows_ledger_roots
    def test_a_scrape_declares_dispatches_and_runs_its_avatar_followups(self):
        _media, config = self.sample()
        result = process_library(config, self.db, self.root / 'generated',
                                 self.root / 'covers',
                                 provider_factory=mock.Mock(return_value=self.provider()),
                                 database=self.database)
        self.assertEqual(result['status'], 'complete')
        with self.database.read_connection() as connection:
            entity_id = connection.execute(
                "SELECT id FROM entity WHERE kind='performer'"
                " AND canonical_name='涼森れむ'").fetchone()[0]
        # 一、刮削自己声明了后继，实体身份就在 key 里。
        self.assertEqual([item['key'] for item in result['followups']],
                         [followup_key('performer', entity_id)])

        # 二、结算这一轮时派出去，排成父任务下的一行。
        parent = self.parent()
        queued = self.store.enqueue_followups(
            parent.id, [(item['key'], item['task_key'], item['label'])
                        for item in result['followups']])['queued']
        self.assertEqual(len(queued), 1)

        # 三、真的被跑掉，收在终态。
        contract = SimpleNamespace(
            task_runs=self.store, database=self.database,
            avatar_root=self.root / 'generated' / 'avatars',
            candidate_root=self.root / 'generated', cover_root=self.root / 'covers',
            cache_bust=lambda: None)
        self.assertEqual(FollowupRunner(contract).drain(), 1)
        done = self.store.get(queued[0])
        self.assertEqual(done.status, 'succeeded')
        self.assertEqual(done.result_summary['outcome'], '图库里没有这个名字，封面上没有能截的脸')
        self.assertFalse((self.root / 'generated' / 'avatars'
                          / f'performer-{entity_id}.img').exists())


class TaskPayloadTests(LedgerTestCase):
    def test_the_detail_endpoint_gives_both_ends_of_the_chain(self):
        from peach.web_tasks import q_task

        parent = self.parent()
        queued = self.store.enqueue_followups(
            parent.id, [("entity-avatar:performer:1", AVATAR_TASK_KEY, "甲")])["queued"]
        contract = SimpleNamespace(task_runs=self.store)
        payload = q_task(contract, parent.id)
        self.assertIsNone(payload["parent"])
        self.assertEqual([row["id"] for row in payload["followups"]], queued)
        self.assertEqual(payload["followup_counts"], {"pending": 1})
        child = q_task(contract, queued[0])
        self.assertEqual(child["parent"]["id"], parent.id)
        self.assertEqual(child["run"]["followup_key"], "entity-avatar:performer:1")
        self.assertEqual(child["run"]["followup_depth"], 1)
        # 契约是 JSON，派生字段不能带出 Path、set 这类东西。
        json.dumps(payload)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
