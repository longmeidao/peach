"""实体资料页：女优／厂牌／创作者／系列的聚合，以及它们的图集与索引页。

实体是 ledger 的规范身份（见 AGENTS.md 术语表），扁平的 `asset_tag`、creator/studio
字段只是兼容投影。这一域负责把两者合成一页：别名归并、代表作、图集分组、索引分类。

它 import `web_catalog` 的可见性谓词，而不是自己写一份——女优页上该不该出现某个标签，
必须和首页是同一个判据。
"""
from __future__ import annotations

import json
import re
import time

from urllib.parse import urlsplit

from .catalog_rules import LENGTH_TAGS, dir_expr, photo_set_title, tag_cat
from .entities import normalize_entity_name, resolve_entity, rewrite_flat_projection
from .web_catalog import (
    COST,
    VISIBLE_CATALOG_ASSET,
    attach_avatar_availability,
    seeded_order,
    tag_is_not_a_performer_name,
    tag_not_hidden,
)
from .web_state import WebContract


#: 有资料页的实体种类。事务所（agency）和厂牌是两件事：厂牌出片、事务所出人，
#: 一位女优可以在同一年里给多个厂牌拍片而只属于一家事务所。
PROFILE_KINDS = {"performer", "studio", "creator", "series", "agency"}


def scope_predicate(kind: str, column: str, subject: str = "?") -> str:
    """这一页的作品挂在谁名下的 SQL 判据，占位符恒为一个。

    事务所自己不挂作品——作品是它的成员拍的，`asset_entity` 里没有它的行。把范围
    从「这个 id」换成「这组 id」之后，事务所页和女优页共用同一批统计、标签和图集
    查询，而不是各写一份再慢慢漂移。

    `subject` 默认是占位符，索引页那种「一句 SQL 里每行一个实体」的写法传列名
    （`e.id`）。判据只有这一份，索引页和资料页数出来的作品数才不会各算各的。
    """
    if kind == "agency":
        return (f"{column} IN (SELECT member_id FROM entity_membership"
                f" WHERE agency_id={subject})")
    return f"{column}={subject}"


#: 索引页地址 → `entity.kind`。有资料页就该有索引页：只靠女优页上那个名字进事务所页的话，
#: 名下没有关系的几十家等于只能靠猜地址。标签不在这里，它走另一条分支。
INDEX_ENTITY_KINDS = {"performers": "performer", "creators": "creator",
                      "studios": "studio", "agencies": "agency"}


