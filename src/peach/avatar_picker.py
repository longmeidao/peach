"""换头像：列出这个人可选的图，取来其中一张，装上去。

自动挑选按来源优先级走（`gfriends.quality_key`），而那个顺序回答的是「先试哪一张」，
不是「哪一张适合当头像」。实测两类偏差都真实存在：葵つかさ排第一的是一张压着书名的
写真封面，而她的经纪事务所那张正脸原图排第六；横宫七海更直接——她的头像是作品封面
兜底装上的，gfriends 里那 9 张人像因为「文件已存在」从来没被看过一眼。

所以这里的立场是：自动挑一张先用着，人随时能换成别的。可换的来源有四种——图库里
同名的其他候选、这个人自己作品里的画面、本机的图片文件、一个 https 地址。

作品那一路和其余三路的形状不一样：封面是横版封套，九宫格是十六比九的画面，里面
常常还不止一个人。这种图整张装进圆框只会得到一块背景，所以它必须先框出一块再装
（`crop` 那个参数）；人像候选本来就是方图，那三路照旧一点就换。

**换过的图都留着。** 每一张取到的图都按内容哈希进候选缓存，换回去只是再装一次，
不重新下载；被顶下来的那张也在里面，不会因为换了一次就永远找不回来。
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import gfriends, images
from .catalog_rules import normalise_code_key
from .avatar_provider import (
    AvatarCandidateCache, InspectedAvatar, POLICY_VERSION, inspect_avatar,
    install_entity_avatar, provenance_now,
)
from .http import HttpRequest, HttpTransport, public_https_url, resolves_publicly

#: 一次最多给页面列这么多张。同名候选最多的人有十几张，再多就不是选图而是翻图册了。
MAX_CHOICES = 40
#: 候选缓存按来源分目录（`gfriends/`、`social/`、`babepedia/`……），各有自己的
#: `objects/`、`requests/` 与 `evidence/`。取过的图要跨目录找：同一个人的几张图
#: 常常来自不同来源。图库索引和图库对象同处 `gfriends/`。
GFRIENDS_CACHE = "gfriends"
#: 下载一张头像的上限。图库里最大的一张 3 MB 上下，留足余量即可；这个数同时是
#: 「别人给的地址指向一个 4 GB 文件」时我们停下来的地方。
MAX_IMAGE_BYTES = 16 * 1024 * 1024
FETCH_TIMEOUT = 30
#: 证据里的 `provider` 是采集路线的代号，摆到格子底下要换成来源本身的名字：
#: `jae:actress.html#joyu117` 这种串回答的是「批处理怎么再找到它」，不是「这张图哪来的」。
#: 表里没有的按代号原样显示——新来源接进来时先露一个代号，好过盖成一个含混的
#: 「其他」：看到代号的人才知道该来这里补一行。
SOURCE_NAMES = {
    "gfriends": "图库",
    "jae": "展会名录",
    "social-web": "社交主页",
    "cover": "作品封面",
    "cover-fallback": "作品封面",
    "babepedia": "Babepedia",
    "kmib": "官网",
    "picker": "自己挑的",
    "asset": "作品画面",
}
#: 作品那一组一次最多列这么多部。这一组是拿来找一张能框出脸的画面的，不是作品列表；
#: 一个人的作品动辄上百部，全列出来就把图库候选挤到看不见的地方去了。
MAX_ASSET_CHOICES = 12
#: 九宫格的格数。底图可以在这九格加封面之间换，框选在换底图之后重来。
SHEET_CELLS = 9


class PickerError(RuntimeError):
    """这一次换不成，原因可以直接给用户看。"""


@dataclass(frozen=True)
class Choice:
    """一个可选项。`ref` 是前端唯一回递的东西。"""

    ref: str
    source: str
    label: str
    width: int = 0
    height: int = 0
    detail: str = ""
    #: 这一格是按哪个名字从图库里找到的。只有一个名字命中时留空。
    found_by: str = ""
    current: bool = False
    #: 这一格必须先框一块再装。作品画面是横图，整张装进圆框只剩一块背景。
    crop: bool = False
    #: 框选时可以换的底图，按 `ref` 给。空表示这一格只有它自己那一张。
    bases: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"ref": self.ref, "source": self.source, "label": self.label,
                "width": self.width, "height": self.height,
                "detail": self.detail, "found_by": self.found_by,
                "current": self.current, "crop": self.crop,
                "bases": list(self.bases)}


def name_chain(connection: sqlite3.Connection, entity_id: int) -> list[str]:
    """查图库用的名字，按匹配次序：规范名在前，别名在后。

    别名不是锦上添花：大陆简体与日文字体在图库里是两个不同的键（`横宫七海` 与
    `横宮七海`），只拿规范名去查，汉字简化过的那些人一个也找不到。
    """
    names: list[str] = []
    row = connection.execute("SELECT canonical_name FROM entity WHERE id=?",
                             (int(entity_id),)).fetchone()
    if row and row[0]:
        names.append(str(row[0]))
    names += [str(alias) for (alias,) in connection.execute(
        "SELECT alias FROM entity_alias WHERE entity_id=?", (int(entity_id),))
        if alias]
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        key = gfriends.normalized(name)
        if key and key not in seen:
            seen.add(key)
            ordered.append(name)
    return ordered


def installed_digest(avatar_root: Path, kind: str, entity_id: int) -> str:
    """当前装着那张图的哈希，用来在候选里把它标出来。读不到就是空。"""
    from .previews import entity_image_key

    path = avatar_root / f"{entity_image_key(kind, int(entity_id))}.img"
    try:
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()
    except OSError:
        return ""


def _history(providers_root: Path, entity_id: int, current: str) -> list[Choice]:
    """这个人取过的图。证据文件按 `performer-<id>-<sha>.json` 存，天然是一份历史。

    这里给的是「换回去不用重下」的那一批：装过又被顶掉的、批处理下过但没装的，
    都在候选缓存里按内容寻址躺着。跨来源目录找——取过的图未必都来自图库。

    两种记录不列出来：对象已经不在缓存里的（列了也只能点出一句「不在本机缓存里」），
    和整张只有一个颜色的（`images.is_flat`）。后者是来源取不到人像时给的占位底色，
    尺寸格式都合规，摆进候选里就是一块白格子。
    """
    out: list[Choice] = []
    seen: set[str] = set()
    for path in sorted(providers_root.glob(
            f"*/evidence/performer-{int(entity_id)}-*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        digest = str(record.get("sha256") or "")
        # 同一张图可能在几个来源目录里各留了一份证据——摆出来是两个一模一样的格子。
        if not digest or digest in seen:
            continue
        seen.add(digest)
        body = _object_bytes(providers_root, digest)
        if body is None or images.is_flat(body):
            continue
        provider = str(record.get("provider") or "")
        out.append(Choice(
            ref=f"sha256:{digest}", source="history",
            label=SOURCE_NAMES.get(provider, provider or "取过的图"),
            width=int(record.get("width") or 0), height=int(record.get("height") or 0),
            detail=str(record.get("upstream_url") or ""),
            current=digest == current))
    return out


def asset_artwork(connection: sqlite3.Connection, cover_root: Path,
                  entity_id: int) -> list[Choice]:
    """这个人的作品里能拿来框头像的那些画面。

    一部作品只占一格，格上那张是它的封面（没有就是九宫格正中那一格）；点开之后
    底图可以在封面和九宫格九格之间换。列的是作品而不是每一张图：一个人几十部作品
    乘以十张图，摆出来是几百个格子，而人要找的是「哪一部里有一张正脸」。

    没有封面也没铺过九宫格的作品不列：那种格子点开是一片空白。
    """
    rows = connection.execute(
        "SELECT a.id,a.code,COALESCE(NULLIF(a.catalog_title,''),a.name),a.snapshot_path "
        "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
        "WHERE ae.entity_id=? AND a.medium='video' "
        "ORDER BY a.size DESC LIMIT ?",
        (int(entity_id), MAX_ASSET_CHOICES * 3),
    ).fetchall()
    out: list[Choice] = []
    for asset_id, code, title, snapshot in rows:
        if len(out) >= MAX_ASSET_CHOICES:
            break
        key = normalise_code_key(code)
        has_cover = bool(key) and (Path(cover_root) / f"{key}.jpg").is_file()
        has_sheet = bool(snapshot)
        if not has_cover and not has_sheet:
            continue
        bases = ([f"asset:{int(asset_id)}:cover"] if has_cover else [])
        if has_sheet:
            bases += [f"asset:{int(asset_id)}:cell{cell}" for cell in range(SHEET_CELLS)]
        out.append(Choice(
            ref=bases[0], source="asset",
            label=str(code or title or f"作品 {asset_id}"),
            detail=str(title or ""), crop=True, bases=tuple(bases)))
    return out


def choices(connection: sqlite3.Connection, providers_root: Path,
            avatar_root: Path, kind: str, entity_id: int,
            cover_root: Path | None = None) -> dict:
    """页面要展示的一切：图库同名候选、取过的历史、当前装着的是哪一张。

    索引只读本地缓存。联网补索引是批处理的事——为一次点击同步拉 6 MB，页面会卡在
    那里，而卡住的理由用户完全看不见。
    """
    index_dir = providers_root / GFRIENDS_CACHE
    names = name_chain(connection, entity_id)
    index = gfriends.load_index(index_dir)
    match = gfriends.candidates(index, names)
    current = installed_digest(avatar_root, kind, entity_id)
    cache = AvatarCandidateCache(index_dir)
    #: 图库候选里已经取过的那些，按内容哈希记下来。取过的图会同时以「图库某个分类」
    #: 和「这个人取过的图」两种身份出现，摆在一起就是两个一模一样的格子。留图库那
    #: 一边：`S1`、`GRAPHIS` 说得出是谁家的图，「图库」只说得出它从哪个路子来。
    taken: set[str] = set()
    items: list[Choice] = []
    # 好几个名字都命中时，每一格得说得出自己是按哪个名字找来的：找错人是这一屏唯一
    # 会出的大错，而一屏里混着两个人的图时，名字是唯一能看出来的线索。只有一个名字
    # 命中就不必说——那句话对每一格都一样，等于没说。
    tell_finder = len(match.names) > 1
    for category, filename in match.items:
        shot = cache.describe(gfriends.image_url(category, filename)) or {}
        digest = str(shot.get("sha256") or "")
        if digest:
            taken.add(digest)
        items.append(Choice(
            ref=f"gfriends:{category}/{filename}", source="gfriends",
            label=gfriends.category_label(category), detail=filename,
            found_by=match.finder.get((category, filename), "") if tell_finder else "",
            width=int(shot.get("width") or 0), height=int(shot.get("height") or 0),
            current=bool(digest) and digest == current))
    for choice in _history(providers_root, entity_id, current):
        if choice.ref.split(":", 1)[1] not in taken:
            items.append(choice)
    # 在用的那张排第一。它是这一屏唯一的参照物——别的候选好不好，是跟它比出来的；
    # 排在第十二个就得先把它找出来才能开始比。排序是稳定的，其余顺序不动。
    items.sort(key=lambda choice: not choice.current)
    # 作品画面接在人像候选后面，而且不跟它们抢 `MAX_CHOICES` 那个名额：这一组要回答
    # 的是「图库和历史里都没有合用的时候去哪找」，被截在名额外面就等于这条路不存在。
    listed = items[:MAX_CHOICES]
    if cover_root is not None:
        listed += asset_artwork(connection, cover_root, entity_id)
    age = gfriends.index_age(index_dir)
    return {
        "kind": kind, "entity_id": int(entity_id),
        "names": names, "matched_names": list(match.names),
        "choices": [choice.as_dict() for choice in listed],
        "index_age_hours": round(age / 3600, 1) if age is not None else None,
        "index_stale": age is None or age > gfriends.INDEX_MAX_AGE_SECONDS,
    }


def _object_bytes(providers_root: Path, digest: str) -> bytes | None:
    """按内容哈希在各来源目录里找那张图的字节；找不到或读不出就是 None。

    列举候选和真正装上去都要这一步，差别只在读不到时怎么办：列举跳过，安装报错。
    """
    for path in providers_root.glob(f"*/objects/{digest}.*"):
        try:
            body = path.read_bytes()
        except OSError:
            continue
        if hashlib.sha256(body).hexdigest() == digest:
            return body
    return None


def _cached_object(providers_root: Path, digest: str) -> bytes:
    """按内容哈希取那张图。路径可能过期，内容不会。"""
    body = _object_bytes(providers_root, digest)
    if body is None:
        raise PickerError("这张图不在本机缓存里了")
    return body


def fetch_image(transport: HttpTransport, url: str) -> bytes:
    """取一张图。`url` 必须已经过 `allowed_source` 或由我们自己拼出来。"""
    try:
        response = transport(
            HttpRequest("GET", url, {"Accept": "image/*"}),
            FETCH_TIMEOUT, MAX_IMAGE_BYTES)
    except Exception as error:  # noqa: BLE001 — 网络层什么都可能抛
        raise PickerError(f"取不到这张图：{error}") from error
    if response is None or response.status != 200:
        status = "无响应" if response is None else f"HTTP {response.status}"
        raise PickerError(f"取不到这张图：{status}")
    return response.body


def allowed_source(url: str) -> bool:
    """用户手填的地址能不能让 Peach 去取。

    Peach 跑在用户自己的机器上，它能访问路由器后台、NAS、局域网里别的服务和本机
    各个端口。「你给地址我去下」如果不设边界，就是一个替人发请求的跳板：填
    `http://127.0.0.1:8080/admin` 进来，Peach 会替人去访问，再把结果当图片存下。
    判据与追更代理共用一份（`http.public_https_url` 加 `http.resolves_publicly`）：
    必须 https、必须是公网域名、不能是 IP 字面量、解析出来的每一个地址都得是公网的。
    """
    if not public_https_url(url):
        return False
    return resolves_publicly(urllib.parse.urlsplit(url).hostname or "")


def accept_image(body: bytes) -> InspectedAvatar:
    """确认这堆字节真是一张能用的图。格式由解码结果定，不看扩展名也不信响应头。"""
    if len(body) > MAX_IMAGE_BYTES:
        raise PickerError("图太大了")
    inspected = inspect_avatar(body)
    if inspected is None:
        raise PickerError("这不是一张能识别的 JPEG 或 PNG 图片")
    return inspected


@dataclass(frozen=True)
class ArtworkSource:
    """作品画面从哪来。端点把这两样拼好递进来，这一层不认识预览服务。"""

    cover_root: Path
    #: `(asset_id, cell) -> 那一格的路径或 None`。九宫格没铺过时由它现抽一张。
    frame: Callable[[int, int], Path | None]


def _asset_image(ref: str, connection: sqlite3.Connection, entity_id: int,
                 artwork: ArtworkSource | None) -> tuple[bytes, dict]:
    """`asset:<id>:cover` / `asset:<id>:cell<n>` → 那张图的字节和来源记录。

    作品必须真的挂在这个人身上才给。页面只会递自己刚列出来的那些，但这一层不能
    依赖那一点：`asset:1:cover` 是个人都拼得出来，凭它就能把任意一部作品的封面
    读出来，而资料页本来看不到那部作品。
    """
    if artwork is None:
        raise PickerError("这一次取不到作品画面")
    _, _, rest = ref.partition(":")
    raw_id, _, what = rest.partition(":")
    try:
        asset_id = int(raw_id)
    except ValueError as error:
        raise PickerError("认不出这个候选") from error
    row = connection.execute(
        "SELECT a.code FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
        "WHERE ae.entity_id=? AND ae.asset_id=?",
        (int(entity_id), asset_id)).fetchone()
    if row is None:
        raise PickerError("这部作品不在这个人名下")
    if what == "cover":
        key = normalise_code_key(row[0])
        path = (Path(artwork.cover_root) / f"{key}.jpg") if key else None
        label = "封面"
    elif what.startswith("cell"):
        try:
            cell = int(what[len("cell"):])
        except ValueError as error:
            raise PickerError("认不出这个候选") from error
        if not 0 <= cell < SHEET_CELLS:
            raise PickerError("认不出这个候选")
        path = artwork.frame(asset_id, cell)
        label = f"第 {cell + 1} 格"
    else:
        raise PickerError("认不出这个候选")
    if path is None or not Path(path).is_file():
        raise PickerError(f"这部作品的{label}还没有落在本机")
    try:
        body = Path(path).read_bytes()
    except OSError as error:
        raise PickerError(f"读不出这部作品的{label}") from error
    return body, {"source": "avatar picker", "provider": "asset",
                  "external_id": f"{asset_id}:{what}",
                  "asset_id": asset_id, "asset_code": str(row[0] or "")}


def resolve(ref: str, connection: sqlite3.Connection, providers_root: Path,
            entity_id: int,
            transport: HttpTransport | None,
            artwork: ArtworkSource | None = None) -> tuple[bytes, dict]:
    """把页面回递的 `ref` 换成图片字节和一份来源记录。

    `ref` 只认这里自己刚枚举出来的那些：图库候选要在索引里真的存在，历史候选要在
    缓存里真的有对象。页面递不进任意地址——手填地址是另一条路，它有自己的边界。
    """
    if ref.startswith("sha256:"):
        digest = ref.split(":", 1)[1].strip().lower()
        body = _cached_object(providers_root, digest)
        return body, {"source": "avatar picker", "provider": "history",
                      "external_id": digest[:12]}
    if ref.startswith("asset:"):
        return _asset_image(ref, connection, entity_id, artwork)
    if not ref.startswith("gfriends:"):
        raise PickerError("认不出这个候选")
    category, _, filename = ref.split(":", 1)[1].partition("/")
    index = gfriends.load_index(providers_root / GFRIENDS_CACHE)
    match = gfriends.candidates(index, name_chain(connection, entity_id))
    if (category, filename) not in match.finder:
        raise PickerError("这个候选不在当前索引里")
    # 证据里记的是找到这一张的那个名字，不是整条链：事后要答的是「这张图凭什么算他」。
    matched = match.finder[(category, filename)]
    url = gfriends.image_url(category, filename)
    cache = AvatarCandidateCache(providers_root / GFRIENDS_CACHE)
    body = cache.lookup(url)
    if body is None:
        if transport is None:
            raise PickerError("这张图还没下载过，而这一次不允许联网")
        body = fetch_image(transport, url)
    return body, {"source": "avatar picker", "provider": "gfriends",
                  "gfriends_category": category, "gfriends_file": filename,
                  "matched_name": matched, "name_source": "picker",
                  "external_id": f"{category}/{filename}", "upstream_url": url}


def crop(body: bytes, box: object) -> tuple[bytes, dict]:
    """按源图像素框切出头像那一块，连同一份记着框的来源补充。

    原图不动：切出来的是新字节，被切的那张（作品封面、九宫格的一格）还在原处。
    装上去之后这份新字节自己进候选缓存，所以同一个框换回来不必再切一次。
    """
    size = images.measure_image_size(body)
    if size is None:
        raise PickerError("这不是一张能识别的图片")
    edges = images.clamp_box(box, size[0], size[1])
    if edges is None:
        raise PickerError("框选的区域不成立")
    cropped = images.crop_to_box(
        body, (edges["x0"], edges["y0"], edges["x1"], edges["y1"]))
    if cropped is None:
        raise PickerError("这一块裁不出来")
    return cropped, {"source_kind": "user_cropped",
                     "crop_box": [edges["x0"], edges["y0"], edges["x1"], edges["y1"]],
                     "crop_source_px": [size[0], size[1]]}


def install(providers_root: Path, avatar_root: Path, kind: str,
            entity_id: int, body: bytes, origin: dict) -> dict:
    """装上去，同时把这张图连同证据留在候选缓存里——换回来时就不必再取一次。"""
    inspected = accept_image(body)
    cache = AvatarCandidateCache(
        providers_root / str(origin.get("provider") or "picker"))
    url = str(origin.get("upstream_url") or f"peach:picker/{inspected.sha256}")
    cache.store(url, body, inspected)
    cache.store_provenance(provenance_now(
        entity_id=int(entity_id), provider=str(origin.get("provider") or "picker"),
        source_kind=str(origin.get("source_kind") or "user_selected"),
        matched_name=str(origin.get("matched_name") or ""),
        name_source=str(origin.get("name_source") or "picker"),
        external_id=str(origin.get("external_id") or ""), upstream_url=url,
        width=inspected.width, height=inspected.height,
        mime_type=inspected.mime_type, sha256=inspected.sha256,
        cache_path=f"objects/{inspected.sha256}{inspected.extension}"))
    install_entity_avatar(avatar_root, kind, int(entity_id), body,
                          inspected.mime_type,
                          {**origin, "sha256": inspected.sha256,
                           "width": inspected.width, "height": inspected.height,
                           "policy_version": POLICY_VERSION})
    return {"sha256": inspected.sha256, "width": inspected.width,
            "height": inspected.height, "mime_type": inspected.mime_type}
