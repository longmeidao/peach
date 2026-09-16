"""既有库边车识别和统一处理的隔离回归。"""
import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import closing

from filelock import FileLock

from peach.field_owners import owner_of, review_owner
from peach.library_nfo import read_nfo, sidecars, local_art
from peach.library_processing import (STALL_AFTER_SECONDS, decorate, issues_path,
                                      process_library, snapshot, state_path, _fields)
from peach.review_csv import read_rows
from peach.settings_file import PeachConfig
from peach.web_review import _apply_metadata_candidate
from support.conditions import windows_ledger_roots
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

    def test_numbered_image_set_beside_the_video_is_not_its_poster(self):
        gallery = self.root / 'gallery'
        gallery.mkdir()
        video = gallery / 'TG@BOT- (1).mp4'
        for name in ('TG@BOT- (1).mp4', 'TG@BOT- (1).jpg', 'TG@BOT- (2).jpg', 'TG@BOT- (10).jpg'):
            (gallery / name).touch()
        self.assertEqual(sidecars(video)[1], [])
        (gallery / 'cover.jpg').touch()
        self.assertEqual(sidecars(video)[1], [gallery / 'cover.jpg'])

    def test_releases_sharing_a_folder_keep_their_same_name_posters(self):
        for code in ('ABC-123', 'ABC-124'):
            (self.root / f'{code}.mp4').touch()
            (self.root / f'{code}.jpg').touch()
        (self.root / 'ABC-123-fanart.jpg').touch()
        self.assertEqual(sidecars(self.root / 'ABC-123.mp4')[1], [self.root / 'ABC-123.jpg'])

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

    @windows_ledger_roots
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
            owner = review_owner('local_nfo')
            self.assertEqual(
                _apply_metadata_candidate(connection, title, candidate, '2026-09-06', owner), 1)
            written = connection.execute(
                'SELECT catalog_title,field_owners FROM asset WHERE medium="video"').fetchone()
            self.assertEqual(written['catalog_title'], 'Local title')
            # 批准写下的值要答得出是谁写的，否则下一轮自动落库分不清该不该覆盖它。
            self.assertEqual(owner_of(written['field_owners'], 'catalog_title'), owner)
            title['asset_path'] = 'moved.mp4'
            with self.assertRaises(ValueError):
                _apply_metadata_candidate(connection, title, candidate, '2026-09-06', owner)
        self.assertEqual(snapshot(config)['status'], 'complete')

    def test_status_reads_do_not_start_processing(self):
        from peach.web_library_processing import q_library_processing
        from unittest.mock import patch
        contract = Mock()
        contract.library_processing_job.snapshot.return_value = {'status': 'running', 'job_id': 'one'}
        with patch('peach.web_library_processing.process_library') as worker:
            self.assertEqual(q_library_processing(contract, {})['job_id'], 'one')
            worker.assert_not_called()

    @windows_ledger_roots
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

    @windows_ledger_roots
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

    @windows_ledger_roots
    def test_fields_the_local_nfo_gives_take_no_remote_candidate(self):
        """NFO 给了日文原题，r18 再给一条英文机翻只会变成一道复核题。"""
        from PIL import Image
        media = self.root / 'media'
        media.mkdir()
        (media / 'ABW-358.mp4').write_bytes(b'video')
        (media / 'ABW-358.nfo').write_text('<movie><title>涼森れむ流</title><sorttitle>ABW-358</sorttitle>'
            '<actor><name>涼森れむ</name></actor></movie>', encoding='utf-8')
        Image.new('RGB', (40, 60), 'blue').save(media / 'ABW-358-poster.jpg')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'id': 'ABW-358', 'title': 'Remu Style', 'maker': 'Prestige',
                                       'actresses': [{'japanese_name': 'Remu Suzumori'}]}
        process_library(config, db, self.root / 'generated', self.root / 'covers',
                        provider_factory=Mock(return_value=provider))
        groups = {row['field']: [entry['source'] for entry in json.loads(row['candidates_json'])]
                  for row in read_rows(self.root / 'generated/library-metadata-field-candidates.csv')}
        self.assertEqual(groups['title'], ['local_nfo'])
        self.assertEqual(groups['performers'], ['local_nfo'])
        self.assertEqual(groups['studio'], ['r18dev'])

    @windows_ledger_roots
    def test_online_sources_only_offer_fields_the_ledger_has_no_value_for(self):
        """账本有日文原题，r18 的英文机翻不是分歧，只是写法。"""
        media = self.root / 'media'
        media.mkdir()
        (media / 'DASS-468.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'id': 'DASS-468', 'title': 'I Was Spoiled To Death', 'maker': 'Das',
                                       'series': 'Spoiled To Death', 'release_date': '2024-09-10',
                                       'actresses': [{'japanese_name': '胡桃さくら'}]}
        factory = Mock(return_value=provider)
        candidates = self.root / 'generated/library-metadata-field-candidates.csv'
        process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertEqual({row['field'] for row in read_rows(candidates)},
                         {'title', 'studio', 'series', 'release_date', 'performers'})
        with closing(sqlite3.connect(db)) as connection, connection:
            asset_id = connection.execute("SELECT id FROM asset WHERE code='DASS-468'").fetchone()[0]
            connection.execute("UPDATE asset SET catalog_title=?, studio=?, series=?, release_date=? WHERE id=?",
                               ('ふわとろ巨乳の年下義母 胡桃さくら', 'Das', 'ふわとろ巨乳の年下義母',
                                '2024-09-06', asset_id))
            connection.execute("INSERT INTO asset_tag(asset_id, tag, confidence, source) VALUES(?,?,?,?)",
                               (asset_id, '巨乳', 1.0, 'user'))
            connection.execute("INSERT INTO entity(kind, canonical_name, normalized_name, created_at, updated_at) "
                               "VALUES(?,?,?,?,?)",
                               ('performer', '胡桃樱花', 'hutaoyinghua', '2026-09-15', '2026-09-15'))
            entity_id = connection.execute("SELECT id FROM entity WHERE canonical_name='胡桃樱花'").fetchone()[0]
            connection.execute("INSERT INTO asset_entity(asset_id, entity_id, role, source, confidence) "
                               "VALUES(?,?,?,?,?)", (asset_id, entity_id, 'performer', 'user', 1.0))
        candidates.unlink()
        process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertEqual(list(read_rows(candidates, missing_ok=True)), [])
        provider.query.assert_called_once()

    def test_the_collector_carries_the_cookies_saved_in_scraping_settings(self):
        """采集设置里贴的 JavBus Cookie 要真的跟着采集走。

        凭据根多给一层 `follow` 不会报错，只会让每个来源都读成「没贴过 Cookie」，
        表现是 JavBus 一直回年龄确认页。
        """
        from peach import scraping_access
        from peach.library_processing import _RemoteSession
        config = PeachConfig(self.root, self.root / 'config.toml', present=True)
        scraping_access.save(config.directory('secrets'), 'javbus', {'cookie': 'existmag=all; age=verified'})
        session = _RemoteSession(config, None, None, retrying=False)
        root = session.provider().transport.inner.root
        self.assertTrue(list(scraping_access.cookie_jar(scraping_access.values_for(root, 'javbus'), 'javbus')))

    @windows_ledger_roots
    def test_a_candidate_repeating_the_current_value_is_not_a_question(self):
        """连本地 NFO 也一样：值和账本里那个字一模一样时没有什么可判断的。"""
        media = self.root / 'media'
        media.mkdir()
        (media / 'ABW-358.mp4').write_bytes(b'video')
        (media / 'ABW-358.nfo').write_text('<movie><title>涼森れむ流</title><sorttitle>ABW-358</sorttitle>'
            '<studio>Prestige</studio></movie>', encoding='utf-8')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'id': 'ABW-358'}
        factory = Mock(return_value=provider)
        candidates = self.root / 'generated/library-metadata-field-candidates.csv'
        process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertIn('title', {row['field'] for row in read_rows(candidates)})
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.execute("UPDATE asset SET catalog_title=? WHERE code='ABW-358'", ('涼森れむ流',))
        candidates.unlink()
        process_library(config, db, self.root / 'generated', self.root / 'covers', provider_factory=factory)
        self.assertNotIn('title', {row['field'] for row in read_rows(candidates)})

    def test_r18_metadata_takes_japanese_title_series_and_names(self):
        from peach.library_processing import LibraryMetadataProvider
        detail = {'content_id': '118abw358', 'title': 'Remu Style', 'maker': {'name': 'Prestige'},
                  'series': {'name': 'HOW TO SEX'}, 'actresses': [{'name': 'Remu Suzumori'}]}
        combined = {'content_id': '118abw358', 'title_ja': '涼森れむ流', 'series_name_ja': '保健室の先生',
                    'label_name_ja': 'ABSOLUTELY WONDERFUL', 'maker_name_ja': 'プレステージ',
                    'actresses': [{'name_kanji': '涼森れむ', 'name_romaji': 'Remu Suzumori'}],
                    'directors': [{'name_kanji': 'チャーリー中田'}]}
        pages = lambda transport, url, **kwargs: json.dumps(combined if 'combined=' in url else detail)
        provider = LibraryMetadataProvider.__new__(LibraryMetadataProvider)
        provider.transport = Mock()
        with patch('peach.jav_cover_fetch._fetch', side_effect=pages) as fetch:
            payload = provider.query('ABW-358')
        self.assertIn('combined=118abw358', fetch.call_args_list[1].args[1])
        fields = _fields(payload)
        self.assertEqual(fields['title']['value'], '涼森れむ流')
        self.assertEqual(fields['series']['value'], '保健室の先生')
        self.assertEqual(fields['performers']['display_value'], '涼森れむ')
        # 账本厂牌实体用品牌名，日文写法会另起一个实体。
        self.assertEqual(fields['studio']['value'], 'Prestige')

    def test_r18_metadata_keeps_english_when_the_japanese_page_fails(self):
        from peach.jav_cover_fetch import Unavailable
        from peach.library_processing import LibraryMetadataProvider
        detail = {'content_id': '118abw358', 'title': 'Remu Style', 'actresses': [{'name': 'Remu Suzumori'}]}
        def pages(transport, url, **kwargs):
            if 'combined=' in url:
                raise Unavailable('HTTP 503')
            return json.dumps(detail)
        provider = LibraryMetadataProvider.__new__(LibraryMetadataProvider)
        provider.transport = Mock()
        with patch('peach.jav_cover_fetch._fetch', side_effect=pages):
            payload = provider.query('ABW-358')
        self.assertEqual(_fields(payload)['title']['value'], 'Remu Style')
        self.assertNotIn('translations', payload)

    def test_community_sources_are_asked_once_per_code_and_say_why_they_failed(self):
        """资料和封面两步都要社区来源的结果，javdb 的配额经不起同一部片问两遍。"""
        from peach.jav_cover_fetch import NotFound, Unavailable
        from peach.library_processing import LibraryMetadataProvider
        provider = LibraryMetadataProvider.__new__(LibraryMetadataProvider)
        provider.transport = Mock()
        avbase = Mock(side_effect=NotFound('AVBase 没有这个番号'))
        javdb = Mock(return_value={'id': 'ORETD-615'})
        with patch('peach.community_catalog.COMMUNITY_SOURCES', (('avbase', avbase), ('javdb', javdb))):
            self.assertEqual(provider.community('ORETD-615'), [('javdb', {'id': 'ORETD-615'})])
            provider.community('ORETD-615')
            javdb.side_effect = TimeoutError()
            with self.assertRaisesRegex(Unavailable, r'^javdb：处理出错（TimeoutError）$'):
                provider.community('ORETD-616')
            with self.assertRaisesRegex(Unavailable, 'javdb：'):
                provider.community('ORETD-616')
            javdb.side_effect = Unavailable('javdb 要求登录')
            with self.assertRaisesRegex(Unavailable, '^javdb 要求登录$'):
                provider.community('ORETD-617')
            javdb.side_effect = NotFound('javdb 没有这个番号')
            with self.assertRaises(NotFound):
                provider.community('ORETD-618')
        self.assertEqual(javdb.call_count, 4)

    def test_a_small_official_cover_stays_unless_a_bigger_one_is_confirmed_by_another_origin(self):
        """小封面比没有封面强；社区来源的大图要另一个图源对得上才换上（ADR-0030）。"""
        from peach.jav_cover_fetch import Candidate, NotFound, Unavailable
        from peach.library_processing import LibraryMetadataProvider
        provider = LibraryMetadataProvider.__new__(LibraryMetadataProvider)
        provider.transport = Mock()
        provider.community = Mock(return_value=[('javdb', {'cover_urls': ['https://c0.jdbstatic.com/covers/x.jpg']})])
        small = (Candidate('image.mgstage.com', 'https://image.mgstage.com/pf_o1.jpg'), (300, 200), b'small')
        large = (Candidate('c0.jdbstatic.com', 'https://c0.jdbstatic.com/covers/x.jpg'), (1200, 800), b'large',
                 ('javdb', 'mgstage'))
        covers = self.root / 'covers'
        with patch('peach.jav_cover_fetch.best_cover', return_value=small) as official, \
                patch('peach.community_catalog.verified_cover', return_value=large) as verified:
            self.assertTrue(provider.cover('ORETD-615', covers))
        self.assertEqual(official.call_args.kwargs['minimum_width'], 240)
        self.assertEqual(verified.call_args.kwargs['reference'], small)
        self.assertEqual((covers / 'ORETD-615.jpg').read_bytes(), b'large')
        evidence = json.loads((covers / 'ORETD-615.scraping.json').read_text(encoding='utf-8'))
        self.assertEqual((evidence['width'], evidence['verified_by']), (1200, ['javdb', 'mgstage']))

        with patch('peach.jav_cover_fetch.best_cover', return_value=small), \
                patch('peach.community_catalog.verified_cover', side_effect=Unavailable('javdb、mgstage 给的封面不是同一张图，无法互相印证')):
            self.assertTrue(provider.cover('ORETD-616', covers))
        self.assertEqual((covers / 'ORETD-616.jpg').read_bytes(), b'small')

        lone = (Candidate('c0.jdbstatic.com', 'https://c0.jdbstatic.com/covers/y.jpg'), (800, 538), b'lone', ())
        with patch('peach.jav_cover_fetch.best_cover', side_effect=NotFound('所有渠道都没有候选')), \
                patch('peach.community_catalog.verified_cover', return_value=lone):
            self.assertTrue(provider.cover('IPX-060', covers))
        evidence = json.loads((covers / 'IPX-060.scraping.json').read_text(encoding='utf-8'))
        self.assertEqual(((covers / 'IPX-060.jpg').read_bytes(), evidence['verified_by']), (b'lone', []),
                         '只有一个图源的封面照样装上，verified_by 为空即未经印证')

        with patch('peach.jav_cover_fetch.best_cover', side_effect=Unavailable('官方封面只有缩略图或占位图')), \
                patch('peach.community_catalog.verified_cover', side_effect=Unavailable('社区来源的封面下载失败')), \
                self.assertRaisesRegex(Unavailable, '^官方封面只有缩略图或占位图；社区来源的封面下载失败$'):
            provider.cover('ORETD-617', covers)
        provider.community.side_effect = NotFound('社区来源都没有这个番号')
        with patch('peach.jav_cover_fetch.best_cover', side_effect=NotFound('所有渠道都没有候选')), \
                self.assertRaises(NotFound):
            provider.cover('ORETD-618', covers)

    @windows_ledger_roots
    def test_codes_r18_does_not_know_are_collected_from_the_community_sources(self):
        """r18.dev 没有的番号问 AVBase 与 javdb，两家各留一条候选；免不免复核由落库那道闸按几家一致判。"""
        from peach.jav_cover_fetch import NotFound
        media = self.root / 'media'
        media.mkdir()
        (media / 'ORETD-615.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.side_effect = NotFound('HTTP 404')
        provider.community.return_value = [
            ('avbase', {'id': 'ORETD-615', 'title': 'たまき', 'release_date': '2024-01-05',
                        'source_url': 'https://www.avbase.net/works/orenoshirouto:ORETD-615'}),
            ('javdb', {'id': 'ORETD-615', 'title': 'たまき', 'release_date': '2024-01-04',
                       'source_url': 'https://javdb.com/v/abc'})]
        provider.cover.return_value = False
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 provider_factory=Mock(return_value=provider))
        self.assertEqual((result['status'], result['issue_count']), ('complete', 0))
        rows = {row['field']: row for row in read_rows(self.root / 'generated/library-metadata-field-candidates.csv')}
        title = json.loads(rows['title']['candidates_json'])
        self.assertEqual(sorted((c['source'], c['provider'], c['source_kind'], c['official'], c['provider_id'])
                                for c in title),
                         [('avbase', 'avbase-search', 'community', False, 'ORETD-615'),
                          ('javdb', 'javdb-page', 'community', False, 'ORETD-615')])
        self.assertEqual(rows['title']['source_profile'], 'library')
        self.assertEqual(len(json.loads(rows['release_date']['candidates_json'])), 2)

    @windows_ledger_roots
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

    @windows_ledger_roots
    def test_fc2_codes_ask_no_r18_metadata_but_still_try_a_cover(self):
        """r18.dev 没有 FC2，问一次就是白等一次主机间隔；封面另有 FC2 自己的来源。"""
        media = self.root / 'media'
        media.mkdir()
        for name in ('FC2-PPV-1239052.mp4', 'ABW-001.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'maker': 'Studio', 'id': 'ABW-001', 'source_url': ''}
        provider.cover.return_value = False
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 provider_factory=Mock(return_value=provider))
        self.assertEqual(result['status'], 'complete')
        self.assertEqual([item.args[0] for item in provider.query.call_args_list], ['ABW-001'])
        self.assertEqual(sorted(item.args[0] for item in provider.cover.call_args_list),
                         ['ABW-001', 'FC2-PPV-1239052'])
        self.assertEqual(result['issue_count'], 0)

    @windows_ledger_roots
    def test_files_without_a_code_are_registered_but_not_reported(self):
        """账本里两万多行创作者作品本来就没有番号，逐行报问题只会淹掉真正要处理的几十条。"""
        media = self.root / 'media'
        media.mkdir()
        (media / '某创作者的作品.mp4').write_bytes(b'video')
        from PIL import Image
        Image.new('RGB', (4, 6), 'teal').save(media / '某创作者的作品.png')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        factory = Mock()
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 provider_factory=factory)
        factory.assert_not_called()
        self.assertEqual((result['status'], result['issue_count'], result['checked']), ('complete', 0, 1))
        self.assertTrue((self.root / 'generated' / 'posters' / '1_4.jpg').is_file(), '本地海报照常登记')

    @windows_ledger_roots
    def test_a_directory_name_sitting_in_the_code_column_counts_as_no_code(self):
        """`asset.code` 里的创作者自编号不是发行番号：问不到来源，也不该报成格式无效。"""
        media = self.root / 'media'
        media.mkdir()
        (media / 'DTW003-放课后.mp4').write_bytes(b'video')
        from PIL import Image
        Image.new('RGB', (4, 6), 'teal').save(media / 'DTW003-放课后.png')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'id': 'DTW003', 'maker': 'Studio', 'source_url': ''}
        provider.cover.return_value = False
        process_library(config, db, self.root / 'generated', self.root / 'covers',
                        stage='scan', provider_factory=lambda: provider)
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.execute("UPDATE asset SET code='DTW003'")
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 stage='collect', provider_factory=lambda: provider)
        provider.query.assert_not_called()
        self.assertEqual((result['status'], result['issue_count'], result['checked']), ('complete', 0, 1))
        self.assertTrue((self.root / 'generated' / 'posters' / '1_4.jpg').is_file(), '本地海报照常登记')

    @windows_ledger_roots
    def test_a_tokyo_hot_code_written_with_the_site_name_is_asked_for(self):
        """账本里按目录名落的 `TOKYO-HOT-N0762` 是真番号，要按规范写法去问来源。"""
        media = self.root / 'media'
        media.mkdir()
        (media / 'n0762.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.return_value = {'id': 'n0762', 'maker': 'Tokyo-Hot', 'source_url': ''}
        provider.cover.return_value = False
        process_library(config, db, self.root / 'generated', self.root / 'covers',
                        stage='scan', provider_factory=lambda: provider)
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.execute("UPDATE asset SET code='TOKYO-HOT-N0762'")
        result = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                 stage='collect', provider_factory=lambda: provider)
        self.assertEqual([item.args[0] for item in provider.query.call_args_list], ['n0762'])
        self.assertEqual(result['issue_count'], 0)

    @windows_ledger_roots
    def test_a_source_that_said_no_is_not_asked_again_for_a_week(self):
        """r18.dev 不认识的番号每轮都重问、每条卡一次 2 秒的主机间隔，答案永远一样。

        只记来源明确说「没有」的（`NotFound`）；超时与网络故障照旧下次再问。
        「重试未完成项」按上一任务的失败集合强制重试，不看这份记忆。
        """
        from peach.jav_cover_fetch import NotFound, Unavailable
        from peach.library_processing import _MissCache, misses_path
        media = self.root / 'media'
        media.mkdir()
        (media / 'STP-26232.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / 'config.toml', present=True, locations={'local': (str(media),)})
        provider = Mock()
        provider.query.side_effect = NotFound('HTTP 404')
        provider.community.side_effect = NotFound('社区来源都没有这个番号')
        provider.cover.side_effect = Unavailable('HTTP 503')
        run = lambda **extra: process_library(config, db, self.root / 'generated', self.root / 'covers',
                                              provider_factory=Mock(return_value=provider), **extra)
        first = run()
        self.assertEqual((provider.query.call_count, provider.community.call_count), (1, 1))
        self.assertEqual([row['message'] for row in first['issue_preview']],
                         ['封面未取得：来源返回 HTTP 503'], '来源说没有只报一个数，不占问题清单')
        self.assertEqual(first['notes'], {'querying_metadata': 1})
        recorded = json.loads(misses_path(config).read_text(encoding='utf-8'))
        self.assertEqual(list(recorded), ['r18dev', 'community'])
        self.assertEqual(list(recorded['r18dev']), ['STP-26232'])

        provider.cover.side_effect = NotFound('所有渠道都没有候选')
        second = run()
        self.assertEqual((provider.query.call_count, provider.community.call_count), (1, 1), '资料 7 天内不再问')
        self.assertEqual(provider.cover.call_count, 2, '封面上次是来源故障，这次照问')
        self.assertEqual(second['issue_preview'], [])
        self.assertEqual(second['notes'], {'querying_metadata': 1, 'fetching_cover': 1})
        self.assertEqual(second['retryable_asset_ids'], [])
        self.assertEqual((second['status'], second['issue_count']), ('complete', 0))
        self.assertEqual((first['status'], first['issue_count']), ('failed', 1))
        # 状态文件里没有 `notes` 的任务，读出来要按日志把告知项和问题分开重算。
        stored = dict(second, status='failed', error='2 项需要处理，请查看详情并重试。', issue_count=2,
                      issue_preview=[{'asset_id': 1, 'title': 'STP-26232.mp4', 'path': '',
                                      'message': message, 'severity': 'error'}
                                     for message in ('外部来源没有这部片的资料，7 天内不再问',
                                                     '外部来源没有这部片的封面，7 天内不再问')])
        stored.pop('notes')
        state_path(config).write_text(json.dumps(stored), encoding='utf-8')
        projected = snapshot(config)
        self.assertEqual((projected['status'], projected['issue_count'], projected['issue_preview']),
                         ('complete', 0, []))
        self.assertEqual(projected['notes'], {'querying_metadata': 1, 'fetching_cover': 1})
        self.assertEqual(json.loads(state_path(config).read_text(encoding='utf-8'))['status'], 'failed')

        third = run()
        self.assertEqual((provider.query.call_count, provider.cover.call_count), (1, 2))
        self.assertEqual(third['issue_count'], 0)
        self.assertEqual((third['status'], third['retryable_asset_ids']), ('complete', []))

        run(retry_ids=[1])
        self.assertEqual((provider.query.call_count, provider.cover.call_count), (2, 3), '重试未完成项不看记忆')

        cache = _MissCache(misses_path(config), now=lambda: time.time() + 8 * 24 * 3600)
        self.assertFalse(cache.fresh('r18dev', 'STP-26232'), '7 天后再问一次')
        self.assertFalse(_MissCache(self.root / 'missing.json').fresh('r18dev', 'STP-26232'))

    def test_management_controls_keep_credentials_and_empty_sections_visible(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'web/app.js').read_text(encoding='utf-8')
        self.assertIn('wireFollowManage(creds)', source)
        self.assertIn('const sources=credentials.filter(source=>source.followable);', source)
        self.assertIn('data-srcfilter-config=', source)
        self.assertNotIn("if(!providers.length){mount.innerHTML='';return}", source)
        self.assertIn("needsAttention?' open':''", source)
        self.assertIn('还没有内容标签', source)
        self.assertIn('还没有存储来源', source)
        self.assertIn("catalogEmptyHtml({configurable:runtimeConfigurable})}</div>", source)
        self.assertIn("unmountIsland($('#libraryProcessingNotice'))", source)
        self.assertIn("mode:'notice'", source)
        configuration = (root / 'frontend/src/react/settings/configuration-page.tsx').read_text(encoding='utf-8')
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

    @windows_ledger_roots
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

    @windows_ledger_roots
    def test_issue_preview_is_capped_while_the_log_keeps_every_row(self):
        media = self.root / 'media'
        media.mkdir()
        for index in range(25):
            (media / f'样品{index:02d}.mp4').write_bytes(b'video')
            (media / f'样品{index:02d}.nfo').write_text('<movie><title>没闭合', encoding='utf-8')
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

    @windows_ledger_roots
    def test_each_issue_names_the_item_its_path_and_where_the_full_log_is(self):
        """一句「NFO 无法解析」加一个链接，是哪个文件得逐个点开才知道；改名或去磁盘上
        确认时要用的是路径。完整清单的地址跟着状态一起给出，不让人按 job_id 自己去拼。
        """
        media = self.root / 'media'
        media.mkdir()
        (media / '样品.mp4').write_bytes(b'video')
        (media / '样品.nfo').write_text('<movie><title>没闭合', encoding='utf-8')
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

    @windows_ledger_roots
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

    @windows_ledger_roots
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

    @windows_ledger_roots
    def test_scanning_alone_registers_the_files_and_asks_no_source(self):
        """只扫描那一段登记完文件就收工，不读本地资料也不联网。

        新盘刚接上时要的就是这个：几万个文件进了馆藏就能用，采集可以留到夜里。
        """
        media = self.root / 'media'
        media.mkdir()
        (media / 'ABW-203.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        provider = self._provider()
        state = process_library(self._config(media), db, self.root / 'generated',
                                self.root / 'covers', stage='scan',
                                provider_factory=lambda: provider)
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['scanned'], 1)
        self.assertEqual(state['checked'], 0)
        self.assertEqual(state['candidates'], 0)
        provider.query.assert_not_called()
        with closing(sqlite3.connect(db)) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM asset').fetchone()[0], 1,
                             "文件要进馆藏，只是没往下走采集")

    @windows_ledger_roots
    def test_collecting_alone_walks_the_library_without_touching_the_disk_again(self):
        """只采集那一段不再扫一遍来源目录，处理的仍是整个馆藏。

        采集被网络拖住时重跑的就是它：几万个文件的目录遍历没有必要再走一趟。
        """
        media = self.root / 'media'
        media.mkdir()
        (media / 'ABW-204.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        provider = self._provider()
        process_library(config, db, self.root / 'generated', self.root / 'covers',
                        stage='scan', provider_factory=lambda: provider)
        with patch('peach.library_processing.scan_location') as scan:
            state = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                    stage='collect', provider_factory=lambda: provider)
        scan.assert_not_called()
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['total'], 1)
        self.assertEqual(state['checked'], 1)

    @windows_ledger_roots
    def test_a_row_with_nothing_left_to_collect_never_touches_the_disk(self):
        """番号已落库、字段都有着落、封面在位的行，采集连 stat 都不做。

        重跑「只采集」时这是绝大多数行；网盘上每行一次 stat 加一次列目录就是两趟往返。
        文件在扫描后被删掉，任务仍然一条问题都不报，就是没碰磁盘的证据。
        """
        from peach.library_processing import FIELDS
        from peach.review_csv import write_rows
        media = self.root / 'media'
        media.mkdir()
        (media / 'ABW-205.mp4').write_bytes(b'video')
        db = fresh_ledger(self.root)
        config = self._config(media)
        provider = self._provider()
        process_library(config, db, self.root / 'generated', self.root / 'covers',
                        stage='scan', provider_factory=lambda: provider)
        with closing(sqlite3.connect(db)) as connection, connection:
            asset_id = connection.execute("UPDATE asset SET code='ABW-205', catalog_title='t', studio='s', "
                                          "release_date='2024-01-01' RETURNING id").fetchone()[0]
        (self.root / 'covers').mkdir()
        (self.root / 'covers' / 'ABW-205.jpg').write_bytes(b'jpg')
        blank = {field: '' for field in FIELDS}
        write_rows(self.root / 'generated' / 'library-metadata-field-candidates.csv', FIELDS,
                   [dict(blank, item_key=f'asset:{asset_id}:{field}') for field in ('performers', 'tags')])
        (media / 'ABW-205.mp4').unlink()
        with patch('peach.library_processing.sidecars') as listing:
            state = process_library(config, db, self.root / 'generated', self.root / 'covers',
                                    stage='collect', provider_factory=lambda: provider)
        listing.assert_not_called()
        provider.query.assert_not_called()
        self.assertEqual((state['status'], state['checked'], state['issue_count']), ('complete', 1, 0))

    @windows_ledger_roots
    def test_one_directory_is_listed_once_for_all_the_videos_in_it(self):
        """同一个文件夹里的片子共用一次目录列表，找 NFO 和找海报也不各列一遍。"""
        from peach import library_nfo
        media = self.root / 'media'
        media.mkdir()
        for name in ('ABW-206.mp4', 'ABW-207.mp4', 'ABW-208.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        provider = self._provider()
        with patch('peach.library_processing.directory_files', wraps=library_nfo.directory_files) as listed:
            state = process_library(self._config(media), db, self.root / 'generated', self.root / 'covers',
                                    provider_factory=lambda: provider)
        self.assertEqual(state['checked'], 3)
        self.assertEqual(listed.call_count, 1)

    @windows_ledger_roots
    def test_candidates_are_written_once_for_a_short_batch_not_once_per_asset(self):
        """候选 CSV 按时间节流落盘，结束时写全；三条资产不该重写三遍整份文件。"""
        from peach import review_csv
        media = self.root / 'media'
        media.mkdir()
        for name in ('ABW-209.mp4', 'ABW-210.mp4', 'ABW-211.mp4'):
            (media / name).write_bytes(b'video')
        db = fresh_ledger(self.root)
        provider = self._provider()
        with patch('peach.library_processing.write_rows', wraps=review_csv.write_rows) as written:
            state = process_library(self._config(media), db, self.root / 'generated', self.root / 'covers',
                                    provider_factory=lambda: provider)
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(written.call_count, 1)
        rows = read_rows(self.root / 'generated' / 'library-metadata-field-candidates.csv')
        self.assertEqual(len({row['asset_id'] for row in rows}), 3)

    def test_the_stage_asked_for_is_the_stage_that_runs(self):
        """页面点哪一段就跑哪一段，不认识的段数拒绝掉。

        段名要一路传到管线里。只拿它换一句提示文字的话，按钮看着分了工、跑起来
        全是同一件事，而且页面上看不出区别。
        """
        from peach.web_library_processing import w_library_processing
        contract = SimpleNamespace(
            db_path=Path(self.root / 'database' / 'ledger.db'),
            candidate_root=self.root / 'generated', cover_root=self.root / 'covers',
            cache_bust=lambda: None,
            library_processing_job=SimpleNamespace(
                snapshot=lambda: None,
                start=lambda work, restart, initial: (work('job'), initial)[1],
                update=lambda job_id, **values: None))
        media = self.root / 'media'
        media.mkdir()
        (self.root / 'database').mkdir(exist_ok=True)
        fresh_ledger(self.root / 'database')
        config = self._config(media)
        with patch('peach.web_library_processing.settings_file.active', return_value=config), \
             patch('peach.web_library_processing.process_library') as run:
            run.return_value = {'job_id': 'job', 'status': 'complete'}
            initial = w_library_processing(contract, {'stage': 'collect'})
            self.assertEqual(run.call_args.kwargs['stage'], 'collect')
            self.assertEqual(initial['requested_stage'], 'collect')
            self.assertEqual(initial['stage'], '准备采集资料')
            w_library_processing(contract, {})
            self.assertEqual(run.call_args.kwargs['stage'], 'all')
            with self.assertRaises(ValueError):
                w_library_processing(contract, {'stage': 'thumbnails'})

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
