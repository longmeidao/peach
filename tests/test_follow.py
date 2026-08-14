import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from peach.follow import FeedAdapter, FeedSnapshotStore, FollowSourceError, HttpResponse


class FeedAdapterTests(unittest.TestCase):
    def test_rss_discovery_normalizes_entries_and_conditional_headers(self):
        calls = []
        rss = b"""<?xml version='1.0'?>
        <rss version='2.0'><channel><title>Example</title><item>
          <guid>post-1</guid><title> First post </title>
          <link>https://example.test/posts/1</link>
          <pubDate>Thu, 14 Aug 2026 08:00:00 GMT</pubDate>
          <author>Alice</author><description>&lt;b&gt;Hello&lt;/b&gt; world</description>
          <enclosure url='https://cdn.example.test/1.mp4' type='video/mp4'/>
        </item></channel></rss>"""

        def transport(request, timeout, max_bytes):
            calls.append((request, timeout))
            return HttpResponse(200, {"ETag": '"v1"'}, rss)

        result = FeedAdapter(transport=transport).fetch(
            "https://example.test/feed.xml#ignored", etag='"v0"',
            last_modified="Wed, 13 Aug 2026 08:00:00 GMT",
        )
        self.assertEqual(result.source_url, "https://example.test/feed.xml")
        self.assertEqual(result.etag, '"v1"')
        self.assertEqual(result.entries[0].external_id, "post-1")
        self.assertEqual(result.entries[0].summary, "Hello world")
        self.assertEqual(result.entries[0].media_url, "https://cdn.example.test/1.mp4")
        self.assertEqual(calls[0][0].get_header("If-none-match"), '"v0"')
        self.assertEqual(calls[0][0].get_header("If-modified-since"),
                         "Wed, 13 Aug 2026 08:00:00 GMT")

    def test_atom_discovery_and_not_modified(self):
        atom = b"""<feed xmlns='http://www.w3.org/2005/Atom'><entry>
          <id>tag:example.test,2026:2</id><title>Second</title>
          <updated>2026-08-14T09:00:00Z</updated>
          <author><name>Bob</name></author>
          <link href='https://example.test/posts/2'/>
          <link rel='enclosure' href='https://cdn.example.test/2.mp4'/>
          <summary>Fresh</summary></entry></feed>"""
        adapter = FeedAdapter(transport=lambda *_: HttpResponse(200, {}, atom))
        result = adapter.fetch("https://example.test/atom")
        self.assertEqual(result.entries[0].author, "Bob")
        self.assertEqual(result.entries[0].url, "https://example.test/posts/2")

        cached = FeedAdapter(transport=lambda *_: HttpResponse(
            304, {"Last-Modified": "Thu, 14 Aug 2026 09:00:00 GMT"}, b"",
        )).fetch("https://example.test/atom")
        self.assertTrue(cached.not_modified)
        self.assertEqual(cached.entries, ())

    def test_rejects_unsafe_urls_oversized_and_invalid_feeds(self):
        adapter = FeedAdapter(transport=lambda *_: HttpResponse(200, {}, b"x" * 5), max_bytes=4)
        with self.assertRaisesRegex(FollowSourceError, "size limit"):
            adapter.fetch("https://example.test/feed")
        with self.assertRaisesRegex(FollowSourceError, "credentials"):
            adapter.fetch("https://user:secret@example.test/feed")
        with self.assertRaisesRegex(FollowSourceError, "absolute HTTP"):
            adapter.fetch("file:///tmp/feed.xml")
        invalid = FeedAdapter(transport=lambda *_: HttpResponse(200, {}, b"<html/>"))
        with self.assertRaisesRegex(FollowSourceError, "unsupported"):
            invalid.fetch("https://example.test/feed")

    def test_snapshot_store_separates_immutable_evidence_and_request_state(self):
        rss = b"<rss><channel><item><guid>one</guid><title>One</title></item></channel></rss>"
        fresh = FeedAdapter(transport=lambda *_: HttpResponse(
            200, {"ETag": '"v1"'}, rss,
        )).fetch("https://example.test/feed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = FeedSnapshotStore(root / "sources", root / "state")
            first = store.persist(
                fresh, checked_at=datetime(2026, 8, 14, 8, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(first.etag, '"v1"')
            self.assertTrue((root / "sources" / first.snapshot).is_file())
            source_dir = (root / "sources" / first.snapshot).parent
            self.assertEqual(len(list(source_dir.glob("*.xml"))), 1)
            self.assertEqual(len(list(source_dir.glob("*.json"))), 1)

            cached = FeedAdapter(transport=lambda *_: HttpResponse(
                304, {}, b"",
            )).fetch("https://example.test/feed")
            second = store.persist(
                cached, checked_at=datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(second.etag, '"v1"')
            self.assertEqual(second.snapshot, first.snapshot)
            self.assertEqual(len(list(source_dir.glob("*.xml"))), 1)
            self.assertEqual(store.load("https://example.test/feed"), second)


if __name__ == "__main__":
    unittest.main()
