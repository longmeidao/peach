# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on `0.0.0.0:80`, listener PID observed as 3688; health mode is `fastapi`.
- `peach.local` is again the single official LAN entry. The publisher restores the verified pre-migration behavior: Python zeroconf listens on all eligible interfaces and publishes `peach.local -> 192.168.50.162`. Production health reports `mdns_backend=zeroconf-all-interfaces`; same-host DNS-SD discovery and `getaddrinfo('peach.local')` both resolved the correct address after restart. A second LAN device remains the final external check; no firewall or router rule was changed.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: `0000`–`0004` applied; zero pending. FTS migration backup: `R:\peach-data\database\ledger.pre-migrate-20260814-213920.db`. The 20:17 backups remain `R:\peach-data\database\ledger.pre-migrate-20260814-201719.db` and `R:\peach-data\archive\ledger.pre-studio-canonicalize-20260814-201719.db`.
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
- 61 isolated tests, Python static compilation, dependency validation and JavaScript parse validation passed under Python 3.14/Node.
- Real migration preserved 81,873 assets and 59,697 tag links; both live database and backup passed `integrity_check` and `foreign_key_check` before later metadata writes.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the same application candidate before the schema-only migration; visual checks were not rerun after migration because no browser instance was connected.
- Restarted production port 80 passed health, home, public OpenCode Go model discovery (26 models at verification time), canonical filtered-list/item reads, thumbnail `200` and 1 KiB `206 Partial Content` Range smoke checks.
- After deleting the legacy server, restarted production also passed real `stats`, `tops` and `facets` aggregate contract checks.
- Optional SSL is supported with an explicit certificate/key pair. Production remains HTTP until a trusted local certificate is supplied.
- Immersive-mode actions now use optically centered 60 px controls with visible `不喜欢` / `看过` / `高潮` labels; the orgasm count is a corner badge and the watched state changes to `已看`.
- Long-card hover now enlarges the card and exposes ±10-second preview seeking; short cards expose a profile-backed “稍后看” action. Item details show linked performers/studio/creator/series, and top performer/studio entries navigate to entity pages instead of mutating filters.
- Migration `0003` added entity summaries, typed links/search terms and `watch_queue`. Thirteen reviewed studio duplicate groups were merged with 15 aliases; Prestige has 248 video assets after Japanese/Prestige Premium normalization, while distinct `PREMIUM` remains separate.
- FC2's 16×16 favicon was replaced by the official 102×43 asset and the user-provided Prestige logo was cached locally, both with provenance sidecars. Performer-image routing prefers a provenance-backed entity cache; Stash's default SVG silhouette is rejected rather than mislabeled as an HD portrait.
- `scripts/import_stash_entities.py` reconciled the Stash public performer contract into Peach without making Stash authoritative: 383 exact stable refs, 52 aliases/search terms and two explicitly declared X links were imported. Of 42 non-placeholder Stash images, 14 passed the 512 px short-side gate and were cached with provenance; 28 smaller images were rejected. Top entries including 一个ren、高桥千凛 and 小桃 now use 720 px-class cached portraits.
- Static/unit/API production checks passed after restart: home/entity routes, FC2/Prestige logos, canonical aliases and a local-media 1 KiB `206 Partial Content` response. No browser instance was connected, so desktop and 390×844 visual verification remain pending.
- The 20:36 Peach restart was launched only after verifying the port-80 command line in the host session. The replacement process can see CloudDrive: asset 4289 again passed `video/mp4` 1 KiB `206 Partial Content` and poster `200`; local asset 1 passed the same Range contract. A sandbox drive check is not authoritative.
- The mDNS regression fix remains deployed. The current listener PID 3688 passed health, Windows hostname resolution and CloudDrive asset 4289 with a 1 KiB `206 Partial Content` response.
- The original Peach process could not see CloudDrive `A:`/`B:` even though CloudDrive was running. After confirming zero copy tasks and no I/O, CloudDrive and Peach were restarted in the same execution context. Asset 4289 (`669.mp4`) then passed `video/mp4`, 1 KiB `206 Range`, thumbnail and generated-poster API checks. Drive-letter visibility differs by Windows token, so the HTTP stream check is the authoritative service test.

