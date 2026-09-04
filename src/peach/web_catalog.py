"""浏览与详情：列表、版本组、分卷组、单条详情、筛面和标签编辑。

从 2372 行的 `web_contract` 拆出的最大一块。这一域的共同点不是「都在查 asset 表」，
而是**共用同一套可见性与展示口径**：`tag_not_hidden` 决定哪些标签算数、
`state_predicate` 决定「未看／稍后看／已标记」怎么翻成 SQL、`attach_jav_display_fields`
决定番号作品在卡片上叫什么。这几条一旦在不同页面漂开，同一部片在首页、女优页和
详情页会显示成三个样子，而每一页单独看都「对」。所以它们必须留在同一个模块里，
由 `web_entity`、`web_stats`、`web_batch` 反过来 import，而不是各自再写一遍。
"""
from __future__ import annotations

import hashlib
import random
import time

from .catalog_rules import (
    LENGTH_TAGS,
    collapse_superseded_taste_tags,
    is_jav_asset,
    jav_display_metadata,
    normalise_code_key,
    ordered_multipart_items,
    part_marker,
    tag_cat,
)
from .entities import normalize_entity_name, upsert_asset_entity
from .metadata_policy import SOURCE_SPECS
from .web_activity import DEFAULT_PROFILE_ID
from .web_state import WebContract


COST = {"local": "free", "115": "free", "pikpak": "metered", "online": "metered"}

#: 卡片随每条记录返回的女优上限。共演作品必须带上全部出镜者，而不是只留第一位；
#: 但 BEST 合集实测有 41 位，全量下发会把列表响应撑大，所以截断并同时给出总数，
#: 由界面显示「等 N 人」。详情页走 q_item，不受这个上限影响。
CARD_PERFORMERS = 6

#: 排序拆成「列 + 方向」两段：`{d}` 由方向填入。方向不进列键，`时长` 才能在同一枚
#: 控件上翻转，而不是分裂成两个互斥选项，也不会有一个方向在界面上永远点不到。
#: 每个方向都显式 `NULLS LAST`——升序时 SQLite 默认把 NULL 排在最前，
#: 「时长最短」会先给出一整屏没有时长的条目。
SORT_COLUMNS = {
    "new": "a.first_seen {d} NULLS LAST, a.id {d}",
    "release": "a.release_date {d} NULLS LAST, a.first_seen {d} NULLS LAST, a.id {d}",
    "size": "a.size {d} NULLS LAST",
    "dur": "a.duration {d} NULLS LAST",
    "played": "a.last_played {d} NULLS LAST",
    "rating": "a.rating {d} NULLS LAST, a.o_count {d} NULLS LAST",
    "plays": "a.play_count {d} NULLS LAST, a.last_played {d} NULLS LAST",
    "o": "a.o_count {d} NULLS LAST",
}

#: 旧键沿用：地址栏和书签里存着把方向写进键名的值，认不出来它们会落到
#: `a.id DESC`——那不报错，只是给出一屏顺序看起来合理、其实没按要求排的结果。
SORT_LEGACY_KEYS = {"big": ("size", "desc"), "short": ("dur", "asc"), "long": ("dur", "desc")}


def attach_jav_display_fields(row: dict, tags=(), entity_kinds=()) -> None:
    """Add one canonical display projection while retaining raw file identity fields."""
    row["is_jav"] = is_jav_asset(
        row.get("code"), row.get("studio"), row.get("release_date"), entity_kinds,
    )
    if row["is_jav"]:
        row.update(jav_display_metadata(row.get("name"), row.get("code"), tags))


def tag_is_not_a_performer_name(tag: str) -> str:
    """「这个标签不是某个女优的名字」的 SQL 判据。

    同名的标签和 performer 身份会互相冒充，所以标签榜要把它们排掉。这条同样写了
    四份，其中一份拿 `lower(trim(t.tag))` 去比 `performer.normalized_name`——后者
    是 Python casefold 写进去的，而 SQLite 的 lower() 只认 ASCII，于是西里尔或
    带罗马数字的名字永远排不掉。列一侧一律走 `peach_normalize()`。
    """
    return ("NOT EXISTS(SELECT 1 FROM entity performer WHERE performer.kind='performer' "
            f"AND performer.normalized_name={tag})")


def tag_not_hidden(asset: str, tag: str) -> str:
    """「这个标签没有被用户隐藏」的 SQL 判据。

    同一条规则此前在五处各写了一份裸 SQL。join 列和比较列因查询语境不同是正常的，
    但规则本体（默认档案、hidden=1、按归一化名比对）只该有一份：漏抄一处，被隐藏
    的标签就会从那个表面漏回来，而这属于语义契约。

    `tag` 传比较用的表达式。列一侧要用 `peach_normalize()`——SQLite 的 lower() 只认
    ASCII，拿它去比 Python casefold 写进去的值，非 ASCII 标签永远匹配不上。
    """
    return ("NOT EXISTS(SELECT 1 FROM asset_tag_preference p "
            f"WHERE p.asset_id={asset} AND p.profile_id='{DEFAULT_PROFILE_ID}' "
            f"AND p.hidden=1 AND p.normalized_tag={tag})")


#: 「这部作品属于某家事务所」的判据：它的出镜者里有这家的现役成员。
#: 归属是人的属性，作品只是顺着人被算进来的——所以这里比的是 `entity_membership`，
#: 不是给作品另存一个事务所字段。多存一份就会漂移，而漂移的那份没人会发现。
AGENCY_ASSET_CLAUSE = (
    "EXISTS(SELECT 1 FROM asset_entity ae "
    "JOIN entity_membership m ON m.member_id=ae.entity_id "
    "JOIN entity agency ON agency.id=m.agency_id "
    "WHERE ae.asset_id=a.id AND agency.kind='agency' AND agency.canonical_name=?)"
)

