from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .api import create_app
from .config import (
    DATABASE_PATH,
    MDNS_NAME,
    MIGRATIONS_DIR,
    SHARED_DATABASE_PATH,
    STATE_DIR,
    PeachSettings,
)
from .follow_cli import register as register_follow
from .migrations import plan, upgrade
from .scripting import open_readonly
from .sync import LedgerSync, device_id
from .sync import plan as sync_plan
from .sync import writer_device


DEFAULT_DB = DATABASE_PATH

#: 只监听这些地址时，服务在局域网上不可达。
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def _is_loopback(host: str) -> bool:
    return (host or "").strip().lower() in _LOOPBACK_HOSTS


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    if bool(args.ssl_certfile) != bool(args.ssl_keyfile):
        raise SystemExit("--ssl-certfile and --ssl-keyfile must be provided together")
    for path in (args.ssl_certfile, args.ssl_keyfile):
        if path is not None and not path.is_file():
            raise SystemExit(f"TLS file not found: {path}")
    tls_enabled = args.ssl_certfile is not None
    # 绑在回环上就不能发布 mDNS：广播出去的是本机的局域网地址，而那个地址上没有
    # 任何东西在监听，`peach.local` 于是变成一个必然连不上的名字。更糟的是开发机
    # 会就此抢占生产用的 `peach.local`，把同一局域网里的真实实例挤掉。
    publish_mdns = not args.no_mdns and not _is_loopback(args.host)
    if not args.no_mdns and not publish_mdns:
        print(
            f"mDNS 未发布：--host {args.host} 只监听回环，"
            f"发布 peach.local 会指向一个连不上的地址。"
            f"需要局域网访问就用 --host 0.0.0.0。"
        )
    settings = PeachSettings(
        db_path=args.db,
        token=args.token,
        docs_enabled=args.docs,
        mdns_enabled=publish_mdns,
        mdns_name=args.mdns_name,
        mdns_port=args.port,
        mdns_address=args.mdns_address,
        tls_enabled=tls_enabled,
    )
    sync = _build_sync(args, settings)
    uvicorn.run(
        create_app(settings, sync), host=args.host, port=args.port, workers=1,
        ssl_certfile=str(args.ssl_certfile) if args.ssl_certfile else None,
        ssl_keyfile=str(args.ssl_keyfile) if args.ssl_keyfile else None,
    )
    return 0


def _build_sync(args: argparse.Namespace, settings: PeachSettings) -> LedgerSync | None:
    """建立只读角色观察器；服务启动与浏览绝不触发跨机复制。

    冲突不自动挑边：两台机器都写过之后没有安全的合并规则，服务照常起但转只读，
    由人选一边（把要保留的那份复制成另一份，或删掉一侧的 `.sync.json` 重新播种）。
    """
    sync = LedgerSync(
        settings.db_path, args.shared_db, device_id(STATE_DIR),
        interval=0,
    )
    decision = sync.observe()
    print(f"账本角色：{sync.status} · {sync.detail}")
    if decision.conflict:
        print(
            "  服务转只读。请人工选定一份账本："
            f"本地 {settings.db_path}，共享 {args.shared_db}。"
        )
    return sync

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


#: 「加工进度」的分母：能落到本机的视频。在线资产没有文件，探测和接触表对它们
#: 不适用，混进分母只会让每一行的百分比永远到不了 100。
_PROCESSED_SCOPE = "medium='video' AND location!='online'"
_PROCESSED_MEASURES = (
    ("有时长 (ffprobe)", "duration IS NOT NULL"),
    ("有接触表", "snapshot_path IS NOT NULL"),
    ("有哈希", "hash IS NOT NULL"),
    ("有创作者归属", "creator IS NOT NULL AND creator!=''"),
    ("有消费记录", "play_count>0 OR rating IS NOT NULL"),
)


