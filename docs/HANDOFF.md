# Handoff

This is durable operating knowledge, not a per-session transcript.

## Zero-friction agent handoff

- Codex automatically discovers `AGENTS.md` in the project hierarchy.
- Claude Code automatically reads `CLAUDE.md`; this repository's `CLAUDE.md` imports `AGENTS.md`.
- Both agents therefore receive the same contract and the same mandatory reading order.
- Do not ask the outgoing agent to write a dated handoff. A task that changes reality must update `docs/STATUS.md`; a durable lesson changes this file or an ADR.
- Start every new task with `R:\peach-app` as the working directory and say only: “接手 Peach，按项目入口文件继续 STATUS 中的下一任务。”

## Data safety

- Real ledger: `R:\Resources\Intake\ledger.db`; WAL mode; normal browsing legitimately changes play/activity fields.
- Tests must create temporary SQLite databases and temporary media files.
- Before real migration: SQLite backup, asset/tag counts, `PRAGMA integrity_check`, migration version check, then service smoke test.
- Media and generated resources remain under `R:\Media` and `R:\Resources`; they are not repository assets.

## Operations

- Main command: `peach serve|migrate` after editable installation.
- Long-running inventory helpers are under `scripts/`; their scheduled tasks already use `R:\peach-app` for the next start. They use absolute data paths and may be interrupted/restarted where their own locking contract allows it.
- Check ports 80, 8900 and 9999 before starting or switching services.
- Report verification separately: static/unit/API, desktop browser, 390×844 browser, and whether production was actually restarted.

## Architectural truth

- Ledger owns truth and behavior.
- Stash is a replaceable adapter; do not add new direct GraphQL helpers or private Stash FFmpeg paths.
- Keep FastAPI and the front end logically separate but deploy as a monolith.
- External sources and AI are supported only through explicit adapters and declared data boundaries.
- AI provider layers are not equivalent: inference APIs and local coding/agent runtimes remain separate.

## Recovery

Deprecated scripts and old dated documents were removed from the active tree during the `peach-app` restructure. They remain recoverable from Git history before the restructure commit. Local `_SHARED_STATE` data remains in `R:\Resources\Intake\_SHARED_STATE`; it was deliberately removed only from version control.
