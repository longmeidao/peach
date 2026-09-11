"""Read-only external metadata providers and Peach-owned candidate normalization."""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from .config import STATE_DIR, TOOLS_DIR
from .catalog_rules import same_release_code, code_query_variants, normalise_code_key
from .genre_taxonomy import map_genres, unmapped_genre_warning
from .http import body_text
from .javdb import LOGIN as JAVDB_LOGIN_PAGE
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
)


JAVINIZER_GO_VERSION = "1.5.1"
#: 日期式那一支两种分隔符都放行：`_` 是一本道等片商的标识，不是可替换的写法
#: （`catalog_rules._CODE_DATE`）。这里拦的是路径、URL 和任意文本，不是分隔符。
_SAFE_CODE = re.compile(
    r"^(?:FC2-PPV-\d{5,}|\d{3}[A-Z]{2,6}-\d{2,5}|[A-Z]{2,8}-\d{2,5}|\d{6}[-_]\d{2,4})$")
CATALOG_EVIDENCE_FIELDS = (
    "title", "original_title", "runtime", "director", "label",
    "poster_url", "cover_url", "screenshot_urls", "trailer_url",
)
MAX_EVIDENCE_URLS = 24


class MetadataProviderError(RuntimeError):
    """来源没给出结果的原因。`kind` 是分类，不是措辞。

    `auth` 单列一档：登录墙、Cookie 过期和 401/403 与「这次没问出结果」不是一回事，
    和「这部片不存在」更不是。混在 `unavailable` 里的代价有两样：一是每个番号都要为
    同一把锁再付一次往返，本批几百次请求全部注定失败；二是批处理按 `unavailable` 退让
    几百秒后又回来重试，而凭据不换，重试多少次都是同一个结果。

    `auth` 固定 `retryable=False`（同一份凭据再问一次不会变）、`temporary=True`
    （换一份 Cookie 就能继续，所以不能作为定论冻进快照——`SETTLED_ERROR_KINDS`
    只收 `not_found`）。
    """

    def __init__(
        self, message: str, *, kind: str = "unknown", status_code: int = 0,
        retryable: bool = False, temporary: bool = False,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retryable = retryable
        self.temporary = temporary


#: 站方在 HTTP 上直说「你没有通行证」的两个状态码。
AUTH_STATUS_CODES = frozenset({401, 403})

#: 重定向终点落在这些路径上就是登录墙或年龄闸。站方不一定回 401：javdb 对未登录
#: 用户访问部分详情页直接 302 到 `/login`，DMM 把未过年龄闸的请求送去
#: `/age_check/`，跟完重定向拿到的都是一页 200。按状态码判会读成「取到了」，
#: 按正文判会读成「查无此片」，只有最终地址能把它认出来（NeoAVDC 的
#: `JavDbSource.ts` 用的也是这一条）。
LOGIN_LOCATIONS = re.compile(
    r"/(?:login|signin|sign_in|users/sign_in|account/login|auth/login|age_?check)(?:[/?.]|$)",
    re.IGNORECASE,
)

#: 站方自己给出的登录页标记。只认页面身份这种固定结构，不按「正文里出现登录二字」
#: 猜——搜索结果页和页脚都会出现那两个字。javdb 那条判据留在 `peach.javdb`，
#: 采集脚本按页判「这一页是不是登录墙」用的是同一份。
_AUTH_PAGE_MARKERS = ((JAVDB_LOGIN_PAGE, "javdb 登录页"),)


def auth_wall_reason(*, status_code: int = 0, final_url: str = "",
                     body: bytes | str = b"") -> str:
    """这次响应是不是「要登录才给看」。是就返回写进错误消息的理由，否则空串。

    三条判据各自对应真实存在的一种形态，缺一条就有来源漏判：明确的 401/403、
    跟完重定向后落在登录页或年龄闸、以及状态 200 但正文就是登录页。
    """
    if status_code in AUTH_STATUS_CODES:
        return f"来源返回 {status_code}"
    path = urlsplit(str(final_url or "")).path
    if path and LOGIN_LOCATIONS.search(path):
        return f"重定向终点落在 {path}"
    text = body_text(body) if isinstance(body, bytes) else str(body)
    for pattern, label in _AUTH_PAGE_MARKERS:
        if pattern.search(text):
            return label
    return ""


def auth_error(source: str, reason: str, *, status_code: int = 0) -> MetadataProviderError:
    """把一次鉴权失败包成 `kind="auth"` 的错误。措辞只有这一处。"""
    return MetadataProviderError(
        f"{source} 需要登录或已被拒绝：{reason}", kind="auth",
        status_code=status_code, retryable=False, temporary=True,
    )


def _platform_tool_path() -> Path | None:
    machine = platform.machine().lower()
    if sys.platform == "darwin" and machine in {"arm64", "aarch64"}:
        return TOOLS_DIR / "javinizer" / f"v{JAVINIZER_GO_VERSION}" / "darwin-arm64" / "javinizer"
    if os.name == "nt" and machine in {"amd64", "x86_64"}:
        return TOOLS_DIR / "javinizer" / f"v{JAVINIZER_GO_VERSION}" / "windows-amd64" / "javinizer.exe"
    if sys.platform.startswith("linux") and machine in {"amd64", "x86_64"}:
        return TOOLS_DIR / "javinizer" / f"v{JAVINIZER_GO_VERSION}" / "linux-amd64" / "javinizer"
    if sys.platform.startswith("linux") and machine in {"arm64", "aarch64"}:
        return TOOLS_DIR / "javinizer" / f"v{JAVINIZER_GO_VERSION}" / "linux-arm64" / "javinizer"
    return None


def resolve_javinizer_binary(explicit: str | Path | None = None) -> Path:
    """Resolve a pinned local tool before falling back to PATH."""
    requested = str(explicit or os.environ.get("PEACH_JAVINIZER_BIN") or "").strip()
    candidates = [Path(requested)] if requested else []
    bundled = _platform_tool_path()
    if bundled is not None:
        candidates.append(bundled)
    on_path = shutil.which("javinizer")
    if on_path:
        candidates.append(Path(on_path))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    expected = str(bundled) if bundled is not None else "PEACH_JAVINIZER_BIN"
    raise MetadataProviderError(f"Javinizer-Go v{JAVINIZER_GO_VERSION} 未安装：{expected}")


def validate_provider_code(code: str) -> str:
    value = str(code or "").strip().upper()
    if not _SAFE_CODE.fullmatch(value):
        raise ValueError("metadata provider 只接受规范化番号，不接受路径、URL 或任意文本")
    return value


#: 番号在来源返回里的身份证据。`id`、`content_id` 和 `source_url` 至少有一处
#: 要认得出这个番号，否则拿到的是别的商品。
IDENTITY_FIELDS = ("id", "content_id", "source_url")


def _compact(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


#: URL 里可能承载番号的片段。路径段与查询值都可能是它，`combined=ene009` 这种
#: 还要按 `=` 再切一层才拿得到右边那一半。
_URL_TOKEN = re.compile(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9]+)*")


def _release_writings(payload: dict) -> list[str]:
    """payload 里所有可能是番号写法的片段，逐个交给 `same_release_code` 比。"""
    values = [str(payload.get(field) or "") for field in ("id", "content_id")]
    url = urlsplit(str(payload.get("source_url") or ""))
    blob = f"{url.path.replace('/', ' ')} {url.query.replace('&', ' ')}"
    for chunk in blob.split():
        values.extend(_URL_TOKEN.findall(chunk))
        if "=" in chunk:
            values.append(chunk.split("=", 1)[-1])
    return [value for value in values if value]


def identifies_code(code: str, payload: dict) -> bool:
    """来源返回的是不是这个番号本身。

    2026-09-01 实测：dl.getchu 对 `ABW-220` 和 `259LUXU-1475` 都返回同一件同人
    商品 `item33938`（`Gカップ黒髪ぱっつん美少女レイヤー05華仙`）。适配器取的是
    站内搜索首条命中，站里没有这个番号时它不报「查无此片」，而是把不相干的商品
    当结果交出来。没有这道闸，那件商品的 genre 会变成三个番号的官方标签。

    真实来源的写法要容得下：DMM 的 `118abw220` 带厂牌数字前缀，r18dev 的
    `h_086iqqq00026` 对 `IQQQ-026` 多补了零，`259LUXU-1475` 只在 URL 里出现。
    实测 800 条成功快照里，除 dl.getchu 的 3 条错配外全部命中。

    先问 `same_release_code`，它认得 FC2 的裸数字写法和登记过的前缀别名；下面那套
    正则不认，于是把 `FC2-PPV-3701252` 和来源返回的 `3701252` 判成两部作品。2026-09-09
    实测候选池里 450 条 fc2 候选全部因此被误判为错配，占当时判否总数的一半以上。
    两条判据取并集：`same_release_code` 严格但不认厂牌数字前缀（`MAAN-545` 与
    `300MAAN-545`），正则宽松但认得，去掉任何一条都有 16 条合法候选被误拒。
    """
    if any(same_release_code(code, writing) for writing in _release_writings(payload)):
        return True
    if re.match(r"^\d{3}[A-Z]", str(code or "").upper()):
        url = urlsplit(str(payload.get("source_url") or ""))
        product = re.fullmatch(r"/product/product_detail/([^/]+)/?", url.path)
        returned = str(payload.get("id") or payload.get("content_id") or "")
        if url.hostname in {"mgstage.com", "www.mgstage.com"} and product:
            product_code = product.group(1)
            return same_release_code(code, product_code) and (
                not returned or same_release_code(product_code, returned)
                or normalise_code_key(returned) in code_query_variants(product_code))
        return any(same_release_code(code, payload.get(field)) for field in ("id", "content_id"))
    blob = "|".join(_compact(payload.get(field)) for field in IDENTITY_FIELDS)
    if not blob.strip("|"):
        return False
    value = str(code or "").upper()
    matched = re.fullmatch(r"(?:\d{3,6})?([A-Z]{2,8})-?(\d{2,5})", value)
    if matched:
        letters, digits = matched.group(1).lower(), matched.group(2).lstrip("0") or "0"
        return any(re.search(rf"(?<![a-z]){letters}[-_]?0*{digits}(?!\d)",
                             str(payload.get(field) or "").lower()) is not None
                   for field in IDENTITY_FIELDS)
    return _compact(value) in blob



Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class JavinizerGoProvider:
    """Query one enabled Javinizer-Go scraper without its organizer or database flow."""

    binary: Path
    config_path: Path = STATE_DIR / "javinizer-provider" / "config.yaml"
    timeout: int = 45
    runner: Runner = subprocess.run

    @classmethod
    def create(
        cls, binary: str | Path | None = None, config_path: str | Path | None = None,
        timeout: int = 45, runner: Runner = subprocess.run,
    ) -> "JavinizerGoProvider":
        resolved = resolve_javinizer_binary(binary)
        try:
            version = runner(
                [str(resolved), "version", "--short"], capture_output=True, text=True,
                encoding="utf-8", errors="strict", timeout=10, check=False, shell=False,
            )
        except OSError as exc:
            raise MetadataProviderError(f"无法验证 Javinizer-Go 版本：{exc}") from exc
        if version.returncode or version.stdout.strip() != f"v{JAVINIZER_GO_VERSION}":
            actual = version.stdout.strip() or version.stderr.strip() or f"exit {version.returncode}"
            raise MetadataProviderError(
                f"Javinizer-Go 版本不匹配：需要 v{JAVINIZER_GO_VERSION}，实际 {actual}"
            )
        return cls(
            resolved,
            Path(config_path) if config_path else STATE_DIR / "javinizer-provider" / "config.yaml",
            timeout,
            runner,
        )

    def query(self, code: str, source: str) -> dict:
        query = validate_provider_code(code)
        scraper = str(source or "").strip()
        if not re.fullmatch(r"[a-z0-9_-]+", scraper):
            raise ValueError("invalid Javinizer-Go scraper name")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.binary), "--config", str(self.config_path), "scrape", query,
            "--output", "json", "--scrapers", scraper,
        ]
        try:
            completed = self.runner(
                command, capture_output=True, text=True, timeout=self.timeout,
                encoding="utf-8", errors="strict", check=False, shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise MetadataProviderError(
                f"{scraper} 查询超时", kind="unavailable", retryable=True, temporary=True,
            ) from exc
        except OSError as exc:
            raise MetadataProviderError(f"无法启动 Javinizer-Go：{exc}") from exc
        try:
            payload = json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError) as exc:
            detail = (completed.stderr or completed.stdout or "empty output").strip()[-800:]
            raise MetadataProviderError(f"Javinizer-Go 返回了非 JSON 输出：{detail}") from exc
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            error = payload["error"]
            status = int(error.get("status_code") or 0)
            message = str(error.get("message") or "Javinizer-Go query failed")
            # Javinizer-Go 不分鉴权这一档，它把 401/403 和登录页一起归进自己的
            # 通用错误。状态码和最终地址它照实给了，所以这道判定放在适配器这一侧：
            # 不改上游，也不让「站点把我们挡在门外」继续伪装成「这次没问到」。
            reason = auth_wall_reason(status_code=status,
                                      final_url=str(error.get("url") or ""))
            if reason or str(error.get("kind") or "") == "auth":
                raise auth_error(scraper, reason or message, status_code=status)
            raise MetadataProviderError(
                message,
                kind=str(error.get("kind") or "unknown"),
                status_code=status,
                retryable=bool(error.get("retryable")),
                temporary=bool(error.get("temporary")),
            )
        if completed.returncode or not isinstance(payload, dict):
            raise MetadataProviderError(f"Javinizer-Go 查询失败（exit {completed.returncode}）")
        if str(payload.get("source") or "").strip() != scraper:
            raise MetadataProviderError("Javinizer-Go 返回来源与请求来源不一致")
        if not identifies_code(query, payload):
            raise MetadataProviderError(
                f"{scraper} 返回的商品不是 {query}："
                f"id={payload.get('id')!r} content_id={payload.get('content_id')!r}",
                kind="not_found",
            )
        return payload


