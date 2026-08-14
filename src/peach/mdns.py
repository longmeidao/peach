from __future__ import annotations

import socket
from collections.abc import Callable

from zeroconf import ServiceInfo, Zeroconf


HTTP_SERVICE_TYPE = "_http._tcp.local."
HTTPS_SERVICE_TYPE = "_https._tcp.local."


def lan_ipv4() -> str:
    """Ask the local routing table for the preferred LAN IPv4 without sending data."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return str(sock.getsockname()[0])
    finally:
        sock.close()


class MdnsPublisher:
    def __init__(
        self,
        name: str,
        port: int,
        secure: bool = False,
        address_resolver: Callable[[], str] = lan_ipv4,
    ) -> None:
        normalized = name.strip().lower().removesuffix(".local")
        if not normalized or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in normalized):
            raise ValueError("mDNS name must contain only letters, digits, and hyphens")
        self.name = normalized
        self.port = port
        self.secure = secure
        self._address_resolver = address_resolver
        self._zeroconf: Zeroconf | None = None
        self._info: ServiceInfo | None = None
        self.address: str | None = None
        self.status = "pending"

    @property
    def hostname(self) -> str:
        return f"{self.name}.local"

    def start(self) -> None:
        if self._zeroconf is not None:
            return
        address = self._address_resolver()
        service_type = HTTPS_SERVICE_TYPE if self.secure else HTTP_SERVICE_TYPE
        info = ServiceInfo(
            service_type,
            f"{self.name}.{service_type}",
            addresses=[socket.inet_aton(address)],
            port=self.port,
            properties={"path": "/", "scheme": "https" if self.secure else "http"},
            server=f"{self.hostname}.",
        )
        zeroconf = Zeroconf(interfaces=[address])
        try:
            zeroconf.register_service(info, allow_name_change=False)
        except Exception:
            zeroconf.close()
            raise
        self._zeroconf = zeroconf
        self._info = info
        self.address = address
        self.status = self.hostname

    def stop(self) -> None:
        if self._zeroconf is None:
            return
        try:
            if self._info is not None:
                self._zeroconf.unregister_service(self._info)
        finally:
            self._zeroconf.close()
            self._zeroconf = None
            self._info = None
            self.address = None
            self.status = "stopped"
