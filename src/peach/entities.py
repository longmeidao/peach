from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from sqlite3 import Connection


def normalize_entity_name(name: str) -> str:
    return strip_zero_width(name).strip().casefold()


KANA = re.compile(r"[぀-ゟ゠-ヿ]")
KANJI = re.compile(r"[一-鿿]")


def name_rank(name: str) -> int:
    """这个写法对日文站有多可用，越小越先试。

    账本里 performer 的规范名是简体中文（`凉森玲梦`、`释爱丽丝`），日文站按它一个都
    搜不到；真正能用的日文写法在 `entity_alias` 里（`涼森れむ`、`釈アリス`）。实测拿
    规范名直接搜，12 位只命中 1 位；改用日文写法后同样 12 位全中。

    汉字加假名混排的是艺名本身，最可靠；纯假名是读音，能搜到但更容易撞名；纯汉字既可能
    是日文也可能是简体中文，放在后面；罗马字对日文站基本无效，排最后。
    """
    kana, kanji = bool(KANA.search(name)), bool(KANJI.search(name))
    if kana and kanji:
        return 0
    if kana:
        return 1
    if kanji:
        return 2
    return 3


def name_chain(canonical: str, aliases: list[str]) -> list[str]:
    """去重后按可用程度排序的候选名字，罗马字不进链。

    罗马字留着只会白跑一次往返，并且它落空后混进未取得，看起来像是「这个人查不到」，
    而实际上是「我们从没用她的日文名查过」。

    放在实体层而不是某个脚本里：`harvest_performer_links` 和 `rediscover_entity_links`
    都要用它。此前它住在前者、后者靠改 `sys.path` 反向 import——依赖门槛把它算成外部
    模块是对的，那种导入既依赖 path 顺序，工具也读不懂。
    """
    seen: list[str] = []
    for name in [canonical, *aliases]:
        name = (name or "").strip()
        if name and name not in seen and name_rank(name) < 3:
            seen.append(name)
    return sorted(seen, key=name_rank)


PERSON_ENTITY_KINDS = frozenset({"creator", "performer"})
INVALID_PERSON_ENTITY_NAMES = frozenset({"画像を拡大する"})


def collapse_repeated_entity_name(name: str) -> str:
    """把 ``姓名 姓名`` 这类完整重复串收敛为一次。

    这里只处理以空白分隔、前后两半完全相同的高置信错误；不会碰
    ``M M Produce``、无空白的叠字或带分隔符的内容标签。
    """
    original = str(name or "").strip()
    canonical = " ".join(original.split())
    parts = canonical.split(" ") if canonical else []
    half = len(parts) // 2
    if (len(parts) >= 2 and len(parts) % 2 == 0
            and [part.casefold() for part in parts[:half]]
            == [part.casefold() for part in parts[half:]]):
        return " ".join(parts[:half])
    return original


#: `Ako Momona (Kou Akemi, Mari Koizumi)` 这种一格装了三个艺名的写法。签名收得很紧：
#: 括号前有一个空格、括号内逗号分隔、整串只有拉丁字母与 `. ' -` 这几个名字里出现的标点。
#: 放宽任何一条都会误伤——`AV DEBUT（本物人妻）` 的括号里是厂牌消歧，`アスナ(SAO)` 是
#: 角色的出处，`快慢扳机（接稿中）` 是接稿状态，`kitty(1)` 是去重后缀。它们和艺名共用
#: 「名字后面跟一对括号」这个形状，只有「两侧都是罗马字人名」能把它们分开。
COMPOSITE_PERSON_NAME = re.compile(
    r"^([A-Za-z][A-Za-z .'-]*) \(([A-Za-z][A-Za-z .',-]*)\)$")


def split_composite_person_name(name: str) -> list[str]:
    """把 `现用名 (曾用名, 曾用名)` 拆成一个人的若干个名字，顺序保持原样、去重。

    r18.dev 的罗马字字段本身就是这个渲染格式，导入时一个字段写一行，于是整串成了一条
    别名。它做别名是死的：没有人叫「Ako Momona (Kou Akemi, Mari Koizumi)」，按任何一段
    都搜不到，选成统称更是不成立。同一条实体的假名和汉字写法本来就各自成行，缺的只是
    这几个罗马字。

    不匹配签名的原样返回一个元素，调用方不必先判断。
    """
    matched = COMPOSITE_PERSON_NAME.match(strip_zero_width(name).strip())
    if not matched:
        stripped = strip_zero_width(name).strip()
        return [stripped] if stripped else []
    parts = [matched.group(1).strip()]
    parts.extend(part.strip() for part in matched.group(2).split(","))
    unique: list[str] = []
    for part in parts:
        if part and part not in unique:
            unique.append(part)
    return unique


