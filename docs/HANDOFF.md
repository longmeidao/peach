# Handoff

This is durable operating knowledge, not a per-session transcript.

## Zero-friction agent handoff

- Codex automatically discovers `AGENTS.md` in the project hierarchy.
- Claude Code automatically reads `CLAUDE.md`; this repository's `CLAUDE.md` imports `AGENTS.md`.
- Both agents therefore receive the same contract and the same mandatory reading order.
- Do not ask the outgoing agent to write a dated handoff. A task that changes reality must update `docs/STATUS.md`; a durable lesson changes this file or an ADR.
- Start every new task with `R:\peach-app` as the working directory and say only: “接手 Peach，按项目入口文件继续 STATUS 中的下一任务。”
- The user is not the message bus. Do not ask the user to copy technical conclusions to another agent; update the shared documents in the same change.
- If the worktree is dirty, inspect and preserve every existing diff. One agent owns a file while actively changing it; work on non-overlapping files or wait for that write to finish, then integrate the diff instead of recreating it.

## Parallel agent execution

- Codex is the coordinator for architecture, code ownership, review, migrations, real-ledger writes, service restarts and final verification. Claude is a parallel worker for bounded mechanical batches such as board reading, metadata candidate scraping and CSV reconciliation; handoff is not the goal.
- Parallel workers receive explicit input/output paths, network and cost policy, write boundary and acceptance criteria. They write `candidate` review artifacts only; they do not mark their own output `approved`, run `--apply`, alter migrations/ADR, or restart services.
- Use separate Git worktrees for concurrent code changes. Data-only batches may share the main checkout only when their sole writable artifact is outside Git and named in the task. Never let two agents edit the same file.
- Worker results return to the coordinating agent for vocabulary/provenance checks, deduplication, isolated tests and approval. The user does not relay reports between agents.
- `scripts/scrape_codes.py` and `scripts/creator_tags.py` are the standard review boundaries. Creator-board work exports `generated/creator-tags-review.csv`; workers may change `pending` to `candidate` or `skip`, while `approved` and the required backup remain coordinator actions.
- Claude Code 2.1.232 refused explicit sexual-act classification from board images. Do not assign that visual-content category to Claude again unless its supported-use boundary is reverified; use human review or a separately approved vision provider. Claude remains suitable for code, public metadata adapters, deduplication and non-visual CSV validation.
- An older Claude Desktop conversation did perform board inspection, but conversation text is not proof of persistence: its reported `ruth_lee` mapping differs from the current ledger. Read the transcript only as candidate evidence and reconcile it into the review CSV; database counts and canonical relations are the completion gate.

## Reuse before restore

- Read `docs/REUSE.md` before introducing a library, protocol implementation or restored legacy script.
- Search the current tree by capability and output contract, not only by the old filename. `scripts/scrape_codes.py` is the maintained successor to the removed `rm-javlookup.py`; restoring the old scraper is forbidden.
- The restructure was not a clean-room rewrite: probe, sheets, status, suggest, traffic watch, SHA1 sync, ledger and the web surface were migrated from legacy implementations. Treat them as inherited code until their behavior has been deliberately replaced and tested.
- Git history is recovery evidence, not an implementation catalog. Restore code only after proving no current successor or mature dependency covers the capability.

## Data safety

- Real ledger: `R:\peach-data\database\ledger.db`; WAL mode; normal browsing legitimately changes play/activity fields.
- Tests must create temporary SQLite databases and temporary media files.
- Before real migration: SQLite backup, asset/tag counts, `PRAGMA integrity_check`, migration version check, then service smoke test.
- Formal migrations `0000`–`0005` were applied to the real ledger on 2026-08-14. `0003` adds the local default profile, profile-scoped watch queue, typed entity links and entity search terms. `0004` adds synchronized SQLite FTS5 trigram search over asset names/codes, canonical entities, aliases and private search terms. `0005` backfills compatibility tags written after `0002` into canonical relations and rebuilds affected FTS rows in one batch. Its backup is `R:\peach-data\database\ledger.pre-migrate-20260814-225437.db`; retain it with the earlier recovery points until a later verified migration.
- Media and runtime data remain under `R:\media` and `R:\peach-data`; they are not repository assets.

## Operations

