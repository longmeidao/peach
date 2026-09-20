"""新导入演员的资料页别名与官方头像补全。"""
from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from peach.http import HttpResponse
from peach.metadata_performer_profiles import enrich_performer_profiles
from support.ledger import fresh_ledger


def picture() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (125, 125), "#795548").save(output, format="JPEG")
    return output.getvalue()


class ImportedPerformerProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.db = fresh_ledger(self.root)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,code) "
                "VALUES(1,'local','R:\\\\ABW-358.mp4','ABW-358.mp4','video','ABW-358')")
            connection.execute(
                "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                "VALUES(7,'performer','涼森れむ','涼森れむ','t','t')")
            connection.execute(
                "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                "VALUES(1,7,'performer','javinizer:local_nfo:performer',0.9)")
            connection.execute(
                "INSERT INTO entity_external_ref(entity_id,provider,external_kind,external_id) "
                "VALUES(7,'r18dev','performer','1051912')")
            connection.execute(
                "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                "VALUES('metadata_fields','asset:1:performers','approved',?, 't')",
                (json.dumps({'candidate_key': 'profile'}),))

    @staticmethod
    def group(url="https://pics.dmm.co.jp/mono/actjpgs/suzumori_remu.jpg"):
        return {
            "asset_id": 1, "item_key": "asset:1:performers", "field": "performers",
            "candidates_json": json.dumps([{"candidate_key": "profile",
                "source": "local_nfo", "value": [{
                "name": "涼森れむ", "external_id": "1051912",
                "aliases": ["すずもりれむ", "Remu Suzumori"],
                "thumb_url": url, "profile_source": "r18dev",
            }]}], ensure_ascii=False),
        }

    def test_exact_profile_adds_aliases_and_installs_the_official_avatar(self):
        transport = Mock(return_value=HttpResponse(
            200, {"content-type": "image/jpeg"}, picture(),
            "https://pics.dmm.co.jp/mono/actjpgs/suzumori_remu.jpg"))
        with patch("peach.avatar_provider.FaceProbe") as face:
            face.return_value.return_value = None
            result = enrich_performer_profiles(
                self.db, [self.group()], self.root / "avatars", self.root / "providers",
                transport_factory=lambda: transport)
        self.assertEqual(result, {"aliases": 2, "avatars": 1, "conflicts": 0, "failed": 0})
        with closing(sqlite3.connect(self.db)) as connection:
            aliases = {row[0] for row in connection.execute(
                "SELECT alias FROM entity_alias WHERE entity_id=7")}
        self.assertEqual(aliases, {"すずもりれむ", "Remu Suzumori"})
        self.assertTrue((self.root / "avatars" / "performer-7.img").is_file())
        transport.assert_called_once()

    def test_tampered_avatar_url_is_never_requested_but_aliases_still_land(self):
        transport = Mock()
        result = enrich_performer_profiles(
            self.db, [self.group("http://127.0.0.1/admin")],
            self.root / "avatars", self.root / "providers",
            transport_factory=lambda: transport)
        self.assertEqual(result["aliases"], 2)
        self.assertEqual(result["avatars"], 0)
        transport.assert_not_called()

    def test_candidate_still_waiting_for_review_cannot_enrich_the_entity(self):
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute(
                "DELETE FROM review_decision WHERE item_key='asset:1:performers'")
        transport = Mock()
        result = enrich_performer_profiles(
            self.db, [self.group()], self.root / "avatars", self.root / "providers",
            transport_factory=lambda: transport)
        self.assertEqual(result, {"aliases": 0, "avatars": 0, "conflicts": 0, "failed": 0})
        transport.assert_not_called()


if __name__ == "__main__":
    unittest.main()
