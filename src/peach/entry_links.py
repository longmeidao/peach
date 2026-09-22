"""人物资料页的外部入口：三个站点的直达地址，以及它们的本机开关与模板。

入口只由后端拼：地址要用的两样东西都在服务端——`entity_external_ref` 里的站点 id，
和 `entity.canonical_name`。前端拿到的是一串 `{site, label, url}`，没有模板也没有
拼装规则，换一个站不必同时改两侧。

**没有 id 的站点不出现。** 退回搜索地址等于把「这个人在那边是谁」这件事交给站内检索
去猜，而同名的人正是最需要点进去核对的那一批；MISSAV 那条按规范名拼，是因为它的路径
本来就是名字，不是猜出来的检索词。
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


@dataclass(frozen=True)
class EntrySite:
    """一个入口站点。`provider` 空串表示这一站按名字拼，不需要账本里的 id。"""

    key: str
    label: str
    placeholder: str
    provider: str
    template: str


SITES: tuple[EntrySite, ...] = (
    EntrySite("javdb", "JavDB", "javdb_id", "javdb",
              "https://javdb.com/actors/{javdb_id}?sort_type=4"),
    EntrySite("minnano-av", "minnano-av", "minnano_id", "minnano-av",
              "https://www.minnano-av.com/actress{minnano_id}.html"),
    EntrySite("missav", "MISSAV", "name", "",
              "https://missav.ws/dm42/cn/actresses/{name}"),
)
_BY_KEY = {site.key: site for site in SITES}
#: 模板长度上限。地址栏塞得下的东西远不止这个数，但入口模板只有一个占位符要填。
_TEMPLATE_LIMIT = 300


def defaults() -> dict:
    """三站全开，模板即上面那三条。"""
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
        "label": site.label,
        "placeholder": site.placeholder,
        "enabled": saved[site.key]["enabled"],
        "template": saved[site.key]["template"],
        "default_template": site.template,
    } for site in SITES]}


def _template_problem(site: EntrySite, template: str) -> str:
    """模板不能用时的那一句原因；能用时是空串。"""
    mark = "{" + site.placeholder + "}"
    if not template:
        return f"{site.label} 的地址模板不能为空"
    if len(template) > _TEMPLATE_LIMIT:
        return f"{site.label} 的地址模板请控制在 {_TEMPLATE_LIMIT} 个字符以内"
    if any(char.isspace() for char in template):
        return f"{site.label} 的地址模板里不能有空格"
    if not template.startswith("https://"):
        return f"{site.label} 的地址模板要以 https:// 开头"
    if template.count(mark) != 1:
        return f"{site.label} 的地址模板要且只要一个 {mark}"
    if template.replace(mark, "").count("{") or template.replace(mark, "").count("}"):
        return f"{site.label} 的地址模板里只认 {mark} 这一个占位符"
    return ""


def save(root: Path, body: dict) -> dict:
    """写回三站的开关与模板。任一项不合规就整批不写。"""
    rows = body.get("sites")
    if not isinstance(rows, dict):
        raise ValueError("请提交每个站点的开关与地址模板")
    result = defaults()
    for site in SITES:
        row = rows.get(site.key)
        if not isinstance(row, dict):
            raise ValueError(f"缺少 {site.label} 的设置")
        if not isinstance(row.get("enabled"), bool):
            raise ValueError(f"{site.label} 的开关必须是 true 或 false")
        template = row.get("template")
        if not isinstance(template, str):
            raise ValueError(f"{site.label} 的地址模板必须是文字")
        problem = _template_problem(site, template.strip())
        if problem:
            raise ValueError(problem)
        result[site.key] = {"enabled": row["enabled"], "template": template.strip()}
    path = Path(root) / FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path) + ".lock", timeout=5):
        atomic_write_text(path, json.dumps({"sites": result}, ensure_ascii=False))
    return snapshot(root)


def provider_ids(refs) -> dict[str, str]:
    """`entity_external_ref` 的行 → 站点 id。只认人物那一档。"""
    found: dict[str, str] = {}
    for ref in refs or ():
        if str(ref.get("external_kind") or "") != EXTERNAL_KIND:
            continue
        external_id = str(ref.get("external_id") or "").strip()
        provider = str(ref.get("provider") or "")
        if external_id and provider not in found:
            found[provider] = external_id
    return found


def build(settings: dict, canonical_name: str, refs) -> list[dict]:
    """这条人物实体能直达的站点。缺 id 的站点不出现在结果里。"""
    ids = provider_ids(refs)
    name = str(canonical_name or "").strip()
    out: list[dict] = []
    for site in SITES:
        row = settings.get(site.key) or {}
        if not row.get("enabled", True):
            continue
        value = ids.get(site.provider, "") if site.provider else name
        if not value:
            continue
        template = str(row.get("template") or site.template)
        if _template_problem(site, template):
            template = site.template
        out.append({"site": site.key, "label": site.label,
                    "url": template.replace("{" + site.placeholder + "}",
                                            quote(value, safe=""))})
    return out


def entry_links(root: Path, canonical_name: str, refs) -> list[dict]:
    """读设置并拼出入口。资料页只调这一个。"""
    return build(read(root), canonical_name, refs)
