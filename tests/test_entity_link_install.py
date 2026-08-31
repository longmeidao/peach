"""实体链接安装：已复核的结果必须能进库，不合法的必须留下拒绝理由。"""
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load_module():
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(
        "install_entity_links", REPO / "scripts" / "install_entity_links.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCHEMA = """
CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT);
CREATE TABLE entity_alias(entity_id INTEGER, alias TEXT);
CREATE TABLE entity_link(
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
  link_kind TEXT NOT NULL CHECK(link_kind IN ('official','social','catalog','source_reference')),
  label TEXT NOT NULL, url TEXT NOT NULL, hostname TEXT,
  is_sensitive INTEGER NOT NULL DEFAULT 0 CHECK(is_sensitive IN (0,1)),
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE(entity_id,url));
"""


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = Path(tempfile.mkdtemp())
        self.db = self.tmp / "ledger.db"
        self.connection = sqlite3.connect(self.db)
        self.connection.executescript(SCHEMA)
        self.connection.executemany(
            "INSERT INTO entity VALUES(?,?,?)",
            [(1, "studio", "MOODYZ"), (2, "studio", "Prestige"), (3, "performer", "立花美涼")])
        self.connection.execute("INSERT INTO entity_alias VALUES(?,?)", (2, "プレステージ"))
        self.connection.commit()

    def tearDown(self):
        self.connection.close()

    def row(self, **kw):
        base = {"entity_id": "", "kind": "studio", "name": "MOODYZ", "link_kind": "official",
                "label": "官方网站", "url": "https://moodyz.com/", "evidence": "标题自述厂牌名"}
        base.update(kw)
        return base

    def test_a_reviewed_link_reaches_the_ledger_with_its_provenance(self):
        """装进去的不只是 URL，还有它凭什么被采信。

        没有 provenance 的话，半年后没人能判断这条链接是人工看图确认的还是脚本猜的，
        于是整表都只能重查一遍——那等于这次复核白做。
        """
        planned = self.module.plan(self.connection, [self.row()])
        self.assertEqual([p["action"] for p in planned], ["insert"])
        self.assertEqual(self.module.install(self.connection, planned, "review.csv"), 1)

        stored = self.connection.execute(
            "SELECT entity_id,link_kind,label,url,hostname,metadata_json FROM entity_link"
        ).fetchone()
        self.assertEqual(stored[:5], (1, "official", "官方网站", "https://moodyz.com/", "moodyz.com"))
        metadata = json.loads(stored[5])
        self.assertEqual(metadata["source"], "review.csv")
        self.assertEqual(metadata["evidence"], "标题自述厂牌名")
        self.assertIn("installed_at", metadata)

    def test_running_twice_does_not_duplicate(self):
        """复核表会被反复重跑；第二遍必须是零写入而不是第二行。"""
        planned = self.module.plan(self.connection, [self.row()])
        self.module.install(self.connection, planned, "review.csv")
        again = self.module.plan(self.connection, [self.row()])
        self.assertEqual([p["action"] for p in again], ["skip"])
        self.assertIn("已存在", again[0]["reason"])
        self.assertEqual(self.module.install(self.connection, again, "review.csv"), 0)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM entity_link").fetchone()[0], 1)

    def test_a_url_without_scheme_does_not_become_a_second_row(self):
        """复核表是人和脚本混写的，`moodyz.com` 和 `https://moodyz.com/` 都会出现。

        不归一的话同一个站会绕过 UNIQUE(entity_id,url) 建出两行，资料页上就并排出现
        两条一模一样的链接。
        """
        self.module.install(self.connection, self.module.plan(self.connection, [self.row()]),
                            "review.csv")
        planned = self.module.plan(self.connection, [self.row(url="moodyz.com/")])
        self.assertEqual(planned[0]["action"], "skip")

    def test_an_entity_can_be_matched_by_alias(self):
        planned = self.module.plan(self.connection, [self.row(name="プレステージ")])
        self.assertEqual(planned[0]["entity_id"], 2)
        self.assertEqual(planned[0]["reason"], "按别名")

    def test_an_unknown_entity_is_reported_not_silently_dropped(self):
        """静默丢行会让「装了 N 条」和「表里多了 N 条」对不上，而没人知道差在哪。"""
        planned = self.module.plan(self.connection, [self.row(name="不存在的厂牌")])
        self.assertEqual(planned[0]["action"], "skip")
        self.assertIn("找不到", planned[0]["reason"])

    def test_an_invalid_link_kind_is_refused_before_sqlite_raises(self):
        """表上有 CHECK 约束，但让它抛出来会中断整批。提前拦下才能继续装其余的。"""
        planned = self.module.plan(self.connection, [self.row(link_kind="blog")])
        self.assertEqual(planned[0]["action"], "skip")
        self.assertIn("link_kind", planned[0]["reason"])

    def test_a_non_http_url_is_refused(self):
        for bad in ("javascript:alert(1)", "ftp://example.com/"):
            planned = self.module.plan(self.connection, [self.row(url=bad)])
            self.assertEqual(planned[0]["action"], "skip", bad)
            self.assertIn("URL", planned[0]["reason"])

    def test_a_link_without_a_label_is_refused(self):
        """资料页拿 label 当链接文字；空 label 会渲染成一个点不到的空链接。"""
        planned = self.module.plan(self.connection, [self.row(label="  ")])
        self.assertEqual(planned[0]["action"], "skip")
        self.assertIn("label", planned[0]["reason"])

    def test_apply_without_backup_refuses_and_writes_nothing(self):
        """真实账本写入必须带备份；缺备份要在读输入之前就停。"""
        code = self.module.main(["--database", str(self.db), "--input", str(self.tmp / "x.csv"),
                                 "--apply"])
        self.assertEqual(code, 2)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM entity_link").fetchone()[0], 0)

    def test_dry_run_is_the_default_and_touches_nothing(self):
        source = self.tmp / "review.csv"
        source.write_text(
            "entity_id,kind,name,link_kind,label,url,evidence\n"
            ",studio,MOODYZ,official,官方网站,https://moodyz.com/,标题自述\n",
            encoding="utf-8-sig")
        self.assertEqual(self.module.main(["--database", str(self.db), "--input", str(source)]), 0)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM entity_link").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
