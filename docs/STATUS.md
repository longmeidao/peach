# Status

Last verified: 2026-08-15

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on HTTP `0.0.0.0:80` (listener PID 28676) and HTTPS `192.168.50.162:443` (listener PID 8268); health mode is `fastapi`.
- `peach.local` is again the single official LAN entry. The publisher restores the verified pre-migration behavior: Python zeroconf listens on all eligible interfaces and publishes `peach.local -> 192.168.50.162`. Production health reports `mdns_backend=zeroconf-all-interfaces`; same-host DNS-SD discovery and `getaddrinfo('peach.local')` both resolved the correct address after restart. A second LAN device remains the final external check; no firewall or router rule was changed.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: `0000`–`0007` applied; zero pending. The `0007` backup is `R:\peach-data\database\ledger.pre-migrate-20260815-013554.db`. It preserved 81,873 assets and 88,672 compatibility tag links, removed 298 reviewed structural creator links, passed `integrity_check`, and has zero foreign-key violations.
- Current pre-0002 recovery point: `R:\peach-data\archive\ledger.pre-migrate-20260814-162004.db`.

Runtime PIDs are observations, not configuration; always re-check them.

## Agent capacity snapshot

- Observed 2026-08-14 23:20 +08 through authenticated, secret-free usage reads: Codex main weekly window is 14% used / 86% remaining, resetting 2026-08-21 15:21 +08; GPT-5.3-Codex-Spark is 0% used, resetting 2026-08-21 23:07 +08.
- Claude Pro is 35% used in the five-hour window / 65% remaining, resetting 2026-08-15 01:50 +08; weekly is 79% used / 21% remaining, resetting 2026-08-17 13:00 +08. Extra usage is disabled.
- These are dispatch snapshots, not durable limits. T3 Code's 30-day historical view reports 3.88B processed tokens (Claude 2.25B, Codex 1.62B) and API-equivalent raw cost; it is not the subscription bill. Prefer Codex for long/critical work until the Claude weekly reset, and Claude for short mechanical candidate batches.

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
- 84 isolated tests pass under Python 3.14, including profile preference, batch operations, client routes, duration range, structural creator cleanup, cached browser transcodes, dynamic-handler safety, agent-worktree isolation and mDNS tunnel-route fallback. The current inline JavaScript also passes syntax validation.
- Real migration preserved 81,873 assets and 59,697 tag links; both live database and backup passed `integrity_check` and `foreign_key_check` before later metadata writes.
- The current slice passed isolated desktop 1280×720 and mobile 390×844 browser checks with zero horizontal overflow, all Lucide references resolved, no visible legacy length tags, and the mobile rail hidden.
- Restarted production port 80 passed health, home, public OpenCode Go model discovery (26 models at verification time), canonical filtered-list/item reads, thumbnail `200` and 1 KiB `206 Partial Content` Range smoke checks.
- After deleting the legacy server, restarted production also passed real `stats`, `tops` and `facets` aggregate contract checks.
- HTTPS is running on `192.168.50.162:443` with a local CA for `peach.local` and the LAN IP. The first generated CA lacked `keyUsage`; the script now emits critical CA constraints/key-sign usage and verifies the chain before install. Python/OpenSSL verification with the corrected CA passed. macOS/iOS clients must install only `peach-local-ca.crt` and explicitly trust it.
- `/stream` now keeps browser-native MP4/WebM/Ogg files on the standard direct Range path and sends unsupported containers through Peach's own immutable MP4 cache. The source is never modified; cache keys include asset id, source size and mtime. Real AVI assets 5272 and 5313 were converted in 5.2 seconds total and verified as H.264/yuv420p plus AAC before deployment.
- Studio logo fallbacks no longer compile metadata inside inline JavaScript handlers. Names containing apostrophes such as `Deep's` use DOM event listeners, eliminating the Firefox unescaped-string failure without weakening escaping.
- Immersive-mode actions use the shared local Lucide set; visible labels are replaced by accessible names and hover titles where the surrounding context is sufficient.
- Long-card hover now enlarges the card and exposes ±10-second preview seeking; short cards expose a profile-backed “稍后看” action. Item details show linked performers/studio/creator/series, and top performer/studio entries navigate to entity pages instead of mutating filters.
- The interaction pass now delays long-card enlargement and ±10-second controls until five seconds of continuous hover; quick pointer movement only previews. Creator names on cards and details navigate directly to entity pages. “换一批” is a filled action, not a pressed sort filter, and bottom “再来 60 个” pagination is replaced by an intersection-driven continuation sentinel.
- The desktop rail now prioritizes “全部艺人” and “全部标签” instead of duplicating “没看过/看过”; the drawer exposes the same destinations. The performer wall returned 600 entries and the tag cloud 173 in candidate verification. The statistics surface uses the shared card/grid language and no longer exposes a bottom load/refresh control.
- Item details now expose an independent Like signal plus a private “为什么喜欢” text field. Migration `0006` stores both by profile in `asset_preference`; it does not overload `asset.feedback`, `watch_queue`, rating, or orgasm count. The original note is truth and AI may only propose separately reviewed taste facets later.
- The detail feedback surface now uses one compact five-icon toolbar: Like, dislike, seen, Later and deletion candidate. Each has a semantic hover/active color, restrained motion, accessible label and hover explanation. “待删” explicitly means candidate-only; deletion still requires the reviewed CSV apply step. Orgasm count is a separate compact row. Entering a reason implies Like; its free-text semantics are not yet consumed by ranking.
- Video cards now prefer canonical performer portraits over creator/studio crops, and the portrait itself opens the performer page. The same performer payload is attached to homepage, related and ad-review cards. Back controls share one aligned pill treatment; drawer navigation has a short reopen guard so the rail cannot immediately cover the destination page.
- Five-second hover controls use consistent top-right circular rewind/forward/open actions, while short cards retain the immediate Later action. Homepage/filter/tag pills and studio icon treatments are now deliberately subdued instead of category-bright.
- Official 115 (120 px PNG), PikPak (SVG), S1 and kawaii marks are cached with source sidecars and rendered centered in source filters/badges. The complete studio-logo audit now finds 28/114 canonical studios with a cached logo and 86 missing. Missing studios show initials rather than a misleading representative-work crop; online logo completion remains queued.
- Migration `0003` added entity summaries, typed links/search terms and `watch_queue`. Thirteen reviewed studio duplicate groups were merged with 15 aliases; Prestige has 248 video assets after Japanese/Prestige Premium normalization, while distinct `PREMIUM` remains separate.
- FC2's 16×16 favicon was replaced by the official 102×43 asset and the user-provided Prestige logo was cached locally, both with provenance sidecars. Performer-image routing prefers a provenance-backed entity cache; Stash's default SVG silhouette is rejected rather than mislabeled as an HD portrait.
- `scripts/import_stash_entities.py` reconciled the Stash public performer contract into Peach without making Stash authoritative: 383 exact stable refs, 52 aliases/search terms and two explicitly declared X links were imported. Of 42 non-placeholder Stash images, 14 passed the 512 px short-side gate and were cached with provenance; 28 smaller images were rejected. Top entries including 一个ren、高桥千凛 and 小桃 now use 720 px-class cached portraits.
- Current production desktop verification passed home loading, 60 cards, item expansion, Like/reason controls and zero horizontal overflow. No real preference or playback data was written during this production browser check.
- The current isolated candidate passed desktop and 390×844 checks for detail identity rows, the five icon controls, 4 px progress bars, mobile overflow, route changes and hidden legacy length tags. The drawer remained closed at content x=120 and opened only after entering the actual 72 px rail. Five-second hover exposed the pinned Lucide rewind/forward/maximize controls only after the preview ring completed its delay.
- The 20:36 Peach restart was launched only after verifying the port-80 command line in the host session. The replacement process can see CloudDrive: asset 4289 again passed `video/mp4` 1 KiB `206 Partial Content` and poster `200`; local asset 1 passed the same Range contract. A sandbox drive check is not authoritative.
- The mDNS regression fix remains deployed. Production explicitly advertises `192.168.50.162` while Zeroconf listens on all eligible interfaces; health and `Resolve-DnsName peach.local` returned that address after restart. No `lmd-dst.local` alias is published by Peach.
- The original Peach process could not see CloudDrive `A:`/`B:` even though CloudDrive was running. After confirming zero copy tasks and no I/O, CloudDrive and Peach were restarted in the same execution context. Asset 4289 (`669.mp4`) then passed `video/mp4`, 1 KiB `206 Range`, thumbnail and generated-poster API checks. Drive-letter visibility differs by Windows token, so the HTTP stream check is the authoritative service test.

