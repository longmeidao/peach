"""既有库边车识别和统一处理的隔离回归。"""
import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import closing

from filelock import FileLock

from peach.library_nfo import read_nfo, sidecars, local_art
from peach.library_processing import (STALL_AFTER_SECONDS, decorate, issues_path,
                                      process_library, snapshot, state_path, _fields)
from peach.review_csv import read_rows
from peach.settings_file import PeachConfig
from peach.web_review import _apply_metadata_candidate
from support.ledger import fresh_ledger


class LibraryNfoTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_javboss_fields_and_original_tags(self):
        path = self.root / 'sample.nfo'
        path.write_text('<movie><generator>JavBoss</generator><uniqueid type="javboss">ABW-358</uniqueid>'
            '<title>作品</title><originaltitle>原題</originaltitle><set><name>系列</name></set>'
            '<premiered>2023-05-26</premiered><runtime>210</runtime><actor><name>涼森れむ</name></actor>'
            '<genre>自定义标签</genre><tag>有码</tag></movie>', encoding='utf-8')
        payload, raw = read_nfo(path)
        self.assertEqual(payload['id'], 'ABW-358')
        self.assertEqual(payload['source_generator'], 'JavBoss')
        self.assertIn('自定义标签', _fields(payload)['tags']['value'])
        self.assertEqual(payload['runtime'], '210')
        self.assertEqual(raw, path.read_bytes())

    def test_movie_sidecar_only_when_unambiguous_and_named_file_preferred(self):
        video = self.root / 'one.mp4'
        video.touch()
        common = self.root / 'movie.nfo'
        common.touch()
        self.assertEqual(sidecars(video)[0], common)
        (self.root / 'two.mkv').touch()
        self.assertIsNone(sidecars(video)[0])
        named = self.root / 'one.NFO'
        named.touch()
        self.assertEqual(sidecars(video)[0], named)

    def test_episode_and_plain_set_without_jav_identity(self):
        path = self.root / 'episode.nfo'
        path.write_text('<episodedetails><title>Episode</title><uniqueid type="tmdb">123</uniqueid>'
            '<set>Collection</set><aired>2024-01-02</aired></episodedetails>', encoding='utf-8')
        payload, _ = read_nfo(path)
        self.assertEqual(payload['id'], '')
        self.assertEqual(payload['series'], 'Collection')
        self.assertEqual(payload['release_date'], '2024-01-02')

    def test_jav_id_and_imdb_id_have_distinct_meanings(self):
        path = self.root / 'movie.nfo'
        path.write_text('<movie><id>ABW-358</id></movie>', encoding='utf-8')
        self.assertEqual(read_nfo(path)[0]['id'], 'ABW-358')
        path.write_text('<movie><id>tt1234567</id></movie>', encoding='utf-8')
        self.assertEqual(read_nfo(path)[0]['id'], '')

    def test_entity_declarations_rejected_in_utf16(self):
        path = self.root / 'unsafe.nfo'
        path.write_bytes('<!DOCTYPE movie [<!ENTITY x "test">]><movie><title>&x;</title></movie>'.encode('utf-16'))
        with self.assertRaises(ValueError):
            read_nfo(path)

    def test_art_cannot_escape_media_directory(self):
        folder = self.root / 'film'
        folder.mkdir()
        (self.root / 'outside.jpg').touch()
        self.assertIsNone(local_art(folder / 'film.mp4', {'local_art': '../outside.jpg'}))
        self.assertIsNone(local_art(folder / 'film.mp4', {'local_art': 'https://example.com/poster.jpg'}))

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_scan_import_and_explicit_review_use_exact_asset(self):
        media = self.root / 'media'
        media.mkdir()
        video = media / 'film.mp4'
        video.write_bytes(b'video')
        (media / 'movie.nfo').write_text('<movie><title>Local title</title><tag>自定义标签</tag></movie>', encoding='utf-8')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        factory = Mock()
        result = process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertEqual(result['status'], 'complete')
        factory.assert_not_called()
        groups = read_rows(self.root / 'generated/library-metadata-field-candidates.csv')
        title = next(row for row in groups if row['field'] == 'title')
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.row_factory = sqlite3.Row
            self.assertIsNone(connection.execute('SELECT catalog_title FROM asset WHERE medium="video"').fetchone()[0])
            candidate = json.loads(title['candidates_json'])[0]
            self.assertEqual(_apply_metadata_candidate(connection, title, candidate, '2026-09-06'), 1)
            self.assertEqual(connection.execute('SELECT catalog_title FROM asset WHERE medium="video"').fetchone()[0], 'Local title')
            title['asset_path'] = 'moved.mp4'
            with self.assertRaises(ValueError):
                _apply_metadata_candidate(connection, title, candidate, '2026-09-06')
        self.assertEqual(snapshot(config)['status'], 'complete')

    def test_status_reads_do_not_start_processing(self):
        from peach.web_library_processing import q_library_processing
        from unittest.mock import patch
        contract = Mock()
        contract.library_processing_job.snapshot.return_value = {'status': 'running', 'job_id': 'one'}
        with patch('peach.web_library_processing.process_library') as worker:
            self.assertEqual(q_library_processing(contract, {})['job_id'], 'one')
            worker.assert_not_called()

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_no_code_video_pairs_with_its_sibling_image_without_nfo(self):
        """无番号、无 NFO 的视频也拿同目录图片当海报，落在 `{id}_4.jpg`。"""
        from PIL import Image
        media = self.root / 'media'
        media.mkdir()
        (media / '梓怡-背著老公.mp4').write_bytes(b'video')
        Image.new('RGB', (24, 36), (180, 120, 90)).save(media / '梓怡-背著老公.png')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True,
                             locations={'local': (str(media),)})
        result = process_library(config, db, self.root / 'generated',
                                 self.root / 'covers', provider_factory=Mock())
        with closing(sqlite3.connect(db)) as connection:
            asset_id = connection.execute(
                "SELECT id FROM asset WHERE name='梓怡-背著老公.mp4'").fetchone()[0]
        self.assertEqual(result['covers'], 1)
        self.assertTrue(
            (self.root / 'generated' / 'posters' / f'{asset_id}_4.jpg').is_file())

    def test_reader_cannot_scan_or_create_candidates(self):
        from peach.settings_file import ReplicationSettings
        config = PeachConfig(self.root, self.root / 'config.toml', replication=ReplicationSettings(enabled=True))
        with self.assertRaisesRegex(ValueError, '只读端'):
            process_library(config, self.root / 'ledger.db', self.root / 'generated', self.root / 'covers')
        self.assertFalse((self.root / 'generated').exists())
        self.assertFalse((self.root / 'ledger.db').exists())

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_local_metadata_remote_completion_and_repeat_are_one_pipeline(self):
        from PIL import Image
        media = self.root / 'media'
        media.mkdir()
        video = media / 'ABW-358.mp4'
        video.write_bytes(b'video')
        (media / 'ABW-358.nfo').write_text('<movie><title>Local title</title><sorttitle>ABW-358</sorttitle>'
            '<premiered>2023-05-26</premiered><actor><name>涼森れむ</name></actor><tag>自定义标签</tag></movie>', encoding='utf-8')
        Image.new('RGB', (40, 60), 'blue').save(media / 'ABW-358-poster.jpg')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'maker': 'Studio', 'id': 'ABW-358', 'director': 'Director', 'runtime': 210}
        factory = Mock(return_value=provider)
        result = process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['identified'], 1)
        self.assertEqual(result['covers'], 1)
        provider.cover.assert_not_called()
        provider.query.assert_called_once()
        self.assertEqual(provider.query.call_args.args, ('ABW-358', 'r18dev'))
        self.assertIn('deadline', provider.query.call_args.kwargs)
        groups = read_rows(self.root / 'generated/library-metadata-field-candidates.csv')
        studio = next(row for row in groups if row['field'] == 'studio')
        self.assertEqual(json.loads(studio['candidates_json'])[0]['catalog_evidence']['runtime']['value'], 210)
        second = process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertEqual(second['status'], 'complete')
        self.assertEqual(second['candidates'], result['candidates'])
        provider.query.assert_called_once()

    def test_korean_mib_codes_ask_no_jav_source_for_metadata_or_cover(self):
        """`HA-101` 是 MIB 的编号，也是一部日本片的番号：问了就取回那部日本片。"""
        media = self.root / 'media'
        media.mkdir()
        for name in ('HA-101.mp4', 'ABW-001.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'maker': 'Studio', 'id': 'ABW-001', 'source_url': ''}
        provider.cover.return_value = False
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 provider_factory=Mock(return_value=provider))
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['identified'], 2)
        self.assertEqual([item.args[0] for item in provider.query.call_args_list], ['ABW-001'])
        self.assertEqual([item.args[0] for item in provider.cover.call_args_list], ['ABW-001'])

    def test_management_controls_keep_credentials_and_empty_sections_visible(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'web/app.js').read_text(encoding='utf-8')
        self.assertIn('wireFollowManage(creds)', source)
        self.assertIn('const sources=[...credentials,...(followData?.sources||[])];', source)
        self.assertIn('data-srcfilter-config=', source)
        self.assertNotIn("if(!providers.length){mount.innerHTML='';return}", source)
        self.assertIn("needsAttention?' open':''", source)
        self.assertIn('还没有内容标签', source)
        self.assertIn('还没有存储来源', source)
        self.assertIn("catalogEmptyHtml({configurable:runtimeConfigurable})}</div>", source)
        self.assertIn("unmountIsland($('#libraryProcessingNotice'))", source)
        self.assertIn("mode:'notice'", source)
        configuration = (root / 'frontend/src/islands/configuration.tsx').read_text(encoding='utf-8')
        self.assertNotIn("'/api/library-processing'", configuration)
        self.assertIn('toast,monitor:true,onComplete:', source)