#: 搜索里的同一条关系，但按名字模糊比，并且认别名——事务所改名比女优改艺名还常见，
#: 「GRANZPRO」和「LiStarPRO」是同一批人。
AGENCY_SEARCH_CLAUSE = (
    "EXISTS(SELECT 1 FROM asset_entity ae "
    "JOIN entity_membership m ON m.member_id=ae.entity_id "
    "JOIN entity agency ON agency.id=m.agency_id "
    "WHERE ae.asset_id=a.id AND agency.kind='agency' "
    "AND (agency.canonical_name LIKE ? OR EXISTS(SELECT 1 FROM entity_alias al "
    "WHERE al.entity_id=agency.id AND al.alias LIKE ?)))"
)


def q_items(contract: WebContract, args):
    trash = args.get("state") == "trash"
    # 普通馆藏仍是视频表面；回收站必须展示所有文件类型，否则从垃圾复核移入的
    # 图片、网址快捷方式等会变成不可见、不可恢复，只能被「清空回收站」直接删掉。
    where, par = ([] if trash else ["a.medium='video'"]), []
    if trash:
        where.append("a.disposal='trash'")
    else:
        where.append("(a.disposal IS NULL OR a.disposal <> 'trash')")
    if args.get("loc"):
        locs = [x for x in args["loc"].split(",") if x]
        where.append("a.location IN (%s)" % ",".join("?" * len(locs))); par += locs
    if args.get("creator"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='creator' AND e.canonical_name=?)"
        ); par.append(args["creator"])
    if args.get("performer"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='performer' AND e.canonical_name=?)"
        ); par.append(args["performer"])
    if args.get("studio"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='studio' AND e.canonical_name=?)"
        ); par.append(args["studio"])
    if args.get("series"):
        where.append(
            "EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='series' AND e.canonical_name=?)"
        ); par.append(args["series"])
    # 事务所隔一层：作品是它的成员拍的，`asset_entity` 里没有事务所的行。
    if args.get("agency"):
        where.append(AGENCY_ASSET_CLAUSE); par.append(args["agency"])
    if args.get("tag"):
        tags = [x for x in args["tag"].split(",") if x]
        tag_clause = (
            "((EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='tag' AND e.canonical_name=?) OR "
            "EXISTS(SELECT 1 FROM asset_tag t WHERE t.asset_id=a.id AND t.tag=?)) AND "
            + tag_not_hidden("a.id", "?") + ")"
        )
        if args.get("tag_match") == "any" and len(tags) > 1:
            where.append("(" + " OR ".join(tag_clause for _ in tags) + ")")
            for tag in tags:
                par.extend((tag, tag, normalize_entity_name(tag)))
        else:
            # 默认保持原有组合语义：逗号分隔的标签必须全部满足。
            for tag in tags:
                where.append(tag_clause)
                par.extend((tag, tag, normalize_entity_name(tag)))
    # 回收站是跨类型恢复入口。首页遗留的「只看有缩略图」、时长、画幅和 JAV
    # 条件只对视频成立，带进这里会再次把图片、网址快捷方式等资源藏起来。
    if not trash and args.get("len"):
        where.append("a.ctx_length = ?"); par.append(args["len"])
    if not trash and args.get("dur_min"):
        where.append("a.duration >= ?"); par.append(max(0, float(args["dur_min"])))
    if not trash and args.get("dur_max"):
        where.append("a.duration <= ?"); par.append(max(0, float(args["dur_max"])))
    if not trash and args.get("orient"):
        where.append("a.ctx_orient = ?"); par.append(args["orient"])
    elif not trash and args.get("exclude_vertical") == "1":
        where.append("(a.ctx_orient IS NULL OR a.ctx_orient <> '竖屏')")
    if not trash and args.get("jav") == "1":
        # 只有番号形态还不够：JI-103 这类 creator clip 没有任何发行证据。
        where.append(JAV_ASSET_PREDICATE)
    if args.get("q"):
        query = args["q"].strip()
        if len(query) >= 3 and contract.has_fts():
            # 事务所名不在 FTS 索引里，也不该进去：`asset_search` 索引的是作品自己的
            # 文字和它名下的实体名，而事务所隔着一层成员关系。搜「Capsule Agency」
            # 要能出这家人的片，所以在这里并联一条成员关系的判据。
            where.append(
                "(a.id IN (SELECT asset_id FROM asset_search WHERE asset_search MATCH ?)"
                " OR " + AGENCY_SEARCH_CLAUSE + ")"
            )
            par.append('"' + query.replace('"', '""') + '"')
            par += [f"%{query}%"] * 2
        else:
            # 短查询走 LIKE，必须和 FTS 覆盖同样的身份写法：规范名、别名和检索词。
            # 只比 canonical_name 会让「凉森」搜不到 `涼森れむ`——trigram 要求三字
            # 起步，两字查询永远落在这条分支上，补检索词也救不了。
            where.append(
                "((a.name LIKE ? OR a.catalog_title LIKE ? OR a.original_title LIKE ? "
                "OR a.code LIKE ? OR EXISTS("
                "SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=a.id AND e.kind IN ('creator','performer','studio') "
                "AND (e.canonical_name LIKE ? "
                "OR EXISTS(SELECT 1 FROM entity_alias al WHERE al.entity_id=e.id "
                "AND al.alias LIKE ?) "
                "OR EXISTS(SELECT 1 FROM entity_search_term st WHERE st.entity_id=e.id "
                "AND st.term LIKE ?))))"
                " OR " + AGENCY_SEARCH_CLAUSE + ")"
            )
            pattern = f"%{query}%"
            par += [pattern] * 9
    state = state_predicate(str(args.get("state") or ""))
    if state:
        where.append(state)
    if not trash and args.get("thumb") == "1":
        # 已保存的关注条目只登记在线资产，不下载媒体或生成本地缩略图。
        # 它仍然是可筛选的真实资产；若沿用首页的缩略图门槛，来源 facet 会显示
        # 「在线 1」，点进去却永远是 0 条。
        where.append("(a.snapshot_path IS NOT NULL OR a.location = 'online')")

    requested = str(args.get("sort") or "")
    sort_key, legacy_dir = SORT_LEGACY_KEYS.get(requested, (requested, ""))
    direction = "ASC" if (str(args.get("dir") or "").lower() or legacy_dir) == "asc" else "DESC"
    column = SORT_COLUMNS.get(sort_key)
    order = column.format(d=direction) if column else ("RANDOM()" if sort_key == "rand" else None)
    if order is None:
        if args.get("sort") == "seed":
            sd = int(args.get("seed") or 1) % 99991 or 7
            order = f"((a.id * {sd}) % 99991)"
        elif args.get("sort") == "daily" or not args.get("sort"):
            # 每日轮换：用当天日期做种子打散，同一天顺序固定，隔天自动换一批。
            # 不用 RANDOM() —— 那样每次刷新都不同，翻页还会重复/漏掉。
            seed = int(time.strftime("%Y%m%d")) % 9973 or 7
            order = f"((a.id * {seed}) % 99991)"
        else:
            order = "a.id DESC"
    lim = min(int(args.get("limit", 60)), 200)
    off = int(args.get("offset", 0))
    include_total = args.get("count", "1") != "0"
    fetch_limit = lim if include_total else lim + 1
    sql = ("SELECT a.id,a.location,a.path,a.name,a.catalog_title,a.original_title,a.medium,"
           "a.creator,a.studio,a.code,a.release_date,a.size,"
           "a.duration,a.width,a.height,a.ctx_length,a.ctx_orient,a.snapshot_path,"
           "a.play_count,a.leave_ratio,a.feedback,a.disposal,a.rating,a.o_count,"
           "a.play_seconds,a.max_reached,a.seek_count,"
           "EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=a.id "
           f"AND w.profile_id='{DEFAULT_PROFILE_ID}') AS watch_later "
           "FROM asset a WHERE " + " AND ".join(where) + f" ORDER BY {order} LIMIT ? OFFSET ?")
    with contract.read_connection() as c:
        rows = [dict(r) for r in c.execute(sql, par + [fetch_limit, off])]
        has_more = len(rows) > lim if not include_total else None
        rows = rows[:lim]
        # 条数和体积同一次聚合出来：回收站卡片要说的是「清空能腾出多少」，
        # 为它单独再发一次请求只是把同一条 WHERE 又跑一遍。
        cnt, total_bytes = (
            c.execute("SELECT count(*),COALESCE(sum(a.size),0) FROM asset a WHERE "
                      + " AND ".join(where), par).fetchone()
            if include_total else (None, None))
    # 卡片要显示出镜者和高权重标签，不能只有番号 —— 一次批量取，别 N+1
    if rows:
        ids = [r["id"] for r in rows]
        qm = ",".join("?" * len(ids))
        tmap: dict[int, list[str]] = {}
        for aid, tag in con_tags(contract, ids, qm):
            tmap.setdefault(aid, []).append(tag)
        emap: dict[int, dict[str, list[str]]] = {}
        performer_refs: dict[int, list[dict[str, object]]] = {}
        for aid, entity_id, kind, name in con_entities(contract, ids, qm):
            emap.setdefault(aid, {}).setdefault(kind, []).append(name)
            if kind == "performer":
                performer_refs.setdefault(aid, []).append(
                    entity_ref(contract, "performer", entity_id, name))
        for r in rows:
            ts = tmap.get(r["id"], [])
            canonical = emap.get(r["id"], {})
            canonical_tags = canonical.get("tag", [])
            canonical_performers = canonical.get("performer", [])
            all_performers = canonical_performers or [
                tag[3:] for tag in ts if tag.startswith("演员:")
            ]
            performers = all_performers[:CARD_PERFORMERS]
            performer_names = {normalize_entity_name(name) for name in all_performers}
            visible_tags = collapse_superseded_taste_tags(
                canonical_tags or [t for t in ts if not t.startswith("演员:")]
            )
            r["tags"] = [
                tag for tag in visible_tags
                if tag_cat(tag) in (
                    "general", "relationship", "role", "appearance", "scene", "story", "position",
                )
                and normalize_entity_name(tag) not in performer_names
            ][:4]
            r["performers"] = performers
            refs = performer_refs.get(r["id"], [])
            r["performer_entities"] = refs[:CARD_PERFORMERS]
            r["performer_total"] = len(refs) or len(all_performers)
            r["_entity_kinds"] = tuple(canonical)
    for r in rows:
        r["cost"] = COST.get(r["location"], "metered")
        r["has_thumb"] = contract.has_snapshot(r["snapshot_path"])
        r["has_cover"] = contract.has_cover(r.get("code"))
        # 卡片上的出镜者称谓、规范番号、版本徽章与详情页使用同一份投影。
        attach_jav_display_fields(r, r.get("tags", ()), r.pop("_entity_kinds", ()))
        if r["has_cover"]:
            r["cover_frame"] = contract.cover_frame(r.get("code"))
        r.pop("snapshot_path", None)
        r.pop("path", None)                     # 路径不外发，串流走 id
    attach_multipart_groups(contract, rows)
    attach_edition_groups(contract, rows)
    return {"total": cnt, "bytes": total_bytes, "items": rows, "has_more": has_more}

