# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on `0.0.0.0:80`, server PID observed as 52476; health mode is `fastapi`.
- mDNS root cause was the Python zeroconf responder failing to answer while several Windows applications shared UDP 5353, even though health incorrectly reported registration. Windows now uses the native DNS-SD API; LAN-client verification is pending the production restart below. No firewall or router rule was changed.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: `0000`, `0001` and `0002` applied; zero pending.
- Current pre-0002 recovery point: `R:\peach-data\archive\ledger.pre-migrate-20260814-162004.db`.

Runtime PIDs are observations, not configuration; always re-check them.

## Verified code state

- FastAPI serves home, stable JSON contract, standard Range/HEAD media, thumbnails, posters, avatars and logos.
- The old `BaseHTTPRequestHandler`, dynamic legacy loader and automatic schema repair path are deleted. Default contract reads are read-only; activity/play/feedback writes are explicit.
- FFmpeg/ffprobe are Peach-managed under `R:\peach-data\tools\ffmpeg`; resolver order is environment, managed bundle, then PATH. Active code has no Stash private binary fallback.
- Stash transport is centralized in `StashClient`; ledger imports now write stable `media_binding` external IDs and explicit tag/performer provenance. The new importer was verified only against an isolated database and was not run on the real ledger.
- Migration `0002` added canonical entity/alias/external-ref/asset-relation tables and backfilled existing performer/tag/studio/creator/series projections. After the post-migration external-metadata reconciliation, the real ledger has 8,603 entities and 131,877 relations. The Stash and external-metadata importers dual-write canonical relations while retaining flattened UI projections.
- Passive `/api/providers` health discovery now exposes separate inference/agent capabilities without model calls, credential reads or secret values.
- The OpenCode Go adapter now supports explicit public model discovery through `/api/providers/opencode-go/models`, with a five-minute in-memory cache and normalized secret-free output. It does not invoke inference or read CLI credentials.
- The first online-follow connector is a generic explicit RSS/Atom `FeedAdapter`: conditional requests, bounded response reads, normalized entries and no ledger writes. `FeedSnapshotStore` persists immutable XML/normalized evidence under `sources/follow` and request cursors under `state/follow`. It has only isolated feed tests so far; no real feed was contacted.
- Snapshot rows still contain 10,714 pre-split `R:\Resources\Intake\snapshots` paths. Runtime now performs a strict legacy-prefix rebase to `R:\peach-data\generated\snapshots`; it does not mutate the real ledger.
- `R:\peach-data` now separates `database/generated/sources/state/secrets/logs/archive/inbox/tools`; the old empty root Inbox and old Resources/Tools compatibility surface are removed.
- `web_contract.py` now uses an application-owned database/cache/write-lock context rather than module globals; separate app instances cannot leak databases or caches into each other.
- Item, detail, tag index and facet reads now prefer canonical `asset_entity` performer/tag relations, with flattened `asset_tag` retained only as a staged compatibility fallback. Real-ledger timings were 0.143 s for a filtered item query, 0.118 s for facets and 0.025 s for the first 30 canonical tags.
- Creator/studio top lists and related-item creator/tag/studio matching now read canonical entity relations. Real-ledger timings were 0.055 s for 28 top entries and 0.055 s for 24 related items.
- Creator/studio filters, canonical-name search, creator index, facets and attribution stats now also read entity relations. Real-ledger timings were 0.040 s for a 1,545-item creator filter, 0.043 s for the first 60 creators, 0.132 s for facets and 0.394 s for stats.
- Snapshot availability checks use the same strict legacy-prefix resolver as `/thumb`, so the front end requests migrated previews instead of displaying false “无预览” cards.
- 45 isolated tests and tracked-script static compilation passed under Python 3.14.
- Real migration preserved 81,873 assets and 59,697 tag links; both live database and backup passed `integrity_check` and `foreign_key_check` before later metadata writes.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the same application candidate before the schema-only migration; visual checks were not rerun after migration because no browser instance was connected.
- Restarted production port 80 passed health, home, public OpenCode Go model discovery (26 models at verification time), canonical filtered-list/item reads, thumbnail `200` and 1 KiB `206 Partial Content` Range smoke checks.
- After deleting the legacy server, restarted production also passed real `stats`, `tops` and `facets` aggregate contract checks.
- Optional SSL is supported with an explicit certificate/key pair. Production remains HTTP until a trusted local certificate is supplied.
- Immersive-mode actions now use optically centered 60 px controls with visible `不喜欢` / `看过` / `高潮` labels; the orgasm count is a corner badge and the watched state changes to `已看`.
- The original Peach process could not see CloudDrive `A:`/`B:` even though CloudDrive was running. After confirming zero copy tasks and no I/O, CloudDrive and Peach were restarted in the same execution context. Asset 4289 (`669.mp4`) then passed `video/mp4`, 1 KiB `206 Range`, thumbnail and generated-poster API checks. Drive-letter visibility differs by Windows token, so the HTTP stream check is the authoritative service test.

## Batch jobs

- `scripts/scrape_codes.py` — code scraping via r18 → avsox → javbus cascade, resumable from
  `R:\peach-data\generated\code-scrape.csv`. All 1,104 non-FC2 codes were processed; 715 rows carry
  data (r18 672, javbus 43). Studio coverage went 1,105 → 1,158 of 1,434 total codes; the run added 2,538
  `asset_tag` rows with `source='r18'`. The 330 FC2 codes are skipped by default (`--include-fc2` to force)
  because a measured 117-code sample produced zero hits across all three sources.
- The completed scrape was reconciled once through the new dual-write path without new network calls. It added 577 previously empty series projections and brought the live ledger to 61,377 compatibility tag links. Recovery point: `R:\peach-data\archive\ledger.pre-metadata-reconcile-20260814-163027.db`.
- `scripts/clean_names.py` — strips pirate-site promo domains and residual noise from filenames, updating
  disk and ledger `path`/`name` together. 274 of 287 candidates renamed, 0 failures, 5 sources already
  gone, 8 skipped on name collision; 2 promo names remain behind collisions. Verified by re-listing every
  renamed path after the cloud write cache flushed. Backup: `R:\peach-data\archive\ledger.pre-rename-20260814-161656.db`.
  The script deliberately does not strip ` (3)` sequence markers (16,278 in the library; removing them
  collides 1,520 Telegram exports) and does not touch `name.mp4.jpg` thumbnails (only 2 true `.mp4.mp4` cases).
- Probe backlog is empty. Free sheet backlog (115/local) is empty: the 20 residual rows were rechecked
  three times and 17 are dead ledger rows, not pending work. PikPak sheets still hold 4,740 items and
  are metered, so they need a traffic budget decision before running.
- 12,204 videos still have no content tag.

## Next work

1. Add explicit feed configuration plus a reviewed candidate import without automatic ledger writes; only then consider a scheduler.
2. Add reviewed inference requests behind the OpenCode Go adapter; AI output must remain a candidate and cannot write ledger truth directly.
3. Replace remaining flattened creator/studio display projections only when the front end can consume canonical DTO fields without breaking compatibility.
