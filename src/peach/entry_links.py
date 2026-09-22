"""人物资料页的外部入口：几个站点的直达地址，以及它们的本机开关与模板。

入口只由后端拼：地址要用的东西都在服务端——`entity_external_ref` 里的站点 id、
`entity.canonical_name` 和 `entity_alias`。前端拿到的是一串带栏位与图标的
`{site, label, url, section, line, icon}`，没有模板也没有拼装规则，换一个站不必同时
改两侧。

**没有 id 的站点不出现。** 退回搜索地址等于把「这个人在那边是谁」这件事交给站内检索
去猜，而同名的人正是最需要点进去核对的那一批。

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

#: 三个栏位。资料页按这三个词给灰色小标题，站点归在它下面。
SECTION_HOME = "演员主页"
SECTION_WATCH = "在线观看"
SECTION_LIBRARY = "在线片库"


@dataclass(frozen=True)
class EntrySite:
    """一个入口站点。

    `provider` 空串表示这一站按名字拼，不需要账本里的 id。`label` 是药丸上的字，
    `title` 是配置页和报错里的站点名——同一个站在两个栏位各有一枚时，药丸靠栏位标题
    说清是哪一枚，而配置页没有栏位标题，得自己把话说全。
    """

    key: str
    label: str
    title: str
    placeholder: str
    provider: str
    template: str
    section: str
    line: int
    icon: str


SITES: tuple[EntrySite, ...] = (
    EntrySite("minnano-av", "minnano-av", "minnano-av", "minnano_id", "minnano-av",
              "https://www.minnano-av.com/actress{minnano_id}.html",
              SECTION_HOME, 1, "brand-minnano"),
    EntrySite("javdb-home", "JavDB", "JavDB 演员主页", "javdb_id", "javdb",
              "https://javdb.com/actors/{javdb_id}",
              SECTION_HOME, 1, "brand-javdb"),
    EntrySite("missav", "MISSAV", "MISSAV", "name", "",
              "https://missav.ws/cn/actresses/{name}",
              SECTION_WATCH, 1, "brand-missav"),
    EntrySite("javdb", "JavDB", "JavDB 作品列表", "javdb_id", "javdb",
              "https://javdb.com/actors/{javdb_id}?sort_type=4",
              SECTION_LIBRARY, 2, "brand-javdb"),
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


def _numbered(label: str, index: int) -> str:
    """同一个站点第二枚起带序号，否则两枚药丸读起来是同一条。"""
    if index == 0:
        return label
    if index <= len(_ORDINALS):
        return f"{label} {_ORDINALS[index - 1]}"
    return f"{label} ({index + 1})"


def build(settings: dict, canonical_name: str, refs, aliases=()) -> list[dict]:
    """这条人物实体能直达的地址，按栏位与行序排好。缺 id 的站点不出现在结果里。"""
    ids = provider_ids(refs)
    written = japanese_name(canonical_name, aliases)
    out: list[dict] = []
    for site in SITES:
        row = settings.get(site.key) or {}
        if not row.get("enabled", True):
            continue
        values = ids.get(site.provider, []) if site.provider else ([written] if written else [])
        template = str(row.get("template") or site.template)
        if _template_problem(site, template):
            template = site.template
        for index, value in enumerate(values):
            out.append({"site": site.key, "label": _numbered(site.label, index),
                        "section": site.section, "line": site.line, "icon": site.icon,
                        "url": template.replace("{" + site.placeholder + "}",
                                                quote(value, safe=""))})
    # 稳定排序：行内仍按 SITES 的先后，而 SITES 的顺序就是栏位的顺序。
    return sorted(out, key=lambda entry: entry["line"])


def entry_links(root: Path, canonical_name: str, refs, aliases=()) -> list[dict]:
    """读设置并拼出入口。资料页只调这一个。"""
    return build(read(root), canonical_name, refs, aliases)
