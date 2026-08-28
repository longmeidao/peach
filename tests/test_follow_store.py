"""追更订阅与候选落地的隔离测试。全部使用临时数据库，绝不碰真实 ledger。"""
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from peach.follow import FollowSourceError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.follow_store import FollowStore, ReleaseGroup
from peach.migrations import discover


ROOT = Path(__file__).resolve().parents[1]
MOMENT = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)


def _candidate(external_id, title, **kwargs):
    kwargs.setdefault("provider", "rule34video")
    return FollowCandidate(external_id=external_id, title=title, **kwargs)


def _fetch(candidates, *, provider="rule34video", ref="lazyprocrastinator",
           semantics="work", raw=b"<html/>", **kwargs):
    return SourceFetch(
        provider=provider, ref=ref,
        request_url=f"https://{provider}.test/{ref}", semantics=semantics,
        candidates=tuple(candidates), raw_body=raw, **kwargs)


class _StoreCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.connection = sqlite3.connect(self.root / "ledger.db")
        self.connection.row_factory = sqlite3.Row
        self.addCleanup(self.connection.close)
        for migration in discover(ROOT / "migrations"):
            self.connection.executescript(migration.sql)
        self.store = FollowStore(lambda: self.connection,
                                 sources_root=self.root / "sources")

    def _entity(self, name="LazyProcrast", aliases=("LazyProcrastinator",)):
        cursor = self.connection.execute(
            "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
            " VALUES('creator',?,?,?,?)",
            (name, name.lower(), "2026-08-25T00:00:00Z", "2026-08-25T00:00:00Z"))
        entity_id = int(cursor.lastrowid)
        for alias in aliases:
            self.connection.execute(
                "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source)"
                " VALUES(?,?,?,'test')", (entity_id, alias, alias.lower()))
        return entity_id

    def _source(self, provider="rule34video", ref="lazyprocrastinator", **kwargs):
        kwargs.setdefault("label", "LazyProcrastinator")
        kwargs.setdefault("url", f"https://{provider}.test/{ref}")
        return self.store.register(provider=provider, ref=ref, moment=MOMENT, **kwargs)


class RegistrationTests(_StoreCase):
    def test_register_is_idempotent_and_updates_the_label(self):
        first = self._source()
        second = self._source(label="Lazy P")
        self.assertEqual(first, second)
        rows = self.store.sources()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["label"], "Lazy P")

    def test_rule34_case_variants_are_the_same_source(self):
        first = self._source(provider="rule34xxx", ref="LazyProcrastinator")
        second = self._source(provider="rule34xxx", ref="lazyprocrastinator")
        self.assertEqual(first, second)
        self.assertEqual(len(self.store.sources()), 1)
        self.assertEqual(self.store.sources()[0]["ref"], "lazyprocrastinator")

    def test_register_keeps_an_existing_entity_when_the_update_omits_it(self):
        entity_id = self._entity()
        self._source(entity_id=entity_id)
        self._source(label="again")
        self.assertEqual(self.store.sources()[0]["entity_id"], entity_id)

    def test_enabled_only_filters_disabled_sources(self):
        source_id = self._source()
        self._source(provider="kemono", ref="fanbox/30917150")
        self.store.set_enabled(source_id, False, moment=MOMENT)
        self.assertEqual([row["provider"] for row in self.store.sources(enabled_only=True)],
                         ["kemono"])

    def test_bad_semantics_is_rejected(self):
        with self.assertRaises(FollowSourceError):
            self._source(semantics="whatever")

    def test_creator_aliases_include_canonical_name_and_aliases(self):
        entity_id = self._entity()
        self.assertEqual(self.store.creator_aliases(entity_id),
                         ("LazyProcrast", "LazyProcrastinator"))
        self.assertEqual(self.store.creator_aliases(None), ())


