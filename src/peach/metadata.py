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

from .config import STATE_DIR, TOOLS_DIR
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
)


JAVINIZER_GO_VERSION = "1.5.1"
_SAFE_CODE = re.compile(r"^(?:FC2-PPV-\d{5,}|\d{3}[A-Z]{2,6}-\d{2,5}|[A-Z]{2,8}-\d{2,5}|\d{6}-\d{2,4})$")


class MetadataProviderError(RuntimeError):
    def __init__(
        self, message: str, *, kind: str = "unknown", status_code: int = 0,
        retryable: bool = False, temporary: bool = False,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retryable = retryable
        self.temporary = temporary


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
            raise MetadataProviderError(
                str(error.get("message") or "Javinizer-Go query failed"),
                kind=str(error.get("kind") or "unknown"),
                status_code=int(error.get("status_code") or 0),
                retryable=bool(error.get("retryable")),
                temporary=bool(error.get("temporary")),
            )
        if completed.returncode or not isinstance(payload, dict):
            raise MetadataProviderError(f"Javinizer-Go 查询失败（exit {completed.returncode}）")
        if str(payload.get("source") or "").strip() != scraper:
            raise MetadataProviderError("Javinizer-Go 返回来源与请求来源不一致")
        return payload


def collapse_repeated_phrase(value: str) -> tuple[str, bool]:
    """Compatibility wrapper around Peach's shared entity-name gate."""
    original = str(value or "").strip()
    cleaned = collapse_repeated_entity_name(original)
    return cleaned, cleaned != original


def safe_entity_name(value: str) -> str:
    return canonicalize_entity_name("performer", value)


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


def extract_peach_fields(payload: dict, category_map: dict[str, str]) -> dict[str, dict]:
    """Map raw provider data to the Peach truth fields supported by P0."""
    out: dict[str, dict] = {}
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
    mapped = [category_map[name] for name in payload.get("genres") or [] if name in category_map]
    mapped = list(dict.fromkeys(mapped))
    if mapped:
        out["tags"] = {"value": mapped, "display_value": "、".join(mapped), "warnings": []}
    return out
