"""amane 刮削站点的 Peach 侧接入：起桥子进程、读一行 JSON、把结果翻成 Peach 候选（ADR-0043）。

桥本体在 `tools/amane-bridge/bridge.py`，运行环境由同目录的 `pyproject.toml` / `uv.lock`
钉死，venv 建在数据目录 `<tools>/amane-bridge/.venv`，不进 Peach 主 venv。这里只做三件事：
找到 venv 里的解释器并起子进程；把 amane 的 `MediaMetadata` 映成 `extract_peach_fields`
认得的 payload；把 amane 的 `FailureReason` 映到 `MetadataProviderError` 现有的
`auth` / `unavailable` / `not_found` 三档，细档留在 `detail` 里给冷却用。

聚合不在这里：一站一份 payload 交给 `metadata_policy` / ADR-0038 的结算，不复制 amane 的
`aggregate`。升级也不在这里：钉的 sha 只在 `pyproject.toml` 一处，本模块读它，不另存一份。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .metadata import MetadataProviderError, auth_error, identifies_code, validate_provider_code
from .user_agent import USER_AGENT

AMANE_REPOSITORY = "https://github.com/sqzw-x/amane"
AMANE_LICENSE = "GPL-3.0"
#: 桥的源码目录：清单、锁与脚本都在仓库里，随 Peach 分发的只有这三个文件，不含 amane 源码。
BRIDGE_ROOT = Path(__file__).resolve().parents[2] / "tools" / "amane-bridge"
BRIDGE_SCRIPT = BRIDGE_ROOT / "bridge.py"
#: 桥的 venv 建在数据目录的工具区，和 FFmpeg 同一层；名字与源码目录一致。
BRIDGE_TOOL_NAME = "amane-bridge"
#: 一次子进程的默认超时。桥内每站并发、单请求 30 秒、最多两次重试，60 秒够一站走完。
DEFAULT_TIMEOUT = 60

#: 经桥开放给 Peach 来源链的站，只列 Peach 自己没有解析器的：站名 → 界面上的名字。
#: javdb / dmm / javbus 这些 Peach 已有的不经桥换——两条路径答同一站，分歧没人会去看。
SITES: dict[str, str] = {
    "fc2club": "FC2Club",
    "freejavbt": "FreeJavBT",
    "airav": "AIRAV",
    "avsox": "AVSOX",
}

#: amane 的 `FailureReason` → Peach 的 `MetadataProviderError.kind`。
#: `auth` 一档收「站方把我们挡在门外」的几种：年龄闸要 Cookie，Cloudflare 与出口 IP 封禁要等
#: 或换出口，地区限制要换出口——同一份请求再发一次结果不变，正是 `auth` 的语义
#: （`retryable=False`、`temporary=True`）。`parse_error` 是站点改版，重试无用但也不是这部片没有。
REASON_KINDS: dict[str, str] = {
    "not_found": "not_found",
    "no_usable_metadata": "not_found",
    "rate_limited": "unavailable",
    "server_error": "unavailable",
    "timeout": "unavailable",
    "network": "unavailable",
    "http_error": "unavailable",
    "empty_response": "unavailable",
    "unexpected": "unavailable",
    "crawler_unavailable": "unavailable",
    "parse_error": "unavailable",
    "cloudflare_challenge": "auth",
    "cloudflare_blocked": "auth",
    "ip_banned": "auth",
    "geo_restricted": "auth",
    "age_verification": "auth",
}
#: 这几档说明的是「这个出口对这一站发得太多或已被封」，整站要进冷却，不只是这一部片。
#: 用的是 `scraping_access` 已有的两档：限流按 429 那一档停，封禁按 403 那一档翻倍。
RATE_LIMITED_REASONS = frozenset({"rate_limited"})
BLOCKED_REASONS = frozenset({"cloudflare_challenge", "cloudflare_blocked", "ip_banned"})
#: 这几档重试没有意义：不是这部片没有，也不是等一会儿就好。
PERMANENT_REASONS = frozenset({"parse_error"})

Runner = Callable[..., subprocess.CompletedProcess[str]]


def pinned_revision(root: Path = BRIDGE_ROOT) -> str:
    """清单里钉的 amane sha。只认 40 位十六进制，短 sha 或分支名一律不算钉死。"""
    manifest = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    for requirement in manifest["project"]["dependencies"]:
        matched = re.fullmatch(r"amane\s*@\s*git\+\S+@([0-9a-f]{40})", requirement.strip())
        if matched:
            return matched.group(1)
    raise ValueError("amane 桥的清单没有钉住 amane 的 revision")


def locked_version(root: Path = BRIDGE_ROOT) -> str:
    """锁文件里 amane 那一条的版本号，只用于显示；锁不在就空串。"""
    try:
        lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    for package in lock.get("package", []):
        if package.get("name") == "amane":
            return str(package.get("version") or "")
    return ""


def bridge_home(tools_root: Path) -> Path:
    return Path(tools_root) / BRIDGE_TOOL_NAME


def bridge_python(tools_root: Path) -> Path:
    home = bridge_home(tools_root) / ".venv"
    return home / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def find_uv() -> Path | None:
    """建 venv 用的 uv。托盘进程的 PATH 未必带 WinGet 的 Links 目录，所以多看一眼那里。"""
    explicit = os.environ.get("PEACH_UV", "").strip()
    candidates = [Path(explicit)] if explicit else []
    on_path = shutil.which("uv")
    if on_path:
        candidates.append(Path(on_path))
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        candidates.append(Path(local) / "Microsoft" / "WinGet" / "Links" / "uv.exe")
    return next((path for path in candidates if path.is_file()), None)


def rebuild_command(tools_root: Path, *, uv: Path, root: Path = BRIDGE_ROOT) -> tuple[list[str], dict]:
    """按锁重建桥 venv 的命令与环境。`--locked` 让锁和清单不一致时直接失败，不悄悄改锁。"""
    command = [str(uv), "sync", "--locked", "--no-dev", "--python", "3.14",
               "--project", str(root)]
    env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(bridge_home(tools_root) / ".venv")}
    return command, env


def rebuild(tools_root: Path, *, runner: Runner = subprocess.run, timeout: int = 900,
            root: Path = BRIDGE_ROOT) -> dict:
    """重建桥 venv，返回给设置页的回执。首次要下载约 98 MB，之后只校验。"""
    uv = find_uv()
    if uv is None:
        return {"ok": False, "error": "未找到 uv，请先安装 uv 再重建 amane 桥"}
    command, env = rebuild_command(tools_root, uv=uv, root=root)
    bridge_home(tools_root).mkdir(parents=True, exist_ok=True)
    try:
        completed = runner(command, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, check=False, shell=False, env=env)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"重建 amane 桥超过 {timeout} 秒未完成"}
    except OSError as exc:
        return {"ok": False, "error": f"无法启动 uv：{exc}"}
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "").strip()[-800:]
        return {"ok": False, "error": f"uv sync 失败（exit {completed.returncode}）：{detail}"}
    return {"ok": True, "result": f"amane 桥已按 {pinned_revision(root)[:12]} 重建",
            **describe(tools_root, root=root)}


def describe(tools_root: Path, *, root: Path = BRIDGE_ROOT) -> dict:
    """设置页那张卡要的事实：钉的 sha、锁里的版本、venv 建没建、桥开了哪几站。"""
    python = bridge_python(tools_root)
    return {
        "repository": AMANE_REPOSITORY,
        "license": AMANE_LICENSE,
        "revision": pinned_revision(root),
        "version": locked_version(root),
        "installed": python.is_file(),
        "python": str(python),
        "sites": [{"source": name, "label": label} for name, label in SITES.items()],
    }


def latest_upstream_tag(client_options: Mapping[str, object], *, timeout: float = 10.0) -> str:
    """上游最新 release 的 tag，只读 GitHub API；取不到一律回「未取得」，不猜。"""
    import httpx
    try:
        with httpx.Client(**client_options, timeout=timeout,
                          headers={"Accept": "application/vnd.github+json",
                                   "User-Agent": USER_AGENT}) as client:
            response = client.get(f"https://api.github.com/repos/{AMANE_REPOSITORY.rsplit('/', 2)[-2]}/"
                                  f"{AMANE_REPOSITORY.rsplit('/', 1)[-1]}/releases/latest")
            if response.status_code != 200:
                return "未取得"
            tag = response.json().get("tag_name")
            return str(tag) if tag else "未取得"
    except Exception:  # noqa: BLE001 - 网络、代理、限额都是同一个答案
        return "未取得"


def proxy_argument(proxy_options: Mapping[str, object]) -> tuple[list[str], dict]:
    """把 `peach_proxy.client_options` 翻成桥的 `--proxy` 与子进程环境。

    三种模式：显式代理直接传；直连要把 `*_PROXY` 从环境里摘掉，否则 libcurl 自己会读；
    跟随环境就把环境里那一份显式传过去，行为与 POC 一致，不靠 libcurl 的隐式读取。
    """
    env = dict(os.environ)
    if proxy_options.get("proxy"):
        return ["--proxy", str(proxy_options["proxy"])], env
    if not proxy_options.get("trust_env", True):
        for name in list(env):
            if name.upper().endswith("_PROXY"):
                env.pop(name)
        return [], env
    inherited = next((env[name] for name in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy")
                      if env.get(name)), "")
    return (["--proxy", inherited] if inherited else []), env


@dataclass(frozen=True)
class AmaneBridge:
    """起一次桥子进程：一次 `--output json`、stdout 一行 JSON；可注入 runner，单测不起真进程。"""

    python: Path
    script: Path = BRIDGE_SCRIPT
    timeout: int = DEFAULT_TIMEOUT
    runner: Runner = subprocess.run

    @classmethod
    def create(cls, tools_root: Path, *, timeout: int = DEFAULT_TIMEOUT,
               runner: Runner = subprocess.run) -> "AmaneBridge":
        python = bridge_python(tools_root)
        if not python.is_file():
            raise MetadataProviderError(
                f"amane 桥未安装：在「来源和凭证」页重建，或放到 {python}")
        if not BRIDGE_SCRIPT.is_file():
            raise MetadataProviderError(f"amane 桥脚本缺失：{BRIDGE_SCRIPT}")
        return cls(python, BRIDGE_SCRIPT, timeout, runner)

    def query(self, code: str, sites: Sequence[str], *, language: str = "jp",
              proxy_options: Mapping[str, object] | None = None,
              timeout: float | None = None) -> dict:
        """问几站，返回桥的整份报告（`sites` 键下每站一条记录）。"""
        number = validate_provider_code(code)
        names = [str(site).strip() for site in sites]
        unknown = [site for site in names if site not in SITES]
        if not names or unknown:
            raise ValueError("未开放的 amane 站点：" + "、".join(unknown or ["（空）"]))
        proxy_args, env = proxy_argument(proxy_options or {"trust_env": True})
        env["PYTHONIOENCODING"] = "utf-8"
        command = [str(self.python), "-X", "utf8", str(self.script), "--number", number,
                   "--sites", ",".join(names), "--language", language, "--output", "json",
                   *proxy_args]
        try:
            completed = self.runner(
                command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout or self.timeout, check=False, shell=False, env=env)
        except subprocess.TimeoutExpired as exc:
            raise MetadataProviderError("amane 桥查询超时", kind="unavailable",
                                        retryable=True, temporary=True) from exc
        except OSError as exc:
            raise MetadataProviderError(f"无法启动 amane 桥：{exc}") from exc
        line = next((row for row in reversed(completed.stdout.splitlines()) if row.strip()), "")
        try:
            report = json.loads(line)
        except (TypeError, json.JSONDecodeError) as exc:
            detail = (completed.stderr or completed.stdout or "empty output").strip()[-800:]
            raise MetadataProviderError(f"amane 桥返回了非 JSON 输出：{detail}") from exc
        if not isinstance(report, dict) or "sites" not in report:
            message = report.get("error") if isinstance(report, dict) else ""
            raise MetadataProviderError(str(message or f"amane 桥查询失败（exit {completed.returncode}）"))
        return report


def failure_error(site: str, record: Mapping[str, object]) -> MetadataProviderError:
    """桥记录里一站的失败 → Peach 的错误对象。细档留在 `detail`，措辞里也带着。"""
    reason = str(record.get("reason") or "unexpected")
    status = int(record.get("http_status") or 0)
    label = SITES.get(site, site)
    kind = REASON_KINDS.get(reason, "unavailable")
    if kind == "auth":
        return auth_error(label, {
            "age_verification": "站方要求年龄验证",
            "geo_restricted": "站方按地区拒绝了这个出口",
            "cloudflare_challenge": "撞上 Cloudflare 挑战页",
            "cloudflare_blocked": "被 Cloudflare 拦下",
            "ip_banned": "出口 IP 已被站方封禁",
        }[reason] + f"（{reason}）", status_code=status, detail=reason)
    if kind == "not_found":
        return MetadataProviderError(f"{label} 上没有这个番号（{reason}）", kind="not_found",
                                     status_code=status, detail=reason)
    text = str(record.get("detail") or "").strip()
    message = f"{label} 未取得资料（{reason}" + (f"，HTTP {status}" if status else "") + "）"
    return MetadataProviderError(
        message + (f"：{text[:160]}" if text and reason in {"unexpected", "parse_error"} else ""),
        kind="unavailable", status_code=status, detail=reason,
        retryable=reason not in PERMANENT_REASONS, temporary=reason not in PERMANENT_REASONS)


def _first(values: object) -> str:
    if isinstance(values, list):
        return str(next((value for value in values if value), "") or "")
    return str(values or "")


def to_payload(site: str, code: str, metadata: Mapping[str, object]) -> dict:
    """amane `MediaMetadata` → `extract_peach_fields` / `extract_catalog_evidence` 认得的形状。

    键名沿用来源快照的写法（`maker`、`label`、`actresses[].japanese_name`、`genres`），
    这样候选、复核与自动落库那一路一行不用改。amane 的 `publisher` 是レーベル，对应 `label`
    而不是 `studio`；`external_id` 实测填的是详情页地址，不当 `content_id`——那一栏放站上
    读回的番号写法，`identifies_code` 拿它核身份。男演员不进 `actresses`：账本那一栏是出演女优。
    `code` 只用于 `raw` 之外的调用方对账，payload 里的身份字段一律取站上读回的值。
    """
    actors = metadata.get("actors") if isinstance(metadata.get("actors"), list) else []
    actresses = []
    for actor in actors:
        if isinstance(actor, str):
            actor = {"name": actor}
        if not isinstance(actor, dict) or str(actor.get("gender") or "") == "male":
            continue
        name = str(actor.get("name") or "").strip()
        if name:
            actresses.append({"japanese_name": name})
    directors = metadata.get("directors") if isinstance(metadata.get("directors"), list) else []
    # `id` 与 `content_id` 都填站上读回的番号写法，不填问的那个：`identifies_code` 靠它们
    # 认身份，填成问的番号等于把这道闸拆掉，搜索首条命中的别的片会被当成这一部。
    returned = str(metadata.get("number") or "")
    payload = {
        "id": returned,
        "content_id": returned,
        "source": site,
        "source_url": str(metadata.get("source_url") or metadata.get("external_id") or ""),
        "title": str(metadata.get("title") or ""),
        "maker": str(metadata.get("studio") or ""),
        "label": str(metadata.get("publisher") or ""),
        "series": str(metadata.get("series") or ""),
        "release_date": str(metadata.get("release") or ""),
        "runtime": metadata.get("runtime"),
        "director": _first(directors),
        "cover_url": _first(metadata.get("thumb_urls")),
        "poster_url": _first(metadata.get("poster_urls")),
        "screenshot_urls": [str(url) for url in (metadata.get("extrafanart") or []) if url],
        "trailer_url": _first(metadata.get("trailer_urls")),
        "actresses": actresses,
        "genres": [str(tag) for tag in (metadata.get("tags") or []) if tag],
        "plot": str(metadata.get("plot") or ""),
        "raw": dict(metadata),
    }
    return payload


def split_report(code: str, report: Mapping[str, object]) -> tuple[list[tuple[str, dict]], dict[str, MetadataProviderError]]:
    """桥的报告拆成两份：取到的 `[(站, payload)]`，与每站的失败。

    取回的商品必须认得出这个番号（`identifies_code`），否则按 `not_found` 记：站内搜索首条
    命中常常是别的片，这道闸和 r18.dev 那一路是同一道。
    """
    found: list[tuple[str, dict]] = []
    failures: dict[str, MetadataProviderError] = {}
    sites = report.get("sites") if isinstance(report.get("sites"), dict) else {}
    for site, record in sites.items():
        if not isinstance(record, dict):
            continue
        if record.get("status") == "found" and isinstance(record.get("metadata"), dict):
            payload = to_payload(site, code, record["metadata"])
            if identifies_code(code, payload):
                found.append((site, payload))
                continue
            failures[site] = MetadataProviderError(
                f"{SITES.get(site, site)} 返回的商品不是 {code}：content_id={payload['content_id']!r}",
                kind="not_found", detail="not_found")
            continue
        failures[site] = failure_error(site, record)
    return found, failures


def cooldown_action(error: MetadataProviderError) -> str:
    """这次失败要不要把整站停下：`blocked` 按 403 那一档翻倍，`rate_limited` 按 429 那一档，空串不停。"""
    reason = str(getattr(error, "detail", "") or "")
    if reason in BLOCKED_REASONS:
        return "blocked"
    if reason in RATE_LIMITED_REASONS:
        return "rate_limited"
    return ""