class RecordTests(_StoreCase):
    def test_first_fetch_adds_items_and_classifies_variants(self):
        source_id = self._source(entity_id=self._entity())
        outcome = self.store.record(source_id, _fetch([
            _candidate("4542713", "Fiona - Paizuri"),
            _candidate("4542721", "Fiona - Paizuri (Nude)"),
            _candidate("4542899", "Mitsuru [WIP]"),
        ]), creator_aliases=self.store.creator_aliases(1), moment=MOMENT)
        self.assertEqual((outcome.added, outcome.updated, outcome.discovered), (3, 0, 3))
        kinds = {item.external_id: item.variant_kind for item in self.store.items()}
        self.assertEqual(kinds, {"4542713": "main", "4542721": "alt", "4542899": "wip"})

    def test_second_fetch_updates_without_resetting_user_state(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "Fiona - Paizuri")]),
                          moment=MOMENT)
        item = self.store.items()[0]
        self.store.set_status(item.id, "ignored")
        later = MOMENT + timedelta(hours=1)
        outcome = self.store.record(
            source_id, _fetch([_candidate("1", "Fiona - Paizuri", url="https://x.test/1")],
                              raw=b"<html>2</html>"), moment=later)
        self.assertEqual((outcome.added, outcome.updated), (0, 1))
        refreshed = self.store.items()[0]
        self.assertEqual(refreshed.status, "ignored")
        self.assertEqual(refreshed.url, "https://x.test/1")
        self.assertEqual(refreshed.first_seen_at, item.first_seen_at)
        self.assertNotEqual(refreshed.last_seen_at, item.last_seen_at)

    def test_not_modified_records_the_check_without_touching_items(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "A")]), moment=MOMENT)
        outcome = self.store.record(
            source_id, _fetch([], raw=None, not_modified=True), moment=MOMENT)
        self.assertTrue(outcome.not_modified)
        self.assertEqual(len(self.store.items()), 1)
        self.assertEqual(self.store.sources()[0]["last_status"], "not_modified")

    def test_conditional_cursor_is_stored_on_the_source_row(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "A")], etag='"v1"',
                                            last_modified="Mon, 25 Aug 2026 09:00:00 GMT"),
                          moment=MOMENT)
        row = self.store.sources()[0]
        self.assertEqual(row["etag"], '"v1"')
        self.assertEqual(row["last_modified"], "Mon, 25 Aug 2026 09:00:00 GMT")

    def test_raw_evidence_is_written_once_and_immutably(self):
        source_id = self._source()
        outcome = self.store.record(source_id, _fetch([_candidate("1", "A")]),
                                    moment=MOMENT)
        # evidence_path 是相对 `sources/` 的路径，分隔符随平台不同——不能写死 `/`。
        evidence = self.root / "sources" / Path(outcome.evidence_path)
        self.assertTrue(evidence.is_file())
        sidecar = json.loads(evidence.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(sidecar["candidates"], 1)
        self.assertEqual(sidecar["request_url"], "https://rule34video.test/lazyprocrastinator")

    def test_an_unusable_evidence_root_does_not_lose_the_candidates(self):
        """Mac 上 `peach-data/sources` 指向外置盘。盘不在时它是一条断链，
        `mkdir(exist_ok=True)` 会抛 `FileExistsError`（链接在、目标不在）。
        发现跟归档盘无关，不该让整次检查连同已抓到的候选一起炸掉。

        这里用「路径被普通文件占住」构造同一个 `FileExistsError`：断链要 symlink，
        而非管理员的 Windows 建不了 symlink，那样测试就只在一个平台成立。
        """
        (self.root / "evidence").write_text("not a directory", encoding="utf-8")
        store = FollowStore(lambda: self.connection,
                            sources_root=self.root / "evidence")
        source_id = store.register(provider="rule34video", ref="x", label="X",
                                   url="https://x.test/", moment=MOMENT)
        outcome = store.record(source_id, _fetch([_candidate("1", "Fiona - Paizuri")]),
                               moment=MOMENT)
        self.assertEqual(outcome.added, 1)
        self.assertIsNone(outcome.evidence_path)
        self.assertIn("证据未取得", outcome.evidence_error)
        item = store.items()[0]
        self.assertEqual(item.title, "Fiona - Paizuri")
        self.assertIsNone(item.metadata.get("evidence_path"))

    def test_a_readable_evidence_root_reports_no_error(self):
        source_id = self._source()
        outcome = self.store.record(source_id, _fetch([_candidate("1", "A")]),
                                    moment=MOMENT)
        self.assertIsNotNone(outcome.evidence_path)
        self.assertIsNone(outcome.evidence_error)

    def test_approximate_precision_is_carried_through_from_the_connector(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([
            _candidate("1", "A", published_at="2026-08-18T00:00:00Z",
                       extra={"published_precision": "approximate"}),
            _candidate("2", "B"),
        ]), moment=MOMENT)
        precision = {i.external_id: i.published_precision for i in self.store.items()}
        self.assertEqual(precision, {"1": "approximate", "2": "unknown"})

    def test_record_error_keeps_the_message_and_status(self):
        source_id = self._source()
        self.store.record_error(source_id, "HTTP 403", moment=MOMENT,
                                status="unauthorized")
        row = self.store.sources()[0]
        self.assertEqual(row["last_status"], "unauthorized")
        self.assertEqual(row["last_error"], "HTTP 403")

    def test_items_can_be_filtered_by_status(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "A"), _candidate("2", "B")]),
                          moment=MOMENT)
        self.store.set_status(self.store.items()[0].id, "seen")
        self.assertEqual(len(self.store.items(statuses=("new",))), 1)

    def test_an_ignored_item_can_be_restored_to_new(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "A")]), moment=MOMENT)
        item = self.store.items()[0]
        self.store.set_status(item.id, "ignored")
        self.store.set_status(item.id, "new")
        self.assertEqual(self.store.items()[0].status, "new")

    def test_saved_status_cannot_be_set_directly(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "A")]), moment=MOMENT)
        with self.assertRaises(FollowSourceError):
            self.store.set_status(self.store.items()[0].id, "saved")
        with self.assertRaises(FollowSourceError):
            self.store.set_status(self.store.items()[0].id, "nonsense")


