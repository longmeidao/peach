# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on `0.0.0.0:80`, PID observed as 46796; health mode is `fastapi`.
- mDNS publisher: `peach.local` is published on `192.168.50.162` as HTTP, but an actual LAN client could not resolve it. Use `http://192.168.50.162/` until the client/router multicast path is fixed; no firewall/router change was made.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: `0000` and `0001` applied. Code migration `0002_canonical_entities` is tested but deliberately pending on the real ledger until a fresh backup/maintenance window.
- Pre-migration backup: `R:\peach-data\archive\ledger.pre-migrate-20260814-152821.db`.

Runtime PIDs are observations, not configuration; always re-check them.

## Verified code state

- FastAPI serves home, stable JSON contract, standard Range/HEAD media, thumbnails, posters, avatars and logos.
- The old `BaseHTTPRequestHandler`, dynamic legacy loader and automatic schema repair path are deleted. Default contract reads are read-only; activity/play/feedback writes are explicit.
- FFmpeg/ffprobe are Peach-managed under `R:\peach-data\tools\ffmpeg`; resolver order is environment, managed bundle, then PATH. Active code has no Stash private binary fallback.
- Stash transport is centralized in `StashClient`; ledger imports now write stable `media_binding` external IDs and explicit tag/performer provenance. The new importer was verified only against an isolated database and was not run on the real ledger.
- Migration `0002` adds canonical entity/alias/external-ref/asset-relation tables and backfills existing performer/tag/studio/creator projections. The Stash importer dual-writes canonical relations while retaining current flattened tags for UI compatibility; isolated tests only.
- Passive `/api/providers` health discovery now exposes separate inference/agent capabilities without model calls, credential reads or secret values.
- Snapshot rows still contain 10,714 pre-split `R:\Resources\Intake\snapshots` paths. Runtime now performs a strict legacy-prefix rebase to `R:\peach-data\generated\snapshots`; it does not mutate the real ledger.
- `R:\peach-data` now separates `database/generated/sources/state/secrets/logs/archive/inbox/tools`; the old empty root Inbox and old Resources/Tools compatibility surface are removed.
- 29 isolated tests passed under Python 3.14, including canonical migration/import, provider registry, snapshot rebasing, HTTP/HTTPS mDNS publication and TLS argument boundaries.
- Real migration preserved 81,873 assets and 59,697 tag links; both live database and backup passed `integrity_check` and `foreign_key_check`.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the same application candidate before the schema-only migration; visual checks were not rerun after migration because no browser instance was connected.
- Restarted production port 80 passed health, home, 24,980-item all-source list, 2,552-item local list and one-byte `206 Partial Content` Range smoke checks.
- After deleting the legacy server, restarted production also passed real `stats`, `tops` and `facets` aggregate contract checks.
- Optional SSL is supported with an explicit certificate/key pair. Production remains HTTP until a trusted local certificate is supplied.
- The original Peach process could not see CloudDrive `A:`/`B:` even though CloudDrive was running. After confirming zero copy tasks and no I/O, CloudDrive and Peach were restarted in the same execution context. Asset 4289 (`669.mp4`) then passed `video/mp4`, 1 KiB `206 Range`, thumbnail and generated-poster API checks. Drive-letter visibility differs by Windows token, so the HTTP stream check is the authoritative service test.

## Next work

1. Back up the real ledger, apply `0002`, verify counts/integrity, then restart and smoke-test production.
2. Split `web_contract.py` globals into explicit repository/application objects before enabling multiple workers.
3. Implement the first real online-source and AI provider adapters behind the existing boundaries.
