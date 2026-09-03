"""预览生成的并发行为，以及「取不取得到」和真正取图的一致性。

`previews.py` 此前没有直接对应的测试（检视报告把它列为覆盖盲区）。这里先补上
最要紧的一条：生成锁的粒度。功能正确性由 `/api/entity`、`/logo` 等端点的既有
测试间接覆盖。

后半部分是另一件事。页面按 `WebContract.has_entity_image()` / `has_avatar()` 决定
要不要输出 `<img>`，这两个判据和 `PreviewService` 真正的取图必须在同一个目录上给出
同一个答案，所以这里把两边摆在一处对照着测。
"""
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from peach import previews, web_review
from peach.previews import PreviewService, PreviewUnavailable, entity_image_key
from peach.repository import MediaAsset
from peach.web_state import WebContract


class GenerateLockStripingTests(unittest.TestCase):
    def test_the_same_destination_always_takes_the_same_lock(self):
        """同一个目标必须同一把锁：两个线程同时生成同一个文件，
        `os.replace` 会互相覆盖，而其中一个的临时文件可能已经被删了。"""
        target = Path("/generated/posters/42_4.jpg")
        self.assertIs(previews._generate_lock(target), previews._generate_lock(Path(target)))

    def test_different_destinations_spread_across_stripes(self):
        """分片要真的分开——全落一片就退化成一把全局锁。"""
        locks = {id(previews._generate_lock(Path(f"/generated/posters/{n}_4.jpg")))
                 for n in range(64)}
        self.assertGreater(len(locks), 1, "64 个不同目标不该全挤在一把锁上")
        self.assertLessEqual(len(locks), previews._LOCK_STRIPES)