class GroupingTests(_StoreCase):
    def _populate(self):
        video = self._source()
        booru = self._source(provider="rule34xxx", ref="lazyprocrastinator")
        self.store.record(video, _fetch([
            _candidate("4542713", "Fiona - Paizuri"),
            _candidate("4542721", "Fiona - Paizuri (Nude)"),
            _candidate("4542705", "Fiona - Missionary"),
        ]), moment=MOMENT)
        self.store.record(booru, _fetch([
            FollowCandidate(provider="rule34xxx", external_id="9988770",
                            title="fiona paizuri",
                            group_hint="rule34xxx:post:9988770"),
            FollowCandidate(provider="rule34xxx", external_id="9988776",
                            title="totally different filename",
                            title_is_name=False,
                            group_hint="rule34xxx:post:9988770"),
        ], provider="rule34xxx"), moment=MOMENT)

    def test_alt_folds_under_its_main_and_other_works_stay_apart(self):
        self._populate()
        groups = {g.primary.title: g for g in self.store.group(self.store.items())}
        self.assertIn("Fiona - Paizuri", groups)
        self.assertIn("Fiona - Missionary", groups)
        paizuri = groups["Fiona - Paizuri"]
        self.assertIn("Fiona - Paizuri (Nude)", [v.title for v in paizuri.variants])
        self.assertEqual(groups["Fiona - Missionary"].variants, ())

    def test_cross_site_duplicate_is_reported_separately_from_same_site_variants(self):
        self._populate()
        paizuri = next(g for g in self.store.group(self.store.items())
                       if g.primary.title == "Fiona - Paizuri")
        self.assertEqual(sorted(paizuri.providers), ["rule34video", "rule34xxx"])
        self.assertTrue(all(d.provider == "rule34xxx" for d in paizuri.duplicates))

    def test_group_hint_beats_an_unrelated_title(self):
        # booru 子帖的「标题」是标签拼的，和父帖毫无关系，只有来源声明的键能连起来。
        self._populate()
        groups = self.store.group(self.store.items())
        stray = [g for g in groups if g.primary.title == "totally different filename"]
        self.assertEqual(stray, [])

    def test_a_shared_origin_key_merges_two_different_sites(self):
        # 这是跨站去重真正靠得住的那条路：rule34.xxx 从 source 归一出的键，
        # 和 kemono 上同一帖子的键完全相同，标题再不一样也能精确合并。
        booru = self._source(provider="rule34xxx", ref="lazyprocrastinator")
        kemono = self._source(provider="kemono", ref="fanbox/30917150")
        self.store.record(booru, _fetch([
            FollowCandidate(provider="rule34xxx", external_id="18534395",
                            title="fiona · blush", title_is_name=False,
                            group_hint="fanbox:12304831"),
        ], provider="rule34xxx", ref="lazyprocrastinator"), moment=MOMENT)
        self.store.record(kemono, _fetch([
            FollowCandidate(provider="kemono", external_id="12304831",
                            title="Fiona - Paizuri", group_hint="fanbox:12304831"),
        ], provider="kemono", ref="fanbox/30917150"), moment=MOMENT)
        groups = self.store.group(self.store.items())
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0].providers), ["kemono", "rule34xxx"])

    def test_paheal_and_existing_sources_deduplicate_on_the_subscribestar_post(self):
        paheal = self._source(provider="rule34paheal", ref="initiala")
        mirror = self._source(provider="rule34xxx", ref="initiala")
        self.store.record(paheal, _fetch([
            FollowCandidate(provider="rule34paheal", external_id="7428820",
                            title="Amina · Tifa", title_is_name=False,
                            group_hint="subscribestar:2639932"),
        ], provider="rule34paheal", ref="initiala"), moment=MOMENT)
        self.store.record(mirror, _fetch([
            FollowCandidate(provider="rule34xxx", external_id="18540000",
                            title="Different tag label", title_is_name=False,
                            group_hint="subscribestar:2639932"),
        ], provider="rule34xxx", ref="initiala"), moment=MOMENT)
        groups = self.store.group(self.store.items())
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0].providers), ["rule34paheal", "rule34xxx"])

    def test_a_tag_derived_title_never_merges_two_works_on_its_own(self):
        # 标签拼出来的「标题」不是名字：同一作者标签相似的两条不能因此被并掉。
        source_id = self._source(provider="rule34xxx", ref="lazyprocrastinator")
        self.store.record(source_id, _fetch([
            FollowCandidate(provider="rule34xxx", external_id="1",
                            title="fiona · blush", title_is_name=False),
            FollowCandidate(provider="rule34xxx", external_id="2",
                            title="fiona · blush", title_is_name=False),
        ], provider="rule34xxx", ref="lazyprocrastinator"), moment=MOMENT)
        self.assertEqual(len(self.store.group(self.store.items())), 2)

    def test_wip_is_surfaced_on_the_group(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([
            _candidate("1", "Mitsuru School Movie"),
            _candidate("2", "Mitsuru School Movie [WIP]"),
        ]), moment=MOMENT)
        group = self.store.group(self.store.items())[0]
        self.assertTrue(group.has_wip)
        self.assertEqual(group.primary.variant_kind, "main")

    def test_groups_are_ordered_newest_first(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([
            _candidate("1", "Older", published_at="2026-08-01T00:00:00Z"),
            _candidate("2", "Newer", published_at="2026-08-20T00:00:00Z"),
        ]), moment=MOMENT)
        self.assertEqual([g.primary.title for g in self.store.group(self.store.items())],
                         ["Newer", "Older"])

    def test_empty_input_groups_to_nothing(self):
        self.assertEqual(self.store.group(()), ())

    def test_same_provider_title_collision_is_not_merged_under_work_semantics(self):
        # 实测踩到的：kemono 上「February Poll Animations」和「February Poll + Animations」
        # 归一化后完全相同，却是两个帖子。同站两个 main 撞车只说明标题判据到头了。
        source_id = self._source(provider="kemono", ref="fanbox/30917150")
        self.store.record(source_id, _fetch([
            FollowCandidate(provider="kemono", external_id="10",
                            title="February Poll + Animations",
                            published_at="2026-02-15T21:27:50Z"),
            FollowCandidate(provider="kemono", external_id="19",
                            title="February Poll Animations",
                            published_at="2026-01-31T22:10:13Z"),
        ], provider="kemono", ref="fanbox/30917150"), moment=MOMENT)
        groups = self.store.group(self.store.items())
        self.assertEqual(len(groups), 2)
        self.assertEqual([g.variants for g in groups], [(), ()])

    def test_an_alt_still_folds_when_its_provider_has_only_one_main(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([
            _candidate("1", "Fiona - Paizuri"),
            _candidate("2", "Fiona - Paizuri (Nude)"),
        ]), moment=MOMENT)
        groups = self.store.group(self.store.items())
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].variants), 1)

    def test_f95_resource_replies_are_independent_release_groups(self):
        source_id = self._source(provider="f95zone", ref="50685", semantics="release")
        self.store.record(source_id, _fetch([
            FollowCandidate(provider="f95zone", external_id="21383374",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            published_at="2026-08-21T04:14:09Z"),
            FollowCandidate(provider="f95zone", external_id="21394555",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            published_at="2026-08-22T18:09:23Z"),
        ], provider="f95zone", ref="50685", semantics="release"), moment=MOMENT)
        groups = self.store.group(self.store.items())
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(group.is_release for group in groups))
        self.assertTrue(all(group.variants == () for group in groups))
        # 最新楼层排在前面，但不会把较早的资源楼层吞成「动态」。
        self.assertEqual(groups[0].primary.external_id, "21394555")
        self.assertEqual(groups[0].primary.version, "2026-06-28")


