# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on `0.0.0.0:80`, PID observed as 58508; health mode is `fastapi`.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: `0000` and `0001` applied; `peach migrate status` reports zero pending migrations.
- Pre-migration backup: `R:\peach-data\archive\ledger.pre-migrate-20260814-152821.db`.

Runtime PIDs are observations, not configuration; always re-check them.

## Verified code state

- FastAPI serves home, legacy-compatible JSON, standard Range/HEAD media, thumbnails, posters, avatars and logos.
- Default ledger connections in the compatibility query layer are read-only; activity/play/feedback writes are explicit.
- FFmpeg/ffprobe are Peach-managed under `R:\peach-data\tools\ffmpeg`; resolver order is environment, managed bundle, then PATH. Active code has no Stash private binary fallback.
- `R:\peach-data` now separates `database/generated/sources/state/secrets/logs/archive/inbox/tools`; the old empty root Inbox and old Resources/Tools compatibility surface are removed.
- 24 isolated tests passed under Python 3.14 after the real migration and FFmpeg decoupling.
- Real migration preserved 81,873 assets and 59,697 tag links; both live database and backup passed `integrity_check` and `foreign_key_check`.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the same application candidate before the schema-only migration; visual checks were not rerun after migration because no browser instance was connected.
- Restarted production port 80 passed health, home, 24,980-item all-source list, 2,552-item local list and one-byte `206 Partial Content` Range smoke checks.

## Next work

1. Extract the remaining query/write functions from `compat_web.py`, then delete that compatibility module.
2. Route the remaining `scripts/ledger.py` Stash import through the centralized adapter and formalize entity provenance.
3. Implement the first real online-source and AI provider adapters behind the existing boundaries.