def q_entity(contract: WebContract, args):
    """女优、厂牌、事务所等实体的资料页。

    `source_reference` 是私人馆藏来源证据：API 只返回站点名和备注，不把敏感下载
    地址变成可点击链接。官方、社交和资料库链接可直接访问。
    """
    kind = args.get("kind", "")
    name = args.get("name", "")
    if kind not in PROFILE_KINDS or not name:
        return {"error": "invalid entity"}
    with contract.read_connection() as c:
        row = resolve_entity(c, kind, name)
        if not row:
            return {"error": "not found"}
        d = dict(row)
        try:
            metadata = json.loads(d.pop("metadata_json") or "{}")
        except (TypeError, ValueError):
            metadata = {}
        d["metadata"] = metadata
        # 同一个名字按来源分行（主键含 source），合并会再写一条 `merge:*`，所以同一个
        # 写法能出现两次。留痕属于账本，展示不该把同一个名字并排列两遍：按归一形取
        # 置信度最高的那一条。`max()` 让 SQLite 把裸列取自同一行，结果是确定的。
        d["aliases"] = [r[0] for r in c.execute(
            "SELECT alias,max(confidence) AS top FROM entity_alias WHERE entity_id=?"
            " GROUP BY normalized_alias ORDER BY top DESC,alias",
            (d["id"],),
        )]
        # 罗马字仍是检索和旧链接的重要身份键，但中文/日文规范名下面再把英文全列一遍
        # 只会像名称没有本地化。展示契约单独收窄，身份契约 `aliases` 保持完整。
        d["display_aliases"] = _display_entity_aliases(
            d["canonical_name"], d["aliases"])
        links = []
        for link in c.execute(
            "SELECT id AS link_id,link_kind,label,url,hostname,is_sensitive,metadata_json "
            "FROM entity_link WHERE entity_id=? ORDER BY link_kind,label", (d["id"],),
        ):
            item = dict(link)
            host = item["hostname"] or urlsplit(item["url"]).hostname or ""
            sensitive = bool(item.pop("is_sensitive")) or item["link_kind"] == "source_reference"
            item["hostname"] = host
            item["clickable"] = not sensitive
            if sensitive:
                item["url"] = None
            try:
                item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            except (TypeError, ValueError):
                item["metadata"] = {}
            links.append(item)
        d["links"] = links
        d["search_terms"] = [dict(r) for r in c.execute(
            "SELECT term,purpose,source FROM entity_search_term WHERE entity_id=? "
            "ORDER BY purpose,term", (d["id"],),
        )]
        d["external_refs"] = [dict(r) for r in c.execute(
            "SELECT provider,external_kind,external_id,last_synced_at "
            "FROM entity_external_ref WHERE entity_id=? ORDER BY provider,external_kind",
            (d["id"],),
        )]
        scope = scope_predicate(kind, "ae.entity_id")
        count, rep = c.execute(
            "SELECT count(DISTINCT ae.asset_id),"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE " + scope_predicate(kind, "ae2.entity_id") +
            " AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY a2.size DESC LIMIT 1) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE " + scope + " AND a.medium='video'", (d["id"], d["id"]),
        ).fetchone()
        d["asset_count"] = count
        d["representative_asset_id"] = rep
        d["avatar_focus"] = contract.avatar_focus(kind, d["id"])
        d["tags"] = [dict(r) for r in c.execute(
            "SELECT tag.id,tag.canonical_name k,count(DISTINCT scope.asset_id) n "
            "FROM asset_entity scope "
            "JOIN asset_entity tagged ON tagged.asset_id=scope.asset_id "
            "JOIN entity tag ON tag.id=tagged.entity_id "
            "JOIN asset a ON a.id=scope.asset_id "
            "WHERE " + scope_predicate(kind, "scope.entity_id") +
            " AND a.medium='video' AND tag.kind='tag' "
            "AND " + tag_is_not_a_performer_name("tag.normalized_name") + " "
            f"AND tag.canonical_name NOT IN ({','.join('?' for _ in LENGTH_TAGS)}) "
            "AND " + tag_not_hidden("scope.asset_id", "tag.normalized_name") + " "
            "GROUP BY tag.id,tag.canonical_name ORDER BY n DESC,tag.canonical_name LIMIT 36",
            (d["id"], *sorted(LENGTH_TAGS)),
        )]
        # 那排圆头像，事务所页问的是另一个问题。别的资料页问「谁和这条实体同台」，
        # 事务所页问「这家有哪些人」——共演者对它没有意义，它自己一部片都没拍。
        # 契约形状保持一致（id / k / n / rep），前端仍是同一个组件。
        if kind == "agency":
            roster = c.execute(
                "SELECT person.id,person.canonical_name k,"
                "(SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae "
                " JOIN asset a ON a.id=ae.asset_id "
                " WHERE ae.entity_id=person.id AND a.medium='video') n,"
                "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
                " WHERE ae2.entity_id=person.id AND a2.medium='video' "
                " AND a2.snapshot_path IS NOT NULL "
                " ORDER BY COALESCE(a2.play_count,0) DESC,COALESCE(a2.play_seconds,0) DESC,"
                " COALESCE(a2.width,0)*COALESCE(a2.height,0) DESC,a2.size DESC LIMIT 1) rep "
                "FROM entity_membership m JOIN entity person ON person.id=m.member_id "
                "WHERE m.agency_id=? ORDER BY n DESC,person.canonical_name",
                (d["id"],))
        else:
            roster = c.execute(
                "SELECT person.id,person.canonical_name k,count(DISTINCT scope.asset_id) n,"
                "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
                " WHERE ae2.entity_id=person.id AND a2.medium='video' "
                " AND a2.snapshot_path IS NOT NULL "
                " ORDER BY COALESCE(a2.play_count,0) DESC,COALESCE(a2.play_seconds,0) DESC,"
                " COALESCE(a2.width,0)*COALESCE(a2.height,0) DESC,a2.size DESC LIMIT 1) rep "
                "FROM asset_entity scope "
                "JOIN asset_entity co ON co.asset_id=scope.asset_id "
                "JOIN entity person ON person.id=co.entity_id "
                "JOIN asset a ON a.id=scope.asset_id "
                "WHERE scope.entity_id=? AND a.medium='video' AND person.kind='performer' "
                "AND person.id<>? "
                "GROUP BY person.id,person.canonical_name "
                "ORDER BY n DESC,person.canonical_name LIMIT 18",
                (d["id"], d["id"]))
        d["related_performers"] = [dict(person) for person in roster]
        d["member_count"] = c.execute(
            "SELECT count(*) FROM entity_membership WHERE agency_id=?", (d["id"],)).fetchone()[0]
        # 这条实体现在归哪家事务所。`metadata.agency` 记的是采到的原文和采集时间，
        # 这里给的是账本里那条实体——前者是证据，后者才是能点进去的身份。
        d["agency"] = None
        home = c.execute(
            "SELECT agency.id,agency.canonical_name,m.source,m.checked_at "
            "FROM entity_membership m JOIN entity agency ON agency.id=m.agency_id "
            "WHERE m.member_id=?", (d["id"],)).fetchone()
        if home:
            d["agency"] = dict(home)
    # 公司那个大位先取 `/logo`、取不到才退到别的图。没装标识时直接跳过这一环，省掉
    # 必然 404 的那一跳。标识按名字落盘，厂牌和事务所是同一个仓、同一条取图链。
    if kind in ("studio", "agency"):
        d["has_logo"] = contract.has_logo(d["canonical_name"])
    # 大位那条链的后两环同样要随资料下发：实体图取不到就直接从代表作头像起步，两样
    # 都取不到就一个 `<img>` 都不出。判定在库连接之外做，它读的是目录索引。
    d["has_image"] = contract.has_entity_image(kind, d["id"])
    attach_avatar_availability(contract, [d], key="representative_asset_id")
    # 页脚那排共演者是同一个圆头像，用的也是同一条两级链，取景也是同一份 sidecar。
    # 圆框越小越需要取景：一张 3762×2535 的封面塞进 44 px 的圆里，几何居中给出的是
    # 封面正中那块版式，脸在不在里面全看运气。事务所页的艺人大图与这排小圆头像用
    # 同一条链，差别只在框多大，所以判据不该按页面分岔。
    for person in d["related_performers"]:
        person["has_image"] = contract.has_entity_image("performer", person["id"])
        person["avatar_focus"] = contract.avatar_focus("performer", person["id"])
    attach_avatar_availability(contract, d["related_performers"])
    if kind == "agency":
        # 事务所的门面是它自己的标识。没装实体图时给出官网那条链接的 id，页面拿它去
        # `/link-mark` 取站点圆标；两样都没有就只剩首字母。作品截图不参加——那是
        # 某位成员某部片的画面，和这家公司没有关系。
        d["mark_link_id"] = next(
            (link["link_id"] for link in d["links"] if link["link_kind"] == "official"), None)
    return d

