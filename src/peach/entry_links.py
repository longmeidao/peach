"""人物资料页的外部入口：几个站点的直达地址，以及它们的本机开关与模板。

入口只由后端拼：地址要用的东西都在服务端——`entity_external_ref` 里的站点 id、
`entity.canonical_name` 和 `entity_alias`。前端拿到的是一串带位置与标记的
`{site, label, slot, mark, url}`，没有模板也没有拼装规则，换一个站不必同时改两侧。

**没有 id 的站点不出现。** 退回搜索地址等于把「这个人在那边是谁」这件事交给站内检索
去猜，而同名的人正是最需要点进去核对的那一批。

**JavDB 与 MISSAV 只给 JAV 女优。** 账本里 `kind='performer'` 装着两种人：商业 AV 女优，
和 `145cm色白お嬢様` 这样的 FC2 个人摄创作者。后者不在这两个站的收录范围里，而 MISSAV
只按名字拼地址，不设门就会给每个创作者挂一条必然落空的链接。门槛是 `_JAV_DIRECTORIES`：
账本里有没有哪个 JAV 目录站给过她 id——那是别人已经收录过她的现成证据，比猜名字是不是
日文、比看标签都硬。`stash` 不算（那是本机 Stash 的 id，库里每个人都有），
`r18:performer_name` 也不算（那是名字映射，不是目录页上的 id）。

**MISSAV 按日文艺名拼。** 它的路径就是名字，而账本里 794 位 performer 有 601 位的规范名
是中文译名，拿译名拼出来的是一个不存在的页面（实测 `/cn/actresses/释爱丽丝` 返回 404，
`/cn/actresses/釈アリス` 返回 200）。所以这一站从别名里挑日文艺名：

- 含假名才算日文写法。汉字分不出中日——`佐々木さき` 认得出，纯汉字的艺名认不出，
  那种只能退回规范名。
- 纯平假名的那条是读音不是艺名。`r18:performer` 每位都带一条（`しゃくありす`），
  而站上的页面挂在混着汉字或片假名的艺名下（`釈アリス`），实测纯平假名同样 404。
- 同样形态的有多条时，优先 `avdb-actor-mapping`、`javdb`、`wiki` 这几类艺名来源。
- 一条都挑不出时才用规范名：拼错的地址和没有地址相比，前者更难发现。

**同一个站点可以有多枚入口。** 一位女优在 javdb 常有两个演员页，两边挂的作品不同，
所以每个 id 各出一枚，第二枚起在标签后缀一个序号。

**两种位置。** minnano-av 是一份资料页，和事务所官网、社媒是同一类东西，所以它排进上面
那排链接里。JavDB 与 MISSAV 是「去看片」的入口，另起一行，用两站自己的标识。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from filelock import FileLock

from .fsutil import atomic_write_text

#: 入口设置落在数据根的 state 目录下。它是本机显示偏好，不是账本真相。
FILENAME = "entry-links.json"
#: `entity_external_ref.external_kind`：人物那一档。
EXTERNAL_KIND = "performer"

#: 入口在页面上的两个位置。`pill` 混进上面那排外链，`mark` 自己一行、用站点标识。
SLOT_PILL = "pill"
SLOT_MARK = "mark"

#: JAV 目录站。实体在这些站里有 `performer` id，才算「这是一位 JAV 女优」。
#: 判据见模块开头：这是别处已经收录过她的现成证据。
JAV_DIRECTORIES = frozenset({"javdb", "minnano-av", "r18dev", "dmm", "kmib", "avbase"})


@dataclass(frozen=True)
class EntrySite:
    """一个入口站点。

    `provider` 空串表示这一站按名字拼，不需要账本里的 id。`label` 是页面上那枚入口的
    可读名字，`title` 是配置页和报错里的站点名。`mark` 是雪碧图里那枚标记的名字；
    MISSAV 没有可用的图形标识，它的 `mark` 是空串，由前端按站点自己的排版规则排字。
    """

    key: str
    label: str
    title: str
    placeholder: str
    provider: str
    template: str
    slot: str
    mark: str
    jav_only: bool = False


SITES: tuple[EntrySite, ...] = (
    EntrySite("minnano-av", "minnano-av", "minnano-av", "minnano_id", "minnano-av",
              "https://www.minnano-av.com/actress{minnano_id}.html",
              SLOT_PILL, "brand-minnano"),
    # javdb 的演员页就是作品列表，`sort_type=4` 只是把它按发行日期排；两条地址落在同一页，
    # 所以只留这一条，按用户平时点的那个排序走。
    EntrySite("javdb", "JavDB", "JavDB", "javdb_id", "javdb",
              "https://javdb.com/actors/{javdb_id}?sort_type=4",
              SLOT_MARK, "mark-javdb", jav_only=True),
    EntrySite("missav", "MISSAV", "MISSAV", "name", "",
              "https://missav.ws/cn/actresses/{name}",
              SLOT_MARK, "", jav_only=True),
)
_BY_KEY = {site.key: site for site in SITES}
#: 模板长度上限。地址栏塞得下的东西远不止这个数，但入口模板只有一个占位符要填。
_TEMPLATE_LIMIT = 300
#: 第二枚起的序号。用完退回括号数字，标签宁可长一点也不能两枚长得一模一样。
_ORDINALS = "②③④⑤⑥⑦⑧⑨"
#: 艺名类的别名来源。按子串认：来源串后面还挂着采集批次。
_STAGE_NAME_SOURCES = ("avdb-actor-mapping", "javdb", "wiki")


def defaults() -> dict:
    """各站全开，模板即上面那几条。"""
    return {site.key: {"enabled": True, "template": site.template} for site in SITES}


def _clean(saved: object) -> dict:
    """把读到的内容收敛成已知站点。坏值退回默认，不让一个手改坏的文件关掉整行入口。"""
    result = defaults()
    if not isinstance(saved, dict):
        return result
    rows = saved.get("sites")
    for key, value in (rows.items() if isinstance(rows, dict) else ()):
        site = _BY_KEY.get(str(key))
        if site is None or not isinstance(value, dict):
            continue
        if isinstance(value.get("enabled"), bool):
            result[site.key]["enabled"] = value["enabled"]
        template = value.get("template")
        if isinstance(template, str) and _template_problem(site, template.strip()) == "":
            result[site.key]["template"] = template.strip()
    return result


def read(root: Path) -> dict:
    """当前设置。文件不在、读不出或内容坏掉都退回默认。"""
    try:
        return _clean(json.loads((Path(root) / FILENAME).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return defaults()


def snapshot(root: Path) -> dict:
    """配置页要的形状：每站一行，带站名、占位符和可恢复的默认模板。"""
    saved = read(root)
    return {"sites": [{
        "key": site.key,
        "label": site.title,
        "placeholder": site.placeholder,
        "enabled": saved[site.key]["enabled"],
        "template": saved[site.key]["template"],
        "default_template": site.template,
    } for site in SITES]}


def _template_problem(site: EntrySite, template: str) -> str:
    """模板不能用时的那一句原因；能用时是空串。"""
    mark = "{" + site.placeholder + "}"
    if not template:
        return f"{site.title} 的地址模板不能为空"
    if len(template) > _TEMPLATE_LIMIT:
        return f"{site.title} 的地址模板请控制在 {_TEMPLATE_LIMIT} 个字符以内"
    if any(char.isspace() for char in template):
        return f"{site.title} 的地址模板里不能有空格"
    if not template.startswith("https://"):
        return f"{site.title} 的地址模板要以 https:// 开头"
    if template.count(mark) != 1:
        return f"{site.title} 的地址模板要且只要一个 {mark}"
    if template.replace(mark, "").count("{") or template.replace(mark, "").count("}"):
        return f"{site.title} 的地址模板里只认 {mark} 这一个占位符"
    return ""


def save(root: Path, body: dict) -> dict:
    """写回各站的开关与模板。任一项不合规就整批不写。"""
    rows = body.get("sites")
    if not isinstance(rows, dict):
        raise ValueError("请提交每个站点的开关与地址模板")
    result = defaults()
    for site in SITES:
        row = rows.get(site.key)
        if not isinstance(row, dict):
            raise ValueError(f"缺少 {site.title} 的设置")
        if not isinstance(row.get("enabled"), bool):
            raise ValueError(f"{site.title} 的开关必须是 true 或 false")
        template = row.get("template")
        if not isinstance(template, str):
            raise ValueError(f"{site.title} 的地址模板必须是文字")
        problem = _template_problem(site, template.strip())
        if problem:
            raise ValueError(problem)
        result[site.key] = {"enabled": row["enabled"], "template": template.strip()}
    path = Path(root) / FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path) + ".lock", timeout=5):
        atomic_write_text(path, json.dumps({"sites": result}, ensure_ascii=False))
    return snapshot(root)


def provider_ids(refs) -> dict[str, list[str]]:
    """`entity_external_ref` 的行 → 这个站点上的 id 们。只认人物那一档。"""
    found: dict[str, list[str]] = {}
    for ref in refs or ():
        if str(ref.get("external_kind") or "") != EXTERNAL_KIND:
            continue
        external_id = str(ref.get("external_id") or "").strip()
        provider = str(ref.get("provider") or "")
        ids = found.setdefault(provider, [])
        if external_id and external_id not in ids:
            ids.append(external_id)
    return found


def _has_kana(written: str) -> bool:
    return any(0x3040 <= ord(char) <= 0x30FF for char in written)


def _only_hiragana(written: str) -> bool:
    """写法里除了空白和标点就只有平假名。那是读音，不是站上挂着页面的艺名。"""
    return all(char.isspace() or not char.isalnum() or 0x3041 <= ord(char) <= 0x309F
               for char in written)


def japanese_name(canonical_name: str, aliases) -> str:
    """这位的日文艺名。挑不出来时退回规范名，判据见模块开头。"""
    name = str(canonical_name or "").strip()
    chosen: tuple[tuple[int, int, int], str] | None = None
    for index, row in enumerate(aliases or ()):
        written = str((row.get("alias") if isinstance(row, dict) else row) or "").strip()
        if not written or not _has_kana(written):
            continue
        source = str((row.get("source") if isinstance(row, dict) else "") or "")
        rank = (1 if _only_hiragana(written) else 0,
                0 if any(mark in source for mark in _STAGE_NAME_SOURCES) else 1,
                index)
        if chosen is None or rank < chosen[0]:
            chosen = (rank, written)
    return chosen[1] if chosen else name


def is_jav_performer(refs) -> bool:
    """这条实体在 JAV 目录站里有身份吗。判据与理由见模块开头。"""
    return any(provider in JAV_DIRECTORIES for provider in provider_ids(refs))


def _ordinal(index: int) -> str:
    """同一个站点第二枚起的序号，第一枚没有。

    序号单独给一项而不是只拼进 `label`：标识那一行印的是站点自己的图形，没有位置放
    整句话，序号得能单独摆在标识旁边。用完那几个字符退回括号数字，宁可长一点也不能
    两枚长得一模一样。
    """
    if index == 0:
        return ""
    if index <= len(_ORDINALS):
        return _ORDINALS[index - 1]
    return f"({index + 1})"


def build(settings: dict, canonical_name: str, refs, aliases=()) -> list[dict]:
    """这条人物实体能直达的地址，按 SITES 的先后排好。缺 id 的站点不出现在结果里。"""
    ids = provider_ids(refs)
    jav = is_jav_performer(refs)
    written = japanese_name(canonical_name, aliases)
    out: list[dict] = []
    for site in SITES:
        row = settings.get(site.key) or {}
        if not row.get("enabled", True) or (site.jav_only and not jav):
            continue
        values = ids.get(site.provider, []) if site.provider else ([written] if written else [])
        template = str(row.get("template") or site.template)
        if _template_problem(site, template):
            template = site.template
        for index, value in enumerate(values):
            ordinal = _ordinal(index)
            out.append({"site": site.key,
                        "label": f"{site.label} {ordinal}".strip(),
                        "ordinal": ordinal, "slot": site.slot, "mark": site.mark,
                        "url": template.replace("{" + site.placeholder + "}",
                                                quote(value, safe=""))})
    return out


def entry_links(root: Path, canonical_name: str, refs, aliases=()) -> list[dict]:
    """读设置并拼出入口。资料页只调这一个。"""
    return build(read(root), canonical_name, refs, aliases)
