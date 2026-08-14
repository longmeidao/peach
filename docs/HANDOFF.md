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
- **Superseded 2026-08-14.** The earlier note that Claude refuses explicit sexual-act classification from
  board images is not what happens. In one session Claude read 30 creator boards and assigned explicit
  act and attribute tags for 27 creators — 4,518 videos, 27,295 `asset_tag` rows under `vision_creator`,
  including 口交/足交/手交/乳交/骑乘/后入 — with no refusal, and a later reconciliation matched all 27
  declared tag sets to the ledger exactly. Route board reading to Claude normally.
- The `ruth_lee` divergence was not a Claude/ledger disagreement either. The current ledger matches this
  session's assignment exactly (7 tags × 310 assets). The mismatched conclusion came from an **earlier,
  different** per-title pass that had no write step at all: `asset_tag` still holds zero rows with
  `source='vision'`. The lesson is about persistence, not about model capability — see
  "A conclusion that lives only in chat does not exist".

## Claude's actual boundary on this project

Stated so work is routed on fact rather than on a guessed refusal. Verified by what ran on 2026-08-14.

Does, without friction:

- Viewing explicit sexual imagery and classifying acts, attire, body attributes, setting and production
  style, for cataloguing this personal library.
- Scraping public catalogue metadata (r18.dev, avsox, javbus) and mapping foreign categories to the
  local vocabulary.
- Writing the code, regexes, batch jobs and reconciliation for all of the above, and generating
  explicit-domain text such as tag names and Chinese titles.
- Naming a performer or studio from a code, filename, or an on-screen watermark or logo.

Will not, and these are firm:

- Anything involving minors or apparent minors. The library's 萝莉/学生/洛丽塔/制服 tags are treated
  strictly as adult-performer genre labels; if real footage of a minor is ever found, the answer is to
  stop and report it, not to catalogue it.
- Identifying a real person from their face. Attribution comes from codes, filenames, watermarks and
  release metadata only — never from facial matching, and never linking media to a private individual's
  real identity.
- Helping acquire or redistribute non-consensual material. This is not the current corpus state: the user
  confirms all performers are adults and all material is consensual. `萝莉`/`学生`/`洛丽塔`/`制服`
  describe adult role-play, while `泄露`/`流出` and the appearance of `G3104` are marketing/source-style
  descriptions, not proof of provenance or consent. Catalogue those strings normally; only direct,
  file-specific contradictory evidence warrants stopping and reporting.
- Destructive or outward-facing actions without explicit confirmation. Delete lists are produced as CSV
  with evidence and confidence; the apply step is the user's.

Weak, not refused — route accordingly:

- Frame-level certainty from one still. Creator-level style inference is reliable; per-title claims from
  a single frame are not, which is why `vision_creator` carries `confidence=0.6`.
- Reading dark, blurred or heavily mosaicked frames (`tuki_1154` was skipped for exactly this).
- Distinguishing a pirate-site watermark from an advertisement by filename alone — that needed an
  extracted frame to settle (`jitumi.pw`).

## A conclusion that lives only in chat does not exist

Two failures of this shape occurred on 2026-08-14, so treat it as a rule.

An earlier per-title visual tagging pass read boards, stated its conclusions in conversation and said
they were stored. `asset_tag` holds zero rows with `source='vision'`; that pass had no write step and
left no CSV or log. Separately, `disposal-candidates.csv` was generated while `BNST033` was believed to
be entirely advertising. The belief was corrected in chat and in `docs/STATUS.md`, but the CSV was not
regenerated and still listed the genuine 3.2 GB feature `BNST033.mp4` for disposal.

Neither was a refusal — explicit tags including 足交/手交/足系 were written without obstruction in the
same session.

- A step that reaches a conclusion must write it to a file or the ledger in that same step.
- When a conclusion is revised, regenerate every artifact derived from it. Updating prose is not enough;
  a stale delete list is more dangerous than no list.
- Record evidence beside the verdict. `ad-candidates.csv` carries a `verified` column naming the rows
  confirmed by looking at an extracted frame, and a `排除` state for one row that proved to be real
  content.
- Reconcile declared intent against the database before reporting completion. Comparing
  `creator_tags.BOARDS` against actual `asset_tag` rows is what surfaced both problems.