def con_tags(contract: WebContract, ids, qm):
    with contract.read_connection() as c:
        return c.execute(
            f"SELECT asset_id, tag FROM asset_tag WHERE asset_id IN ({qm})", ids).fetchall()


def con_entities(contract: WebContract, ids, qm):
    with contract.read_connection() as connection:
        return connection.execute(
            f"SELECT DISTINCT ae.asset_id,e.id,e.kind,e.canonical_name "
            f"FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            f"WHERE ae.asset_id IN ({qm}) "
            f"AND e.kind IN ('tag','performer','creator','studio','series') "
            f"ORDER BY ae.asset_id,e.kind,e.canonical_name", ids,
        ).fetchall()


def entity_ref(contract: WebContract, kind: str, entity_id, name: str) -> dict:
    """身份引用：id、名字，加上「实体图取不取得到」。

    卡片头像、详情页身份格和沉浸模式的署名圈都读这一份，所以标志跟着引用走，不由
    各处自己再问一遍。缺了它，这些位置只能无条件出 `<img>`、等 `/entity-image` 回
    404 再把图摘掉——一个作品详情页实测就是 5 个这样的 404，而那条响应不带缓存头。
    """
    return {"id": entity_id, "name": name,
            "has_image": contract.has_entity_image(kind, entity_id)}


