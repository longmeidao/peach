"""人物资料页的外部入口：几个站点的直达地址，以及其中两站可换的镜像域名。

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

**配置页只有两个域名框。** JavDB 与 MISSAV 各有一排可换的镜像域名，主域名连不上时得跟着
换，所以这两站各留一个框，留空就是上面那个默认域名；路径与占位符由这里定死。整条模板不
交给使用者填：占位符写错换来的是一排看着正常、点开全是 404 的入口，而域名对不对点一次
就知道。みんなのAV 只此一家，没有可换的东西，它不出现在配置页上。

**没有开关。** 入口本来就按账本里有没有 id 决定出不出现，三枚按钮自己就在资料页上；
再给每站一个开关，是让人到设置里关掉一枚他在页面上根本没见到过的入口。
"""
from __future__ import annotations

import json
import re
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
#: 事务所自己的名册不算——`k-mib.com` 那类站收的是所属艺人，和她拍不拍 JAV 是两件事，
#: 只凭它出现在名册上推不出 JavDB 与 MISSAV 上有她的页面。
JAV_DIRECTORIES = frozenset({"javdb", "minnano-av", "r18dev", "dmm", "avbase"})


@dataclass(frozen=True)
class EntrySite:
    """一个入口站点。

    `provider` 空串表示这一站按名字拼，不需要账本里的 id。`label` 是页面上那枚入口的
    可读名字，`title` 是配置页和报错里的站点名。`mark` 是雪碧图里那枚标记的名字；
    MISSAV 没有可用的图形标识，它的 `mark` 是空串，由前端按站点自己的排版规则排字。
    `host` 是默认域名，`mirrored` 说这一站能不能在配置页换域名。
    """

    key: str
    label: str
    title: str
    placeholder: str
    provider: str
    host: str
    path: str
    slot: str
    mark: str
    jav_only: bool = False
    mirrored: bool = False


SITES: tuple[EntrySite, ...] = (
    # 页面上写站点自己的名字「みんなのAV」，取自它官网的 title；`minnano-av` 是域名和
    # 账本里的 provider，留给设置项的 key 与 `entity_external_ref` 用。
    EntrySite("minnano-av", "みんなのAV", "みんなのAV", "minnano_id", "minnano-av",
              "www.minnano-av.com", "/actress{minnano_id}.html",
              SLOT_PILL, "brand-minnano"),
    EntrySite("javdb", "JavDB", "JavDB", "javdb_id", "javdb",
              "javdb.com", "/actors/{javdb_id}",
              SLOT_MARK, "mark-javdb", jav_only=True, mirrored=True),
    EntrySite("missav", "MISSAV", "MISSAV", "name", "",
              "missav.ws", "/cn/actresses/{name}",
              SLOT_MARK, "", jav_only=True, mirrored=True),
)
_BY_KEY = {site.key: site for site in SITES}
#: 域名长度上限与形状。只认域名本身：字母数字、连字符和点，至少一个点。
_HOST_LIMIT = 100
_HOST_SHAPE = re.compile(r"[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?"
                         r"(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)+")
#: 第二枚起的序号。用完退回括号数字，标签宁可长一点也不能两枚长得一模一样。
_ORDINALS = "②③④⑤⑥⑦⑧⑨"
#: 艺名类的别名来源。按子串认：来源串后面还挂着采集批次。
_STAGE_NAME_SOURCES = ("avdb-actor-mapping", "javdb", "wiki")


def defaults() -> dict:
    """一个域名都没换过：能换的那两站留空，读的时候各自退回自己的默认域名。"""
    return {site.key: {"host": ""} for site in SITES if site.mirrored}


def _clean(saved: object) -> dict:
    """把读到的内容收敛成已知站点。坏值退回默认，不让一个手改坏的文件废掉整行入口。"""
    result = defaults()
    if not isinstance(saved, dict):
        return result
    rows = saved.get("sites")
    for key, value in (rows.items() if isinstance(rows, dict) else ()):
        site = _BY_KEY.get(str(key))
        if site is None or not site.mirrored or not isinstance(value, dict):
            continue
        host = _tidy_host(value.get("host"))
        if _host_problem(site, host) == "":
            result[site.key]["host"] = host
    return result


def read(root: Path) -> dict:
    """当前设置。文件不在、读不出或内容坏掉都退回默认。"""
    try:
        return _clean(json.loads((Path(root) / FILENAME).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return defaults()


def snapshot(root: Path) -> dict:
    """配置页要的形状：只有能换域名的那几站，各带当前值和留空时用的默认域名。"""
    saved = read(root)
    return {"sites": [{
        "key": site.key,
        "label": site.title,
        "host": saved[site.key]["host"],
        "default_host": site.host,
    } for site in SITES if site.mirrored]}


def _tidy_host(written: object) -> str:
    """把填进来的东西收成域名。

    镜像地址多半是从别处整条复制过来的，带着 `https://` 和结尾的斜杠。这两样去掉就是
    合法的域名，为它们弹一条错误只是让人手工删一遍。再往后的路径不收：那是在改地址
    形状，不是换域名。
    """
    host = str(written or "").strip()
    for scheme in ("https://", "http://"):
        if host.lower().startswith(scheme):
            host = host[len(scheme):]
    return host.rstrip("/")


def _host_problem(site: EntrySite, host: str) -> str:
    """域名不能用时的那一句原因；能用时是空串。

    空串本身可用——它就是「没换过，走默认域名」。要回到默认值，清空这个框就行；逼人去
    手抄一遍默认域名的话，抄错了还得他自己认。
    """
    if not host:
        return ""
    if len(host) > _HOST_LIMIT:
        return f"{site.title} 的地址请控制在 {_HOST_LIMIT} 个字符以内"
    if not _HOST_SHAPE.fullmatch(host):
        return f"{site.title} 这里只写域名本身，像 {site.host}"
    return ""


def save(root: Path, body: dict) -> dict:
    """写回可换的那几站的域名。任一项不合规就整批不写。"""
    rows = body.get("sites")
    if not isinstance(rows, dict):
        raise ValueError("请提交每个站点的地址")
    result = defaults()
    for site in SITES:
        if not site.mirrored:
            continue
        row = rows.get(site.key)
        if not isinstance(row, dict):
            raise ValueError(f"缺少 {site.title} 的设置")
        if not isinstance(row.get("host"), str):
            raise ValueError(f"{site.title} 的地址必须是文字")
        host = _tidy_host(row["host"])
        problem = _host_problem(site, host)
        if problem:
            raise ValueError(problem)
        result[site.key]["host"] = host
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
        if site.jav_only and not jav:
            continue
        values = ids.get(site.provider, []) if site.provider else ([written] if written else [])
        host = _tidy_host(row.get("host")) if site.mirrored else site.host
        if not host or _host_problem(site, host):
            host = site.host
        for index, value in enumerate(values):
            ordinal = _ordinal(index)
            path = site.path.replace("{" + site.placeholder + "}", quote(value, safe=""))
            out.append({"site": site.key,
                        "label": f"{site.label} {ordinal}".strip(),
                        "ordinal": ordinal, "slot": site.slot, "mark": site.mark,
                        "url": f"https://{host}{path}"})
    return out


def entry_links(root: Path, canonical_name: str, refs, aliases=()) -> list[dict]:
    """读设置并拼出入口。资料页只调这一个。"""
    return build(read(root), canonical_name, refs, aliases)
