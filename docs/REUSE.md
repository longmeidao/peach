# Reuse register

This file is the implementation lookup table shared by Codex and Claude. Check it before adding or restoring code.

## Peach-owned domain logic

These are product behavior and remain custom:

- canonical performer/studio/creator/tag identity, aliases and provenance;
- profile behavior, watch queue, taste and recommendation ranking;
- local/115/PikPak/Stash/online binding and fallback policy;
- metered-source authorization, privacy classification and reviewed candidate import;
- private acquisition/source references and discovery keywords;
- creator-level visual sampling semantics;
- inference-provider versus agent-provider capability contracts;
- job ownership, progress, cancellation, cost and evidence rules.

## Required reuse

| Capability | Reuse | Peach responsibility |
|---|---|---|
| HTTP | project-wide `httpx.Client`/transport | source policy, DTO and redaction |
| RSS/Atom | `feedparser` | bounded fetch, snapshots, review and import |
| HTML adapters | Beautiful Soup or selectolax | source-specific selectors and provenance |
| Raster images | Pillow | portrait/logo quality and source policy |
| Search | SQLite FTS5 | indexed fields, ranking and profile-aware filters |
| Media probe/transcode | managed FFmpeg/ffprobe | job policy and Media Engine orchestration |
| HLS/DASH playback | hls.js or Shaka Player | stream plan, authorization and fallback order |
| Icons | pinned local Lucide subset | labels, state and interaction design |
| Scheduled polling | APScheduler when persistent feed config exists | job definitions and safety policy |
| Local file events | watchdog plus periodic reconciliation | media identity and missed-event repair |
| Transitional metadata/media | Stash GraphQL, CommunityScrapers and Stash job system | adapter, reconciliation and exit gates |
| LAN discovery | Python zeroconf | service lifecycle and real-client acceptance |
| Agent usage/quota | official provider quota APIs; T3 Code/CodexBar for local history | task routing, redaction and stale-snapshot labeling |
| Video source/end-card evidence | existing FFmpeg frame extraction plus a reviewed OCR/vision adapter | opening/ending sample policy, provenance and incomplete-version candidates |
| Referenced product behavior | current live interaction plus versioned public DOM/CSS/JS, or exact screenshot measurements when source is unavailable | evidence register, accessibility, Peach-specific deviations and regression checks |

Do not introduce a dependency until its first consumer and isolated tests land in the same change.

## Maintained successors

| Removed/old name | Current implementation | Rule |
|---|---|---|
| `rm-web.py` / `rm-web.html` | `src/peach/api.py`, `src/peach/web_contract.py`, `web/index.html` | never restore the HTTP server |
| `rm-javlookup.py` | `scripts/scrape_codes.py` | extend source adapters; do not fork another scraper |
| `rm-probe.py` | `scripts/probe.py` | move reusable policy into `src/peach`, preserve resume semantics |
| `rm-sheets.py` | `scripts/sheets.py` | share FFmpeg/job primitives; do not create another sheet pipeline |
| `rm-ledger.py` | `scripts/ledger.py` plus repository/migrations | new product reads belong in repositories, not this legacy CLI |
| `rm-status.py` | `scripts/status.py` | status is read-only |
| `rm-suggest.py` | `scripts/suggest.py` | ranking logic will move behind an application port |
| `rm-trafficwatch.py` | `scripts/traffic_watch.py` | stop only owned task process trees |
| `rm-sha1.py` | `scripts/sync_sha1_115.py` | reuse provider hashes; do not rehash cloud media blindly |

## Current replacement queue

Completed in the consolidation slice: shared Media/Job/HTTP boundaries, feedparser, Pillow, Beautiful Soup, FTS5, import-safe batch scripts and scoped task termination.

1. Add a Media Engine stream-plan API and a mature HLS/DASH player before using Stash transcodes in the browser.
2. Configure and evaluate Stash metadata providers before writing another source adapter.
3. Move remaining legacy status/suggest/ledger application logic behind repository/application ports, then delete obsolete CLI surfaces.
4. Do not build a token/cost log scanner inside Peach or bind to T3 Code's private RPC; use its UI/CodexBar and official live quota surfaces.
5. “模仿/参考/对齐” is not authorization to approximate from memory. Obtain and record reproducible evidence before implementation; otherwise mark the item `未取得` and keep it out of production.