#: 规范名里要剥掉的零宽字符。上游译名夹带过 `‌斋藤亚美里`（performer）和
#: `比特ビット‌`（creator）：页面上和普通名字一模一样，但 `strip()` 不认它们不是
#: 空白，`normalized_name` 也就带着它，于是同一个人在账本里能存成两个实体、按名字搜
#: 一个都搜不到。U+200D（ZWJ）不在名单里——emoji 的家庭、职业序列靠它连字，剥掉会把
#: 创作者名字里的一个 emoji 拆成两三个。
ZERO_WIDTH = str.maketrans({"​": None, "‌": None,
                            "⁠": None, "﻿": None})


def strip_zero_width(name: str) -> str:
    return str(name or "").translate(ZERO_WIDTH)


def canonicalize_entity_name(kind: str, name: str | None) -> str:
    canonical = strip_zero_width(name).strip()
    if kind in PERSON_ENTITY_KINDS:
        canonical = collapse_repeated_entity_name(canonical)
        if canonical in INVALID_PERSON_ENTITY_NAMES:
            return ""
    return canonical


#: 规范名有一份扁平投影（ADR-0005）：女优落在 `asset_tag` 的 `演员:` 标签里，其余三种
#: 落在 `asset` 的同名列里。只改实体名不改这一份，卡片上还写着旧名、按旧名也照样查得到，
#: 资料页和卡片就各说各话了。
FLAT_COLUMN = {"studio": "studio", "creator": "creator", "series": "series"}


def rewrite_flat_projection(connection: Connection, kind: str, entity_id: int,
                            old_name: str, new_name: str) -> int:
    """规范名换写法之后，把扁平投影一并改过来，返回改动的资产数。

    资料页的统称选择器和账本清理脚本改的是同一件事，共用这一份：投影跟不上实体名的
    后果不是报错，是卡片和资料页各说各话，而且按旧名还照样搜得到。
    """
    column = FLAT_COLUMN.get(kind)
    if column:
        connection.execute(f"UPDATE asset SET {column}=? WHERE {column}=?",
                           (new_name, old_name))
        return connection.execute("SELECT changes()").fetchone()[0]
    rewritten = 0
    old_tag, new_tag = f"演员:{old_name}", f"演员:{new_name}"
    for item in connection.execute(
        "SELECT DISTINCT asset_id FROM asset_entity WHERE entity_id=?", (entity_id,)
    ):
        asset_id = int(item[0])
        # 置信度与来源跟着旧标签走：换的是写法，不是这条标注的可信程度。
        connection.execute(
            "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
            "SELECT asset_id,?,confidence,source FROM asset_tag WHERE asset_id=? AND tag=?",
            (new_tag, asset_id, old_tag))
        connection.execute("DELETE FROM asset_tag WHERE asset_id=? AND tag=?",
                           (asset_id, old_tag))
        if connection.execute("SELECT changes()").fetchone()[0]:
            rewritten += 1
    return rewritten


