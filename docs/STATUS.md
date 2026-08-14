# Status

Last verified: 2026-08-14

## Runtime

- Production Peach: FastAPI `0.2.0` from `R:\peach-app` on `0.0.0.0:80`, PID observed as 57976; health mode is `fastapi`.
- mDNS publisher: `peach.local` registered on `192.168.50.162` as HTTP. Same-host Windows discovery does not loop back reliably; confirmation from another LAN device remains required.
- Stash: `127.0.0.1:9999`, PID observed as 35332.
- Traffic monitor: running through `RM-TrafficWatch` from `R:\peach-app\.venv`; all probe/sheets tasks use the same project environment.
- Runtime Python: 3.14.7. The removed system Python 3.12 invalidated the old venv, which was rebuilt and reverified before production start.
- Real ledger migrations: `0000` and `0001` applied; `peach migrate status` reports zero pending migrations.
- Pre-migration backup: `R:\peach-data\archive\ledger.pre-migrate-20260814-152821.db`.

Runtime PIDs are observations, not configuration; always re-check them.

## Verified code state

- FastAPI serves home, stable JSON contract, standard Range/HEAD media, thumbnails, posters, avatars and logos.
- The old `BaseHTTPRequestHandler`, dynamic legacy loader and automatic schema repair path are deleted. Default contract reads are read-only; activity/play/feedback writes are explicit.
- FFmpeg/ffprobe are Peach-managed under `R:\peach-data\tools\ffmpeg`; resolver order is environment, managed bundle, then PATH. Active code has no Stash private binary fallback.
- `R:\peach-data` now separates `database/generated/sources/state/secrets/logs/archive/inbox/tools`; the old empty root Inbox and old Resources/Tools compatibility surface are removed.
- 24 isolated tests passed under Python 3.14, including HTTP/HTTPS mDNS publication and TLS argument boundaries.
- Real migration preserved 81,873 assets and 59,697 tag links; both live database and backup passed `integrity_check` and `foreign_key_check`.
- Desktop 1280×720 and mobile 390×844 browser checks passed on the same application candidate before the schema-only migration; visual checks were not rerun after migration because no browser instance was connected.
- Restarted production port 80 passed health, home, 24,980-item all-source list, 2,552-item local list and one-byte `206 Partial Content` Range smoke checks.
- After deleting the legacy server, restarted production also passed real `stats`, `tops` and `facets` aggregate contract checks.
- Optional SSL is supported with an explicit certificate/key pair. Production remains HTTP until a trusted local certificate is supplied.

## Next work

1. Route the remaining `scripts/ledger.py` Stash import through the centralized adapter and formalize entity provenance.
2. Split `web_contract.py` globals into explicit repository/application objects before enabling multiple workers.
3. Implement the first real online-source and AI provider adapters behind the existing boundaries.
