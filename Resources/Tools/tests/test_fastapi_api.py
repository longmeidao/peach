import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


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
  o_count INTEGER, watch_ratio REAL, snapshot_path TEXT, first_seen TEXT,
  feedback TEXT, disposal TEXT, leave_ratio REAL, play_seconds REAL,
  feedback_at REAL, seek_count INTEGER, max_reached REAL,
  UNIQUE(location,path));
CREATE TABLE asset_tag(asset_id INTEGER,tag TEXT,confidence REAL DEFAULT 1.0,source TEXT,
                       UNIQUE(asset_id,tag));
"""


@unittest.skipUnless(HAS_DEPS, "FastAPI/httpx 尚未安装")
class FastApiContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        con = sqlite3.connect(self.db)
        con.executescript(BASE_SCHEMA)
        con.execute(
            """INSERT INTO asset(id,location,path,name,medium,size,creator,studio,duration,
                                  width,height,first_seen)
               VALUES(1,'local','R:\\Media\\one.mp4','one.mp4','video',100,
                      'Alice','Studio A',100,1920,1080,'2026-08-14')"""
        )
        con.execute("INSERT INTO asset_tag(asset_id,tag,source) VALUES(1,'Tag A','test')")
        con.commit()
        con.close()
        app = create_app(PeachSettings(db_path=self.db, token="secret"))
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.tmp.cleanup()

    async def test_health_is_side_effect_free(self):
        response = await self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "compat")

    async def test_auth_and_items_contract(self):
        denied = await self.client.get("/api/items")
        self.assertEqual(denied.status_code, 401)
        response = await self.client.get("/api/items?t=secret&loc=local&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertNotIn("path", data["items"][0])
        self.assertEqual(response.headers["cache-control"], "no-store")

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


if __name__ == "__main__":
    unittest.main()
