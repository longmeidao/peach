"""实体资料页：女优／厂牌／创作者／系列的聚合，以及它们的图集与索引页。

实体是 ledger 的规范身份（见 AGENTS.md 术语表），扁平的 `asset_tag`、creator/studio
字段只是兼容投影。这一域负责把两者合成一页：别名归并、代表作、图集分组、索引分类。

它 import `web_catalog` 的可见性谓词，而不是自己写一份——女优页上该不该出现某个标签，
必须和首页是同一个判据。
"""
from __future__ import annotations

import json
import re

from urllib.parse import urlsplit

from .catalog_rules import LENGTH_TAGS, dir_expr, photo_set_title, tag_cat
from .entities import normalize_entity_name, resolve_entity
from .web_catalog import (
    COST,
    attach_avatar_availability,
    tag_is_not_a_performer_name,
    tag_not_hidden,
)
from .web_state import WebContract


def q_entity(contract: WebContract, args):
    """女优、厂牌、创作者等实体的资料页。

    `source_reference` 是私人馆藏来源证据：API 只返回站点名和备注，不把敏感下载
    地址变成可点击链接。官方、社交和资料库链接可直接访问。
    """
    kind = args.get("kind", "")
    name = args.get("name", "")
    if kind not in {"performer", "studio", "creator", "series"} or not name:
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
        d["aliases"] = [r[0] for r in c.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=? ORDER BY confidence DESC,alias",
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
        count, rep = c.execute(
            "SELECT count(DISTINCT ae.asset_id),"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE ae2.entity_id=? AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY a2.size DESC LIMIT 1) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE ae.entity_id=? AND a.medium='video'", (d["id"], d["id"]),
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
            "WHERE scope.entity_id=? AND a.medium='video' AND tag.kind='tag' "
            "AND " + tag_is_not_a_performer_name("tag.normalized_name") + " "
            f"AND tag.canonical_name NOT IN ({','.join('?' for _ in LENGTH_TAGS)}) "
            "AND " + tag_not_hidden("scope.asset_id", "tag.normalized_name") + " "
            "GROUP BY tag.id,tag.canonical_name ORDER BY n DESC,tag.canonical_name LIMIT 36",
            (d["id"], *sorted(LENGTH_TAGS)),
        )]
        related = []
        for performer in c.execute(
            "SELECT person.id,person.canonical_name k,count(DISTINCT scope.asset_id) n,"
            "(SELECT a2.id FROM asset_entity ae2 JOIN asset a2 ON a2.id=ae2.asset_id "
            " WHERE ae2.entity_id=person.id AND a2.medium='video' AND a2.snapshot_path IS NOT NULL "
            " ORDER BY COALESCE(a2.play_count,0) DESC,COALESCE(a2.play_seconds,0) DESC,"
            " COALESCE(a2.width,0)*COALESCE(a2.height,0) DESC,a2.size DESC LIMIT 1) rep "
            "FROM asset_entity scope "
            "JOIN asset_entity co ON co.asset_id=scope.asset_id "
            "JOIN entity person ON person.id=co.entity_id "
            "JOIN asset a ON a.id=scope.asset_id "
            "WHERE scope.entity_id=? AND a.medium='video' AND person.kind='performer' "
            "AND person.id<>? "
            "GROUP BY person.id,person.canonical_name ORDER BY n DESC,person.canonical_name LIMIT 18",
            (d["id"], d["id"]),
        ):
            related.append(dict(performer))
        d["related_performers"] = related
    # 厂牌页那个大位先取 `/logo`、取不到才退到实体图。没装标识时直接从实体图起步，
    # 省掉必然 404 的那一跳；别的实体没有这个位置，标志只对厂牌成立。
    if kind == "studio":
        d["has_logo"] = contract.has_logo(d["canonical_name"])
    # 大位那条链的后两环同样要随资料下发：实体图取不到就直接从代表作头像起步，两样
    # 都取不到就一个 `<img>` 都不出。判定在库连接之外做，它读的是目录索引。
    d["has_image"] = contract.has_entity_image(kind, d["id"])
    attach_avatar_availability(contract, [d], key="representative_asset_id")
    # 页脚那排共演者是同一个圆头像，用的也是同一条两级链。
    for person in d["related_performers"]:
        person["has_image"] = contract.has_entity_image("performer", person["id"])
    attach_avatar_availability(contract, d["related_performers"])
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
    if kind not in {"performer", "studio", "creator", "series"} or not name:
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
            "WHERE ae.entity_id=? AND a.medium='image' AND a.name IS NOT NULL "
            "AND (a.disposal IS NULL OR a.disposal<>'trash') "
            f"GROUP BY {PHOTO_DIR},a.location ORDER BY n DESC,dir",
            (row["id"],),
        )]
        total = c.execute(
            "SELECT count(DISTINCT a.id) "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            "WHERE ae.entity_id=? AND a.medium='image' AND a.name IS NOT NULL "
            "AND (a.disposal IS NULL OR a.disposal<>'trash')",
            (row["id"],),
        ).fetchone()[0]
        items = [{"id": item["id"], "name": item["name"], "size": item["size"] or 0,
                  "location": item["location"]}
                 for item in c.execute(
                     f"SELECT a.id,a.name,a.size,a.location,{PHOTO_DIR} dir "
                     "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
                     "WHERE ae.entity_id=? AND a.medium='image' AND a.name IS NOT NULL "
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
    """全部艺人 / 创作者 / 标签的索引页数据。"""
    with contract.read_connection() as c:
        if kind in {"creators", "performers"}:
            entity_kind = "creator" if kind == "creators" else "performer"
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
    if kind in {"creators", "performers"}:
        entity_kind = "creator" if kind == "creators" else "performer"
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
    result = {"kind": kind, "items": rows, "has_more": has_more}
    if kind == "tags":
        result["categories"] = category_counts
    return result