## Batch jobs

- The creator-board sampler completed before its implementation was changed; it left 86 boards and 598 cached frames. No `creator_boards.py` process was active at the final observation. The command now uses the shared source-access policy, disk guard, PID lock and Peach-managed FFmpeg resolver while preserving its prior arguments and output layout.
- Creator tagging is now review-first: `scripts/creator_tags.py --export-review` produced `R:\peach-data\generated\creator-tags-review.csv` with 86 boards, 30 prior decisions and 56 pending rows. A parallel worker may write only `candidate`/`skip`; applying accepts only coordinator-reviewed `approved` rows, requires a SQLite backup, and dual-writes compatibility plus canonical tag relations.
- A Claude Code 2.1.232 batch was asked to inspect those 56 boards but refused explicit sexual-act visual classification after 24 seconds; it made no CSV changes. The queue remains 27 applied, 3 skipped and 56 pending. Claude should be used for non-visual scraping/code/data reconciliation, not this visual category.
- The earlier Claude Desktop session did visually inspect boards and reported intermediate creator mappings (including `ruth_lee` and `luckydog22`), but its transcript and current ledger disagree: the reported `ruth_lee` foot/hand tags are absent from the persisted `vision_creator` rows. Treat chat text as evidence input, never as an applied result; only the review CSV plus database postcondition is authoritative.
- Migration `0005_backfill_legacy_tags.sql` is applied to the real ledger. It repaired all 27,295 late `vision_creator` compatibility rows missing from `asset_entity`, temporarily suspended the per-row FTS trigger and rebuilt affected search rows once. The real apply took about 7 seconds; 81,873 assets and 88,672 compatibility tag rows were preserved, canonical relations reached 159,172, missing legacy relations are zero, integrity is `ok` and foreign-key violations are zero. Backup: `R:\peach-data\database\ledger.pre-migrate-20260814-225437.db`.
- The visible terminal mistaken for a slow batch was the permanent `RM-TrafficWatch` heartbeat. Its scheduled action was changed from `python.exe` to `pythonw.exe` at 22:36, the task restarted successfully, and the new hidden process continued writing `trafficwatch-20260814-223642.log` every 30 seconds. It stops only matching Peach task trees and no longer terminates machine-wide FFmpeg/ffprobe processes.

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
- `scripts/creator_boards.py` + `scripts/creator_tags.py` — creator-level visual tagging. Boards tile one
  cell from each of nine different videos into a 3x3 sheet, so one image read characterizes a whole
  creator instead of a single title. 30 boards were read; 27 creators produced tags, covering 4,518
  videos and 27,295 `asset_tag` rows written as `source='vision_creator'`, `confidence=0.6` — deliberately
  distinct from per-title `vision` (0.9) and scraped `r18` (0.9), because the evidence describes a
  creator's recurring style rather than a confirmed property of each title. Untagged videos went
  12,056 → 7,538. Tags are constrained to the existing 76-term vocabulary; the script refuses to run if a
  tag is not already in it.
- Three creators were read but deliberately left untagged, with reasons recorded in `creator_tags.SKIPPED`:
  `BNST033` is 34 H-game advertisements, `G3104` is someone's personal camera roll, `tuki_1154` had too
  few usable frames. `R:\peach-data\generated\disposal-candidates.csv` lists the 106 affected files
  (3.7 GB + 1.2 GB) for a human disposal decision; nothing was deleted.
- Two vocabulary gaps surfaced: 3D/CG animated content (`oscarkim123`, `Bewyx 2509`) has no medium tag,
  and video-frame advertising has no marker. Neither was forced into an existing term.
