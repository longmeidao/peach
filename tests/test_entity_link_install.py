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
        # `--no-check` 不只是提速：测试不许发网络请求，否则一次断网就变成红灯。
        self.assertEqual(self.module.main(
            ["--database", str(self.db), "--input", str(source), "--no-check"]), 0)
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM entity_link").fetchone()[0], 0)

    def test_a_link_that_does_not_open_never_reaches_the_ledger(self):
        """这条守的是一次真实事故。

        首批 703 条链接一条都没验就装进了账本，事后逐条测发现 289 条 official 里有
        107 条打不开（84 个 404、18 个 502），37% 是死的。上游给什么就存什么，等于把
        minnano-av 几年前的快照当成现在的事实——T-POWERS 改过站，`/official/talent/X`
        早已 404，而资料页上它看起来和好链接一模一样。

        门槛放在安装器而不是各个采集器里：这里是所有来源进入账本的唯一入口。
        """
        planned = self.module.plan(self.connection, [
            self.row(url="https://dead.example/gone"),
            self.row(name="Prestige", url="https://alive.example/"),
        ])
        self.assertEqual([p["action"] for p in planned], ["insert", "insert"])
        self.module.check_links(
            planned, probe=lambda url: (url == "https://alive.example/", "HTTP 404"))
        self.assertEqual([p["action"] for p in planned], ["skip", "insert"])
        self.assertIn("打不开", planned[0]["reason"])
        self.assertIn("404", planned[0]["reason"])
        self.assertEqual(self.module.install(self.connection, planned, "review.csv"), 1)

    def test_dead_links_already_in_the_ledger_are_found_for_pruning(self):
        """可达性门槛只挡新写入；库里那 703 条是在门槛存在之前进去的。

        链接还会随时间烂掉——事务所改版、艺人解约、博客注销——所以这条路要留着复用，
        不是一次性的清理脚本。
        """
        for url in ("https://alive.example/", "https://dead.example/gone"):
            planned = self.module.plan(self.connection, [self.row(url=url)])
            self.module.install(self.connection, planned, "seed.csv")
        self.assertEqual(
            self.connection.execute("SELECT count(*) FROM entity_link").fetchone()[0], 2)

        dead = self.module.dead_links(
            self.connection, probe=lambda url: (url == "https://alive.example/", "HTTP 404"))
        self.assertEqual([d["url"] for d in dead], ["https://dead.example/gone"])
        self.assertEqual(dead[0]["entity"], "MOODYZ")
        self.assertEqual(dead[0]["note"], "HTTP 404")

    def test_only_a_gone_status_counts_as_proof_that_a_link_is_dead(self):
        """取不到不等于没了，这两件事只有 404／410 能划清。

        实测全库 152 条打不开的链接里，有 26 条属于「取不到」而非「没了」：
        `linktr.ee` 回 403（Linktree 挡爬虫，浏览器里能正常打开）、`facebook.com`
        回 400、`x.com/MomotaEmiri` 回 500（X 的临时错误，账号很可能还在）、
        `diaz-g.com` 直接连接失败。按「非 200 就删」会把这些好链接一起删掉。

        这和取证失败时写 `未取得` 而不是写结论是同一条规矩。
        """
        for note in ("HTTP 404", "HTTP 410"):
            self.assertTrue(self.module.is_gone(note), note)
        for note in ("HTTP 403", "HTTP 400", "HTTP 500", "HTTP 502",
                     "取不到：ConnectError", "取不到：ReadTimeout", "可打开"):
            self.assertFalse(self.module.is_gone(note), note)

    def test_the_reachability_gate_does_not_re_probe_rows_already_skipped(self):
        """已经因为别的原因跳过的行不必再请求一次——那是白费一次往返。"""
        planned = self.module.plan(self.connection, [self.row(name="不存在的厂牌")])
        self.assertEqual(planned[0]["action"], "skip")
        probed = []

        def probe(url):
            probed.append(url)
            return True, ""

        self.module.check_links(planned, probe=probe)
        self.assertEqual(probed, [])


if __name__ == "__main__":
    unittest.main()
