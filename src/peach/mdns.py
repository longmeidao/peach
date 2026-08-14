from __future__ import annotations

import socket
import ipaddress
from collections.abc import Callable

from zeroconf import ServiceInfo, Zeroconf


HTTP_SERVICE_TYPE = "_http._tcp.local."
HTTPS_SERVICE_TYPE = "_https._tcp.local."


def _normalized_name(name: str) -> str:
    normalized = name.strip().lower().removesuffix(".local")
    if not normalized or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in normalized):
        raise ValueError("mDNS name must contain only letters, digits, and hyphens")
    return normalized


def lan_ipv4() -> str:
    """Ask the routing table for the preferred LAN IPv4 without sending data."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        routed = str(sock.getsockname()[0])
    finally:
        sock.close()
    benchmark = ipaddress.ip_network("198.18.0.0/15")
    if ipaddress.ip_address(routed) not in benchmark:
        return routed
    # Full-tunnel proxies may own the default route. Fall back to host interfaces,
    # rejecting the benchmarking range used by Mihomo and obvious host-only endpoints.
    candidates = []
    for value in socket.gethostbyname_ex(socket.gethostname())[2]:
        address = ipaddress.ip_address(value)
        if not isinstance(address, ipaddress.IPv4Address) or address in benchmark:
            continue
        if address.is_loopback or address.is_link_local or address.is_unspecified:
            continue
        prefix_score = 3 if value.startswith("192.168.") else (2 if value.startswith("10.") else 1)
        endpoint_score = 0 if int(value.rsplit(".", 1)[1]) in {1, 2} else 1
        candidates.append((prefix_score, endpoint_score, value))
    if not candidates:
        raise RuntimeError("no publishable LAN IPv4 address; pass --mdns-address")
    return max(candidates)[2]


def _explicit_resolver(address: str) -> Callable[[], str]:
    parsed = ipaddress.ip_address(address)
    if not isinstance(parsed, ipaddress.IPv4Address):
        raise ValueError("mDNS address must be IPv4")
    if parsed.is_loopback or parsed.is_multicast or parsed.is_unspecified:
        raise ValueError("mDNS address must be a publishable interface IPv4")
    return lambda: str(parsed)


class MdnsPublisher:
    """Publish Peach exactly like the verified pre-migration web server.

    ``Zeroconf()`` deliberately listens on all eligible interfaces. Restricting it to
    one IPv4 interface during the FastAPI migration made publication unreliable on
    this Windows host, while Windows ``DnsServiceRegister`` advertised discovery but
    could not create the branded ``peach.local`` host record.
    """

    backend = "zeroconf-all-interfaces"

    def __init__(
        self,
        name: str,
        port: int,
        secure: bool = False,
        address_resolver: Callable[[], str] = lan_ipv4,
    ) -> None:
        self.name = _normalized_name(name)
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
        zeroconf = Zeroconf()
        try:
            zeroconf.register_service(info, allow_name_change=True)
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


def create_mdns_publisher(
    name: str, port: int, secure: bool = False, address: str | None = None,
) -> MdnsPublisher:
    resolver = _explicit_resolver(address) if address else lan_ipv4
    return MdnsPublisher(name, port, secure=secure, address_resolver=resolver)