# ────────────────────────────── 照片 ──────────────────────────────
# 图集就是目录：账本没有图集实体，一个目录下的图片本来就是一份图集，
# `<作品目录>\P\001.jpg` 这种约定在 A:/B: 上到处都是。图集的 id 用目录里最小的
# 资产 id，既稳定又不用把真实路径发给前端（`q_item` 同样不发 `path`）。

#: 图集查询一律带 `a.` 别名。
PHOTO_DIR = dir_expr()


def _display_entity_aliases(canonical_name: str, aliases: list[str]) -> list[str]:
    """本地化规范名不重复展示纯拉丁转写；原始别名仍完整保留在 API。"""
    east_asian = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
    canonical_key = normalize_entity_name(canonical_name)
    unique_aliases = [alias for alias in aliases
                      if normalize_entity_name(alias) != canonical_key]
    if not east_asian.search(canonical_name or ""):
        return unique_aliases
    return [alias for alias in unique_aliases
            if east_asian.search(alias or "") or not re.search(r"[A-Za-z]", alias or "")]


def q_entity_photos(contract: WebContract, args):
    """实体名下的图片墙；目录分组只保留为兼容元数据。"""
    kind, name = args.get("kind", ""), args.get("name", "")
    if kind not in PROFILE_KINDS or not name:
        return {"error": "invalid entity"}
    try:
        limit = max(1, min(int(args.get("limit") or 120), 600))
        offset = max(0, int(args.get("offset") or 0))
        # 带种子是「换一批」；不带就按目录、文件名排，一套图的编号顺序不被打乱。
        seed = str(args.get("seed") or "")
        order = seeded_order(seed) if seed else "dir,a.name,a.id"
    except (TypeError, ValueError):
        return {"error": "invalid pagination"}
    with contract.read_connection() as c:
        row = resolve_entity(c, kind, name)
        if not row:
            return {"error": "not found"}
        sets = [{
            "id": item["id"],
            "title": photo_set_title(item["dir"]),
            "n": item["n"],
            "bytes": item["bytes"] or 0,
            "location": item["location"],
            "cost": COST.get(item["location"], "metered"),
        } for item in c.execute(
            f"SELECT {PHOTO_DIR} dir,min(a.id) id,count(*) n,sum(a.size) bytes,a.location "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE " + scope_predicate(kind, "ae.entity_id") +
            " AND a.medium='image' AND a.name IS NOT NULL "
            "AND (a.disposal IS NULL OR a.disposal<>'trash') "
            f"GROUP BY {PHOTO_DIR},a.location ORDER BY n DESC,dir",
            (row["id"],),
        )]
        total = c.execute(
            "SELECT count(DISTINCT a.id) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE " + scope_predicate(kind, "ae.entity_id") +
            " AND a.medium='image' AND a.name IS NOT NULL "
            "AND (a.disposal IS NULL OR a.disposal<>'trash')",
            (row["id"],),
        ).fetchone()[0]
        items = [{"id": item["id"], "name": item["name"], "size": item["size"] or 0,
                  "location": item["location"]}
                 for item in c.execute(
                     f"SELECT a.id,a.name,a.size,a.location,{PHOTO_DIR} dir "
                     "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
                     "WHERE " + scope_predicate(kind, "ae.entity_id") +
                     " AND a.medium='image' AND a.name IS NOT NULL "
                     "AND (a.disposal IS NULL OR a.disposal<>'trash') "
                     f"GROUP BY a.id,a.name,a.size,a.location,{PHOTO_DIR} "
                     f"ORDER BY {order} LIMIT ? OFFSET ?",
                     (row["id"], limit, offset),
                 )]
        return {
            "kind": kind, "name": row["canonical_name"], "entity_id": row["id"],
            "sets": sets, "total": total, "items": items, "seed": seed,
            "has_more": offset + len(items) < total,
        }