class LibraryWatchdogTests(unittest.TestCase):
    """扫描与采集任务的进度心跳、卡住提示、预算与失败项重试。"""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def _config(self, media):
        return PeachConfig(self.root, self.root / 'config.toml', present=True,
                           locations={'local': (str(media),)})

    def _provider(self):
        provider = Mock()
        provider.query.return_value = {'id': 'code', 'maker': 'Studio', 'source_url': ''}
        provider.cover.return_value = False
        return provider

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_reports_carry_current_asset_action_and_rising_sequence(self):
        media = self.root / 'media'
        media.mkdir()
        for name in ('ABW-001.mp4', 'ABW-002.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        reports = []
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 provider_factory=lambda: self._provider(), report=reports.append)
        actions = [row['current_action'] for row in reports]
        names = {row['current_asset_name'] for row in reports if row['current_asset_name']}
        self.assertEqual(names, {'ABW-001.mp4', 'ABW-002.mp4'})
        self.assertIn('reading_local', actions)
        self.assertIn('querying_metadata', actions)
        self.assertIn('fetching_cover', actions)
        sequences = [row['progress_seq'] for row in reports]
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(len(set(sequences)), len(sequences))
        self.assertEqual(result['status'], 'complete')
        self.assertIsNone(result['current_asset_id'])
        self.assertEqual(result['current_action'], '')

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_issue_preview_is_capped_while_the_log_keeps_every_row(self):
        media = self.root / 'media'
        media.mkdir()
        for index in range(25):
            (media / f'样品{index:02d}.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        result = process_library(config, db, self.root / 'generated', self.root / 'covers')
        self.assertEqual(result['issue_count'], 25)
        self.assertEqual(len(result['issue_preview']), 20)
        self.assertTrue(result['issues_truncated'])
        log = issues_path(config, result['job_id'])
        self.assertEqual(len([line for line in log.read_text(encoding='utf-8').splitlines() if line]), 25)
        from peach.web_library_processing import q_library_processing_issues
        contract = Mock()
        contract.library_processing_job.snapshot.return_value = {'status': 'running', 'job_id': result['job_id']}
        with patch('peach.web_library_processing.settings_file.active', return_value=config):
            page = q_library_processing_issues(contract, {'job_id': result['job_id'], 'offset': 20, 'limit': 5})
        self.assertEqual(page['total'], 25)
        self.assertEqual(len(page['rows']), 5)
        logged = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line]
        self.assertEqual(page['rows'], logged[20:25])

    def test_status_read_recovers_the_log_path_left_by_an_earlier_job(self):
        """上一趟任务的状态文件里没有这个字段，它那份完整清单却还在磁盘上。"""
        from peach.web_library_processing import q_library_processing
        config = self._config(self.root / 'media')
        log = issues_path(config, 'old')
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(json.dumps({'asset_id': 1, 'message': '未识别到番号'}) + '\n', encoding='utf-8')
        state_path(config).write_text(json.dumps({'status': 'failed', 'job_id': 'old', 'issue_count': 1}),
                                      encoding='utf-8')
        contract = Mock()
        contract.library_processing_job.snapshot.return_value = None
        with patch('peach.web_library_processing.settings_file.active', return_value=config):
            self.assertEqual(q_library_processing(contract, {})['issues_log'], str(log))

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_each_issue_names_the_item_its_path_and_where_the_full_log_is(self):
        """一句「未识别到番号」加一个链接，是哪个文件得逐个点开才知道；改名或去磁盘上
        确认时要用的是路径。完整清单的地址跟着状态一起给出，不让人按 job_id 自己去拼。
        """
        media = self.root / 'media'
        media.mkdir()
        (media / '样品.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        result = process_library(config, db, self.root / 'generated', self.root / 'covers')
        preview = result['issue_preview'][0]
        self.assertEqual(preview['title'], '样品.mp4')
        self.assertTrue(preview['path'].endswith('样品.mp4'), preview['path'])
        self.assertEqual(result['issues_log'], str(issues_path(config, result['job_id'])))
        log = issues_path(config, result['job_id'])
        logged = json.loads(log.read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(logged['title'], '样品.mp4')
        self.assertEqual(logged['path'], preview['path'])

    def test_stalled_warning_never_flips_a_live_task_to_failed(self):
        config = self._config(self.root / 'media')
        path = state_path(config)
        path.parent.mkdir(parents=True, exist_ok=True)
        old = time.time() - (STALL_AFTER_SECONDS + 30)
        path.write_text(json.dumps({'status': 'running', 'job_id': 'one', 'started_at': old,
                                    'last_progress_at': old, 'current_started_at': old,
                                    'current_action': 'reading_local'}), encoding='utf-8')
        with FileLock(str(path) + '.lock', timeout=0):
            live = snapshot(config)
        self.assertEqual(live['status'], 'running')
        self.assertTrue(live['stalled'])
        dead = snapshot(config)
        self.assertEqual(dead['status'], 'failed')
        self.assertIn('中断', dead['error'])
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['status'], 'failed')
        # 另一个读取者正好占着锁时读到的也是同一个结论，不会跳回「运行中」。
        with FileLock(str(path) + '.lock', timeout=0):
            again = snapshot(config)
        self.assertEqual(again['status'], 'failed')
        self.assertNotIn('stalled', again)

    def test_deadline_within_budget_is_running_and_expired_is_stalled(self):
        now = time.time()
        within = decorate({'status': 'running', 'last_progress_at': now - 300,
                           'current_deadline_at': now + 30}, now=now)
        expired = decorate({'status': 'running', 'last_progress_at': now - 300,
                            'current_deadline_at': now - 1}, now=now)
        self.assertFalse(within['stalled'])
        self.assertTrue(expired['stalled'])

    def test_legacy_issue_list_projects_into_count_and_preview(self):
        legacy = [{'asset_id': index, 'message': '未识别到番号'} for index in range(1, 26)]
        state = decorate({'status': 'failed', 'job_id': 'old', 'issues': legacy})
        self.assertNotIn('issues', state)
        self.assertEqual(state['issue_count'], 25)
        self.assertEqual(len(state['issue_preview']), 20)
        self.assertEqual(state['issue_preview'][0],
                         {'asset_id': 1, 'title': '', 'path': '', 'message': '未识别到番号'})
        self.assertTrue(state['issues_truncated'])

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_deadline_skips_one_asset_and_keeps_processing(self):
        from peach.jav_cover_fetch import DeadlineExceeded
        media = self.root / 'media'
        media.mkdir()
        for name in ('ABW-101.mp4', 'ABW-102.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        provider = self._provider()
        provider.query.side_effect = [DeadlineExceeded('预算'), provider.query.return_value]
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 provider_factory=lambda: provider)
        with closing(sqlite3.connect(db)) as connection:
            ids = {name: row_id for name, row_id in connection.execute('SELECT name, id FROM asset')}
        self.assertEqual(result['retryable_asset_ids'], [ids['ABW-101.mp4']])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(provider.query.call_count, 2)
        self.assertEqual(provider.reset.call_count, 1)

    @unittest.skipUnless(os.name == 'nt', '真实声明根使用 Windows 盘符')
    def test_retry_skips_rescan_and_touches_only_listed_assets(self):
        media = self.root / 'media'
        media.mkdir()
        for name in ('ABW-201.mp4', 'ABW-202.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        provider = self._provider()
        first = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                provider_factory=lambda: provider)
        self.assertEqual(first['total'], 2)
        with closing(sqlite3.connect(db)) as connection:
            ids = {name: row_id for name, row_id in connection.execute('SELECT name, id FROM asset')}
        provider.reset_mock()
        with patch('peach.library_processing.scan_location') as scan:
            retried = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                      retry_ids=[ids['ABW-202.mp4']],
                                      provider_factory=lambda: provider)
        scan.assert_not_called()
        self.assertEqual(retried['total'], 1)
        self.assertEqual(retried['checked'], 1)
        self.assertEqual(retried['status'], 'complete')

    def test_retry_request_accepts_only_the_previous_failure_set(self):
        from peach.web_library_processing import _retry_ids
        previous = {'job_id': 'one', 'retryable_asset_ids': [130, 131]}
        self.assertIsNone(_retry_ids(previous, {}))
        self.assertEqual(_retry_ids(previous, {'job_id': 'one', 'retry': [130]}), [130])
        self.assertEqual(_retry_ids(previous, {'job_id': 'one', 'retry': []}), [130, 131])
        with self.assertRaises(ValueError):
            _retry_ids(previous, {'job_id': 'old', 'retry': [130]})
        with self.assertRaises(ValueError):
            _retry_ids(previous, {'job_id': 'one', 'retry': [999]})
        with self.assertRaises(ValueError):
            _retry_ids(previous, {'job_id': 'one', 'retry': 'all'})

    def test_fetch_refuses_to_start_after_its_budget_is_gone(self):
        from peach.jav_cover_fetch import DeadlineExceeded, _fetch
        transport = Mock()
        with self.assertRaises(DeadlineExceeded):
            _fetch(transport, 'https://example.com/a.jpg', referer='https://example.com/',
                   limit=100, deadline=time.monotonic() - 1)
        transport.assert_not_called()

    def test_fetch_clamps_each_attempt_to_the_remaining_budget(self):
        from peach.jav_cover_fetch import _fetch
        transport = Mock()
        transport.return_value = Mock(status=200, body=b'x')
        _fetch(transport, 'https://example.com/a.jpg', referer='https://example.com/',
               limit=100, deadline=time.monotonic() + 5)
        timeout = transport.call_args.args[1]
        self.assertGreater(timeout, 4)
        self.assertLessEqual(timeout, 5)
