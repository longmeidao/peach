import csv
import importlib.util
import json
import sqlite3
import struct
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from peach import __version__


ROOT = Path(__file__).resolve().parents[1]


HAS_DEPS = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))
if HAS_DEPS:
    import httpx
    from peach import api as api_module
    from peach.api import create_app
    from peach.follow_covers import PLACEHOLDER_CONTENT_TYPE
    from peach.config import PeachSettings


BASE_SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY, location TEXT NOT NULL, path TEXT NOT NULL, name TEXT,
  medium TEXT, size INTEGER, creator TEXT, studio TEXT, series TEXT, code TEXT, release_date TEXT,
  catalog_title TEXT, original_title TEXT,
  duration REAL, width INTEGER, height INTEGER, ctx_length TEXT, ctx_orient TEXT,
  ctx_quality TEXT, play_count INTEGER DEFAULT 0, last_played TEXT, rating INTEGER,
  o_count INTEGER, watch_ratio REAL, stash_scene_id INTEGER, snapshot_path TEXT, first_seen TEXT,
  feedback TEXT, disposal TEXT, leave_ratio REAL, play_seconds REAL,
  feedback_at REAL, seek_count INTEGER, max_reached REAL,
  UNIQUE(location,path));
CREATE TABLE asset_tag(asset_id INTEGER,tag TEXT,confidence REAL DEFAULT 1.0,source TEXT,
                       UNIQUE(asset_id,tag));
CREATE TABLE entity(
  id INTEGER PRIMARY KEY,kind TEXT,canonical_name TEXT,normalized_name TEXT,
  metadata_json TEXT DEFAULT '{}',created_at TEXT,updated_at TEXT,
  UNIQUE(kind,normalized_name));
CREATE TABLE entity_alias(
  entity_id INTEGER,alias TEXT,normalized_alias TEXT,source TEXT,confidence REAL DEFAULT 1.0);
CREATE TABLE entity_external_ref(
  entity_id INTEGER,provider TEXT,external_kind TEXT,external_id TEXT,
  metadata_json TEXT DEFAULT '{}',last_synced_at TEXT);
CREATE TABLE entity_link(
  id INTEGER PRIMARY KEY,entity_id INTEGER,link_kind TEXT,label TEXT,url TEXT,
  hostname TEXT,is_sensitive INTEGER DEFAULT 0,metadata_json TEXT DEFAULT '{}',
  created_at TEXT,updated_at TEXT);
CREATE TABLE entity_search_term(
  entity_id INTEGER,term TEXT,purpose TEXT,source TEXT,created_at TEXT);
CREATE TABLE asset_entity(
  asset_id INTEGER,entity_id INTEGER,role TEXT,source TEXT,confidence REAL,
  metadata_json TEXT DEFAULT '{}',first_seen_at TEXT,last_seen_at TEXT,
  UNIQUE(asset_id,entity_id,role,source));
CREATE TABLE entity_membership(
  member_id INTEGER PRIMARY KEY,agency_id INTEGER,source TEXT,
  confidence REAL DEFAULT 1.0,checked_at TEXT);
CREATE TABLE watch_queue(profile_id TEXT,asset_id INTEGER,added_at TEXT,source TEXT,
  PRIMARY KEY(profile_id,asset_id));
CREATE TABLE playlist(
  id INTEGER PRIMARY KEY,profile_id TEXT,name TEXT,source_kind TEXT,
  source_seed_asset_id INTEGER,current_asset_id INTEGER,created_at TEXT,updated_at TEXT);
CREATE TABLE playlist_item(
  playlist_id INTEGER,asset_id INTEGER,position INTEGER,added_at TEXT,
  PRIMARY KEY(playlist_id,asset_id),UNIQUE(playlist_id,position));