def _status(args: argparse.Namespace) -> int:
    """一屏看完账本、迁移和同步状态。只读，随时可跑。

    这里刻意不报后台任务：进程名和日志 mtime 都不是存活判据（长跑批处理各自持有
    pid 锁与进度文件），`scripts/job_status.py` 才是那件事的正式表面。
    """
    if not args.db.is_file():
        print(f"账本不存在：{args.db}")
        return 4
    connection = open_readonly(args.db)
    try:
        one = lambda sql: connection.execute(sql).fetchone()[0]      # noqa: E731
        print(f"账本 {args.db}")
        for location, count, size in connection.execute(
                "SELECT location,COUNT(*),COALESCE(SUM(size),0) FROM asset "
                "GROUP BY 1 ORDER BY 3 DESC"):
            print(f"  {location or '?':<10}{count:>9,} 条{size / 1024 ** 4:>10.2f} TB")
        print(f"  {'合计':<10}{one('SELECT COUNT(*) FROM asset'):>9,} 条"
              f"{one('SELECT COALESCE(SUM(size),0) FROM asset') / 1024 ** 4:>10.2f} TB")

        print("\n  媒介构成：")
        for medium, count, size in connection.execute(
                "SELECT medium,COUNT(*),COALESCE(SUM(size),0) FROM asset "
                "GROUP BY 1 ORDER BY 2 DESC"):
            print(f"    {medium or '?':<14}{count:>8,}{size / 1024 ** 3:>11.1f} GB")

        total = one(f"SELECT COUNT(*) FROM asset WHERE {_PROCESSED_SCOPE}")
        print(f"\n  加工进度（本机视频 {total:,} 条）：")
        for label, condition in _PROCESSED_MEASURES:
            done = one(f"SELECT COUNT(*) FROM asset WHERE {_PROCESSED_SCOPE} "
                       f"AND ({condition})")
            percent = done / total * 100 if total else 0.0
            print(f"    {label:<18}{done:>8,} / {total:,}  {percent:5.1f}%  "
                  f"{'█' * int(percent / 4)}")

        print("\n  情境层：")
        for column, label in (("ctx_length", "时长档"), ("ctx_orient", "屏向"),
                              ("ctx_quality", "画质")):
            rows = connection.execute(
                f"SELECT {column},COUNT(*) FROM asset WHERE {column} IS NOT NULL "
                "GROUP BY 1 ORDER BY 2 DESC").fetchall()
            if rows:
                print(f"    {label:<8}"
                      + "  ".join(f"{key}={value:,}" for key, value in rows))
    finally:
        connection.close()

    all_migrations, pending = plan(args.db, MIGRATIONS_DIR)
    print(f"\n  迁移：共 {len(all_migrations)} 个，待应用 {len(pending)} 个")
    for migration in pending:
        print(f"    PENDING {migration.version} {migration.name}")

    decision = sync_plan(args.db, args.shared_db)
    owner = writer_device(args.db, args.shared_db)
    # 只读取已有的 device-id，不像 `device_id()` 那样在缺失时顺手生成一个：
    # 状态命令生成标识会让「这一代是谁写的」多出一个从没写过库的名字。
    local_device = ""
    try:
        local_device = (STATE_DIR / "device-id").read_text(encoding="utf-8").strip()
    except OSError:
        pass
    whose = "本机" if owner and owner == local_device else (owner or "未确定")
    print(f"  同步：{decision.action} · {decision.reason}；写入端 {whose}")
    return 0


def _ledger_sync(args: argparse.Namespace) -> int:
    sync = LedgerSync(args.db, args.shared_db, device_id(STATE_DIR), interval=0)
    decision = sync.take_ownership() if args.take_ownership else sync.synchronize_now()
    completed = {
        "pull": "已从共享副本拉取",
        "push": "已推送到共享副本",
        "local-ahead": "已推送到共享副本",
        "in-sync": "两侧已经一致",
        "take-ownership": "本机已成为唯一写入端",
        "disabled": decision.reason,
    }
    print(f"账本同步：{decision.action} · {completed.get(decision.action, decision.reason)}")
    return {"conflict": 2, "offline": 3, "missing": 4}.get(decision.action, 0)


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
    serve.add_argument("--shared-db", type=Path, default=SHARED_DATABASE_PATH)
    serve.add_argument("--no-ledger-sync", action="store_true")
    serve.add_argument("--ledger-sync-seconds", type=float, default=0.0,
                       help=argparse.SUPPRESS)
    serve.add_argument("--mdns-name", default=MDNS_NAME)
    serve.add_argument("--mdns-address", help="explicit LAN IPv4 to publish")
    serve.add_argument("--ssl-certfile", type=Path)
    serve.add_argument("--ssl-keyfile", type=Path)
    serve.set_defaults(handler=_serve)

    migrate = commands.add_parser("migrate", help="inspect or apply SQLite migrations")
    migrate.add_argument("action", choices=("status", "upgrade"), nargs="?", default="status")
    migrate.add_argument("--db", type=Path, default=DEFAULT_DB)
    migrate.add_argument("--yes", action="store_true")
    migrate.set_defaults(handler=_migrate)

    status = commands.add_parser("status", help="read-only ledger, migration and sync state")
    status.add_argument("--db", type=Path, default=DEFAULT_DB)
    status.add_argument("--shared-db", type=Path, default=SHARED_DATABASE_PATH)
    status.set_defaults(handler=_status)

    ledger_sync = commands.add_parser("ledger-sync", help="synchronize the local ledger now")
    ledger_sync.add_argument("--db", type=Path, default=DEFAULT_DB)
    ledger_sync.add_argument("--shared-db", type=Path, default=SHARED_DATABASE_PATH)
    ledger_sync.add_argument("--take-ownership", action="store_true",
                             help="claim the single-writer role after both copies are in sync")
    ledger_sync.set_defaults(handler=_ledger_sync)

    register_follow(commands)
    return parser


def subcommands() -> frozenset[str]:
    """`peach` 现有的子命令名。

    打包入口靠它决定「第一个参数是子命令还是托盘参数」。这个集合必须从 parser 现算，
    不能在别处抄一份常量：抄过一次，结果是 `follow` 和 `ledger-sync` 在 EXE 里一直
    不可达，而且不报错——参数被当成托盘参数吞掉了。

    `_subparsers` 是 argparse 私有属性，argparse 没有公开的「列出子命令」接口；私有
    访问只留在这一处。
    """
    names: set[str] = set()
    container = build_parser()._subparsers
    for action in getattr(container, "_group_actions", ()):
        names.update(getattr(action, "choices", ()) or ())
    return frozenset(names)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