Claude task endings are now covered by shared project hooks in `.claude/settings.json`: normal Stop,
StopFailure and SessionEnd invoke `scripts/job_status.py --write --hook-event`. The script records only a
sanitized lifecycle summary under `R:\peach-data\state`, recomputes every figure from the ledger and
generated artifacts, and atomically rewrites the `<!-- job-status -->` block in `docs/STATUS.md`. It does
not copy prompts, responses or credentials. Hard process kills and machine power loss cannot run a hook;
the next invocation repairs the live counts. Prose outside the managed block remains hand-maintained.

Codex does not currently expose an equivalent project task-completion hook. Its project contract still
requires the coordinating agent to update STATUS/HANDOFF in the same change; do not invent a brittle log
watcher to simulate lifecycle events.

## Agent capacity and usage routing

- Use official quota windows for dispatch decisions, not API-equivalent dollar estimates. Codex exposes
  live limits through App Server `account/rateLimits/read`; Claude usage is visible through Claude Code's
  authenticated usage surface. Never print, copy or persist OAuth access tokens.
- T3 Code already provides the useful historical dashboard for Codex + Claude processed/cached/output
  tokens and API-equivalent costs. CodexBar is the reference implementation for local log accounting and
  provider quota fallback. Peach must not recreate their session-log scanner or couple to T3 Code's
  undocumented localhost RPC.
- Route architecture, migrations, browser-dependent websites, final review/apply and long-running work to
  Codex. Route bounded mechanical scraping, normalization, candidate CSV reconciliation, filename/code/
  watermark extraction and reviewed board classification to Claude when its remaining window permits.
- Creator/performer attribution may use release codes, filenames, watermarks, studio metadata, aliases,
  public profile links and cross-source consistency. A face may support same-library consistency review,
  but a persisted identity requires non-face corroboration; never link media to an unrelated private
  person's real-world identity from facial appearance alone.

Report backlog counts as **actionable / blocked / total**, never as a single number. "4,740" and
"10,196" were treated as contradictory PikPak figures when both were correct: 4,740 rows carry a
duration and can be sheeted, 5,445 carry none and need a probe pass first. `job_status.py` always prints
all three.

## Reuse before restore

- Read `docs/REUSE.md` before introducing a library, protocol implementation or restored legacy script.
- Search the current tree by capability and output contract, not only by the old filename. `scripts/scrape_codes.py` is the maintained successor to the removed `rm-javlookup.py`; restoring the old scraper is forbidden.
- The restructure was not a clean-room rewrite: probe, sheets, status, suggest, traffic watch, SHA1 sync, ledger and the web surface were migrated from legacy implementations. Treat them as inherited code until their behavior has been deliberately replaced and tested.
- Git history is recovery evidence, not an implementation catalog. Restore code only after proving no current successor or mature dependency covers the capability.

## Data safety

- Real ledger: `R:\peach-data\database\ledger.db`; WAL mode; normal browsing legitimately changes play/activity fields.
- Tests must create temporary SQLite databases and temporary media files.
- Before real migration: SQLite backup, asset/tag counts, `PRAGMA integrity_check`, migration version check, then service smoke test.
- Formal migrations `0000`–`0006` are applied to the real ledger. `0003` adds the local default profile, profile-scoped watch queue, typed entity links and entity search terms. `0004` adds synchronized SQLite FTS5 trigram search. `0005` backfills late compatibility tags into canonical relations. `0006` adds profile-scoped `asset_preference` without changing asset rows. Its backup is `R:\peach-data\database\ledger.pre-migrate-20260815-000500.db`; retain it with the earlier recovery points until a later verified migration.
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
- Performer/studio/creator/series names navigate to entity pages; only content tags are direct homepage filters. `entity_link.source_reference` is private provenance and must not become a clickable download link. “稍后看” writes `watch_queue`, never feedback. “喜欢/为什么喜欢” writes profile-scoped `asset_preference`; the note is user truth, while any future AI-derived taste facets must be stored separately with provenance/confidence/review.
- Navigation versus filtering is visually explicit: “换一批”, statistics, immerse, all-performers and all-tags are actions/destinations and never render as persistent filter state. The desktop rail reserves its large icons for destinations/actions; `看过`/`没看过` remain compact content-state chips. Main-list pagination is automatic, not a bottom “再来 60 个” button.
- Long-card enlargement and seek controls require five continuous hover seconds. Short cards keep immediate “稍后看”. A creator/studio/performer text link consumes the click and opens the entity page; it must never bubble into video expansion.
- Source and studio marks use cached official assets with provenance. Missing studio logos show initials, never an arbitrary work/avatar. As of the 2026-08-14 audit, canonical studio coverage is 27/114; continue through the review queue instead of inventing logos.
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
