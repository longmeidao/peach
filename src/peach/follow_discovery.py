"""从一个裸 id 或名字反查它在哪些站点上存在。

粘链接是精确的，但人手边常常只有一个名字或一串数字。这一层把那个词拿去各个来源
问一遍，把**查到的**结果摆出来让人选——不猜、不自动登记，查不到就说查不到。

联网只在显式调用 `discover()` 时发生。每个来源独立成败：一个站点挂了或缺凭据，
不该让其余来源的结果一起消失。
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

from .follow import FollowSourceError
from .follow_secrets import Credential, CredentialError, CredentialStore
from .follow_sources import (
    DEFAULT_MAX_ITEMS, USER_AGENT, F95ZoneConnector, KemonoConnector,
    Rule34VideoConnector, Rule34XxxConnector, _BaseConnector, canonical_source_ref,
)

#: 创作者索引的缓存有效期。索引是几 MB 的整站清单，不该每次发现都重下一遍。
CREATOR_INDEX_TTL_SECONDS = 24 * 3600

#: 单个来源最多回多少个候选。发现是给人看的，不是导出整站。
MAX_CANDIDATES_PER_SOURCE = 8

_NUMERIC_RE = re.compile(r"^\d{1,12}$")
#: 名字里不能出现的字符：路径分隔、查询串标点和控制字符。除此之外一律放行——
#: kemono 上大量创作者是日文或中文名（`うるしばら`、`冰鲜鱼子酱二代目`），
#: 用「只允许 ASCII」的白名单会把他们整批挡在门外。
_TERM_FORBIDDEN_RE = re.compile(r"[/\\?#&<>\"'`\x00-\x1f\x7f]")
MAX_TERM_LENGTH = 80


@dataclass(frozen=True)
class Candidate:
    """一个查到的、可以登记的来源。"""

    provider: str
    ref: str
    url: str
    label: str
    semantics: str
    #: 为什么认为它命中了。界面照实显示，不要替用户断言「就是这个」。
    evidence: str


@dataclass(frozen=True)
class ExternalSearch:
    """站内索引没命中时，交给人继续核对的外部搜索入口。"""

    provider: str
    label: str
    query: str
    url: str
    evidence: str


@dataclass(frozen=True)
class Discovery:
    term: str
    candidates: tuple[Candidate, ...] = ()
    #: 逐来源的失败原因；界面要显示，否则「没查到」和「没查成」分不开。
    failures: dict[str, str] = field(default_factory=dict)
    #: 搜索引擎只提供继续核对的入口，不伪装成可直接登记的来源。
    external_searches: tuple[ExternalSearch, ...] = ()


class CreatorIndex:
    """kemono 系整站创作者清单的本机缓存。

    这三个站点没有按名字查创作者的接口，只有一份整站清单（实测 2–6 MB）。
    与其对着几十种服务名盲探 `/{service}/user/{id}/profile`，不如下一次清单，
    id 和名字都能精确命中，而且缓存一天之后后续发现是零网络开销。
    """

    def __init__(self, state_root: Path, *, transport=None, ttl: float = CREATOR_INDEX_TTL_SECONDS):
        self.root = Path(state_root) / "follow"
        self.transport = transport
        self.ttl = ttl

    def _path(self, provider: str) -> Path:
        return self.root / f"creators-{provider}.json"

    def load(self, provider: str, *, now: float | None = None) -> list[dict]:
        path = self._path(provider)
        now = now if now is not None else time.time()
        try:
            if path.is_file() and (now - path.stat().st_mtime) < self.ttl:
                cached = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(cached, list):
                    return cached
        except (OSError, ValueError):
            pass
        return self._refresh(provider, path)

    def _refresh(self, provider: str, path: Path) -> list[dict]:
        connector = KemonoConnector(provider=provider, transport=self.transport,
                                    max_bytes=48 * 1024 * 1024)
        response = connector._get(f"https://{connector.host}/api/v1/creators")
        connector._check_status(response)
        payload = connector._json(response)
        if not isinstance(payload, list):
            raise FollowSourceError(f"{provider} 的创作者清单格式不符")
        rows = [
            {"id": str(row.get("id") or ""), "name": str(row.get("name") or ""),
             "service": str(row.get("service") or "")}
            for row in payload if isinstance(row, dict) and row.get("id")
        ]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            # 缓存写不进去不影响这一次发现，只是下次要重下。
            pass
        return rows


def _kemono_candidates(provider: str, term: str, index: CreatorIndex) -> list[Candidate]:
    rows = index.load(provider)
    folded = term.casefold()
    numeric = bool(_NUMERIC_RE.match(term))
    exact_id = [row for row in rows if numeric and row["id"] == term]
    by_name = [row for row in rows if row["name"].casefold() == folded]
    partial = [row for row in rows
               if folded in row["name"].casefold() and row not in by_name]
    host = KemonoConnector.HOSTS[provider]
    picked, seen = [], set()
    for row, why in ([(r, "站内 id 精确匹配") for r in exact_id]
                     + [(r, "创作者名精确匹配") for r in by_name]
                     + [(r, "创作者名包含该词") for r in partial]):
        key = (row["service"], row["id"])
        if key in seen:
            continue
        seen.add(key)
        picked.append(Candidate(
            provider, f"{row['service']}/{row['id']}",
            f"https://{host}/{row['service']}/user/{row['id']}",
            f"{row['name']} · {row['service']}", "work", why))
        if len(picked) >= MAX_CANDIDATES_PER_SOURCE:
            break
    return picked


def _rule34video_candidates(term: str, transport) -> list[Candidate]:
    slug = re.sub(r"[^a-z0-9]+", "", term.casefold())
    if not slug:
        return []
    connector = Rule34VideoConnector(transport=transport)
    response = connector._get(f"https://rule34video.com/models/{slug}/",
                              headers={"Accept": "text/html"})
    if response.status != 200:
        return []
    return [Candidate("rule34video", slug,
                      f"https://rule34video.com/models/{slug}/",
                      term.strip(), "work", "作者页存在")]


def _rule34xxx_candidates(term: str, transport, credential: Credential | None) -> list[Candidate]:
    if credential is None:
        raise CredentialError("rule34xxx 需要 user_id 与 api_key 才能查标签")
    tag = canonical_source_ref("rule34xxx", re.sub(r"\s+", "_", term.strip()))
    connector = Rule34XxxConnector(transport=transport, credential=credential, max_items=1)
    result = connector.fetch(tag)
    if not result.candidates:
        return []
    return [Candidate("rule34xxx", tag,
                      "https://rule34.xxx/index.php?page=post&s=list"
                      f"&tags={urllib.parse.quote(tag)}",
                      tag.replace("_", " "), "work", "标签下有作品")]


def search_variants(term: str) -> tuple[str, ...]:
    """一个词的几种写法。

    f95 的全文搜索按词匹配，`lazyprocrastinator` 搜不到而 `lazy procrastinator` 能。
    下划线、连字符和大小写边界都是明确的切分信号；全小写的连写仍然切不开，
    那就只用原词，不去猜词典。
    """
    text = term.strip()
    variants = [text]
    separated = re.sub(r"[_-]+", " ", text).strip()
    if separated != text and separated not in variants:
        variants.append(separated)
    split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text).strip()
    if split != text and split not in variants:
        variants.append(split)
    return tuple(variants)


def _f95_external_search(term: str) -> ExternalSearch:
    """Google 由浏览器打开；Peach 不抓结果页，也不绕验证码。"""
    query = f"{term} f95zone"
    return ExternalSearch(
        provider="f95zone",
        label="用 Google 继续查找 F95zone",
        query=query,
        url="https://www.google.com/search?" + urllib.parse.urlencode({"q": query}),
        evidence="F95zone 站内索引未命中，请核对搜索结果里的真实线程链接",
    )


def _f95_candidates(term: str, transport) -> list[Candidate]:
    connector = F95ZoneConnector(transport=transport)
    picked: list[Candidate] = []
    if _NUMERIC_RE.match(term):
        response = connector._get(f"https://f95zone.to/threads/{term}/",
                                  headers={"Accept": "text/html"})
        if response.status == 200:
            picked.append(Candidate("f95zone", term,
                                    f"https://f95zone.to/threads/{term}/",
                                    f"线程 {term}", "release", "线程存在"))
        return picked
    seen: set[str] = set()
    for query in search_variants(term):
        for category in connector.CATEGORIES:
            for row in connector.thread_index(category, query):
                thread = str(row.get("thread_id") or "")
                if not thread or thread in seen:
                    continue
                seen.add(thread)
                version = str(row.get("version") or "").strip()
                picked.append(Candidate(
                    "f95zone", thread, f"https://f95zone.to/threads/{thread}/",
                    str(row.get("title") or f"线程 {thread}"), "release",
                    f"{category} 分类命中" + (f"，当前版本 {version}" if version else "")))
                if len(picked) >= MAX_CANDIDATES_PER_SOURCE:
                    return picked
        if picked:
            return picked
    return picked


def discover(term: str, *, secrets_root: Path, state_root: Path,
             transport=None, providers: tuple[str, ...] | None = None) -> Discovery:
    """把一个裸 id 或名字拿去各来源问一遍。

    只回**查到的**结果，每个都带上「为什么认为它命中」。查不到就是查不到，
    不按命名规律拼一个看起来像的链接——那种猜测登记之后永远抓不到东西。
    """
    text = (term or "").strip()
    if not text:
        raise FollowSourceError("请先输入要查找的名字或 id")
    if len(text) > MAX_TERM_LENGTH:
        raise FollowSourceError(f"名字或 id 最长 {MAX_TERM_LENGTH} 个字符")
    if _TERM_FORBIDDEN_RE.search(text):
        raise FollowSourceError("名字或 id 里不能包含 / \\ ? # & < > 引号或控制字符")

    credentials = CredentialStore(secrets_root)
    index = CreatorIndex(state_root, transport=transport)
    wanted = providers or ("kemono", "coomer", "pawchive", "rule34video",
                           "rule34xxx", "f95zone")
    found: list[Candidate] = []
    failures: dict[str, str] = {}
    external_searches: list[ExternalSearch] = []

    def run(name: str, fn) -> None:
        if name not in wanted:
            return
        try:
            found.extend(fn())
        except (FollowSourceError, CredentialError) as error:
            failures[name] = str(error)

    for provider in ("kemono", "coomer", "pawchive"):
        run(provider, lambda provider=provider: _kemono_candidates(provider, text, index))
    if not _NUMERIC_RE.match(text):
        run("rule34video", lambda: _rule34video_candidates(text, transport))
        run("rule34xxx",
            lambda: _rule34xxx_candidates(text, transport,
                                          credentials.load("rule34xxx")))
    run("f95zone", lambda: _f95_candidates(text, transport))
    if "f95zone" in wanted and not any(row.provider == "f95zone" for row in found):
        external_searches.append(_f95_external_search(text))
    return Discovery(text, tuple(found), failures, tuple(external_searches))