def collapse_repeated_phrase(value: str) -> tuple[str, bool]:
    """Compatibility wrapper around Peach's shared entity-name gate."""
    original = str(value or "").strip()
    cleaned = collapse_repeated_entity_name(original)
    return cleaned, cleaned != original


def normalized_performers(raw: object) -> tuple[list[dict], list[str]]:
    performers: list[dict] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        preferred = item.get("japanese_name") or " ".join(
            part for part in (item.get("last_name"), item.get("first_name")) if part
        )
        original = str(preferred or "").strip()
        name = canonicalize_entity_name("performer", original)
        repeated = bool(name and name != original)
        if repeated:
            warnings.append(f"来源演员名含重复片段，已规范化：{preferred} → {name}")
        key = normalize_entity_name(name)
        if not name or key in seen:
            continue
        seen.add(key)
        performers.append({
            "name": name,
            "external_id": str(item.get("dmm_id") or ""),
            "thumb_url": str(item.get("thumb_url") or ""),
        })
    return performers, warnings


def normalized_release_date(raw: object) -> tuple[str, list[str]]:
    value = str(raw or "").strip()
    if not value:
        return "", []
    candidate = value[:10]
    try:
        normalized = date.fromisoformat(candidate).isoformat()
    except ValueError:
        return "", [f"来源发行日期无效，已忽略：{value}"]
    warnings = [] if value == normalized else [f"来源发行时间已规范化为日期：{value} → {normalized}"]
    return normalized, warnings


