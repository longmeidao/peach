from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .api import create_app
from .config import DATABASE_PATH, MIGRATIONS_DIR, PeachSettings
from .migrations import plan, upgrade


DEFAULT_DB = DATABASE_PATH


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    if bool(args.ssl_certfile) != bool(args.ssl_keyfile):
        raise SystemExit("--ssl-certfile and --ssl-keyfile must be provided together")
    for path in (args.ssl_certfile, args.ssl_keyfile):
        if path is not None and not path.is_file():
            raise SystemExit(f"TLS file not found: {path}")
    tls_enabled = args.ssl_certfile is not None
    settings = PeachSettings(
        db_path=args.db,
        token=args.token,
        docs_enabled=args.docs,
        mdns_enabled=not args.no_mdns,
        mdns_name=args.mdns_name,
        mdns_port=args.port,
        tls_enabled=tls_enabled,
    )
    uvicorn.run(
        create_app(settings), host=args.host, port=args.port, workers=1,
        ssl_certfile=str(args.ssl_certfile) if args.ssl_certfile else None,
        ssl_keyfile=str(args.ssl_keyfile) if args.ssl_keyfile else None,
    )
    return 0


def _migrate(args: argparse.Namespace) -> int:
    all_migrations, pending = plan(args.db, MIGRATIONS_DIR)
    print(f"database: {args.db}")
    print(f"migrations: {len(all_migrations)}, pending: {len(pending)}")
    for migration in pending:
        print(f"PENDING {migration.version} {migration.name}")
    if args.action == "status" or not pending:
        return 0
    if args.db.resolve() == DEFAULT_DB.resolve() and not args.yes:
        raise SystemExit("refusing to modify the real ledger without --yes")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = args.db.with_name(f"{args.db.stem}.pre-migrate-{stamp}{args.db.suffix}")
    done = upgrade(args.db, MIGRATIONS_DIR, backup)
    print(f"backup: {backup}")
    print("applied: " + ", ".join(item.version for item in done))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="peach")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="run the FastAPI application")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8900)
    serve.add_argument("--db", type=Path, default=DEFAULT_DB)
    serve.add_argument("--token", default="")
    serve.add_argument("--docs", action="store_true")
    serve.add_argument("--no-mdns", action="store_true")
    serve.add_argument("--mdns-name", default="peach")
    serve.add_argument("--ssl-certfile", type=Path)
    serve.add_argument("--ssl-keyfile", type=Path)
    serve.set_defaults(handler=_serve)

    migrate = commands.add_parser("migrate", help="inspect or apply SQLite migrations")
    migrate.add_argument("action", choices=("status", "upgrade"), nargs="?", default="status")
    migrate.add_argument("--db", type=Path, default=DEFAULT_DB)
    migrate.add_argument("--yes", action="store_true")
    migrate.set_defaults(handler=_migrate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
