"""实体事实的种子包：一台机器账本里的公开事实随仓库走，另一台机器只给已有实体填空（ADR-0073）。

导出的是女优、厂牌与事务所名下**能在公开站点上重新查到**的文字事实：别名、站上编号、
官网与社媒链接、女优资料表、所属事务所。不导任何图像字节、本机路径、刮削残片
（`entity.metadata_json`、资料的 `raw_json`、链接的 `evidence`）与 Stash 的编号——那些
要么是本机的，要么是别的用户账本里不可能对上的。

导入按 ADR-0024 第五条：不造实体。包里的一位女优只有在本机账本已经登记了她（规范名、
别名或站上编号对得上）时才补，补的每一格都是空格（ADR-0052 第三条），归属串 `auto:seed`、
批次 `auto:seed@<版本>`，`scripts/revert_auto_landing.py --source auto:seed` 整批撤回。
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .entities import _ref_is_free, normalize_entity_name
from .minnano_av import PROFILE_COLUMNS
from .performer_profiles import read_profile, write_profile
from .settings_file import PROJECT_ROOT
from .social_links import canonical_url

FORMAT = 1
SOURCE = "auto:seed"
DEFAULT_PACK = PROJECT_ROOT / "resources" / "seed" / "entities.json"
#: 导出的实体种类。创作者、系列与标签是本机馆藏的投影，不在这里。
KINDS = ("performer", "studio", "agency")
#: 不导的站上编号：Stash 的 id 是那台机器上另一份数据库的行号。
EXCLUDED_PROVIDERS = frozenset({"stash"})
#: 导出的链接类型：目录页与来源引用是采集残迹，不是这个人或这家公司自己的地址。
LINK_KINDS = ("official", "social")
COUNT_KEYS = ("entities", "aliases", "refs", "links", "profiles", "memberships")


def batch_of(version: str) -> str:
    return f"{SOURCE}@{version}"


def _ours(source: object) -> bool:
    text = str(source or "")
    return text == SOURCE or text.startswith(SOURCE + "@")


def _metadata_ours(raw: object) -> bool:
    try:
        metadata = json.loads(str(raw or "{}"))
    except ValueError:
        return False
    return isinstance(metadata, dict) and _ours(metadata.get("source"))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- 导出 ----------------------------------------------------------------------


def _aliases(connection: sqlite3.Connection, entity_id: int) -> list[dict]:
    """名下的别名写法，同一写法只留排在前面的那个来源；种子自己写的不再导出。"""
    found: dict[str, dict] = {}
    for alias, source in connection.execute(
            "SELECT alias,source FROM entity_alias WHERE entity_id=? ORDER BY normalized_alias,source",
            (entity_id,)):
        if _ours(source) or not str(alias or "").strip():
            continue
        found.setdefault(normalize_entity_name(str(alias)), {"alias": str(alias), "source": str(source)})
    return list(found.values())


def _refs(connection: sqlite3.Connection, entity_id: int) -> list[dict]:
    return [{"provider": str(provider), "kind": str(kind), "id": str(external_id)}
            for provider, kind, external_id, metadata in connection.execute(
                "SELECT provider,external_kind,external_id,metadata_json FROM entity_external_ref"
                " WHERE entity_id=? ORDER BY provider,external_kind,external_id", (entity_id,))
            if provider not in EXCLUDED_PROVIDERS and not _metadata_ours(metadata)]


def _links(connection: sqlite3.Connection, entity_id: int) -> list[dict]:
    marks = ",".join("?" * len(LINK_KINDS))
    return [{"kind": str(kind), "label": str(label), "url": str(url)}
            for kind, label, url, metadata in connection.execute(
                f"SELECT link_kind,label,url,metadata_json FROM entity_link WHERE entity_id=?"
                f" AND is_sensitive=0 AND link_kind IN ({marks}) ORDER BY url", (entity_id, *LINK_KINDS))
            if not _metadata_ours(metadata)]


def _profile(connection: sqlite3.Connection, entity_id: int) -> dict | None:
    """资料表按列导出，`raw` 是刮削残片不导；种子自己写的那一行不再导出。"""
    found = read_profile(connection, entity_id)
    if found is None or _ours(found.get("source")):
        return None
    fields = {column: found[column] for column in PROFILE_COLUMNS if found.get(column) is not None}
    fields["tags"] = list(found.get("tags") or [])
    return {"fields": fields, "source": str(found["source"]), "source_url": str(found["source_url"]),
            "fetched_at": str(found["fetched_at"])}


def _agency(connection: sqlite3.Connection, entity_id: int) -> dict | None:
    row = connection.execute(
        "SELECT a.canonical_name,m.source FROM entity_membership m JOIN entity a ON a.id=m.agency_id"
        " WHERE m.member_id=?", (entity_id,)).fetchone()
    if row is None or _ours(row[1]):
        return None
    return {"name": str(row[0]), "source": str(row[1])}


def export_pack(connection: sqlite3.Connection, *, version: str) -> dict:
    """账本里三类实体的公开事实。只有名字、没有任何可补事实的实体不进包：导入不造实体，
    光一个名字对别的账本没有用处。输出按种类与归一名排序，同一账本两次导出逐字节一致。"""
    entities, counts = [], dict.fromkeys(COUNT_KEYS, 0)
    for entity_id, kind, name in connection.execute(
            f"SELECT id,kind,canonical_name FROM entity WHERE kind IN ({','.join('?' * len(KINDS))})"
            " ORDER BY kind,normalized_name,id", KINDS):
        item = {"kind": str(kind), "name": str(name), "aliases": _aliases(connection, entity_id),
                "refs": _refs(connection, entity_id), "links": _links(connection, entity_id)}
        if kind == "performer":
            profile, agency = _profile(connection, entity_id), _agency(connection, entity_id)
            if profile:
                item["profile"] = profile
            if agency:
                item["agency"] = agency
        if not (item["aliases"] or item["refs"] or item["links"] or "profile" in item or "agency" in item):
            continue
        entities.append(item)
        counts["entities"] += 1
        counts["aliases"] += len(item["aliases"])
        counts["refs"] += len(item["refs"])
        counts["links"] += len(item["links"])
        counts["profiles"] += "profile" in item
        counts["memberships"] += "agency" in item
    return {"format": FORMAT, "version": version, "source": SOURCE, "counts": counts, "entities": entities}


def dump(pack: dict) -> str:
    """落盘形态：键有序、一层缩进，改一位女优只动她那几行。"""
    return json.dumps(pack, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def load(path) -> dict:
    pack = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(pack, dict) or pack.get("format") != FORMAT or not pack.get("version"):
        raise ValueError(f"{path} 不是格式 {FORMAT} 的种子包")
    return pack


# -- 导入 ----------------------------------------------------------------------


def match_entity(connection: sqlite3.Connection, item: dict) -> int | None:
    """包里这一条对应本机哪个实体：规范名、每个写法、每个站上编号各自去认，认出来的必须是同一位。

    认出两位就返回 None，哪怕其中一位是规范名逐字相同：名字对上 A、编号却挂在 B 名下，说明
    本机账本里这两条里至少有一条是错的，指错人比漏补糟得多，这样的留给人看。"""
    kind = item["kind"]
    keys = [normalize_entity_name(name) for name in
            (item["name"], *(alias["alias"] for alias in item.get("aliases") or []))]
    marks = ",".join("?" * len(keys))
    found = {int(row[0]) for row in connection.execute(
        f"SELECT id FROM entity WHERE kind=? AND normalized_name IN ({marks})"
        f" UNION SELECT e.id FROM entity e JOIN entity_alias a ON a.entity_id=e.id"
        f" WHERE e.kind=? AND a.normalized_alias IN ({marks})", (kind, *keys, kind, *keys))}
    refs = [ref for ref in item.get("refs") or [] if ref["provider"] not in EXCLUDED_PROVIDERS]
    if refs:
        clause = " OR ".join("(r.provider=? AND r.external_kind=? AND r.external_id=?)" for _ in refs)
        values = [value for ref in refs for value in (ref["provider"], ref["kind"], ref["id"])]
        found |= {int(row[0]) for row in connection.execute(
            f"SELECT e.id FROM entity_external_ref r JOIN entity e ON e.id=r.entity_id"
            f" WHERE e.kind=? AND ({clause})", (kind, *values))}
    return found.pop() if len(found) == 1 else None


def _land_aliases(connection, entity_id: int, item: dict, version: str, batch: str) -> int:
    """女优别名走补别名后继的判据（ADR-0055：不收的写法、已有、被占用）；厂牌与事务所
    只查同类实体里有没有人用着这个写法。"""
    names = [item["name"], *(alias["alias"] for alias in item.get("aliases") or [])]
    if item["kind"] == "performer":
        from .performer_alias_followup import WRITE, land
        canonical = connection.execute("SELECT canonical_name FROM entity WHERE id=?", (entity_id,)).fetchone()
        rows = land(connection, entity_id, str(canonical[0]), "seed", f"{SOURCE}:{version}", names, batch)
        return sum(row["action"] == WRITE for row in rows)
    written = 0
    for name in dict.fromkeys(names):
        key = normalize_entity_name(name)
        taken = connection.execute(
            "SELECT 1 FROM entity WHERE kind=? AND normalized_name=?"
            " UNION SELECT 1 FROM entity_alias a JOIN entity e ON e.id=a.entity_id"
            " WHERE e.kind=? AND a.normalized_alias=?", (item["kind"], key, item["kind"], key)).fetchone()
        if taken is None and key:
            connection.execute(
                "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
                " VALUES(?,?,?,?,1.0)", (entity_id, name, key, batch))
            written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def _land_refs(connection, entity_id: int, item: dict, batch: str, stamp: str) -> int:
    """站上编号只在这个编号没人登记、这位在这家来源下也还没有编号时写：现成的
    `ON CONFLICT … DO UPDATE` 会把别人的编号改指到她，这里不用它。"""
    written = 0
    for ref in item.get("refs") or []:
        if ref["provider"] in EXCLUDED_PROVIDERS:
            continue
        held = connection.execute(
            "SELECT 1 FROM entity_external_ref WHERE provider=? AND external_kind=? AND external_id=?",
            (ref["provider"], ref["kind"], ref["id"])).fetchone()
        if held is not None or not _ref_is_free(connection, entity_id, ref["provider"], ref["kind"], ref["id"]):
            continue
        connection.execute(
            "INSERT OR IGNORE INTO entity_external_ref(entity_id,provider,external_kind,external_id,"
            "metadata_json,last_synced_at) VALUES(?,?,?,?,?,?)",
            (entity_id, ref["provider"], ref["kind"], ref["id"],
             json.dumps({"source": SOURCE, "batch": batch}, ensure_ascii=False), stamp))
        written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def _land_links(connection, entity_id: int, item: dict, batch: str, stamp: str) -> int:
    written = 0
    for link in item.get("links") or []:
        url = str(link.get("url") or "").strip()
        if not url or link.get("kind") not in LINK_KINDS:
            continue
        url = canonical_url(url if urlsplit(url).scheme else "https://" + url)
        connection.execute(
            "INSERT OR IGNORE INTO entity_link(entity_id,link_kind,label,url,hostname,is_sensitive,"
            "metadata_json,created_at,updated_at) VALUES(?,?,?,?,?,0,?,?,?)",
            (entity_id, link["kind"], str(link.get("label") or urlsplit(url).hostname or url), url,
             urlsplit(url).hostname or "", json.dumps({"source": SOURCE, "batch": batch}, ensure_ascii=False),
             stamp, stamp))
        written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def _land_profile(connection, entity_id: int, item: dict, batch: str) -> int:
    """资料只给没有资料的那位写：`write_profile` 会整行替换自动来源的行，本机后继刚刮的
    比种子新，不能被盖掉。"""
    profile = item.get("profile")
    if not profile or item["kind"] != "performer" or read_profile(connection, entity_id) is not None:
        return 0
    fields = dict(profile.get("fields") or {})
    fields["raw"] = {}
    return int(write_profile(connection, entity_id, fields, source=batch,
                             source_url=str(profile.get("source_url") or ""),
                             fetched_at=str(profile.get("fetched_at") or "") or None))


def _land_membership(connection, entity_id: int, item: dict, batch: str, stamp: str) -> int:
    """所属事务所只在本机已经有这家事务所、这位又还没有归属时写；不造事务所实体。"""
    agency = item.get("agency")
    if not agency or item["kind"] != "performer":
        return 0
    if connection.execute("SELECT 1 FROM entity_membership WHERE member_id=?", (entity_id,)).fetchone():
        return 0
    agency_id = match_entity(connection, {"kind": "agency", "name": agency["name"]})
    if agency_id is None:
        return 0
    connection.execute(
        "INSERT OR IGNORE INTO entity_membership(member_id,agency_id,source,confidence,checked_at)"
        " VALUES(?,?,?,1.0,?)", (entity_id, agency_id, batch, stamp))
    return connection.execute("SELECT changes()").fetchone()[0]


def land(connection: sqlite3.Connection, pack: dict) -> dict:
    """把包里的事实补进这本账，返回逐类计数。调用方负责事务与备份；dry-run 走 `plan`。"""
    version, batch, stamp = str(pack["version"]), batch_of(str(pack["version"])), _now()
    report = {"version": version, "batch": batch, "matched": 0, "unmatched": 0,
              **dict.fromkeys(COUNT_KEYS[1:], 0)}
    for item in pack.get("entities") or []:
        entity_id = match_entity(connection, item)
        if entity_id is None:
            report["unmatched"] += 1
            continue
        report["matched"] += 1
        report["aliases"] += _land_aliases(connection, entity_id, item, version, batch)
        report["refs"] += _land_refs(connection, entity_id, item, batch, stamp)
        report["links"] += _land_links(connection, entity_id, item, batch, stamp)
        report["profiles"] += _land_profile(connection, entity_id, item, batch)
        report["memberships"] += _land_membership(connection, entity_id, item, batch, stamp)
    return report


def plan(connection: sqlite3.Connection, pack: dict) -> dict:
    """dry-run：在只读账本的内存副本上跑一遍 `land`，交出同样的计数，本机账本一字不动。"""
    scratch = sqlite3.connect(":memory:")
    try:
        connection.backup(scratch)
        scratch.execute("PRAGMA foreign_keys=ON")
        return land(scratch, pack)
    finally:
        scratch.close()