## Batch jobs

- The creator-board sampler completed before its implementation was changed; it left 86 boards and 598 cached frames. No `creator_boards.py` process was active at the final observation. The command now uses the shared source-access policy, disk guard, PID lock and Peach-managed FFmpeg resolver while preserving its prior arguments and output layout.
- Creator tagging is now review-first: `scripts/creator_tags.py --export-review` produced `R:\peach-data\generated\creator-tags-review.csv` with 86 boards, 30 prior decisions and 56 pending rows. A parallel worker may write only `candidate`/`skip`; applying accepts only coordinator-reviewed `approved` rows, requires a SQLite backup, and dual-writes compatibility plus canonical tag relations.
- A Claude Code 2.1.232 batch initially stopped after 24 seconds, but the later completed run read 30 boards and classified 27 creators without refusal. The persisted 27,295 `vision_creator` rows reconcile exactly with that run's declared creator-level tag sets. An older per-title pass remained chat-only and wrote neither CSV nor ledger rows; only persisted review artifacts plus database postconditions are authoritative.
- Migration `0005_backfill_legacy_tags.sql` is applied to the real ledger. It repaired all 27,295 late `vision_creator` compatibility rows missing from `asset_entity`, temporarily suspended the per-row FTS trigger and rebuilt affected search rows once. The real apply took about 7 seconds; 81,873 assets and 88,672 compatibility tag rows were preserved, canonical relations reached 159,172, missing legacy relations are zero, integrity is `ok` and foreign-key violations are zero. Backup: `R:\peach-data\database\ledger.pre-migrate-20260814-225437.db`.
- The 115 backlog was not blocked by missing work; it was unreachable. `probe.py` selected only
  `duration IS NULL`, while a soft ffprobe failure had been persisted as `duration=0`, which also fails
  the sheets `duration>2` gate. 3,937 of the 4,034 blocked 115 rows sat in that gap, which is why
  "probe backlog is empty" and "4,034 blocked" were both true. Unknown durations now persist as `-1`
  and `--redo zero|failed|all` re-queues recorded failures. The real 115 pass processed 3,737 rows in
  54.2 minutes with 38 failures (1%); the `zero` bucket is now empty and sheetable 115 rows went
  19 → 3,914. It cost about 98 GB of 115 download, roughly 25 MB per file probed.
