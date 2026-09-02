"""「检查更新」这一段共用流程本身的测试。

以前 Web 与命令行各写一遍，两份不等价：命令行没有往回翻页、没有凭据到位后的强制
重取、也不学官方渠道的作者别名。这里锁住「同一句检查更新在两处做同样的事」。
"""
import contextlib
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from peach.follow import FollowHistoryEnd, FollowSourceError
from peach.follow_check import plan_check, run_check
from peach.follow_secrets import CredentialError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.follow_store import FollowStore
from peach.migrations import discover


ROOT = Path(__file__).resolve().parents[1]
MOMENT = datetime(2026, 9, 3, tzinfo=timezone.utc)


class _Credentials:
    """只回答「有没有配」的凭据仓库替身；不带任何真实凭据值。"""

    def __init__(self, providers=()):
        self._providers = set(providers)

    def load(self, provider):
        return object() if provider in self._providers else None


class _Connector:
    def __init__(self, fetch=None, error=None):
        self._fetch, self._error = fetch, error
        self.calls = []

    def fetch(self, ref, *, etag=None, last_modified=None, page=0):
        self.calls.append({"ref": ref, "etag": etag,
                           "last_modified": last_modified, "page": page})
        if self._error is not None:
            raise self._error
        return self._fetch


def _fetch(provider="fanbox", ref="ffxivinitiala", **kwargs):
    base = dict(provider=provider, ref=ref, semantics="work",
                request_url=f"https://{ref}.fanbox.cc/")
    base.update(kwargs)
    return SourceFetch(**base)


class _CheckCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.connection = sqlite3.connect(self.root / "ledger.db")
        self.connection.row_factory = sqlite3.Row
        for migration in discover(ROOT / "migrations"):
            self.connection.executescript(migration.sql)
        self.connection.commit()
        self.addCleanup(self.connection.close)
        self.store = FollowStore(lambda: self.connection,
                                 sources_root=self.root / "sources")

    @contextlib.contextmanager
    def writer(self):
        yield self.store

    def _register(self, **kwargs):
        base = dict(provider="fanbox", ref="ffxivinitiala", label="Initiala",
                    url="https://ffxivinitiala.fanbox.cc/", semantics="work")
        base.update(kwargs)
        return self.store.register(**base)

    def _row(self, source_id):
        return next(dict(row) for row in self.store.sources()
                    if row["id"] == source_id)

    def _run(self, source_id, connector, **kwargs):
        return run_check(self._row(source_id), credentials=_Credentials(),
                         writer=self.writer,
                         connector_factory=lambda provider, **kw: connector,
                         moment=MOMENT, **kwargs)


class PlanCheckTests(_CheckCase):
    def test_only_enabled_sources_are_planned(self):
        first = self._register()
        second = self._register(ref="other", url="https://other.fanbox.cc/")
        self.store.set_enabled(second, False)
        planned = plan_check(self.store, _Credentials())
        self.assertEqual([row["id"] for row in planned], [first])

    def test_paging_back_is_offered_only_where_it_actually_works(self):
        """官方渠道没有历史分页；把它列进往回翻页只会白打一次请求。"""
        self._register()
        archive = self._register(provider="kemono", ref="fanbox/1",
                                 url="https://kemono.cr/fanbox/user/1")
        planned = plan_check(self.store, _Credentials(), older=True,
                             backfill_providers=frozenset({"kemono"}))
        self.assertEqual([row["id"] for row in planned], [archive])

    def test_a_credential_that_just_arrived_forces_one_unconditional_refetch(self):
        """凭据到位而旧候选还标着 needs_credential 时必须绕过条件请求游标。

        否则上游回 304，旧解析结果永久不变——配了凭据却什么都没变，用户没法自己
        看出原因。这一条以前只有 Web 那份有。
        """
        source_id = self._register(provider="rule34xxx", ref="tag",
                                   url="https://rule34.xxx/?tags=tag")
        self.store.record(source_id, _fetch(
            provider="rule34xxx", ref="tag", candidates=(
                FollowCandidate(provider="rule34xxx", external_id="1", title="a",
                                extra={"media_needs_credential": True}),)),
            moment=MOMENT)
        planned = plan_check(self.store, _Credentials({"rule34xxx"}))
        self.assertTrue(planned[0]["force_media_reparse"])
        without = plan_check(self.store, _Credentials())
        self.assertFalse(without[0]["force_media_reparse"],
                         "没配凭据就没有可生效的重解析，不该白打一次无条件请求")

    def test_paging_back_never_forces_a_refetch(self):
        """往回翻的那一页本来就没有游标，强制重取没有意义。"""
        source_id = self._register(provider="rule34xxx", ref="tag",
                                   url="https://rule34.xxx/?tags=tag")
        self.store.record(source_id, _fetch(
            provider="rule34xxx", ref="tag", candidates=(
                FollowCandidate(provider="rule34xxx", external_id="1", title="a",
                                extra={"media_needs_credential": True}),)),
            moment=MOMENT)
        planned = plan_check(self.store, _Credentials({"rule34xxx"}), older=True,
                             backfill_providers=frozenset({"rule34xxx"}))
        self.assertFalse(planned[0]["force_media_reparse"])

    def test_force_applies_to_every_source(self):
        """命令行的 `--force` 是无条件的，不依赖任何 needs_credential 痕迹。"""
        self._register()
        planned = plan_check(self.store, _Credentials(), force=True)
        self.assertTrue(planned[0]["force_media_reparse"])


