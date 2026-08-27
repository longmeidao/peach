import csv
import importlib.util
import json
import sqlite3
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach import __version__


ROOT = Path(__file__).resolve().parents[1]


HAS_DEPS = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))
if HAS_DEPS:
    import httpx
    from peach.api import create_app
    from peach.config import PeachSettings


BASE_SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY, location TEXT NOT NULL, path TEXT NOT NULL, name TEXT,
  medium TEXT, size INTEGER, creator TEXT, studio TEXT, series TEXT, code TEXT, release_date TEXT,
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
        self.transcode_root = self.root / "transcodes"
        self.photo_root = self.root / "photo-thumbs"
        self.vendor_root = self.root / "vendor"
        # 复核候选必须来自临时目录：早先版本直接读真实的 R:\peach-data\generated。
        self.candidate_root = self.root / "generated"
        self.candidate_root.mkdir()
        self.endcard_frame = (
            self.candidate_root / "endcard-evidence" / "1" / "tail-000098000.png"
        )
        self.endcard_frame.parent.mkdir(parents=True)
        self.endcard_frame.write_bytes(b"endcard")
        for path in (self.media_root, self.snapshot_root, self.poster_root,
                     self.avatar_root, self.logo_root, self.vendor_root):
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
        con = sqlite3.connect(self.db)
        con.executescript(BASE_SCHEMA)
        con.execute(
            """INSERT INTO asset(id,location,path,name,medium,size,creator,studio,duration,
                                  width,height,ctx_orient,snapshot_path,first_seen)
               VALUES(1,'local',?,'one.mp4','video',100,
                      'Alice','Studio A',100,1920,1080,'横屏',?,'2026-08-14')""",
            (str(self.media_file), str(self.legacy_snapshot_file)),
        )
        con.execute("INSERT INTO asset_tag(asset_id,tag,source) VALUES(1,'Tag A','test')")
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(1,'tag','Tag A','tag a')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,1,'tag','test',1.0)"
        )
        con.commit()
        con.close()
        self.settings = PeachSettings(
            db_path=self.db, token="secret", page_path=self.page, vendor_path=self.vendor_root,
            allowed_media_roots=(self.media_root,), snapshot_root=self.snapshot_root,
            legacy_snapshot_roots=(self.legacy_snapshot_root,),
            poster_root=self.poster_root, avatar_root=self.avatar_root, logo_root=self.logo_root,
            ffmpeg_root=self.root / "ffmpeg", transcode_root=self.transcode_root,
            candidate_root=self.candidate_root, photo_root=self.photo_root,
        )
        self.app = create_app(self.settings)
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

    async def test_peach_logo_is_served_as_png(self):
        response = await self.client.get("/peach-logo.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))

    async def test_follow_avatar_redirects_only_after_the_official_resolver(self):
        denied = await self.client.get("/follow-avatar?service=fanbox&id=30917150")
        self.assertEqual(denied.status_code, 401)
        with patch("peach.api.resolve_official_avatar",
                   return_value="https://pixiv.pximg.net/icon.jpeg") as resolver:
            response = await self.client.get(
                "/follow-avatar?t=secret&service=fanbox&id=30917150")
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"],
                         "https://pixiv.pximg.net/icon.jpeg")
        resolver.assert_called_once_with("fanbox", "30917150")

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

    async def test_search_history_is_shared_through_the_api(self):
        saved = await self.client.post("/api/search-history?t=secret", json={"query": "ABW"})
        self.assertEqual(saved.status_code, 200)
        history = await self.client.get("/api/search-history?t=secret")
        self.assertEqual(history.json()["items"], ["ABW"])
        removed = await self.client.post("/api/search-history?t=secret", json={"operation": "remove", "query": "ABW"})
        self.assertEqual(removed.status_code, 200)

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

    async def test_unexpected_contract_errors_are_logged_but_not_exposed(self):
        with patch(
            "peach.api.web_contract.dispatch_api_get",
            side_effect=RuntimeError("private C:\\ledger.db detail"),
        ):
            with self.assertLogs("peach.api", level="ERROR") as captured:
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

    async def test_client_routes_serve_the_single_page_surface(self):
        await self.client.post(
            "/login", content="token=secret&next=%2F",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        for path in ("/item/1", "/performers/Alice", "/studios/Prestige",
                     "/creators/luckydog11", "/series/Example", "/performers",
                     "/creators", "/tags", "/stats", "/immerse", "/trash", "/review",
                     # 前端路由写好了不等于能直接打开：SPA 路径是逐条登记的，
                     # 漏登记时源码断言照样全绿，只有真的请求一次才会露出 404。
                     "/unseen", "/watch-later", "/flagged",
                     "/duplicates", "/quality-goals", "/mix/1/2", "/playlists",
                     "/playlists/1/1"):
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
        self.assertEqual(invalid.headers["content-range"], "*/10")

        head = await self.client.head("/stream?id=1", headers=headers)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.content, b"")
        self.assertEqual(head.headers["content-length"], "10")

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
        self.assertEqual(poster.headers["cache-control"], "public, max-age=86400")

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
        con = sqlite3.connect(self.db)
        con.execute(
            "INSERT INTO asset(id,location,path,name,medium,size,first_seen) "
            "VALUES(9,'pikpak',?,'001.jpg','image',?,'2026-08-24')",
            (str(source), source.stat().st_size),
        )
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(9,'creator','Alice','alice')")
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(9,9,'creator','legacy:asset',1.0)")
        con.commit()
        con.close()
        return source

    async def test_photo_sets_expose_directories_without_leaking_paths(self):
        self._seed_photo()
        headers = {"X-Token": "secret"}
        listing = await self.client.get("/api/photos?kind=creator&name=Alice", headers=headers)
        self.assertEqual(listing.status_code, 200)
        payload = listing.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["sets"][0]["id"], 9)
        self.assertEqual(payload["sets"][0]["title"], "shoot")
        self.assertNotIn(str(self.media_root), json.dumps(payload),
                         "只发目录名和图集 id，不发真实路径")
        detail = await self.client.get("/api/photo-set?id=9", headers=headers)
        self.assertEqual([item["id"] for item in detail.json()["items"]], [9])

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


if __name__ == "__main__":
    unittest.main()