def japanese_view(payload: dict) -> dict:
    """Return the Japanese translation bundled in an r18dev payload."""
    for translation in payload.get("translations") or []:
        if not isinstance(translation, dict):
            continue
        if str(translation.get("language") or "").lower().startswith("ja"):
            return translation
    return {}


def _normalized_text(raw: object) -> str:
    return " ".join(str(raw or "").split())


def _text_evidence(raw: object) -> dict | None:
    value = _normalized_text(raw)
    if not value:
        return None
    return {"value": value, "display_value": value, "warnings": []}


def _runtime_evidence(raw: object) -> dict | None:
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        minutes = float(raw)
    except (TypeError, ValueError):
        return None
    if not 0 < minutes <= 24 * 60:
        return None
    value: int | float = int(minutes) if minutes.is_integer() else round(minutes, 2)
    return {"value": value, "display_value": f"{value:g} 分钟", "warnings": []}


def _safe_evidence_url(raw: object) -> str:
    value = str(raw or "").strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None):
        return ""
    return value


def _url_evidence(raw: object, label: str) -> dict | None:
    value = _safe_evidence_url(raw)
    if not value:
        return None
    host = urlsplit(value).hostname or "外部来源"
    return {"value": value, "display_value": f"{label}（{host}）", "warnings": []}