- Measured transfer cost, 2026-08-15, through the mihomo connection counter: 115 is routed DIRECT via
  `cdnfhnfile.115cdn.net` and PikPak through the proxy via `*.mypikpak.net`. A nine-frame contact sheet
  costs about 285 MB on 115 (1,074 MB source) and 163 MB / 13.7 s on PikPak (385 MB source). The earlier
  "25~40 s per PikPak frame" record does not reproduce; the real constraint is bytes, not seconds.
  `-probesize/-analyzeduration` limiting does **not** reduce it — the bytes are CloudDrive block
  prefetches in fixed ~12.9 MiB units spread across several CDN nodes, below FFmpeg's control.
- `traffic_watch.py` counted only non-DIRECT bytes, so a metered source routed DIRECT would never trip
  the ceiling. `--count-direct` now puts direct bytes in the same budget and the per-connection delta
  split is a pure `accumulate()` with tests. PikPak was then measured as proxied, so the resident
  proxy-only 200 GB watcher does cover it; the 98 GB of 115 traffic remains invisible to every ceiling.
- `disposal-candidates.csv` was regenerated at 22:53 and no longer lists the 3.2 GB `BNST033.mp4`
  feature for disposal — it now carries verdict `保留` with the reason recorded, beside three `存疑`
  rows from the same directory. The HANDOFF entry describes the historical incident, not a live defect.
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
  `BNST033` mixes a real feature with advertisements, `G3104` lacks reliable classification evidence,
  and `tuki_1154` had too few usable frames. User-confirmed corpus context is consenting adults only;
  labels such as `泄露`/`流出` are marketing/source vocabulary, not evidence of non-consent. The generated
  disposal review remains candidate-only; nothing was deleted.
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
- Desktop 1280×720 and mobile 390×844 are currently verified against an isolated copy of the database. Production HTTP/HTTPS/API checks are reported separately and never use feedback/play writes.

## Next work

0. **Resume the 115 sheet pass**: `python scripts/sheets.py --location 115 --workers 4`. It was stopped
   at the user's request on 2026-08-15 03:58 for a machine shutdown, not by a failure. 680 of the 3,914
   rows the probe fix unblocked are done; 3,234 remain and the job resumes by itself because it selects
   on `snapshot_path IS NULL`. Sheets already written but not yet registered (the ledger commits every
   50 rows) are re-detected as `已存在` and cost no download. The stale PID lock left by the kill was
   removed after confirming the process was gone.
   Measured rate: **163 MB and 3.3 s per contact sheet**, 3.3% failures, largest files first — so that
   is an upper bound and the remainder should stay under ~530 GB, not the 1 TB first extrapolated from
   a single large sample. When it
   finishes, run `creator_boards.py` (snapshot mode is free) for the newly sheetable creators, then the
   review-first `creator_tags.py --export-review` queue. Note the ceiling of that route: of the 2,547
   untagged 115 videos only 577 have a creator, 1,051 carry a code that is 384 FC2 plus ~330 `WX`-style
   amateur codes — exactly the sources measured to return zero catalogue hits — and 1,031 have neither.
   Creator boards and code scraping cannot reach roughly 1,500 of them; do not present either as a plan
   for the whole 115 tail.
   PikPak remains deliberately untouched: the user deferred it on 2026-08-15 rather than declining it.
   The prepared step is creator sampling only — 88 boards, ~792 frames, ~14 GB, ~20 minutes, under a
   dedicated `--limit 100` sentinel, and with no PikPak probe pass beforehand. Full PikPak sheeting
   (~773 GB) and a full PikPak probe (~207 GB) are both out of budget and should not be started.
