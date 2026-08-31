"""预览生成的并发行为。

`previews.py` 此前没有直接对应的测试（检视报告把它列为覆盖盲区）。这里先补上
最要紧的一条：生成锁的粒度。功能正确性由 `/api/entity`、`/logo` 等端点的既有
测试间接覆盖，本文件只管并发。
"""
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from peach import previews
from peach.previews import PreviewService
from peach.repository import MediaAsset


class GenerateLockStripingTests(unittest.TestCase):
    def test_the_same_destination_always_takes_the_same_lock(self):
        """同一个目标必须同一把锁：两个线程同时生成同一个文件，
        `os.replace` 会互相覆盖，而其中一个的临时文件可能已经被删了。"""
        target = Path("/generated/posters/42_4.jpg")
        self.assertIs(previews._generate_lock(target), previews._generate_lock(Path(target)))

    def test_different_destinations_spread_across_stripes(self):
        """分片要真的分开——全落一片就退化成原来那把全局锁。"""
        locks = {id(previews._generate_lock(Path(f"/generated/posters/{n}_4.jpg")))
                 for n in range(64)}
        self.assertGreater(len(locks), 1, "64 个不同目标不该全挤在一把锁上")
        self.assertLessEqual(len(locks), previews._LOCK_STRIPES)


class ParallelGenerationTests(unittest.TestCase):
    """两个资产的预览生成必须能同时进行。

    改成分片锁之前这里是一把模块级全局锁：任何一个资产在生成，其他资产全排队，
    而 `avatar()` 持锁要连跑 6 次 ffmpeg（每次 20 秒上限）。

    断言方式换过两版，都栽在同一件事上——不要让"谁先到"决定分工：
    第一版用 Barrier 双向等待，满载时两边一起超时；第二版用
    `if not first_inside.is_set()` 判断谁是第一个，但那不是原子的，两个线程可能
    同时判成第一个、双双挂起等待放行，于是第二个信号永远不来。这次按 asset id
    静态分工：LEFT 负责占住锁，RIGHT 负责证明它能在此期间进来，没有竞态可言。
    """

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.snapshot_root = root / "snapshots"
        self.snapshot_root.mkdir()
        self.poster_root = root / "posters"
        for asset_id in (self.LEFT, self.RIGHT):
            (self.snapshot_root / f"{asset_id}.jpg").write_bytes(b"snapshot")

        repository = SimpleNamespace(media_asset=lambda asset_id: MediaAsset(
            id=asset_id, path=None,
            snapshot_path=str(self.snapshot_root / f"{asset_id}.jpg"),
        ))
        resolver = SimpleNamespace(
            ffmpeg=lambda: SimpleNamespace(path=Path("ffmpeg")))
        self.service = PreviewService(
            repository, resolver, self.snapshot_root, self.poster_root,
            root / "avatars", root / "logos",
        )

    def tearDown(self):
        self.tmp.cleanup()

    #: 两个落在不同锁片上的资产 id；同片的话这个测试就没有意义了。
    LEFT, RIGHT = None, None

    @classmethod
    def setUpClass(cls):
        stripe = lambda n: id(previews._generate_lock(Path(f"posters/{n}_4.jpg")))
        base = 1
        for other in range(2, 200):
            if stripe(base) != stripe(other):
                cls.LEFT, cls.RIGHT = base, other
                return
        raise AssertionError("找不到落在不同锁片上的两个资产 id")

    def test_two_assets_do_not_queue_behind_each_other(self):
        # 分工按 asset id 定死，不看谁先到：LEFT 占住自己那把锁不放，
        # RIGHT 必须能在这期间跑完自己的生成。锁真的分片了 RIGHT 才进得来。
        holder_inside, other_done = threading.Event(), threading.Event()
        release_holder = threading.Event()
        timeout = 15

        def fake_run(command):
            target = Path(command[-1]).name
            if target.startswith(f"{self.LEFT}_"):
                holder_inside.set()
                release_holder.wait(timeout)
            else:
                other_done.set()
            Path(command[-1]).write_bytes(b"jpg")

        done = []
        with mock.patch.object(PreviewService, "_run", staticmethod(fake_run)):
            workers = [
                threading.Thread(
                    target=lambda a=asset: done.append(self.service.poster(a)),
                    daemon=True)
                for asset in (self.LEFT, self.RIGHT)
            ]
            for worker in workers:
                worker.start()
            self.assertTrue(holder_inside.wait(timeout), "占锁的那个生成没有开始")
            entered = other_done.wait(timeout)
            release_holder.set()
            for worker in workers:
                worker.join(timeout)

        self.assertTrue(
            entered,
            "另一个资产在这一个持锁期间进不来——生成锁又变回全局串行了",
        )
        self.assertEqual(len(done), 2, "两个生成都要完成")
        self.assertTrue(all(path.is_file() for path in done))

    def test_the_same_asset_is_generated_only_once(self):
        """同一个资产并发请求两次，只跑一次 ffmpeg：持锁后要再看一眼文件在不在。"""
        calls = []
        entered = threading.Event()

        def fake_run(command):
            calls.append(command[-1])
            entered.set()
            Path(command[-1]).write_bytes(b"jpg")

        with mock.patch.object(PreviewService, "_run", staticmethod(fake_run)):
            workers = [
                threading.Thread(
                    target=lambda: self.service.poster(self.LEFT), daemon=True)
                for _ in range(2)
            ]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(8)

        self.assertEqual(len(calls), 1, f"同一目标只该生成一次，实际 {len(calls)} 次")


if __name__ == "__main__":
    unittest.main()
