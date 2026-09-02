"""追更订阅与候选条目的 ledger 边界。

这一层只负责登记与候选：`follow_item` 的 `status` 停在 `new`/`seen` 时，不影响任何
asset、标签或反馈。只有 `save_asset()` 会写出真相，而它要求显式 `confirm=True`，
并且只 INSERT 一条 `location='online'` 的新 asset，绝不改写既有真相字段。

原始响应按来源存进 `peach-data/sources/follow/`，一次写死；条件请求游标存在
`follow_source` 行上，因为它可替换、且要参与界面查询。
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .follow import FollowSourceError, write_immutable
from .follow_sources import FollowCandidate, SourceFetch, canonical_source_ref
from .follow_variants import classify, group_duplicates


def _now_text(moment: datetime | None = None) -> str:
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise FollowSourceError("追更时间戳必须带时区")
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class FollowItemRow:
    id: int
    source_id: int
    provider: str
    ref: str
    source_label: str
    entity_id: int | None
    external_id: str
    title: str
    url: str | None
    media_url: str | None
    thumb_url: str | None
    published_at: str | None
    published_precision: str
    version: str | None
    duration: float | None
    semantics: str
    release_key: str
    variant_kind: str
    variant_label: str | None
    group_hint: str | None
    status: str
    asset_id: int | None
    first_seen_at: str
    last_seen_at: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ReleaseGroup:
    """一个作品在所有来源上的全部形态。"""

    release_key: str
    primary: FollowItemRow
    variants: tuple[FollowItemRow, ...]
    duplicates: tuple[FollowItemRow, ...]

    @property
    def providers(self) -> tuple[str, ...]:
        members = (self.primary, *self.variants, *self.duplicates)
        return tuple(dict.fromkeys(item.provider for item in members))

    @property
    def is_release(self) -> bool:
        """这一组是同一作品的历次动态（f95 线程），不是同一作品的多个版本。"""
        return self.primary.semantics == "release"

    @property
    def has_wip(self) -> bool:
        return any(item.variant_kind == "wip" for item in self.variants)

    @property
    def newest_at(self) -> str:
        members = (self.primary, *self.variants, *self.duplicates)
        return max((item.published_at or item.first_seen_at) for item in members)


@dataclass(frozen=True)
class RecordOutcome:
    source_id: int
    discovered: int = 0
    added: int = 0
    updated: int = 0
    not_modified: bool = False
    evidence_path: str | None = None
    #: 证据没存下来的原因。发现本身仍然成立，所以这不是失败，但必须说出来。
    evidence_error: str | None = None


class FollowStore:
    def __init__(self, connect, *, sources_root: Path | None = None):
        """`connect` 是返回 sqlite3 连接的可调用对象；由调用方决定读写事务边界。"""
        self._connect = connect
        self.sources_root = Path(sources_root) / "follow" if sources_root else None

    # ---- 订阅登记 -------------------------------------------------------

    def register(self, *, provider: str, ref: str, label: str, url: str,
                 semantics: str = "work", entity_id: int | None = None,
                 metadata: dict | None = None, moment: datetime | None = None) -> int:
        if semantics not in ("work", "release"):
            raise FollowSourceError("semantics 只能是 work 或 release")
        ref = canonical_source_ref(provider, ref)
        stamp = _now_text(moment)
        payload = json.dumps(metadata or {}, ensure_ascii=False)
        connection = self._connect()
        connection.execute(
            "INSERT INTO follow_source"
            "(entity_id,provider,ref,label,url,semantics,metadata_json,created_at,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(provider,ref) DO UPDATE SET"
            "  label=excluded.label, url=excluded.url, semantics=excluded.semantics,"
            "  entity_id=COALESCE(excluded.entity_id, follow_source.entity_id),"
            "  metadata_json=CASE WHEN excluded.metadata_json='{}'"
            "    THEN follow_source.metadata_json ELSE excluded.metadata_json END,"
            "  updated_at=excluded.updated_at",
            (entity_id, provider, ref, label, url, semantics, payload, stamp, stamp),
        )
        row = connection.execute(
            "SELECT id FROM follow_source WHERE provider=? AND ref=?", (provider, ref)
        ).fetchone()
        return int(row[0])

    def set_enabled(self, source_id: int, enabled: bool,
                    moment: datetime | None = None) -> None:
        self._connect().execute(
            "UPDATE follow_source SET enabled=?, updated_at=? WHERE id=?",
            (1 if enabled else 0, _now_text(moment), source_id),
        )

    def sources(self, *, enabled_only: bool = False) -> tuple[sqlite3.Row, ...]:
        clause = " WHERE enabled=1" if enabled_only else ""
        return tuple(self._connect().execute(
            "SELECT s.*, e.canonical_name AS entity_name FROM follow_source s"
            " LEFT JOIN entity e ON e.id=s.entity_id" + clause +
            " ORDER BY s.provider, s.ref"
        ).fetchall())

    def creator_aliases(self, entity_id: int | None) -> tuple[str, ...]:
        """规范名 + 全部别名。变体判定靠它剥掉标题里的创作者手柄。"""
        if entity_id is None:
            return ()
        connection = self._connect()
        names = [row[0] for row in connection.execute(
            "SELECT canonical_name FROM entity WHERE id=?", (entity_id,))]
        names += [row[0] for row in connection.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=?", (entity_id,))]
        return tuple(dict.fromkeys(name for name in names if name))

    def source_needs_media_reparse(self, source_id: int) -> bool:
        """Whether saved credentials could unlock stale media metadata.

        This is deliberately derived from candidate metadata rather than a new
        truth field.  A successful unconditional refresh replaces the metadata
        and naturally clears the condition.

        判定交给 SQLite 的 `json_extract`：以前是把这个来源**每一条**候选的
        `metadata_json` 整串取回 Python 再逐条 `json.loads`，而这里只想知道
        「有没有任意一条」。回填过的来源单源就有几百到上千行，为一个布尔值把它们
        全解一遍。

        `json_valid` 的外壳不能省：`json_extract` 遇到非法 JSON 是**报错**，不是
        返回 NULL，那会把原来 `except json.JSONDecodeError: continue` 的容忍变成
        整个检查崩掉。写成 `CASE` 而不是并列的 `AND`，因为 SQL 的 `AND` 不保证
        求值顺序。
        """
        row = self._connect().execute(
            "SELECT 1 FROM follow_item WHERE source_id=? AND CASE"
            "   WHEN json_valid(metadata_json)"
            "   THEN json_extract(metadata_json,'$.media_needs_credential')"
            "   END = 1 LIMIT 1",
            (source_id,),
        ).fetchone()
        return row is not None

    # ---- 抓取结果落地 ---------------------------------------------------

    def record(self, source_id: int, fetch: SourceFetch, *,
               creator_aliases: tuple[str, ...] = (),
               moment: datetime | None = None, page: int = 0) -> RecordOutcome:
        stamp = _now_text(moment)
        connection = self._connect()
        if fetch.not_modified:
            connection.execute(
                "UPDATE follow_source SET last_checked_at=?, last_status='not_modified',"
                " last_error=NULL, updated_at=? WHERE id=?", (stamp, stamp, source_id))
            return RecordOutcome(source_id, not_modified=True)

        evidence, evidence_error = self._persist_evidence(fetch, moment)
        added = updated = 0
        for candidate in fetch.candidates:
            verdict = classify(candidate.title, creator_aliases=creator_aliases,
                               version=candidate.version, semantics=fetch.semantics)
            release_key = verdict.release_key
            if fetch.provider == "f95zone":
                # F95 的线程标题只是容器名；每个带资源的楼层都是一次独立发布。
                # 同一楼层若展开出多个视频，由 media_items 在详情里组成 Mix。
                release_key = f"{release_key}\u0000{candidate.external_id}"
            elif not candidate.title_is_name:
                # booru 的「标题」是标签拼出来的，不是名字。让它各自成组，只靠
                # `group_hint` 合并；否则同一作者标签相似的两个作品会被并掉。
                release_key = f"{release_key}\u0000{candidate.external_id}"
            precision = str(candidate.extra.get("published_precision") or
                            ("exact" if candidate.published_at else "unknown"))
            if precision not in ("exact", "approximate", "unknown"):
                precision = "unknown"
            values = (
                source_id, candidate.external_id, candidate.title, candidate.url,
                candidate.media_url, candidate.thumb_url, candidate.published_at,
                precision, verdict.version, candidate.duration, release_key,
                verdict.variant_kind, verdict.variant_label, candidate.group_hint,
                evidence,
                # author 与 summary 单独并进来：连接器把它们放在 DTO 的具名字段上而不是
                # extra 里，但界面要显示「谁发的、说了什么」——f95 线程里九条回复的标题
                # 全是线程名，摘要才是那条动态的内容。摘要截断，追更不做全文存档。
                json.dumps({"markers": list(verdict.markers),
                            **({"author": candidate.author} if candidate.author else {}),
                            **({"summary": candidate.summary[:400]}
                               if candidate.summary else {}),
                            **dict(candidate.extra)}, ensure_ascii=False),
                stamp, stamp,
            )
            existed = connection.execute(
                "SELECT 1 FROM follow_item WHERE source_id=? AND external_id=?",
                (source_id, candidate.external_id)).fetchone() is not None
            connection.execute(
                "INSERT INTO follow_item(source_id,external_id,title,url,media_url,"
                "thumb_url,published_at,published_precision,version,duration,release_key,"
                "variant_kind,variant_label,group_hint,evidence_path,metadata_json,"
                "first_seen_at,last_seen_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(source_id,external_id) DO UPDATE SET"
                "  title=excluded.title, url=excluded.url, media_url=excluded.media_url,"
                # 详情页取不到不等于这条没有发布时间。paheal 每个候选都要单独打一次
                # 详情页，被限流时 `_detail` 返回 {}，这里若直接覆盖，就会把上一轮
                # 已经取到的上传时间和时长抹成 NULL——实测 168 条里 7 条正是这样，
                # 而 `COALESCE(published_at, first_seen_at)` 会让界面改显示抓取时刻。
                "  thumb_url=excluded.thumb_url,"
                "  published_at=COALESCE(excluded.published_at, follow_item.published_at),"
                "  published_precision=CASE WHEN excluded.published_at IS NOT NULL"
                "    THEN excluded.published_precision ELSE follow_item.published_precision END,"
                "  version=excluded.version,"
                "  duration=COALESCE(excluded.duration, follow_item.duration),"
                "  release_key=excluded.release_key, variant_kind=excluded.variant_kind,"
                "  variant_label=excluded.variant_label, group_hint=excluded.group_hint,"
                "  metadata_json=excluded.metadata_json, last_seen_at=excluded.last_seen_at",
                # status、asset_id 与 first_seen_at 刻意不在 SET 里：用户处理过的条目
                # 不因为再次抓到就退回 new，首见时间也不该被重写。
                values,
            )
            if existed:
                updated += 1
            else:
                added += 1
        if page:
            # 往回抓：**不动 etag/last_modified**。那两个值是第一页的条件请求凭据，
            # 拿第 3 页的 etag 覆盖掉，下次常规检查就会拿它去问第一页，
            # 站点回 304，新的更新从此再也进不来。只推进游标。
            connection.execute(
                "UPDATE follow_source SET backfill_page=max(backfill_page,?),"
                " last_checked_at=?, last_status='ok', last_error=NULL, updated_at=?"
                " WHERE id=?", (page, stamp, stamp, source_id))
        else:
            connection.execute(
                "UPDATE follow_source SET etag=?, last_modified=?, last_checked_at=?,"
                " last_status='ok', last_error=NULL, updated_at=? WHERE id=?",
                (fetch.etag, fetch.last_modified, stamp, stamp, source_id))
        return RecordOutcome(source_id, len(fetch.candidates), added, updated,
                             evidence_path=evidence, evidence_error=evidence_error)

    def record_error(self, source_id: int, message: str,
                     moment: datetime | None = None, *, status: str = "error") -> None:
        stamp = _now_text(moment)
        self._connect().execute(
            "UPDATE follow_source SET last_checked_at=?, last_status=?, last_error=?,"
            " updated_at=? WHERE id=?", (stamp, status, message[:500], stamp, source_id))

    def record_history_end(self, source_id: int,
                           moment: datetime | None = None) -> None:
        """Record a successful terminal backfill without advancing its cursor."""
        stamp = _now_text(moment)
        self._connect().execute(
            "UPDATE follow_source SET last_checked_at=?, last_status='not_modified',"
            " last_error=NULL, updated_at=? WHERE id=?", (stamp, stamp, source_id))

    def _persist_evidence(self, fetch: SourceFetch,
                          moment: datetime | None) -> tuple[str | None, str | None]:
        """存原始响应。存不下来不算检查失败。

        Mac 上 `peach-data/sources` 是指向外置盘的符号链接，盘不在时它是一条**断链**——
        `mkdir(exist_ok=True)` 在断链上会抛 `FileExistsError`（链接在、目标不在），
        原来这会让整个 `record()` 连同已经抓到的候选一起炸掉。发现本身跟归档盘无关，
        所以这里降级：候选照常入库，证据标成未取得，原因往上报。

        这和「脱盘模式」是同一条边界——脱的是盘不是账本，不该让整个功能挂掉。
        """
        if self.sources_root is None or fetch.raw_body is None:
            return None, None
        reference = moment or datetime.now(timezone.utc)
        digest = hashlib.sha256(fetch.raw_body).hexdigest()
        key = hashlib.sha256(f"{fetch.provider}\n{fetch.ref}".encode()).hexdigest()[:20]
        directory = self.sources_root / fetch.provider / key
        stamp = reference.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        path = directory / f"{stamp}-{digest[:12]}.raw"
        try:
            directory.mkdir(parents=True, exist_ok=True)
            write_immutable(path, fetch.raw_body)
            write_immutable(path.with_suffix(".json"), (json.dumps({
                "provider": fetch.provider, "ref": fetch.ref,
                # 脱敏后的请求 URL：凭据永不进证据目录。
                "request_url": fetch.request_url, "sha256": digest,
                "checked_at": _now_text(reference), "candidates": len(fetch.candidates),
            }, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        except OSError as error:
            return None, f"证据未取得（{self.sources_root} 不可写：{error.strerror or error}）"
        return str(path.relative_to(self.sources_root.parent)), None

    # ---- 读取与分组 -----------------------------------------------------

    _SELECT = (
        "SELECT i.*, s.provider, s.ref, s.label AS source_label, s.entity_id,"
        " s.semantics"
        " FROM follow_item i JOIN follow_source s ON s.id=i.source_id"
    )

    def items(self, *, statuses: tuple[str, ...] = (), source_id: int | None = None,
              limit: int = 500, offset: int = 0) -> tuple[FollowItemRow, ...]:
        """按发布时间倒序取一页条目。

        排序里带 `i.id DESC` 兜底不只是为了稳定：分页靠 OFFSET，而 `published_at`
        在同一批抓取里大量并列，只按它排的话两次查询的相对顺序可以不同，翻页就会
        重复或漏掉条目。
        """
        clauses, params = [], []
        if statuses:
            clauses.append(f"i.status IN ({','.join('?' * len(statuses))})")
            params.extend(statuses)
        if source_id is not None:
            clauses.append("i.source_id=?")
            params.append(source_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        params.extend((int(limit), max(0, int(offset))))
        rows = self._connect().execute(
            self._SELECT + where +
            " ORDER BY COALESCE(i.published_at, i.first_seen_at) DESC, i.id DESC"
            " LIMIT ? OFFSET ?",
            params).fetchall()
        return tuple(self._row(row) for row in rows)

    def item(self, item_id: int) -> FollowItemRow | None:
        row = self._connect().execute(
            self._SELECT + " WHERE i.id=?", (int(item_id),)
        ).fetchone()
        return self._row(row) if row is not None else None

    def items_for_item(self, item_id: int) -> tuple[FollowItemRow, ...]:
        """Return the target and its grouping peers for a direct detail route."""
        target = self.item(item_id)
        if target is None:
            return ()
        clauses = ["i.release_key=?"]
        params: list[object] = [target.release_key]
        if target.group_hint:
            clauses.append("i.group_hint=?")
            params.append(target.group_hint)
        rows = self._connect().execute(
            self._SELECT + " WHERE " + " OR ".join(clauses) +
            " ORDER BY COALESCE(i.published_at, i.first_seen_at) DESC, i.id DESC",
            params,
        ).fetchall()
        return tuple(self._row(row) for row in rows)

    @staticmethod
    def _row(row) -> FollowItemRow:
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, ValueError):
            metadata = {}
        return FollowItemRow(
            id=row["id"], source_id=row["source_id"], provider=row["provider"],
            ref=row["ref"], source_label=row["source_label"], entity_id=row["entity_id"],
            external_id=row["external_id"], title=row["title"], url=row["url"],
            media_url=row["media_url"], thumb_url=row["thumb_url"],
            published_at=row["published_at"],
            published_precision=row["published_precision"], version=row["version"],
            duration=row["duration"], semantics=row["semantics"],
            release_key=row["release_key"],
            variant_kind=row["variant_kind"], variant_label=row["variant_label"],
            group_hint=row["group_hint"], status=row["status"], asset_id=row["asset_id"],
            first_seen_at=row["first_seen_at"], last_seen_at=row["last_seen_at"],
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    @staticmethod
    def group(items: tuple[FollowItemRow, ...]) -> tuple[ReleaseGroup, ...]:
        """把条目折叠成作品分组。

        先按来源自带的 `group_hint` 合并（booru 的 `parent_id` 比标题可靠），
        再按标题推出的 `release_key` 合并，最后同一组里选主条目。
        """
        # 先按标题判据拆开同站撞车，再按来源自带的关系合并：来源自己声明过的关系
        # 优先，绝不能被标题判据拆散。
        # 兼容已经落库的旧 F95 行：旧版用线程标题作为 release_key，读时也要按
        # 楼层拆开，部署后无需改写真实 ledger 就会立即显示成独立条目。
        split_posts = tuple(
            FollowItemRow(**{**item.__dict__,
                             "release_key": f"{item.release_key}\u0000{item.external_id}"})
            if item.provider == "f95zone"
            and not item.release_key.endswith(f"\u0000{item.external_id}")
            else item
            for item in items
        )
        aligned = _align_by_group_hint(
            _split_ambiguous_works(split_posts, _hint_linked(split_posts)))
        primaries = group_duplicates(aligned)
        buckets: dict[int, tuple[FollowItemRow, list[FollowItemRow]]] = {}
        for item, primary in zip(aligned, primaries):
            primary = primary if primary is not None else item
            buckets.setdefault(id(primary), (primary, []))[1].append(item)
        groups = [
            ReleaseGroup(
                primary.release_key, primary,
                tuple(m for m in members
                      if m is not primary and m.provider == primary.provider),
                tuple(m for m in members
                      if m is not primary and m.provider != primary.provider),
            )
            for primary, members in buckets.values()
        ]
        return tuple(sorted(groups, key=lambda g: g.newest_at, reverse=True))

    # ---- 状态与真相写入 -------------------------------------------------

    def set_status(self, item_id: int, status: str) -> None:
        if status not in ("new", "seen", "saved", "ignored"):
            raise FollowSourceError(f"未知的追更状态：{status}")
        if status == "saved":
            raise FollowSourceError("`saved` 只能由 save_asset() 设置")
        self._connect().execute(
            "UPDATE follow_item SET status=? WHERE id=?", (status, item_id))

    def save_asset(self, item_id: int, *, confirm: bool = False,
                   moment: datetime | None = None) -> int:
        """把一个候选保存成 `location='online'` 的 asset。

        这是真相写入，必须显式 `confirm=True`。它只 INSERT 新行并回填 `asset_id`，
        不改写任何既有 asset 的真相字段，也不下载媒体。
        """
        if not confirm:
            raise FollowSourceError("写 ledger 需要显式 confirm=True")
        connection = self._connect()
        row = connection.execute(
            self._SELECT + " WHERE i.id=?", (item_id,)).fetchone()
        if row is None:
            raise FollowSourceError(f"追更条目 {item_id} 不存在")
        item = self._row(row)
        if item.asset_id:
            return item.asset_id
        if not item.url:
            raise FollowSourceError("候选没有作品页 URL，无法作为在线资产保存")
        stamp = _now_text(moment)
        existing = connection.execute(
            "SELECT id FROM asset WHERE location='online' AND path=?", (item.url,)
        ).fetchone()
        if existing is not None:
            asset_id = int(existing[0])
        else:
            creator = connection.execute(
                "SELECT canonical_name FROM entity WHERE id=?", (item.entity_id,)
            ).fetchone() if item.entity_id else None
            cursor = connection.execute(
                "INSERT INTO asset(location,path,name,medium,creator,duration,"
                "release_date,first_seen,last_seen) VALUES('online',?,?,?,?,?,?,?,?)",
                (item.url, item.title, _medium_for(item), creator[0] if creator else None,
                 item.duration,
                 (item.published_at or "")[:10] or None, stamp, stamp),
            )
            asset_id = int(cursor.lastrowid)
            if item.entity_id:
                connection.execute(
                    "INSERT OR IGNORE INTO asset_entity(asset_id,entity_id,role,source,"
                    "confidence,first_seen_at,last_seen_at)"
                    " VALUES(?,?,'creator',?,1.0,?,?)",
                    (asset_id, item.entity_id, f"follow:{item.provider}", stamp, stamp))
        connection.execute(
            "UPDATE follow_item SET status='saved', asset_id=? WHERE id=?",
            (asset_id, item_id))
        return asset_id


def _medium_for(item: FollowItemRow) -> str:
    if item.duration:
        return "video"
    if item.provider in ("kemono", "coomer", "pawchive"):
        return "illustration"
    return "video"


def _hint_linked(items: tuple[FollowItemRow, ...]) -> frozenset[tuple[str, str]]:
    """来源已经声明为同组的条目。

    `group_hint` 是一个全局字符串（`fanbox:12304831`、`rule34xxx:post:998877`），
    只要两条以上共用它，来源就已经把它们认成同一个作品了。
    """
    counts: dict[str, int] = {}
    for item in items:
        if item.group_hint:
            counts[item.group_hint] = counts.get(item.group_hint, 0) + 1
    shared = {hint for hint, count in counts.items() if count > 1}
    return frozenset(
        (item.provider, item.external_id) for item in items
        if item.group_hint in shared
    )


def _split_ambiguous_works(items: tuple[FollowItemRow, ...],
                           linked: frozenset[tuple[str, str]] = frozenset(),
                           ) -> tuple[FollowItemRow, ...]:
    """`work` 语义下，同一来源出现两个 main 就不再按标题合并这一来源的这一组。

    实测踩到的例子：kemono 上「February Poll Animations」（1 月 31 日）和
    「February Poll + Animations」（2 月 15 日）是两个帖子，归一化后标题完全相同。
    同一个站点里两个都没有变体标记的帖子本来就是两个作品，撞车只说明标题判据到头了。
    这时哪个 alt 该挂到哪个 main 也无从判断，所以整组按 `external_id` 拆开，宁可多出
    几张卡片，也不把两个作品并成一个。

    `release` 语义不适用：那里同一来源的多条本来就是同一个作品的历次动态。
    """
    buckets: dict[tuple[str, str], list[FollowItemRow]] = {}
    for item in items:
        if item.semantics == "release" or not item.release_key:
            continue
        if (item.provider, item.external_id) in linked:
            continue
        buckets.setdefault((item.provider, item.release_key), []).append(item)
    ambiguous = {
        key for key, members in buckets.items()
        if sum(1 for member in members if member.variant_kind == "main") > 1
    }
    if not ambiguous:
        return items
    return tuple(
        FollowItemRow(**{**item.__dict__,
                         "release_key": f"{item.release_key}\u0000{item.external_id}"})
        if (item.provider, item.release_key) in ambiguous
        and (item.provider, item.external_id) not in linked else item
        for item in items
    )


def _align_by_group_hint(items: tuple[FollowItemRow, ...]) -> tuple[FollowItemRow, ...]:
    """让来源声明为同组的条目共用一个 `release_key`。

    判据是「`group_hint` 字符串相同」，**跨站点成立**：rule34.xxx 从 `source` 归一出的
    `fanbox:12304831` 与 kemono 上同一帖子的键完全相同，同一个作品在两个站上因此
    精确合并，不必靠标题去猜。booru 的父子帖也走这条——父帖用自己的 id、子帖用
    `parent_id`，拼出来是同一个键。

    组键取组内最小的 `release_key`，保证结果与条目顺序无关。
    """
    keys: dict[str, str] = {}
    for item in items:
        if not item.group_hint or not item.release_key:
            continue
        current = keys.get(item.group_hint)
        if current is None or item.release_key < current:
            keys[item.group_hint] = item.release_key
    if not keys:
        return items
    return tuple(
        FollowItemRow(**{**item.__dict__, "release_key": keys[item.group_hint]})
        if item.group_hint and item.group_hint in keys
        and keys[item.group_hint] != item.release_key else item
        for item in items
    )