def attach_avatar_availability(contract: WebContract, rows, key="rep",
                               flag="has_avatar"):
    """给带代表作 id 的行标上「`/avatar` 取不取得到」。

    判据要看接触印相在不在盘上，一次批量取路径——逐行查库就是 N+1，顶栏一次 30 行。
    「还没裁过但印相还在」算取得到：`/avatar` 按需生成，把这种也判成没有等于把点一下
    就有的头像永远关掉。
    """
    ids = sorted({int(row[key]) for row in rows if row.get(key)})
    paths: dict[int, str | None] = {}
    if ids:
        marks = ",".join("?" * len(ids))
        with contract.read_connection() as connection:
            paths = {row[0]: row[1] for row in connection.execute(
                f"SELECT id,snapshot_path FROM asset WHERE id IN ({marks})", ids)}
    for row in rows:
        rep = row.get(key)
        row[flag] = bool(rep) and contract.has_avatar(rep, paths.get(int(rep)))


def attach_card_performers(contract: WebContract, rows):
    """给各类视频卡片补同一份表演者资料，避免首页/相关/复核卡片各说各话。"""
    if not rows:
        return
    ids = [row["id"] for row in rows]
    qm = ",".join("?" * len(ids))
    names: dict[int, list[str]] = {}
    refs: dict[int, list[dict[str, object]]] = {}
    for asset_id, entity_id, kind, name in con_entities(contract, ids, qm):
        if kind != "performer":
            continue
        names.setdefault(asset_id, []).append(name)
        refs.setdefault(asset_id, []).append(
            entity_ref(contract, "performer", entity_id, name))
    for row in rows:
        row["performers"] = names.get(row["id"], [])[:CARD_PERFORMERS]
        row["performer_entities"] = refs.get(row["id"], [])[:CARD_PERFORMERS]
        row["performer_total"] = len(names.get(row["id"], []))


#: 版次的展示次序：正片在前，处理过的在后。这不是偏好排序，只是要一个稳定的
#: 锚点——卡片标题取第一个，次序一变卡片就换名字。
EDITION_ORDER = ("有码", "中字", "无码", "无码破解")


def _edition_label(row: dict, tags: tuple[str, ...] = ()) -> str:
    """这一份是哪个版次。

    判据只有 `jav_display_metadata` 一份。自己按文件名再写一套「像不像无码」的判断，
    会和卡片上已经显示的徽章各说各话——同一个文件，角标写着无码、分组却当它是正片。
    """
    badges = jav_display_metadata(
        row.get("name"), row.get("code"), tags,
    ).get("edition_badges") or []
    return str(badges[0]) if badges else "有码"


def _edition_rows(contract: WebContract, codes) -> list[dict]:
    raw_codes = sorted({str(code) for code in codes if str(code or "").strip()})
    if not raw_codes:
        return []
    placeholders = ",".join("?" * len(raw_codes))
    with contract.read_connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT id,name,code,size,duration FROM asset "
            f"WHERE medium='video' AND code IN ({placeholders}) "
            "AND (disposal IS NULL OR disposal<>'trash')",
            raw_codes,
        )]
        if not rows:
            return []
        # 版次判据同时看文件名和标签（`无码` 可能只登记在标签上），所以标签要一起取。
        marks = ",".join("?" * len(rows))
        tags: dict[int, list[str]] = {}
        for row in connection.execute(
                "SELECT ae.asset_id aid, e.canonical_name name FROM asset_entity ae "
                "JOIN entity e ON e.id=ae.entity_id "
                f"WHERE e.kind='tag' AND ae.asset_id IN ({marks})",
                [row["id"] for row in rows]):
            tags.setdefault(int(row["aid"]), []).append(str(row["name"]))
    for row in rows:
        row["edition"] = _edition_label(row, tuple(tags.get(int(row["id"]), ())))
    return rows


def _edition_groups(contract: WebContract, codes) -> dict[str, list[dict]]:
    """按番号聚合，只保留版次真的不同的那些。

    同番号多文件不等于多版本：实测 158 个同番号多文件的番号里，84 个是分卷、
    还有一批是同名重复（`ABP-442.avi` 出现两次、`.MP4` 与 `.mp4` 各一份）。把它们
    一并当版本，会把「该去重复文件页处理的东西」伪装成「可选的版本」。
    """
    candidates: dict[str, list[dict]] = {}
    for row in _edition_rows(contract, codes):
        candidates.setdefault(normalise_code_key(row.get("code")), []).append(row)
    groups: dict[str, list[dict]] = {}
    for code, items in candidates.items():
        if len(items) < 2:
            continue
        if ordered_multipart_items(items):
            continue                      # 分卷由 attach_multipart_groups 负责，含裸名首卷
        if len({item["edition"] for item in items}) < 2:
            continue                      # 版次相同就是重复文件，不是版本
        groups[code] = sorted(
            items,
            key=lambda item: (EDITION_ORDER.index(item["edition"])
                              if item["edition"] in EDITION_ORDER else len(EDITION_ORDER),
                              -int(item.get("size") or 0), int(item["id"])),
        )
    return groups


def attach_edition_groups(contract: WebContract, rows) -> None:
    """给列表卡挂上同番号的版次组，不写账本。

    用户实测：`ABF-234` 与 `ABF-234 UN` 是两张并排的卡，`ABF-216` 也是。它们是同一部
    片的两个版次，占两个格子只是让人多滚一屏，还得自己认哪个是无码。
    """
    if not rows:
        return
    groups = _edition_groups(contract, [row.get("code") for row in rows])
    for row in rows:
        code = normalise_code_key(row.get("code"))
        group = groups.get(code)
        if not group or not any(item["id"] == row["id"] for item in group):
            continue
        row["edition_group"] = {
            "key": code,
            "title": code or str(row.get("code") or "多版本作品"),
            "count": len(group),
            "seed_id": group[0]["id"],
            "item_ids": [item["id"] for item in group],
            "editions": [item["edition"] for item in group],
        }


