"""复核队列的隔离测试。

随 `web_review` 从 `web_contract` 一同拆出。patch 目标跟着代码走：这批用例
patch `read_candidates` 与 `_review_rows`，代码搬走后若仍打在 `web_contract` 上，
patch 会静默失效——不报错，一路跑到断言才炸。
"""
import csv
import json
import os
import re
import pathlib
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from peach import metadata_policy as rm_policy
from peach import review_csv as rm_candidates
from peach import web_contract as rm_web
from peach import web_review as rm_review
from peach.genre_taxonomy import map_genres
from peach.metadata_auto_apply import _fc2_seller_as_label, auto_apply_metadata
from peach.field_owners import (
    EXPECTED_REVISION_FIELD,
    USER_MANUAL,
    RevisionConflict,
    owner_of,
    write_owned_fields,
)

from support.ledger import fresh_ledger


class ReviewQueueTests(unittest.TestCase):
    """复核队列：候选来源、稳定主键、批准的权威值与写入边界。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.candidates = root / "generated"
        self.candidates.mkdir()
        self.logo_root = root / "logos"
        self.logo_root.mkdir()
        self.avatar_root = root / "avatars"
        self.avatar_root.mkdir()
        self.db_path = str(fresh_ledger(root))
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(1,'creator','ukiru','ukiru','2026-01-01','2026-01-01')")
        for asset_id in (1, 2, 3):
            con.execute("INSERT INTO asset(id,location,path,name,medium,snapshot_path) "
                        "VALUES(?,'local',?,?,'video','s.jpg')",
                        (asset_id, f"/x/{asset_id}.mp4", f"{asset_id}.mp4"))
            con.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                        "VALUES(?,1,'creator','board',1.0)", (asset_id,))
        con.commit(); con.close()
        self.contract = rm_web.WebContract(
            Path(self.db_path), candidate_root=self.candidates, logo_root=self.logo_root,
            avatar_root=self.avatar_root,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_candidates(self, name, rows):
        path = self.candidates / name
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["board", "creator", "tags", "status"])
            writer.writeheader(); writer.writerows(rows)
        return path

    def write_metadata_candidates(self, rows):
        path = self.candidates / "metadata-field-candidates-20260822.csv"
        fields = ["item_key", "code", "query", "asset_id", "asset_path", "field",
                  "field_label", "current_value", "candidates_json", "source_count",
                  "source_profile", "status", "size_gb", "videos", "fetched_at"]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        return path

    def write_logo_candidates(self, rows):
        path = self.candidates / "studio-logo-candidate-20260818.csv"
        fields = ["studio", "handle", "platform", "resolved_url", "saved", "accepted"]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        return path

    def decide(self, category, item_key, status):
        return rm_review.w_review_decision(
            self.contract,
            {"category": category, "item_key": item_key, "status": status})

    def queue_keys(self, category):
        rows, _source, _skipped = rm_review._review_rows(self.contract, category)
        return [row["item_key"] for row in rows]

    def queue_row(self, category, item_key):
        rows, _source, _skipped = rm_review._review_rows(self.contract, category)
        return next(row for row in rows if row["item_key"] == item_key)

    def write_metadata_rows(self, rows):
        import json as _json
        payload = []
        for item in rows:
            code = item.get("code", item["item_key"])
            source = item.get("source", "r18dev")
            payload.append({
                "item_key": item["item_key"], "code": code,
                "query": code, "field": item["field"],
                "field_label": item["field"], "current_value": item["current"],
                "candidates_json": _json.dumps([
                    self._candidate(item, i, source, value)
                    for i, value in enumerate(item["candidates"])], ensure_ascii=False),
                "source_count": "1", "source_profile": item.get("profile", ""),
                "status": "candidate", "size_gb": "", "videos": "1", "fetched_at": "",
            })
        return self.write_metadata_candidates(payload)

    @staticmethod
    def _candidate(item, index, default_source, value):
        """一个候选。`value` 给字符串就是单来源的取值；给 dict 可以单独指定来源，
        并把 `value`（落库用的结构）和 `display`（来源页面的原文）分开。"""
        source, display, extra = default_source, value, {}
        if isinstance(value, dict):
            source = value.get("source", default_source)
            display = value.get("display", value["value"])
            # 其余键原样带过去：标签候选还要带上 `unmapped_genres`。
            extra = {key: item for key, item in value.items()
                     if key not in {"source", "display", "value"}}
            value = value["value"]
        return {**extra, "candidate_key": f"{item['item_key']}:{index}", "source": source,
                "display_value": display, "value": value, "confidence": 0.9,
                # 来源自报的番号。落库前要和这一行的番号对得上，所以默认取同一个值；
                # 用例给 `provider_id` 就能造出「来源返回的是别的作品」那一半。
                "provider_id": item.get("provider_id") or item.get("code", item["item_key"]),
                "source_url": "", "raw_snapshot": ""}

    def _asset(self, aid, code, name):
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO asset(id,location,path,name,medium,code) "
                    "VALUES(?,'local',?,?,'video',?)", (aid, f"/x/{name}", name, code))
        con.commit(); con.close()

    def _auto(self):
        return auto_apply_metadata(self.contract.database, self.candidates)

    def test_auto_apply_commits_in_batches_and_keeps_what_landed_before_a_stop(self):
        """整库一趟能有上万条。一个事务包到底的话，写锁全程被占着，界面上的复核与编辑
        都得排队；任务中途停下来，已经判完的也跟着回滚。分批提交两头都解决。
        """
        rows = []
        for index, asset_id in enumerate((201, 202, 203, 204), start=1):
            code = f"PPT-1{index:02d}"
            self._asset(asset_id, code, f"{code}.mp4")
            rows.append({"item_key": f"{code}:release_date", "field": "release_date",
                         "current": "", "candidates": ["2015-02-20"], "code": code})
        self.write_metadata_rows(rows)

        database = self.contract.database
        opened = []
        real = database.write_transaction

        def counted():
            opened.append(1)
            return real()

        database.write_transaction = counted
        # 第三批开始之前停：前两批各自提交过，剩下的一条都不动。
        result = auto_apply_metadata(database, self.candidates, batch_size=1,
                                     active=lambda: len(opened) < 2)
        database.write_transaction = real

        self.assertEqual(len(opened), 2)
        self.assertEqual(result["applied"], 2)
        con = sqlite3.connect(self.db_path)
        try:
            landed = [row[0] for row in con.execute(
                "SELECT id FROM asset WHERE release_date='2015-02-20' ORDER BY id")]
        finally:
            con.close()
        self.assertEqual(landed, [201, 202])

    def test_latest_candidate_uses_write_time_not_filename_order(self):
        older = self.candidates / "metadata-field-candidates-windows-p0-proof-20260822.csv"
        newer = self.candidates / "metadata-field-candidates-japanese-official-tags-20260827.csv"
        older.write_text("item_key\nOLD\n", encoding="utf-8")
        newer.write_text("item_key\nNEW\n", encoding="utf-8")
        os.utime(older, (1000, 1000))
        os.utime(newer, (2000, 2000))

        self.assertEqual(
            rm_candidates.latest_candidate_file("metadata_fields", self.candidates), newer,
        )

    def test_a_health_report_written_beside_the_batch_is_not_the_latest_batch(self):
        batch = self.candidates / "studio-logo-candidate-20260923.csv"
        health = self.candidates / "studio-logo-candidate-20260923-health.csv"
        batch.write_text("studio,saved\nFALENO,FALENO.jpg\n", encoding="utf-8")
        health.write_text("attempted,resolved\n12,12\n", encoding="utf-8")
        # 报告在候选之后落盘，修改时间晚几毫秒。
        os.utime(batch, (2000, 2000))
        os.utime(health, (2001, 2001))

        rows, _source, _skipped = rm_candidates.read_candidates("studio_logos", self.candidates)

        self.assertEqual([row["item_key"] for row in rows], ["FALENO"])

    def test_older_batches_keep_their_undecided_rows_in_the_queue(self):
        """跑了新批次不该让上一批未复核的行消失。

        实测：9 月 1 日那批的 128 条可落库行被 9 月 5 日的批次挤出队列，界面上再也
        看不到——既没被判过，也再没机会被判。每批只覆盖它自己那批番号。
        """
        older = self.candidates / "metadata-field-candidates-tagbackfill.csv"
        newer = self.candidates / "metadata-field-candidates-javdb-20260905.csv"
        older.write_text("item_key\n259LUXU-1509:studio\n", encoding="utf-8")
        newer.write_text("item_key\nJBS-023:studio\n", encoding="utf-8")
        os.utime(older, (1000, 1000))
        os.utime(newer, (2000, 2000))

        rows, source, _skipped = rm_review.read_candidates("metadata_fields", self.candidates)
        self.assertEqual({row["item_key"] for row in rows},
                         {"259LUXU-1509:studio", "JBS-023:studio"})
        self.assertIn(newer.name, source)

    def test_newer_batch_wins_when_two_batches_carry_the_same_key(self):
        """同一个 item_key 出现在两批里时，新批次的证据说了算。"""
        fields = ["item_key", "code", "query", "field", "current_value",
                  "candidates_json", "source_count", "status", "size_gb", "videos",
                  "fetched_at"]
        common = {"code": "ABC-001", "query": "ABC-001", "field": "studio",
                  "current_value": "", "source_count": "1", "status": "candidate",
                  "size_gb": "1", "videos": "1", "fetched_at": "now"}
        older = self._csv("metadata-field-candidates-20260901.csv", fields, [{
            **common, "item_key": "ABC-001:studio",
            "candidates_json": '[{"value":"旧批次"}]'}])
        newer = self._csv("metadata-field-candidates-20260905.csv", fields, [{
            **common, "item_key": "ABC-001:studio",
            "candidates_json": '[{"value":"新批次"}]'}])
        os.utime(older, (1000, 1000))
        os.utime(newer, (2000, 2000))

        rows, _source, _skipped = rm_review.read_candidates("metadata_fields", self.candidates)
        self.assertEqual(len(rows), 1)
        self.assertIn("新批次", rows[0]["candidates_json"])

    def test_fc2_metadata_partition_joins_the_latest_jav_queue(self):
        fields = ["item_key", "code", "query", "field", "field_label", "current_value",
                  "candidates_json", "source_count", "source_profile", "policy_version",
                  "status", "size_gb", "videos", "fetched_at"]
        common = {"current_value": "", "candidates_json": "[]", "source_count": "1",
                  "source_profile": "test", "policy_version": "test", "status": "candidate",
                  "size_gb": "1", "videos": "1", "fetched_at": "now"}
        self._csv("metadata-field-candidates-20260822.csv", fields, [{
            **common, "item_key": "ABC-001:title", "code": "ABC-001",
            "query": "ABC-001", "field": "title", "field_label": "标题",
        }])
        self._csv("fc2-metadata-field-candidates.csv", fields, [{
            **common, "item_key": "FC2-PPV-3701252:title", "code": "FC2-PPV-3701252",
            "query": "FC2-PPV-3701252", "field": "title", "field_label": "标题",
        }])
        rows, source, skipped = rm_review.read_candidates("metadata_fields", self.candidates)
        self.assertEqual({row["item_key"] for row in rows},
                         {"ABC-001:title", "FC2-PPV-3701252:title"})
        self.assertIn("metadata-field-candidates-20260822.csv", source)
        self.assertIn("fc2-metadata-field-candidates.csv", source)
        self.assertEqual(skipped, 0)

    def test_japanese_title_partition_overrides_the_same_key_from_the_general_batch(self):
        fields = ["item_key", "code", "query", "field", "current_value",
                  "candidates_json", "source_count", "source_profile", "policy_version",
                  "status", "size_gb", "videos", "fetched_at"]
        common = {"code": "ABP-222", "query": "ABP-222", "field": "title",
                  "current_value": "English", "source_count": "1", "source_profile": "test",
                  "policy_version": "test", "status": "candidate", "size_gb": "1",
                  "videos": "1", "fetched_at": "now"}
        self._csv("metadata-field-candidates-20260822.csv", fields, [{
            **common, "item_key": "ABP-222:title", "candidates_json": '[{"value":"English"}]',
        }])
        self._csv("japanese-title-candidates.csv", fields, [{
            **common, "item_key": "ABP-222:title", "candidates_json": '[{"value":"日本語"}]',
        }])
        rows, source, skipped = rm_review.read_candidates("metadata_fields", self.candidates)
        self.assertEqual(len(rows), 1)
        self.assertIn("日本語", rows[0]["candidates_json"])
        self.assertIn("japanese-title-candidates.csv", source)
        self.assertEqual(skipped, 0)

    def _release_row(self, key, code, source="r18dev", current="", n=1):
        return {"item_key": key, "field": "release_date", "current": current,
                "candidates": ["2015-02-20"][:n], "code": code, "source": source}

    def test_release_date_from_one_official_source_lands_without_review(self):
        """ADR-0018 的窄例外：补空 + 唯一候选 + 官方来源 + 番号在文件名里。"""
        self._asset(90, "PPT-018", "PPT-018-1-uncensored.mp4")
        self.write_metadata_rows([{"item_key": "PPT-018:release_date", "field": "release_date",
                                   "current": "", "candidates": ["2015-02-20"],
                                   "code": "PPT-018"}])
        result = self._auto()
        self.assertEqual(result["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=90").fetchone()[0],
                "2015-02-20")
            # 留痕才是「不直接改写真相字段」真正要保住的东西。
            note = con.execute("SELECT note FROM review_decision WHERE item_key=?",
                               ("PPT-018:release_date",)).fetchone()[0]
            self.assertIn("auto_applied", note)
            self.assertIn("adr-0018", note)
        finally:
            con.close()
        # 落库后不再占队列。
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_auto_apply_refuses_when_the_code_is_not_in_the_filename(self):
        """番号是这条捷径唯一的身份保证：刮削按番号取值，番号错则值错。"""
        self._asset(91, "PPT-018", "无关的文件名.mp4")
        self.write_metadata_rows([{"item_key": "PPT-018:release_date", "field": "release_date",
                                   "current": "", "candidates": ["2015-02-20"],
                                   "code": "PPT-018"}])
        self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertIsNone(
                con.execute("SELECT release_date FROM asset WHERE id=91").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(self.queue_keys("metadata_fields"), ["PPT-018:release_date"])

    def test_a_filename_without_the_hyphen_still_identifies_the_code(self):
        """`MEYD911.mp4` 就是 `MEYD-911`，编目规则读得出来，逐字比对读不出。

        差一个连字符就要人去点一遍，而点的人在界面上看到的仍只是番号和候选值，
        并不比这条判据知道得更多。本机 2611 条有番号的视频里这样的有 297 条。
        """
        self._asset(94, "MEYD-911", "MEYD911.mp4")
        self.write_metadata_rows([{"item_key": "MEYD-911:release_date", "field": "release_date",
                                   "current": "", "candidates": ["2015-02-20"],
                                   "code": "MEYD-911"}])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=94").fetchone()[0],
                "2015-02-20")
        finally:
            con.close()

    def test_the_ledgers_own_spelling_of_the_code_still_matches_the_candidate(self):
        """账本存编目后的写法，候选件写来源站上那个号，两边归一化之后是同一个键。

        `n0762` 在账本里是 `TOKYO-HOT-N0762`，按字符串比一条都对不上——而复核页
        用的就是归一化那一份，于是页面显示「1 个匹配资产」，自动落库却说没有。
        """
        self._asset(95, "TOKYO-HOT-N0762", "n0762.mkv")
        self.write_metadata_rows([{"item_key": "n0762:release_date", "field": "release_date",
                                   "current": "", "candidates": ["2012-07-13"],
                                   "code": "n0762"}])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=95").fetchone()[0],
                "2012-07-13")
        finally:
            con.close()

    def test_a_code_that_only_looks_alike_is_not_taken_for_this_one(self):
        """收小范围用的是子串，判等仍按归一化：`N0762` 出现在别的番号里不算命中。"""
        self._asset(96, "AN0762X", "AN0762X.mp4")
        self.write_metadata_rows([{"item_key": "n0762:release_date", "field": "release_date",
                                   "current": "", "candidates": ["2012-07-13"],
                                   "code": "n0762"}])
        self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertIsNone(
                con.execute("SELECT release_date FROM asset WHERE id=96").fetchone()[0])
        finally:
            con.close()

    def test_an_fc2_filename_is_read_by_its_product_number(self):
        """FC2 的身份是商品号那串数字，前缀写法盘里有好几种。"""
        self._asset(97, "FC2-PPV-4927200", "FC2-4927200-CD1.mp4")
        self._asset(98, "FC2-PPV-4927200", "fc4927200.mp4")
        self.write_metadata_rows([{"item_key": "FC2-PPV-4927200:release_date",
                                   "field": "release_date", "current": "",
                                   "candidates": ["2024-03-01"], "code": "FC2-PPV-4927200"}])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=97").fetchone()[0],
                "2024-03-01")
        finally:
            con.close()

    def test_a_promo_clip_in_the_same_group_does_not_stop_the_whole_code(self):
        """盗版包塞进来的推广片读不出任何番号，它证明不了这组是别的片。"""
        self._asset(99, "259LUXU-902", "259LUXU-902.mp4")
        self._asset(100, "259LUXU-902", "免费手机看片.avi")
        self.write_metadata_rows([{"item_key": "259LUXU-902:release_date",
                                   "field": "release_date", "current": "",
                                   "candidates": ["2018-05-02"], "code": "259LUXU-902"}])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=99").fetchone()[0],
                "2018-05-02")
        finally:
            con.close()

    def test_another_release_code_in_the_group_still_goes_to_a_person(self):
        """组里混进的是另一部片时那条文件名读得出来，身份就不成立了。"""
        self._asset(101, "259LUXU-902", "259LUXU-902.mp4")
        self._asset(102, "259LUXU-902", "ABW-358.mp4")
        self.write_metadata_rows([{"item_key": "259LUXU-902:release_date",
                                   "field": "release_date", "current": "",
                                   "candidates": ["2018-05-02"], "code": "259LUXU-902"}])
        self.assertEqual(self._auto()["applied"], 0)
        self.assertEqual(self.queue_keys("metadata_fields"), ["259LUXU-902:release_date"])

    def _tag_row(self, item_key, code, genres, *, current=""):
        """一条标签候选。`value` 是投影后的标签，`unmapped_genres` 是没有去向的原文。"""
        tags, unmapped = map_genres(genres)
        return {"item_key": item_key, "code": code, "field": "tags", "current": current,
                "candidates": [{"value": tags, "display": "、".join(tags),
                                "unmapped_genres": unmapped}]}

    def test_a_tag_set_with_nowhere_left_to_judge_lands_without_a_human(self):
        """当前值为空、只有一个来源、每个 genre 都有去向——页面上没有可判断项。

        `当前值：尚无；1 个匹配资产；1 个来源候选` 这样的卡片本机有 268 条，
        点「通过」和不点的区别只是谁去点。
        """
        self._asset(95, "ABW-251", "ABW-251.mp4")
        self.write_metadata_rows([self._tag_row(
            "ABW-251:tags", "ABW-251", ["Shaved Pussy", "Masturbation", "Featured Actress"])])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                sorted(row[0] for row in con.execute(
                    "SELECT tag FROM asset_tag WHERE asset_id=95")),
                ["白虎", "自慰"], "`Featured Actress` 是演员编成，按非内容排除")
        finally:
            con.close()
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_an_unresolved_genre_keeps_only_the_word_in_the_queue(self):
        """认得出的标签先落库，没人判过的那个词单独留在队列里等收录（ADR-0038）。

        它此前扣住整条候选：一行里认得出的十几个标签陪着一个生词一起等人，而等来的
        判断只关乎那个词。
        """
        self._asset(96, "MIAD-573", "MIAD573_01.wmv")
        # 素材必须是占位词，不能拿真实来源词：词表一收那个词，这条路径就没有未决的
        # 词可测，而扩词表的人跑不到 catalog 域。2026-09-21 先后拿 `シャワー` 和
        # `温泉` 当素材，两次都是这样把测试跑红的。
        row = self._tag_row("MIAD-573:tags", "MIAD-573", ["スレンダー", "まだ知らない分類"])
        self.assertEqual(row["candidates"][0]["unmapped_genres"], ["まだ知らない分類"])
        self.write_metadata_rows([row])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            landed = sorted(tag[0] for tag in con.execute(
                "SELECT tag FROM asset_tag WHERE asset_id=96"))
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='MIAD-573:tags'"
            ).fetchone()[0])
        finally:
            con.close()
        self.assertEqual(landed, [map_genres(["スレンダー"])[0][0]])
        self.assertEqual(note["pending_genres"], ["まだ知らない分類"])
        # 那个词还没人收录，所以这一行照样摆在复核页上——要判的只剩这个词。
        self.assertEqual(self.queue_keys("metadata_fields"), ["MIAD-573:tags"])

    def test_the_row_leaves_the_queue_once_the_pending_word_is_recorded(self):
        """收录了那个词，这一行就没有可判的东西了，该自己消失。"""
        self._asset(96, "MIAD-573", "MIAD573_01.wmv")
        self.write_metadata_rows([self._tag_row(
            "MIAD-573:tags", "MIAD-573", ["スレンダー", "まだ知らない分類"])])
        self.assertEqual(self._auto()["applied"], 1)
        rm_review.w_review_genre(
            self.contract, {"genre": "まだ知らない分類", "tag": "苗条"})
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_a_community_value_or_a_choice_between_two_waits_for_review(self):
        self._asset(92, "AAA-1", "AAA-1.mp4")
        self._asset(93, "BBB-2", "BBB-2.mp4")
        con = sqlite3.connect(self.db_path)
        # 「已有值」这件事由账本说了算，候选件那一栏只是抓取那一刻的快照。
        con.execute("UPDATE asset SET release_date='2001-01-01' WHERE id=92")
        con.commit(); con.close()
        self.write_metadata_rows([
            # 已有值遇上 community 来源：它只补空，改不动账本里已经成立的判断。
            {"item_key": "AAA", "field": "release_date", "current": "2001-01-01",
             "candidates": ["2015-02-20"], "code": "AAA-1", "source": "javdb"},
            # 两个候选：存在取舍，正是复核该做的事。
            {"item_key": "BBB", "field": "release_date", "current": "",
             "candidates": ["2015-02-20", "2016-03-30"], "code": "BBB-2"},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["AAA", "BBB"])

    def test_the_only_source_being_official_replaces_the_value_the_ledger_carries(self):
        """一个字段上只有官方一家说话时，它说的就是这部片的事实，直接落库（ADR-0035）。

        `259LUXU-891` 的发行日期账本里是 2017-11-26，来自官方 mgstage 那页；队列里
        摆着的挑战者是 javbus 按 `259LUXU-1891` 取回的 2026-07-29。把官方唯一来源
        卡在人工这一侧，只会让人从这类队列里一条条把错值挑出去。
        """
        self._asset(88, "MGS-1", "MGS-1.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET release_date='2001-01-01' WHERE id=88")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "MGS", "field": "release_date", "current": "2001-01-01",
             "candidates": ["2017-11-26"], "code": "MGS-1", "source": "mgstage"},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=88").fetchone()[0],
                "2017-11-26")
            note = con.execute(
                "SELECT note FROM review_decision WHERE item_key='MGS'").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(json.loads(note)["rule"],
                         "adr-0035-official-replaces-single-source")

    def test_javbus_gives_way_to_any_other_source_on_the_same_field(self):
        """javbus 的取值只在没有别家时才算证据（ADR-0035）。

        用户 2026-09-16 逐条核对：它常常答的是另一部片。两家分歧时它退开，剩下的
        一家就是唯一来源，本来要人判的取舍题不再存在。
        """
        self._asset(89, "BUS-1", "BUS-1.mp4")
        self.write_metadata_rows([
            {"item_key": "BUS", "field": "release_date", "current": "",
             "candidates": [{"source": "javdb", "value": "2015-02-20"},
                            {"source": "javbus", "value": "2026-07-29"}],
             "code": "BUS-1"},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=89").fetchone()[0],
                "2015-02-20")
        finally:
            con.close()

    def test_auto_apply_fills_empty_fields_from_community_sources_too(self):
        """补空不覆盖任何东西，唯一的风险由「番号在文件名里」那条管，与来源级别无关。

        卡住 official 的代价是实测 76 条 javbus 补空候选全部滞留人工，补的都是账本里
        空着的发行日期——没有可判断项，却要人逐条点过。白名单之外的字段仍然不走这条路。
        """
        self._asset(94, "CCC-3", "CCC-3.mp4")
        self._asset(95, "DDD-4", "DDD-4.mp4")
        self.write_metadata_rows([
            {"item_key": "CCC", "field": "release_date", "current": "",
             "candidates": ["2015-02-20"], "code": "CCC-3", "source": "javdb"},
            # 标签不在白名单：它是多值集合，来源之间的分类粒度分歧是真实的。
            {"item_key": "DDD", "field": "tags", "current": "",
             "candidates": ["巨乳"], "code": "DDD-4"},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT release_date FROM asset WHERE id=94").fetchone()[0],
                "2015-02-20")
            note = con.execute(
                "SELECT note FROM review_decision WHERE item_key='CCC'").fetchone()[0]
        finally:
            con.close()
        # 规则名要留下来源级别，否则日后回溯不出哪些值是 community 源补的。
        self.assertEqual(json.loads(note)["rule"],
                         "adr-0018-empty-field-single-community-source")

    def test_auto_apply_takes_a_local_nfo_value_and_lets_it_win_the_chain(self):
        """NFO 的番号已经和文件名对过，是补空证据；和在线来源写法不一时它排在链首。

        英文机翻对日文原题这道题此前每次都摆到人面前（ADR-0029 已经判过一次同样的
        事），而链上 `local_nfo` 本来就在 r18dev 前面——让它说话就不必再问人。
        """
        self._asset(90, "ABW-358", "ABW-358.mp4")
        self._asset(91, "ABW-359", "ABW-359.mp4")
        self.write_metadata_rows([
            {"item_key": "ABW", "field": "title", "current": "",
             "candidates": ["涼森れむ流 HOW TO SEX！！"], "code": "ABW-358", "source": "local_nfo"},
            {"item_key": "ABX", "field": "title", "current": "",
             "candidates": ["涼森れむ流", {"value": "Remu Style", "source": "r18dev"}],
             "code": "ABW-359", "source": "local_nfo"},
        ])
        self.assertEqual(self._auto()["applied"], 2)
        con = sqlite3.connect(self.db_path)
        try:
            title, owners = con.execute(
                "SELECT catalog_title,field_owners FROM asset WHERE id=90").fetchone()
            notes = dict(con.execute(
                "SELECT item_key,note FROM review_decision WHERE item_key IN ('ABW','ABX')"))
            chained = con.execute(
                "SELECT catalog_title FROM asset WHERE id=91").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(title, "涼森れむ流 HOW TO SEX！！")
        self.assertEqual(owner_of(owners, "catalog_title"), "auto:local_nfo")
        self.assertEqual(json.loads(notes["ABW"])["rule"], "adr-0029-empty-field-local-nfo")
        self.assertEqual(chained, "涼森れむ流")
        # 被压下的说法要留痕：事后得答得出当时还有哪个值、为什么没选它。
        self.assertEqual(json.loads(notes["ABX"])["rule"], "adr-0038-chain-local_nfo")
        self.assertEqual(json.loads(notes["ABX"])["overruled"],
                         [{"source": "r18dev", "value": "Remu Style"}])
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_the_chain_settles_a_disagreement_between_two_official_sources(self):
        """转售店与片商的口径差不是「哪个对」，链上片商排在前面就该听它的（ADR-0038）。

        本机队列里按链取舍的 60 行全是这一种：mgstage 的标题缀着店铺加赠、系列
        写的是店内货架名，dmm 与 libredmm 那一侧才是片商自己的口径。
        """
        self._asset(120, "ABW-360", "ABW-360.mp4")
        self.write_metadata_rows([
            {"item_key": "SHOP", "field": "title", "current": "", "code": "ABW-360",
             "candidates": [{"value": "圧倒的ケツ圧ピストン！！", "source": "dmm"},
                            {"value": "圧倒的ケツ圧ピストン！！【MGSだけのおまけ映像付き】",
                             "source": "mgstage"}]},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            title = con.execute(
                "SELECT catalog_title FROM asset WHERE id=120").fetchone()[0]
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='SHOP'").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(title, "圧倒的ケツ圧ピストン！！")
        self.assertEqual(note["rule"], "adr-0038-chain-dmm")
        # 被压下的说法要留痕：事后得答得出当时还有哪个值、为什么没选它。
        self.assertEqual(
            note["overruled"],
            [{"source": "mgstage", "value": "圧倒的ケツ圧ピストン！！【MGSだけのおまけ映像付き】"}])

    def test_one_source_giving_two_values_still_waits_for_a_human(self):
        """链能排来源，排不了同一家自己给出的两个值：那里没有可依据的先后。"""
        self._asset(121, "ABW-361", "ABW-361.mp4")
        self.write_metadata_rows([
            {"item_key": "TWO", "field": "title", "current": "", "code": "ABW-361",
             "candidates": [{"value": "第一种说法", "source": "dmm"},
                            {"value": "第二种说法", "source": "dmm"}]},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        self.assertEqual(self.queue_keys("metadata_fields"), ["TWO"])

    def test_a_blacklisted_source_does_not_speak_for_that_field(self):
        """黑名单优先于一切：被拉黑的来源连「只剩它一家」都不算数（ADR-0038）。"""
        self._asset(122, "ABW-362", "ABW-362.mp4")
        self.write_metadata_rows([
            {"item_key": "BLOCK", "field": "series", "current": "", "code": "ABW-362",
             "candidates": [{"value": "店内货架名", "source": "mgstage"}]},
        ])
        with mock.patch.dict(rm_policy.FIELD_SOURCE_BLACKLIST,
                             {"series": frozenset({"mgstage"})}, clear=True):
            self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertIsNone(
                con.execute("SELECT series FROM asset WHERE id=122").fetchone()[0])
        finally:
            con.close()

    def test_a_field_priority_entry_lifts_a_source_to_the_head_of_the_chain(self):
        """稀疏例外把某一家提到链首，只影响写在表里的那个字段。"""
        self._asset(123, "ABW-363", "ABW-363.mp4")
        self.write_metadata_rows([
            {"item_key": "LIFT", "field": "series", "current": "", "code": "ABW-363",
             "candidates": [{"value": "片商系列", "source": "dmm"},
                            {"value": "店内货架名", "source": "mgstage"}]},
        ])
        with mock.patch.dict(rm_policy.FIELD_SOURCE_PRIORITY,
                             {"series": ("mgstage",)}, clear=True):
            self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT series FROM asset WHERE id=123").fetchone()[0],
                "店内货架名")
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='LIFT'").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(note["rule"], "adr-0038-chain-mgstage")

    def test_a_fallback_source_does_not_challenge_a_value_the_ledger_has(self):
        """兜底来源改不动账本已有的值，也不必让人看一眼（ADR-0038）。

        本机队列里这样的行有 111 条（系列 41、出演者 37、厂牌 33），挑战方无一例外
        是 javbus——它搜不到就返回首个近似命中。
        """
        self._asset(124, "TRE-080", "TRE-080.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET series='真实系列' WHERE id=124")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "FALL", "field": "series", "current": "真实系列", "code": "TRE-080",
             "candidates": [{"value": "别的片的系列", "source": "javbus"}]},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT series FROM asset WHERE id=124").fetchone()[0], "真实系列")
        finally:
            con.close()
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def _wiki_snapshot(self, code, names):
        """本机落盘的 Seesaa 作品页快照：这部片写着的正式出演者名。"""
        root = Path(self.tmp.name) / "snapshots"
        folder = root / code
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "sougouwiki.json").write_text(json.dumps({
            "provider": "javinizer-go", "code": code, "source": "sougouwiki",
            "result": {"id": code, "actresses": [{"japanese_name": name} for name in names]},
        }, ensure_ascii=False), encoding="utf-8")
        return root

    def test_a_planning_alias_resolves_to_the_stage_name_on_the_cached_wiki_page(self):
        """企划名义解得出主艺名就落主艺名，原称呼留成别名（ADR-0038）。"""
        self._asset(125, "200GANA-2245", "200GANA-2245.mp4")
        self.write_metadata_rows([
            {"item_key": "PLAN", "field": "performers", "current": "",
             "code": "200GANA-2245", "source": "mgstage",
             "candidates": [{"value": [{"name": "めぐみちゃん"}], "display": "めぐみちゃん"}]},
        ])
        result = auto_apply_metadata(
            self.contract.database, self.candidates,
            snapshot_root=self._wiki_snapshot("200GANA-2245", ["目黒めぐみ"]))
        self.assertEqual(result["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            landed = [row[0] for row in con.execute(
                "SELECT e.canonical_name FROM entity e JOIN asset_entity ae ON ae.entity_id=e.id "
                "WHERE ae.asset_id=125 AND ae.role='performer'")]
            aliases = [row[0] for row in con.execute(
                "SELECT alias FROM entity_alias WHERE source='javinizer:planning-alias'")]
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='PLAN'").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(landed, ["目黒めぐみ"])
        self.assertEqual(aliases, ["めぐみちゃん"],
                         "封面上印的是那个称呼，不登记就等于这次解析搜不到")
        self.assertEqual(note["rule"], "adr-0038-planning-alias-resolved-sougouwiki")

    def test_a_planning_alias_with_no_evidence_still_goes_to_review(self):
        """解不出就交人工。这一层不从宣传语里猜人名，ADR-0025 否决过那件事。"""
        self._asset(126, "FC2-PPV-2486345", "FC2-PPV-2486345.mp4")
        self.write_metadata_rows([
            {"item_key": "NOPE", "field": "performers", "current": "",
             "code": "FC2-PPV-2486345", "source": "javdb",
             "candidates": [{"value": [{"name": "飛鳥ちゃん"}], "display": "飛鳥ちゃん"}]},
        ])
        result = auto_apply_metadata(
            self.contract.database, self.candidates,
            snapshot_root=Path(self.tmp.name) / "empty-snapshots")
        self.assertEqual(result["applied"], 0)
        self.assertEqual(self.queue_keys("metadata_fields"), ["NOPE"])

    def test_a_descriptive_name_is_not_landed_as_a_performer(self):
        """`145cm色白お嬢様` 是标题里的称呼，不是艺名：交人工，不建女优实体。"""
        self._asset(128, "FC2-PPV-1785524", "FC2-PPV-1785524.mp4")
        self._asset(129, "FC2-PPV-1785525", "FC2-PPV-1785525.mp4")
        self.write_metadata_rows([
            {"item_key": "DESC", "field": "performers", "current": "",
             "code": "FC2-PPV-1785524", "source": "javdb",
             "candidates": [{"value": [{"name": "145cm色白お嬢様"}], "display": "145cm色白お嬢様"}]},
            {"item_key": "CROWD", "field": "performers", "current": "",
             "code": "FC2-PPV-1785525", "source": "fc2cmadb",
             "candidates": [{"value": [{"name": "人気焼肉店の看板娘"}],
                             "display": "人気焼肉店の看板娘"}]},
        ])
        result = auto_apply_metadata(
            self.contract.database, self.candidates,
            snapshot_root=Path(self.tmp.name) / "empty-snapshots")
        self.assertEqual(result["applied"], 0)
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["CROWD", "DESC"])
        con = sqlite3.connect(self.db_path)
        try:
            performers = con.execute(
                "SELECT count(*) FROM entity WHERE kind='performer' AND canonical_name IN (?,?)",
                ("145cm色白お嬢様", "人気焼肉店の看板娘")).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(performers, 0)

    def test_an_fc2_seller_lands_as_the_label_under_the_fc2_ppv_studio(self):
        """FC2 番号上来源给的厂牌是卖家：厂牌落 `FC2-PPV`，卖家记在候选的 `label` 上。

        本地 NFO 与 javdb 给的是两个卖家写法，归一之后说的是同一件事，照常一致落库。
        """
        self._asset(130, "FC2-PPV-4927200", "FC2-PPV-4927200.mp4")
        self.write_metadata_rows([
            {"item_key": "SELLER:studio", "field": "studio", "current": "",
             "code": "FC2-PPV-4927200",
             "candidates": [{"source": "local_nfo", "value": "プライベートアーカイブ管理人"},
                            {"source": "javdb", "value": "FC2"}]},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            studio = con.execute("SELECT studio FROM asset WHERE id=130").fetchone()[0]
            entities = [row[0] for row in con.execute(
                "SELECT canonical_name FROM entity WHERE kind='studio'")]
        finally:
            con.close()
        self.assertEqual(studio, "FC2-PPV")
        self.assertEqual(entities, ["FC2-PPV"])
        folded = _fc2_seller_as_label(
            "studio", "FC2-PPV-4927200-1", {"value": "プライベートアーカイブ管理人"})
        self.assertEqual((folded["value"], folded["label"]),
                         ("FC2-PPV", "プライベートアーカイブ管理人"))
        self.assertEqual(_fc2_seller_as_label("studio", "ABP-001", {"value": "Prestige"}),
                         {"value": "Prestige"})

    def test_library_collection_fills_an_empty_field_from_a_lone_community_source(self):
        """官方落空时只有 javdb 一家也补空，note 里分得清是一家还是两家一致（ADR-0034）。"""
        self._asset(90, "ABW-358", "ABW-358.mp4")
        self._asset(91, "ABW-359", "ABW-359.mp4")
        self._asset(92, "ABW-360", "ABW-360.mp4")
        self.write_metadata_rows([
            {"item_key": "ONE", "field": "release_date", "current": "", "profile": "library",
             "candidates": ["2023-05-23"], "code": "ABW-358", "source": "javdb"},
            {"item_key": "TWO", "field": "release_date", "current": "", "profile": "library",
             "candidates": ["2023-05-26", {"value": "2023-05-26", "source": "avbase"}],
             "code": "ABW-359", "source": "javdb"},
            {"item_key": "R18", "field": "release_date", "current": "", "profile": "library",
             "candidates": ["2023-05-26"], "code": "ABW-360", "source": "r18dev"},
        ])
        self.assertEqual(self._auto()["applied"], 3)
        con = sqlite3.connect(self.db_path)
        try:
            dates = dict(con.execute("SELECT id,release_date FROM asset WHERE id IN (90,91,92)"))
            notes = dict(con.execute(
                "SELECT item_key,note FROM review_decision WHERE item_key IN ('ONE','TWO')"))
        finally:
            con.close()
        self.assertEqual(dates, {90: "2023-05-23", 91: "2023-05-26", 92: "2023-05-26"})
        self.assertEqual(json.loads(notes["ONE"])["rule"], "adr-0018-empty-field-single-community-source")
        self.assertEqual(json.loads(notes["TWO"])["rule"], "adr-0025-empty-field-2-agreed-community-sources")
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_auto_apply_records_the_source_as_the_field_owner(self):
        self._asset(96, "EEE-5", "EEE-5.mp4")
        self.write_metadata_rows([
            {"item_key": "EEE", "field": "release_date", "current": "",
             "candidates": ["2015-02-20"], "code": "EEE-5", "source": "javdb"},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            owners, revision = con.execute(
                "SELECT field_owners,mutation_revision FROM asset WHERE id=96").fetchone()
        finally:
            con.close()
        self.assertEqual(owner_of(owners, "release_date"), "auto:javdb")
        self.assertEqual(revision, 1)

    def test_auto_apply_leaves_a_field_the_user_decided_alone(self):
        """用户可以把一个字段判成空，那也是判断，不该被免复核落库当成无主的空位。"""
        self._asset(97, "FFF-6", "FFF-6.mp4")
        con = sqlite3.connect(self.db_path)
        with con:
            write_owned_fields(con, [97], {"release_date": None}, USER_MANUAL)
        con.close()
        self.write_metadata_rows([
            {"item_key": "FFF", "field": "release_date", "current": "",
             "candidates": ["2015-02-20"], "code": "FFF-6"},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertIsNone(
                con.execute("SELECT release_date FROM asset WHERE id=97").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(self.queue_keys("metadata_fields"), ["FFF"])

    def test_approval_writes_the_reviewed_source_as_the_owner(self):
        self._asset(98, "GGG-7", "GGG-7.mp4")
        self.write_metadata_rows([
            {"item_key": "GGG-7:release_date", "field": "release_date", "current": "",
             "candidates": ["2015-02-20"], "code": "GGG-7", "source": "javbus"},
        ])
        result = rm_review.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "GGG-7:release_date",
            "status": "approved", "candidate_key": "GGG-7:release_date:0"})
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            owners = con.execute(
                "SELECT field_owners FROM asset WHERE id=98").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(owner_of(owners, "release_date"), "review:javbus")

    def test_a_stale_expected_revision_refuses_the_approval(self):
        """乐观并发：客户端手上的取值过期时整次批准不落地，`review_decision` 也不留。"""
        self._asset(99, "HHH-8", "HHH-8.mp4")
        con = sqlite3.connect(self.db_path)
        with con:
            write_owned_fields(con, [99], {"studio": "先写的"}, USER_MANUAL)
        con.close()
        self.write_metadata_rows([
            {"item_key": "HHH-8:release_date", "field": "release_date", "current": "",
             "candidates": ["2015-02-20"], "code": "HHH-8", "source": "javbus"},
        ])
        body = {"category": "metadata_fields", "item_key": "HHH-8:release_date",
                "status": "approved", "candidate_key": "HHH-8:release_date:0",
                EXPECTED_REVISION_FIELD: 0}
        with self.assertRaises(RevisionConflict) as caught:
            rm_review.w_review_decision(self.contract, body)
        self.assertEqual(caught.exception.revisions, {99: 1})
        con = sqlite3.connect(self.db_path)
        try:
            self.assertIsNone(
                con.execute("SELECT release_date FROM asset WHERE id=99").fetchone()[0])
            self.assertEqual(con.execute(
                "SELECT count(*) FROM review_decision WHERE item_key=?",
                ("HHH-8:release_date",)).fetchone()[0], 0)
        finally:
            con.close()
        # 拿到现值再来一次就通过。
        body[EXPECTED_REVISION_FIELD] = 1
        self.assertEqual(
            rm_review.w_review_decision(self.contract, body)["applied_assets"], 1)

    def test_the_card_says_who_owns_the_value_it_is_asking_about(self):
        self._asset(100, "III-9", "III-9.mp4")
        con = sqlite3.connect(self.db_path)
        with con:
            write_owned_fields(con, [100], {"studio": "用户写的"}, USER_MANUAL)
        con.close()
        self.write_metadata_rows([
            # 兜底来源挑战已有值的行不进队列（ADR-0038），这里问的是卡片怎么说归属。
            {"item_key": "III-9:studio", "field": "studio", "current": "用户写的",
             "candidates": ["别家厂牌"], "code": "III-9", "source": "javdb"},
        ])
        rows, _source, _skipped = rm_review._review_rows(self.contract, "metadata_fields")
        row = next(item for item in rows if item["item_key"] == "III-9:studio")
        self.assertEqual(row["current_owner"], USER_MANUAL)
        self.assertEqual(row["asset_mutation_revision"], 1)
        self.assertIn("（手动填写）", rm_review._review_evidence("metadata_fields", row))

    def test_two_sources_saying_the_same_thing_land_without_review(self):
        """数取值，不数候选条数。

        两家独立来源给出同一个值，是这批候选里最强的证据；按条数算却会被判成
        「有分歧」。实测 349 条这样被扣住，`259LUXU-1509` 的厂牌、演员和发行日期
        都是 mgstage 与 libredmm 逐字相同，却谁也没写进账本。
        """
        self._asset(120, "259LUXU-1509", "259LUXU-1509.mp4")
        self.write_metadata_rows([{
            "item_key": "259LUXU-1509:studio", "field": "studio", "current": "",
            "code": "259LUXU-1509",
            "candidates": [{"source": "libredmm", "value": "ラグジュTV"},
                           {"source": "mgstage", "value": "ラグジュTV"}],
        }])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT studio FROM asset WHERE id=120").fetchone()[0],
                "ラグジュTV")
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key=?",
                ("259LUXU-1509:studio",)).fetchone()[0])
        finally:
            con.close()
        # 几家一致要记下来：这类的证据强度和单来源补空不一样。
        self.assertEqual(note["rule"], "adr-0025-empty-field-2-agreed-official-sources")
        # 署名给字段来源顺序里最靠前的那家，不是候选数组里排第一的那家。
        self.assertEqual(note["source"], "libredmm")

    def test_the_chain_puts_javdb_over_other_community_and_official_over_javdb(self):
        """社区之间听 javdb，官方在场时听官方——两件事在链上是同一条规则（ADR-0038）。"""
        self._asset(122, "MAAN-545", "MAAN-545.mp4")
        self._asset(123, "HHH-8", "HHH-8.mp4")
        self.write_metadata_rows([
            {"item_key": "MAAN:studio", "field": "studio", "current": "", "code": "MAAN-545",
             "candidates": [{"source": "avbase", "value": "DOC"},
                            {"source": "javbus", "value": "DOC"},
                            {"source": "javdb", "value": "プレステージプレミアム"}]},
            {"item_key": "HHH:studio", "field": "studio", "current": "", "code": "HHH-8",
             "candidates": [{"source": "mgstage", "value": "官方厂牌"},
                            {"source": "javdb", "value": "社区厂牌"}]},
        ])
        self.assertEqual(self._auto()["applied"], 2)
        con = sqlite3.connect(self.db_path)
        try:
            studios = dict(con.execute("SELECT id,studio FROM asset WHERE id IN (122,123)"))
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='MAAN:studio'").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(studios, {122: "プレステージプレミアム", 123: "官方厂牌"})
        self.assertEqual((note["source"], note["rule"]), ("javdb", "adr-0038-chain-javdb"))
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_a_studio_spelled_as_a_registered_alias_lands_under_its_canonical_name(self):
        """javdb 写 `Tokyo-Hot`，账本把它登记为 `东京热` 的别名，卡片上就该是 `东京热`。"""
        self._asset(127, "N1042", "n1042.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,"
                    "updated_at) VALUES(61,'studio','东京热','东京热','2026-01-01','2026-01-01')")
        con.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
                    "confidence) VALUES(61,'Tokyo-Hot','tokyo-hot','user:manual',1.0)")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "N1042:studio", "field": "studio", "current": "", "code": "N1042",
             "candidates": ["Tokyo-Hot"], "source": "javdb"},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            studio = con.execute("SELECT studio FROM asset WHERE id=127").fetchone()[0]
            linked = con.execute("SELECT entity_id FROM asset_entity WHERE asset_id=127 "
                                 "AND role='studio'").fetchall()
            studios = con.execute("SELECT count(*) FROM entity WHERE kind='studio'").fetchone()[0]
        finally:
            con.close()
        self.assertEqual((studio, linked, studios), ("东京热", [(61,)], 1))

    def test_a_dated_code_keeps_the_release_date_it_carries(self):
        """`092415_001` 自己写着 2015-09-24，javdb 给的转售上架日不落；番号那天谁都没给就交给人。"""
        self._asset(124, "092415_001", "1pon-092415_001.mp4")
        self._asset(125, "092415_159", "1pon-092415_159.mp4")
        self.write_metadata_rows([
            {"item_key": "D1", "field": "release_date", "current": "", "code": "092415_001",
             "candidates": [{"source": "javbus", "value": "2015-09-24"},
                            {"source": "javdb", "value": "2016-06-16"}]},
            {"item_key": "D2", "field": "release_date", "current": "", "code": "092415_159",
             "candidates": [{"source": "javdb", "value": "2016-06-09"}]},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            dates = dict(con.execute("SELECT id,release_date FROM asset WHERE id IN (124,125)"))
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='D1'").fetchone()[0])
        finally:
            con.close()
        self.assertEqual(dates, {124: "2015-09-24", 125: None})
        self.assertEqual((note["source"], note["rule"]), ("javbus", "adr-0034-empty-field-code-date"))
        self.assertEqual(self.queue_keys("metadata_fields"), ["D2"])

    def test_a_result_for_another_release_never_lands(self):
        """来源返回的不是这个番号，就不该写进真相字段。

        自动批准的三项判据对这类候选全部成立——`AR-101 Ari....mp4` 的文件名里确实
        逐字有 `AR-101`——但那证明的是候选属于这个文件，不是来源返回的属于这个番号。
        javbus 搜不到就给首个近似命中，`AR-101` 取回的是 `STAR-101`。
        """
        self._asset(130, "AR-101", "AR-101 Ari.mp4")
        self._asset(131, "259LUXU-764", "259LUXU-764.mp4")
        self.write_metadata_rows([
            {"item_key": "AR-101:studio", "field": "studio", "current": "",
             "candidates": ["SODクリエイト"], "code": "AR-101",
             "provider_id": "STAR-101", "source": "javbus"},
            {"item_key": "259LUXU-764:studio", "field": "studio", "current": "",
             "candidates": ["ラグジュTV"], "code": "259LUXU-764",
             "provider_id": "259LUXU-1764", "source": "javbus"},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM asset WHERE studio IS NOT NULL")
                .fetchone()[0], 0)
        finally:
            con.close()

    def test_a_row_whose_candidates_all_name_another_release_stays_out_of_the_queue(self):
        """错配的候选连队列都不该进：它写不进去，摆在那儿只是要人认出它写不进去。

        `259LUXU-891` 那一行的两个候选都是 javbus 按 `259LUXU-1891` 取回的，点批准
        会被落库端拒掉。实测队列 148 行里有 18 个这样的候选，14 行整行只有它们。
        """
        self._asset(133, "259LUXU-891", "259LUXU-891.mp4")
        self._asset(134, "259LUXU-892", "259LUXU-892.mp4")
        self.write_metadata_rows([
            {"item_key": "259LUXU-891:release_date", "field": "release_date",
             "current": "2017-11-26", "candidates": ["2026-07-29"],
             "code": "259LUXU-891", "provider_id": "259LUXU-1891", "source": "javbus"},
            # 同一家给对了番号：这一行仍然是人该看的。
            {"item_key": "259LUXU-892:release_date", "field": "release_date",
             "current": "2017-11-26", "candidates": ["2017-12-01"],
             "code": "259LUXU-892", "source": "javbus"},
        ])
        self.assertEqual(self.queue_keys("metadata_fields"), ["259LUXU-892:release_date"])

    def test_manual_approval_is_refused_for_another_release_too(self):
        """人点的批准也过这道闸：错配落库的那批里有四成是人工批准的。"""
        self._asset(132, "259LUXU-811", "259LUXU-811.mp4")
        self.write_metadata_rows([
            {"item_key": "259LUXU-811:studio", "field": "studio", "current": "",
             "candidates": ["ラグジュTV"], "code": "259LUXU-811",
             "provider_id": "259LUXU-1811", "source": "javbus"},
        ])
        with self.assertRaises(ValueError) as caught:
            rm_review.w_review_decision(self.contract, {
                "category": "metadata_fields", "item_key": "259LUXU-811:studio",
                "candidate_key": "259LUXU-811:studio:0", "status": "approved"})
        self.assertIn("259LUXU-811", str(caught.exception))
        con = sqlite3.connect(self.db_path)
        try:
            self.assertIsNone(
                con.execute("SELECT studio FROM asset WHERE id=132").fetchone()[0])
        finally:
            con.close()

    def test_performer_name_is_cut_at_the_age_the_official_page_appends(self):
        """素人系官方页把年龄职业写进出演者栏，照抄会把整句变成实体名。"""
        self._asset(122, "259LUXU-1509", "259LUXU-1509.mp4")
        self.write_metadata_rows([{
            "item_key": "259LUXU-1509:performers", "field": "performers", "current": "",
            "code": "259LUXU-1509",
            "candidates": [{"source": "mgstage", "display": "本庄美奈子 30歳 元カフェ店員",
                            "value": [{"name": "本庄美奈子 30歳 元カフェ店員",
                                       "external_id": "", "thumb_url": ""}]}],
        }])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                [row[0] for row in con.execute(
                    "SELECT canonical_name FROM entity WHERE kind='performer' "
                    "AND canonical_name LIKE '本庄%'")],
                ["本庄美奈子"])
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key=?",
                ("259LUXU-1509:performers",)).fetchone()[0])
        finally:
            con.close()
        # 剪过就要留得下原文，否则回溯不出账本里这个名字是从哪一句剪出来的。
        self.assertEqual(note["value"], "本庄美奈子")
        self.assertEqual(note["raw_value"], "本庄美奈子 30歳 元カフェ店員")

    def test_two_sources_naming_one_registered_person_is_not_a_disagreement(self):
        """两家给的艺名不同，账本却早把它们登记在同一条实体名下，那就不是分歧。

        `n0646` javbus 写 `一ノ瀬アメリ`、javdb 写 `美空あやか`，本机账本里这两个写法
        都挂在实体 8074（规范名 `美空彩香`）下。按字符串比这类行全被扣在人工队列，
        而要判的那个问题账本自己已经答过了。
        """
        self._asset(125, "N0646", "n0646.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,"
                    "updated_at) VALUES(60,'performer','美空彩香','美空彩香',"
                    "'2026-01-01','2026-01-01')")
        for alias in ("一ノ瀬アメリ", "美空あやか"):
            con.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
                        "confidence) VALUES(60,?,?,'peach:canonicalization',1.0)",
                        (alias, alias))
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "N0646:performers", "field": "performers", "current": "",
             "code": "N0646",
             "candidates": [{"source": "javbus", "display": "一ノ瀬アメリ",
                             "value": [{"name": "一ノ瀬アメリ"}]},
                            {"source": "javdb", "display": "美空あやか",
                             "value": [{"name": "美空あやか"}]}]},
        ])
        self.assertEqual(self._auto()["applied"], 1)
        self.assertEqual(self.queue_keys("metadata_fields"), [])
        con = sqlite3.connect(self.db_path)
        try:
            # 落的是同一条实体，不是第三个新人。
            self.assertEqual(con.execute(
                "SELECT ae.entity_id FROM asset_entity ae WHERE ae.asset_id=125 "
                "AND ae.role='performer'").fetchall(), [(60,)])
            note = json.loads(con.execute(
                "SELECT note FROM review_decision WHERE item_key='N0646:performers'"
            ).fetchone()[0])
        finally:
            con.close()
        # 记的不是链上取舍：折叠之后这一行根本没有第二个取值可压。计数只剩一家，是
        # 因为兜底那一家（javbus）在比之前就降过级（ADR-0035）。
        self.assertEqual(note["rule"], "adr-0018-empty-field-single-community-source")

    def test_one_source_listing_the_cast_in_another_order_is_not_a_disagreement(self):
        """同一组人换个排序不是换人：`FSEI-003` 两家给的就是同样六个人，顺序不同。"""
        self._asset(127, "FSEI-003", "FSEI-003.mp4")
        self.write_metadata_rows([{
            "item_key": "FSEI-003:performers", "field": "performers", "current": "",
            "code": "FSEI-003",
            "candidates": [{"source": "javbus", "display": "宇流木さら、伊東紅蘭",
                            "value": [{"name": "宇流木さら"}, {"name": "伊東紅蘭"}]},
                           {"source": "javdb", "display": "伊東紅蘭、宇流木さら",
                            "value": [{"name": "伊東紅蘭"}, {"name": "宇流木さら"}]}]}])
        self.assertEqual(self._auto()["applied"], 1)

    def test_performer_names_that_are_promo_copy_stay_in_review(self):
        """剪完仍带敬称或空白的不是艺名，是企划文案：剪到哪儿才对本身就是个判断。"""
        self._asset(123, "300MIUM-544", "300MIUM-544.mp4")
        self._asset(124, "390JAC-076", "390JAC-076.mp4")
        self.write_metadata_rows([
            {"item_key": "300MIUM-544:performers", "field": "performers", "current": "",
             "code": "300MIUM-544",
             "candidates": [{"source": "mgstage", "display": "りほちゃん 22歳 歯科衛生士",
                             "value": [{"name": "りほちゃん 22歳 歯科衛生士"}]}]},
            {"item_key": "390JAC-076:performers", "field": "performers", "current": "",
             "code": "390JAC-076",
             "candidates": [{"source": "libredmm",
                             "display": "超バドミントン部あかりちゃん 23歳 潮吹き部長",
                             "value": [{"name": "超バドミントン部あかりちゃん 23歳 潮吹き部長"}]}]},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        self.assertEqual(sorted(self.queue_keys("metadata_fields")),
                         ["300MIUM-544:performers", "390JAC-076:performers"])
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM entity WHERE kind='performer' "
                            "AND (canonical_name LIKE '%ちゃん%' "
                            "OR canonical_name LIKE '%歳%')").fetchone()[0],
                0)
        finally:
            con.close()

    def test_community_candidate_never_challenges_an_official_written_value(self):
        """按官方来：community 源推不翻 official 源已确认的值，这种行不进队列。

        实测 26 条发行日期「冲突」里，账本现值全部由 official 源写入（r18dev 10、
        aventertainment 9、libredmm 1），挑战方无一例外是 javbus。让人再判一遍等于把
        `SOURCE_SPECS` 早就排好的信任模型丢回给人。
        """
        self._asset(96, "EEE-5", "EEE-5.mp4")
        self._asset(97, "FFF-6", "FFF-6.mp4")
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                "VALUES('metadata_fields','EEE','approved',?,'2026-08-30T00:00:00Z')",
                (json.dumps({"auto_applied": True, "source": "r18dev",
                             "value": "2015-05-30"}),))
            con.commit()
        finally:
            con.close()
        self.write_metadata_rows([
            # 现值由 r18dev 写入，javbus 想改成别的日期：按信任模型直接不进队列。
            {"item_key": "EEE", "field": "release_date", "current": "2015-05-30",
             "candidates": ["2015-08-30"], "code": "EEE-5", "source": "javbus"},
            # 现值来路不明（没有落库记录）时，community 的异议仍然有意义。
            {"item_key": "FFF", "field": "release_date", "current": "2014-01-01",
             "candidates": ["2014-03-03"], "code": "FFF-6", "source": "javbus"},
        ])
        self.assertEqual(self.queue_keys("metadata_fields"), ["FFF"])

    def test_a_decision_without_a_recorded_value_never_suppresses_the_row(self):
        """人工批准的 note 只记 `candidate_key` 与 `source`，不记写进去的值。

        没记值就证明不了账本现在这一个是它写的，拿它当「official 已确认」会把
        `_metadata_decision_is_stale` 本该重开的字段永久压在队列外面。
        """
        self._asset(98, "GGG-7", "GGG-7.mp4")
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                "VALUES('metadata_fields','GGG','approved',?,'2026-08-30T00:00:00Z')",
                (json.dumps({"candidate_key": "GGG:release_date:r18dev:gone",
                             "source": "r18dev", "user_note": ""}),))
            con.commit()
        finally:
            con.close()
        self.write_metadata_rows([
            {"item_key": "GGG", "field": "release_date", "current": "2016-06-06",
             "candidates": ["2016-09-09"], "code": "GGG-7", "source": "javbus"},
        ])
        self.assertEqual(self.queue_keys("metadata_fields"), ["GGG"])

    def test_metadata_candidates_that_repeat_the_current_value_never_queue(self):
        """复核的成本是注意力：和现值一模一样的行会把真正要判的淹掉。

        实测 43 条里 24 条没有新信息——17 条逐字相同、7 条标签只是顺序不同。
        """
        self.write_metadata_rows([
            {"item_key": "SAME", "field": "studio", "current": "Prestige",
             "candidates": ["Prestige"]},
            {"item_key": "REORDER", "field": "tags", "current": "乳系、痴女、高颜值",
             "candidates": ["高颜值、痴女、乳系"]},
            {"item_key": "EMPTY", "field": "release_date", "current": "",
             "candidates": ["2015-02-20"]},
            {"item_key": "REAL", "field": "studio", "current": "Prestige",
             "candidates": ["Faleno"]},
        ])
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["EMPTY", "REAL"])

    def test_korean_mib_candidates_never_reach_the_review_queue(self):
        """韩国 MIB 不适用 JAV 规则，它的候选没有一条值得占用注意力。

        `allows_code` 拦在刮削入口，管的是以后不再生成；候选件是历史产物，闸门管不着。
        2026-09-04 实测队列里还有 49 条（AR 39、JI 10），值全是 JAV 目录站按错番号返回的
        **别的作品**，让人一条条认出来正是这道过滤要省掉的事。
        """
        self.write_metadata_rows([
            {"item_key": "MIB-AR", "field": "studio", "current": "",
             "candidates": ["Attackers"], "code": "AR-301"},
            {"item_key": "MIB-JI", "field": "release_date", "current": "",
             "candidates": ["2009-12-05"], "code": "JI-103"},
            {"item_key": "MIB-WX", "field": "title", "current": "",
             "candidates": ["某标题"], "code": "WX-017"},
            {"item_key": "MIB-SA", "field": "series", "current": "",
             "candidates": ["某系列"], "code": "SA-104"},
            # BeFree 是真实 JAV 厂牌，两字母前缀不能连它一起拦。
            {"item_key": "BEFREE", "field": "studio", "current": "",
             "candidates": ["BeFree"], "code": "BF-366"},
            {"item_key": "REAL", "field": "studio", "current": "",
             "candidates": ["Faleno"], "code": "ARM-123"},
        ])
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["BEFREE", "REAL"])

    def test_korean_mib_candidates_are_not_auto_applied_either(self):
        """自动批准不读复核队列，那道过滤管不着它，MIB 的闸要单独立在这里。

        三字母前缀同属这套命名，`MIN-102`、`SUY-101` 和两字母的一样不能问 JAV 来源。
        """
        for index, code in enumerate(("AR-101", "MIN-102", "SUY-101", "YUJ-103")):
            self._asset(140 + index, code, f"{code} MIB.mp4")
        self._asset(150, "ARM-123", "ARM-123.mp4")
        self.write_metadata_rows([
            {"item_key": f"{code}:studio", "field": "studio", "current": "",
             "candidates": ["某厂牌"], "code": code}
            for code in ("AR-101", "MIN-102", "SUY-101", "YUJ-103")
        ] + [{"item_key": "ARM-123:studio", "field": "studio", "current": "",
              "candidates": ["Faleno"], "code": "ARM-123"}])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            written = con.execute(
                "SELECT code FROM asset WHERE studio IS NOT NULL").fetchall()
        finally:
            con.close()
        self.assertEqual([row[0] for row in written], ["ARM-123"])

    def test_mib_official_candidates_reach_the_review_queue(self):
        """MIB 官网是这批番号自己的发行方，它的候选要让人看得到；混进 JAV 来源的仍拦下。"""
        self.write_metadata_rows([
            {"item_key": "AR-101:title:kmib", "field": "title", "current": "",
             "candidates": ["PURE PINK"], "code": "AR-101", "source": "kmib"},
            {"item_key": "AR-101:studio", "field": "studio", "current": "",
             "candidates": [{"value": "MIB", "source": "kmib"},
                            {"value": "Attackers", "source": "r18dev"}],
             "code": "AR-101"},
        ])
        self.assertEqual(self.queue_keys("metadata_fields"), ["AR-101:title:kmib"])

    def test_mib_official_candidates_fill_empty_fields_automatically(self):
        self._asset(160, "YUJ-103", "YUJ-103 Ain Do you wanna be my slave.mp4")
        self.write_metadata_rows([
            {"item_key": "YUJ-103:release_date:kmib", "field": "release_date",
             "current": "", "candidates": ["2024-11-20"], "code": "YUJ-103",
             "source": "kmib"}])
        self.assertEqual(self._auto()["applied"], 1)
        con = sqlite3.connect(self.db_path)
        try:
            written = con.execute("SELECT release_date FROM asset WHERE id=160").fetchone()
        finally:
            con.close()
        self.assertEqual(written, ("2024-11-20",))

    def test_japanese_performer_candidate_folds_onto_the_localised_entity(self):
        """r18dev 给日文名，账本规范名多已本地化成中文，而日文名早登记为别名。

        实测 8 对全部解析到同一条实体：按字符串比会全判成「有差异」，批准反而把
        规范名倒退成别名。真正要看的是换人，不是换写法。
        """
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(30,'performer','桃谷绘里香','桃谷绘里香','2026-01-01','2026-01-01')")
        con.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
                    "confidence) VALUES(30,'桃谷エリカ','桃谷エリカ','r18dev',1.0)")
        con.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
                    "confidence) VALUES(30,'桃谷絵里香','桃谷絵里香','r18dev',1.0)")
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(31,'performer','别人','别人','2026-01-01','2026-01-01')")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "ALIAS", "field": "performers", "current": "桃谷绘里香",
             "candidates": ["桃谷エリカ"]},
            {"item_key": "PAREN", "field": "performers", "current": "桃谷绘里香",
             "candidates": ["桃谷エリカ（桃谷絵里香）"]},
            {"item_key": "CAST", "field": "performers", "current": "桃谷绘里香",
             "candidates": ["别人"]},
        ])
        # 只是换写法的不入队；真的换人的留下。
        self.assertEqual(self.queue_keys("metadata_fields"), ["CAST"])

    def test_studio_candidate_folds_onto_the_ledger_brand_entity(self):
        """厂牌在账本里是实体，字段里那串字符只是投影。

        同一家在三处各有写法：账本存规范名 `Prestige`，javbus 给日文名，
        mgstage 与 libredmm 给日英并写的一串。实测本机队列里 10 条「厂牌冲突」
        全是这一种，指的都是同一条实体。
        """
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(50,'studio','Prestige','prestige','2026-01-01','2026-01-01')")
        con.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
                    "confidence) VALUES(50,'プレステージプレミアム','プレステージプレミアム',"
                    "'peach:canonicalization',1.0)")
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(51,'studio','Faleno','faleno','2026-01-01','2026-01-01')")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "JA", "field": "studio", "current": "Prestige",
             "candidates": ["プレステージプレミアム"], "source": "javbus"},
            {"item_key": "BOTH", "field": "studio", "current": "Prestige",
             "candidates": ["プレステージプレミアム(PRESTIGE PREMIUM)"], "source": "libredmm"},
            # 换成另一条实体是真的换了一家，要人判。来源不用兜底那一家：兜底挑战已有
            # 值的行整条不进队列（ADR-0038），那样这两条就在空队列上断言了。
            {"item_key": "OTHER", "field": "studio", "current": "Prestige",
             "candidates": ["Faleno"], "source": "javdb"},
            # 两边都没登记过就没有「同一实体」可言，异议照常要人判。
            {"item_key": "UNKNOWN", "field": "studio", "current": "Prestige",
             "candidates": ["某个没登记的牌子"], "source": "javdb"},
        ])
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["OTHER", "UNKNOWN"])

    def test_planning_alias_never_challenges_the_main_stage_name_in_the_ledger(self):
        """素人企划的出演者栏写的是这部片给她起的称呼，账本存的是她本人的主艺名。

        `259LUXU-1459` 账本存 `結城のの`，libredmm 与 mgstage 给的是
        `桜井奈々 28歳 某企業広報担当` 和 `佐倉井さん 28歳 某企業広報担当`。两者不在
        同一层，按字符串比就成了要人判的「冲突」（用户 2026-09-16 定「取主艺名」）。

        带年龄职业介绍的和剪不出艺名边界的都算企划名义；`DIC-088` 那种三家官方源
        一致给 `堀越麻央`、账本却存着罗马字的，不带这两个特征，照常要人判。
        """
        self.write_metadata_rows([
            {"item_key": "INTRO", "field": "performers", "current": "結城のの",
             "candidates": [{"source": "libredmm", "value": "桜井奈々 28歳 某企業広報担当"},
                            {"source": "mgstage", "value": "佐倉井さん 28歳 某企業広報担当"}]},
            # 敬称结尾同样是企划名义，哪怕没写年龄。
            {"item_key": "HONORIFIC", "field": "performers", "current": "美穗乃",
             "candidates": [{"source": "javbus", "value": "結愛さん"}]},
            # 一条是企划名义、另一条给的是别的艺名：后者照常要人判。
            {"item_key": "MIXED", "field": "performers", "current": "結城のの",
             "candidates": [{"source": "mgstage", "value": "佐倉井さん 28歳 某企業広報担当"},
                            {"source": "javdb", "value": "桜庭ひかり"}]},
            {"item_key": "ROMAJI", "field": "performers", "current": "Horikoshimao",
             "candidates": [{"source": "dmm", "value": "堀越麻央"}]},
        ])
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["MIXED", "ROMAJI"])

    def test_reseller_dissent_never_queues_when_the_maker_store_backs_the_ledger(self):
        """MGS 是转售店，它跟片商那份的三处差异是店铺口径，不是事实争议。

        标题尾巴上缀店铺加赠，发行日期写自己的先行配信日，系列写店内货架名。
        本机 214 条「账本已有值、来源给的不一样」里 158 条是这一种：发行日期 65、
        标题 64、系列 29，与账本一致的一方是 dmm+libredmm 129 条、dmm 29 条。
        """
        self.write_metadata_rows([
            {"item_key": "BONUS", "field": "title", "current": "圧倒的ケツ圧ピストン！！",
             "candidates": [{"source": "dmm", "value": "圧倒的ケツ圧ピストン！！"},
                            {"source": "mgstage",
                             "value": "圧倒的ケツ圧ピストン！！ 【MGSだけのおまけ映像付き+5分】"}]},
            {"item_key": "EARLY", "field": "release_date", "current": "2021-05-07",
             "candidates": [{"source": "libredmm", "value": "2021-05-07"},
                            {"source": "mgstage", "value": "2021-04-29"}]},
            # MGS 独家发行：片商方没有候选，它给的值是这个番号唯一的说法。
            {"item_key": "ONLYMGS", "field": "title", "current": "旧标题",
             "candidates": [{"source": "mgstage", "value": "しろうと女子のAV初体験"}]},
            # 片商方自己也在反对：那是真冲突，这道过滤不该碰。
            {"item_key": "MAKER", "field": "release_date", "current": "2021-05-07",
             "candidates": [{"source": "dmm", "value": "2021-06-01"},
                            {"source": "mgstage", "value": "2021-04-29"}]},
        ])
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["MAKER", "ONLYMGS"])

    def test_the_current_value_comes_from_the_ledger_not_the_snapshot(self):
        """候选件的现值停在抓取那一刻，落过库之后它还写着空。

        实测 300 行队列里 85 行是这样（标签 29、演员 22、标题 13、厂牌 8、系列 8、
        发行日期 5）。队列拿它判「补空还是冲突」，判错的方向是把已有值当成空位。
        """
        self._asset(120, "LIVE-1", "LIVE-1.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET catalog_title='账本里已经有的标题' WHERE id=120")
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,"
                    "updated_at) VALUES(60,'performer','账本里的女优','账本里的女优',"
                    "'2026-01-01','2026-01-01')")
        con.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                    "VALUES(120,60,'performer','board',1.0)")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "LIVE-1:title", "field": "title", "current": "",
             "candidates": ["来源给的另一个标题"], "code": "LIVE-1"},
            {"item_key": "LIVE-1:performers", "field": "performers", "current": "",
             "candidates": ["来源给的另一个人"], "code": "LIVE-1"},
        ])
        self.assertEqual(self.queue_row("metadata_fields", "LIVE-1:title")["current_value"],
                         "账本里已经有的标题")
        self.assertEqual(
            self.queue_row("metadata_fields", "LIVE-1:performers")["current_value"],
            "账本里的女优")

    def test_a_community_source_reads_the_ledger_not_the_snapshot_for_emptiness(self):
        """「这个字段是不是空的」问的必须是账本此刻，不是抓取那一刻的快照。

        快照里那个空值是过期的：照它落库不是补空，是拿 community 来源覆盖账本已有
        的值——而且写完还记一笔 approved。
        """
        self._asset(121, "LIVE-2", "LIVE-2.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET catalog_title='账本里已经有的标题' WHERE id=121")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "LIVE-2:title", "field": "title", "current": "",
             "candidates": ["来源给的另一个标题"], "code": "LIVE-2", "source": "javdb"},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        con = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(
                con.execute("SELECT catalog_title FROM asset WHERE id=121").fetchone()[0],
                "账本里已经有的标题")
            self.assertEqual(con.execute(
                "SELECT count(*) FROM review_decision WHERE item_key='LIVE-2:title'"
            ).fetchone()[0], 0)
        finally:
            con.close()

    def test_an_empty_ledger_field_outranks_a_value_left_in_the_snapshot(self):
        """账本这一格空着，那它就是个空位，哪怕快照里写着一个值。"""
        self._asset(122, "LIVE-3", "LIVE-3.mp4")
        self.write_metadata_rows([
            {"item_key": "LIVE-3:release_date", "field": "release_date",
             "current": "2019-01-01", "candidates": ["2020-02-02"], "code": "LIVE-3"},
        ])
        self.assertEqual(
            self.queue_row("metadata_fields", "LIVE-3:release_date")["current_value"], "")

    def test_one_filled_copy_in_the_group_means_the_field_is_not_empty(self):
        """同番号多卷时落库是整组一起写，所以「空不空」也得按整组问。

        实测 `259LUXU-902` 在账本里有 10 条，九条空、一条有值。只看空着的那一条会
        判成空位，落库却把第十条已有的值一起改掉。
        """
        self._asset(123, "LIVE-4", "LIVE-4-A.mp4")
        self._asset(124, "LIVE-4", "LIVE-4-B.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET catalog_title='第二卷上已有的标题' WHERE id=124")
        con.commit(); con.close()
        self.write_metadata_rows([
            {"item_key": "LIVE-4:title", "field": "title", "current": "",
             "candidates": ["来源给的另一个标题"], "code": "LIVE-4", "source": "javdb"},
        ])
        self.assertEqual(self.queue_row("metadata_fields", "LIVE-4:title")["current_value"],
                         "第二卷上已有的标题")
        self.assertEqual(self._auto()["applied"], 0)

    def test_a_row_pinned_to_one_file_asks_only_that_file(self):
        """带 `asset_path` 的行落库只写那一个文件，现值也只能问那一个。"""
        self._asset(125, "LIVE-5", "LIVE-5-A.mp4")
        self._asset(126, "LIVE-5", "LIVE-5-B.mp4")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET catalog_title='另一卷的标题' WHERE id=126")
        con.commit(); con.close()
        payload = [{
            "item_key": "asset:125:title", "code": "LIVE-5", "query": "LIVE-5",
            "asset_id": "125", "asset_path": "/x/LIVE-5-A.mp4",
            "field": "title", "field_label": "标题", "current_value": "",
            "candidates_json": json.dumps([{
                "candidate_key": "asset:125:title:r18dev:1", "source": "r18dev",
                "display_value": "来源给的标题", "value": "来源给的标题",
                "confidence": 0.9, "provider_id": "LIVE-5", "source_url": "",
                "raw_snapshot": ""}], ensure_ascii=False),
            "source_count": "1", "source_profile": "", "status": "candidate",
            "size_gb": "", "videos": "1", "fetched_at": "",
        }]
        self.write_metadata_candidates(payload)
        self.assertEqual(
            self.queue_row("metadata_fields", "asset:125:title")["current_value"], "")

    def test_a_code_the_ledger_never_heard_of_keeps_the_snapshot_value(self):
        """账本里没有这个番号的资产，就没有「现值」可问，别把有值的改成空。"""
        self.write_metadata_rows([
            {"item_key": "GHOST:studio", "field": "studio", "current": "Prestige",
             "candidates": ["Faleno"], "code": "GHOST-1"},
        ])
        self.assertEqual(self.queue_row("metadata_fields", "GHOST:studio")["current_value"],
                         "Prestige")

    def test_performer_avatar_rows_show_the_ledger_name_not_the_scraped_romaji(self):
        """候选 CSV 给的是罗马音，账本早就有更好的名字，罗马音本身也已是别名。"""
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(40,'performer','释爱丽丝','释爱丽丝','2026-01-01','2026-01-01')")
        con.commit(); con.close()
        path = self.candidates / "performer-avatar-candidate-20260818.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["entity_id", "current_name", "assets", "verdict"])
            writer.writeheader()
            writer.writerow({"entity_id": "40", "current_name": "Alice Shaku",
                             "assets": "3", "verdict": "ok"})
        rows, _source, _skipped = rm_review._review_rows(self.contract, "performer_avatars")
        self.assertEqual(rows[0]["current_name"], "释爱丽丝")
        # 来源写法不能丢，降为副标题。
        self.assertEqual(rows[0]["source_name"], "Alice Shaku")

    def test_decided_rows_leave_the_queue_and_skipped_ones_sink(self):
        """判过的不能一刷新又回来。

        `_review_rows` 原样返回全部候选、只挂一个 `decision`、靠前端在本地 splice
        的话，点「通过」当场消失、刷新全回来（厂牌 logo 上最明显）。
        `跳过` 是「稍后再看」，仍留在队列但排到最后——否则一次跳过等于永久隐藏，
        而界面上没有任何入口能把它找回来。
        """
        self.write_candidates("creator-tags-candidate-20260818.csv", [
            {"board": "a", "creator": "ukiru", "tags": "x", "status": "candidate"},
            {"board": "b", "creator": "ukiru", "tags": "y", "status": "candidate"},
            {"board": "c", "creator": "ukiru", "tags": "z", "status": "candidate"},
        ])
        self.assertEqual(self.queue_keys("creator_tags"), ["a", "b", "c"])
        self.decide("creator_tags", "b", "rejected")
        self.assertEqual(self.queue_keys("creator_tags"), ["a", "c"])
        self.decide("creator_tags", "a", "skipped")
        self.assertEqual(self.queue_keys("creator_tags"), ["c", "a"])

    def test_approving_a_studio_logo_actually_installs_it(self):
        """批准必须真的把图装进 `/logo` 读的目录。

        `studio_logos` 此前只在分类白名单里，没有写入分支：点通过只往
        review_decision 记一笔，logo 一张也没装上。
        """
        source_dir = self.candidates / "studio-logos"
        source_dir.mkdir()
        (source_dir / "Deep_s.png").write_bytes(b"PNGDATA")
        # `saved` 列写的是旧数据根 R:\peach-data\...，本机上并不存在，
        # 必须按文件名在当前候选目录里解析，否则批准永远失败。
        sep = chr(92)
        stale = sep.join(["R:", "peach-data", "generated", "studio-logos", "Deep_s.png"])
        self.write_logo_candidates([
            {"studio": "Deep's", "handle": "deeps_official", "platform": "x",
             "resolved_url": "https://example.invalid/a.png", "saved": stale,
             "accepted": "True"},
        ])
        result = self.decide("studio_logos", "Deep's", "approved")
        self.assertTrue(result["ok"])
        self.assertEqual(result["applied_assets"], 1)
        # 落盘名必须和 PreviewService.logo 的规则一致，否则 /logo 读不到。
        installed = self.contract.logo_root / "Deep_s.img"
        self.assertEqual(installed.read_bytes(), b"PNGDATA")
        self.assertEqual(
            (self.contract.logo_root / "Deep_s.img.ct").read_text(encoding="utf-8"),
            "image/png")
        self.assertIn("deeps_official", (
            self.contract.logo_root / "Deep_s.img.provenance.json").read_text(encoding="utf-8"))
        # 装完就该离开队列。
        self.assertEqual(self.queue_keys("studio_logos"), [])

    def test_studio_logo_approval_refuses_when_the_image_is_not_on_this_machine(self):
        self.write_logo_candidates([
            {"studio": "Ghost", "handle": "h", "platform": "x", "resolved_url": "",
             "saved": "Ghost.png", "accepted": "True"},
        ])
        with self.assertRaises(ValueError):
            self.decide("studio_logos", "Ghost", "approved")

    def test_logo_queue_excludes_empty_and_unchanged_but_reopens_changed_source(self):
        fields = ["studio", "resolved_url", "saved", "accepted", "confirmation",
                  "content_state", "reason"]
        self._csv("studio-logo-candidate-20260825.csv", fields, [
            {"studio": "No Handle", "saved": "", "accepted": "False",
             "confirmation": "no-handle", "content_state": "no_handle"},
            {"studio": "Same", "saved": "Same.png", "accepted": "False",
             "confirmation": "confirmed-handle", "content_state": "unchanged"},
            {"studio": "Changed", "saved": "Changed.png", "accepted": "True",
             "confirmation": "confirmed-handle", "content_state": "changed",
             "resolved_url": "https://x/changed.png"},
        ])
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO review_decision(category,item_key,status,updated_at) "
            "VALUES('studio_logos','Changed','approved','old')"
        )
        con.commit(); con.close()
        rows = rm_review.q_review(self.contract)["sections"]["studio_logos"]
        self.assertEqual([row["studio"] for row in rows], ["Changed"])
        self.assertEqual(rows[0]["decision"], "pending")

    def _decide_with_note(self, item_key, note):
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
            "VALUES('metadata_fields',?,'approved',?,'old')", (item_key, note))
        con.commit(); con.close()

    def test_an_approval_of_a_vanished_candidate_reopens_the_field(self):
        """`item_key` 不带候选身份，旧批准不得盖住后来抓到的新来源值。

        实测：TRE-080 的标题在 2026-09-01 对着 r18dev 的空日文标题批过一次，
        之后 javbus 抓到真标题，队列里却一条也看不见。
        """
        self.write_metadata_rows([{
            "item_key": "ABC-001:title", "code": "ABC-001", "field": "title",
            # 来源不能是兜底那一家：兜底来源挑战账本已有的值已经不进队列（ADR-0038），
            # 这几条用例问的是别的事，拿 javbus 当素材会让它们对着空队列断言。
            "current": "English Title", "candidates": ["日本語タイトル"], "source": "javdb",
        }])
        self._decide_with_note(
            "ABC-001:title",
            '{"candidate_key":"ABC-001:title:r18dev:gone","source":"r18dev","user_note":""}')

        rows = rm_review.q_review(self.contract)["sections"]["metadata_fields"]
        self.assertEqual([row["item_key"] for row in rows], ["ABC-001:title"])
        self.assertEqual(rows[0]["decision"], "pending")

    def test_an_approval_still_pointing_at_a_live_candidate_stays_decided(self):
        self.write_metadata_rows([{
            "item_key": "ABC-001:title", "code": "ABC-001", "field": "title",
            # 来源不能是兜底那一家：兜底来源挑战账本已有的值已经不进队列（ADR-0038），
            # 这几条用例问的是别的事，拿 javbus 当素材会让它们对着空队列断言。
            "current": "English Title", "candidates": ["日本語タイトル"], "source": "javdb",
        }])
        self._decide_with_note(
            "ABC-001:title",
            '{"candidate_key":"ABC-001:title:0","source":"javbus","user_note":""}')

        # 判过的行不占队列，所以「仍然算已判」的观测形态就是它不在队列里。
        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_a_free_text_note_is_left_alone_rather_than_guessed_at(self):
        """早期留痕是自由文本，读不出指向哪个候选就别把用户批过的翻出来。"""
        self.write_metadata_rows([{
            "item_key": "ABC-001:title", "code": "ABC-001", "field": "title",
            # 来源不能是兜底那一家：兜底来源挑战账本已有的值已经不进队列（ADR-0038），
            # 这几条用例问的是别的事，拿 javbus 当素材会让它们对着空队列断言。
            "current": "English Title", "candidates": ["日本語タイトル"], "source": "javdb",
        }])
        self._decide_with_note("ABC-001:title", "手工核过，就用这个")

        self.assertEqual(self.queue_keys("metadata_fields"), [])

    def test_metadata_field_approval_uses_selected_candidate_and_never_writes_creator(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001',creator='Folder Creator' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:performers:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "provider_id": "ABC-001",
            "provider_id": "ABC-001", "content_id": "abc00001",
            "value": [{"name": "木村さん", "external_id": "7", "thumb_url": ""}],
            "display_value": "木村さん", "warnings": [], "raw_snapshot": "/evidence.json",
            "catalog_evidence": {
                "title": {"value": "来源标题", "display_value": "来源标题", "warnings": []},
                "label": {"value": "Label A", "display_value": "Label A", "warnings": []},
            },
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:performers", "code": "ABC-001", "query": "ABC-001",
            "field": "performers", "field_label": "演员", "current_value": "",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        queue = rm_review.q_review(self.contract)["sections"]["metadata_fields"]
        self.assertEqual(queue[0]["candidates"][0]["display_value"], "木村さん")
        self.assertEqual(
            queue[0]["candidates"][0]["catalog_evidence"]["label"]["value"], "Label A",
        )
        result = rm_review.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:performers",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT creator FROM asset WHERE id=1").fetchone()[0], "Folder Creator")
        self.assertEqual(con.execute("SELECT name FROM asset WHERE id=1").fetchone()[0], "1.mp4")
        self.assertEqual(con.execute(
            "SELECT e.kind,e.canonical_name,ae.role FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=1 AND ae.role='performer'"
        ).fetchall(), [("performer", "木村さん", "performer")])
        self.assertEqual(con.execute(
            "SELECT tag FROM asset_tag WHERE asset_id=1 AND source='javinizer:r18dev:performer'"
        ).fetchall(), [("演员:木村さん",)])
        self.assertEqual(con.execute(
            "SELECT provider,external_id FROM entity_external_ref"
        ).fetchall(), [("r18dev", "7")])
        note = con.execute(
            "SELECT note FROM review_decision WHERE category='metadata_fields'"
        ).fetchone()[0]
        con.close()
        self.assertEqual(json.loads(note)["candidate_key"], candidate["candidate_key"])

    def test_metadata_release_date_approval_writes_the_date_field(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:release_date:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "provider_id": "ABC-001",
            "value": "2020-09-13", "display_value": "2020-09-13", "warnings": [],
            "raw_snapshot": "/evidence.json",
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:release_date", "code": "ABC-001", "query": "ABC-001",
            "field": "release_date", "field_label": "发行日期", "current_value": "",
            "candidates_json": json.dumps([candidate]), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        result = rm_review.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:release_date",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT release_date FROM asset WHERE id=1").fetchone()[0], "2020-09-13")
        con.close()

    def test_metadata_tag_approval_writes_tags_for_detail_consumers(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.execute(
            "INSERT INTO asset_tag(asset_id,tag,confidence,source) "
            "VALUES(1,'乳系',0.4,'filename')"
        )
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:tags:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "provider_id": "ABC-001",
            "value": ["乳系", "颜射"], "display_value": "乳系、颜射", "warnings": [],
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:tags", "code": "ABC-001", "query": "ABC-001",
            "field": "tags", "field_label": "标签", "current_value": "",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        result = rm_review.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:tags",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT tag,confidence,source FROM asset_tag WHERE asset_id=1 ORDER BY tag"
        ).fetchall(), [
            ("乳系", 0.9, "javinizer:r18dev:tag"),
            ("颜射", 0.9, "javinizer:r18dev:tag"),
        ])
        con.close()

    def test_specific_official_tag_replaces_broad_taste_tag_everywhere(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(50,'tag','乳系','乳系','2026-01-01','2026-01-01')")
        con.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                    "VALUES(1,50,'tag','vision_creator',0.6)")
        con.execute("INSERT INTO asset_tag(asset_id,tag,confidence,source) "
                    "VALUES(1,'乳系',0.6,'vision_creator')")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:tags:r18dev:specific", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "provider_id": "ABC-001",
            "value": ["乳系", "美乳", "颜射"], "display_value": "乳系、美乳、颜射",
            "warnings": [],
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:tags", "code": "ABC-001", "query": "ABC-001",
            "field": "tags", "field_label": "标签", "current_value": "乳系",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])

        result = rm_review.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:tags",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT tag FROM asset_tag WHERE asset_id=1 ORDER BY tag"
        ).fetchall(), [("美乳",), ("颜射",)])
        self.assertEqual(con.execute(
            "SELECT e.canonical_name FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=1 AND ae.role='tag' ORDER BY e.canonical_name"
        ).fetchall(), [("美乳",), ("颜射",)])
        con.close()

    def test_metadata_title_approval_writes_catalog_title(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:title:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "provider_id": "ABC-001",
            "value": "正式作品标题", "display_value": "正式作品标题", "warnings": [],
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:title", "code": "ABC-001", "query": "ABC-001",
            "field": "title", "field_label": "标题", "current_value": "",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        result = rm_review.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:title",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT catalog_title FROM asset WHERE id=1"
        ).fetchone()[0], "正式作品标题")
        con.close()

    def test_metadata_approval_rejects_repeated_name_even_if_csv_is_tampered(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "bad", "source": "r18dev", "confidence": 0.9,
            "value": [{"name": "木村さん 木村さん", "external_id": "7"}],
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:performers", "code": "ABC-001", "query": "ABC-001",
            "field": "performers", "field_label": "演员", "current_value": "",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        with self.assertRaises(ValueError):
            rm_review.w_review_decision(self.contract, {
                "category": "metadata_fields", "item_key": "ABC-001:performers",
                "candidate_key": "bad", "status": "approved",
            })
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT count(*) FROM review_decision WHERE category='metadata_fields'"
        ).fetchone()[0], 0)
        con.close()

    def test_latest_batch_is_used_instead_of_a_hardcoded_date(self):
        """候选文件名带批次日期；把日期写死在源码里会让下一批生成后页面静默变空。"""
        self.write_candidates("creator-tags-candidate-20260101.csv",
                              [{"board": "old", "creator": "ukiru", "tags": "旧", "status": "candidate"}])
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "new", "creator": "ukiru", "tags": "新", "status": "candidate"}])
        rows, source, _ = rm_review.read_candidates("creator_tags", self.candidates)
        self.assertEqual(source, "creator-tags-candidate-20260817.csv")
        self.assertEqual([row["item_key"] for row in rows], ["new"])

    def test_rows_without_a_stable_key_are_dropped_and_counted(self):
        """缺主键的行绝不能退化成行号：CSV 一重排，历史决定就挪到别的条目上了。"""
        self.write_candidates("creator-tags-candidate-20260817.csv", [
            {"board": "", "creator": "ukiru", "tags": "足系", "status": "candidate"},
            {"board": "ok", "creator": "ukiru", "tags": "足系", "status": "candidate"},
        ])
        rows, _, skipped = rm_review.read_candidates("creator_tags", self.candidates)
        self.assertEqual([row["item_key"] for row in rows], ["ok"])
        self.assertEqual(skipped, 1)

    def test_approval_takes_creator_and_tags_from_the_candidate_not_the_body(self):
        """否则「批准候选 X」能写入与 X 无关的标签，而留痕仍写着 X 通过。"""
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        with self.assertRaises(ValueError):
            rm_review.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "b1", "status": "approved",
                "creator": "别的创作者", "tags": "伪造标签",
            })
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM review_decision").fetchone()[0], 0)
        con.close()

    def test_approval_refuses_candidates_outside_the_current_batch(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        with self.assertRaises(ValueError):
            rm_review.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "已消失的候选", "status": "approved",
            })

    def test_skip_candidate_cannot_be_approved(self):
        """机械批次明确跳过的聚合目录不能从复核页误批准回真相层。"""
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "skip"}])
        with self.assertRaises(ValueError):
            rm_review.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "b1", "status": "approved",
            })
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM review_decision").fetchone()[0], 0)
        con.close()

    def test_unselected_approval_is_capped_instead_of_tagging_everything(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        with mock.patch.object(rm_review, "REVIEW_APPLY_LIMIT", 2):
            with self.assertRaises(ValueError) as caught:
                rm_review.w_review_decision(self.contract, {
                    "category": "creator_tags", "item_key": "b1", "status": "approved",
                })
        self.assertIn("显式勾选", str(caught.exception))
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 0)
        con.close()

    def test_approval_writes_both_projections_and_reports_the_real_count(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系|素人", "status": "candidate"}])
        result = rm_review.w_review_decision(self.contract, {
            "category": "creator_tags", "item_key": "b1", "status": "approved",
            "creator": "ukiru", "tags": "足系|素人",
        })
        self.assertEqual(result["applied_assets"], 3)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 6)
        self.assertEqual(con.execute(
            "SELECT count(*) FROM asset_entity WHERE role='tag'").fetchone()[0], 6)
        self.assertEqual(con.execute(
            "SELECT status FROM review_decision WHERE item_key='b1'").fetchone()[0], "approved")
        con.close()

    def test_selected_ids_must_belong_to_the_reviewed_creator(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO asset(id,location,path,name,medium) "
                    "VALUES(99,'local','/x/99.mp4','99.mp4','video')")
        con.commit(); con.close()
        with self.assertRaises(ValueError):
            rm_review.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "b1", "status": "approved",
                "selected_ids": [1, 99],
            })

    def _csv(self, name, fields, rows):
        path = self.candidates / name
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        return path

    def test_identity_samples_include_unpictured_files_and_exclude_trash(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("UPDATE asset SET snapshot_path=NULL WHERE id=2")
            connection.execute("UPDATE asset SET disposal='trash' WHERE id=3")
        connection.close()
        self._csv("babepedia-candidates.csv", ["entity_id", "creator", "videos", "verdict"],
                  [{"entity_id": "1", "creator": "ukiru", "videos": "2", "verdict": "命中"}])
        row = rm_review.q_review(self.contract)["sections"]["western_identity"][0]
        self.assertEqual([asset["id"] for asset in row["preview_assets"]], [1, 2])
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            pictured = rm_review._creator_previews(connection, ["ukiru"])
        connection.close()
        self.assertEqual([asset["id"] for asset in pictured["ukiru"]], [1])

    def test_settled_western_identity_rows_stay_out_of_the_queue(self):
        # 168 条里 143 条是「确认无档案」，站上确实没有这个人，没有可判断的东西。
        fields = ["entity_id", "creator", "videos", "verdict", "matched_variant",
                  "babepedia_name", "token_overlap", "portrait_url", "profile_url"]
        self._csv("babepedia-candidates.csv", fields, [
            {"entity_id": "1", "creator": "ruth_lee", "videos": "336", "verdict": "命中",
             "matched_variant": "ruth_lee", "babepedia_name": "Ruth Lee",
             "token_overlap": "1.0", "portrait_url": "https://x/p.jpg", "profile_url": ""},
            {"entity_id": "2", "creator": "minhie", "videos": "17", "verdict": "需人工确认",
             "matched_variant": "minhie", "babepedia_name": "Aryminh",
             "token_overlap": "0.0", "portrait_url": "", "profile_url": ""},
            {"entity_id": "3", "creator": "luckydog22", "videos": "496",
             "verdict": "确认无档案", "matched_variant": "", "babepedia_name": "",
             "token_overlap": "0.0", "portrait_url": "", "profile_url": ""},
        ])
        rows = rm_review.q_review(self.contract)["sections"]["western_identity"]
        self.assertEqual({r["creator"] for r in rows}, {"ruth_lee", "minhie"})

    def test_western_identity_rows_carry_a_readable_evidence_line(self):
        fields = ["entity_id", "creator", "videos", "verdict", "matched_variant",
                  "babepedia_name", "token_overlap", "portrait_url"]
        self._csv("babepedia-candidates.csv", fields, [
            {"entity_id": "1", "creator": "SexySaffron", "videos": "357", "verdict": "命中",
             "matched_variant": "Sexy Saffron", "babepedia_name": "Saffron Bacchus",
             "token_overlap": "0.33", "portrait_url": "https://x/s.jpg"}])
        row = rm_review.q_review(self.contract)["sections"]["western_identity"][0]
        self.assertIn("Saffron Bacchus", row["reason"])
        self.assertIn("写法 Sexy Saffron", row["reason"], "别名跳转必须写明用了哪个写法")
        self.assertEqual(row["preview_url"], "https://x/s.jpg")

    def test_review_rows_say_up_front_whether_the_face_can_be_fetched(self):
        """复核卡片那张脸和别处一样先问再出图，只是这里没有代表作可退。

        这两类的卡片左边直接按 `entity_id` 取 `/entity-image`；没有标志就只能无条件
        出图、等 404 再把图摘掉。落盘名带 kind，所以判定必须按 `ENTITY_REVIEW_KINDS`
        说的那种实体去找，不能凭卡片长得像谁猜。
        """
        self._csv("babepedia-candidates.csv",
                  ["entity_id", "creator", "videos", "verdict", "matched_variant",
                   "babepedia_name", "token_overlap", "portrait_url"],
                  [{"entity_id": "1", "creator": "ukiru", "videos": "3", "verdict": "命中",
                    "matched_variant": "ukiru", "babepedia_name": "Ukiru",
                    "token_overlap": "1.0", "portrait_url": ""}])
        self.write_candidates("creator-tags-candidate-20260818.csv", [
            {"board": "a", "creator": "ukiru", "tags": "x", "status": "candidate"},
            {"board": "b", "creator": "查无此人", "tags": "y", "status": "candidate"},
        ])

        def faces(category):
            rows = rm_review.q_review(self.contract)["sections"][category]
            return {row["item_key"]: row["has_image"] for row in rows}

        self.assertEqual(faces("creator_tags"), {"a": False, "b": False})
        self.assertEqual(faces("western_identity"), {"1": False})
        # 写成 performer 的名字读不到：kind 是落盘名的一部分。
        (self.avatar_root / "performer-1.img").write_bytes(b"\xff\xd8\xff\xd9")
        self.contract.cache_bust()
        self.assertEqual(faces("creator_tags"), {"a": False, "b": False})
        (self.avatar_root / "creator-1.img").write_bytes(b"\xff\xd8\xff\xd9")
        self.contract.cache_bust()
        # 解析到实体 1 的那行有了图，名字对不上账本的那行仍然没有身份、没有图。
        self.assertEqual(faces("creator_tags"), {"a": True, "b": False})
        self.assertEqual(faces("western_identity"), {"1": True})
        # 不在表里的类别没有这个位置，别给它凭空挂一个标志。
        path = self.candidates / "performer-avatar-candidate-20260818.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["entity_id", "current_name", "assets", "verdict"])
            writer.writeheader()
            writer.writerow({"entity_id": "1", "current_name": "ukiru",
                             "assets": "3", "verdict": "ok"})
        rows = rm_review.q_review(self.contract)["sections"]["performer_avatars"]
        self.assertTrue(rows)
        self.assertNotIn("has_image", rows[0])

    def test_record_only_review_categories_can_be_decided(self):
        result = rm_review.w_review_decision(self.contract, {
            "category": "western_identity", "item_key": "1", "status": "skipped",
        })
        self.assertTrue(result["ok"])
        self.assertEqual(result["applied_assets"], 0)

    def test_cover_fetch_status_never_becomes_manual_review_work(self):
        fields = ["code", "result", "source", "width", "height", "kb", "url", "note"]
        self._csv("cover-fetch-log.csv", fields, [
            {"code": "BAZX-302", "result": "取得", "source": "awsimgsrc.dmm.co.jp",
             "width": "2184", "height": "1459", "kb": "1065", "url": "u", "note": ""},
            {"code": "PPT-018", "result": "取得", "source": "pics.dmm.co.jp",
             "width": "800", "height": "539", "kb": "165", "url": "u", "note": ""},
            {"code": "HEYZO-1380", "result": "未取得", "source": "", "width": "",
             "height": "", "kb": "", "url": "", "note": "所有渠道都没有候选"},
        ])
        rows = rm_review.q_review(self.contract)["sections"]["cover_sources"]
        self.assertEqual(rows, [], "封面成功、尺寸和缺失都由机械状态处理")

    def test_metadata_review_links_back_to_one_original_asset(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.commit(); con.close()
        self.write_metadata_candidates([{
            "item_key": "ABC-001:tags", "code": "ABC-001", "query": "ABC-001",
            "field": "tags", "field_label": "标签", "current_value": "",
            "candidates_json": "[]", "source_count": "1", "status": "candidate",
            "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        row = rm_review.q_review(self.contract)["sections"]["metadata_fields"][0]
        self.assertEqual(row["asset_id"], 1)
        self.assertEqual(row["asset_name"], "1.mp4")

    FC2_FIELDS = ["code", "video_id", "result", "title", "release_date", "duration",
                  "censored", "writer", "writer_slug", "tags", "performers",
                  "performer_votes", "is_collection", "collection_parts",
                  "equivalents", "cover_url", "note"]

    def _fc2_row(self, code, **over):
        row = {field: "" for field in self.FC2_FIELDS}
        row.update({"code": code, "video_id": code.split("-")[-1], "result": "取得"})
        row.update(over)
        return row

    def test_fc2_markings_only_surface_rows_that_carry_a_marking(self):
        """FC2 大多数作品页评论区是空的，全列出来会淹掉真正有标记的那几十条。"""
        self._csv("fc2-candidate-log.csv", self.FC2_FIELDS, [
            self._fc2_row("FC2-PPV-2355314", performers="真夏",
                          performer_votes="真夏:2"),
            self._fc2_row("FC2-PPV-3701252", equivalents="2407240"),
            self._fc2_row("FC2-PPV-3788093"),
            self._fc2_row("FC2-PPV-4078398", result="未取得", note="连接失败"),
        ])
        rows = rm_review.q_review(self.contract)["sections"]["fc2_markings"]
        self.assertEqual({r["code"] for r in rows},
                         {"FC2-PPV-2355314", "FC2-PPV-3701252"})

    def test_fc2_evidence_line_shows_how_many_comments_agree(self):
        self._csv("fc2-candidate-log.csv", self.FC2_FIELDS, [
            self._fc2_row("FC2-PPV-2355314", performers="真夏",
                          performer_votes="真夏:2", writer="陸王24")])
        row = rm_review.q_review(self.contract)["sections"]["fc2_markings"][0]
        self.assertIn("真夏:2", row["reason"], "票数是这批候选唯一的置信度信号")
        self.assertIn("陸王24", row["reason"])

    def test_a_collection_says_its_cover_is_withheld(self):
        """合集封面套给每个分片会让 21 段不同内容显示同一张图。"""
        self._csv("fc2-candidate-log.csv", self.FC2_FIELDS, [
            self._fc2_row("FC2PPV-3312576", is_collection="1",
                          collection_parts="19", cover_url="")])
        row = rm_review.q_review(self.contract)["sections"]["fc2_markings"][0]
        self.assertIn("19 个分片", row["reason"])
        self.assertIn("封面不下发", row["reason"])

    def test_fc2_cross_number_similarity_is_a_record_only_review_candidate(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='FC2-PPV-1083921' WHERE id=1")
        con.execute(
            "INSERT INTO asset(id,location,path,name,medium,code,duration,snapshot_path) "
            "VALUES(4,'local',?,'right.mp4','video','FC2-PPV-1384193',100,'r.jpg')",
            (r"R:\Media\right.mp4",),
        )
        con.commit(); con.close()
        fields = ["pair_key", "code", "left_code", "right_code", "evidence_kinds",
                  "duration_delta_seconds", "size_delta_percent", "shared_performers",
                  "left_asset_id", "right_asset_id", "warnings", "reason", "status"]
        self._csv("fc2-similarity-candidate-20260825.csv", fields, [{
            "pair_key": "1083921|1384193", "code": "FC2-PPV-1083921",
            "left_code": "FC2-PPV-1083921", "right_code": "FC2-PPV-1384193",
            "evidence_kinds": "comment_equivalent media_similarity",
            "duration_delta_seconds": "1.2", "size_delta_percent": "0.5",
            "shared_performers": "真夏", "warnings": "匿名评论等价标记只作候选",
            "left_asset_id": "1", "right_asset_id": "4",
            "reason": "", "status": "candidate",
        }])
        row = rm_review.q_review(self.contract)["sections"]["fc2_similarity"][0]
        self.assertEqual(row["item_key"], "1083921|1384193")
        self.assertEqual(row["asset_id"], 1)
        self.assertEqual([asset["id"] for asset in row["comparison_assets"]], [1, 4])
        self.assertEqual(row["comparison_assets"][1]["preview_url"], "/poster?id=4&c=4")
        self.assertIn("comment_equivalent", row["reason"])
        self.assertIn("时长差 1.2 秒", row["reason"])
        result = rm_review.w_review_decision(self.contract, {
            "category": "fc2_similarity", "item_key": row["item_key"],
            "status": "skipped",
        })
        self.assertEqual(result["applied_assets"], 0)

    def test_endcard_candidate_links_ocr_frame_and_original_video(self):
        fields = ["candidate_key", "asset_id", "name", "sample_kind",
                  "timestamp_seconds", "frame_key", "ocr_text", "verdict",
                  "detected_urls", "confidence", "reason", "status"]
        self._csv("video-endcard-candidate-20260825.csv", fields, [{
            "candidate_key": "1", "asset_id": "1", "name": "1.mp4",
            "sample_kind": "tail", "timestamp_seconds": "98",
            "frame_key": "1/tail-000098000.png",
            "ocr_text": "Full version available on: fansly.com/example",
            "verdict": "incomplete_candidate", "detected_urls": "fansly.com/example",
            "confidence": "0.98", "reason": "片尾明确写有 Full version available",
            "status": "candidate",
        }])
        row = rm_review.q_review(self.contract)["sections"]["video_endcards"][0]
        self.assertEqual(row["item_key"], "1")
        self.assertEqual(row["asset_id"], 1)
        self.assertEqual(
            row["preview_url"],
            "/endcard-frame?id=1&name=tail-000098000.png",
        )
        result = rm_review.w_review_decision(self.contract, {
            "category": "video_endcards", "item_key": "1", "status": "skipped",
        })
        self.assertEqual(result["applied_assets"], 0)

    def _code_creator(self, entity_id, name, assets):
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,"
                    "created_at,updated_at) VALUES(?,'creator',?,?,'2026-01-01','2026-01-01')",
                    (entity_id, name, name.casefold()))
        for asset_id, asset_name, path in assets:
            con.execute("INSERT INTO asset(id,location,path,name,medium,creator) "
                        "VALUES(?,'local',?,?,'video',?)", (asset_id, path, asset_name, name))
            con.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                        "VALUES(?,?,'creator','legacy:asset',1.0)", (asset_id, entity_id))
        con.commit(); con.close()

    def test_code_creator_queue_is_computed_from_the_ledger(self):
        """这一类没有候选文件，队列按当前账本现算。

        读 CSV 那份是跑脚本当时的快照：44 行里 27 行的实体后来被清掉了，点进去无事
        可做，而真正该看的只有 24 条。判据的输入本来就只有账本，没有要留存的外部证据。
        """
        self._code_creator(6869, "banbi_555", [
            (101, "18歳Eカップ彼氏持ち美女.mp4", r"A:\Pack From Shared\pen\banbi_555\18歳.mp4")])
        rows = rm_review.q_review(self.contract)["sections"]["code_creators"]
        self.assertEqual([row["item_key"] for row in rows], ["6869"])
        self.assertEqual(rows[0]["verdict"], "存疑")
        self.assertIn("没有同番号文件", rows[0]["reason"])

    def test_a_cleaned_up_creator_leaves_the_queue_on_its_own(self):
        """清理过的行不该靠重跑脚本刷 CSV 才消失。"""
        self._code_creator(6870, "HD-abp-758", [
            (102, "HD-abp-758.mp4", r"B:\云下载\HD-abp-758\HD-abp-758.mp4")])
        self.assertEqual(
            [row["item_key"] for row in
             rm_review.q_review(self.contract)["sections"]["code_creators"]], ["6870"])

        con = sqlite3.connect(self.db_path)
        con.execute("DELETE FROM asset_entity WHERE entity_id=6870")
        con.execute("DELETE FROM entity WHERE id=6870")
        con.commit(); con.close()
        self.assertEqual(
            rm_review.q_review(self.contract)["counts"]["code_creators"], 0)


class PerformerAvatarApplyTests(ReviewQueueTests):
    """批准人物头像候选必须真的把图装上。

    这个缺陷犯到第三次了：`creator_tags` 犯过（留痕说通过、实际没写），
    `studio_logos` 犯过（只在白名单里、没有写入分支），`performer_avatars` 一模一样。
    审计脚本按设计只把外部图放进内容寻址缓存，落地要人批准；而批准这一步什么也没做，
    于是 18 个已判 ok 的候选从 2026-08-25 起一直进不去。

    落盘名跟着实体 kind 走（`{kind}-{id}.img`）：`/entity-image` 按 kind 分文件，
    creator 实体（babepedia 命中的西方网黄）装成 performer-<id>.img 永远读不到。
    基建的 entity 1 是 creator（creator_tags 测试要用），这里整体拨回 performer，
    creator 的落盘另用一条独立用例锁住。
    """

    FIELDS = ("entity_id", "current_name", "matched_name", "name_source", "provider",
              "source_url", "external_id", "width", "height", "mime_type", "sha256",
              "cache_path", "verdict")

    def setUp(self):
        super().setUp()
        con = sqlite3.connect(self.db_path)
        # 基建的 entity 1 留给 creator_tags 用例；头像落盘另立 performer 9。
        # 名字不能与父类用例插入的「释爱丽丝」撞 UNIQUE(kind, normalized_name)。
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(9,'performer','示例女优','示例女优','2026-01-01','2026-01-01')")
        con.commit(); con.close()

    def _seed(self, *, verdict="ok", body=b"\xff\xd8\xff\xdb-fake-jpeg", digest=None,
              entity_id="9", provider_dir="gfriends"):
        import hashlib
        real = hashlib.sha256(body).hexdigest()
        objects = (self.candidates / "provider-cache" / "performer-avatars"
                   / provider_dir / "objects")
        objects.mkdir(parents=True, exist_ok=True)
        (objects / f"{real}.jpg").write_bytes(body)
        path = self.candidates / "performer-avatar-candidate-20260901-000000.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(self.FIELDS))
            writer.writeheader()
            writer.writerow({
                "entity_id": entity_id, "current_name": "释爱丽丝",
                "matched_name": "釈アリス",
                "name_source": "localization_jp", "provider": provider_dir,
                "source_url": "https://example.invalid/x.jpg", "external_id": "5-Premium/x.jpg",
                "width": "648", "height": "800", "mime_type": "image/jpeg",
                "sha256": digest or real, "cache_path": digest or real, "verdict": verdict,
            })
        return real

    def _decide(self, status="approved", item_key="9"):
        return rm_web.w_review_decision(self.contract, {
            "category": "performer_avatars", "item_key": item_key, "status": status,
        })

    def test_approving_installs_the_image_where_entity_image_reads_it(self):
        body = b"\xff\xd8\xff\xdb-fake-jpeg"
        self._seed(body=body)
        result = self._decide()
        self.assertEqual(result["applied_assets"], 1)
        target = self.avatar_root / "performer-9.img"
        self.assertTrue(target.is_file(), "批准之后图必须真的装上，而不是只记一笔决定")
        self.assertEqual(target.read_bytes(), body)
        self.assertEqual(Path(f"{target}.ct").read_text(encoding="utf-8"), "image/jpeg")
        prov = json.loads(Path(f"{target}.provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["matched_name"], "釈アリス")
        self.assertEqual(prov["name_source"], "localization_jp")

    def test_a_creator_candidate_installs_where_creator_images_are_read(self):
        """creator 实体的头像必须落成 creator-<id>.img。

        babepedia 命中的西方网黄全是 creator 实体；`/entity-image` 按 kind 分文件，
        装成 performer-<id>.img 谁也读不到——同样的字节，两份都「装了」，界面上
        依旧是视频抽帧兜底。
        """
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
                    "VALUES(2,'creator','SexySaffron','sexysaffron','2026-01-01','2026-01-01')")
        con.commit(); con.close()
        body = b"\xff\xd8\xff\xdb-other-jpeg"
        self._seed(body=body, entity_id="2", provider_dir="babepedia")
        result = self._decide(item_key="2")
        self.assertEqual(result["applied_assets"], 1)
        self.assertTrue((self.avatar_root / "creator-2.img").is_file())
        self.assertFalse((self.avatar_root / "performer-2.img").exists())

    def test_the_face_sidecar_follows_the_image_it_describes(self):
        """装上新图之后，边上不能还留着别的图的脸框。

        圆头像按 `<kind>-<id>.face.json` 里那张脸摆位，没有 sidecar 就几何居中。
        顶掉一张旧头像时若把旧 sidecar 留在原地，页面会拿上一张图的脸框给这一张取景、
        放大到一个空位置上——而这在界面上与「这张图本来就该这么显示」看不出区别。

        这里的候选是几个字节的假 JPEG，检出器解不开，所以正确结果是没有 sidecar；
        真图检出人脸时写进去的形状由 `peach.avatar_face` 自己的用例锁住。
        """
        target = self.avatar_root / "performer-9.img"
        target.parent.mkdir(parents=True, exist_ok=True)
        stale = target.with_suffix(".face.json")
        stale.write_text('{"ratio": 0.8, "px": [100, 125], '
                         '"face": {"cx": 0.5, "cy": 0.2, "w": 0.4, "h": 0.4, "score": 0.9}, '
                         '"focus": {"axis": "y", "pct": 0}}', encoding="utf-8")
        self._seed(body=b"\xff\xd8\xff\xdb-replacement")
        self.assertEqual(self._decide()["applied_assets"], 1)
        self.assertFalse(stale.exists(), "检不出脸就该没有 sidecar，不能留着上一张图的脸框")

    def test_a_candidate_that_did_not_pass_quality_is_refused(self):
        self._seed(verdict="rejected")
        with self.assertRaisesRegex(ValueError, "ok"):
            self._decide()
        self.assertFalse((self.avatar_root / "performer-9.img").exists())

    def test_a_hash_that_does_not_match_the_cached_bytes_is_refused(self):
        """内容寻址的意义就在于不必相信路径。

        候选 CSV 里的 cache_path 只是哈希名，缓存目录可能被别的批次覆写；装载前
        重算一遍，对不上就拒绝，而不是把一张来历不明的图装成这个人的头像。
        """
        self._seed(digest="0" * 64)
        with self.assertRaisesRegex(ValueError, "缓存"):
            self._decide()
        self.assertFalse((self.avatar_root / "performer-9.img").exists())

    def test_rejecting_records_the_decision_without_installing(self):
        self._seed()
        result = self._decide(status="rejected")
        self.assertEqual(result["applied_assets"], 0)
        self.assertFalse((self.avatar_root / "performer-9.img").exists())

    def test_every_approvable_category_can_land(self):
        """每个能被批准的类别，要么有落地分支，要么明确声明只记决定。

        `w_review_decision` 的落地分支是一条条手写的，把类别加进白名单却忘了写分支，
        表现就是「点通过、什么也没发生」——这个组合最糟：留痕说通过、实际没写。
        已经犯过三次，所以这里不再靠人记。
        """
        source = pathlib.Path(rm_review.__file__).read_text(encoding="utf-8")
        block = source.split("if category not in {", 1)[1].split("}", 1)[0]
        whitelist = set(re.findall(r'"(\w+)"', block))
        self.assertGreaterEqual(len(whitelist), 10, "没解析到分类白名单，门槛会空转")
        lands = set(re.findall(r'elif category == "(\w+)" and status == "approved"', source))
        lands |= set(re.findall(r'if category == "(\w+)" and status == "approved"', source))
        declared = set(rm_review.DECISION_ONLY_CATEGORIES)
        missing = sorted(whitelist - lands - declared)
        self.assertEqual(
            missing, [],
            "这些类别能被批准却既没有落地分支、也没声明只记决定："
            "补一个 _install_* 分支，或把它写进 DECISION_ONLY_CATEGORIES 并说明原因",
        )
