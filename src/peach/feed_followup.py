"""给 Feed 发现的番号取一份资料和封面（ADR-0042 第六条）。

拉取只解出番号，壳上除了番号什么都没有——没有标题就没法在页面上认出这是哪一部。
这条后继把标题、女优、厂牌、发行日与封面地址取回来写进壳，再把封面装进本机封面目录。

**一轮拉取一条后继。** 同一轮发现的番号在活动页上是一件事，拆成一部一条，一次订阅
就是二十张一模一样的卡片；键里带着这一批的番号，重跑、去重都按这一批算。

**不复用 `process_library`**：那条路以 `asset` 行为单位、要写候选 CSV、要按字段优先级链
结算到真相字段，而壳没有真相字段可写。壳上的每个值都只是「某个来源这么说」，用户复核
的时机是文件真的到手、建成 `asset` 之后。所以这里只借来源链本身
（`metadata_routes`）和发请求那一层（`library_processing.LibraryMetadataProvider`），
不借结算。

**封面走馆藏那一条。** 取图是 `jav_cover_fetch.best_cover`（和重探封面同一个），落盘是
`cover_artwork.install_cover`：书脊折痕的正封框与人脸位置随图一起写进边车，新作卡和
资产卡按同一份边车取景。文件到手、建成 `asset` 之后，这张封面原样就是它的封面。

幂等（ADR-0040 第六条要求）：重跑一次只是把同样的值再写一遍，本机已有的封面不再取；
壳已经不在了就跳过那一部。
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import feeds, metadata_routes
from .catalog_rules import normalise_code_key
from .followups import Followup, FollowupType, register
from .metadata import extract_peach_fields

TASK_KEY = "feed-scrape"
TASK_LABEL = "取新作资料"

#: 一条资料够用就停。四个标量都拿到就不再问下一家——Feed 是后台跑的，
#: 多问一家换来的是配额，而壳上的值本来就不是真相字段。
WANTED = ("title", "performers", "studio", "release_date")

#: 一批最多带几部。新发现的先排，余下的名额给还缺资料或封面、到了重试时间的旧壳。
MAX_BATCH = 24

#: 缺封面或上次没取到资料的壳，定时拉取隔多久再试一次。新片的封面常常晚于番号出现，
#: 所以不是试一次就放弃；但也不该每拉一轮源就把同一批再问一遍。人手点的那一次不等：
#: 点「检查」本身就是要现在取。
RETRY_AFTER = timedelta(hours=12)

#: 一部封面最多等多久。后继在写账本那条串行通道上，一部卡住不能拖住后面整批。
COVER_SECONDS = 30


def followup_key(codes) -> str:
    return f"{TASK_KEY}:{','.join(codes)}"


def parse_key(key: str) -> list[str]:
    prefix, _, body = str(key).partition(":")
    codes = [code for code in body.split(",") if code]
    if prefix != TASK_KEY or not codes:
        raise ValueError(f"认不出这条取资料后继：{key}")
    return codes


def _label(codes: list[str]) -> str:
    if len(codes) == 1:
        return f"{TASK_LABEL}：{codes[0]}"
    return f"{TASK_LABEL}：{codes[0]} 等 {len(codes)} 部"


def plan(codes) -> list[Followup]:
    """一批番号合成一条后继；一部都没有就不派。"""
    batch = list(dict.fromkeys(code for code in codes if code))[:MAX_BATCH]
    if not batch:
        return []
    return [Followup(key=followup_key(batch), task_key=TASK_KEY, label=_label(batch))]


def has_local_cover(cover_root: Path, code: str) -> bool:
    key = normalise_code_key(code)
    return bool(key) and (Path(cover_root) / f"{key}.jpg").is_file()


def backlog(connection, cover_root: Path, *, exclude=(), now: datetime | None = None,
            limit: int = MAX_BATCH, retry_after: timedelta = RETRY_AFTER) -> list[str]:
    """还缺资料或本机封面、上次尝试已经过了 `retry_after` 的壳。

    已忽略的不算：人说了不想看，就不再替它花配额。已经入库的壳本来就不在表里
    （入库即从列表里消失，ADR-0042 第三条），这里同样用番号键排除掉。
    """
    moment = now or datetime.now(timezone.utc)
    cutoff = feeds.stamp(moment - retry_after)
    skip = set(exclude)
    rows = connection.execute(
        "SELECT d.code,d.scraped_at,d.scrape_error FROM feed_discovery d"
        " WHERE d.ignored_at IS NULL AND (d.scraped_at IS NULL OR d.scraped_at<?)"
        " AND NOT EXISTS (SELECT 1 FROM asset a WHERE a.code IS NOT NULL"
        " AND normalise_code_key(a.code)=normalise_code_key(d.code))"
        " ORDER BY COALESCE(d.release_date,d.discovered_at) DESC, d.id DESC",
        (cutoff,)).fetchall()
    found: list[str] = []
    for row in rows:
        code = row["code"]
        if code in skip:
            continue
        needs_fields = row["scraped_at"] is None or row["scrape_error"] is not None
        if needs_fields or not has_local_cover(cover_root, code):
            found.append(code)
        if len(found) >= limit:
            break
    return found


def _cover(payload: dict) -> str | None:
    for field in ("cover_url", "cover"):
        value = str(payload.get(field) or "").strip()
        if value:
            return value
    urls = payload.get("cover_urls")
    if isinstance(urls, list):
        for value in urls:
            text = str(value or "").strip()
            if text:
                return text
    return None


def collect(provider, code: str) -> tuple[dict, str | None]:
    """按番号问来源链，返回 (字段, 封面地址)。

    问哪几家由 `metadata_routes` 决定，与刮削链同一份判据；这里没有本机证据可给，
    所以只传番号本身。一家都没给就抛——调用方把原因写进壳的 `scrape_error`，
    页面上那一行因此能说清是「还没取」还是「取不到」。
    """
    chain = metadata_routes.route_for_code(code)
    found = provider.community(
        code, route=metadata_routes.community_route(code))
    fields: dict[str, object] = {}
    cover: str | None = None
    for _source, payload in found:
        if not isinstance(payload, dict):
            continue
        cover = cover or _cover(payload)
        for name, item in extract_peach_fields(payload).items():
            if name in WANTED and name not in fields:
                fields[name] = item.get("value")
        if all(name in fields for name in WANTED):
            break
    if not fields and cover is None:
        raise ValueError(f"来源链 {'、'.join(chain)} 上都没有这个番号的资料")
    return fields, cover


def fetch_cover(contract, code: str) -> tuple[bytes, tuple[int, int], dict]:
    """官方渠道里这个番号最大的那张封面，连同写进 `.scraping.json` 的来路。

    取不到就抛；原因交给调用方记账，一部取不到不影响同批其余几部。
    """
    from .jav_cover_fetch import HostLimitedTransport, best_cover
    from .scraping_access import SourceTransport

    raw = SourceTransport(contract.follow_secrets_root, max_requests=40,
                          max_bytes=32 * 1024 * 1024, max_seconds=COVER_SECONDS)
    transport = HostLimitedTransport(raw, 1.0)
    try:
        candidate, size, data = best_cover(
            transport, code, 0,
            metadata_root=contract.follow_sources_root / "metadata" / "javinizer-go",
            deadline=time.monotonic() + COVER_SECONDS)
    finally:
        transport.close()
    digest = hashlib.sha256(data).hexdigest()
    evidence = {"code": code, "width": size[0], "height": size[1],
                "source": candidate.source, "source_url": candidate.url,
                "raw_sha256": digest, "installed_sha256": digest,
                "checked_at": time.time(), "resolver": "peach-jav-cover-v1"}
    return data, size, evidence


def _install_cover(contract, code: str) -> bool:
    """本机还没有这个番号的封面就去取来装上。返回这一部现在有没有封面。"""
    from .catalog_rules import is_korean_mib_code
    from .cover_artwork import install_cover

    key = normalise_code_key(code)
    if not key or is_korean_mib_code(key):
        return False
    if has_local_cover(contract.cover_root, key):
        return True
    data, size, evidence = fetch_cover(contract, key)
    install_cover(Path(contract.cover_root) / f"{key}.jpg", key, data, size, evidence=evidence)
    return True


def _performer_names(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item.get("name") or "") if isinstance(item, dict) else str(item)
                for item in value]
    return []


def _scrape_fields(contract, provider, row) -> bool:
    """取一部的资料写进壳。返回取没取到；取不到的原因写在壳的 `scrape_error` 上。"""
    code = row["code"]
    try:
        fields, cover = collect(provider, code)
    except Exception as error:  # noqa: BLE001 - 原因要写到壳上给人看
        with contract.database.write_transaction() as connection:
            connection.execute(
                "UPDATE feed_discovery SET scrape_error=?,scraped_at=? WHERE id=?",
                (str(error), feeds.stamp(), int(row["id"])))
        return False
    names = _performer_names(fields.get("performers"))
    with contract.database.write_transaction() as connection:
        connection.execute(
            "UPDATE feed_discovery SET title=COALESCE(?,title),cover_url=COALESCE(?,cover_url),"
            "studio=COALESCE(?,studio),release_date=COALESCE(?,release_date),"
            "performers=COALESCE(?,performers),scrape_error=NULL,scraped_at=? WHERE id=?",
            (fields.get("title") or None, cover, fields.get("studio") or None,
             fields.get("release_date") or None, "、".join(name for name in names if name) or None,
             feeds.stamp(), int(row["id"])))
        for entity_id in feeds.match_performers(connection, names):
            feeds.link_entity(connection, int(row["id"]), entity_id)
    return True


def run(contract, key: str, handle) -> dict:
    """跑一批取资料。返回的摘要就是活动页上那一行：几部、取到几部、装上几张封面。"""
    from .library_processing import LibraryMetadataProvider

    codes = parse_key(key)
    provider = None
    fetched = missed = covers = 0
    for index, code in enumerate(codes):
        handle.progress(current=index, total=len(codes),
                        label=f"{TASK_LABEL}：{code}", throttle=0)
        with contract.database.read_connection() as connection:
            row = connection.execute(
                "SELECT id,code,scraped_at,scrape_error FROM feed_discovery WHERE code=?",
                (code,)).fetchone()
        if row is None:
            # 壳被删了，或者这个番号这中间已经入库。两种都不该再取一遍。
            continue
        if row["scraped_at"] is None or row["scrape_error"] is not None:
            provider = provider or LibraryMetadataProvider(contract.follow_secrets_root)
            if _scrape_fields(contract, provider, row):
                fetched += 1
            else:
                missed += 1
        try:
            covers += _install_cover(contract, code)
        except Exception:  # noqa: BLE001 - 取不到封面这一部照样有资料，下一轮再试
            pass
        # 封面取没取到都记下这一次尝试，`backlog` 按它隔 `RETRY_AFTER` 再试。
        with contract.database.write_transaction() as connection:
            connection.execute("UPDATE feed_discovery SET scraped_at=? WHERE id=?",
                               (feeds.stamp(), int(row["id"])))
    handle.progress(current=len(codes), total=len(codes), label=TASK_LABEL, throttle=0)
    contract.cache_bust()
    return {"total": len(codes), "ok": fetched, "miss": missed, "covers": covers}


#: 写账本：壳与实体关联都在 `ledger.db` 里，所以它走串行那条通道。
TYPE = register(FollowupType(task_key=TASK_KEY, label=TASK_LABEL,
                             writes_ledger=True, run=run))
