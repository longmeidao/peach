"""追更的 Web 契约与页面源测试。

契约层测试用临时数据库；页面源测试守的是「追更表面」这一个语义契约，
不是某个文件——判据同 `tests/test_web_ui.py`。
"""
import json
import os
import re
import sqlite3
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from peach import web_follow
from peach.follow import FollowSourceError
from peach.follow_secrets import CredentialError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.follow_store import FollowStore
from peach.migrations import discover
from peach.web_contract import WebContract, dispatch_api_get, dispatch_api_post


ROOT = Path(__file__).resolve().parents[1]
MOMENT = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)


class FollowContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.db = self.root / "ledger.db"
        connection = sqlite3.connect(self.db)
        for migration in discover(ROOT / "migrations"):
            connection.executescript(migration.sql)
        connection.commit()
        connection.close()
        self.contract = WebContract(
            self.db, follow_sources_root=self.root / "sources",
            follow_secrets_root=self.root / "secrets")

    def _seed(self, candidates=None, provider="rule34video", ref="lazyprocrastinator",
              semantics="work"):
        candidates = candidates if candidates is not None else (
            FollowCandidate(provider=provider, external_id="4542713",
                            title="Fiona - Paizuri", duration=20.0,
                            url="https://rule34video.com/video/4542713/x/",
                            thumb_url="https://rule34video.com/t/4542713.jpg",
                            extra={"published_precision": "approximate"},
                            published_at="2026-08-18T00:00:00Z"),
            FollowCandidate(provider=provider, external_id="4542721",
                            title="Fiona - Paizuri (Nude)",
                            url="https://rule34video.com/video/4542721/x/"),
        )
        with self.contract.database.write_transaction() as connection:
            store = FollowStore(lambda: connection,
                                sources_root=self.contract.follow_sources_root)
            source_id = store.register(
                provider=provider, ref=ref, label="LazyProcrastinator",
                url=f"https://{provider}.test/{ref}", semantics=semantics, moment=MOMENT)
            store.record(source_id, SourceFetch(
                provider=provider, ref=ref, request_url=f"https://{provider}.test/{ref}",
                semantics=semantics, candidates=candidates, raw_body=b"<html/>"),
                moment=MOMENT)
        return source_id

    def _get(self, path="/api/follow", **args):
        return dispatch_api_get(self.contract, path, args)

    def _post(self, path, body):
        return dispatch_api_post(self.contract, path, body)

    def test_feed_groups_variants_under_one_card(self):
        self._seed()
        payload = self._get()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["groups"]), 1)
        group = payload["groups"][0]
        self.assertEqual(group["primary"]["title"], "Fiona - Paizuri")
        self.assertEqual([v["variant_label"] for v in group["variants"]], ["nude"])
        self.assertEqual(group["providers"], ["rule34video"])
        self.assertFalse(group["has_wip"])

    def test_feed_reports_approximate_publication_precision(self):
        self._seed()
        primary = self._get()["groups"][0]["primary"]
        self.assertEqual(primary["published_precision"], "approximate")

    def test_feed_never_exposes_the_raw_media_url(self):
        # 界面只需要知道有没有媒体；直链是来源层的事，不进公共 JSON。
        self._seed()
        payload = json.dumps(self._get(), ensure_ascii=False)
        self.assertNotIn("media_url", payload)
        self.assertIn('"has_media"', payload)

    def test_feed_filters_by_status_and_reports_counts(self):
        self._seed()
        first = self._get()["groups"][0]["primary"]["id"]
        self._post("/api/follow/status", {"item": first, "to": "ignored"})
        self.assertEqual(self._get(status="new")["counts"],
                         {"new": 1, "seen": 0, "saved": 0, "ignored": 1})
        self.assertEqual(len(self._get(status="ignored")["groups"]), 1)

    def test_feed_ignores_a_nonsense_limit_instead_of_failing(self):
        self._seed()
        self.assertEqual(len(self._get(limit="nope")["groups"]), 1)

    def test_sources_are_listed_with_their_last_status(self):
        self._seed()
        source = self._get()["sources"][0]
        self.assertEqual(source["provider_label"], "Rule34Video")
        self.assertEqual(source["last_status"], "ok")
        self.assertTrue(source["enabled"])

    def test_status_write_rejects_a_non_integer_item(self):
        with self.assertRaises(ValueError):
            self._post("/api/follow/status", {"item": "1", "to": "seen"})

    def test_saving_writes_one_online_asset(self):
        self._seed()
        item = self._get()["groups"][0]["primary"]["id"]
        result = self._post("/api/follow/save", {"item": item})
        self.assertTrue(result["ok"])
        with self.contract.database.read_connection() as connection:
            row = connection.execute(
                "SELECT location,path FROM asset WHERE id=?",
                (result["asset_id"],)).fetchone()
        self.assertEqual(row["location"], "online")
        self.assertEqual(self._get(status="saved")["counts"]["saved"], 1)

    def test_check_is_the_only_endpoint_that_reaches_the_network(self):
        self._seed()
        fetch = SourceFetch(
            provider="rule34video", ref="lazyprocrastinator",
            request_url="https://rule34video.com/models/lazyprocrastinator/",
            semantics="work", raw_body=b"<html>2</html>",
            candidates=(FollowCandidate(provider="rule34video", external_id="999",
                                        title="Sayuri - Handy"),))
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch
            result = self._post("/api/follow/check", {})
        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["results"][0]["added"], 1)

    def test_one_failing_source_does_not_hide_the_others(self):
        self._seed()
        self._seed(provider="rule34xxx", ref="lazyprocrastinator", candidates=())

        def factory(provider, **kwargs):
            connector = mock.Mock()
            if provider == "rule34xxx":
                connector.fetch.side_effect = CredentialError("需要 user_id 与 api_key")
            else:
                connector.fetch.return_value = SourceFetch(
                    provider="rule34video", ref="lazyprocrastinator",
                    request_url="https://rule34video.test/", semantics="work",
                    not_modified=True)
            return connector

        with mock.patch.object(web_follow, "build_connector", factory):
            result = self._post("/api/follow/check", {})
        outcomes = {row["provider"]: row for row in result["results"]}
        self.assertFalse(outcomes["rule34xxx"]["ok"])
        self.assertEqual(outcomes["rule34xxx"]["status"], "unauthorized")
        self.assertTrue(outcomes["rule34video"]["ok"])
        self.assertTrue(outcomes["rule34video"]["not_modified"])

    def test_an_unwritable_evidence_root_is_reported_without_failing_the_check(self):
        self._seed()
        contract = self.contract
        contract.follow_sources_root = self.root / "evidence"
        # 用普通文件占住路径构造同一个 FileExistsError：symlink 在非管理员 Windows 上建不了。
        (self.root / "evidence").write_text("not a directory", encoding="utf-8")
        fetch = SourceFetch(
            provider="rule34video", ref="lazyprocrastinator",
            request_url="https://rule34video.com/models/lazyprocrastinator/",
            semantics="work", raw_body=b"<html>2</html>",
            candidates=(FollowCandidate(provider="rule34video", external_id="999",
                                        title="Sayuri - Handy"),))
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch
            result = self._post("/api/follow/check", {})
        outcome = result["results"][0]
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["added"], 1)
        self.assertIn("证据未取得", outcome["evidence_error"])
        self.assertEqual(self._get()["sources"][0]["last_status"], "ok")

    def test_source_errors_are_recorded_for_later_inspection(self):
        self._seed()
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.side_effect = FollowSourceError("HTTP 503")
            self._post("/api/follow/check", {})
        self.assertEqual(self._get()["sources"][0]["last_status"], "error")
        self.assertIn("503", self._get()["sources"][0]["last_error"])

    def test_credentials_say_what_each_source_actually_needs(self):
        payload = self._get("/api/follow/credentials")
        by_provider = {row["provider"]: row for row in payload["providers"]}
        self.assertEqual(by_provider["kemono"]["requirement"], "none")
        self.assertEqual(by_provider["rule34xxx"]["requirement"], "required")
        self.assertEqual(by_provider["rule34xxx"]["needs"], ["user_id", "api_key"])
        self.assertEqual(by_provider["rule34xxx"]["missing"], ["user_id", "api_key"])
        self.assertEqual(by_provider["f95zone"]["requirement"], "optional")
        self.assertEqual(by_provider["simpcity"]["requirement"], "blocked")
        self.assertIn("DDoS-Guard", by_provider["simpcity"]["why"])
        self.assertTrue(by_provider["rule34xxx"]["path"].endswith("rule34xxx.json"))

    def test_a_configured_credential_reports_nothing_missing(self):
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "sekret"}', encoding="utf-8")
        row = next(r for r in self._get("/api/follow/credentials")["providers"]
                   if r["provider"] == "rule34xxx")
        self.assertEqual(row["missing"], [])
        self.assertNotIn("sekret", json.dumps(row))

    def test_saving_a_credential_writes_it_without_echoing_the_value(self):
        result = self._post("/api/follow/credential", {
            "provider": "rule34xxx",
            "values": {"user_id": "42", "api_key": "sekret"}})
        self.assertTrue(result["ok"])
        self.assertNotIn("sekret", json.dumps(result))
        self.assertEqual(result["saved"]["fields"], ["api_key", "user_id"])
        path = self.root / "secrets" / "follow" / "rule34xxx.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                         {"user_id": "42", "api_key": "sekret"})
        if os.name == "nt":
            # Windows 的 chmod 只能拨只读位，NTFS 权限走 ACL——这里不假装收紧过。
            self.assertFalse(result["permissions_tightened"])
        else:
            self.assertTrue(result["permissions_tightened"])
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_clearing_a_credential_removes_the_file(self):
        self._post("/api/follow/credential", {
            "provider": "rule34xxx", "values": {"user_id": "42", "api_key": "k"}})
        result = self._post("/api/follow/credential",
                            {"provider": "rule34xxx", "values": {}})
        self.assertTrue(result["cleared"])
        self.assertFalse((self.root / "secrets" / "follow" / "rule34xxx.json").exists())

    def test_only_declared_providers_and_fields_are_accepted(self):
        for body in ({"provider": "kemono", "values": {"x": "1"}},
                     {"provider": "../escape", "values": {"x": "1"}},
                     {"provider": "rule34xxx", "values": {"evil": "1"}},
                     {"provider": "rule34xxx", "values": "notadict"}):
            with self.assertRaises(ValueError):
                self._post("/api/follow/credential", body)
        self.assertFalse((self.root / "secrets").exists())

    def test_credentials_endpoint_reports_fields_but_never_values(self):
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "sekret"}', encoding="utf-8")
        payload = self._get("/api/follow/credentials")
        rule34 = next(row for row in payload["providers"]
                      if row["provider"] == "rule34xxx")
        self.assertTrue(rule34["present"])
        self.assertEqual(rule34["fields"], ["api_key", "user_id"])
        self.assertNotIn("sekret", json.dumps(payload))

    def test_f95_thread_activity_is_labelled_as_a_release_group(self):
        self._seed(provider="f95zone", ref="50685", semantics="release", candidates=(
            FollowCandidate(provider="f95zone", external_id="21383374",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            url="https://f95zone.to/threads/50685/post-21383374",
                            published_at="2026-08-21T04:14:09Z", author="Jkhomie1198",
                            summary="New batch up Gofile",
                            extra={"media_needs_credential": True}),
            FollowCandidate(provider="f95zone", external_id="21394555",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            url="https://f95zone.to/threads/50685/post-21394555",
                            published_at="2026-08-22T18:09:23Z"),
        ))
        group = self._get()["groups"][0]
        self.assertTrue(group["is_release"])
        self.assertEqual(group["primary"]["external_id"], "21394555")
        self.assertEqual(group["primary"]["version"], "2026-06-28")
        self.assertTrue(group["variants"][0]["media_needs_credential"])
        # 线程动态要说清是谁发的；一个线程里九条回复全标成 main 没有信息量。
        self.assertEqual(group["variants"][0]["author"], "Jkhomie1198")
        self.assertEqual(group["variants"][0]["summary"], "New batch up Gofile")