class ParallelGenerationTests(unittest.TestCase):
    """两个资产的预览生成必须能同时进行。

    一把模块级全局锁会让任何一个资产在生成时其他资产全排队，而 `avatar()` 持锁
    要连跑 6 次 ffmpeg（每次 20 秒上限）。

    断言方式试过两种跑真线程的写法，都栽在同一件事上——不要让"谁先到"决定分工：
    Barrier 双向等待在满载时两边一起超时；`if not first_inside.is_set()` 判断谁是
    第一个不是原子的，两个线程可能同时判成第一个、双双挂起等待放行，于是第二个
    信号永远不来。这里按 asset id 静态分工：LEFT 负责占住锁，RIGHT 负责证明它能
    在此期间进来，没有竞态可言。
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

    def test_two_assets_can_hold_their_locks_at_the_same_time(self):
        """不同资产的锁必须能被同时持有——这就是分片的全部意义。

        这条断言试过三种跑真线程的写法。头两种都想直接证明"并行发生了"：Barrier
        双向等待在满载时两边一起超时；靠 `Event.is_set()` 判断谁先到不是原子的；
        按 asset id 静态分工的那种单独跑 8/8 通过，全量满载下仍然翻车。

        它们失败的都不是被测代码，而是"在满载机器上观测两个线程真的重叠了"这件事
        本身——那是调度器说了算的。而反复假红比没有这条测试更糟：它会训练人忽略红色。

        要证明的东西其实不需要并发：分片锁的贡献是"不同目标映射到不同的锁对象"，
        锁本身能不能同时持有是 threading 的语义，标准库负责。所以直接对锁对象断言。
        真正的互斥语义由下面那条"同一资产只生成一次"覆盖，它不依赖并行时序。
        """
        left = previews._generate_lock(Path(f"posters/{self.LEFT}_4.jpg"))
        right = previews._generate_lock(Path(f"posters/{self.RIGHT}_4.jpg"))
        self.assertIsNot(left, right, "不同目标必须落在不同锁片上")
        self.assertTrue(left.acquire(blocking=False))
        try:
            self.assertTrue(
                right.acquire(blocking=False),
                "一把锁被占住时另一把仍应可得——否则又退回全局串行",
            )
            right.release()
        finally:
            left.release()

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


class EntityImageAvailabilityTests(unittest.TestCase):
    """「这个实体有没有图」必须和 `/entity-image` 真正的取图判据逐字一致。

    判得松一格，页面就为一个必然 404 的地址出 `<img>`；紧一格，明明装了的图从此
    只显示首字母。所以每条都对照着 `PreviewService.entity_image()` 测，不各测一半。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.avatars = root / "avatars"
        self.avatars.mkdir()
        self.service = PreviewService(
            SimpleNamespace(), SimpleNamespace(), root / "snapshots", root / "posters",
            self.avatars, root / "logos")
        # 库文件不必存在：可用性判定只扫目录，一个字节都不查库。但 `avatar_root` 得
        # 显式指到临时目录，默认值是本机真实的 generated 树。
        self.contract = WebContract(root / "ledger.db", avatar_root=self.avatars)

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, name):
        (self.avatars / name).write_bytes(b"x")

    def resolves(self, kind, entity_id):
        try:
            self.service.entity_image(kind, entity_id)
        except PreviewUnavailable:
            return False
        return True

    def assertAgrees(self, kind, entity_id):
        """可用性判定和取图在同一个目录上必须给同一个答案。"""
        available = self.contract.has_entity_image(kind, entity_id)
        self.assertEqual(available, self.resolves(kind, entity_id),
                         f"{kind}-{entity_id}：可用性说 {available}，取图不同意")
        return available

    def test_an_installed_image_is_available_and_a_missing_one_is_not(self):
        self.install("performer-11.img")
        self.assertTrue(self.assertAgrees("performer", 11))
        self.assertFalse(self.assertAgrees("performer", 12))

    def test_the_kind_is_part_of_the_name_not_just_the_id(self):
        """creator 的图落在 `creator-<id>.img`，拿 performer 去问不该命中。

        两边少认一层 kind，就会出现「装的是 creator、页面按 performer 问」这种恒假，
        那张图从此不显示。
        """
        self.install("creator-12.img")
        self.assertTrue(self.assertAgrees("creator", 12))
        self.assertFalse(self.assertAgrees("performer", 12))

    def test_a_sidecar_is_not_an_entity_image(self):
        """`.ct`、来源留档、人脸取景都躺在同一个目录里，但都不是取图会返回的文件。"""
        self.install("performer-11.img.ct")
        self.install("performer-11.provenance.json")
        self.install("performer-11.face.json")
        self.assertFalse(self.assertAgrees("performer", 11))

    def test_an_unknown_kind_is_never_available(self):
        """`/entity-image` 只认那几种实体，别的一律 404，页面不该发得出来。"""
        self.install("photo-11.img")
        self.assertFalse(self.assertAgrees("photo", 11))

    def test_a_missing_entity_id_is_never_available(self):
        """身份格里没规范到实体的那些格子没有 id，它们只有首字母。"""
        for entity_id in (None, "", "abc"):
            with self.subTest(entity_id=entity_id):
                self.assertFalse(self.contract.has_entity_image("performer", entity_id))

    def test_availability_is_case_insensitive_like_the_resolver(self):
        """`is_file()` 在 Windows 和 macOS 的默认文件系统上大小写不敏感，
        索引不能顺手把这层容错丢掉。"""
        self.install("Performer-11.img")
        self.assertTrue(self.contract.has_entity_image("performer", 11))

    def test_a_missing_avatar_directory_is_an_empty_index(self):
        """目录还没建（新机器、干净数据目录）时全部退回首字母，不是报错。"""
        root = Path(self.tmp.name).resolve()
        contract = WebContract(root / "ledger.db", avatar_root=root / "nowhere")
        self.assertEqual(contract.avatar_root_index().entity_images, frozenset())
        self.assertFalse(contract.has_entity_image("performer", 11))

    def test_a_newly_installed_image_shows_up_after_the_cache_bust(self):
        """索引带 TTL，但复核批准会 `cache_bust()`：刚装上的图立刻可见。"""
        self.assertFalse(self.contract.has_entity_image("performer", 11))
        self.install("performer-11.img")
        self.contract.cache_bust()
        self.assertTrue(self.contract.has_entity_image("performer", 11))

    def test_the_install_path_and_the_resolver_share_one_key_rule(self):
        """批准落地写的文件名和取图找的文件名只能有一份实现。"""
        self.assertIs(web_review.entity_image_key, entity_image_key)


