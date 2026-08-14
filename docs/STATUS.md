# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on `0.0.0.0:80`, PID observed as 54576; health mode is `fastapi`.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: not applied. `schema_migration` is absent in the real database.

Runtime PIDs are observations, not configuration; always re-check them.

## Verified code state

- FastAPI serves home, legacy-compatible JSON, standard Range/HEAD media, thumbnails, posters, avatars and logos.
- Default ledger connections in the compatibility query layer are read-only; activity/play/feedback writes are explicit.
- FFmpeg resolution is centralized: environment, Peach-managed binary, PATH, then temporary Stash fallback.
- `R:\peach-data` now separates `database/generated/sources/state/secrets/logs/archive/inbox`; the old empty root Inbox and old Resources/Tools compatibility surface are removed.
- 23 isolated tests passed under Python 3.14 after the repository and data restructure.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the candidate service.
- Production port 80 passed health, home, 2,552-item real read-only list and one-byte `206 Partial Content` Range smoke checks after the switch.

## Next work

1. Apply formal migrations to the real ledger in a maintenance window, with SQLite backup and count/integrity verification.
2. Move FFmpeg/ffprobe to a Peach-managed installation and remove the temporary Stash binary fallback.
3. Extract the remaining query/write functions from `compat_web.py`, then delete that compatibility module.
4. Implement the first real online-source and AI provider adapters behind the existing boundaries.
