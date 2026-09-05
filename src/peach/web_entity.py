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
    attach_avatar_availability,
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
    # 页脚那排共演者是同一个圆头像，用的也是同一条两级链。
    for person in d["related_performers"]:
        person["has_image"] = contract.has_entity_image("performer", person["id"])
    attach_avatar_availability(contract, d["related_performers"])
    if kind == "agency":
        # 事务所页默认摆的是艺人大图，那个版式把头像裁成竖幅，几何居中会切掉脸。
        # 取景与索引页大图同一份 sidecar、同一个换算，别的页面那排小圆头像用不上。
        for person in d["related_performers"]:
            person["avatar_focus"] = contract.avatar_focus("performer", person["id"])
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
    """实体名下的图片瀑布流；目录分组只保留为兼容元数据。"""
    kind, name = args.get("kind", ""), args.get("name", "")
    if kind not in PROFILE_KINDS or not name:
        return {"error": "invalid entity"}
    try:
        limit = max(1, min(int(args.get("limit") or 120), 600))
        offset = max(0, int(args.get("offset") or 0))
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
                     "ORDER BY dir,a.name,a.id LIMIT ? OFFSET ?",
                     (row["id"], limit, offset),
                 )]
        return {
            "kind": kind, "name": row["canonical_name"], "entity_id": row["id"],
            "sets": sets, "total": total, "items": items,
            "has_more": offset + len(items) < total,
        }


def q_photo_set(contract: WebContract, args):
    """一个图集里的图片。按文件名排，`001.jpg` 这类编号才不会乱序。"""
    try:
        set_id = int(args.get("id", ""))
    except (TypeError, ValueError):
        return {"error": "invalid id"}
    limit = max(1, min(int(args.get("limit") or 120), 600))
    offset = max(0, int(args.get("offset") or 0))
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
                     "ORDER BY a.name,a.id LIMIT ? OFFSET ?",
                     (*par, limit, offset),
                 )]
        return {
            "id": anchor["id"], "title": photo_set_title(directory),
            "location": anchor["location"], "cost": COST.get(anchor["location"], "metered"),
            "total": total, "items": items, "has_more": offset + len(items) < total,
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
