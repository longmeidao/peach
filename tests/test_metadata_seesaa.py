import csv
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx

from peach.http import HttpResponse
from peach.metadata import MetadataProviderError
from peach.metadata_policy import resolve_policy
from peach.metadata_seesaa import ROOT, SeesaaProvider, parse_page, page_url


def fixture(code='ABC-007', actors=None):
    actors = actors if actors is not None else '<a href="/w/sougouwiki/d/OtherName">架空花子</a>／<a href="/w/sougouwiki/d/B">架空春子</a>'
    return (f'<div id="page-body"><div class="user-area"><table id="table_edit_1">'
            '<tr><th>NO</th><th>PHOTO</th><th>TITLE</th><th>ACTRESS</th><th>RELEASE</th><th>NOTE</th></tr>'
            f'<tr><td>{code}</td><td><a href="https://example.org/cover.jpg">画像</a></td>'
            f'<td>架空の作品</td><td>{actors}</td><td>2024/11/20</td><td>別版 ABC-008</td></tr>'
            '</table></div></div><aside>ABC-008 別の出演者</aside>').encode('euc_jp')


class SeesaaMetadataTests(unittest.TestCase):
    def provider(self, root, transport, **kwargs):
        return SeesaaProvider(root, transport=transport, limiter=Mock(), **kwargs)

    def test_table_scopes_code_cast_date_and_evidence(self):
        row = parse_page(fixture(), ROOT+'d/Label')[0]
        self.assertEqual(row['id'], 'ABC-007')
        self.assertEqual(row['release_date'], '2024-11-20')
        self.assertEqual([a['japanese_name'] for a in row['actresses']], ['架空花子', '架空春子'])
        self.assertEqual(row['wiki_evidence']['performer_links'][0]['source_url'], ROOT+'d/OtherName')
        self.assertEqual(row['wiki_evidence']['notes'], '別版 ABC-008')
        self.assertEqual(row['cover_url'], 'https://example.org/cover.jpg')

    def test_uncertain_or_unlinked_cast_is_evidence_only(self):
        for tail in ('／？', '／3人目', '／未確認', '／未リンク花子'):
            row = parse_page(fixture(actors='<a href="/w/sougouwiki/d/A">架空花子</a>'+tail), ROOT+'d/Label')[0]
            self.assertEqual(row['actresses'], [])
            self.assertFalse(row['wiki_evidence']['performers_complete'])

    def test_edit_comments_and_unscoped_tables_are_not_records(self):
        self.assertEqual(parse_page(fixture().replace(b'user-area', b'comments'), ROOT+'d/Label'), [])
        for url in ('https://evil.test/w/sougouwiki/d/X', ROOT+'e/edit', ROOT+'d/X?edit=1'):
            with self.assertRaises(ValueError):
                page_url(url)

    def test_search_discovers_label_without_using_person_as_entire_cast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            search = b'<div class="result-box"><div class="body"><h3><a href="/w/sougouwiki/d/Person">Person</a></h3></div></div>'
            person = '<div id="page-body"><div class="user-area"><a href="/w/sougouwiki/d/Label">(レーベル一覧)</a></div></div>'.encode('euc_jp')
            transport = Mock(side_effect=[HttpResponse(200, {}, search), HttpResponse(200, {}, person), HttpResponse(200, {}, fixture())])
            provider = self.provider(root, transport)
            self.assertEqual(len(provider.query('ABC-007')['actresses']), 2)
            self.assertEqual(transport.call_count, 3)
            self.assertEqual(provider.query('123ABC-007')['id'], 'ABC-007')
            self.assertEqual(transport.call_count, 3)

    def test_success_cache_resumes_and_failures_remain_retryable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            url = ROOT+'d/Label'
            first = self.provider(root, Mock(return_value=HttpResponse(200, {}, fixture())), pages=[url])
            first.query('ABC-007')
            transport = Mock(side_effect=AssertionError('unexpected network'))
            resumed = self.provider(root, transport, pages=[url])
            self.assertEqual(resumed.query('ABC-007')['id'], 'ABC-007')
            transport.assert_not_called()

    def test_block_budget_timeout_and_large_responses_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for response in (HttpResponse(403, {}, b''), HttpResponse(429, {}, b''),
                             HttpResponse(200, {}, b'Just a moment')):
                transport = Mock(return_value=response)
                provider = self.provider(root, transport)
                for code in ('ABC-007', 'ABC-008'):
                    with self.assertRaises(MetadataProviderError):
                        provider.query(code)
                self.assertEqual(transport.call_count, 1)
            provider = self.provider(root, Mock(side_effect=httpx.ReadTimeout('timeout')))
            with self.assertRaises(MetadataProviderError) as caught:
                provider.query('ABC-007')
            self.assertTrue(caught.exception.retryable)
            provider = self.provider(root, Mock(), max_requests=0)
            with self.assertRaises(MetadataProviderError):
                provider.query('ABC-007')
            provider.transport.assert_not_called()
            provider = self.provider(root, Mock(return_value=HttpResponse(200, {}, b'x'*(4*1024*1024+1))))
            with self.assertRaises(MetadataProviderError) as caught:
                provider.query('ABC-007')
            self.assertEqual(caught.exception.kind, 'size_limit')

    def test_conflicting_rows_and_neighbor_codes_are_not_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = self.provider(Path(tmp).resolve(), Mock())
            provider.records['one'] = parse_page(fixture(), ROOT+'d/One')
            self.assertIsNone(provider._match('ABC-008'))
            provider.records['two'] = parse_page(fixture(actors='<a href="/w/sougouwiki/d/C">架空夏子</a>'), ROOT+'d/Two')
            with self.assertRaisesRegex(MetadataProviderError, '冲突'):
                provider._match('ABC-007')

    def test_cli_outputs_community_candidates_without_javinizer_or_ledger_changes(self):
        path = Path(__file__).resolve().parents[1] / 'scripts/scrape_codes.py'
        spec = importlib.util.spec_from_file_location('seesaa_scrape_test', path)
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            db = root/'ledger.db'
            with sqlite3.connect(db) as c:
                c.executescript("CREATE TABLE asset(id INTEGER, medium TEXT, code TEXT, size INTEGER, catalog_title TEXT, original_title TEXT, studio TEXT, series TEXT, release_date TEXT); CREATE TABLE entity(id INTEGER, kind TEXT, canonical_name TEXT); CREATE TABLE asset_entity(asset_id INTEGER, entity_id INTEGER, role TEXT); INSERT INTO asset VALUES(1,'video','ABC-007',1,NULL,NULL,NULL,NULL,NULL);")
            c.close()
            before = db.read_bytes()
            pages = root/'pages.txt'
            pages.write_text(ROOT+'d/Label', encoding='utf8')
            output = root/'metadata-field-candidates-test.csv'
            with patch('peach.metadata_seesaa.HttpxTransport', return_value=Mock(return_value=HttpResponse(200, {}, fixture()))), patch.object(script.JavinizerGoProvider, 'create', side_effect=AssertionError('not required')):
                self.assertEqual(script.main(['--db', str(db), '--out', str(output), '--raw-dir', str(root/'raw'), '--log-dir', str(root/'logs'), '--profile', 'seesaa', '--wiki-pages-file', str(pages), '--delay', '0', '--min-free', '0']), 0)
            with output.open(encoding='utf-8-sig') as handle:
                rows = list(csv.DictReader(handle))
            candidate = json.loads(next(r for r in rows if r['field']=='performers')['candidates_json'])[0]
            self.assertEqual(candidate['source_kind'], 'community')
            self.assertFalse(candidate['official'])
            self.assertTrue(candidate['wiki_evidence']['performers_complete'])
            self.assertTrue(candidate['warnings'])
            self.assertEqual(before, db.read_bytes())
            self.assertEqual(resolve_policy(profile='seesaa').sources, ('sougouwiki',))