class FollowSourceAddTests(FollowContractTests):
    """粘链接登记来源。首次检查用注入的连接器，测试不联网。"""

    def _add(self, url, fetch=None):
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch or SourceFetch(
                provider="rule34video", ref="x", request_url="https://x.test/",
                semantics="work", not_modified=True)
            return self._post("/api/follow/source", {"action": "add", "url": url})

    def test_pasting_a_creator_link_registers_and_checks_it(self):
        result = self._add("https://rule34video.com/models/lazyprocrastinator/")
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "rule34video")
        self.assertEqual(result["ref"], "lazyprocrastinator")
        self.assertTrue(result["checked"]["ok"])
        self.assertEqual(self._get()["sources"][0]["url"],
                         "https://rule34video.com/models/lazyprocrastinator/")

    def test_a_thread_link_is_registered_with_release_semantics(self):
        self._add("https://f95zone.to/threads/"
                  "lazy-procrastinator-collection-2026-06-28-lazyprocrast.50685/")
        source = self._get()["sources"][0]
        self.assertEqual(source["provider"], "f95zone")
        self.assertEqual(source["ref"], "50685")
        self.assertEqual(source["semantics"], "release")
        self.assertEqual(source["label"], "lazy procrastinator collection")

    def test_a_kemono_link_keeps_its_service_and_user(self):
        self._add("https://kemono.cr/fanbox/user/30917150")
        source = self._get()["sources"][0]
        self.assertEqual(source["provider"], "kemono")
        self.assertEqual(source["ref"], "fanbox/30917150")

    def test_the_same_link_twice_does_not_duplicate_the_source(self):
        self._add("https://rule34video.com/models/lazyprocrastinator/")
        self._add("https://rule34video.com/models/lazyprocrastinator/")
        self.assertEqual(len(self._get()["sources"]), 1)

    def test_a_failing_first_check_still_leaves_the_source_registered(self):
        # rule34.xxx 缺 key 就是这种情况。整个回滚掉反而让人不知道发生了什么。
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.side_effect = CredentialError("需要 user_id")
            result = self._post("/api/follow/source", {
                "action": "add",
                "url": "https://rule34.xxx/index.php?page=post&s=list&tags=lazy"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["checked"]["ok"])
        source = self._get()["sources"][0]
        self.assertEqual(source["last_status"], "unauthorized")
        self.assertIn("user_id", source["last_error"])

    def test_an_unknown_host_is_refused_with_the_supported_list(self):
        with self.assertRaises(FollowSourceError) as caught:
            self._post("/api/follow/source",
                       {"action": "add", "url": "https://example.test/creator"})
        self.assertIn("kemono.cr", str(caught.exception))

    def test_simpcity_is_refused_with_the_bot_check_reason(self):
        with self.assertRaises(FollowSourceError) as caught:
            self._post("/api/follow/source",
                       {"action": "add", "url": "https://simpcity.cr/threads/x.1/"})
        self.assertIn("DDoS-Guard", str(caught.exception))

    def test_removing_a_source_takes_its_items_with_it(self):
        self._seed()
        source_id = self._get()["sources"][0]["id"]
        self.assertTrue(self._get()["groups"])
        self._post("/api/follow/source", {"action": "remove", "id": source_id})
        payload = self._get()
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["groups"], [])

    def test_remove_requires_an_integer_id(self):
        with self.assertRaises(ValueError):
            self._post("/api/follow/source", {"action": "remove", "id": "1"})

    def test_unknown_actions_are_rejected(self):
        with self.assertRaises(ValueError):
            self._post("/api/follow/source", {"action": "explode"})


class FollowWebSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        web = ROOT / "web"
        cls.page = chr(10).join(
            (web / name).read_text(encoding="utf-8")
            for name in ("index.html", "app.css", "app.js"))

    def assertPageContains(self, needle, message=""):
        if needle not in self.page:
            self.fail(f"Web 表面缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def test_watching_lives_in_the_left_rail_and_managing_stays_in_the_manage_area(self):
        # 看和管是两件事，两个页面：左侧导航进「看」，管理区进「管」。
        # 断言「相邻」这件事本身，不要连换行和缩进一起写死——那种断言一改格式就红，
        # 红的原因还和它想守的契约无关。
        rail = self.page[self.page.index("const EDGE_ICONS=["):]
        rail = rail[:rail.index("];")]
        keys = re.findall(r"\['([a-z]*)'", rail)
        self.assertIn("follow", keys)
        self.assertEqual(keys[keys.index("follow") + 1], "immerse",
                         "关注入口应当排在沉浸模式前面")
        self.assertPageContains("['follow','关注','globe']")
        self.assertPageContains("if(k==='follow'){openFollow();return}")
        self.assertPageContains("if(k==='follow')return path==='/follow';")
        self.assertPageContains("['follow','关注','globe']")
        self.assertPageContains("if(path==='/follow-manage')return 'follow'")
        self.assertPageContains("if(section==='follow'){openFollowManage();return}")

    def test_both_follow_routes_restore_on_reload(self):
        self.assertPageContains("if(path==='/follow'){await openFollow(false);return}")
        self.assertPageContains(
            "if(path==='/follow-manage'){await openFollowManage(false);return}")

    def test_sources_are_added_by_pasting_not_by_a_command(self):
        self.assertPageContains('id="followAdd"')
        self.assertPageContains('name="lines"')
        self.assertPageContains("'/api/follow/source'")
        self.assertPageContains("data-follow-remove")

    def test_a_bare_name_or_id_is_looked_up_across_sources(self):
        self.assertPageContains("'/api/follow/resolve'")
        self.assertPageContains("function renderFollowPicks(")
        # 结果先勾选再落地，不自动登记。
        self.assertPageContains("data-pick-add")
        self.assertPageContains("data-pick-cancel")

    def test_already_followed_candidates_are_shown_but_not_selectable(self):
        # 灰掉但仍显示，免得人以为没查到。
        self.assertPageContains("c.known?' known':''")
        self.assertPageContains("'已经在追'")

    def test_the_first_name_lookup_warns_about_the_index_download(self):
        self.assertPageContains("首次按名字查要下载创作者索引，可能几十秒")

    def test_the_input_and_its_button_are_the_same_height(self):
        # 静止时输入框就该和按钮齐平；固定多行的话按钮只有它一小截高。
        page = self.page
        self.assertEqual(page.count(".faddform textarea{"), 1,
                         "旧规则留在后面会覆盖新输入框样式")
        rule = page[page.index(".faddform textarea{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("height:32px", rule)
        self.assertIn("min-height:32px", rule)
        button = page[page.index(".fbtn{"):]
        self.assertIn("height:32px", button[:button.index("}")])

    def test_the_manage_page_is_ordered_by_what_you_do_first(self):
        # 只看管理页那一段：同样的标题在别的页面上也出现过，全页搜索会命中错的那个。
        page = self.page
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowItems(")]
        order = [body.index(f'<h3>{heading}')
                 for heading in ("添加关注", "关注列表", "凭据")]
        self.assertEqual(order, sorted(order), "管理页分区顺序应为 加关注 → 关注列表 → 凭据")

    def test_counts_are_a_footnote_not_their_own_section(self):
        # 四个数字单独占一张通栏卡片，在宽屏上就是一条空长条。
        page = self.page
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowItems(")]
        self.assertNotIn("<h3>内容", body)
        self.assertIn("条未看", body)

    def test_the_page_uses_two_columns_so_the_width_is_not_wasted(self):
        page = self.page
        rule = page[page.index(".followmanage{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("grid-template-columns:minmax(0,1fr)", rule)

    def test_the_panel_has_no_cards_nested_inside_cards(self):
        """vercel.com/design.md 点名的反模式：卡片套卡片、用边框补救层级。

        分组该靠标题和一条分隔线，不是给每一行都套个盒子。
        """
        page = self.page
        self.assertNotIn(".fcard{", page)
        self.assertNotIn(".fsource{", page,
                         "旧来源卡片规则会给新行重新套上边框和圆角")
        rule = page[page.index(".frow{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("border-bottom:1px solid", rule)
        self.assertNotIn("border-radius", rule)

    def test_the_type_scale_has_no_arbitrary_in_between_sizes(self):
        """同一份文档点名的另一条：细小灰字加随意字号。

        管理页只用 14 正文 / 13 次要 / 12 元信息三档。
        """
        page = self.page
        block = page[page.index("/* ── 关注管理页 ──"):page.index("/* ── 查找结果的勾选清单")]
        sizes = sorted({m for m in re.findall(r"font-size:([\d.]+)px", block)},
                       key=float)
        self.assertEqual(sizes, ["12", "13", "14"], f"字号档位应只有三档，实际 {sizes}")

    def test_credential_rows_say_whether_they_are_needed_at_all(self):
        # 「未配置」本身不是信息：要说清需不需要、需要什么、去哪儿拿。
        self.assertPageContains("required:['需要'")
        self.assertPageContains("none:['不需要'")
        self.assertPageContains("blocked:['接不进来'")
        self.assertPageContains("row.where")
        self.assertPageContains("row.howto")

    def test_the_page_says_where_the_credential_actually_lands(self):
        # 从 Mac 浏览 Windows 实例时，凭据落在 Windows 上——不能写成「本机」。
        self.assertPageContains("运行 Peach 的那台机器")
        self.assertPageContains("Windows 上不收紧文件权限")
        self.assertPageContains("row.path")
        self.assertPageContains("row.world_readable")

    def test_credentials_are_typed_into_the_page_not_into_a_file_by_hand(self):
        self.assertPageContains('data-cred-form=')
        self.assertPageContains("'/api/follow/credential'")
        self.assertPageContains('type="password"')
        # 值只往磁盘走：保存后清空输入框，页面上再也看不到。
        self.assertPageContains("form.reset();await openFollowManage(false)")
        self.assertPageContains("data-cred-clear")

    def test_only_a_missing_required_credential_demands_attention(self):
        # 可选的、不需要的、站点接不进来的都收起来；永远展开就是永久噪音。
        self.assertPageContains("row.requirement==='required'&&!configured")
        self.assertPageContains("${needsAttention?' open':''}")

    def test_the_watch_page_does_not_carry_source_management(self):
        # 输入框、移除、凭据都只属于管理页；看的那页保持干净。
        page = self.page
        watch = page[page.index("function renderFollow(){"):page.index("async function openFollow")]
        for management in ("followAdd", "data-follow-remove", "fcreds", "data-follow-bulk"):
            if management in watch:
                self.fail(f"看的那一页不应出现管理控件：{management!r}")

    def test_times_are_rendered_in_the_viewer_timezone_not_raw_utc(self):
        # 账本存 UTC；直接把那串字面量印出来，UTC+8 的人看到的每个时间都早 8 小时。
        self.assertPageContains("function localTime(iso)")
        self.assertPageContains("new Date(text)")
        self.assertPageContains("when.getHours()")
        page = self.page
        body = page[page.index("function followWhen("):page.index("function followBadges(")]
        self.assertNotIn(".replace('T',' ').slice(0,16)", body)

    def test_approximate_timestamps_are_labelled_as_approximate(self):
        # 站点只给「1 周前」时换算值不是发布时间，界面必须照实说。
        self.assertPageContains("item.published_precision==='approximate'?`约 ${text}`")

    def test_release_variant_rows_show_when_not_a_meaningless_kind(self):
        self.assertPageContains("if(!label&&group.is_release)label=localTime(item.published_at).slice(5,10)")

    def test_release_rows_show_the_reply_body_not_the_thread_title(self):
        self.assertPageContains("const body=group.is_release")
        self.assertPageContains("'（仅附件）'")

    def test_thread_activity_is_not_called_a_version(self):
        self.assertPageContains("group.is_release?`${group.variants.length+1} 条动态`")

    def test_cross_site_duplicates_are_shown_as_another_source(self):
        self.assertPageContains("另见 ")
        self.assertPageContains("fbadge dup")

    def test_wip_has_its_own_badge(self):
        self.assertPageContains('<span class="fbadge wip">WIP</span>')

    def test_network_check_is_an_explicit_button_not_an_auto_refresh(self):
        self.assertPageContains("data-follow-check")
        # 「换一批」自动刷新绝不能顺手触发一次联网检查。
        self.assertPageContains(
            "if(location.pathname==='/follow'||location.pathname==='/follow-manage')return;")

    def test_every_entered_state_can_be_left_again(self):
        self.assertPageContains("""item.status==='seen'||item.status==='ignored'""")
        self.assertPageContains(">恢复未看</button>")

    def test_a_missing_evidence_archive_is_shown_not_swallowed(self):
        self.assertPageContains("检查完成，但证据未存档")
        self.assertPageContains("r.evidence_error")

    def test_credential_dependent_media_is_called_out(self):
        self.assertPageContains("媒体需要登录会话才能取，发现本身不需要")

    def test_follow_styles_exist_for_the_card_surface(self):
        for selector in (".followlist{", ".followitem{", ".fbadge{", ".fvariants{"):
            self.assertPageContains(selector)

    def test_the_check_button_stays_visible_on_a_narrow_viewport(self):
        # 标签条窄屏横滚会把主操作滚出视野；390 宽下它必须独占一行。
        self.assertPageContains(".follow .reviewtabs .fcheck{margin-left:0;flex:1 1 100%")


if __name__ == "__main__":
    unittest.main()