def _url_list_evidence(raw: object, label: str) -> dict | None:
    if not isinstance(raw, list):
        return None
    values = list(dict.fromkeys(
        value for value in (_safe_evidence_url(item) for item in raw) if value
    ))
    if not values:
        return None
    warnings = []
    if len(values) > MAX_EVIDENCE_URLS:
        warnings.append(
            f"来源返回 {len(values)} 个链接；候选只保留前 {MAX_EVIDENCE_URLS} 个，完整值仍在原始快照"
        )
        values = values[:MAX_EVIDENCE_URLS]
    hosts = list(dict.fromkeys(urlsplit(value).hostname or "外部来源" for value in values))
    host_label = "、".join(hosts[:2]) + (" 等" if len(hosts) > 2 else "")
    return {
        "value": values,
        "display_value": f"{len(values)} {label}（{host_label}）",
        "warnings": warnings,
    }


def extract_catalog_evidence(payload: dict) -> dict[str, dict]:
    """Preserve source-only catalog fields without mapping them to ledger truth.

    MetaTube's richer movie DTO is used as a fixed-revision checklist. These
    values stay attached to the source candidate: ``label`` is not silently
    folded into Peach ``studio``; catalog runtime never overrides probed media
    duration; remote media URLs are evidence only and are not downloaded here.
    """
    japanese = japanese_view(payload)
    out: dict[str, dict] = {}
    text_fields = {
        "title": japanese.get("title") or payload.get("title"),
        "original_title": payload.get("original_title"),
        "director": japanese.get("director") or payload.get("director"),
        "label": japanese.get("label") or payload.get("label"),
    }
    for field, raw in text_fields.items():
        evidence = _text_evidence(raw)
        if evidence is not None:
            out[field] = evidence
    if (out.get("original_title", {}).get("value")
            == out.get("title", {}).get("value")):
        out.pop("original_title", None)
    runtime = _runtime_evidence(payload.get("runtime"))
    if runtime is not None:
        out["runtime"] = runtime
    for field, label in {
        "poster_url": "海报", "cover_url": "封面", "trailer_url": "预告片",
    }.items():
        evidence = _url_evidence(payload.get(field), label)
        if evidence is not None:
            out[field] = evidence
    screenshots = _url_list_evidence(payload.get("screenshot_urls"), "张截图")
    if screenshots is not None:
        out["screenshot_urls"] = screenshots
    return out