def q_photo_set(contract: WebContract, args):
    """一个图集里的图片。默认按文件名排，`001.jpg` 这类编号才不会乱序；带种子时按种子
    打散，那是「换一批」，翻页沿用同一粒。"""
    try:
        set_id = int(args.get("id", ""))
    except (TypeError, ValueError):
        return {"error": "invalid id"}
    limit = max(1, min(int(args.get("limit") or 120), 600))
    offset = max(0, int(args.get("offset") or 0))
    seed = str(args.get("seed") or "")
    order = seeded_order(seed) if seed else "a.name,a.id"
    with contract.read_connection() as c:
        anchor = c.execute(
            "SELECT id,location,path,name FROM asset "
            "WHERE id=? AND medium='image' AND name IS NOT NULL", (set_id,),
        ).fetchone()
        if not anchor:
            return {"error": "not found"}
        directory = anchor["path"][: len(anchor["path"]) - len(anchor["name"]) - 1]
        par = (directory, anchor["location"])
        total = c.execute(
            f"SELECT count(*) FROM asset a WHERE a.medium='image' AND a.name IS NOT NULL "
            f"AND {PHOTO_DIR}=? AND a.location=? "
            "AND (a.disposal IS NULL OR a.disposal<>'trash')", par,
        ).fetchone()[0]
        items = [{"id": item["id"], "name": item["name"], "size": item["size"] or 0,
                  "location": item["location"]}
                 for item in c.execute(
                     f"SELECT a.id,a.name,a.size,a.location FROM asset a WHERE a.medium='image' "
                     f"AND a.name IS NOT NULL AND {PHOTO_DIR}=? AND a.location=? "
                     "AND (a.disposal IS NULL OR a.disposal<>'trash') "
                     f"ORDER BY {order} LIMIT ? OFFSET ?",
                     (*par, limit, offset),
                 )]
        return {
            "id": anchor["id"], "title": photo_set_title(directory),
            "location": anchor["location"], "cost": COST.get(anchor["location"], "metered"),
            "total": total, "items": items, "seed": seed, "has_more": offset + len(items) < total,
        }