def q_editions(contract: WebContract, args):
    """按版次次序返回同一番号的全部版本。"""
    asset_id = int(args["id"])
    with contract.read_connection() as connection:
        seed = connection.execute(
            "SELECT id,code FROM asset WHERE id=? AND medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash')",
            (asset_id,),
        ).fetchone()
    if not seed or not seed["code"]:
        return {"error": "edition group not found"}
    code = normalise_code_key(seed["code"])
    group = _edition_groups(contract, [seed["code"]]).get(code, [])
    if not group or not any(item["id"] == asset_id for item in group):
        return {"error": "edition group not found"}
    items = []
    for row in group:
        item = q_item(contract, row["id"])
        item["edition_label"] = row["edition"]
        items.append(item)
    return {"title": code or str(seed["code"]), "count": len(items), "items": items}


def _multipart_rows(contract: WebContract, codes) -> list[dict]:
    raw_codes = sorted({str(code) for code in codes if str(code or "").strip()})
    if not raw_codes:
        return []
    placeholders = ",".join("?" * len(raw_codes))
    with contract.read_connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT id,name,code,size,duration FROM asset "
            f"WHERE medium='video' AND code IN ({placeholders}) "
            "AND (disposal IS NULL OR disposal<>'trash')",
            raw_codes,
        )]
    return rows                           # 裸名首卷没有标记，由 ordered_multipart_items 定夺


def _multipart_groups(contract: WebContract, codes) -> dict[str, list[dict]]:
    candidates: dict[str, list[dict]] = {}
    for row in _multipart_rows(contract, codes):
        candidates.setdefault(normalise_code_key(row.get("code")), []).append(row)
    return {
        code: ordered
        for code, items in candidates.items()
        if (ordered := ordered_multipart_items(items))
    }


def attach_multipart_groups(contract: WebContract, rows) -> None:
    """Annotate list cards with one derived multipart release, without ledger writes."""
    if not rows:
        return
    groups = _multipart_groups(contract, [row.get("code") for row in rows])
    for row in rows:
        code = normalise_code_key(row.get("code"))
        group = groups.get(code)
        if not group or not any(item["id"] == row["id"] for item in group):
            continue
        row["part_group"] = {
            "key": code,
            "title": code or str(row.get("code") or "分卷作品"),
            "count": len(group),
            "seed_id": group[0]["id"],
            "item_ids": [item["id"] for item in group],
            "total_duration": sum(float(item.get("duration") or 0) for item in group),
            "total_size": sum(int(item.get("size") or 0) for item in group),
        }


def q_parts(contract: WebContract, args):
    """Return an explicitly marked multipart release in playback order."""
    asset_id = int(args["id"])
    with contract.read_connection() as connection:
        seed = connection.execute(
            "SELECT id,code FROM asset WHERE id=? AND medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash')",
            (asset_id,),
        ).fetchone()
    if not seed or not seed["code"]:
        return {"error": "multipart release not found"}
    code = normalise_code_key(seed["code"])
    group = _multipart_groups(contract, [seed["code"]]).get(code, [])
    if not group or not any(item["id"] == asset_id for item in group):
        return {"error": "multipart release not found"}
    items = []
    for position, row in enumerate(group, 1):
        item = q_item(contract, row["id"])
        marker = part_marker(str(row.get("name") or ""))
        # 裸名首卷没有标记，卷标按队列位置给；有标记时沿用文件名里的写法。
        item["part_label"] = (marker.upper() if marker.isalpha() else marker) or str(position)
        items.append(item)
    return {"title": code or str(seed["code"]), "count": len(items), "items": items}

