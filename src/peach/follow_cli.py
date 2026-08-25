"""`peach follow` 子命令：登记订阅、显式检查更新、复核与保存。

联网只发生在 `check`。`list`、`feed`、`creds` 都不发请求，`save` 也不发。
`save` 是唯一会写真相的动作，必须显式 `--confirm`。
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import DATABASE_PATH, SECRETS_DIR, SOURCES_DIR
from .follow import FollowSourceError
from .follow_secrets import CredentialError, CredentialStore
from .follow_sources import CONNECTORS, build_connector
from .follow_store import FollowStore


#: 登记订阅时按 provider 拼作品页 URL；只用于展示与去重，不参与抓取。
_SOURCE_URL = {
    "kemono": "https://kemono.cr/{ref}",
    "coomer": "https://coomer.st/{ref}",
    "pawchive": "https://pawchive.pw/{ref}",
    "rule34video": "https://rule34video.com/models/{ref}/",
    "rule34xxx": "https://rule34.xxx/index.php?page=post&s=list&tags={ref}",
    "f95zone": "https://f95zone.to/threads/{ref}/",
    "simpcity": "https://simpcity.cr/threads/{ref}/",
}

#: 这些来源的每个条目是同一作品的一次发布，不是独立作品。
_RELEASE_PROVIDERS = frozenset({"f95zone", "simpcity"})


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _store(args) -> tuple[FollowStore, sqlite3.Connection]:
    connection = _connect(args.db)
    return FollowStore(lambda: connection, sources_root=args.sources_root), connection


def _add(args) -> int:
    store, connection = _store(args)
    provider = args.provider
    if provider not in CONNECTORS:
        raise SystemExit(f"未知的追更来源：{provider}；可选 {', '.join(sorted(CONNECTORS))}")
    semantics = args.semantics or (
        "release" if provider in _RELEASE_PROVIDERS else "work")
    url = args.url or _SOURCE_URL[provider].format(ref=args.ref)
    try:
        source_id = store.register(
            provider=provider, ref=args.ref, label=args.label or args.ref, url=url,
            semantics=semantics, entity_id=args.entity)
        connection.commit()
    finally:
        connection.close()
    print(f"已登记 #{source_id} {provider}/{args.ref} · {semantics} · {url}")
    return 0


def _list(args) -> int:
    store, connection = _store(args)
    try:
        rows = store.sources()
    finally:
        connection.close()
    if not rows:
        print("还没有登记任何追更来源。用 `peach follow add` 添加。")
        return 0
    for row in rows:
        flag = " " if row["enabled"] else "×"
        entity = f" → {row['entity_name']}" if row["entity_name"] else ""
        status = row["last_status"] or "未检查"
        checked = row["last_checked_at"] or "—"
        print(f"{flag} #{row['id']:<4} {row['provider']:<12} {row['ref']:<28}"
              f" {status:<14} {checked}{entity}")
        if row["last_error"]:
            print(f"      错误：{row['last_error']}")
    return 0


def _check(args) -> int:
    store, connection = _store(args)
    credentials = CredentialStore(args.secrets_root)
    failures = 0
    try:
        rows = [row for row in store.sources(enabled_only=True)
                if args.source is None or row["id"] == args.source]
        if not rows:
            print("没有需要检查的来源。")
            return 0
        for row in rows:
            moment = datetime.now(timezone.utc)
            provider, ref = row["provider"], row["ref"]
            try:
                credential = credentials.load(provider)
                connector = build_connector(provider, credential=credential)
                fetch = connector.fetch(
                    ref,
                    etag=None if args.force else row["etag"],
                    last_modified=None if args.force else row["last_modified"])
            except CredentialError as error:
                store.record_error(row["id"], str(error), moment, status="unauthorized")
                connection.commit()
                print(f"! {provider}/{ref}：{error}")
                failures += 1
                continue
            except FollowSourceError as error:
                store.record_error(row["id"], str(error), moment)
                connection.commit()
                print(f"! {provider}/{ref}：{error}")
                failures += 1
                continue
            outcome = store.record(
                row["id"], fetch,
                creator_aliases=store.creator_aliases(row["entity_id"]), moment=moment)
            connection.commit()
            if outcome.not_modified:
                print(f"= {provider}/{ref}：无变化")
            else:
                print(f"+ {provider}/{ref}：发现 {outcome.discovered}，"
                      f"新增 {outcome.added}，更新 {outcome.updated}")
    finally:
        connection.close()
    return 1 if failures else 0


def _feed(args) -> int:
    store, connection = _store(args)
    try:
        statuses = tuple(args.status) if args.status else ()
        groups = store.group(store.items(statuses=statuses, limit=args.limit))
    finally:
        connection.close()
    if not groups:
        print("没有符合条件的追更条目。")
        return 0
    for group in groups:
        primary = group.primary
        when = primary.published_at or primary.first_seen_at
        if primary.published_precision == "approximate":
            when = f"约 {when}"
        badges = []
        if group.has_wip:
            badges.append("WIP")
        if group.variants:
            # 线程的多条回复是动态，不是版本；说成「版本」会把追更判断带偏。
            noun = "条动态" if group.is_release else "个版本"
            badges.append(f"{len(group.variants) + 1} {noun}"
                          if group.is_release else f"{len(group.variants)} {noun}")
        if group.duplicates:
            badges.append(f"另见 {', '.join(d.provider for d in group.duplicates)}")
        if primary.version:
            badges.append(f"版本 {primary.version}")
        suffix = f"  [{' · '.join(badges)}]" if badges else ""
        print(f"#{primary.id:<5} {primary.status:<8} {when[:19]:<22} {primary.title}{suffix}")
        if args.verbose:
            for variant in group.variants:
                print(f"        └ {variant.variant_kind}/{variant.variant_label}"
                      f" #{variant.id} {variant.title}")
            for duplicate in group.duplicates:
                print(f"        ≡ {duplicate.provider} #{duplicate.id} {duplicate.title}")
    return 0


def _status(args) -> int:
    store, connection = _store(args)
    try:
        for item_id in args.item:
            store.set_status(item_id, args.to)
        connection.commit()
    finally:
        connection.close()
    print(f"已把 {len(args.item)} 条标记为 {args.to}")
    return 0


def _save(args) -> int:
    if not args.confirm:
        raise SystemExit("写 ledger 需要 --confirm；先用 `peach follow feed` 复核。")
    store, connection = _store(args)
    saved = []
    try:
        for item_id in args.item:
            saved.append((item_id, store.save_asset(item_id, confirm=True)))
        connection.commit()
    finally:
        connection.close()
    for item_id, asset_id in saved:
        print(f"追更条目 #{item_id} → asset #{asset_id}")
    return 0


def _creds(args) -> int:
    store = CredentialStore(args.secrets_root)
    for provider in sorted(CONNECTORS):
        described = store.describe(provider)
        state = "已配置" if described["present"] else "未配置"
        fields = ", ".join(described["fields"]) or "—"
        warning = "  ⚠ 权限过宽" if described["world_readable"] else ""
        print(f"{provider:<12} {state:<8} 字段：{fields}{warning}")
    print(f"\n凭据目录：{store.root}")
    print("rule34xxx 需要 user_id + api_key；f95zone 与 simpcity 的 cookie 只在"
          "读登录后内容时需要。凭据只留在本机，不进 Git、URL、日志或 ledger。")
    return 0


def register(commands) -> None:
    follow = commands.add_parser("follow", help="在线追更：登记、检查、复核与保存")
    follow.add_argument("--db", type=Path, default=DATABASE_PATH)
    follow.add_argument("--sources-root", type=Path, default=SOURCES_DIR)
    follow.add_argument("--secrets-root", type=Path, default=SECRETS_DIR)
    actions = follow.add_subparsers(dest="follow_command", required=True)

    add = actions.add_parser("add", help="登记一个追更来源")
    add.add_argument("--provider", required=True, choices=sorted(CONNECTORS))
    add.add_argument("--ref", required=True,
                     help="来源内的引用：kemono 系用 `service/user_id`，"
                          "rule34video 用作者 slug，rule34xxx 用标签，f95zone 用线程 id")
    add.add_argument("--label", help="界面上显示的名字，默认用 ref")
    add.add_argument("--url", help="资料页 URL，默认按 provider 推导")
    add.add_argument("--entity", type=int, help="关联的 creator entity id")
    add.add_argument("--semantics", choices=("work", "release"))
    add.set_defaults(handler=_add)

    listing = actions.add_parser("list", help="列出已登记的来源（不联网）")
    listing.set_defaults(handler=_list)

    check = actions.add_parser("check", help="显式检查更新（唯一会联网的动作）")
    check.add_argument("--source", type=int, help="只检查这一个来源 id")
    check.add_argument("--force", action="store_true", help="忽略条件请求游标")
    check.set_defaults(handler=_check)

    feed = actions.add_parser("feed", help="按作品分组显示追更结果（不联网）")
    feed.add_argument("--status", action="append",
                      choices=("new", "seen", "saved", "ignored"))
    feed.add_argument("--limit", type=int, default=200)
    feed.add_argument("--verbose", action="store_true", help="展开变体与跨站重复项")
    feed.set_defaults(handler=_feed)

    status = actions.add_parser("status", help="标记条目为已看或忽略")
    status.add_argument("item", type=int, nargs="+")
    status.add_argument("--to", required=True, choices=("new", "seen", "ignored"))
    status.set_defaults(handler=_status)

    save = actions.add_parser("save", help="把候选保存成 online asset（写 ledger）")
    save.add_argument("item", type=int, nargs="+")
    save.add_argument("--confirm", action="store_true")
    save.set_defaults(handler=_save)

    creds = actions.add_parser("creds", help="报告本机凭据配置状态（不显示凭据值）")
    creds.set_defaults(handler=_creds)
