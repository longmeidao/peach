from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

from . import certs, settings_file
from .api import create_app
from .config import (
    DATABASE_PATH,
    MDNS_NAME,
    MIGRATIONS_DIR,
    REPLICATION_ENABLED,
    SERVE_HOST,
    SERVE_PORT,
    SETTINGS_ERROR,
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


def _require_readable_settings() -> None:
    """设置文件在但读不出来时，明确拒绝。

    这种情况下 `config` 里那份是退回的内建默认——数据根仍然对（发现顺序不看文件内容），
    但端口、mDNS 名、复制坐标全是通用值。拿它启动会得到一个「看起来正常」的服务，
    比直接失败难查得多。
    """
    if SETTINGS_ERROR is not None:
        raise SystemExit(
            f"{SETTINGS_ERROR}\n修好这个文件，或者用 `peach init --force` 重新生成。")


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    _require_readable_settings()
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

    `replication.enabled = false` 时整条链路不装配：不建观察器、不探测共享目录。
    没有第二台机器就没有「读者」可言，服务按独立写者跑——写接口全开，只读闸门不生效
    （`sync is None` 时 `/healthz` 的 `ledger_sync` 是 `disabled`，不是 `writer`）。
    """
    if not REPLICATION_ENABLED:
        print("账本角色：disabled · replication.enabled = false，按独立写者运行")
        return None
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
    _require_readable_settings()
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
    _require_readable_settings()
    if not args.db.is_file():
        print(f"账本不存在：{args.db}")
        if not args.db.parent.is_dir():
            print("这台机器还没初始化过，先跑 `peach init`。")
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


def _parse_mounts(
    raw: list[str] | None, locations: dict[str, str] | None = None,
) -> dict[str, str]:
    """`--mount local=/Volumes/RESOURCES/media` 形式的挂载点。

    键是 `asset.location`（`[media.locations]` 里声明过的来源 ID），不是盘符：
    打错一个 ID 如果静默收下，那个来源就会安静地进脱盘模式，所以这里直接拒绝。
    """
    known = dict(locations or {})
    mounts: dict[str, str] = {}
    for chunk in raw or ():
        key, separator, value = chunk.partition("=")
        key = key.strip()
        if not separator or not key:
            raise SystemExit(f"--mount 要写成 来源ID=路径，收到：{chunk}")
        if known and key not in known:
            raise SystemExit(
                f"--mount 的来源 ID 未在 [media.locations] 声明：{key}"
                f"（已知：{'、'.join(sorted(known))}）"
            )
        mounts[key] = value.strip()
    return mounts


def _resolved_config(
    data_root: Path | None,
) -> tuple[settings_file.PeachConfig, settings_file.SettingsFileError | None]:
    """按当前环境解析一份配置，外加「旧文件读不出来」时的原始错误。

    `--data-root` 走和运行期同一条发现路径，不另开分支。读取用 `strict=False`
    （`init --force` 是坏文件的唯一自救入口），但错误必须留下来：静默退回内建默认
    再写回去，等于把旧文件里的坐标悄悄抹平。
    """
    environ = None if data_root is None else dict(
        os.environ, PEACH_DATA_ROOT=str(data_root))
    kwargs = {} if environ is None else {"environ": environ}
    try:
        return settings_file.load_config(**kwargs), None
    except settings_file.SettingsFileError as exc:
        return settings_file.load_config(**kwargs, strict=False), exc


def _init(args: argparse.Namespace) -> int:
    """首次运行：建目录、建库、写设置文件、生成本机 CA。

    `--from-existing` 是给已经在跑的机器用的另一条路径：不建目录、不建库、不生成
    证书，只把当前生效的配置落成设置文件。现有部署的坐标散在环境变量和运行现场里，
    进程看不见的那几项（局域网地址、钥匙串账号名）由命令行显式补，落不下的会在末尾
    逐条列出来，绝不拿猜的值填。
    """
    config, broken = _resolved_config(args.data_root)
    if config.path.exists() and not args.force:
        print(f"设置文件已存在：{config.path}")
        print("要重新生成就加 --force；它会覆盖这个文件，不动数据。")
        return 3
    if broken is not None:
        # 第一阶段的 `[media] R = ...` 在第二阶段是硬错误，于是 `--from-existing` 读到的
        # 「当前生效配置」其实是内建默认。不说这一句，重写出来的文件会安静地丢掉旧文件
        # 里的 mDNS 名、writer 地址和 SMB 坐标——那正是这条命令声称要保下来的东西。
        print(f"注意：{broken}")
        print("下面这份是按内建默认加环境变量重建的，**没有**继承旧文件里的值。")
        print("旧文件里自定义过的坐标要在这次命令里用对应参数重新给一遍。")

    overrides: dict[str, object] = {
        "host": args.host, "port": args.port, "mdns_name": args.mdns_name,
        "review_writer_origin": args.writer_origin,
        "review_writer_proxy": args.writer_proxy,
        "shared_root": str(args.shared_root) if args.shared_root else None,
        "smb_host": args.smb_host, "smb_share": args.smb_share,
        "smb_user": args.smb_user,
    }
    mounts = dict(config.mounts)
    mounts.update(_parse_mounts(args.mount, config.locations))
    prepared = settings_file.capture_existing(
        config, replication_enabled=args.from_existing,
        overrides=overrides, mounts=mounts,
    )

    if not args.from_existing:
        _create_data_tree(prepared)
    path = settings_file.write(prepared, force=args.force)
    print(f"设置文件：{path}")
    _report_blanks(prepared)
    _print_next_steps(prepared, from_existing=args.from_existing)
    return 0


def _create_data_tree(config: settings_file.PeachConfig) -> None:
    """建目录、把库迁到最新、生成本机 CA。已经有账本就不碰它。"""
    for key in settings_file.DIRECTORY_KEYS:
        config.directory(key).mkdir(parents=True, exist_ok=True)
    tls_dir = config.directory("secrets") / "tls"
    tls_dir.mkdir(parents=True, exist_ok=True)
    print(f"数据根：{config.data_root}")

    database = config.directory("database") / "ledger.db"
    if database.is_file():
        # 已有账本却在跑全新 init：不迁移、不备份、不覆盖，让人自己决定。
        print(f"账本已存在，跳过建库：{database}")
        print("要为现有部署生成设置文件，用 `peach init --from-existing`。")
    else:
        done = upgrade(database, MIGRATIONS_DIR)
        print(f"账本：{database}（已应用 {len(done)} 个迁移）")

    try:
        files = certs.bootstrap_certificates(tls_dir, config.server.mdns_name + ".local")
        print(f"本机 CA：{files.ca_cert}")
    except (RuntimeError, OSError) as exc:
        # 没有 openssl 不该挡住初始化：HTTP 本地访问照样能用，装 openssl 后重跑即可。
        print(f"未生成本机 CA（{exc}）。装好 openssl 后重跑 `peach init --force` 补上。")


#: 留空就会改变行为的坐标。进程猜不出来，只能让人在命令行给。
_BLANK_HINTS = (
    ("server.review_writer_origin", "--writer-origin https://<writer 的地址>",
     "reader 不做复核镜像"),
    ("replication.smb_host", "--smb-host <writer 的主机名>", "不挂载共享传输点"),
    ("replication.smb_user", "--smb-user <钥匙串里的账号>", "不挂载共享传输点"),
)


def _report_blanks(config: settings_file.PeachConfig) -> None:
    blanks = []
    for dotted, flag, effect in _BLANK_HINTS:
        table, _, name = dotted.partition(".")
        if not getattr(getattr(config, table), name):
            blanks.append(f"  {dotted} 留空 → {effect}；要填就重跑并加 {flag}")
    if not config.mounts and os.name != "nt":
        # Windows 上盘符本身就是挂载点，空表是正常的，提示它只会让人去填没用的值。
        known = "、".join(sorted(config.locations)) or "local"
        blanks.append(
            f"  [media.mounts] 为空 → 所有来源按脱盘处理；"
            f"要填就加 --mount <来源ID>=<挂载点>（已知来源：{known}）"
        )
    if blanks:
        print("以下坐标是空的（这不是错误，单机部署本来就该空）：")
        print("\n".join(blanks))


def _print_next_steps(config: settings_file.PeachConfig, *, from_existing: bool) -> None:
    print("\n下一步：")
    if from_existing:
        print("  1. 打开上面那个文件核对一遍，尤其是 [media.mounts] 和 [replication]。")
        print("  2. 重启服务让它生效。这一步之前，运行行为和现在完全一样。")
        return
    print(f"  1. peach serve --host {config.server.host} --port {config.server.port}")
    print("  2. 浏览器打开 http://127.0.0.1:%d/ 确认页面可用。" % config.server.port)
    print("  3. 要在局域网访问就改 --host 0.0.0.0，并把本机 CA 装进各设备的信任列表。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="peach")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="首次运行：建数据目录、建库、写设置文件")
    init.add_argument("--data-root", type=Path, help="数据根；默认沿用当前发现结果")
    init.add_argument("--from-existing", action="store_true",
                      help="只为已在运行的部署生成设置文件，不建目录、不建库")
    init.add_argument("--force", action="store_true", help="覆盖已存在的设置文件")
    init.add_argument("--host", help="服务监听地址")
    init.add_argument("--port", type=int, help="服务端口")
    init.add_argument("--mdns-name", help="本机在局域网发布的名字（<name>.local）")
    init.add_argument("--writer-origin", help="reader 复核镜像要读的 writer 源")
    init.add_argument("--writer-proxy", help="只对 writer 源生效的 HTTP 代理")
    init.add_argument("--shared-root", type=Path, help="ledger 复制的共享传输点")
    init.add_argument("--smb-host", help="共享传输点所在主机")
    init.add_argument("--smb-share", help="共享名")
    init.add_argument("--smb-user", help="挂载共享用的账号")
    init.add_argument("--mount", action="append", metavar="来源ID=路径",
                      help="来源（asset.location）的声明根在本机的落点，可重复")
    init.set_defaults(handler=_init)

    serve = commands.add_parser("serve", help="run the FastAPI application")
    serve.add_argument("--host", default=SERVE_HOST)
    serve.add_argument("--port", type=int, default=SERVE_PORT)
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