- `scripts/find_ads.py` — identifies promo videos bundled into pirate release packs and writes
  `R:\peach-data\generated\ad-candidates.csv`. Nothing is deleted. 82 candidates, 1.5 GB: 77 marked
  `确认` and 5 `存疑`. Nine sampled directories were visually confirmed as ads (QR code plus promo
  domain in every frame). The strongest signal is structural, not lexical: a group of files in one
  directory sharing an identical byte size and identical duration. Three false-positive classes were
  found and excluded by construction, each verified against a real file:
  `1024` as a substring ate `FC2-PPV-1381024` (970 MB feature); `成人游戏`/`加微信` appear in genuine
  titles (a 9.98 GB feature); and a bare domain with no ad copy is usually a pirate-site watermark on
  real content (`jitumi.pw(1).avi` sampled to an ordinary clothed scene), so those rows are `存疑` for
  human review rather than `确认`.
- Ad-detection recall is bounded: 9,480 of 24,980 videos (38%) have no usable duration, so the
  identical-size-and-duration test cannot run on them, and ads composited into a real video's frames are
  not detectable by metadata at all. `BNST033` is not entirely advertising as previously recorded — its
  directory holds a genuine 3.2 GB feature beside roughly 50 promo clips.
- Remaining untagged videos are mostly creators whose PikPak sheets have not been generated, so visual
  tagging past this point is blocked on the metered PikPak sheet backlog.

## Deployed consolidation

- FastAPI now constructs one `MediaEngine`; filesystem access and the Stash public-protocol adapter are backends of that engine. Stash stream identity reads stable `media_binding` rows instead of using `asset.stash_scene_id` as the sole contract.
- Shared Job policy now owns parameterized source filtering, fail-closed disk-space checks and PID locks for probe, sheets and creator-board work. The traffic watcher targets only matching Python task trees and their descendants; it no longer kills every machine-wide ffmpeg/ffprobe process.
- Probe, sheets, creator boards and traffic watch are import-safe `main()` commands with existing scheduled arguments preserved; importing them for tests no longer opens the real database, log or lock file.
- Stash, OpenCode Go and Feed now share one HTTPX transport in the FastAPI process, including connection pooling, explicit timeouts and bounded response reads. Their protocol DTOs and privacy rules remain separate.
- Feed parsing uses feedparser 6.0.12, raster validation uses Pillow 12.3.0, and source HTML uses Beautiful Soup 4.15.0. `scripts/scrape_codes.py` and `scripts/import_stash_entities.py` also use the shared HTTPX boundary; source-specific selection, provenance and review policy remain Peach-owned.
- Migration `0004` is applied to the real ledger and maintains an FTS5 trigram row for every asset. Assets/entities/relations were unchanged at 81,873 / 8,590 / 131,877; FTS contains 81,873 rows, integrity is `ok`, foreign-key violations are zero, and an FC2 count took 0.0005 s. Production is running this query path; `q=FC2` returned 834 matching assets in the final API smoke test.
- `scripts/find_ads.py` was converted from a one-off hard-coded script into an import-safe, configurable, read-only candidate scanner with isolated tests. Its 82-row generated review result remains unchanged; it still deletes nothing.
- The reuse register and ADR-0010 record required mature dependencies, Peach-owned domain logic and old-to-current script successors. Production port 80 and the scheduled traffic watcher were both restarted onto the consolidated code.
- Final API smoke checks passed `/healthz`, FTS search, local asset 1 Range and CloudDrive asset 4289 Range. No real playback/feedback rows were written by verification.
- Desktop and 390×844 visual checks were attempted but remain unverified: the in-app browser blocks private LAN addresses and the local Firefox automation context could not start. This is a test-environment limitation, not a claimed visual pass.

## Next work

1. Reconcile Claude Desktop transcript candidates through `creator-tags-review.csv` rather than direct writes.
2. Add a Media Engine stream-plan endpoint and integrate hls.js or Shaka Player before enabling Stash HLS/DASH fallback in the browser.
3. Configure/evaluate Stash CommunityScrapers and metadata providers before writing another source adapter.
4. Add explicit feed configuration and reviewed import; only then use APScheduler. Add reviewed inference requests afterward, with AI output remaining candidates.
5. Move remaining legacy status/suggest/ledger application logic behind repository/application ports, then delete obsolete CLI surfaces.