class SaveAssetTests(_StoreCase):
    def _one_item(self, **candidate_kwargs):
        entity_id = self._entity()
        source_id = self._source(entity_id=entity_id)
        candidate_kwargs.setdefault("url", "https://rule34video.com/video/4542713/x/")
        candidate_kwargs.setdefault("duration", 20.0)
        self.store.record(
            source_id,
            _fetch([_candidate("4542713", "Fiona - Paizuri", **candidate_kwargs)]),
            moment=MOMENT)
        return entity_id, self.store.items()[0]

    def test_saving_requires_explicit_confirmation(self):
        _, item = self._one_item()
        with self.assertRaises(FollowSourceError):
            self.store.save_asset(item.id)
        self.assertEqual(self.connection.execute(
            "SELECT count(*) FROM asset").fetchone()[0], 0)

    def test_confirmed_save_creates_one_online_asset_and_links_the_creator(self):
        entity_id, item = self._one_item(published_at="2026-08-18T06:23:33Z")
        asset_id = self.store.save_asset(item.id, confirm=True, moment=MOMENT)
        row = self.connection.execute(
            "SELECT location,path,name,medium,creator,duration,release_date FROM asset"
            " WHERE id=?", (asset_id,)).fetchone()
        self.assertEqual(row["location"], "online")
        self.assertEqual(row["path"], "https://rule34video.com/video/4542713/x/")
        self.assertEqual(row["medium"], "video")
        self.assertEqual(row["creator"], "LazyProcrast")
        self.assertEqual(row["release_date"], "2026-08-18")
        relation = self.connection.execute(
            "SELECT role,source FROM asset_entity WHERE asset_id=? AND entity_id=?",
            (asset_id, entity_id)).fetchone()
        self.assertEqual((relation["role"], relation["source"]),
                         ("creator", "follow:rule34video"))
        self.assertEqual(self.store.items()[0].status, "saved")

    def test_saving_twice_is_idempotent(self):
        _, item = self._one_item()
        first = self.store.save_asset(item.id, confirm=True, moment=MOMENT)
        second = self.store.save_asset(item.id, confirm=True, moment=MOMENT)
        self.assertEqual(first, second)
        self.assertEqual(self.connection.execute(
            "SELECT count(*) FROM asset").fetchone()[0], 1)

    def test_an_existing_online_asset_is_reused_not_duplicated(self):
        _, item = self._one_item()
        self.connection.execute(
            "INSERT INTO asset(location,path,name) VALUES('online',?,'existing')",
            (item.url,))
        asset_id = self.store.save_asset(item.id, confirm=True, moment=MOMENT)
        self.assertEqual(self.connection.execute(
            "SELECT name FROM asset WHERE id=?", (asset_id,)).fetchone()[0], "existing")

    def test_kemono_posts_without_duration_are_saved_as_illustrations(self):
        source_id = self._source(provider="kemono", ref="fanbox/30917150")
        self.store.record(source_id, _fetch(
            [FollowCandidate(provider="kemono", external_id="11406814", title="VVD 7",
                             url="https://kemono.cr/fanbox/user/30917150/post/11406814")],
            provider="kemono", ref="fanbox/30917150"), moment=MOMENT)
        asset_id = self.store.save_asset(self.store.items()[0].id, confirm=True,
                                         moment=MOMENT)
        self.assertEqual(self.connection.execute(
            "SELECT medium FROM asset WHERE id=?", (asset_id,)).fetchone()[0],
            "illustration")

    def test_a_candidate_without_a_page_url_cannot_be_saved(self):
        source_id = self._source()
        self.store.record(source_id, _fetch([_candidate("1", "No URL")]), moment=MOMENT)
        with self.assertRaises(FollowSourceError):
            self.store.save_asset(self.store.items()[0].id, confirm=True)

    def test_missing_item_is_an_error(self):
        with self.assertRaises(FollowSourceError):
            self.store.save_asset(9999, confirm=True)


class ReleaseGroupTests(unittest.TestCase):
    def test_group_is_immutable(self):
        group = ReleaseGroup("k", None, (), ())
        with self.assertRaises(Exception):
            group.release_key = "other"


if __name__ == "__main__":
    unittest.main()
