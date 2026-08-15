import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach import __version__


HAS_DEPS = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))
if HAS_DEPS:
    import httpx
    from peach.api import create_app
    from peach.config import PeachSettings


BASE_SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY, location TEXT NOT NULL, path TEXT NOT NULL, name TEXT,
  medium TEXT, size INTEGER, creator TEXT, studio TEXT, series TEXT, code TEXT,
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
CREATE TABLE asset_entity(
  asset_id INTEGER,entity_id INTEGER,role TEXT,source TEXT,confidence REAL,
  metadata_json TEXT DEFAULT '{}',first_seen_at TEXT,last_seen_at TEXT,
  UNIQUE(asset_id,entity_id,role,source));
CREATE TABLE watch_queue(profile_id TEXT,asset_id INTEGER,added_at TEXT,source TEXT,
  PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_preference(profile_id TEXT,asset_id INTEGER,liked INTEGER,reason TEXT,
  source TEXT,updated_at TEXT,PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_tag_preference(profile_id TEXT,asset_id INTEGER,normalized_tag TEXT,
  hidden INTEGER,updated_at TEXT,PRIMARY KEY(profile_id,asset_id,normalized_tag));
CREATE TABLE media_binding(
  asset_id INTEGER,backend TEXT,external_id TEXT,metadata_json TEXT,last_synced_at TEXT,
  PRIMARY KEY(asset_id,backend),UNIQUE(backend,external_id));
"""


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
        for path in (self.media_root, self.snapshot_root, self.poster_root,
                     self.avatar_root, self.logo_root):
            path.mkdir()
        self.media_file = self.media_root / "one.mp4"
        self.media_file.write_bytes(b"0123456789")
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
                                  width,height,snapshot_path,first_seen)
               VALUES(1,'local',?,'one.mp4','video',100,
                      'Alice','Studio A',100,1920,1080,?,'2026-08-14')""",
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
        self.app = create_app(PeachSettings(
            db_path=self.db, token="secret", page_path=self.page,
            allowed_media_roots=(self.media_root,), snapshot_root=self.snapshot_root,
            legacy_snapshot_roots=(self.legacy_snapshot_root,),
            poster_root=self.poster_root, avatar_root=self.avatar_root, logo_root=self.logo_root,
            ffmpeg_root=self.root / "ffmpeg", transcode_root=self.transcode_root,
        ))
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
        self.assertEqual(denied.status_code, 401)
        response = await self.client.get("/?t=secret")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ready", response.text)
        cookie = response.headers["set-cookie"]
        self.assertIn("tok=secret", cookie)
        self.assertIn("HttpOnly", cookie)

    async def test_client_routes_serve_the_single_page_surface(self):
        await self.client.get("/?t=secret")
        for path in ("/item/1", "/performers/Alice", "/studios/Prestige",
                     "/creators/luckydog11", "/series/Example", "/performers",
                     "/creators", "/tags", "/stats", "/immerse"):
            response = await self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("Peach test", response.text)

        removed = await self.client.get("/entity/performer/Alice")
        self.assertEqual(removed.status_code, 404)

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


if __name__ == "__main__":
    unittest.main()