class RunCheckTests(_CheckCase):
    def test_a_normal_check_reads_the_first_page_with_the_stored_cursors(self):
        source_id = self._register()
        self.store.record(source_id, _fetch(etag='W/"1"', last_modified="Mon"),
                          moment=MOMENT)
        connector = _Connector(_fetch(not_modified=True))
        result = self._run(source_id, connector)
        self.assertTrue(result.ok)
        self.assertEqual(connector.calls, [{"ref": "ffxivinitiala", "etag": 'W/"1"',
                                            "last_modified": "Mon", "page": 0}])
        self.assertTrue(result.outcome.not_modified)

    def test_paging_back_asks_for_the_next_page_and_drops_the_cursors(self):
        source_id = self._register(provider="kemono", ref="fanbox/1",
                                   url="https://kemono.cr/fanbox/user/1")
        connector = _Connector(_fetch(provider="kemono", ref="fanbox/1"))
        result = self._run(source_id, connector, older=True)
        self.assertEqual(result.page, 1)
        self.assertTrue(result.older)
        self.assertEqual(connector.calls[0]["page"], 1)
        # 第二次再往回，接着上一次走到的位置。
        connector = _Connector(_fetch(provider="kemono", ref="fanbox/1"))
        self.assertEqual(self._run(source_id, connector, older=True).page, 2)

    def test_the_end_of_history_is_recorded_not_reported_as_a_failure(self):
        source_id = self._register(provider="kemono", ref="fanbox/1",
                                   url="https://kemono.cr/fanbox/user/1")
        result = self._run(source_id, _Connector(error=FollowHistoryEnd("400")),
                           older=True)
        self.assertTrue(result.ok)
        self.assertTrue(result.exhausted)
        self.assertEqual(result.message, "没有更多历史内容")
        self.assertEqual(self._row(source_id)["last_status"], "not_modified")
        self.assertEqual(self._row(source_id)["backfill_page"], 0,
                         "翻到尽头不推进游标，否则下一次会跳过真实存在的一页")

    def test_a_missing_credential_is_its_own_status(self):
        source_id = self._register()
        result = self._run(source_id,
                           _Connector(error=CredentialError("需要 user_id 与 api_key")))
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "unauthorized")
        self.assertEqual(result.error, "需要 user_id 与 api_key")
        self.assertEqual(self._row(source_id)["last_status"], "unauthorized")
        self.assertNotIn("api_key", str(result.fetch or ""))

    def test_a_source_failure_is_a_return_value_not_an_exception(self):
        """逐条独立成败：一个来源被挡住不该让其余来源的更新一起消失。"""
        source_id = self._register()
        result = self._run(source_id, _Connector(error=FollowSourceError("HTTP 503")))
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "error")
        self.assertEqual(self._row(source_id)["last_status"], "error")

    def test_an_official_profile_handle_is_learned_from_one_unambiguous_author(self):
        """fanbox 的 ref 就是作者本人的手柄，可以直接学成别名。

        这一条以前只在 Web 那份检查里有，`peach follow check` 抓同一条来源不会学，
        于是同一个人在命令行抓完之后仍然显示成两个作者。
        """
        source_id = self._register()
        result = self._run(source_id, _Connector(_fetch(candidates=(
            FollowCandidate(provider="fanbox", external_id="1", title="a",
                            author="Initiala"),
            FollowCandidate(provider="fanbox", external_id="2", title="b",
                            author="Initiala"),
        ))))
        self.assertEqual(result.author_alias_learned,
                         {"canonical": "Initiala", "alias": "ffxivinitiala",
                          "source": "official:fanbox"})
        mapping, _groups = self.store.author_aliases()
        self.assertEqual(mapping["ffxivinitiala"], "initiala")

    def test_two_different_authors_in_one_fetch_teach_nothing(self):
        source_id = self._register()
        result = self._run(source_id, _Connector(_fetch(candidates=(
            FollowCandidate(provider="fanbox", external_id="1", title="a",
                            author="Initiala"),
            FollowCandidate(provider="fanbox", external_id="2", title="b",
                            author="Someone Else"),
        ))))
        self.assertIsNone(result.author_alias_learned)
        self.assertEqual(self.store.author_aliases(), ({}, []))

    def test_an_archive_ref_is_never_learned_as_an_author_name(self):
        """`fanbox/30917150` 里的数字 id 不是名字，学成别名会造出一个假作者。"""
        source_id = self._register(provider="kemono", ref="fanbox/30917150",
                                   url="https://kemono.cr/fanbox/user/30917150")
        result = self._run(source_id, _Connector(_fetch(
            provider="kemono", ref="fanbox/30917150", candidates=(
                FollowCandidate(provider="kemono", external_id="1", title="a",
                                author="Initiala"),))))
        self.assertIsNone(result.author_alias_learned)
        self.assertEqual(self.store.author_aliases(), ({}, []))


if __name__ == "__main__":
    unittest.main()