def q_item(contract: WebContract, aid):
    """按 id 直取。
    ⚠️ 没有这个接口时，前端只能用「带筛选条件再查一遍然后 find」的绕法：
       limit 被覆盖成 1 → find 必然失败 → 走兜底 items[0]，
       于是**每次点击都打开同一个默认列表首项**（一个 12.6 GB 的 PikPak 文件），
       既显示错条目，又反复拉计费流量。按 id 取就按 id 取。"""
    with contract.read_connection() as c:
        r = c.execute(
            "SELECT id,location,path,name,catalog_title,original_title,creator,studio,code,"
            "release_date,size,duration,width,height,"
            "ctx_length,ctx_orient,snapshot_path,play_count,leave_ratio,feedback,disposal,"
            "rating,o_count,play_seconds,max_reached,seek_count,"
            "COALESCE((SELECT p.liked FROM asset_preference p WHERE p.asset_id=asset.id "
            f"AND p.profile_id='{DEFAULT_PROFILE_ID}'),0) AS liked,"
            "COALESCE((SELECT p.reason FROM asset_preference p WHERE p.asset_id=asset.id "
            f"AND p.profile_id='{DEFAULT_PROFILE_ID}'),'') AS like_reason,"
            "COALESCE((SELECT g.wanted FROM asset_quality_goal g WHERE g.asset_id=asset.id "
            f"AND g.profile_id='{DEFAULT_PROFILE_ID}'),0) AS better_version,"
            "COALESCE((SELECT g.reason FROM asset_quality_goal g WHERE g.asset_id=asset.id "
            f"AND g.profile_id='{DEFAULT_PROFILE_ID}'),'') AS better_version_reason,"
            "EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=asset.id "
            f"AND w.profile_id='{DEFAULT_PROFILE_ID}') AS watch_later FROM asset WHERE id=?", (aid,)).fetchone()
        if not r:
            return {"error": "not found"}
        d = dict(r)
        # 在线资产的 `path` 是来源作品页，不是可播地址；能播的那条代理在
        # `/follow-stream?id=<follow_item>`。保存时写的是 `follow_item.asset_id`，
        # 反查一次就能让馆藏详情自己播，不必先跳回关注页。
        if d.get("location") == "online":
            row = c.execute(
                "SELECT id FROM follow_item WHERE asset_id=? ORDER BY id LIMIT 1", (aid,),
            ).fetchone()
            d["follow_item_id"] = int(row[0]) if row else None
        legacy_rows = list(c.execute(
            "SELECT t.tag,t.source FROM asset_tag t WHERE t.asset_id=? AND "
            + tag_not_hidden("t.asset_id", "peach_normalize(t.tag)")
            + " ORDER BY t.tag", (aid,),
        ))
        canonical = list(c.execute(
            "SELECT DISTINCT e.id,e.kind,e.canonical_name FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=? "
            "AND e.kind IN ('tag','performer','creator','studio','series') "
            "AND (e.kind<>'tag' OR "
            + tag_not_hidden("ae.asset_id", "e.normalized_name") + ") "
            "ORDER BY e.kind,e.canonical_name", (aid,),
        ))
    legacy = [row[0] for row in legacy_rows]
    official_tag_names = {
        normalize_entity_name(tag)
        for tag, source in legacy_rows
        if str(source or "").startswith("javinizer:")
        and str(source or "").endswith(":tag")
        and SOURCE_SPECS.get(str(source).split(":", 2)[1], None)
        and SOURCE_SPECS[str(source).split(":", 2)[1]].official
    }
    canonical_tags = [name for _, kind, name in canonical if kind == "tag"]
    canonical_performers = [name for _, kind, name in canonical if kind == "performer"]
    canonical_creators = {
        normalize_entity_name(name)
        for _, kind, name in canonical if kind == "creator"
    }
    performers = canonical_performers or [
        tag[3:] for tag in legacy
        if tag.startswith("演员:")
        and normalize_entity_name(tag[3:]) not in canonical_creators
    ]
    performer_names = {normalize_entity_name(name) for name in performers}
    tags = collapse_superseded_taste_tags([tag for tag in (canonical_tags or [
        tag for tag in legacy if not tag.startswith("演员:")
    ]) if normalize_entity_name(tag) not in performer_names])
    d["tags"] = [
        {
            "k": tag,
            "cat": tag_cat(tag),
            "official": normalize_entity_name(tag) in official_tag_names,
        }
        for tag in tags if tag not in LENGTH_TAGS
    ]
    d["performers"] = performers
    d["entities"] = {
        kind: [name for _, item_kind, name in canonical if item_kind == kind]
        for kind in ("creator", "performer", "studio", "series")
    }
    d["entity_refs"] = {
        kind: [entity_ref(contract, kind, entity_id, name)
               for entity_id, item_kind, name in canonical if item_kind == kind]
        for kind in ("creator", "performer", "studio", "series")
    }
    if d["entities"]["creator"]:
        d["creator"] = d["entities"]["creator"][0]
    if d["entities"]["studio"]:
        d["studio"] = d["entities"]["studio"][0]
    d["cost"] = COST.get(d["location"], "metered")
    d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
    # 身份格的厂牌位和顶栏小圆片同一条判据：没装标识就不输出 `<img>`。规范厂牌走
    # `entity_refs`，非规范的那条只有扁平 `studio` 字段，两边都要有标志，否则
    # 后者会从「本来能取到图」退化成永远首字母。
    for ref in d["entity_refs"]["studio"]:
        ref["has_logo"] = contract.has_logo(ref["name"])
    d["has_studio_logo"] = contract.has_logo(d.get("studio"))
    # 「女优」是番号发行物的行业称谓；creator clip 即使长得像番号也仍是普通内容。
    attach_jav_display_fields(
        d, [tag["k"] for tag in d["tags"]],
        [kind for kind, values in d["entities"].items() if values],
    )
    d.pop("snapshot_path", None); d.pop("path", None)
    return d

def q_related(contract: WebContract, aid, limit=24):
    """接着看：IDF 抑制泛标签，MMR 避免近重复连续占满列表。"""
    from peach.related import rank_related

    with contract.read_connection() as c:
        source_row = c.execute(
            "SELECT id,duration,release_date FROM asset WHERE id=?", (aid,),
        ).fetchone()
        if not source_row:
            return {"items": []}
        source_entities = list(c.execute(
            "SELECT DISTINCT ae.entity_id,e.kind FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=? "
            "AND e.kind IN ('creator','performer','series','studio','tag')", (aid,),
        ))
        if not source_entities:
            return {"items": []}
        COLS = ("id,location,name,catalog_title,original_title,creator,studio,code,size,duration,width,height,"
                "ctx_orient,snapshot_path,play_count,leave_ratio,feedback,disposal,o_count")
        source_entity_ids = [row[0] for row in source_entities]
        source_marks = ",".join("?" * len(source_entity_ids))
        candidate_rows = [dict(row) for row in c.execute(
            f"SELECT {COLS},a.release_date FROM asset a JOIN asset_entity shared "
            "ON shared.asset_id=a.id WHERE a.medium='video' AND a.id<>? "
            "AND (a.feedback IS NULL OR a.feedback<>'dislike') AND a.disposal IS NULL "
            f"AND shared.entity_id IN ({source_marks}) GROUP BY a.id "
            "ORDER BY count(DISTINCT shared.entity_id) DESC,a.id LIMIT 4000",
            (aid, *source_entity_ids),
        )]
        ids = [aid, *(row["id"] for row in candidate_rows)]
        entities = {asset_id: {} for asset_id in ids}
        for offset in range(0, len(ids), 800):
            batch = ids[offset:offset + 800]
            qm = ",".join("?" * len(batch))
            for asset_id, entity_id, kind in c.execute(
                "SELECT ae.asset_id,ae.entity_id,e.kind FROM asset_entity ae "
                "JOIN entity e ON e.id=ae.entity_id "
                f"WHERE ae.asset_id IN ({qm}) AND e.kind IN "
                "('creator','performer','series','studio','tag')", tuple(batch),
            ):
                entities[asset_id].setdefault(kind, set()).add(entity_id)

        def rank_row(row):
            release_date = row.get("release_date") or ""
            return {
                **row, "entities": entities[row["id"]],
                "year": int(release_date[:4]) if release_date[:4].isdigit() else None,
            }

        source = rank_row(dict(source_row))
        picked = rank_related(source, (rank_row(row) for row in candidate_rows), limit,
                              seed=f"related:{aid}")
        for row in picked:
            row["_entity_kinds"] = tuple(row["entities"])
            row.pop("entities", None)
            row.pop("year", None)
    attach_card_performers(contract, picked)
    related_tags: dict[int, list[str]] = {}
    if picked:
        related_ids = [row["id"] for row in picked]
        marks = ",".join("?" * len(related_ids))
        for asset_id, tag in con_tags(contract, related_ids, marks):
            related_tags.setdefault(asset_id, []).append(tag)
    for d in picked:
        d["cost"] = COST.get(d["location"], "metered")
        d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
        d["has_cover"] = contract.has_cover(d.get("code"))
        attach_jav_display_fields(
            d, related_tags.get(d["id"], ()), d.pop("_entity_kinds", ()),
        )
        if d["has_cover"]:
            d["cover_frame"] = contract.cover_frame(d.get("code"))
        d.pop("release_date", None)
        d.pop("snapshot_path", None)
    return {"items": picked[:limit]}

