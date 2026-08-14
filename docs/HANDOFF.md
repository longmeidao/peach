# Handoff

This is durable operating knowledge, not a per-session transcript.

## Zero-friction agent handoff

- Codex automatically discovers `AGENTS.md` in the project hierarchy.
- Claude Code automatically reads `CLAUDE.md`; this repository's `CLAUDE.md` imports `AGENTS.md`.
- Both agents therefore receive the same contract and the same mandatory reading order.
- Do not ask the outgoing agent to write a dated handoff. A task that changes reality must update `docs/STATUS.md`; a durable lesson changes this file or an ADR.
- Start every new task with `R:\peach-app` as the working directory and say only: “接手 Peach，按项目入口文件继续 STATUS 中的下一任务。”

## Data safety

- Real ledger: `R:\peach-data\database\ledger.db`; WAL mode; normal browsing legitimately changes play/activity fields.
- Tests must create temporary SQLite databases and temporary media files.
- Before real migration: SQLite backup, asset/tag counts, `PRAGMA integrity_check`, migration version check, then service smoke test.
- Formal migrations `0000` and `0001` were applied to the real ledger on 2026-08-14. The verified pre-migration recovery point is `R:\peach-data\archive\ledger.pre-migrate-20260814-152821.db`; do not delete it until later migrations have their own verified recovery point.
- Media and runtime data remain under `R:\media` and `R:\peach-data`; they are not repository assets.

## Operations

- Main command: `peach serve|migrate` after editable installation.
- FastAPI is the only Web server. `web_contract.py` contains the stable JSON surface; do not recreate a parallel `http.server` or dynamic legacy loader.
- FFmpeg/ffprobe resolve from explicit environment overrides, then `R:\peach-data\tools\ffmpeg\bin`, then `PATH`. No active code may fall back to the Stash private directory.
- Long-running inventory helpers are under `scripts/`; their scheduled tasks use `R:\peach-app\.venv\Scripts\python.exe`. They use absolute data paths and may be interrupted/restarted where their own locking contract allows it.
- Check ports 80, 8900 and 9999 before starting or switching services.
- Report verification separately: static/unit/API, desktop browser, 390×844 browser, and whether production was actually restarted.

## Architectural truth

- Ledger owns truth and behavior.
- Stash is a replaceable adapter; do not add new direct GraphQL helpers or private Stash FFmpeg paths.
- Keep FastAPI and the front end logically separate but deploy as a monolith.
- External sources and AI are supported only through explicit adapters and declared data boundaries.
- AI provider layers are not equivalent: inference APIs and local coding/agent runtimes remain separate.

## Recovery

Deprecated scripts and old dated documents were removed from the active tree during the `peach-app` restructure. They remain recoverable from Git history before the restructure commit. Former `_SHARED_STATE` content lives under `R:\peach-data\state`; it is deliberately outside version control. The pre-restructure root repository metadata is retained temporarily under `R:\peach-data\archive\peach-root-repo-backup-20260814` as a recovery copy.