def q_index(contract: WebContract, kind, q="", limit=600, offset=0, category=""):
    """全部艺人 / 创作者 / 厂牌 / 事务所 / 标签的索引页数据。"""
    with contract.read_connection() as c:
        if kind == "agencies":
            # 事务所自己不挂作品，所以它排的是人：一家有多少艺人是它的规模，作品数是
            # 顺着成员算出来的。代表图也不取作品截图——那是某位成员某部片的画面，
            # 拿它当一家公司的门面，页面上就会是一张与这家公司无关的脸。
            sql = ("SELECT e.id entity_id,e.canonical_name k,"
                   "(SELECT count(*) FROM entity_membership m WHERE m.agency_id=e.id) members,"
                   "(SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae "
                   " JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND "
                   + scope_predicate("agency", "ae.entity_id", "e.id") + ") n,"
                   "(SELECT l.id FROM entity_link l WHERE l.entity_id=e.id"
                   " AND l.link_kind='official' ORDER BY l.id LIMIT 1) mark "
                   "FROM entity e WHERE e.kind='agency' ")
            par: list = []
            if q: sql += "AND e.canonical_name LIKE ? "; par.append(f"%{q}%")
            sql += "ORDER BY members DESC,n DESC,e.canonical_name LIMIT ? OFFSET ?"
            par.extend((limit + 1, offset))
            rows = [dict(r) for r in c.execute(sql, par)]
            has_more = len(rows) > limit
            rows = rows[:limit]
        elif kind in INDEX_ENTITY_KINDS:
            entity_kind = INDEX_ENTITY_KINDS[kind]
            sql = ("SELECT e.id entity_id,e.canonical_name k,count(DISTINCT ae.asset_id) n,"
                   "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
                   " WHERE ae2.entity_id=e.id AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
                   " ORDER BY COALESCE(a2.play_count,0) DESC,COALESCE(a2.play_seconds,0) DESC,"
                   " COALESCE(a2.width,0)*COALESCE(a2.height,0) DESC,a2.size DESC LIMIT 1) rep "
                   "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                   "JOIN asset a ON a.id=ae.asset_id "
                   "WHERE a.medium='video' AND e.kind=? ")
            par = [entity_kind]
            if q: sql += "AND e.canonical_name LIKE ? "; par.append(f"%{q}%")
            sql += "GROUP BY e.id,e.canonical_name ORDER BY n DESC LIMIT ? OFFSET ?"
            par.extend((limit + 1, offset))
            rows = [dict(r) for r in c.execute(sql, par)]
            has_more = len(rows) > limit
            rows = rows[:limit]
        else:
            sql = ("SELECT e.canonical_name k, count(DISTINCT ae.asset_id) n "
                   "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                   "JOIN asset a ON a.id=ae.asset_id WHERE a.medium='video' AND e.kind='tag' "
                   f"AND e.canonical_name NOT IN ({','.join('?' for _ in LENGTH_TAGS)}) "
                   "AND " + tag_is_not_a_performer_name("e.normalized_name") + " "
                   "AND " + tag_not_hidden("ae.asset_id", "e.normalized_name") + " ")
            par = sorted(LENGTH_TAGS)
            if q: sql += "AND e.canonical_name LIKE ? "; par.append(f"%{q}%")
            sql += "GROUP BY e.id,e.canonical_name ORDER BY n DESC"
            all_rows = [dict(r, cat=tag_cat(r["k"])) for r in c.execute(sql, par)]
            category_counts: dict[str, int] = {}
            for row in all_rows:
                category_counts[row["cat"]] = category_counts.get(row["cat"], 0) + 1
            if category and category != "all":
                all_rows = [row for row in all_rows if row["cat"] == category]
            rows = all_rows[offset:offset + limit]
            has_more = offset + limit < len(all_rows)
    if kind in INDEX_ENTITY_KINDS:
        entity_kind = INDEX_ENTITY_KINDS[kind]
        # 索引页一屏几十个圆头像，走的是和顶栏那排同一条两级链：规范实体图优先，
        # 取不到才回落到代表作头像。没有这两个标志就只能无条件出图、等 404 再把图摘掉，
        # `/performers` 桌面视口滚三屏实测 77 个取图请求里 5 个是这样的 404。
        # 判定在库连接之外做，它读的是目录索引而不是账本。
        for row in rows:
            row["has_image"] = contract.has_entity_image(entity_kind, row.get("entity_id"))
        attach_avatar_availability(contract, rows)
        #: 索引页的大图版式把头像裁成竖幅，几何居中会切掉脸。取景与资料页大图同一份
        #: sidecar、同一个换算，只是这里按行取；读的是文件，所以放在连接之外。
        for row in rows:
            row["avatar_focus"] = contract.avatar_focus(entity_kind, row["entity_id"])
        #: 公司的门面是它的标识，和资料页大位同一条链：`/logo` 优先，取不到才退回实体图。
        #: 索引页一屏几十格，缺了这个标志就只能格格出 `<img>` 等 404。
        if entity_kind in ("studio", "agency"):
            for row in rows:
                row["has_logo"] = contract.has_logo(row["k"])
    result = {"kind": kind, "items": rows, "has_more": has_more}
    if kind == "tags":
        result["categories"] = category_counts
    return result


