"""本机测试证据：代码内容、依赖环境和验证范围共同决定有效性。"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path

from filelock import FileLock, Timeout


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout.strip()


def evidence_dir(root: Path) -> Path:
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return common.parent / "build" / "agent-verification"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def manifest(root: Path) -> dict:
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    files = {}
    for name in sorted(set(names.split("\0")) - {""}):
        path = root / name
        if path.is_symlink():
            files[name] = "link:" + os.readlink(path)
        elif path.is_file():
            files[name] = [stat.S_IMODE(path.stat().st_mode), hashlib.sha256(path.read_bytes()).hexdigest()]
        elif not path.exists():
            files[name] = "deleted"
        else:
            raise ValueError(f"无法为文件生成验证快照：{name}")
    version = root / "src/peach/__init__.py"
    body = version.read_text(encoding="utf-8") if version.is_file() else ""
    body = re.sub(r'(?m)^__version__ = "\d+\.\d+\.\d+"$', '__version__ = "VERSION"', body)
    return {"files": files, "version_body": digest(body)}


def snapshot(root: Path) -> str:
    return digest(manifest(root))


def interpreter(root: Path) -> Path:
    suffix = Path("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    local = root / ".venv" / suffix
    if local.is_file():
        return local.absolute()
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    shared = common.parent / ".venv" / suffix
    return shared.absolute() if shared.is_file() else Path(sys.executable).absolute()


@lru_cache(maxsize=16)
def python_identity(executable: str, stamp: int) -> dict:
    return json.loads(subprocess.run(
        [executable, "-c", "import json,sys,site; print(json.dumps({'version':sys.version,'sites':site.getsitepackages()}))"],
        check=True, capture_output=True, text=True, encoding="utf-8").stdout)


#: 外部工具的版本探针。工具身份取它自报的版本，不取 PATH 解析到的路径和文件字节：
#: 同一套 Git 安装在 PowerShell 里解析到 `Git\cmd\git.exe`、在 Git Bash 里解析到
#: `Git\mingw64\bin\git.exe`，两个前端字节不同、版本相同、行为也相同。按路径记身份的
#: 后果是记录绑在 shell 上——在一个 shell 里跑出记录，在另一个 shell 里 `integrate`
#: 就报「缺少有效测试记录」，而回到工作树跑 `auto` 又说「复用记录」，两句查的是两个键。
#: 探针只用最短的那条：`openssl version -a` 会连 OPENSSLDIR 一起打出来，那又是路径。
TOOL_PROBES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("node", ("--version",)),
    ("npm", ("--version",)),
    ("git", ("--version",)),
    ("ffmpeg", ("-version",)),
    ("ffprobe", ("-version",)),
    ("openssl", ("version",)),
)


@lru_cache(maxsize=32)
def tool_identity(executable: str, stamp: int, probe: tuple[str, ...]) -> str:
    """工具自报的版本摘要。`stamp` 只用于让缓存跟着文件改动失效。

    非零退出码连着输出一起进摘要：探针不成立的工具彼此仍要能区分开，那本身就是环境差异。
    """
    try:
        done = subprocess.run([executable, *probe], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "unspawnable"
    return digest([done.returncode, done.stdout.strip(), done.stderr.strip()])


def environment(root: Path) -> str:
    tools = {}
    for name, probe in TOOL_PROBES:
        executable = shutil.which(name)
        if not executable and name == "openssl" and sys.platform == "win32":
            bundled = Path("C:/Program Files/Git/usr/bin/openssl.exe")
            executable = str(bundled) if bundled.is_file() else None
        if not executable:
            tools[name] = None
            continue
        try:
            stamp = Path(executable).stat().st_mtime_ns
        except OSError:
            stamp = 0
        tools[name] = tool_identity(executable, stamp, probe)
    # 同一个目录可在 sys.path 中出现多次；依赖身份取集合，版本变化仍改变指纹。
    python = interpreter(root)
    identity = python_identity(str(python), python.stat().st_mtime_ns)
    installed = sorted({(d.metadata.get("Name", ""), d.version)
                        for d in importlib.metadata.distributions(path=identity["sites"])
                        if d.metadata.get("Name", "").casefold() != "peach"})
    node_lock = root / "frontend/node_modules/.package-lock.json"
    return digest({
        "schema": 4, "python": identity["version"], "executable": str(python),
        "platform": platform.platform(), "packages": installed, "tools": tools,
        "node_modules": hashlib.sha256(node_lock.read_bytes()).hexdigest() if node_lock.exists() else None,
        "flags": {k: v for k, v in os.environ.items()
                  if k.startswith(("PEACH_", "CI", "GITHUB_", "PYTHON")) and k != "PYTHONPATH"},
    })


def key(root: Path) -> str:
    return digest([snapshot(root), environment(root)])


def inputs(root: Path) -> dict:
    content, dependencies = manifest(root), environment(root)
    return {"manifest": content, "environment": dependencies,
            "state": digest([digest(content), dependencies])}


def baselines(root: Path, current: dict):
    folder = evidence_dir(root)
    paths = sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:32]
    for path in paths:
        record = read(root, path.stem)
        if "full" not in record.get("passed", ()) or record.get("environment") != current["environment"]:
            continue
        old = record.get("manifest", {})
        new = current["manifest"]
        if not isinstance(old.get("files"), dict):
            continue
        changed = sorted(name for name in old["files"].keys() | new["files"].keys()
                         if old["files"].get(name) != new["files"].get(name))
        version = "src/peach/__init__.py"
        version_only = version in changed and version in old["files"] and version in new["files"] \
            and old.get("version_body") == new.get("version_body") \
            and old["files"][version][0] == new["files"][version][0]
        if version_only:
            changed.remove(version)
        yield record, changed, version_only


def read(root: Path, state: str) -> dict:
    try:
        record = json.loads((evidence_dir(root) / f"{state}.json").read_text(encoding="utf-8"))
        if not isinstance(record, dict) or not isinstance(record.get("validated"), dict):
            return {}
        if record.get("state") == state:
            record["passed"] = [scope for scope, stamp in record["validated"].items()
                                if isinstance(stamp, (float, int)) and 0 <= time.time() - stamp < 86400]
            return record
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return {}


def covers(record: dict, scopes: tuple[str, ...]) -> bool:
    passed = set(record.get("passed", ()))
    return "full" in passed or set(scopes).issubset(passed)


def write(root: Path, state: str, scopes: tuple[str, ...], *, success: bool,
          elapsed: float, slowest: list, count: int, previous: dict | None = None,
          context: dict | None = None, baseline: dict | None = None) -> None:
    folder = evidence_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    prior = previous if previous is not None else read(root, state)
    validated = dict(prior.get("validated", {})) if success else {}
    if success:
        validated.update({scope: time.time() for scope in scopes})
        if baseline:
            validated["full"] = baseline["validated"]["full"]
    record = {**(context or inputs(root)), "state": state, "validated": validated, "finished": time.time(),
              "baseline": baseline.get("state") if baseline else None,
              "elapsed": elapsed, "count": count, "slowest": slowest}
    temporary = folder / f"{state}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(folder / f"{state}.json")


def run_lock(root: Path, state: str) -> FileLock:
    folder = evidence_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    return FileLock(folder / f"{state}.lock", timeout=0)