#: JAV 语境下的资产过滤片段。历史缺连字符编号先规范化，但仍必须再有发行证据；
#: 否则 RAIKUN325 这类账号和 JI-103 creator clip 会混入。FC2 单独保留。
JAV_ASSET_PREDICATE = (
    "a.code IS NOT NULL AND a.code<>'' AND is_jav_code(normalise_code_key(a.code)) AND ("
    "upper(trim(a.code)) LIKE 'FC2%' OR COALESCE(trim(a.studio),'')<>'' "
    "OR COALESCE(trim(a.release_date),'')<>'' OR EXISTS("
    "SELECT 1 FROM asset_entity jav_ae JOIN entity jav_e ON jav_e.id=jav_ae.entity_id "
    "WHERE jav_ae.asset_id=a.id AND jav_e.kind IN ('performer','studio','series')))"
)
JAV_ASSET_CLAUSE = "AND " + JAV_ASSET_PREDICATE + " "


#: 首页的状态筛选（新鲜 / 看过 / 已标记 / 稍后看）。作品列表、顶部三层和筛选面板
#: 必须用同一份口径：否则「已标记」页会列出全库的人物、厂牌和标签，点进去却是空的。
def state_predicate(state: str) -> str:
    """返回这个状态对应的 SQL 谓词（已加括号，不含 `AND`）；未知状态返回空串。"""
    if state == "fresh":
        return "((a.play_count IS NULL OR a.play_count=0) AND a.feedback IS NULL)"
    if state == "played":
        return "(a.play_count > 0)"
    if state == "flagged":
        return ("(COALESCE(a.o_count,0)>0 OR EXISTS(SELECT 1 FROM asset_preference p "
                f"WHERE p.asset_id=a.id AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.liked=1))")
    if state == "later":
        return ("(EXISTS(SELECT 1 FROM watch_queue w WHERE w.asset_id=a.id "
                f"AND w.profile_id='{DEFAULT_PROFILE_ID}'))")
    return ""


def state_clause(state: str) -> str:
    """同一个谓词的 `AND ...` 形式，给拼在 WHERE 后面的查询用。"""
    predicate = state_predicate(state)
    return f"AND {predicate} " if predicate else ""


#: 顶部三层的候选池相对展示位的倍数。严格取前 N 会让这一条永远是同一批人——
#: 「换一批」刷新后上面纹丝不动。放大候选池再按种子确定性抽样，既保持是常见身份，
#: 又能真的换一批。倍数太大就会开始出现只有一两部作品的冷门项。
TOPS_POOL_FACTOR = 4


def q_tops(contract: WebContract, n=28, jav=False, seed="", state=""):
    """顶部三层用的数据：女优圆头像 / 厂牌 / 内容标签。

    缓存的人物肖像由前端优先使用；缺失时才回退到代表作接触印相裁切。

    `state` 跟作品列表同一份口径：在「已标记」这类页面上，上面这排头像
    只应该出现真的有已标记作品的人，否则点进去是空的。"""
    with contract.read_connection() as c:
        scope = (JAV_ASSET_CLAUSE if jav else "") + state_clause(state)
        base = (
            "SELECT e.id,e.canonical_name,count(DISTINCT ae.asset_id) n,"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE ae2.entity_id=e.id AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY (a2.play_count IS NULL),a2.size DESC LIMIT 1) rep "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id "
            "WHERE a.medium='video' AND e.kind=? " + scope +
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT ?"
        )

        def pick(kind):
            """按数量取候选池，再按种子确定性抽样。种子为空时退回严格前 N。"""
            pool = [{"id": entity_id, "k": k, "n": cnt, "rep": representative}
                    for entity_id, k, cnt, representative
                    in c.execute(base, (kind, n * TOPS_POOL_FACTOR if seed else n))]
            if not seed or len(pool) <= n:
                return pool[:n]
            # 同一个种子必须给出同一批人：翻页和重绘之间不能抖动。
            digest = hashlib.blake2b(f"{seed}:{kind}".encode(), digest_size=8).digest()
            rng = random.Random(int.from_bytes(digest, "big"))
            chosen = rng.sample(pool, n)
            # 抽完仍按数量排序，免得常见身份被排到末尾。
            return sorted(chosen, key=lambda row: -row["n"])

        out = {}
        out["performers"] = pick("performer")
        out["studios"] = pick("studio")
    # 顶栏那排厂牌小圆片据此决定要不要输出 `<img>`：没装标识就直接首字母垫底。
    # 判定在库连接之外做，它读的是目录索引而不是账本。
    for studio in out["studios"]:
        studio["has_logo"] = contract.has_logo(studio["k"])
    # 女优那排同理，只是它有两级图：规范实体图优先，取不到才回落到代表作头像。
    # 两级都要标志，否则第一级空着的那些人会各打一个必然 404 的请求再回落。
    for performer in out["performers"]:
        performer["has_image"] = contract.has_entity_image("performer", performer["id"])
    # 厂牌那排自己不出头像，但两排的 `rep` 都会进前端的 REP 表，卡片头像回落时读的
    # 就是它——所以两排都得判。
    attach_avatar_availability(contract, out["performers"] + out["studios"])
    return out