#: 补全每组的条数上限。下拉栏还要同时装搜索记录，每组给满五条已经会把靠后的组
#: 推到需要滚动的位置。
SUGGEST_GROUP_LIMIT = 5

#: 补全的分组顺序与显示名，顺序就是下拉栏里的先后。它只定在这里，界面照抄——
#: 两侧各排一次的话，改了一侧就会出现「后端认为最该先看的组显示在第三位」。
#: 作品垫底：它的值是番号或整句标题，扫读成本比一个人名高。
SUGGEST_GROUPS = (
    ("performer", "女优"), ("creator", "创作者"), ("studio", "厂牌"),
    ("agency", "事务所"), ("series", "系列"), ("tag", "标签"), ("asset", "作品"),
)

#: 直接挂在作品上的实体种类。事务所不在内：`asset_entity` 里没有它的行，
#: 作品是它的成员拍的，所以它单走一条查询。
SUGGEST_ENTITY_KINDS = ("performer", "creator", "studio", "series", "tag")

#: 拉丁短输入按词首比的字符数门槛。两个字母做子串比，命中的多半是别的词中间那
#: 两个字母：真实账本上「MO」会捞出 `kemonokai`，「Pr」会捞出 `chf3_prob4`，而用户
#: 在打的是 MOODYZ 和 Prestige。
SUGGEST_WORD_HEAD_BELOW = 3


def _suggest_patterns(query: str) -> dict[str, str]:
    """这段输入该按什么形状去比。

    拉丁文字的词有词首，所以短输入比词首——整串开头，或某个空格之后。汉字和假名
    没有分词空格，人名与标签本来就出现在名字中间，那一侧照旧按子串，否则「凉森」
    这种两字输入会连自己都补不出来。

    补全按这两种形状取词，`/api/items` 一律按子串找片，所以补全给出的是搜索命中的
    一个子集——反过来不成立才是问题：那意味着下拉里的词点下去是空的。
    """
    prefix = f"{query}%"
    if len(query) < SUGGEST_WORD_HEAD_BELOW and query.isascii():
        return {"head": prefix, "tail": f"% {query}%", "prefix": prefix}
    contains = f"%{query}%"
    return {"head": contains, "tail": contains, "prefix": prefix}


def _suggest_like(column: str) -> str:
    """一列与这段输入的比较。两个占位符是同一件事的两种形状，见 `_suggest_patterns`。"""
    return f"({column} LIKE :head OR {column} LIKE :tail)"


#: 一个实体被这段输入命中的三条路，与 `/api/items` 的搜索同源：规范名、别名、检索词。
#: 少认一条的后果是两个方向的落空——补出来的词搜不到，或者搜得到的词补不出来。
SUGGEST_ENTITY_MATCH = (
    "(" + _suggest_like("e.canonical_name")
    + " OR EXISTS(SELECT 1 FROM entity_alias al WHERE al.entity_id=e.id"
    " AND " + _suggest_like("al.alias") + ")"
    " OR EXISTS(SELECT 1 FROM entity_search_term st WHERE st.entity_id=e.id"
    " AND " + _suggest_like("st.term") + "))"
)

#: 命中的是哪个写法。规范名自己命中时留空——那一项显示的就是规范名，再标一次
#: 等于把「涼森れむ（涼森れむ）」摆到用户面前。命中别名或检索词才有话要说：
#: 用户输入「凉森」，看到的一行是「涼森れむ」，不说凭什么，他会以为补错了人。
SUGGEST_MATCHED = (
    "CASE WHEN " + _suggest_like("e.canonical_name") + " THEN '' ELSE COALESCE("
    "(SELECT al.alias FROM entity_alias al WHERE al.entity_id=e.id"
    " AND " + _suggest_like("al.alias") + " LIMIT 1),"
    "(SELECT st.term FROM entity_search_term st WHERE st.entity_id=e.id"
    " AND " + _suggest_like("st.term") + " LIMIT 1),'') END matched"
)


