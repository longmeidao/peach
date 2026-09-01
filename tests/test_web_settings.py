"""跟账本走的界面设置。

只有侧栏顺序进这里。测试重点是两件事：白名单不能被绕过（别的设置不该悄悄跟着
同步过去），以及归一化必须挡住坏载荷——侧栏渲染不出来会让整个导航不可用。
"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach import web_settings
from peach.web_contract import WebContract
from peach.web_settings import (
    DEFAULT_SIDEBAR_ORDER,
    normalise_sidebar_order,
    q_settings,
    w_settings,
)

PROFILE_SCHEMA = """
CREATE TABLE profile(
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  is_default INTEGER NOT NULL DEFAULT 0,
  settings_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
INSERT INTO profile(id,user_id,name,is_default,settings_json,created_at,updated_at)
VALUES('local-default','local','Default',1,'{}','2026-08-14T12:17:23Z','2026-08-14T12:17:23Z');
"""


class SidebarOrderNormalisationTests(unittest.TestCase):
    def test_unknown_keys_are_dropped_instead_of_rendered(self):
        """不认识的键可能来自旧版本或手改的载荷，留着会渲染出点不开的入口。"""
        self.assertEqual(
            normalise_sidebar_order(["", "tags", "nope", "performers"]),
            ["", "tags", "performers"],
        )

    def test_duplicates_collapse_and_order_is_kept(self):
        self.assertEqual(
            normalise_sidebar_order(["tags", "", "tags", "performers", ""]),
            ["tags", "", "performers"],
        )

    def test_an_empty_result_falls_back_to_the_default(self):
        """空侧栏没有可用性可言，宁可回到默认顺序。"""
        self.assertEqual(normalise_sidebar_order([]), list(DEFAULT_SIDEBAR_ORDER))
        self.assertEqual(normalise_sidebar_order(["nope"]), list(DEFAULT_SIDEBAR_ORDER))
        self.assertEqual(normalise_sidebar_order("tags"), list(DEFAULT_SIDEBAR_ORDER))
        self.assertEqual(normalise_sidebar_order(None), list(DEFAULT_SIDEBAR_ORDER))

    def test_optional_entries_are_accepted(self):
        """可选入口加进侧栏就是「显示」——顺序和显隐是同一个数组。"""
        self.assertEqual(
            normalise_sidebar_order(["", "trash", "quality"]),
            ["", "trash", "quality"],
        )

    def test_old_cleanup_entries_collapse_into_the_combined_destination(self):
        self.assertEqual(
            normalise_sidebar_order(["", "ads", "dupes", "trash"]),
            ["", "data-cleanup", "trash"],
        )


class SettingsRoundTripTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        con = sqlite3.connect(self.db)
        con.executescript(PROFILE_SCHEMA)
        con.commit()
        con.close()
        self.contract = WebContract(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def _stored_json(self) -> dict:
        con = sqlite3.connect(self.db)
        try:
            raw = con.execute(
                "SELECT settings_json FROM profile WHERE id='local-default'").fetchone()[0]
        finally:
            con.close()
        return json.loads(raw)

    def test_an_unset_profile_reads_the_default_order(self):
        self.assertEqual(q_settings(self.contract),
                         {"sidebarOrder": list(DEFAULT_SIDEBAR_ORDER)})

    def test_a_written_order_survives_a_reread(self):
        order = ["", "follow", "tags", "trash"]
        self.assertEqual(w_settings(self.contract, {"sidebarOrder": order}),
                         {"ok": True, "sidebarOrder": order})
        self.assertEqual(q_settings(self.contract)["sidebarOrder"], order)
        self.assertEqual(self._stored_json()["sidebarOrder"], order)

    def test_a_write_normalises_before_it_lands(self):
        """坏载荷不能进账本——存进去之后每次读都要再挡一遍。"""
        w_settings(self.contract, {"sidebarOrder": ["tags", "nope", "tags", ""]})
        self.assertEqual(self._stored_json()["sidebarOrder"], ["tags", ""])

    def test_settings_outside_the_allow_list_are_refused(self):
        """白名单不是黑名单：新增设置字段的人必须显式表态它该不该跨机同步。"""
        with self.assertRaises(ValueError) as caught:
            w_settings(self.contract, {"hoverDelaySeconds": 3})
        self.assertIn("hoverDelaySeconds", str(caught.exception))
        with self.assertRaises(ValueError):
            w_settings(self.contract, {"sidebarOrder": [""], "batchSize": 90})
        self.assertEqual(self._stored_json(), {}, "被拒的请求不该留下任何写入")

    def test_a_write_merges_instead_of_replacing_the_whole_blob(self):
        """请求没提到的键要保持原样，否则旧版本前端提交一次就会抹掉新字段。"""
        con = sqlite3.connect(self.db)
        con.execute("UPDATE profile SET settings_json=? WHERE id='local-default'",
                    (json.dumps({"futureKey": "keep me"}),))
        con.commit()
        con.close()
        w_settings(self.contract, {"sidebarOrder": ["", "tags"]})
        self.assertEqual(self._stored_json()["futureKey"], "keep me")

    def test_a_corrupt_blob_reads_as_unset_rather_than_breaking_the_page(self):
        con = sqlite3.connect(self.db)
        con.execute("UPDATE profile SET settings_json='not json' WHERE id='local-default'")
        con.commit()
        con.close()
        self.assertEqual(q_settings(self.contract)["sidebarOrder"],
                         list(DEFAULT_SIDEBAR_ORDER))

    def test_a_non_object_body_is_a_type_error(self):
        with self.assertRaises(TypeError):
            w_settings(self.contract, ["", "tags"])
        with self.assertRaises(ValueError):
            w_settings(self.contract, {})


class ContractRegistrationTests(unittest.TestCase):
    def test_the_routes_are_registered_and_the_write_stays_behind_the_ledger_gate(self):
        """写侧栏顺序要写账本，所以它必须留在只读闸门后面。

        reader（macOS）因此改不了顺序，但读到的是 writer 的那一份——这正是
        「同一份习惯」的意思，不是缺陷。
        """
        from peach import web_contract

        self.assertIs(web_contract.GET_HANDLERS["/api/settings"], q_settings)
        self.assertIs(web_contract.POST_HANDLERS["/api/settings"], w_settings)
        self.assertNotIn(
            "/api/settings", web_contract.READ_ONLY_POST_ROUTES,
            "这个 POST 写账本，不能放进只读白名单",
        )

    def test_the_sidebar_key_lists_match_the_web_surface(self):
        """键表是前后端共用的语义契约，两边各写一份就会漂。

        漂了不会报错：后端把前端没有的键判成合法、存进账本，前端渲染时又整个丢掉，
        表现是「排好的顺序刷新后自己变了」。所以逐字比对两份清单。
        """
        import re

        page = (Path(__file__).resolve().parents[1] / "web" / "app.js").read_text(
            encoding="utf-8")

        def js_list(name):
            raw = re.search(rf"const {name}=\[(.*?)\];", page).group(1)
            return tuple(item.strip().strip("'") for item in raw.split(","))

        self.assertEqual(js_list("DEFAULT_SIDEBAR_ORDER"), DEFAULT_SIDEBAR_ORDER)
        self.assertEqual(js_list("OPTIONAL_SIDEBAR_KEYS"),
                         web_settings.OPTIONAL_SIDEBAR_KEYS)

    def test_the_front_end_writes_the_order_back_to_the_ledger(self):
        """侧栏顺序必须提交到 /api/settings，不能只写 localStorage。

        这是这次改动的全部目的：换台机器看到的是同一份导航。
        """
        page = (Path(__file__).resolve().parents[1] / "web" / "app.js").read_text(
            encoding="utf-8")
        self.assertIn("api('/api/settings',{method:'POST'", page,
                      "保存侧栏顺序没有写回服务端")
        self.assertIn("loadSyncedSettings", page, "启动时没有从服务端纠正本地缓存")


if __name__ == "__main__":
    unittest.main()
