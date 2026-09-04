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

from peach import web_contract as rm_web
from peach import web_review as rm_review

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
        fields = ["item_key", "code", "query", "field", "field_label", "current_value",
                  "candidates_json", "source_count", "status", "size_gb", "videos", "fetched_at"]
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
                    {"candidate_key": f"{item['item_key']}:{i}", "source": source,
                     "display_value": value, "value": value, "confidence": 0.9,
                     "source_url": "", "raw_snapshot": ""}
                    for i, value in enumerate(item["candidates"])], ensure_ascii=False),
                "source_count": "1", "status": "candidate", "size_gb": "",
                "videos": "1", "fetched_at": "",
            })
        return self.write_metadata_candidates(payload)

    def _asset(self, aid, code, name):
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO asset(id,location,path,name,medium,code) "
                    "VALUES(?,'local',?,?,'video',?)", (aid, f"/x/{name}", name, code))
        con.commit(); con.close()

    def _auto(self):
        return rm_review.w_review_auto_apply(self.contract)

    def test_latest_candidate_uses_write_time_not_filename_order(self):
        older = self.candidates / "metadata-field-candidates-windows-p0-proof-20260822.csv"
        newer = self.candidates / "metadata-field-candidates-japanese-official-tags-20260827.csv"
        older.write_text("item_key\nOLD\n", encoding="utf-8")
        newer.write_text("item_key\nNEW\n", encoding="utf-8")
        os.utime(older, (1000, 1000))
        os.utime(newer, (2000, 2000))

        self.assertEqual(
            rm_review.latest_candidate_file("metadata_fields", self.candidates), newer,
        )

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

    def test_auto_apply_never_overwrites_or_picks_between_values(self):
        self._asset(92, "AAA-1", "AAA-1.mp4")
        self._asset(93, "BBB-2", "BBB-2.mp4")
        self.write_metadata_rows([
            # 已有值：只补空，永不覆盖。
            {"item_key": "AAA", "field": "release_date", "current": "2001-01-01",
             "candidates": ["2015-02-20"], "code": "AAA-1"},
            # 两个候选：存在取舍，正是复核该做的事。
            {"item_key": "BBB", "field": "release_date", "current": "",
             "candidates": ["2015-02-20", "2016-03-30"], "code": "BBB-2"},
        ])
        self.assertEqual(self._auto()["applied"], 0)
        self.assertEqual(sorted(self.queue_keys("metadata_fields")), ["AAA", "BBB"])

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
            # 演员和标签不在白名单：那两类分歧是真实的。
            {"item_key": "DDD", "field": "performers", "current": "",
             "candidates": ["某人"], "code": "DDD-4"},
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
            "current": "English Title", "candidates": ["日本語タイトル"], "source": "javbus",
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
            "current": "English Title", "candidates": ["日本語タイトル"], "source": "javbus",
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
            "current": "English Title", "candidates": ["日本語タイトル"], "source": "javbus",
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

    def test_code_creator_candidates_reach_the_review_page(self):
        fields = ["entity_id", "creator", "verdict", "identity", "assets",
                  "sample_path", "code_action", "reason"]
        self._csv("code-creator-review.csv", fields, [
            {"entity_id": "6869", "creator": "banbi_555", "verdict": "存疑",
             "identity": "BANBI-555", "assets": "69", "sample_path": "A:/x.mp4",
             "code_action": "", "reason": "名字像番号，但目录内没有同番号文件"}])
        rows = rm_review.q_review(self.contract)["sections"]["code_creators"]
        self.assertEqual(rows[0]["item_key"], "6869")
        self.assertIn("没有同番号文件", rows[0]["reason"])


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