class AvatarAvailabilityTests(unittest.TestCase):
    """头像不是有和没有两态：`/avatar` 按需生成，还没裁过不等于取不到。

    真缺（印相不在盘上了）和没抓过（印相还在、只是没人要过）必须分开。把后者也判成
    没有，等于把点一下就有的那条路永远关掉。
    """

    ASSET = 7

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.avatars = root / "avatars"
        self.avatars.mkdir()
        self.snapshots = root / "snapshots"
        self.snapshots.mkdir()
        self.snapshot = self.snapshots / f"{self.ASSET}.jpg"
        repository = SimpleNamespace(media_asset=lambda asset_id: MediaAsset(
            id=asset_id, path=None,
            snapshot_path=str(self.snapshot) if self.snapshot.is_file() else None))
        tools = SimpleNamespace(ffmpeg=lambda: SimpleNamespace(path=Path("ffmpeg")))
        self.service = PreviewService(
            repository, tools, self.snapshots, root / "posters", self.avatars,
            root / "logos")
        self.contract = WebContract(
            root / "ledger.db", avatar_root=self.avatars, snapshot_root=self.snapshots)

    def tearDown(self):
        self.tmp.cleanup()

    def available(self):
        return self.contract.has_avatar(
            self.ASSET, str(self.snapshot) if self.snapshot.is_file() else None)

    def test_an_already_cut_avatar_is_available_and_needs_nothing_else(self):
        (self.avatars / f"{self.ASSET}.jpg").write_bytes(b"jpg")
        self.assertTrue(self.available())
        self.assertEqual(self.service.avatar(self.ASSET),
                         self.avatars / f"{self.ASSET}.jpg")

    def test_an_asset_without_its_snapshot_is_never_available(self):
        """印相不在盘上就是真缺：可用性说没有，取图也确实取不到。"""
        self.assertFalse(self.available())
        with self.assertRaises(PreviewUnavailable):
            self.service.avatar(self.ASSET)

    def test_a_snapshot_still_on_disk_counts_before_anyone_ever_asks(self):
        """还没裁过但印相还在，算取得到——第一次请求就现裁一张出来。

        这是「没抓过」不是「没有」。判成没有的话页面从此不出这个 `<img>`，
        那张本来点一下就有的头像永远不会被生成。
        """
        self.snapshot.write_bytes(b"snapshot")
        self.assertFalse((self.avatars / f"{self.ASSET}.jpg").exists())
        self.assertTrue(self.available())

        def fake_run(command):
            Path(command[-1]).write_bytes(b"jpg")

        # 亮度探针走的是 `subprocess.run` 而不是 `_run`，不一起挡住的话六格全判成
        # 全黑，`avatar()` 会以「snapshot is too dark」拒绝。
        bright = SimpleNamespace(stdout=bytes([200]))
        with mock.patch.object(PreviewService, "_run", staticmethod(fake_run)):
            with mock.patch.object(previews.subprocess, "run", return_value=bright):
                self.assertTrue(self.service.avatar(self.ASSET).is_file())

    def test_a_half_finished_temporary_file_is_not_an_avatar(self):
        """生成中途的 `<id>.<格>.tmp.jpg` 随时会被改名或删掉，不算裁好了。"""
        (self.avatars / f"{self.ASSET}.11.tmp.jpg").write_bytes(b"jpg")
        self.assertFalse(self.available())

    def test_a_newly_cut_avatar_shows_up_after_the_cache_bust(self):
        self.assertFalse(self.available())
        (self.avatars / f"{self.ASSET}.jpg").write_bytes(b"jpg")
        self.contract.cache_bust()
        self.assertTrue(self.available())

    def test_a_missing_asset_id_is_never_available(self):
        self.snapshot.write_bytes(b"snapshot")
        for asset_id in (None, "", "abc"):
            with self.subTest(asset_id=asset_id):
                self.assertFalse(self.contract.has_avatar(asset_id, str(self.snapshot)))