1. Extend source/provenance sampling to weight the opening and final frames in addition to the existing
   representative board cells. Detect visible handles/domains/watermarks there, and add a reviewed
   `incomplete/cut` candidate when end cards say `full version available` or equivalent. Seed the first
   regression fixture from `115/04_Stepsistercaughtmejerkingoff,deepthroat,throatpie.mp4`, whose final
   seconds point to `fansly.com/smuzillipussy`; do not persist the attribution without frame evidence.
2. Finish visual identity quality: implement the deferred portrait scoring hierarchy (reviewed/public HD
   portrait → high-quality public portrait → face-aware crop from the most-watched work → sharp keyframe),
   and source the 86 missing studio logos from official/public sources with provenance and quality gates.
3. Add a Media Engine stream-plan endpoint and integrate hls.js or Shaka Player before enabling Stash HLS/DASH fallback in the browser.
4. Configure/evaluate Stash CommunityScrapers and metadata providers before writing another source adapter.
5. Add explicit feed configuration and reviewed import; only then use APScheduler. Add reviewed inference requests afterward, with AI output remaining candidates.
6. Run a pre-release copy audit: replace or delete construction-stage explanatory prose, keeping only text that changes a decision, prevents data loss or explains an unfamiliar state. Then move remaining legacy status/suggest/ledger application logic behind repository/application ports and delete obsolete CLI surfaces.

Claude project hooks now refresh the managed batch block on Stop, StopFailure and SessionEnd. Codex has no equivalent task-end project hook; its coordinator must keep the same STATUS/HANDOFF write contract manually. Hook verification used a synthetic event and a temporary document/state file; no prompt, response or token was persisted.

The current UI/API candidate passed JavaScript parse, 84 isolated tests, desktop 1280×720 and mobile 390×844. Production HTTP, HTTPS and mDNS were restarted onto this code. HTTPS chain verification passed with the corrected local CA; browsing tests remained on the isolated candidate and did not write real playback, preference or feedback data.

## 批处理进度（自动生成）

<!-- job-status:start -->

<!-- 由 scripts/job_status.py 生成，勿手改；数字现算于账本与产物 -->
<!-- generated 2026-08-15T01:56Z -->

- 最近自动交接：`claude` / `Stop` / `completed`，2026-08-15T01:56:09+00:00。
- 资产 81873 条，其中视频 24980 条。
- 待抽帧（可抽 / 缺时长待 probe / 合计）：
  - `local`：4 / 1 / 5
  - `115`：3134 / 139 / 3273
  - `pikpak`：4751 / 5445 / 10196
  PikPak 计费且走代理（`*.mypikpak.net`）；2026-08-15 实测 9 帧接触表 163 MB / 13.7 秒，即约 18 MB、1.5 秒一帧。瓶颈是流量不是时间：全量抽帧约 773 GB，按创作者采样 88 板约 14 GB / 20 分钟。115 走直连，同样动作约 285 MB 一张接触表。
- 无内容标签视频 7538 条（占视频 30%）。
- `asset_tag` 来源分布：`vision_creator` 27295、`pixiv_tag` 19753、`name` 19107、`stash` 15450、`r18` 2538、`performer` 1887、`follow` 1376、`r18:performer` 1216、`javbus:performer` 50。
- 番号 1434 个，其中 1158 个有厂牌（81%）。

| 产物 | 行数 | 生成时间 | 说明 |
| --- | ---: | --- | --- |
| `code-scrape.csv` | 1104 | 08-14 16:17 | 番号刮削结果 |
| `name-clean.csv` | 287 | 08-14 16:18 | 文件名净化清单 |
| `ad-candidates.csv` | 82 | 08-14 22:53 | 广告候选（confidence 分级） |
| `disposal-candidates.csv` | 54 | 08-14 22:53 | 待处置候选（含「保留」判定） |
| `creator-tags-review.csv` | 86 | 08-14 22:30 | 创作者标签待审 |

<!-- job-status:end -->