def merge_entity(
    connection: Connection, *, target_id: int, source_id: int,
    source_name: str, alias_source: str, now: str | None = None,
) -> dict:
    """把 source 实体并入 target，然后删除 source。调用方负责事务与备份。

    合并是不可逆的，只应在人工确认两个实体确为同一身份后调用——典型场景是
    同一位女优的旧艺名与现用艺名各自成了一个实体。

    `entity_external_ref` 有 `UNIQUE(entity_id, provider, external_kind)`，
    同一 provider 下只能留一条，所以 source 侧同类引用会被丢弃而不是覆盖；
    丢弃数量在返回值里报告，便于人工回看。
    """
    stamp = now or datetime.now(timezone.utc).isoformat()
    moved = {"assets": 0, "aliases": 0, "refs": 0, "links": 0, "terms": 0,
             "dropped_refs": 0}

    # 被并入的名字本身留作别名，否则按旧名搜索会落空。
    connection.execute(
        "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
        " VALUES(?,?,?,?,1.0)",
        (target_id, source_name, normalize_entity_name(source_name), alias_source),
    )
    connection.execute(
        "INSERT OR IGNORE INTO entity_alias"
        " SELECT ?,alias,normalized_alias,source,confidence FROM entity_alias WHERE entity_id=?",
        (target_id, source_id),
    )
    moved["aliases"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM entity_alias WHERE entity_id=?", (source_id,))

    connection.execute(
        "INSERT OR IGNORE INTO asset_entity"
        " SELECT asset_id,?,role,source,confidence,metadata_json,first_seen_at,last_seen_at"
        " FROM asset_entity WHERE entity_id=?", (target_id, source_id))
    moved["assets"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM asset_entity WHERE entity_id=?", (source_id,))

    before = connection.execute(
        "SELECT count(*) FROM entity_external_ref WHERE entity_id=?", (source_id,)).fetchone()[0]
    connection.execute(
        "UPDATE OR IGNORE entity_external_ref SET entity_id=? WHERE entity_id=?",
        (target_id, source_id))
    left = connection.execute(
        "SELECT count(*) FROM entity_external_ref WHERE entity_id=?", (source_id,)).fetchone()[0]
    moved["refs"] = before - left
    moved["dropped_refs"] = left
    connection.execute("DELETE FROM entity_external_ref WHERE entity_id=?", (source_id,))

    connection.execute(
        "INSERT OR IGNORE INTO entity_link(entity_id,link_kind,label,url,hostname,"
        "is_sensitive,metadata_json,created_at,updated_at)"
        " SELECT ?,link_kind,label,url,hostname,is_sensitive,metadata_json,created_at,updated_at"
        " FROM entity_link WHERE entity_id=?", (target_id, source_id))
    moved["links"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM entity_link WHERE entity_id=?", (source_id,))

    connection.execute(
        "INSERT OR IGNORE INTO entity_search_term(entity_id,term,purpose,source,created_at)"
        " SELECT ?,term,purpose,source,created_at FROM entity_search_term WHERE entity_id=?",
        (target_id, source_id))
    moved["terms"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM entity_search_term WHERE entity_id=?", (source_id,))

    connection.execute("UPDATE entity SET updated_at=? WHERE id=?", (stamp, target_id))
    connection.execute("DELETE FROM entity WHERE id=?", (source_id,))
    return moved


def upsert_asset_entity(
    connection: Connection, *, kind: str, name: str | None, asset_id: int,
    role: str, source: str, confidence: float = 1.0,
    external_provider: str | None = None, external_id: str | int | None = None,
    metadata: dict | None = None, now: str | None = None,
) -> int | None:
    """写入规范实体关系；调用方负责事务和兼容投影。"""
    canonical = canonicalize_entity_name(kind, name)
    if not canonical:
        return None
    stamp = now or datetime.now(timezone.utc).isoformat()
    normalized = normalize_entity_name(canonical)
    payload = json.dumps(metadata or {}, ensure_ascii=False)
    entity_id = None
    if external_provider and external_id is not None:
        matched = connection.execute(
            "SELECT e.id FROM entity_external_ref x JOIN entity e ON e.id=x.entity_id "
            "WHERE x.provider=? AND x.external_kind=? AND x.external_id=? AND e.kind=?",
            (external_provider, kind, str(external_id), kind),
        ).fetchone()
        entity_id = int(matched[0]) if matched else None
    if entity_id is None:
        matched = connection.execute(
            "SELECT id FROM entity WHERE kind=? AND normalized_name=?",
            (kind, normalized),
        ).fetchone()
        entity_id = int(matched[0]) if matched else None
    if entity_id is None and kind in PERSON_ENTITY_KINDS:
        alias_matches = connection.execute(
            "SELECT DISTINCT e.id FROM entity e JOIN entity_alias a ON a.entity_id=e.id "
            "WHERE e.kind=? AND a.normalized_alias=? ORDER BY e.id LIMIT 2",
            (kind, normalized),
        ).fetchall()
        if len(alias_matches) == 1:
            entity_id = int(alias_matches[0][0])
    if entity_id is None:
        connection.execute(
            "INSERT INTO entity(kind,canonical_name,normalized_name,metadata_json,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?)",
            (kind, canonical, normalized, payload, stamp, stamp),
        )
        entity_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
    else:
        connection.execute(
            "UPDATE entity SET metadata_json=?,updated_at=? WHERE id=?",
            (payload, stamp, entity_id),
        )
    connection.execute(
        """INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence,
                                     metadata_json,first_seen_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?)
           ON CONFLICT(asset_id,entity_id,role,source) DO UPDATE SET
             confidence=excluded.confidence,
             metadata_json=excluded.metadata_json,
             last_seen_at=excluded.last_seen_at""",
        (asset_id, entity_id, role, source, confidence, payload, stamp, stamp),
    )
    if external_provider and external_id is not None:
        connection.execute(
            """INSERT INTO entity_external_ref(
                 entity_id,provider,external_kind,external_id,metadata_json,last_synced_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(provider,external_kind,external_id) DO UPDATE SET
                 entity_id=excluded.entity_id,
                 metadata_json=excluded.metadata_json,
                 last_synced_at=excluded.last_synced_at""",
            (entity_id, external_provider, kind, str(external_id), payload, stamp),
        )
    return int(entity_id)


def resolve_entity(connection: Connection, kind: str, name: str):
    """先取精确规范名，再取唯一别名；撞名时不任意指向另一位。

    别名撞名返回 None 而不是随便挑一个：指错实体会把作品挂到另一个人名下，
    那是要人工复核才能发现的错误。
    """
    canonical = connection.execute(
        "SELECT e.* FROM entity e WHERE e.kind=? AND e.canonical_name=? LIMIT 1",
        (kind, name),
    ).fetchone()
    if canonical:
        return canonical
    aliases = connection.execute(
        "SELECT DISTINCT e.* FROM entity e JOIN entity_alias a ON a.entity_id=e.id "
        "WHERE e.kind=? AND a.alias=? ORDER BY e.id LIMIT 2",
        (kind, name),
    ).fetchall()
    return aliases[0] if len(aliases) == 1 else None