def _suggest_entity_rows(connection, params):
    """直接挂着作品的实体，按名下作品数排，前缀命中的排在前面。"""
    length_keys = {f"lt{index}": tag for index, tag in enumerate(sorted(LENGTH_TAGS))}
    kinds = ",".join(f"'{kind}'" for kind in SUGGEST_ENTITY_KINDS)
    sql = (
        "SELECT e.kind kind, e.canonical_name k, count(DISTINCT ae.asset_id) n, "
        + SUGGEST_MATCHED + " FROM entity e "
        "JOIN asset_entity ae ON ae.entity_id=e.id JOIN asset a ON a.id=ae.asset_id "
        "WHERE " + VISIBLE_CATALOG_ASSET + f" AND e.kind IN ({kinds}) "
        "AND " + SUGGEST_ENTITY_MATCH + " "
        # 标签沿用标签榜的可见性：时长标签是筛选控件而不是词，与女优同名的标签是
        # 另一个身份的冒充，被隐藏的标签用户已经说过不想看见。
        "AND (e.kind<>'tag' OR (e.canonical_name NOT IN ("
        + ",".join(f":{key}" for key in length_keys) + ") AND "
        + tag_is_not_a_performer_name("e.normalized_name") + " AND "
        + tag_not_hidden("ae.asset_id", "e.normalized_name") + ")) "
        "GROUP BY e.id ORDER BY "
        "CASE WHEN e.canonical_name LIKE :prefix THEN 0 ELSE 1 END, n DESC, e.canonical_name"
    )
    return connection.execute(sql, {**params, **length_keys}).fetchall()


def _suggest_agency_rows(connection, params):
    """事务所的规模顺着成员算，判据与它的资料页、索引页同一份。

    名下一部作品都没有的事务所不进补全：账本里有它的身份，但按它搜出来是空的。
    """
    sql = (
        "SELECT * FROM (SELECT 'agency' kind, e.canonical_name k, "
        "(SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae "
        " JOIN asset a ON a.id=ae.asset_id WHERE " + VISIBLE_CATALOG_ASSET + " AND "
        + scope_predicate("agency", "ae.entity_id", "e.id") + ") n, "
        + SUGGEST_MATCHED + " FROM entity e WHERE e.kind='agency' AND "
        + SUGGEST_ENTITY_MATCH + ") WHERE n>0 "
        "ORDER BY CASE WHEN k LIKE :prefix THEN 0 ELSE 1 END, n DESC, k"
    )
    return connection.execute(sql, params).fetchall()


def _suggest_asset_rows(connection, params, limit):
    """作品这一组给的是「打开这一条」，不是一个搜索词。

    番号是可搜的短词，整句标题不是：把一整行带全角括号和空格的标题填回搜索框，
    下一次搜索会因为其中任何一个字符对不上而落空。所以这一组带上 id，由界面
    直接开详情，而不是绕一趟搜索。

    文件名排在最后一档。它是存储事实而不是这部片叫什么，命中它的多半是扩展名和
    转码标记：真实账本上「MO」会从文件名里捞出 `IMG_2757_682.MOV` 和一条标题里
    带 `MOVIE版` 的转码文件。番号和发行标题够五条时它就不露面。
    """
    named = (
        "(" + _suggest_like("a.code") + " OR " + _suggest_like("a.catalog_title")
        + " OR " + _suggest_like("a.original_title") + ")"
    )
    sql = (
        "SELECT a.id id, COALESCE(a.code,'') code, COALESCE(a.catalog_title,'') title, "
        "COALESCE(a.name,'') name FROM asset a WHERE " + VISIBLE_CATALOG_ASSET
        + " AND (" + named + " OR " + _suggest_like("a.name") + ") "
        "ORDER BY CASE WHEN a.code LIKE :prefix THEN 0 WHEN " + named + " THEN 1 "
        "ELSE 2 END, COALESCE(a.play_count,0) DESC, a.id DESC LIMIT :limit"
    )
    return connection.execute(sql, {**params, "limit": limit}).fetchall()


def _asset_display_name(name: str) -> str:
    """文件名去掉扩展名。`.mp4` 是存储事实，不是这部片叫什么。

    去掉之后它仍是 `asset.name` 的子串，所以拿它去搜照样命中这一条。
    """
    head, _, tail = name.rpartition(".")
    return head if head and len(tail) <= 4 else name