def q_facets(
    contract: WebContract,
    jav: bool = False,
    scope_kind: str = "",
    scope_name: str = "",
    asset_id: int | None = None,
    state: str = "",
):
    """返回当前浏览集合真正存在的筛选项。

    首页不带 scope，维持全库口径；实体资料页按规范实体收窄，详情页按单个作品收窄。
    筛选项必须来自和作品列表相同的规范关系，不能让前端拿全库 facets 猜当前页面。
    """
    with contract.read_connection() as c:
        scope = (JAV_ASSET_CLAUSE if jav else "") + state_clause(state)
        scope_params: list[object] = []
        if asset_id is not None:
            scope += "AND a.id=? "
            scope_params.append(int(asset_id))
        elif scope_kind or scope_name:
            if (scope_kind not in {"creator", "performer", "studio", "series", "agency"}
                    or not scope_name):
                raise ValueError("invalid facet scope")
            if scope_kind == "agency":
                # 事务所的筛选项必须和它的作品列表同源，否则右栏会给出点进去是 0 条的项。
                scope += "AND " + AGENCY_ASSET_CLAUSE + " "
                scope_params.append(scope_name)
            else:
                scope += (
                    "AND EXISTS(SELECT 1 FROM asset_entity scope_ae "
                    "JOIN entity scope_e ON scope_e.id=scope_ae.entity_id "
                    "WHERE scope_ae.asset_id=a.id AND scope_e.kind=? "
                    "AND scope_e.canonical_name=?) "
                )
                scope_params.extend((scope_kind, scope_name))
        out = {}
        out["locations"] = [dict(r) for r in c.execute(
            "SELECT a.location AS k, count(*) AS n, "
            "SUM(CASE WHEN a.play_count>0 THEN 1 ELSE 0 END) AS played "
            "FROM asset a WHERE a.medium='video' " + scope +
            "GROUP BY a.location ORDER BY n DESC", scope_params)]
        out["orientations"] = [dict(r) for r in c.execute(
            "SELECT a.ctx_orient AS k,count(*) AS n FROM asset a "
            "WHERE a.medium='video' AND a.ctx_orient IS NOT NULL AND a.ctx_orient<>'' " + scope +
            "GROUP BY a.ctx_orient ORDER BY n DESC", scope_params)]
        out["creators"] = [dict(r) for r in c.execute(
            "SELECT e.canonical_name AS k,count(DISTINCT ae.asset_id) AS n "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='creator' " + scope +
        
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 60", scope_params)]
        # 标签要分层 —— 一锅端会让「演员:一个ren」和「1080P」「足交」混在一起。
        # 三类分开：技术规格（画质/时长/画幅，筛选价值低）、内容维度（真正有用的）、演员（另立一栏）。
        rows = [dict(r) for r in c.execute(
            "SELECT e.canonical_name AS k, count(DISTINCT ae.asset_id) AS n "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='tag' " + scope +
            "AND " + tag_is_not_a_performer_name("e.normalized_name") + " "
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 400", scope_params)]
        classified = [
            dict(r, cat=tag_cat(r["k"]))
            for r in rows
            if r["k"] not in LENGTH_TAGS
        ]
        out["tags"] = [r for r in classified if r["cat"] != "meta"][:44]
        out["tech"] = [r for r in classified if r["cat"] == "meta"][:16]
        out["tagperformers"] = [dict(r) for r in c.execute(
            "SELECT e.canonical_name AS k,count(DISTINCT ae.asset_id) AS n "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='performer' " + scope +
        
            "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT 20", scope_params)]
        st = c.execute(
            "SELECT count(*) total, COALESCE(sum(size),0) bytes, "
            "SUM(CASE WHEN duration IS NOT NULL THEN 1 ELSE 0 END) duration, "
            "SUM(CASE WHEN play_count>0 THEN 1 ELSE 0 END) played, "
            "SUM(CASE WHEN COALESCE(o_count,0)>0 OR EXISTS(SELECT 1 FROM asset_preference p "
            f"WHERE p.asset_id=a.id AND p.profile_id='{DEFAULT_PROFILE_ID}' AND p.liked=1) "
            "THEN 1 ELSE 0 END) flagged, "
            "SUM(EXISTS(SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=a.id AND e.kind='creator')) attributed "
            "FROM asset a WHERE a.medium='video' AND (a.disposal IS NULL OR a.disposal<>'trash') "
            + scope, scope_params).fetchone()
        out["stats"] = dict(st)
    return out

# ────────────────────────────── 写入 ──────────────────────────────

def w_item_tag(contract: WebContract, body):
    """新增或隐藏单条资源标签；隐藏不销毁刮削/识别来源证据。"""
    contract.cache_bust()
    aid = int(body["id"])
    operation = str(body.get("operation", "")).strip()
    tag = str(body.get("tag", "")).strip()
    if operation not in {"add", "remove"}:
        raise ValueError("operation must be add or remove")
    if not tag or len(tag) > 80 or tag.startswith("演员:"):
        raise ValueError("tag must be 1 to 80 characters and cannot be a performer marker")
    normalized = normalize_entity_name(tag)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # 事务边界只有一个入口：write_transaction 自己取 database.write_lock 并在异常时回滚。
    # 这里不手取那把锁再手动 commit/close：任何 execute 抛出都会漏掉回滚和关闭。
    # 那把锁不可重入，所以外层不能再套一个取同一把锁的 with，否则自死锁。
    with contract.write_transaction() as c:
        if not c.execute("SELECT 1 FROM asset WHERE id=?", (aid,)).fetchone():
            raise ValueError("asset not found")
        if operation == "remove":
            c.execute(
                "INSERT INTO asset_tag_preference(profile_id,asset_id,normalized_tag,hidden,updated_at) "
                f"VALUES('{DEFAULT_PROFILE_ID}',?,?,1,?) ON CONFLICT(profile_id,asset_id,normalized_tag) "
                "DO UPDATE SET hidden=1,updated_at=excluded.updated_at",
                (aid, normalized, stamp),
            )
        else:
            c.execute(
                f"DELETE FROM asset_tag_preference WHERE profile_id='{DEFAULT_PROFILE_ID}' "
                "AND asset_id=? AND normalized_tag=?", (aid, normalized),
            )
            c.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "VALUES(?,?,1.0,'web-user')", (aid, tag),
            )
            upsert_asset_entity(
                c, kind="tag", name=tag, asset_id=aid, role="tag",
                source="web-user", confidence=1.0,
                metadata={"profile_id": DEFAULT_PROFILE_ID}, now=stamp,
            )
    return {"ok": True, "operation": operation, "tag": tag,
            "tags": [item["k"] for item in q_item(contract, aid)["tags"]]}
