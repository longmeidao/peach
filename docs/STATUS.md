# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: legacy server on `0.0.0.0:80`, PID observed as 37392. It has not been switched to the new project yet.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: the current instance still runs from the old tools directory; its scheduled task now points to `R:\peach-app` for the next start.
- FastAPI candidate: implemented and verified on temporary `127.0.0.1:8900`, then stopped.
- Real ledger migrations: not applied. `schema_migration` is absent in the real database.

Runtime PIDs are observations, not configuration; always re-check them.

## Verified code state

- FastAPI serves home, legacy-compatible JSON, standard Range/HEAD media, thumbnails, posters, avatars and logos.
- Default ledger connections in the compatibility query layer are read-only; activity/play/feedback writes are explicit.
- FFmpeg resolution is centralized: environment, Peach-managed binary, PATH, then temporary Stash fallback.
- 23 isolated tests passed again after the repository restructure.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the candidate service.
- The restructured candidate passed health, home, real read-only list and one-byte Range smoke checks on temporary port 8900; it was then stopped.

## Next work

1. Perform a controlled production switch from the old server on port 80 to `peach serve --host 0.0.0.0 --port 80`, with immediate rollback available.
2. Apply formal migrations to the real ledger only in that maintenance window, with SQLite backup and count/integrity verification.
3. Restart the traffic monitor at a safe accounting boundary so its running instance also uses the new path.
4. Remove the final old Web/traffic-monitor compatibility files after no process depends on them.