def q_suggest(contract: WebContract, q: str, limit: int = SUGGEST_GROUP_LIMIT):
    """搜索栏下拉的补全：给一段输入，返回馆藏里点得开的身份与作品。

    「点得开」不是靠调用方逐条验一遍达成的，是判据本身与 `/api/items` 同源：
    可见性用的是同一个 `VISIBLE_CATALOG_ASSET`，命中的三条路是搜索 LIKE 分支的
    那三条，实体行来自实际挂着作品的 join。所以这里返回的每一项，按它的 `value`
    去搜都有结果——补全与搜索口径漂开，比没有补全更难查。
    """
    query = (q or "").strip()
    if not query:
        return {"q": "", "groups": []}
    per_group = max(1, min(int(limit), SUGGEST_GROUP_LIMIT * 4))
    params = _suggest_patterns(query)
    with contract.read_connection() as connection:
        entities = [dict(row) for row in _suggest_entity_rows(connection, params)]
        entities += [dict(row) for row in _suggest_agency_rows(connection, params)]
        assets = [dict(row) for row in _suggest_asset_rows(connection, params, per_group)]
    buckets: dict[str, list[dict]] = {}
    for row in entities:
        bucket = buckets.setdefault(row["kind"], [])
        if len(bucket) < per_group:
            bucket.append({"value": row["k"], "n": row["n"],
                           "matched": row["matched"], "id": None})
    buckets["asset"] = [{
        # 番号优先：它既是这条作品的名字，也是一个搜得到的短词。没有番号的
        # 才退到发行标题，最后才是文件名——文件名是最不像「这部片叫什么」的
        # 那个写法。
        "value": row["code"] or row["title"] or _asset_display_name(row["name"]),
        "n": 0, "matched": "", "id": row["id"],
    } for row in assets]
    return {"q": query, "groups": [
        {"kind": kind, "label": label, "items": buckets[kind]}
        for kind, label in SUGGEST_GROUPS if buckets.get(kind)
    ]}


#: 用户在资料页选定统称时，被换下的旧规范名记这个来源。合并留的是 `merge:*`，
#: 刮削留的是站点名；分得开才答得出「这个名字是谁定的」。
PREFERRED_NAME_SOURCE = "user:preferred-name"

def w_entity_name(contract: WebContract, body):
    """把这个实体已有的某个名字提为统称，旧规范名转成别名。

    统称就是 `entity.canonical_name`，它是真相字段。所以这里只做「换一个已经在
    这条实体名下的名字」：候选必须是现在的规范名或它的别名之一，不收自由文本——
    自由文本是改名，那要有来源和证据，不是一次点击该干的事。

    规范名唯一（`entity(kind, normalized_name)`），选中的名字若已经是另一条实体的
    规范名，这里只报冲突。那种情况要么是两条该合并，要么是同名不同人，都得人来判。

    这是可逆的：把换下来的那个再选回去就还原了。
    """
    contract.cache_bust()
    kind = str(body.get("kind", "")).strip()
    name = str(body.get("name", "")).strip()
    chosen = str(body.get("canonical", "")).strip()
    if kind not in PROFILE_KINDS or not name:
        raise ValueError("kind must be a known entity kind and name is required")
    if not chosen:
        raise ValueError("canonical is required")
    with contract.write_transaction() as c:
        row = resolve_entity(c, kind, name)
        if not row:
            raise ValueError("entity not found")
        entity_id, current = int(row["id"]), str(row["canonical_name"])
        chosen_key = normalize_entity_name(chosen)
        if chosen_key == normalize_entity_name(current):
            return {"ok": True, "canonical_name": current, "changed": False}
        known = {normalize_entity_name(str(item[0])): str(item[0]) for item in c.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=?", (entity_id,))}
        if chosen_key not in known:
            raise ValueError("canonical must be one of this entity's existing names")
        taken = c.execute(
            "SELECT canonical_name FROM entity WHERE kind=? AND normalized_name=? AND id<>?",
            (kind, chosen_key, entity_id)).fetchone()
        if taken:
            raise ValueError(f"another {kind} is already named {taken[0]}")
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        c.execute(
            "UPDATE entity SET canonical_name=?,normalized_name=?,updated_at=? WHERE id=?",
            (known[chosen_key], chosen_key, stamp, entity_id))
        # 旧规范名留成别名：它是这个人真的用过的名字，也是选回去的入口。
        c.execute(
            "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
            " VALUES(?,?,?,?,1.0)",
            (entity_id, current, normalize_entity_name(current), PREFERRED_NAME_SOURCE))
        flat = rewrite_flat_projection(c, kind, entity_id, current, known[chosen_key])
        return {"ok": True, "canonical_name": known[chosen_key], "changed": True,
                "previous_name": current, "flat_rewritten": flat}