CREATE TABLE asset_preference(profile_id TEXT,asset_id INTEGER,liked INTEGER,reason TEXT,
  source TEXT,updated_at TEXT,PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_quality_goal(profile_id TEXT,asset_id INTEGER,wanted INTEGER,reason TEXT,
  updated_at TEXT,PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_tag_preference(profile_id TEXT,asset_id INTEGER,normalized_tag TEXT,
  hidden INTEGER,updated_at TEXT,PRIMARY KEY(profile_id,asset_id,normalized_tag));
CREATE TABLE media_binding(
  asset_id INTEGER,backend TEXT,external_id TEXT,metadata_json TEXT,last_synced_at TEXT,
  PRIMARY KEY(asset_id,backend),UNIQUE(backend,external_id));
CREATE TABLE activity_event(id INTEGER PRIMARY KEY,asset_id INTEGER,kind TEXT,created_at TEXT);
CREATE TABLE search_history(
  query TEXT PRIMARY KEY, used_count INTEGER NOT NULL DEFAULT 1, last_used_at TEXT NOT NULL);
CREATE TABLE review_decision(
  category TEXT NOT NULL,item_key TEXT NOT NULL,status TEXT NOT NULL,
  reviewer TEXT NOT NULL DEFAULT 'local-default',note TEXT NOT NULL DEFAULT '',updated_at TEXT NOT NULL,
  PRIMARY KEY(category,item_key));
"""


def _box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + kind + payload


def minimal_mp4(*, timescale: int, sample_delta: int, samples: int, keyframe_every: int) -> bytes:
    """只含时间表的最小 MP4：够 peach.mp4index 解析关键帧，不含真实媒体数据。"""
    mdhd = _box(b"mdhd", struct.pack(">4sIIII HH", bytes(4), 0, 0, timescale,
                                     samples * sample_delta, 0, 0))
    hdlr = _box(b"hdlr", struct.pack(">4sI4s", bytes(4), 0, b"vide") + bytes(12))
    stts = _box(b"stts", struct.pack(">IIII", 0, 1, samples, sample_delta))
    sync = [n for n in range(1, samples + 1) if (n - 1) % keyframe_every == 0]
    stss = _box(b"stss", struct.pack(">II", 0, len(sync))
                + b"".join(struct.pack(">I", n) for n in sync))
    stbl = _box(b"stbl", stts + stss)
    mdia = _box(b"mdia", mdhd + hdlr + _box(b"minf", stbl))
    return (_box(b"ftyp", b"isom" + bytes(8))
            + _box(b"moov", _box(b"trak", mdia))
            + _box(b"mdat", bytes(64)))


class MediaCacheHeaderTests(unittest.TestCase):
    """生成物的缓存时长只许在一处写死。

    这条断言扫的是媒体路由真正所在的模块。钉死扫 `api.py` 的话，媒体路由拆到
    `routes_media.py` 之后它会永远绿——那里已经一条媒体路由都没有了。门槛跟着
    实现走，不跟着文件名走。
    """

    def test_no_media_endpoint_hardcodes_a_day(self):
        source = (ROOT / "src" / "peach" / "routes_media.py").read_text(encoding="utf-8")
        self.assertIn("MEDIA_CACHE_SECONDS", source, "媒体路由不在这个文件里了，门槛已空转")
        self.assertNotIn("max-age=86400", source, "媒体端点不该再写死一天")
        # `immutable` 只许出现在 /vendor/ 那条中间件里，它留在 api.py。这里不查
        # 字面量：常量上方那段注释正是在解释「为什么不加 immutable」。
        self.assertNotIn('"public, max-age=31536000, immutable"', source)


@unittest.skipUnless(HAS_DEPS, "FastAPI/httpx 尚未安装")
class FastApiContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "ledger.db"
        self.media_root = self.root / "media"
        self.snapshot_root = self.root / "snapshots"
        self.legacy_snapshot_root = self.root / "legacy-snapshots"
        self.poster_root = self.root / "posters"
        self.avatar_root = self.root / "avatars"
        self.logo_root = self.root / "logos"
        self.cover_root = self.root / "covers"
        self.transcode_root = self.root / "transcodes"
        self.stream_root = self.root / "stream-segments"
        self.photo_root = self.root / "photo-thumbs"
        self.vendor_root = self.root / "vendor"
        self.taste_store = self.root / "sources" / "taste-history" / "history.sqlite"
        self.taste_import_root = self.root / "sources" / "taste-history" / "imports"
        self.taste_output_root = self.root / "review" / "taste-history"
        self.taste_manifest = self.root / "state" / "taste-history" / "manifest.json"
        # 复核候选必须来自临时目录，不去读真实的 R:\peach-data\generated。
        self.candidate_root = self.root / "generated"
        self.candidate_root.mkdir()
        self.endcard_frame = (
            self.candidate_root / "endcard-evidence" / "1" / "tail-000098000.png"
        )
        self.endcard_frame.parent.mkdir(parents=True)
        self.endcard_frame.write_bytes(b"endcard")
        for path in (self.media_root, self.snapshot_root, self.poster_root,
                     self.avatar_root, self.logo_root, self.cover_root,
                     self.vendor_root):
            path.mkdir()
        (self.vendor_root / "player.js").write_text("window.vendorReady=true;", encoding="utf-8")
        self.media_file = self.media_root / "one.mp4"
        self.media_file.write_bytes(b"0123456789")
        # HLS 分片按真实关键帧切，所以它的测试媒体必须带可解析的 moov/stss；
        # Range 契约测试仍用上面那个 10 字节文件，两者不要互相牵连。
        self.hls_file = self.media_root / "segmented.mp4"
        self.hls_file.write_bytes(minimal_mp4(timescale=1000, sample_delta=40,
                                              samples=338, keyframe_every=25))
        self.snapshot_file = self.snapshot_root / "cloud" / "local" / "one.jpg"
        self.snapshot_file.parent.mkdir(parents=True)
        self.snapshot_file.write_bytes(b"snapshot")
        self.legacy_snapshot_file = self.legacy_snapshot_root / "cloud" / "local" / "one.jpg"
        (self.poster_root / "1_4.jpg").write_bytes(b"poster")
        (self.avatar_root / "1.jpg").write_bytes(b"avatar")
        (self.logo_root / "Studio_A.img").write_bytes(b"logo")
        (self.logo_root / "Studio_A.img.ct").write_text("image/png", encoding="utf-8")
        self.page = self.root / "index.html"
        self.page.write_text("<!doctype html><title>Peach test</title><main>ready</main>", encoding="utf-8")
        # 前端已拆成 ES module，`/js/{name}` 从页面同级的 js/ 取文件。
        (self.root / "js").mkdir()
        (self.root / "js" / "core.js").write_text("export const ok = 1;", encoding="utf-8")
        # island 产物（ADR-0022）：构建结果提交进 Git，运行时由 `/dist/{name}` 提供。
        (self.root / "dist").mkdir()
        (self.root / "dist" / "peach-ui.js").write_text(
            "export const mountIsland = () => {};", encoding="utf-8")
        (self.root / "dist" / "peach-ui.css").write_text(".island{}", encoding="utf-8")
        con = sqlite3.connect(self.db)
        con.executescript(BASE_SCHEMA)
        con.executescript((ROOT / "migrations" / "0018_online_follow.sql").read_text(
            encoding="utf-8"))
        con.execute(
            """INSERT INTO asset(id,location,path,name,medium,size,creator,studio,duration,
                                  width,height,ctx_orient,snapshot_path,first_seen)
               VALUES(1,'local',?,'one.mp4','video',100,
                      'Alice','Studio A',100,1920,1080,'横屏',?,'2026-08-14')""",
            (str(self.media_file), str(self.legacy_snapshot_file)),
        )
        con.execute("INSERT INTO asset_tag(asset_id,tag,source) VALUES(1,'Tag A','test')")
        con.execute(
            "INSERT INTO asset_tag(asset_id,tag,source) "
            "VALUES(1,'官方标签','javinizer:r18dev:tag')"
        )
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(1,'tag','Tag A','tag a')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,1,'tag','test',1.0)"
        )
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(2002,'tag','官方标签','官方标签')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,2002,'tag','javinizer:r18dev:tag',0.9)"
        )
        con.commit()
        con.close()
        self.settings = PeachSettings(
            db_path=self.db, configured=True, token="secret", page_path=self.page, vendor_path=self.vendor_root,
            allowed_media_roots=(self.media_root,), snapshot_root=self.snapshot_root,
            legacy_snapshot_roots=(self.legacy_snapshot_root,),
            poster_root=self.poster_root, avatar_root=self.avatar_root, logo_root=self.logo_root,
            cover_root=self.cover_root, stream_root=self.stream_root,
            ffmpeg_root=self.root / "ffmpeg", transcode_root=self.transcode_root,
            candidate_root=self.candidate_root, photo_root=self.photo_root,
            taste_history_store=self.taste_store,
            taste_history_import_root=self.taste_import_root,
            taste_history_output_root=self.taste_output_root,
            taste_history_manifest=self.taste_manifest,
        )
        self.app = create_app(self.settings)
        # 字节与时间表夹具不含可解码画面；编码判定由媒体域的真实样本覆盖。
        from peach.transcodes import _MediaProfile
        self.profile_patch = patch.object(
            self.app.state.transcode_service, "_probe",
            return_value=_MediaProfile("h264", "yuv420p", "aac"),
        )
        self.profile_patch.start()
        self.addCleanup(self.profile_patch.stop)
        self.assertIs(
            self.app.state.web_contract.database,
            self.app.state.repository.database,
        )
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.tmp.cleanup()

    async def test_health_is_side_effect_free(self):
        response = await self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "fastapi")
        self.assertEqual(response.json()["version"], __version__)

    async def test_reader_role_keeps_gets_available_and_rejects_posts(self):
        class ReaderSync:
            status = "reader"
            detail = "写入端是 mac"
            read_only = True
            read_only_message = "账本由 mac 负责写入，本机当前只能浏览。"

            def observe(self):
                return None

            def start(self):
                return None

            def stop(self):
                return None

        class ReaderMirror:
            def resolve(self, payload):
                result = dict(payload)
                result["mirror"] = {"state": "live", "read_only": True}
                return result

        app = create_app(self.settings, ReaderSync(), ReaderMirror())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        ) as client:
            health = await client.get("/healthz")
            self.assertEqual(health.json()["ledger_sync"], "reader")
            self.assertTrue(health.json()["ledger_read_only"])
            self.assertIn("只能浏览", health.json()["ledger_read_only_message"])
            reviewed = await client.get("/api/review?t=secret")
            self.assertEqual(reviewed.status_code, 200)
            self.assertEqual(reviewed.json()["mirror"]["state"], "live")
            listed = await client.get("/api/items?t=secret")
            self.assertEqual(listed.status_code, 200)
            denied = await client.post(
                "/api/feedback?t=secret", json={"id": 1, "kind": "dispose"},
            )
            self.assertEqual(denied.status_code, 409)
            body = denied.json()
            self.assertEqual(body["error"], "ledger read-only")
            # `detail` 是诊断串，界面要展示的是 `message`；缺了它前端只能显示内部原话。
            self.assertEqual(body["detail"], "写入端是 mac")
            self.assertIn("只能浏览", body["message"])

    async def test_replication_off_runs_as_a_standalone_writer(self):
        """`replication.enabled = false` 时没有 sync 对象（ADR-0023 第 3 阶段）。

        `ledger_sync` 必须是明确的 `disabled`，不能冒充 `writer`：复核镜像那一侧
        正是按这个字段判断对面是不是写入端的。写接口照常开——没有第二台机器就没有
        「读者」，只读闸门本来就不该生效。
        """
        app = create_app(self.settings, None)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        ) as client:
            health = (await client.get("/healthz")).json()
            self.assertEqual(health["ledger_sync"], "disabled")
            self.assertFalse(health["ledger_read_only"])
            allowed = await client.post(
                "/api/feedback?t=secret", json={"id": 1, "kind": "dispose"},
            )
            self.assertNotEqual(allowed.status_code, 409)

    async def test_peach_logo_is_served_as_png(self):
        response = await self.client.get("/peach-logo.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))

    async def test_front_end_modules_are_served_and_the_name_cannot_escape(self):
        """ES module 拆分之后新增的静态路由。

        路径穿越是静态路由最典型的入口。这里不做 resolve 后比根目录，而是根本不接受
        分隔符——名字必须是一层平铺的 `[a-z0-9_-]+.js`，别的一律 404。
        """
        served = await self.client.get("/js/core.js?t=secret")
        self.assertEqual(served.status_code, 200)
        self.assertTrue(served.headers["content-type"].startswith("text/javascript"))
        # 页面资产走 ETag 复验：更新语义与 no-store 相同（每次都回源问），但没变时
        # 回 304 零传输。完整契约在 tests/test_web_perf.py，这里只钉住用的是哪一档。
        self.assertEqual(served.headers["cache-control"], "no-cache")
        self.assertIn("export", served.text, "取回的必须是真的 module")

        for escape in ("..%2f..%2fapp.js", "..%5c..%5csecrets.json", "sub%2fmod.js",
                       "Core.js", "core.mjs", "core.js.map"):
            denied = await self.client.get(f"/js/{escape}?t=secret")
            self.assertEqual(denied.status_code, 404, f"{escape} 不该被提供")

    async def test_front_end_modules_need_the_same_token_as_the_page(self):
        unauthorized = await self.client.get("/js/core.js")
        self.assertEqual(unauthorized.status_code, 401)

    async def test_island_bundle_is_served_with_the_same_guards_as_the_modules(self):
        """`/dist/{name}` 提供 `frontend/` 的构建产物（ADR-0022）。

        产物文件名不带内容哈希，`app.js` 直接 `import('/dist/peach-ui.js')`，所以这条
        路由的口令、缓存与名字校验必须和 `/js/` 完全一致，不能因为「是构建产物」放宽。
        """
        for name, media in (("peach-ui.js", "text/javascript"), ("peach-ui.css", "text/css")):
            served = await self.client.get(f"/dist/{name}?t=secret")
            self.assertEqual(served.status_code, 200, name)
            self.assertTrue(served.headers["content-type"].startswith(media), name)
            self.assertEqual(served.headers["cache-control"], "no-cache", name)

        for escape in ("..%2f..%2fapp.js", "..%5c..%5csecrets.json", "sub%2fpeach-ui.js",
                       "..%2fapp.js", "peach-ui.js.map", "peach-ui.mjs", "Peach-UI.js"):
            denied = await self.client.get(f"/dist/{escape}?t=secret")
            self.assertEqual(denied.status_code, 404, f"{escape} 不该被提供")

        unauthorized = await self.client.get("/dist/peach-ui.js")
        self.assertEqual(unauthorized.status_code, 401)

    async def test_follow_avatar_redirects_only_after_the_official_resolver(self):
        denied = await self.client.get("/follow-avatar?service=fanbox&id=30917150")
        self.assertEqual(denied.status_code, 401)
        # patch 打在真正 import 它的模块上。`/follow-avatar` 现在住在 routes_media，
        # 打在 `peach.api` 上会静默失效——那个名字已经不在那里了。
        with patch("peach.routes_media.resolve_official_avatar",
                   return_value="https://pixiv.pximg.net/icon.jpeg") as resolver:
            response = await self.client.get(
                "/follow-avatar?t=secret&service=fanbox&id=30917150")
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"],
                         "https://pixiv.pximg.net/icon.jpeg")
        resolver.assert_called_once_with("fanbox", "30917150")

    async def test_unauthorized_keeps_three_shapes_grouped_by_route_class(self):
        """401 三种形态按路由类分组，收敛到 Depends 之后也不许并成一种。

        页面路由跳登录页、页面资产回 PlainText 提示、API 与媒体路由回 JSON。
        统一 Depends 后每种形态仍必须出现在正确的路由类上。
        """
        page = await self.client.get("/")
        self.assertEqual(page.status_code, 303)
        self.assertEqual(page.headers["location"], "/login?next=/")

        asset = await self.client.get("/app.js")
        self.assertEqual(asset.status_code, 401)
        self.assertEqual(asset.text, "需要 ?t=口令")
        self.assertTrue(asset.headers["content-type"].startswith("text/plain"))

        api = await self.client.get("/api/items")
        self.assertEqual(api.status_code, 401)
        self.assertEqual(api.json(), {"error": "unauthorized"})

        media = await self.client.get("/thumb?id=1")
        self.assertEqual(media.status_code, 401)
        self.assertEqual(media.json(), {"error": "unauthorized"})

    async def test_emptying_the_recycle_bin_is_actually_wired_and_deletes_media(self):
        """接线本身要有测试：此前 dispatch 接上了 `/api/trash/empty`，函数却根本没写。

        单测直接调用函数抓不到这类错误，只有走一遍 HTTP 才会暴露。
        """
        disposed = await self.client.post("/api/feedback?t=secret",
                                          json={"id": 1, "kind": "dispose"})
        self.assertEqual(disposed.json()["disposal"], "trash")
        self.assertTrue(self.media_file.exists())

        emptied = await self.client.post("/api/trash/empty?t=secret")
        self.assertEqual(emptied.status_code, 200)
        self.assertEqual(emptied.json()["purged"], 1)
        self.assertEqual(emptied.json()["blocked"], [])
        self.assertFalse(self.media_file.exists(), "清空回收站必须真的删掉媒体文件")

        listed = await self.client.get("/api/items?t=secret")
        self.assertEqual([item["id"] for item in listed.json()["items"]], [])

    async def test_recycle_bin_route_and_batch_delete_are_reachable(self):
        legacy = await self.client.get("/trash?t=secret")
        self.assertEqual(legacy.status_code, 303)
        self.assertEqual(legacy.headers["location"], "/trash")
        page = await self.client.get("/trash")
        self.assertEqual(page.status_code, 200)
        refused = await self.client.post("/api/batch?t=secret",
                                         json={"ids": [1], "operation": "delete"})
        self.assertEqual(refused.status_code, 400, "不在回收站的资产不允许彻底删除")

        await self.client.post("/api/feedback?t=secret", json={"id": 1, "kind": "dispose"})
        deleted = await self.client.post("/api/batch?t=secret",
                                         json={"ids": [1], "operation": "delete"})
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["purged"], 1)
        self.assertFalse(self.media_file.exists())

    async def test_ads_queue_batch_disposal_removes_the_candidate(self):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "UPDATE asset SET name='扫码加入福利群.mp4',size=?,duration=60 WHERE id=1",
            (20 * 1024 * 1024,),
        )
        connection.commit(); connection.close()

        before = await self.client.get("/api/ads?t=secret")
        self.assertEqual([item["id"] for item in before.json()["items"]], [1])

        disposed = await self.client.post(
            "/api/batch?t=secret", json={"ids": [1], "operation": "dispose"},
        )
        self.assertEqual(disposed.status_code, 200)
        self.assertEqual(disposed.json()["changed"], 1)

        after = await self.client.get("/api/ads?t=secret")
        self.assertEqual(after.json()["items"], [])
        recycle_bin = await self.client.get("/api/items?t=secret&state=trash")
        self.assertEqual([item["id"] for item in recycle_bin.json()["items"]], [1])

    async def test_ads_queue_can_filter_and_reverse_not_junk_decisions(self):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "UPDATE asset SET name='Mib19.com.zip',medium='archive',size=? WHERE id=1",
            (14 * 1024**3,),
        )
        connection.commit(); connection.close()

        archive = await self.client.get("/api/ads?t=secret&kind=archive")
        self.assertEqual([item["id"] for item in archive.json()["items"]], [1])
        self.assertEqual(archive.json()["counts"]["archive"], 1)

        dismissed = await self.client.post(
            "/api/batch?t=secret", json={"ids": [1], "operation": "dismiss-junk"},
        )
        self.assertEqual(dismissed.status_code, 200)
        self.assertEqual((await self.client.get("/api/ads?t=secret")).json()["items"], [])
        excluded = (await self.client.get("/api/ads?t=secret&status=dismissed")).json()
        self.assertEqual([item["id"] for item in excluded["items"]], [1])

        reconsidered = await self.client.post(
            "/api/batch?t=secret", json={"ids": [1], "operation": "reconsider-junk"},
        )
        self.assertEqual(reconsidered.status_code, 200)
        self.assertEqual(
            [item["id"] for item in (await self.client.get("/api/ads?t=secret")).json()["items"]],
            [1],
        )

    async def test_search_history_is_shared_through_the_api(self):
        saved = await self.client.post("/api/search-history?t=secret", json={"query": "ABW"})
        self.assertEqual(saved.status_code, 200)
        history = await self.client.get("/api/search-history?t=secret")
        self.assertEqual(history.json()["items"], ["ABW"])
        removed = await self.client.post("/api/search-history?t=secret", json={"operation": "remove", "query": "ABW"})
        self.assertEqual(removed.status_code, 200)

    async def test_taste_import_combines_private_history_with_peach_behavior(self):
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute(
                "UPDATE asset SET play_count=2,play_seconds=600,last_played=? WHERE id=1",
                (1_700_000_200,),
            )
            connection.commit()
        payload = json.dumps([{
            "url": "https://rule34.xxx/index.php?page=post&s=list&tags=tag+a",
            "dt": 1_700_000_000,
            "metadata": None,
        }]).encode()
        imported = await self.client.post(
            "/api/taste/import?t=secret",
            content=payload,
            headers={"Content-Type": "application/octet-stream",
                     "X-Peach-Filename": "history.json"},
        )
        self.assertEqual(imported.status_code, 200, imported.text)
        dashboard = imported.json()["dashboard"]
        self.assertEqual(dashboard["summary"]["history_visits"], 1)
        self.assertEqual(dashboard["summary"]["peach_items"], 1)
        self.assertEqual(dashboard["rankings"]["tags"][0]["name"], "Tag A")
        self.assertNotIn("rule34.xxx/index.php", imported.text)
        self.assertTrue(self.taste_store.is_file())
        self.assertTrue(self.taste_manifest.is_file())

        listed = await self.client.get("/api/taste?t=secret&window=all")
        self.assertEqual(listed.status_code, 200)
        source_key = listed.json()["sources"][0]["source_key"]
        removed = await self.client.post(
            "/api/taste/source?t=secret",
            json={"operation": "remove", "source_key": source_key, "window": "all"},
        )
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(removed.json()["removed"], 1)
        self.assertEqual(removed.json()["dashboard"]["summary"]["history_visits"], 0)

    async def test_entity_focus_uses_the_apps_configured_avatar_root(self):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(2,'performer','Alice','alice')"
        )
        connection.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,2,'performer','test',1.0)"
        )
        connection.commit(); connection.close()
        (self.avatar_root / "performer-2.face.json").write_text(
            '{"focus":{"axis":"y","pct":23}}', encoding="utf-8")

        response = await self.client.get(
            "/api/entity?t=secret&kind=performer&name=Alice"
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["avatar_focus"], {"axis": "y", "pct": 23})

    async def test_review_queue_is_readable_and_decisions_are_persisted(self):
        response = await self.client.get("/api/review?t=secret")
        self.assertEqual(response.status_code, 200)
        self.assertIn("metadata_fields", response.json()["sections"])
        self.assertIn("creator_tags", response.json()["sections"])
        decided = await self.client.post(
            "/api/review/decision?t=secret",
            json={"category": "media_failure", "item_key": "12510", "status": "skipped"},
        )
        self.assertEqual(decided.status_code, 200)

    async def test_quality_goal_queue_is_readable_from_management(self):
        saved = await self.client.post(
            "/api/quality-goal?t=secret", json={"id": 1, "wanted": True},
        )
        self.assertEqual(saved.status_code, 200)
        response = await self.client.get("/api/quality-goals?t=secret&limit=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["id"], 1)

    async def test_metadata_field_candidate_is_approved_through_the_http_contract(self):
        connection = sqlite3.connect(self.db)
        connection.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        connection.commit(); connection.close()
        candidate = {
            "candidate_key": "ABC-001:studio:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "value": "Studio B", "display_value": "Studio B", "warnings": [],
            "raw_snapshot": "/evidence.json",
        }
        fields = ["item_key", "code", "query", "field", "field_label", "current_value",
                  "candidates_json", "source_count", "status", "size_gb", "videos", "fetched_at"]
        path = self.candidate_root / "metadata-field-candidates-20260822.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerow({
                "item_key": "ABC-001:studio", "code": "ABC-001", "query": "ABC-001",
                "field": "studio", "field_label": "厂牌", "current_value": "Studio A",
                "candidates_json": json.dumps([candidate]), "source_count": "1",
                "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
            })
        approved = await self.client.post("/api/review/decision?t=secret", json={
            "category": "metadata_fields", "item_key": "ABC-001:studio",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["applied_assets"], 1)
        connection = sqlite3.connect(self.db)
        self.assertEqual(connection.execute("SELECT studio FROM asset WHERE id=1").fetchone()[0], "Studio B")
        self.assertEqual(connection.execute(
            "SELECT e.canonical_name FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=1 AND ae.source='javinizer:r18dev:studio'"
        ).fetchall(), [("Studio B",)])
        connection.close()

    async def test_metadata_tag_approval_promotes_an_existing_tag_to_official_source(self):
        connection = sqlite3.connect(self.db)
        connection.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        connection.execute(
            "INSERT INTO asset_tag(asset_id,tag,confidence,source) "
            "VALUES(1,'乳系',0.4,'filename')"
        )
        connection.commit(); connection.close()
        candidate = {
            "candidate_key": "ABC-001:tags:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "value": ["乳系", "颜射"], "display_value": "乳系、颜射", "warnings": [],
        }
        fields = ["item_key", "code", "query", "field", "field_label", "current_value",
                  "candidates_json", "source_count", "status", "size_gb", "videos", "fetched_at"]
        path = self.candidate_root / "metadata-field-candidates-20260822.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerow({
                "item_key": "ABC-001:tags", "code": "ABC-001", "query": "ABC-001",
                "field": "tags", "field_label": "标签", "current_value": "乳系",
                "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
                "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
            })
        approved = await self.client.post("/api/review/decision?t=secret", json={
            "category": "metadata_fields", "item_key": "ABC-001:tags",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(approved.status_code, 200, approved.text)
        connection = sqlite3.connect(self.db)
        self.assertEqual(connection.execute(
            "SELECT tag,confidence,source FROM asset_tag WHERE asset_id=1 "
            "AND tag IN ('乳系','颜射') ORDER BY tag"
        ).fetchall(), [
            ("乳系", 0.9, "javinizer:r18dev:tag"),
            ("颜射", 0.9, "javinizer:r18dev:tag"),
        ])
        connection.close()

    async def test_catalog_keeps_missing_performers_separate_from_release_code(self):
        with closing(sqlite3.connect(self.db)) as con:
            con.execute(
                "INSERT INTO asset(id,location,path,name,medium,size,code,studio,first_seen) "
                "VALUES(29999,'local',?,'JBS-023.mp4','video',10,'JBS-023','Prestige','2026-09-05')",
                (str((self.media_root / 'JBS-023.mp4').resolve()),),
            )
            con.commit()
        response = await self.client.get('/api/items?t=secret&loc=local')
        self.assertEqual(response.status_code, 200)
        item = next(row for row in response.json()['items'] if row['id'] == 29999)
        self.assertEqual(item['code'], 'JBS-023')
        self.assertFalse(item.get('creator'))
        self.assertEqual(item['performers'], [])
        self.assertEqual(item['performer_entities'], [])

    async def test_auth_and_items_contract(self):
        denied = await self.client.get("/api/items")
        self.assertEqual(denied.status_code, 401)
        wrong_cookie = await self.client.get(
            "/api/items", headers={"Cookie": "notok=secret"}
        )
        self.assertEqual(wrong_cookie.status_code, 401)
        cookie = await self.client.get(
            "/api/items?loc=local&limit=10", headers={"Cookie": "tok=secret"}
        )
        self.assertEqual(cookie.status_code, 200)
        response = await self.client.get("/api/items?t=secret&loc=local&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertTrue(data["items"][0]["has_thumb"])
        self.assertNotIn("path", data["items"][0])
        self.assertEqual(response.headers["cache-control"], "no-store")

        scoped = await self.client.get("/api/facets?t=secret&id=1")
        self.assertEqual(scoped.status_code, 200)
        self.assertEqual(scoped.json()["locations"], [
            {"k": "local", "n": 1, "played": 0},
        ])
        self.assertEqual(scoped.json()["orientations"], [
            {"k": "横屏", "n": 1},
        ])

    async def test_global_facets_supply_recommendations_for_an_untagged_detail(self):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "INSERT INTO asset(id,location,path,name,medium,first_seen) "
            "VALUES(2,'online','https://example.test/untagged','Untagged','video','2026-08-31')"
        )
        connection.commit(); connection.close()

        scoped = await self.client.get("/api/facets?t=secret&id=2")
        recommended = await self.client.get("/api/facets?t=secret")
        self.assertEqual(scoped.status_code, 200)
        self.assertEqual(scoped.json()["tags"], [])
        self.assertEqual(recommended.status_code, 200)
        self.assertIn({"k": "Tag A", "n": 1, "cat": "general"}, recommended.json()["tags"])

    async def test_saved_online_asset_survives_the_default_thumbnail_filter(self):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "INSERT INTO asset(id,location,path,name,medium,first_seen) "
            "VALUES(2,'online','https://example.test/post/2','Saved online post','video','2026-08-30')"
        )
        connection.commit(); connection.close()

        listed = await self.client.get(
            "/api/items?t=secret&loc=online&thumb=1&limit=10"
        )
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["total"], 1)
        self.assertEqual(listed.json()["items"][0]["location"], "online")
        self.assertFalse(listed.json()["items"][0]["has_thumb"])

    async def test_multipart_api_keeps_assets_separate_but_returns_an_ordered_queue(self):
        connection = sqlite3.connect(self.db)
        connection.executemany(
            "INSERT INTO asset(id,location,path,name,medium,size,studio,code,duration,"
            "width,height,first_seen) VALUES(?,'local',?,?,'video',?,'S1','OJIE-325',?,"
            "1920,1080,'2026-08-28')",
            [
                (4, str(self.media_root / "OJIE-325-B.mp4"), "OJIE-325-B.mp4", 10_000, 14349),
                (5, str(self.media_root / "OJIE-325-A.mp4"), "OJIE-325-A.mp4", 20_000, 14281),
            ],
        )
        connection.commit(); connection.close()

        listed = (await self.client.get("/api/items?t=secret&q=OJIE-325&limit=10")).json()
        self.assertEqual(listed["total"], 2)
        self.assertTrue(all(item["part_group"]["count"] == 2 for item in listed["items"]))
        queue = (await self.client.get("/api/parts?t=secret&id=4")).json()
        self.assertEqual([item["part_label"] for item in queue["items"]], ["A", "B"])
        self.assertTrue(all("path" not in item for item in queue["items"]))

    async def test_unexpected_contract_errors_are_logged_but_not_exposed(self):
        with patch(
            "peach.routes_api.web_contract.dispatch_api_get",
            side_effect=RuntimeError("private C:\\ledger.db detail"),
        ):
            with self.assertLogs("peach.routes_api", level="ERROR") as captured:
                response = await self.client.get("/api/items?t=secret")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "internal server error"})
        self.assertNotIn("ledger.db", response.text)
        self.assertIn("private C:\\ledger.db detail", "\n".join(captured.output))

    async def test_preference_is_an_independent_authenticated_write(self):
        denied = await self.client.post(
            "/api/preference", json={"id": 1, "liked": True, "reason": "镜头自然"},
        )
        self.assertEqual(denied.status_code, 401)
        saved = await self.client.post(
            "/api/preference?t=secret",
            json={"id": 1, "liked": True, "reason": "镜头自然"},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json(), {
            "ok": True, "liked": True, "like_reason": "镜头自然",
        })
        detail = await self.client.get("/api/item?t=secret&id=1")
        self.assertTrue(detail.json()["liked"])
        self.assertEqual(detail.json()["like_reason"], "镜头自然")

    async def test_item_detail_exposes_official_title_and_official_tag_marker(self):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "UPDATE asset SET catalog_title='正式作品标题',original_title='原标题',"
            "studio='Prestige',code='ABW-232' WHERE id=1"
        )
        connection.commit(); connection.close()
        detail = (await self.client.get("/api/item?t=secret&id=1")).json()
        self.assertEqual(detail["catalog_title"], "正式作品标题")
        self.assertEqual(detail["original_title"], "原标题")
        self.assertEqual(detail["display_code"], "ABW-232")
        self.assertIn("edition_badges", detail)
        official = next(tag for tag in detail["tags"] if tag["k"] == "官方标签")
        self.assertTrue(official["official"])

    async def test_provider_health_is_authenticated_and_secret_free(self):
        denied = await self.client.get("/api/providers")
        self.assertEqual(denied.status_code, 401)
        response = await self.client.get("/api/providers?t=secret")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["providers"]), 3)
        self.assertNotIn("secret_ref", response.text)

    async def test_item_tags_are_authenticated_and_source_evidence_is_preserved(self):
        denied = await self.client.post(
            "/api/item-tag", json={"id": 1, "operation": "remove", "tag": "Tag A"},
        )
        self.assertEqual(denied.status_code, 401)
        removed = await self.client.post(
            "/api/item-tag?t=secret",
            json={"id": 1, "operation": "remove", "tag": "Tag A"},
        )
        self.assertEqual(removed.status_code, 200)
        self.assertNotIn("Tag A", removed.json()["tags"])
        added = await self.client.post(
            "/api/item-tag?t=secret",
            json={"id": 1, "operation": "add", "tag": "手动标签"},
        )
        self.assertEqual(added.status_code, 200)
        self.assertIn("手动标签", added.json()["tags"])

    async def test_opencode_models_endpoint_is_explicit_and_normalized(self):
        denied = await self.client.get("/api/providers/opencode-go/models")
        self.assertEqual(denied.status_code, 401)
        with patch("peach.api.OpenCodeGoClient.list_models", return_value=[{
            "id": "kimi-k3", "object": "model", "owned_by": "opencode",
        }]) as discover:
            response = await self.client.get(
                "/api/providers/opencode-go/models?t=secret",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["models"][0]["id"], "kimi-k3")
        discover.assert_called_once_with()

    async def test_post_writes_only_test_database(self):
        response = await self.client.post(
            "/api/activity", headers={"X-Token": "secret"},
            json={"id": 1, "position": 50, "duration": 100, "delta": 7, "seeks": 1},
        )
        self.assertEqual(response.status_code, 200)
        con = sqlite3.connect(self.db)
        row = con.execute("SELECT play_seconds,seek_count,max_reached FROM asset WHERE id=1").fetchone()
        con.close()
        self.assertEqual(row, (7.0, 1, 0.5))

    async def test_home_sets_exact_http_only_cookie(self):
        denied = await self.client.get("/")
        self.assertEqual(denied.status_code, 303)
        self.assertEqual(denied.headers["location"], "/login?next=/")
        legacy = await self.client.get("/?t=secret")
        self.assertEqual(legacy.status_code, 303)
        self.assertEqual(legacy.headers["location"], "/")
        cookie = legacy.headers["set-cookie"]
        self.assertIn("tok=secret", cookie)
        self.assertIn("HttpOnly", cookie)
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ready", response.text)

    async def test_login_posts_the_token_without_putting_it_in_the_url(self):
        page = await self.client.get("/login?next=/stats")
        self.assertEqual(page.status_code, 200)
        self.assertIn('type="password"', page.text)
        refused = await self.client.post(
            "/login", content="token=wrong&next=%2Fstats",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(refused.status_code, 401)
        accepted = await self.client.post(
            "/login", content="token=secret&next=%2Fstats",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(accepted.status_code, 303)
        self.assertEqual(accepted.headers["location"], "/stats")
        self.assertNotIn("secret", accepted.headers["location"])

    async def test_the_login_page_follows_the_chosen_theme(self):
        """登录页在拿到 cookie 之前出图，所以它自带一份最小色板，跟着同一个选择走。

        它取不到 `/app.css`，颜色只能写在页面里。写死一档的话，固定浅色的人从地址栏
        直接进来先看见一整屏黑，登录完才跳回浅色——同一次打开出现两套配色。
        """
        page = await self.client.get("/login?next=/")
        self.assertEqual(page.status_code, 200)
        self.assertIn('<meta name="color-scheme" content="light dark">', page.text)
        self.assertIn(":root{color-scheme:light;--bg:#FFFFFF;", page.text)
        self.assertIn('@media (prefers-color-scheme:dark){html:not([data-theme="light"])', page.text)
        self.assertIn('html[data-theme="dark"]{color-scheme:dark;', page.text)
        self.assertIn("background:var(--bg);color:var(--ink)", page.text)
        # 手动选的那一档存在页面自己的 localStorage 里，首帧之前就要读出来。
        self.assertIn('localStorage.getItem("peach.settings.v1")', page.text)

    async def test_client_routes_serve_the_single_page_surface(self):
        await self.client.post(
            "/login", content="token=secret&next=%2F",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        for path in ("/item/1", "/performers/Alice", "/studios/Prestige",
                     "/creators/luckydog11", "/series/Example", "/performers",
                     "/creators", "/tags", "/stats", "/taste", "/immerse", "/trash", "/review",
                     # 前端路由写好了不等于能直接打开：SPA 路径是逐条登记的，
                     # 漏登记时源码断言照样全绿，只有真的请求一次才会露出 404。
                     "/unseen", "/watch-later", "/flagged", "/junk-files",
                     "/data-cleanup", "/duplicates", "/quality-goals", "/mix/1/2", "/parts/1/2", "/editions/1/2", "/playlists",
                     "/resource-sync",
                     "/playlists/1/1", "/follow", "/follow-manage",
                     "/follow/item/190"):
            response = await self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("Peach test", response.text)

        removed = await self.client.get("/entity/performer/Alice")
        self.assertEqual(removed.status_code, 404)

    async def test_playlist_api_saves_and_reads_a_mix_without_exposing_paths(self):
        await self.client.post(
            "/login", content="token=secret&next=%2F",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        created = await self.client.post("/api/playlist", json={
            "action": "create", "name": "测试 Mix", "asset_ids": [1],
            "source_kind": "mix", "source_seed_asset_id": 1,
        })
        self.assertEqual(created.status_code, 200)
        playlist_id = created.json()["playlist"]["id"]
        listing = (await self.client.get("/api/playlists")).json()["items"]
        self.assertEqual(listing[0]["item_count"], 1)
        detail = (await self.client.get(f"/api/playlist?id={playlist_id}")).json()
        self.assertEqual(detail["items"][0]["id"], 1)
        self.assertNotIn("path", detail["items"][0])

    async def test_pinned_frontend_vendor_assets_are_self_hosted(self):
        response = await self.client.get("/vendor/player.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "window.vendorReady=true;")
        self.assertEqual(response.headers["cache-control"], "public, max-age=31536000, immutable")
        self.assertEqual((await self.client.get("/vendor/missing.js")).status_code, 404)

    async def test_standard_range_and_head_contract(self):
        headers = {"X-Token": "secret"}
        full = await self.client.get("/stream?id=1", headers=headers)
        self.assertEqual(full.status_code, 200)
        self.assertEqual(full.content, b"0123456789")
        self.assertIn("etag", full.headers)
        self.assertIn("last-modified", full.headers)

        partial = await self.client.get(
            "/stream?id=1", headers={**headers, "Range": "bytes=2-5"}
        )
        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial.content, b"2345")
        self.assertEqual(partial.headers["content-range"], "bytes 2-5/10")

        suffix = await self.client.get(
            "/stream?id=1", headers={**headers, "Range": "bytes=-4"}
        )
        self.assertEqual(suffix.status_code, 206)
        self.assertEqual(suffix.content, b"6789")

        invalid = await self.client.get(
            "/stream?id=1", headers={**headers, "Range": "bytes=99-"}
        )
        self.assertEqual(invalid.status_code, 416)
        self.assertEqual(invalid.headers["content-range"], "bytes */10")

        head = await self.client.head("/stream?id=1", headers=headers)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.content, b"")
        self.assertEqual(head.headers["content-length"], "10")

    async def test_follow_qualities_lists_every_tier_the_source_offers(self):
        """档位数量由来源决定，不由我们写死。

        取证时那条给四档，实测线上另有五档（多一个 2160）的条目——所以解析用的是
        `video_alt_url` 加任意编号，而不是固定认三个 alt 字段。这里就用五档兜住：
        少认一档等于用户白白播低清。2160 按站点自己的写法叫 4K，不叫 2160p。
        """
        connection = sqlite3.connect(self.db)
        connection.executescript((ROOT / "migrations" / "0018_online_follow.sql").read_text(
            encoding="utf-8"))
        connection.execute(
            "INSERT INTO follow_source(id,provider,ref,label,url,semantics,created_at,updated_at)"
            " VALUES(2,'rule34video','r34/1','Creator','https://rule34video.com/u','work','x','x')"
        )
        connection.execute(
            "INSERT INTO follow_item(id,source_id,external_id,title,url,media_url,release_key,"
            "first_seen_at,last_seen_at) VALUES(9,2,'9','Remote',"
            "'https://rule34video.com/video/9/x/','https://rule34video.com/get_file/9.mp4/',"
            "'remote','x','x')"
        )
        connection.commit()
        connection.close()

        page = ("<script>"
                "video_url: 'https://rule34video.com/get_file/9_360.mp4/?v=t0';"
                "video_alt_url: 'https://rule34video.com/get_file/9_480p.mp4/?v=t1';"
                "video_alt_url2: 'https://rule34video.com/get_file/9_720p.mp4/?v=t2';"
                "video_alt_url3: 'https://rule34video.com/get_file/9_1080p.mp4/?v=t3';"
                "video_alt_url4: 'https://rule34video.com/get_file/9_2160p.mp4/?v=t4';"
                "</script>").encode("utf-8")

        def upstream(request):
            return httpx.Response(200, stream=httpx.ByteStream(page), request=request,
                                  headers={"content-type": "text/html"})

        original = self.app.state.http_transport.client
        fake = httpx.Client(transport=httpx.MockTransport(upstream), follow_redirects=True)
        self.app.state.http_transport.client = fake
        try:
            response = await self.client.get("/follow-qualities?id=9&t=secret")
        finally:
            self.app.state.http_transport.client = original
            fake.close()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["qualities"], [
            {"height": 2160, "label": "4K"},
            {"height": 1080, "label": "1080p"},
            {"height": 720, "label": "720p"},
            {"height": 480, "label": "480p"},
            {"height": 360, "label": "360p"},
        ])

    async def test_follow_stream_proxies_range_without_exposing_the_upstream_url(self):
        connection = sqlite3.connect(self.db)
        connection.executescript((ROOT / "migrations" / "0018_online_follow.sql").read_text(
            encoding="utf-8"))
        connection.execute(
            "INSERT INTO follow_source(id,provider,ref,label,url,semantics,created_at,updated_at)"
            " VALUES(1,'kemono','fanbox/1','Creator','https://kemono.cr/u','work','x','x')"
        )
        connection.execute(
            "INSERT INTO follow_item(id,source_id,external_id,title,url,media_url,release_key,"
            "first_seen_at,last_seen_at) VALUES(7,1,'7','Remote','https://kemono.cr/p/7',"
            "'https://img.kemono.cr/data/7.mp4','remote','x','x')"
        )
        connection.commit()
        connection.close()

        def upstream(request):
            self.assertEqual(request.headers.get("range"), "bytes=2-5")
            return httpx.Response(
                206, stream=httpx.ByteStream(b"2345"), request=request,
                headers={"content-type": "video/mp4", "content-range": "bytes 2-5/10",
                         "accept-ranges": "bytes", "content-length": "4"},
            )

        original = self.app.state.http_transport.client
        fake = httpx.Client(transport=httpx.MockTransport(upstream), follow_redirects=True)
        self.app.state.http_transport.client = fake
        try:
            denied = await self.client.get("/follow-stream?id=7")
            response = await self.client.get(
                "/follow-stream?id=7&t=secret", headers={"Range": "bytes=2-5"})
        finally:
            self.app.state.http_transport.client = original
            fake.close()
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"2345")
        self.assertEqual(response.headers["content-range"], "bytes 2-5/10")
        self.assertNotIn("img.kemono.cr", response.text)

    async def test_follow_stream_only_offers_a_download_when_asked(self):
        """下载是显式动作，不是播放的副作用。

        文件名从条目标题来，不回传上游地址——上游主机名和签名同样不该外露，
        这和 `/follow-stream` 整体的边界是同一条。
        """
        connection = sqlite3.connect(self.db)
        connection.executescript((ROOT / "migrations" / "0018_online_follow.sql").read_text(
            encoding="utf-8"))
        connection.execute(
            "INSERT INTO follow_source(id,provider,ref,label,url,semantics,created_at,updated_at)"
            " VALUES(1,'kemono','fanbox/1','Creator','https://kemono.cr/u','work','x','x')"
        )
        connection.execute(
            "INSERT INTO follow_item(id,source_id,external_id,title,url,media_url,release_key,"
            "first_seen_at,last_seen_at) VALUES(8,1,'8','2B Camp [4K]','https://kemono.cr/p/8',"
            "'https://img.kemono.cr/data/8.webm','remote','x','x')"
        )
        connection.commit()
        connection.close()

        def upstream(request):
            return httpx.Response(
                200, stream=httpx.ByteStream(b"0123456789"), request=request,
                headers={"content-type": "video/webm", "content-length": "10"},
            )

        original = self.app.state.http_transport.client
        fake = httpx.Client(transport=httpx.MockTransport(upstream), follow_redirects=True)
        self.app.state.http_transport.client = fake
        try:
            played = await self.client.get("/follow-stream?id=8&t=secret")
            saved = await self.client.get("/follow-stream?id=8&t=secret&download=1")
        finally:
            self.app.state.http_transport.client = original
            fake.close()
        self.assertNotIn("content-disposition", played.headers)
        disposition = saved.headers["content-disposition"]
        self.assertIn("attachment;", disposition)
        self.assertIn("2B Camp [4K].webm", disposition)
        self.assertNotIn("img.kemono.cr", disposition)

    async def test_follow_cover_serves_cached_frame_and_degrades_to_a_placeholder(self):
        connection = sqlite3.connect(self.db)
        connection.executescript((ROOT / "migrations" / "0018_online_follow.sql").read_text(
            encoding="utf-8"))
        connection.execute(
            "INSERT INTO follow_source(id,provider,ref,label,url,semantics,created_at,updated_at)"
            " VALUES(1,'rule34paheal','artist','Artist','https://rule34.paheal.net/u',"
            "'work','x','x')"
        )
        connection.execute(
            "INSERT INTO follow_item(id,source_id,external_id,title,url,media_url,thumb_url,"
            "release_key,metadata_json,first_seen_at,last_seen_at) VALUES(7,1,'7','Remote',"
            "'https://rule34.paheal.net/post/view/7',"
            "'https://r34i.paheal-cdn.net/ab/cd/video',"
            "'https://r34t.paheal.net/ab/cd/video','remote',"
            "'{\"media_kind\":\"video\"}','x','x')"
        )
        connection.commit()
        connection.close()
        frame = self.root / "clear.jpg"
        frame.write_bytes(b"clear-jpeg")

        class Cover:
            def __init__(self):
                self.fail = False

            def cover(self, _item):
                if self.fail:
                    from peach.follow_covers import FollowCoverUnavailable
                    raise FollowCoverUnavailable("test")
                return frame

        cover = Cover()
        self.app.state.follow_cover_service = cover
        denied = await self.client.get("/follow-cover?id=7")
        response = await self.client.get("/follow-cover?id=7&t=secret")
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"clear-jpeg")
        self.assertEqual(response.headers["cache-control"],
                         "private, no-cache")
        cover.fail = True
        fallback = await self.client.get(
            "/follow-cover?id=7&t=secret", follow_redirects=False)
        # 生成失败回占位图，不再 302 到上游缩略图：这个端点存在的理由就是
        # 不把上游主机和地址交回浏览器。
        self.assertEqual(fallback.status_code, 404)
        self.assertNotIn("location", fallback.headers)
        self.assertNotIn("paheal", fallback.text)
        self.assertEqual(fallback.headers["content-type"],
                         PLACEHOLDER_CONTENT_TYPE)

    async def test_stream_session_cancel_is_authenticated_and_tombstoned(self):
        denied = await self.client.post("/api/stream-cancel?session=detail-1")
        self.assertEqual(denied.status_code, 401)

        cancelled = await self.client.post(
            "/api/stream-cancel?t=secret&session=detail-1"
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json(), {"ok": True, "cancelled": 0})

        stale = await self.client.get(
            "/stream?id=1&session=detail-1", headers={"X-Token": "secret"}
        )
        self.assertEqual(stale.status_code, 410)

    async def test_remote_session_preserves_open_ended_range(self):
        con = sqlite3.connect(self.db)
        con.execute("UPDATE asset SET location='115' WHERE id=1")
        con.commit()
        con.close()
        response = await self.client.get(
            "/stream?id=1&session=remote-standard",
            headers={"X-Token": "secret", "Range": "bytes=0-"},
        )
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"0123456789")
        self.assertEqual(response.headers["content-range"], "bytes 0-9/10")
        self.assertEqual(response.headers["content-length"], "10")

    async def test_remote_stream_plan_and_hls_playlist_are_segmented(self):
        con = sqlite3.connect(self.db)
        con.execute("UPDATE asset SET location='115', duration=13.5, path=? WHERE id=1",
                    (str(self.hls_file),))
        con.commit()
        con.close()

        # 默认计划是标准 Range：HLS 的 TS 分片装不下浏览器能解的 HEVC，见 ADR-0016。
        default_plan = await self.client.get(
            "/api/stream-plan?id=1&session=hls-test&t=secret",
        )
        self.assertEqual(default_plan.status_code, 200)
        self.assertEqual(default_plan.json()["protocol"], "range")
        self.assertIn("/stream?id=1", default_plan.json()["src"])

        plan = await self.client.get(
            "/api/stream-plan?id=1&session=hls-test&mode=hls&t=secret",
        )
        self.assertEqual(plan.status_code, 200)
        self.assertEqual(plan.json()["protocol"], "hls")
        self.assertEqual(plan.json()["segment_seconds"], 6)
        self.assertIn("/stream/hls/1/index.m3u8?session=hls-test", plan.json()["src"])

        playlist = await self.client.get(
            "/stream/hls/1/index.m3u8?session=hls-test&t=secret",
        )
        self.assertEqual(playlist.status_code, 200)
        self.assertEqual(playlist.headers["content-type"], "application/vnd.apple.mpegurl")
        self.assertEqual(playlist.text.count("#EXTINF:"), 3)

    async def test_incompatible_video_uses_time_slices_without_whole_movie_conversion(self):
        con = sqlite3.connect(self.db)
        con.execute("UPDATE asset SET duration=7632.28 WHERE id=1")
        con.commit()
        con.close()
        with patch.object(self.app.state.transcode_service, 'requires_conversion', return_value=True), \
                patch.object(self.app.state.transcode_service, 'browser_path',
                             side_effect=AssertionError('whole movie conversion')):
            response = await self.client.get('/api/stream-plan?id=1&session=s&t=secret')
            self.assertEqual(response.json()['protocol'], 'hls')
            playlist = await self.client.get('/stream/hls/1/index.m3u8?session=s&t=secret')
            self.assertEqual(playlist.status_code, 200)
            self.assertIn('#EXTINF:0.280', playlist.text)

    async def test_hls_segment_is_generated_for_one_requested_time_slice(self):
        con = sqlite3.connect(self.db)
        con.execute("UPDATE asset SET location='115', duration=13.5, path=? WHERE id=1",
                    (str(self.hls_file),))
        con.commit()
        con.close()
        segment = self.root / "segment.ts"
        segment.write_bytes(b"one segment")

        async def generate(source, start, duration, *, asset_id, index, session, registry):
            # 关键帧每秒一个，6 秒目标 → 第 1 段从 6.0 开始，长 6.0。
            self.assertEqual((start, duration), (6.0, 6.0))
            self.assertEqual((asset_id, index, session), (1, 1, "hls-test"))
            return segment

        with patch.object(self.app.state.hls_service, "generate", new=generate):
            with patch.object(
                self.app.state.hls_plan_executor,
                "submit",
                wraps=self.app.state.hls_plan_executor.submit,
            ) as submit:
                response = await self.client.get(
                    "/stream/hls/1/1.ts?session=hls-test&t=secret",
                )
        submit.assert_called_once()
        self.assertEqual(self.app.state.hls_plan_executor._max_workers, 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"one segment")
        self.assertEqual(response.headers["content-type"], "video/mp2t")
        self.assertTrue(segment.exists(), "片段要留在缓存里，重复请求不该再跑一次 FFmpeg")

    async def test_transcoded_stream_has_browser_mime_and_marker(self):
        avi = self.media_root / "two.avi"
        avi.write_bytes(b"avi-source")
        cached = self.transcode_root / "two.mp4"
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"mp4-cache")
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT INTO asset(id,location,path,name,medium,size,first_seen) "
            "VALUES(2,'local',?,'two.avi','video',10,'2026-08-15')",
            (str(avi),),
        )
        con.commit()
        con.close()

        with patch.object(
            self.app.state.transcode_service, "browser_path",
            return_value=(cached, True),
        ):
            response = await self.client.get(
                "/stream?id=2", headers={"X-Token": "secret", "Range": "bytes=0-2"},
            )
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"mp4")
        self.assertEqual(response.headers["content-type"], "video/mp4")
        self.assertEqual(response.headers["x-peach-transcoded"], "1")

    async def test_cached_visual_assets_and_thumbnail(self):
        headers = {"X-Token": "secret"}
        poster = await self.client.get("/poster?id=1&c=4", headers=headers)
        avatar = await self.client.get("/avatar?id=1", headers=headers)
        logo = await self.client.get("/logo?studio=Studio_A", headers=headers)
        thumb = await self.client.get("/thumb?id=1", headers=headers)
        self.assertEqual((poster.content, avatar.content, logo.content, thumb.content),
                         (b"poster", b"avatar", b"logo", b"snapshot"))
        self.assertEqual(logo.headers["content-type"], "image/png")
        self.assertEqual(logo.headers["cache-control"], "public, no-cache")
        self.assertEqual(poster.headers["cache-control"],
                         "private, no-cache")
        fresh = await self.client.get("/poster?id=1&c=4", headers={
            **headers, "If-None-Match": poster.headers["etag"],
        })
        self.assertEqual(fresh.status_code, 304)
        self.assertEqual(fresh.content, b"")
        denied = await self.client.get("/poster?id=1&c=4", headers={
            "If-None-Match": poster.headers["etag"],
        })
        self.assertEqual(denied.status_code, 401)

    async def test_endcard_frame_is_authenticated_and_confined_to_evidence_root(self):
        denied = await self.client.get(
            "/endcard-frame?id=1&name=tail-000098000.png"
        )
        self.assertEqual(denied.status_code, 401)
        response = await self.client.get(
            "/endcard-frame?id=1&name=tail-000098000.png",
            headers={"X-Token": "secret"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"endcard")
        self.assertEqual(response.headers["content-type"], "image/png")
        traversal = await self.client.get(
            "/endcard-frame?id=1&name=../index.html",
            headers={"X-Token": "secret"},
        )
        self.assertEqual(traversal.status_code, 400)

    def _seed_photo(self):
        """一张真实 JPEG：缩略图端点要真的解码，假字节测不出这条路径。"""
        from PIL import Image

        source = self.media_root / "shoot" / "001.jpg"
        source.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (1600, 2400), (200, 120, 90)).save(source, "JPEG")
        source2 = self.media_root / "shoot-2" / "002.jpg"
        source2.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (2400, 1600), (90, 120, 200)).save(source2, "JPEG")
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT INTO asset(id,location,path,name,medium,size,first_seen) "
            "VALUES(9,'pikpak',?,'001.jpg','image',?,'2026-08-24')",
            (str(source), source.stat().st_size),
        )
        con.execute(
            "INSERT INTO asset(id,location,path,name,medium,size,first_seen) "
            "VALUES(10,'pikpak',?,'002.jpg','image',?,'2026-08-24')",
            (str(source2), source2.stat().st_size),
        )
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(9,'creator','Alice','alice')")
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(9,9,'creator','legacy:asset',1.0)")
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(10,9,'creator','legacy:asset',1.0)")
        con.commit()
        con.close()
        return source

    async def test_photo_sets_expose_directories_without_leaking_paths(self):
        self._seed_photo()
        headers = {"X-Token": "secret"}
        listing = await self.client.get(
            "/api/photos?kind=creator&name=Alice&limit=1", headers=headers)
        self.assertEqual(listing.status_code, 200)
        payload = listing.json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["sets"][0]["id"], 9)
        self.assertEqual(payload["sets"][0]["title"], "shoot")
        self.assertEqual([item["id"] for item in payload["items"]], [9])
        self.assertEqual(payload["items"][0]["location"], "pikpak")
        self.assertTrue(payload["has_more"])
        self.assertNotIn(str(self.media_root), json.dumps(payload),
                         "只发目录名和图集 id，不发真实路径")
        next_page = await self.client.get(
            "/api/photos?kind=creator&name=Alice&limit=1&offset=1", headers=headers)
        self.assertEqual([item["id"] for item in next_page.json()["items"]], [10])
        self.assertFalse(next_page.json()["has_more"])
        detail = await self.client.get("/api/photo-set?id=9", headers=headers)
        self.assertEqual([item["id"] for item in detail.json()["items"]], [9])
        self.assertEqual(detail.json()["items"][0]["location"], "pikpak")
        self.assertNotIn(str(self.media_root), json.dumps(detail.json()),
                         "图片详情也只发安全元数据，真实路径留在服务端")

    async def test_photo_detail_reveal_resolves_the_asset_id_on_the_server(self):
        source = self._seed_photo()
        headers = {"X-Token": "secret"}
        with patch("peach.routes_api.reveal_path", return_value=True) as reveal:
            response = await self.client.post(
                "/api/reveal", headers=headers,
                json={"id": 9, "path": "C:/client-must-not-control-this"},
            )
        self.assertEqual(response.status_code, 200)
        reveal.assert_called_once_with(source)

    async def test_photo_thumbnail_is_generated_once_and_cached(self):
        source = self._seed_photo()
        headers = {"X-Token": "secret"}
        first = await self.client.get("/photo-thumb?id=9", headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers["content-type"], "image/jpeg")
        cached = self.photo_root / "9.jpg"
        self.assertTrue(cached.is_file(), "缩略图要落盘，计费来源不能每次回源")
        self.assertLess(cached.stat().st_size, source.stat().st_size)
        stamp = cached.stat().st_mtime_ns
        again = await self.client.get("/photo-thumb?id=9", headers=headers)
        self.assertEqual(again.status_code, 200)
        self.assertEqual(cached.stat().st_mtime_ns, stamp, "第二次只读缓存")
        full = await self.client.get("/photo?id=9", headers=headers)
        self.assertEqual(full.content, source.read_bytes())

    async def test_photo_endpoints_require_the_token(self):
        self._seed_photo()
        for path in ("/photo?id=9", "/photo-thumb?id=9"):
            response = await self.client.get(path)
            self.assertEqual(response.status_code, 401, path)


@unittest.skipUnless(HAS_DEPS, "fastapi/httpx not installed")
class UnconfiguredMachineTests(unittest.IsolatedAsyncioTestCase):
    """还没跑过 `peach init` 的机器：服务照常起，页面告诉人下一步做什么。

    「未配置」是显式状态，不是崩溃：数据目录不存在、数据库不存在、什么来源都没挂，
    这些都不该让 `serve` 起不来——起不来的服务连提示都没法给。
    """

    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        missing = Path(self.tmp.name).resolve() / "nothing-here"
        self.settings = PeachSettings(
            configured=False,
            db_path=missing / "database" / "ledger.db",
            page_path=missing / "web" / "index.html",
            vendor_path=missing / "web" / "vendor",
            allowed_media_roots=(),
            snapshot_root=missing / "snapshots",
            legacy_snapshot_roots=(),
            poster_root=missing / "posters", avatar_root=missing / "avatars",
            logo_root=missing / "logos", cover_root=missing / "covers",
            photo_root=missing / "photos", stream_root=missing / "stream",
            ffmpeg_root=missing / "ffmpeg", transcode_root=missing / "transcodes",
            candidate_root=missing, review_mirror_cache=missing / "review.json",
            taste_history_store=missing / "history.sqlite",
            taste_history_import_root=missing / "imports",
            taste_history_output_root=missing / "taste",
            taste_history_manifest=missing / "manifest.json",
            follow_state_root=missing / "state",
        )
        self.app = create_app(self.settings)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://test")
        self.addAsyncCleanup(self.client.aclose)

    async def test_health_reports_the_unconfigured_state_instead_of_failing(self):
        response = await self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["configured"])
        self.assertEqual(body["db"], "missing")

    async def test_the_page_serves_the_first_run_form(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn('<form method="post" action="/setup"', response.text)

    async def test_deep_links_land_on_the_same_form(self):
        # 前端路由全部落到 `index`，未配置时不该只有首页能看。
        response = await self.client.get("/tags")
        self.assertEqual(response.status_code, 200)
        self.assertIn('<form method="post" action="/setup"', response.text)

    async def test_a_configured_machine_still_reports_true(self):
        app = create_app(PeachSettings(configured=True, db_path=self.settings.db_path))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        ) as client:
            self.assertTrue((await client.get("/healthz")).json()["configured"])


if __name__ == "__main__":
    unittest.main()
