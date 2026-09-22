"""元数据字段候选的判据与落库：复核页批准与处理任务自动落库共用这一份。

判据（ADR-0018/0025/0029/0033/0034/0035）与写入映射（ADR-0005 的字段归属）是领域规则，
不是 Web 行为：命令行首扫、Web 后台处理任务和复核页的「通过」按钮走的必须是同一套。
它们此前住在 `web_review` 里，于是 `cli` 与处理任务为了自动落库反向 import 了 web 层。

`auto_apply_metadata` 由调用方注入已经在用的 `LedgerDatabase`：进程内写锁是实例级的，
自己再 new 一个就等于在同一个进程里开第二条写入路径，与页面上的写入互相 `database is
locked`。批量落库按 `AUTO_APPLY_BATCH` 条一个事务提交，中途被停止或失败时已经判完的
那些不回滚重来。
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path

from .catalog_rules import (
    code_release_date,
    collapse_superseded_taste_tags,
    is_korean_mib_code,
    normalise_code_key,
    release_code_from_filename,
    same_release_code,
    superseded_taste_tags,
)
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
    resolve_entity,
    upsert_asset_entity,
)
from .field_owners import (
    auto_owner,
    check_revision,
    is_protected,
    owner_of,
    write_owned_fields,
)
from .genre_decisions import load_genre_decisions
from .genre_taxonomy import UNMAPPED, genres_in_warning, resolve_genre
from .metadata import identifies_code
from .metadata_alias_resolve import (
    is_planning_alias as _is_planning_alias,
    register_planning_alias,
    resolve_planning_alias,
    stage_name as _stage_name,
)
from .metadata_policy import (
    CHAIN_OFFICIAL, FALLBACK_SOURCES, LOCAL_NFO_SOURCE, SOURCE_SPECS,
    blacklisted, chain_rank, source_tier,
)
from .review_csv import read_candidates

#: 一个写事务里最多落多少条。整批一个事务在本机实测是几千条候选压着写锁不放，
#: 页面上任何一次写入都得等它跑完；分批之后每段只占一小会儿，被停止时也只丢这一段。
AUTO_APPLY_BATCH = 200

REVIEW_APPLY_LIMIT = 500


#: 多值字段在账本里是实体关系，不是 `asset` 上的列。
_MULTI_VALUE_ROLES = {"performers": "performer", "tags": "tag"}


def _codes_matching(connection, codes: list[str], columns: str) -> list:
    """这些番号名下的资产行。账本里的写法未必和候选件一致。

    账本存的是编目后的规范写法，候选件写的是来源站上的那个号：Tokyo-Hot 的 `n0762`
    在账本里是 `TOKYO-HOT-N0762`，按字符串比一条都对不上（2026-09-22 实测 n0762 的
    标题、演员、系列、发行日期四行全部因此判成「账本里没有这个番号」，停在人工队列，
    而账本里的别名早就把「藤原遼子／森沢かな」和「東熱／東京熱」各自认作一个）。
    `normalise_code_key` 两边归一化之后是同一个键，它也正是封面缓存和复核页在用的那个。

    先按字符串精确查一遍，没覆盖到的番号才宽查：归一化后的键是账本写法的子串
    （`n0762` ⊂ `TOKYO-HOT-N0762`），拿它把范围收小，再逐条按归一化判等。
    """
    wanted = [code for code in dict.fromkeys(code.strip() for code in codes) if code]
    if not wanted:
        return []
    marks = ",".join("?" * len(wanted))
    found = list(connection.execute(
        f"SELECT {columns} FROM asset WHERE medium='video' "
        f"AND (disposal IS NULL OR disposal<>'trash') "
        f"AND upper(trim(code)) IN ({','.join(['upper(?)'] * len(wanted))}) ORDER BY id", wanted))
    covered = {normalise_code_key(str(row["code"] or "")) for row in found}
    missing = [code for code in wanted if normalise_code_key(code) not in covered]
    if not missing:
        return found
    keys = {normalise_code_key(code) for code in missing} - {""}
    likes = " OR ".join(["upper(code) LIKE '%'||upper(?)||'%'"] * len(keys))
    found += [row for row in connection.execute(
        f"SELECT {columns} FROM asset WHERE medium='video' "
        f"AND (disposal IS NULL OR disposal<>'trash') AND ({likes}) ORDER BY id", sorted(keys))
        if normalise_code_key(str(row["code"] or "")) in keys]
    return found


def refresh_current_values(connection, rows: list[dict]) -> None:
    """把候选行的「账本现值」换成账本此刻的值。

    候选件是抓取那一刻写的，`current_value` 也就停在那一刻。之后落过库、合并过实体、
    改过名的，这一栏都不跟着动：实测 300 行队列里有 85 行写着空而账本早有值（标签 29、
    演员 22、标题 13、厂牌 8、系列 8、发行日期 5）。队列拿它判「补空还是冲突」，自动
    落库拿它判「这里是不是空的」——过期一份，两处一起错，而且错的方向是往库里写。

    账本里找不到这个番号的资产时保留候选件那一份：那种行本来就轮不到按现值判。
    """
    codes = [code for code in dict.fromkeys(
        str(row.get(key) or "").strip() for row in rows for key in ("code", "query")) if code]
    if not codes:
        return
    columns = sorted(set(METADATA_FIELD_COLUMNS.values()))
    by_asset: dict[int, dict] = {}
    by_code: dict[str, list[int]] = defaultdict(list)
    for asset in _codes_matching(connection, codes, f"id,code,{','.join(columns)}"):
        by_asset[int(asset["id"])] = dict(asset)
        by_code[normalise_code_key(asset["code"])].append(int(asset["id"]))
    if not by_asset:
        return
    ids = list(by_asset)
    id_marks = ",".join("?" * len(ids))
    linked: dict[int, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for asset_id, role, name in connection.execute(
            f"SELECT ae.asset_id,ae.role,e.canonical_name FROM asset_entity ae"
            f" JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id IN ({id_marks})"
            " AND ae.role IN ('performer','tag') ORDER BY e.canonical_name", ids):
        linked[int(asset_id)][str(role)].append(str(name))

    for row in rows:
        field = str(row.get("field") or "").strip()
        raw = str(row.get("asset_id") or "").strip()
        # 取值范围必须和 `_apply_metadata_candidate` 写的范围一样：钉住单个文件的行
        # （带 `asset_path`，本机 275 行）只看那一个，其余按番号整组。范围不一致就会
        # 出现「按九卷里空着的那一卷判成空位，落库却把第十卷已有的值一起改掉」。
        if str(row.get("asset_path") or "").strip() and raw.isdigit() and int(raw) in by_asset:
            targets = [int(raw)]
        else:
            key = normalise_code_key(str(row.get("code") or row.get("query") or ""))
            targets = by_code.get(key, [])
        if not targets:
            continue
        column = METADATA_FIELD_COLUMNS.get(field)
        if column:
            # 同番号多卷时任取有值的那一卷：落库本来就是整组一起写。
            row["current_value"] = next(
                (value for target in targets
                 if (value := str(by_asset[target][column] or "").strip())), "")
        elif field in _MULTI_VALUE_ROLES:
            role = _MULTI_VALUE_ROLES[field]
            row["current_value"] = "、".join(dict.fromkeys(
                name for target in targets for name in linked[target][role]))


def _unmapped_genres(candidate: dict) -> list[str]:
    """候选里那批未收录原文。

    `unmapped_genres` 是结构化的那份。2026-09-11 之前写下的候选文件只有 `warnings`
    里那句中文提示，而复核页要能在它们身上就把 genre 收录进来——让用户先重抓一遍全库
    才有按钮可点，等于这个功能对现有队列不存在。反解只认 `genre_taxonomy` 自己拼出
    的那个格式，两边写在同一个文件里。
    """
    structured = [str(item).strip() for item in candidate.get("unmapped_genres") or []]
    if any(structured):
        return [item for item in structured if item]
    for warning in candidate.get("warnings") or []:
        recovered = genres_in_warning(warning)
        if recovered:
            return recovered
    return []


def _fold_genre_decisions(field: str, candidate: dict, decided: dict[str, str | None]) -> dict:
    """把用户已经收录的 genre 折进这条候选，剩下的以结构化形式交给页面。

    候选文件是抓取那一刻的产物，收录一个 genre 不重抓全库；判定要写进账本的也是折过
    之后的这份值，否则页面上标签已经多出一个、批准写下去的还是旧的那几个。
    未决的那些从 `warnings` 里那句话挪到 `unmapped_genres`：页面要拿它们做按钮，
    留一句「来源还有 2 个未收录 genre」只能读，读完还是没有出口。

    静态表也要重查一遍，不只查用户的决定：候选文件停在抓取那一刻，而 `CONTENT_GENRES`
    与 `NON_CONTENT_GENRES` 一直在补。实测本机 304 条带未收录 genre 的候选里，101 条
    的未收录项按当前的表全部认得出来——`配信専用`、`ナンパ`、`清楚` 早就在表里了，
    页面上却还摆着它们等人判。
    """
    if field != "tags":
        return candidate
    unmapped = _unmapped_genres(candidate)
    if not unmapped:
        return candidate
    values = [str(value) for value in candidate.get("value") or []]
    remaining: list[str] = []
    for genre in unmapped:
        tag = resolve_genre(genre, decided)
        if tag == UNMAPPED:
            remaining.append(genre)
            continue
        if tag and tag not in values:
            values.append(tag)
    return {**candidate, "value": values, "display_value": "、".join(values),
            "unmapped_genres": remaining,
            "warnings": [warning for warning in candidate.get("warnings") or []
                         if not genres_in_warning(warning)]}


def _split_multi(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[、,，/|]", value or "") if part.strip()]


def _entity_identity_key(connection, kind: str, name: str) -> frozenset:
    """把一个名字折成身份键：能解析到实体的用实体 id，解析不到的保留规范化原名。

    来源常把两种写法并在一串里——演员是「现名（旧名）」，厂牌是
    `プレステージプレミアム(PRESTIGE PREMIUM)` 这种日英并写。整串匹配不到实体，
    括号两边各自却都是已登记别名，所以拆开再查一次。没有一个变体命中就保留原名，
    真正的冲突不会被这一步吞掉。
    """
    variants = [name.strip()]
    match = re.fullmatch(r"\s*([^（(]+?)\s*[（(]([^）)]+)[）)]\s*", name)
    if match:
        variants.extend(part.strip() for part in match.groups() if part.strip())
    resolved = {
        row["id"] for variant in variants
        if (row := resolve_entity(connection, kind, variant))
    }
    return frozenset(resolved) if resolved else frozenset({normalize_entity_name(name)})


def _performer_identity_keys(connection, names: list[str]) -> frozenset:
    """把演员名折成身份键：能解析到实体的用实体 id，解析不到的保留原名。

    r18dev 给的是日文名，而账本规范名多数已本地化成中文——`桃谷エリカ` 与
    `桃谷绘里香` 实测就是同一条实体（日文名早已登记为别名）。按字符串比会把
    这类候选全判成「有差异」，批准反而把规范名倒退成别名。
    """
    keys = set()
    for name in names:
        keys.update(_entity_identity_key(connection, "performer", name))
    return frozenset(keys)


#: 可以不经人判断直接落库的字段（ADR-0025 扩到 P0 全字段）。
#:
#: 标签是多值集合，「取值一致」对它的含义是整份集合逐字相同，而不是逐个标签比对；
#: `_candidate_value_key` 拿的就是拼好的那一串，所以这条判据照样成立。三张表都不认的
#: genre 不再扣住整条候选：认得出的那些先落库，剩下的词记进 `pending_genres` 单独等
#: 人收录（ADR-0038）。
AUTO_APPLY_FIELDS = frozenset({
    "title", "original_title", "performers", "studio", "series", "release_date", "tags",
})


def _planning_alias_resolver(connection, row: dict, snapshot_root):
    """这一行的企划名义解析器：`艺名写法 -> (主艺名, 证据来源)`，解不出返回 None。

    按行缓存。同一行里多个来源常给同一个称呼，每次都去翻一遍快照目录和 `entity_alias`
    是白做的重复 I/O，而这一层在整库落库时每条候选都要走。
    """
    codes = (row.get("code"), row.get("query"))
    cache: dict[str, tuple[str, str] | None] = {}

    def resolve(name: str):
        if name not in cache:
            cache[name] = resolve_planning_alias(
                connection, name, metadata_root=snapshot_root, codes=codes)
        return cache[name]

    return resolve


def _offers_another_stage_name(candidate: dict) -> bool:
    """这条候选给的是不是另一个主艺名；整条都是企划名义就不是。

    空候选照旧算数：那是「来源说这里没人」，与「来源换了个称呼」是两回事。
    """
    names = _split_multi(str(candidate.get("display_value") or ""))
    return not names or not all(_is_planning_alias(name) for name in names)


def _stage_names(candidate: dict, resolve=None) -> tuple[list[str] | None, dict]:
    """整条出演者候选剪成艺名列表，外加解出来的企划名义对照表。

    返回 `(艺名列表, {艺名: (企划名义, 证据来源)})`。剪不出艺名、`resolve` 又给不出
    主艺名的，整条回人工——`(None, {})`。

    `resolve` 缺省是 None，也就是「不走企划名义那条路」。这是有意的默认：解析要读
    本机快照目录，没人把那个目录交给这一层时就不该自己去猜一个（ADR-0038）。
    """
    people = candidate.get("value")
    if not isinstance(people, list) or not people:
        return None, {}
    names: list[str] = []
    resolved: dict[str, tuple[str, str]] = {}
    for person in people:
        if not isinstance(person, dict):
            return None, {}
        raw = str(person.get("name") or "")
        name = _stage_name(raw)
        if name is None:
            # 剪得出边界的那些照旧按 ADR-0025 落剪好的艺名：`桜井奈々 28歳 某企業広報担当`
            # 的艺名就是 `桜井奈々`，不必去别处求证。这条路只管剪完仍认不出的那些。
            found = resolve(raw) if resolve is not None else None
            if found is None:
                return None, {}
            name, source = found
            resolved[name] = (raw.strip(), source)
        names.append(name)
    return (names or None), (resolved if names else {})


def _candidate_value_key(connection, field: str, candidate: dict, resolve=None):
    """两个来源说的是不是同一件事；这条候选本身不可用时返回 None。

    出演者比的是人，不是写法。同一位在两家站上常挂着不同艺名，而账本早把它们登记在
    同一条实体名下：`n0646` javbus 写 `一ノ瀬アメリ`、javdb 写 `美空あやか`，两个写法
    都指向实体 8074（规范名 `美空彩香`）；`011013_511` 的 `飯岡かなこ` 与 `森沢かな`
    同理。按字符串比，这些行会被判成「来源有分歧」而扣在人工队列里，可分歧问的那个
    问题账本自己已经答过了。

    解析不到实体的写法保留规范化原名，所以真换了人不会被这一步折掉；顺序也不参与
    比较——`FSEI-003` 两家给的是同一组六个人，只是排序不同。
    """
    if field == "performers":
        names, _resolved = _stage_names(candidate, resolve)
        return None if names is None else _performer_identity_keys(connection, names)
    value = str(candidate.get("display_value") or "").strip()
    return value or None


def _normalised_candidate(field: str, candidate: dict, resolve=None) -> dict:
    """落库用的候选。出演者写剪好的艺名，原文留在 `raw_display_value` 里备查。

    企划名义解出来的那几位，把原称呼挂在这个人自己身上（`planning_alias`）：落库
    那一步要按它登记别名，而整条的 `raw_display_value` 分不出是哪一位。
    """
    if field != "performers":
        return candidate
    names, resolved = _stage_names(candidate, resolve)
    names = names or []
    people = [{**person, "name": name,
               **({"planning_alias": resolved[name][0]} if name in resolved else {})}
              for person, name in zip(candidate.get("value") or [], names)]
    return {**candidate, "value": people, "display_value": "、".join(names),
            "raw_display_value": str(candidate.get("display_value") or "").strip(),
            **({"alias_source": sorted({source for _raw, source in resolved.values()})[0]}
               if resolved else {})}


def _preferred_candidate(field: str, candidates: list[dict]) -> dict:
    """取值一致时由谁署名。字段优先级链已经排好，落库记的出处就该是链上最靠前的那家。"""
    return min(candidates, key=lambda candidate: chain_rank(
        field, str(candidate.get("source") or "").strip()))


#: 韩国 MIB 番号唯一可信的来源：官网 k-mib.com（`metadata_kmib`）。
MIB_OFFICIAL_SOURCE = "kmib"


def _only_mib_official(row: dict) -> bool:
    """这一行的候选是否全部来自 MIB 官网；没有候选或解析不了时为 False。"""
    candidates = row.get("candidates")
    if candidates is None:
        try:
            candidates = json.loads(str(row.get("candidates_json") or "[]"))
        except (TypeError, ValueError):
            return False
    sources = {str(c.get("source") or "").strip()
               for c in candidates if isinstance(c, dict)}
    return sources == {MIB_OFFICIAL_SOURCE}


def _candidate_identifies_code(code: str, candidate: dict) -> bool:
    """来源返回的是不是这个番号本身。

    落库那一步早就有同一道闸（`_apply_metadata_candidate`），但它只能拒绝，拒绝不掉
    的是这张卡先占了人的注意力：`259LUXU-891` 的队列里摆着 javbus 按 `259LUXU-1891`
    取回的标题和日期——那是另一部片，点了也写不进去。既然认得出来，就别摆出来。

    本地 NFO 不按番号去问谁（证据是它躺在视频旁边），没有番号的行也无从核起。
    """
    source = str(candidate.get("source") or "").strip()
    if not code or source == LOCAL_NFO_SOURCE:
        return True
    return identifies_code(code, {
        "id": candidate.get("provider_id"), "content_id": candidate.get("content_id"),
        "source_url": candidate.get("source_url"),
    })


def _parsed_candidates(row: dict) -> list[dict]:
    """一行 `candidates_json` 里形状成立的候选，不做任何取舍。"""
    try:
        parsed = json.loads(str(row.get("candidates_json") or "[]"))
    except (TypeError, ValueError):
        return []
    return [candidate for candidate in parsed if isinstance(candidate, dict)
            and str(candidate.get("candidate_key") or "").strip()]


def _row_candidates(row: dict, decided) -> list[dict]:
    """把一行的 `candidates_json` 解析成候选列表：折叠 genre 决定、剔掉番号对不上的。"""
    field = str(row.get("field") or "").strip()
    code = str(row.get("code") or "").strip()
    return [_fold_genre_decisions(field, candidate, decided)
            for candidate in _parsed_candidates(row)
            if _candidate_identifies_code(code, candidate)]


def _auto_apply_rule(candidate: dict, agreed: int) -> str:
    """这条自动落库该记在哪条规则名下。

    企划名义解析（ADR-0038）排最前：这一条改的是写进账本的那个名字本身，回溯时要先
    认出它。按字段优先级链取舍过的排第二，规则名带上胜出那一家；被压下的取值另记在
    note 的 `overruled` 里，两样合起来才答得出「为什么是它」。

    official 与 community 两类补空在 `review_decision` 里必须分得开：出了问题要回溯的
    是「哪些值是 community 源补的」，而 note 是唯一留着这个区别的地方。多来源一致
    （ADR-0025）与单来源（ADR-0018）同样要分得开：前者的证据强度不一样。来源之间有
    分歧、按 ADR-0034 取舍过的，记下是按什么取舍的。覆盖既有取值的那一类（ADR-0035）
    单独记名：它是唯一一条会改掉账本已有值的自动写入，回溯时第一个要捞出来的就是它。
    """
    source = str(candidate.get("source") or "").strip()
    if candidate.get("alias_source"):
        return f"adr-0038-planning-alias-resolved-{candidate['alias_source']}"
    if candidate.get("chain_winner"):
        return f"adr-0038-chain-{candidate['chain_winner']}"
    if candidate.get("replaces_current"):
        if agreed > 1:
            return f"adr-0035-official-replaces-{agreed}-agreed-sources"
        return "adr-0035-official-replaces-single-source"
    if candidate.get("settled_by"):
        return f"adr-0034-empty-field-{candidate['settled_by']}"
    if source == LOCAL_NFO_SOURCE:
        return "adr-0029-empty-field-local-nfo"
    spec = SOURCE_SPECS.get(source)
    kind = "official" if spec is not None and spec.official else "community"
    if agreed > 1:
        return f"adr-0025-empty-field-{agreed}-agreed-{kind}-sources"
    return f"adr-0018-empty-field-single-{kind}-source"


def _evidence_candidates(row: dict, field: str = "") -> list[dict]:
    """能当补空证据的候选：已登记来源与本地 NFO，去掉这个字段上被拉黑的来源。

    只剩一家社区来源也算：落库只补空格子（ADR-0033），空着的格子有一个值比没有强；
    补错的值用户改过一次就归 `user:manual`，自动写入不再碰它（ADR-0034）。

    黑名单（ADR-0038）排在最前面，和 amane 的 `field_blacklist` 同一个位置：被拉黑的
    来源在这个字段上连候选都不算，所以也不会因为「只剩它一家」而被采信。
    """
    return [c for c in row.get("candidates") or []
            if (str(c.get("source") or "").strip() in SOURCE_SPECS
                or str(c.get("source") or "").strip() == LOCAL_NFO_SOURCE)
            and not blacklisted(field, str(c.get("source") or "").strip())]


def _settled_candidates(connection, field: str, code: str, candidates: list[dict],
                        resolve=None) -> tuple[list[dict], str | None, list[dict]]:
    """取值只剩一个的那组候选、据以取舍的规则，以及被压下的那些取值。

    日期式番号的发行日期只认番号自己写的那天：候选里没有这一天就交给人。
    兜底来源（javbus）在这之后才降级：还有别家给了值就不看它（ADR-0035），而番号自带
    的那天是硬事实，谁报出来都算——`092415_001` 只有 javbus 报对，先降级就把它丢了。

    取值仍然不一时按字段优先级链取第一位（ADR-0038）：本地 NFO、官方来源、javdb、
    其余社区、兜底，同层之间用 `FIELD_SOURCE_ORDER` 再排。此前这里只处理「在场的全是
    社区来源」那一种，官方之间的分歧一律交人工——而本机队列里那类分歧 60 条全是同一件
    事：mgstage 是转售店，标题带着店铺加赠、系列写的是店内货架名，dmm 与 libredmm 那一
    侧才是片商自己的口径。链上 dmm 本来就排在 mgstage 前面，让它说话就不必再问人。

    被压下的取值原样返回，调用方写进 `review_decision.note`：自动结算的前提是事后
    答得出「当时还有哪些说法、为什么没选它」，那句话只能落在这里。
    """
    settled_by = None
    date = code_release_date(code) if field == "release_date" else None
    if date is not None:
        matching = [c for c in candidates if str(c.get("display_value") or "").strip() == date]
        settled_by = "code-date" if len(matching) < len(candidates) else None
        candidates = matching
    candidates = [c for c in candidates
                  if str(c.get("source") or "").strip() not in FALLBACK_SOURCES] or candidates
    keys = {id(c): _candidate_value_key(connection, field, c, resolve) for c in candidates}
    values = set(keys.values())
    if None in values or not values:
        return [], None, []
    if len(values) == 1:
        return candidates, settled_by, []
    ranks = {id(c): chain_rank(field, str(c.get("source") or "").strip())
             for c in candidates}
    winner = min(candidates, key=lambda candidate: ranks[id(candidate)])
    # 同一家给出两个不同的值时，链上没有人能替它取舍：`ranks` 里它们分数相同，`min`
    # 只会按列表顺序挑一个，而那个顺序不表达任何判断。这种行交回人工。
    if any(ranks[id(c)] == ranks[id(winner)] and keys[id(c)] != keys[id(winner)]
           for c in candidates):
        return [], None, []
    chosen = [c for c in candidates if keys[id(c)] == keys[id(winner)]]
    overruled = [{"source": str(c.get("source") or "").strip(),
                  "value": str(c.get("display_value") or "").strip()}
                 for c in candidates if keys[id(c)] != keys[id(winner)]]
    return chosen, settled_by, overruled


def _filename_carries_code(code: str, name: str) -> bool:
    """这个文件名认不认得出这个番号。

    逐字出现最直白，但盘里有大量不写连字符的名字（`MEYD911.mp4`）。编目规则本来就
    知道怎么从文件名读番号，读出来同号是比子串更强的身份证据——子串只是碰巧包含。
    两条任一成立即可：本机 2611 条有番号的视频里，逐字命中 1715 条，合起来 2012 条。
    """
    if code.casefold() in name.casefold():
        return True
    parsed = release_code_from_filename(name)
    return bool(parsed) and same_release_code(code, parsed)


def pending_genres(candidates: list[dict]) -> list[str]:
    """这批标签候选里三张表都不认的词。

    折叠已经按用户决定和当前静态表跑过一遍（`_fold_genre_decisions`），剩在
    `unmapped_genres` 里的就是没人判过的那些。它们此前扣住整条候选：一行里认得出
    的十几个标签陪着两个生词一起等人，而等来的判断只关乎那两个词（ADR-0038）。

    认得出的标签照常落库，这几个词记进 `review_decision.note` 的 `pending_genres`，
    复核页按它把这一行重新摆出来——要判的只剩「这个词收录成什么」。
    """
    return list(dict.fromkeys(
        str(genre).strip() for candidate in candidates
        for genre in candidate.get("unmapped_genres") or [] if str(genre).strip()))


def _may_replace_current(candidates: list[dict]) -> bool:
    """这批候选能不能改掉账本已有的值：只有链上第一档可以。

    第一档是本地 NFO 与官方来源（含官方镜像）——用户自己整理的那份，和发行方自己
    写的那页。ADR-0035 让官方来源替换现值时用的就是这条界线，ADR-0038 只是把本地
    NFO 一并纳进来：它在链上排在官方前面，没有理由反而不能替换。

    社区来源仍然只补空（ADR-0033）。兜底来源连挑战都不算：javbus 搜不到就给首个
    近似命中，`259LUXU-891` 它答的是 `259LUXU-1891`。
    """
    sources = {str(c.get("source") or "").strip() for c in candidates}
    return bool(sources) and all(
        source_tier(source) <= CHAIN_OFFICIAL for source in sources)


def metadata_auto_apply_candidate(connection, row: dict, *,
                                  snapshot_root=None) -> dict | None:
    """这一行能否不经复核直接落库；不能就返回 None。

    三项必须同时成立，缺一项就仍然走人工：

    1. 候选**取值**按字段优先级链结算后只剩一个（`_settled_candidates`）。取值一致
       是最强的证据，数的是取值不是候选条数（ADR-0025）；取值不一时按链取第一位
       （ADR-0038），被压下的说法记进 note。两种取舍走在链之前：日期式番号的发行日期
       只认番号自己写的那天（ADR-0034），兜底来源在别家在场时退开（ADR-0035）；
    2. 目标字段当前为空，或者结算下来的来源不是兜底那一家——补空之外，链首那家的
       取值直接替换现值。发行方自己那页就是这部片的出处，账本里那个来路不明的旧值
       没有理由压住它；用户改过的格子归属受保护，仍然不碰；
    3. 该番号名下**每一条**资产的文件名都认得出这个番号——逐字出现，或按编目规则
       解析出来就是它。`MEYD911.mp4` 只差一个连字符，逐字比对认不出，而它就是
       `MEYD-911`；本机 2611 条有番号的视频里这样的有 297 条。

    补空那一支不看来源是不是 official（用户 2026-09-04 决定）：补空不覆盖任何东西，
    唯一的风险是「这个值属不属于这部片」，而那由第 3 条管，与来源可信度无关。卡住
    official 这条的代价是实测 76 条 javbus 补空候选全部滞留人工，它们补的都是账本里
    空着的发行日期——没有可判断项，却要人逐条点过。落库时按来源实际级别记规则名，
    回溯得出来。

    第 3 条是这条捷径唯一的身份保证。刮削按番号取值，番号错则值错；文件名认得出
    番号是本机可核验的证据，而复核界面其实给不了这个保证——它只并排显示番号和
    日期，并不告诉你番号跟这个文件对不对得上。

    出演者多一道形态门槛：官方页把年龄职业写在艺名后面，剪不出艺名的先按本机已有的
    证据解一次企划名义（`snapshot_root` 给的快照目录与 `entity_alias`，ADR-0038），
    解不出才交回人工。第 1 条对它比的是人而不是写法：同一位在两家站上挂着不同艺名、
    账本已把这两个写法登记在同一条实体名下时，那不是分歧（`_candidate_value_key`）。

    未登记来源的候选先被剔除再比对取值：没进 `REGISTERED_SOURCES` 的来源不构成证据，
    留着它只会把「一个有效取值」算成分歧。

    来源级别一律按当前 policy 解析，不读候选 CSV 里的同名字段：那是抓取当时的
    快照，实测 r18dev 在 CSV 里写着 False，而现行 policy 认它是 official_mirror。

    本地 NFO 不在登记表里，却同样构成证据（ADR-0029）：采集时它的番号已经和文件名
    对过，第 3 条照样再核一遍。
    """
    field = str(row.get("field") or "").strip()
    if field not in AUTO_APPLY_FIELDS:
        return None
    code = str(row.get("code") or "").strip()
    if not code:
        return None
    resolve = _planning_alias_resolver(connection, row, snapshot_root)
    candidates, settled_by, overruled = _settled_candidates(
        connection, field, code, _evidence_candidates(row, field), resolve)
    if not candidates:
        return None
    replaces_current = bool(str(row.get("current_value") or "").strip())
    if replaces_current and not _may_replace_current(candidates):
        return None
    candidate = _preferred_candidate(field, candidates)
    query = str(row.get("query") or code).strip()
    # 韩国 MIB 的番号问 JAV 目录站必错，这类候选一条都不该走自动批准。第 3 条对它们
    # 全部成立——文件名就叫 `AR-101 Ari....mp4`——但它保证的是「候选属于这个文件」，
    # 保证不了「来源返回的是这个番号」，而 MIB 恰恰错在后者。只有候选全部来自 MIB
    # 官网时才放行：官网按番号列出的就是这部片本身。
    if is_korean_mib_code(code) and not _only_mib_official(row):
        return None
    targets = _codes_matching(connection, [code, query], "code,name,field_owners")
    if not targets:
        return None
    if not all(_filename_carries_code(code, str(target["name"] or "")) for target in targets):
        return None
    # 归属是用户判断的字段不走自动落库。ADR-0018 第 1 条只看取值空不空，而用户可以
    # 把一个字段判成空——那也是判断。没有这一道，「清空再等自动补回来」就成了
    # 用户无法表达的意思。
    column = METADATA_FIELD_COLUMNS.get(field)
    if column and any(is_protected(owner_of(target["field_owners"], column))
                      for target in targets):
        return None
    return {**_normalised_candidate(field, candidate, resolve),
            "agreed_sources": len(candidates),
            **({"settled_by": settled_by} if settled_by else {}),
            **({"chain_winner": str(candidate.get("source") or "").strip(),
                "overruled": overruled} if overruled else {}),
            **({"pending_genres": found} if (found := pending_genres(candidates)) else {}),
            **({"replaces_current": True} if replaces_current else {})}


def _approved_entity_name(value: object, kind: str) -> str:
    name = str(value or "").strip()
    cleaned = canonicalize_entity_name(kind, name)
    if kind not in {"creator", "performer"}:
        cleaned = collapse_repeated_entity_name(cleaned)
    if not name or not cleaned or cleaned != name:
        raise ValueError("候选仍含重复或未规范化的实体名，拒绝写入")
    return cleaned


def _registered_entity_name(connection, kind: str, name: str) -> str:
    """来源的写法是账本里某条实体的别名，就换成那条的规范名。

    javdb 写 `Tokyo-Hot`、javbus 写 `東京熱`，账本只该有一个 `东京热`。解析不到（或别名
    撞了两条）时保留来源原文。
    """
    known = resolve_entity(connection, kind, name)
    return name if known is None else str(known["canonical_name"])


#: 复核字段名 → `asset` 的真相字段列。`performers` 与 `tags` 不在这里：它们落在
#: `asset_tag` / `asset_entity` 的多值行上，不是 `asset` 的一列，归属由那两张表
#: 自己的 `source` 列承担。
METADATA_FIELD_COLUMNS = {
    "title": "catalog_title", "original_title": "original_title",
    "release_date": "release_date", "studio": "studio", "series": "series",
}


def _apply_performer_candidate(connection, asset_ids: list[int], candidate: dict, *,
                               source: str, confidence: float, metadata: dict,
                               now: str) -> None:
    """把演员候选写成这些资产的 performer 实体与 `演员:` 标签。

    演员是 performer 真相，不回写 `asset.creator`；两种身份混写正是重复名称事故的
    来源之一。
    """
    raw_performers = candidate.get("value")
    if not isinstance(raw_performers, list):
        raise ValueError("演员候选必须是数组")
    performers: list[dict] = []
    seen: set[str] = set()
    for raw in raw_performers:
        if not isinstance(raw, dict):
            raise ValueError("演员候选条目无效")
        name = _approved_entity_name(raw.get("name"), "performer")
        normalized = normalize_entity_name(name)
        if normalized in seen:
            continue
        seen.add(normalized)
        performers.append({**raw, "name": name})
    if not performers:
        raise ValueError("演员候选为空")
    marks = ",".join("?" * len(asset_ids))
    connection.execute(
        f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='performer' "
        "AND source LIKE 'javinizer:%'", asset_ids,
    )
    connection.execute(
        f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
        "AND source LIKE 'javinizer:%:performer'", asset_ids,
    )
    for asset_id in asset_ids:
        for performer in performers:
            name = performer["name"]
            external_id = str(performer.get("external_id") or "").strip()
            connection.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)",
                (asset_id, "演员:" + name, confidence, f"javinizer:{source}:performer"),
            )
            entity_id = upsert_asset_entity(
                connection, kind="performer", name=name, asset_id=asset_id,
                role="performer", source=f"javinizer:{source}:performer",
                confidence=confidence,
                external_provider=_performer_external_provider(
                    performer, source, external_id),
                external_id=(external_id or None), metadata=metadata, now=now,
            )
            # 企划名义解出主艺名时，把封面上印的那个称呼留成别名（ADR-0038）：
            # 账本里写的是 `目黒めぐみ`，用户搜的多半是 `めぐみ 28歳 パパ活女子`
            # 里那个 `めぐみ`，不登记就等于这次解析只落在一行 note 里。
            if entity_id is not None and performer.get("planning_alias"):
                register_planning_alias(
                    connection, entity_id, str(performer["planning_alias"]))


def _apply_metadata_candidate(
    connection, group: dict, candidate: dict, now: str, owner: str, *,
    expected_revision: int | None = None,
) -> int:
    """把一个候选的取值写进真相字段，`owner` 是本次写入者的归属串。

    `owner` 没有默认值：写入者是谁属于调用点的事实，给个默认就等于让下一个
    调用点默默继承别人的身份，而这一层留痕正是 ADR-0005 要保住的东西。
    """
    field = str(group.get("field") or "").strip()
    if field not in {
        "title", "original_title", "performers", "studio", "series", "release_date", "tags",
    }:
        raise ValueError("该元数据字段没有 Peach 写入映射")
    code = str(group.get("code") or "").strip()
    query = str(group.get("query") or code).strip()
    if group.get('asset_path'):
        assets = connection.execute(
            "SELECT id FROM asset WHERE id=? AND path=? AND medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash')",
            (group.get('asset_id'), group['asset_path']),
        ).fetchall()
    else:
        # 写入范围必须和判据、现值刷新看的是同一组资产，三处共用一份番号匹配。
        assets = _codes_matching(connection, [code, query], "id,code")
    asset_ids = sorted({int(row["id"]) for row in assets})
    if not asset_ids:
        raise ValueError("当前 ledger 已没有匹配的可用资产")
    if len(asset_ids) > REVIEW_APPLY_LIMIT:
        raise ValueError(f"同番号资产 {len(asset_ids)} 条，超过单次批准上限 {REVIEW_APPLY_LIMIT}")
    # 乐观并发的凭据在写任何一张表之前验，多值字段那两条分支才同样受它保护。
    check_revision(connection, asset_ids, expected_revision)
    source = str(candidate.get("source") or "").strip()
    candidate_key = str(candidate.get("candidate_key") or "").strip()
    if not re.fullmatch(r"[a-z0-9_-]+", source) or not candidate_key:
        raise ValueError("字段候选来源无效")
    try:
        confidence = float(candidate.get("confidence"))
    except (TypeError, ValueError) as exc:
        raise ValueError("字段候选置信度无效") from exc
    if not 0 <= confidence <= 1:
        raise ValueError("字段候选置信度越界")
    # 来源返回的必须就是这个番号。抓取时也核验，但那道闸只管「快照落盘之前」，
    # 而候选一旦进了 CSV 就再没人问过身份：2026-09-08 的自动批准读的正是 09-02
    # 落盘的那批，把 356 条错配写进真相字段，`AR-101` 拿的是 `STAR-101`、
    # `259LUXU-764` 拿的是 `259LUXU-1764`。落库是唯一必经之处，闸放在这里才
    # 同时管住人工批准和自动批准——那 356 条里有 142 条是人点的。
    #
    # 两种情形没有番号可核：没有番号的资产（靠 `asset_path` 钉住那一个文件），
    # 以及本地 NFO——它不按番号去问谁，证据是这份 sidecar 就躺在视频旁边。
    if code and source != "local_nfo" and not identifies_code(code, {
        "id": candidate.get("provider_id"), "content_id": candidate.get("content_id"),
        "source_url": candidate.get("source_url"),
    }):
        raise ValueError(
            f"来源返回的不是 {code}：id={candidate.get('provider_id')!r} "
            f"content_id={candidate.get('content_id')!r}")
    metadata = {
        "provider": candidate.get("provider") or "javinizer-go", "source": source,
        "source_url": candidate.get("source_url"),
        "provider_id": candidate.get("provider_id"), "content_id": candidate.get("content_id"),
        "raw_snapshot": candidate.get("raw_snapshot"), "review_item": group["item_key"],
        "candidate_key": candidate_key,
    }
    marks = ",".join("?" * len(asset_ids))

    if field in {"title", "original_title"}:
        raw_value = str(candidate.get("value") or "")
        value = " ".join(raw_value.split())
        if (not value or len(value) > 1000
                or any(ord(char) < 32 for char in raw_value)):
            raise ValueError("标题候选为空、过长或含控制字符")
        write_owned_fields(
            connection, asset_ids, {METADATA_FIELD_COLUMNS[field]: value}, owner)
        return len(asset_ids)

    if field == "release_date":
        value = str(candidate.get("value") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("发行日期候选必须是 YYYY-MM-DD")
        try:
            time.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("发行日期候选无效") from exc
        write_owned_fields(
            connection, asset_ids, {"release_date": value}, owner)
        return len(asset_ids)

    if field in {"studio", "series"}:
        name = _registered_entity_name(
            connection, field, _approved_entity_name(candidate.get("value"), field))
        write_owned_fields(
            connection, asset_ids, {field: name}, owner)
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role=? "
            "AND source LIKE 'javinizer:%'",
            (*asset_ids, field),
        )
        for asset_id in asset_ids:
            upsert_asset_entity(
                connection, kind=field, name=name, asset_id=asset_id, role=field,
                source=f"javinizer:{source}:{field}", confidence=confidence,
                metadata=metadata, now=now,
            )
        return len(asset_ids)

    if field == "performers":
        _apply_performer_candidate(
            connection, asset_ids, candidate, source=source, confidence=confidence,
            metadata=metadata, now=now)
        return len(asset_ids)

    raw_tags = candidate.get("value")
    if not isinstance(raw_tags, list):
        raise ValueError("标签候选必须是数组")
    tags = collapse_superseded_taste_tags(list(dict.fromkeys(
        _approved_entity_name(tag, "tag") for tag in raw_tags
    )))
    if not tags:
        raise ValueError("标签候选为空")
    obsolete_tags = superseded_taste_tags(tags)
    if obsolete_tags:
        obsolete_marks = ",".join("?" * len(obsolete_tags))
        obsolete_values = sorted(obsolete_tags)
        connection.execute(
            f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
            f"AND tag IN ({obsolete_marks})",
            [*asset_ids, *obsolete_values],
        )
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='tag' "
            f"AND entity_id IN (SELECT id FROM entity WHERE kind='tag' "
            f"AND canonical_name IN ({obsolete_marks}))",
            [*asset_ids, *obsolete_values],
        )
    connection.execute(
        f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='tag' "
        "AND source LIKE 'javinizer:%'", asset_ids,
    )
    connection.execute(
        f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
        "AND source LIKE 'javinizer:%:tag'", asset_ids,
    )
    for asset_id in asset_ids:
        for tag in tags:
            connection.execute(
                "INSERT INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?) "
                "ON CONFLICT DO UPDATE SET "
                "confidence=excluded.confidence,source=excluded.source",
                (asset_id, tag, confidence, f"javinizer:{source}:tag"),
            )
            upsert_asset_entity(
                connection, kind="tag", name=tag, asset_id=asset_id, role="tag",
                source=f"javinizer:{source}:tag", confidence=confidence,
                metadata=metadata, now=now,
            )
    return len(asset_ids)


def _performer_external_provider(performer: dict, source: str,
                                 external_id: str) -> str | None:
    """人物外部编号跟随资料来源，不被承载候选的 NFO 来源冒领。"""
    if not external_id:
        return None
    # NFO 的名字是这次落库的真值。在线 profile 只在随后精确对到这个实体后才登记编号，
    # 不能让一个错误或被改写的 external_id 抢先把作品连到另一条既有实体。
    if source == LOCAL_NFO_SOURCE and performer.get("profile_source"):
        return None
    return str(performer.get("profile_source") or source)


def auto_apply_metadata(database, candidate_root, *, batch_size=AUTO_APPLY_BATCH,
                        active=lambda: True, snapshot_root=None):
    """把确定的那部分直接落库，不占人工队列。

    ADR-0018：这是「刮削结果只作候选、不直接改写真相字段」的一个**窄例外**，
    不是废除该规则。判据见 `metadata_auto_apply_candidate`，四项缺一即回到人工。
    每条仍写 review_decision 留痕（note 里记来源与判据），所以事后可以追问
    「这个值是谁写的、凭什么」——留痕才是那条规则真正要保住的东西。

    `database` 是调用方已经在用的那一个 `LedgerDatabase`：写锁与提交后的缓存失效都挂在
    实例上，自己再 new 一个就绕开了两者。`active` 返回假时停在批与批之间，已经提交的
    那些保留。

    `snapshot_root` 是本机落盘的来源快照目录，企划名义解析要读它（ADR-0038）。缺省
    是 None，也就是只走 `entity_alias` 那一条路：这一层不去猜真实数据根在哪儿，
    猜错的表现是测试悄悄读起了真实库。
    """
    rows, _source, _skipped = read_candidates("metadata_fields", Path(candidate_root))
    applied, skipped = [], 0
    step = max(1, int(batch_size))
    for start in range(0, len(rows), step):
        if not active():
            break
        # 一批一个事务。整批一个事务在本机是几千条候选一路压着写锁，页面上任何一次
        # 写入都要等它跑完；被停止或中途失败时，回滚的也只是当前这一批。
        batch = [dict(row) for row in rows[start:start + step]]
        with database.write_transaction() as connection:
            decided = {row["item_key"] for row in connection.execute(
                "SELECT item_key FROM review_decision WHERE category='metadata_fields'")}
            genres = load_genre_decisions(connection)
            # 第 1 条判据是「这个字段现在是空的」，问的必须是账本此刻，不是候选件那一刻。
            # 候选落盘之后落过库、合并过实体的，快照还写着空，照它落库就是拿来源覆盖已有值。
            refresh_current_values(connection, batch)
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for row in batch:
                item_key = str(row.get("item_key") or "").strip()
                if not item_key or item_key in decided:
                    continue
                if str(row.get("status") or "").strip() != "candidate":
                    continue
                row["candidates"] = _row_candidates(row, genres)
                candidate = metadata_auto_apply_candidate(
                    connection, row, snapshot_root=snapshot_root)
                if candidate is None:
                    skipped += 1
                    continue
                try:
                    count = _apply_metadata_candidate(
                        connection, row, candidate, now,
                        auto_owner(str(candidate.get("source") or "")))
                except ValueError:
                    # 落库条件在这一刻不成立（例如资产已删）：回到人工，不记决定。
                    skipped += 1
                    continue
                connection.execute(
                    "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                    "VALUES('metadata_fields',?,'approved',?,?) "
                    "ON CONFLICT(category,item_key) DO UPDATE SET status=excluded.status,"
                    "note=excluded.note,updated_at=excluded.updated_at",
                    (item_key, json.dumps({
                        "auto_applied": True,
                        # 规则名记来源的实际级别，不写死 official：补空对 community 源同样
                        # 成立，但两者日后要分开回溯时，note 是唯一还留着这个区别的地方。
                        "rule": _auto_apply_rule(candidate, candidate.get("agreed_sources") or 1),
                        "candidate_key": candidate.get("candidate_key"),
                        "source": candidate.get("source"),
                        "value": candidate.get("display_value"),
                        # 链上被压下的说法。自动结算的前提是事后答得出「当时还有哪些
                        # 说法、为什么没选它」，而候选 CSV 会被下一批盖掉，这里是唯一
                        # 跟着账本一起留下来的那一份（ADR-0038）。
                        **({"overruled": candidate["overruled"]}
                           if candidate.get("overruled") else {}),
                        # 三张表都不认的 genre。标签已经落了认得出的那些，这几个词
                        # 单独等人收录，复核页按它把这一行重新摆出来。
                        **({"pending_genres": candidate["pending_genres"]}
                           if candidate.get("pending_genres") else {}),
                        # 出演者写的是剪过的艺名，原文得留着：事后要答得出账本里这个名字
                        # 是从哪一句剪出来的。
                        **({"raw_value": candidate["raw_display_value"]}
                           if candidate.get("raw_display_value")
                           and candidate["raw_display_value"] != candidate.get("display_value")
                           else {}),
                    }, ensure_ascii=False, separators=(",", ":")), now),
                )
                applied.append({"item_key": item_key, "field": row.get("field"),
                                "value": candidate.get("display_value"),
                                "assets": count})
    return {"ok": True, "applied": len(applied), "left_to_review": skipped,
            "items": applied}