def extract_peach_fields(payload: dict, genre_decisions=None) -> dict[str, dict]:
    """Map raw provider data to reviewable Peach truth-field candidates.

    `genre_decisions` 是用户在复核页收录过的来源 genre（见 `genre_taxonomy.map_genres`）。
    """
    out: dict[str, dict] = {}
    catalog = extract_catalog_evidence(payload)
    for field in ("title", "original_title"):
        if field in catalog:
            out[field] = dict(catalog[field])
    performers, warnings = normalized_performers(payload.get("actresses"))
    if performers:
        out["performers"] = {
            "value": performers,
            "display_value": "、".join(item["name"] for item in performers),
            "warnings": warnings,
        }
    japanese = japanese_view(payload)
    for field in ("studio", "series"):
        key = "maker" if field == "studio" else field
        raw_name = str(japanese.get(key) or "").strip() or payload.get(key)
        name, repeated = collapse_repeated_phrase(str(raw_name or ""))
        if name:
            out[field] = {
                "value": name,
                "display_value": name,
                "warnings": ([f"来源值含重复片段，已规范化：{raw_name} → {name}"]
                             if repeated else []),
            }
    release_date, date_warnings = normalized_release_date(payload.get("release_date"))
    if release_date:
        out["release_date"] = {
            "value": release_date,
            "display_value": release_date,
            "warnings": date_warnings,
        }
    # 未收录的 genre 跟着候选一起进复核队列。丢掉它们等于把「这个来源给了值但
    # Peach 还没决定怎么归类」伪装成「来源没给标签」，正是官方 tag 长期缺口的成因。
    # 原文另存一份结构化的：复核页要拿它做「收录成哪个中文标签」的按钮，从那句中文
    # 提示里再拆回词来是把显示当接口用。
    mapped, unmapped = map_genres(payload.get("genres") or [], genre_decisions)
    if mapped:
        out["tags"] = {
            "value": mapped,
            "display_value": "、".join(mapped),
            "unmapped_genres": unmapped,
            "warnings": [unmapped_genre_warning(unmapped)] if unmapped else [],
        }
    return out