- Main command: `peach serve|migrate` after editable installation.
- `peach serve` 默认用 Python zeroconf 发布唯一入口 `peach.local`；使用 `--no-mdns` 可关闭。必须保留迁移前已验证的 `Zeroconf()` 全合格网卡语义，不要缩窄为单一 IPv4，也不要改用只能发布服务/SRV 的 Windows `DnsServiceRegister`。注册在 FastAPI lifespan 中执行，不能在事件循环内同步阻塞。mDNS 修改的验收门槛是：单元测试、运行态 health、DNS-SD 查询、主机名解析，以及一台真实 LAN 客户端；监听端口枚举或注册回调不能单独证明可用。
- TLS 仅在同时提供 `--ssl-certfile` 和 `--ssl-keyfile` 时启用；`.local` 使用本地 CA，不使用 Let's Encrypt，证书和私钥留在 `R:\peach-data\secrets`。
- FastAPI is the only Web server. `web_contract.py` contains the stable JSON surface; do not recreate a parallel `http.server` or dynamic legacy loader.
- FFmpeg/ffprobe resolve from explicit environment overrides, then `R:\peach-data\tools\ffmpeg\bin`, then `PATH`. No active code may fall back to the Stash private directory.
- Long-running inventory helpers are under `scripts/`; their scheduled tasks use `R:\peach-app\.venv\Scripts\python.exe`. They use absolute data paths and may be interrupted/restarted where their own locking contract allows it.
- Probe, sheets, creator boards and traffic watch parse arguments only inside `main()`. They share `src/peach/jobs.py` for fail-closed disk checks, parameterized source policy and PID locks. Traffic watch stops only matching Peach Python process trees; never restore machine-wide ffmpeg termination.
- Stash, OpenCode Go, Feed, code scraping and performer-image imports use the shared HTTPX transport. Feed XML is parsed by feedparser, raster images by Pillow and source HTML by Beautiful Soup. New adapters must reuse these boundaries instead of adding urllib helpers, manual image headers or HTML regex parsing.
- Importing operational scripts must have no filesystem/network/database side effects. `scrape_codes.py` sends only catalog codes to declared metadata sources, writes a resumable review CSV, and dual-writes provenance only with `--apply`. `clean_names.py` previews first and creates a SQLite backup before every apply run.
- Check ports 80, 8900 and 9999 before starting or switching services.
- 115/PikPak playback depends on CloudDrive mounts `B:`/`A:`. Drive-letter visibility differs by Windows execution token; CloudDrive and Peach must see the same mount namespace. A running process or a drive check from another token proves nothing—test one known `/stream` through Peach. Restart CloudDrive only after proving no copy task and no active I/O.
- Ledger snapshot paths written before the project/data split are rebased by an exact configured legacy prefix. Do not add basename searches or arbitrary path fallbacks.
- Report verification separately: static/unit/API, desktop browser, 390×844 browser, and whether production was actually restarted.

## Architectural truth

- Ledger owns truth and behavior.
- Stash is a replaceable adapter; do not add new direct GraphQL helpers or private Stash FFmpeg paths.
- All Stash calls use `StashClient`. Imports persist the stable Scene ID and provenance in `media_binding`; do not regress to `stash_scene_id` as the only external reference.
- Canonical performer/studio/tag/creator truth belongs in `entity`, `entity_external_ref` and `asset_entity`. Flattened `asset_tag` rows are a temporary compatibility projection, not the target model.
- Item/detail/filter/search/facets/index/stats/top lists/related ranking use canonical relations. Flattened creator/studio fields remain only as response compatibility projections; do not use them for identity or matching.
- Performer/studio/creator/series names navigate to entity pages; only content tags are direct homepage filters. `entity_link.source_reference` is private provenance and must not become a clickable download link. “稍后看” writes `watch_queue`, never feedback.
- Entity portraits resolve `generated/avatars/<kind>-<entity_id>.img` first and carry content-type/provenance sidecars. Do not accept Stash's default SVG silhouette or search-result thumbnails as portraits; representative asset crops are fallback only.
- `scripts/import_stash_entities.py` is the transitional performer identity importer. It uses `StashClient`, exact canonical-name matches, stable external refs, dry-run by default and a required backup on apply. Only localhost Stash image URLs are accepted; placeholders and images below a 512 px short side are rejected. Only aliases explicitly marked `X:`/`Twitter:` become social links; plain `@handle` remains a search term because its network is ambiguous.
- Reviewed studio merging runs through `scripts/canonicalize_studios.py` (dry-run by default, backup required for apply). `PREMIUM` is a distinct studio; only Prestige Premium and Japanese Prestige spellings alias to `Prestige`.
- Keep FastAPI and the front end logically separate but deploy as a monolith.
- External sources and AI are supported only through explicit adapters and declared data boundaries.
- `FeedAdapter` is the first online-follow connector. It performs explicit bounded RSS/Atom discovery; `FeedSnapshotStore` separates immutable evidence under `sources/follow` from conditional-request cursors under `state/follow`. Do not make it poll on application startup or write ledger rows directly.
- AI provider layers are not equivalent: inference APIs and local coding/agent runtimes remain separate.
- Search terms of three or more characters use FTS5 trigram; shorter text falls back to LIKE because trigram cannot index shorter terms. FTS writes are maintained by migration triggers, not by Web startup repair.

## Recovery

Deprecated scripts and old dated documents were removed from the active tree during the `peach-app` restructure. They remain recoverable from Git history before the restructure commit. Former `_SHARED_STATE` content lives under `R:\peach-data\state`; it is deliberately outside version control. The pre-restructure root repository metadata is retained temporarily under `R:\peach-data\archive\peach-root-repo-backup-20260814` as a recovery copy.
