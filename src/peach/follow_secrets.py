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
    """按 provider 读取凭据文件；缺失是正常状态，不是错误。

    凭据默认只在本机。`shared_root` 给出时，**只有被声明为可同步的字段**会额外写一份到
    共享副本，并在本机缺失时从那里回填。哪些字段可同步由 `syncable_fields` 显式给出——
    绝不按字段名猜：今天 `api_key` 能同步、`cookie` 不能，明天新增一个 `session_token`
    就会落到错误的一侧。声明式意味着新增来源时作者必须表态。
    """

    def __init__(self, secrets_root: Path, shared_root: Path | None = None,
                 syncable_fields: dict[str, tuple[str, ...]] | None = None):
        self.root = Path(secrets_root) / "follow"
        self.shared_root = (Path(shared_root) / "secrets" / "follow"
                            if shared_root is not None else None)
        self.syncable_fields = syncable_fields or {}

    def path_for(self, provider: str) -> Path:
        if not provider or "/" in provider or "\\" in provider or provider.startswith("."):
            raise CredentialError("provider 名称非法")
        return self.root / f"{provider}.json"

    def syncable(self, provider: str) -> tuple[str, ...]:
        return tuple(self.syncable_fields.get(provider, ()))

    def shared_path_for(self, provider: str) -> Path | None:
        if self.shared_root is None:
            return None
        self.path_for(provider)          # 复用同一套名称校验
        return self.shared_root / f"{provider}.json"

    def _read(self, path: Path, provider: str) -> dict[str, str]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CredentialError(f"{provider} 凭据文件无法解析") from exc
        if not isinstance(payload, dict):
            raise CredentialError(f"{provider} 凭据文件必须是 JSON 对象")
        return {
            str(key): str(value) for key, value in payload.items()
            if value is not None and not isinstance(value, (dict, list))
        }

    def _shared_values(self, provider: str) -> dict[str, str]:
        """共享副本里的可同步字段。盘不在或读不动都当作没有，不让它挡住本机凭据。"""
        path = self.shared_path_for(provider)
        if path is None or not path.is_file():
            return {}
        allowed = set(self.syncable(provider))
        try:
            return {k: v for k, v in self._read(path, provider).items() if k in allowed}
        except (CredentialError, OSError):
            return {}

    def load(self, provider: str) -> Credential | None:
        path = self.path_for(provider)
        shared = self._shared_values(provider)
        if not path.is_file():
            return Credential(provider, dict(shared)) if shared else None
        # 本机优先：共享副本只补本机没有的可同步字段，不覆盖本机已填的值。
        values = {**shared, **self._read(path, provider)}
        return Credential(provider, values)

    def describe(self, provider: str) -> dict[str, object]:
        """只报告存在性与权限，绝不返回凭据值。

        `world_readable` 只在 POSIX 上有意义：NTFS 的访问控制走 ACL，`st_mode` 里的
        组/其他读位是 Python 合成出来的常量，恒为真——拿它当判据会在 Windows 上
        对每个凭据文件都报「权限过宽」。那里报 `None`（未知），不假装知道。
        """
        path = self.path_for(provider)
        if not path.is_file():
            return {"provider": provider, "present": False, "fields": [],
                    "world_readable": False}
        credential = self.load(provider)
        return {
            "provider": provider,
            "present": True,
            "fields": sorted(credential.values) if credential else [],
            "world_readable": self._world_readable(path),
        }

    @staticmethod
    def _world_readable(path: Path) -> bool | None:
        if os.name == "nt":
            return None
        mode = stat.S_IMODE(os.stat(path).st_mode)
        return bool(mode & (stat.S_IRGRP | stat.S_IROTH))
