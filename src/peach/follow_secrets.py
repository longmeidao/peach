"""追更来源的本机凭据读取。

凭据只从 `peach-data/secrets/follow/<provider>.json` 读，永不进 Git、URL、日志或 ledger。
本模块不打印凭据值，`describe()` 只报告字段是否存在。
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path


class CredentialError(RuntimeError):
    pass


@dataclass(frozen=True)
class Credential:
    provider: str
    values: dict[str, str]

    def require(self, *names: str) -> tuple[str, ...]:
        missing = [name for name in names if not self.values.get(name)]
        if missing:
            raise CredentialError(
                f"{self.provider} 凭据缺少字段：{', '.join(missing)}"
            )
        return tuple(str(self.values[name]) for name in names)


class CredentialStore:
    """按 provider 读取本机凭据文件；缺失是正常状态，不是错误。"""

    def __init__(self, secrets_root: Path):
        self.root = Path(secrets_root) / "follow"

    def path_for(self, provider: str) -> Path:
        if not provider or "/" in provider or "\\" in provider or provider.startswith("."):
            raise CredentialError("provider 名称非法")
        return self.root / f"{provider}.json"

    def load(self, provider: str) -> Credential | None:
        path = self.path_for(provider)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CredentialError(f"{provider} 凭据文件无法解析") from exc
        if not isinstance(payload, dict):
            raise CredentialError(f"{provider} 凭据文件必须是 JSON 对象")
        values = {
            str(key): str(value)
            for key, value in payload.items()
            if value is not None and not isinstance(value, (dict, list))
        }
        return Credential(provider, values)

    def describe(self, provider: str) -> dict[str, object]:
        """只报告存在性与权限，绝不返回凭据值。"""
        path = self.path_for(provider)
        if not path.is_file():
            return {"provider": provider, "present": False, "fields": [],
                    "world_readable": False}
        credential = self.load(provider)
        mode = stat.S_IMODE(os.stat(path).st_mode)
        return {
            "provider": provider,
            "present": True,
            "fields": sorted(credential.values) if credential else [],
            "world_readable": bool(mode & (stat.S_IRGRP | stat.S_IROTH)),
        }
