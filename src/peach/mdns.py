from __future__ import annotations

import ctypes
import os
import socket
import threading
from collections.abc import Callable
from ctypes import wintypes

from zeroconf import ServiceInfo, Zeroconf


HTTP_SERVICE_TYPE = "_http._tcp.local."
HTTPS_SERVICE_TYPE = "_https._tcp.local."
DNS_REQUEST_PENDING = 9506


def _normalized_name(name: str) -> str:
    normalized = name.strip().lower().removesuffix(".local")
    if not normalized or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in normalized):
        raise ValueError("mDNS name must contain only letters, digits, and hyphens")
    return normalized


def lan_ipv4() -> str:
    """Ask the local routing table for the preferred LAN IPv4 without sending data."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return str(sock.getsockname()[0])
    finally:
        sock.close()


class MdnsPublisher:
    backend = "zeroconf"

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


_REGISTER_COMPLETE = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
    None, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p,
)


class _DnsServiceRegisterRequest(ctypes.Structure):
    _fields_ = [
        ("Version", wintypes.ULONG),
        ("InterfaceIndex", wintypes.ULONG),
        ("pServiceInstance", ctypes.c_void_p),
        ("pRegisterCompletionCallback", _REGISTER_COMPLETE),
        ("pQueryContext", ctypes.c_void_p),
        ("hCredentials", wintypes.HANDLE),
        ("unicastEnabled", wintypes.BOOL),
    ]


def _load_dnsapi():
    dnsapi = ctypes.WinDLL("dnsapi", use_last_error=True)
    dnsapi.DnsServiceConstructInstance.argtypes = [
        wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(wintypes.ULONG),
        ctypes.c_void_p, wintypes.WORD, wintypes.WORD, wintypes.WORD,
        wintypes.DWORD, ctypes.POINTER(wintypes.LPCWSTR),
        ctypes.POINTER(wintypes.LPCWSTR),
    ]
    dnsapi.DnsServiceConstructInstance.restype = ctypes.c_void_p
    dnsapi.DnsServiceRegister.argtypes = [
        ctypes.POINTER(_DnsServiceRegisterRequest), ctypes.c_void_p,
    ]
    dnsapi.DnsServiceRegister.restype = wintypes.DWORD
    dnsapi.DnsServiceDeRegister.argtypes = [
        ctypes.POINTER(_DnsServiceRegisterRequest), ctypes.c_void_p,
    ]
    dnsapi.DnsServiceDeRegister.restype = wintypes.DWORD
    dnsapi.DnsServiceFreeInstance.argtypes = [ctypes.c_void_p]
    dnsapi.DnsServiceFreeInstance.restype = None
    return dnsapi


class WindowsMdnsPublisher:
    """Advertise through Windows DNS-SD instead of competing for UDP 5353."""

    backend = "windows-dns-sd"

    def __init__(
        self,
        name: str,
        port: int,
        secure: bool = False,
        address_resolver: Callable[[], str] = lan_ipv4,
        dnsapi_factory: Callable[[], object] = _load_dnsapi,
    ) -> None:
        self.name = _normalized_name(name)
        self.port = port
        self.secure = secure
        self._address_resolver = address_resolver
        self._dnsapi_factory = dnsapi_factory
        self._dnsapi = None
        self._instance: int | None = None
        self._request: _DnsServiceRegisterRequest | None = None
        self._callback = None
        self._event = threading.Event()
        self._callback_status: int | None = None
        self.address: str | None = None
        self.status = "pending"

    @property
    def hostname(self) -> str:
        return f"{self.name}.local"

    def start(self) -> None:
        if self._request is not None:
            return
        address = self._address_resolver()
        dnsapi = self._dnsapi_factory()
        service = "_https._tcp.local" if self.secure else "_http._tcp.local"
        instance_name = f"{self.name}.{service}"
        ip4 = wintypes.ULONG.from_buffer_copy(socket.inet_aton(address))
        keys = (wintypes.LPCWSTR * 2)("path", "scheme")
        values = (wintypes.LPCWSTR * 2)("/", "https" if self.secure else "http")
        instance = dnsapi.DnsServiceConstructInstance(
            instance_name, self.hostname, ctypes.byref(ip4), None, self.port,
            0, 0, 2, keys, values,
        )
        if not instance:
            raise OSError(ctypes.get_last_error(), "DnsServiceConstructInstance failed")

        self._event.clear()
        self._callback_status = None

        @_REGISTER_COMPLETE
        def completed(status, _context, callback_instance):
            self._callback_status = int(status)
            if callback_instance:
                dnsapi.DnsServiceFreeInstance(callback_instance)
            self._event.set()

        request = _DnsServiceRegisterRequest(
            1, 0, instance, completed, None, None, False,
        )
        result = int(dnsapi.DnsServiceRegister(ctypes.byref(request), None))
        if result != DNS_REQUEST_PENDING:
            dnsapi.DnsServiceFreeInstance(instance)
            raise OSError(result, "DnsServiceRegister failed")
        if not self._event.wait(5) or self._callback_status != 0:
            dnsapi.DnsServiceDeRegister(ctypes.byref(request), None)
            dnsapi.DnsServiceFreeInstance(instance)
            raise OSError(self._callback_status or result, "mDNS registration did not complete")
        self._dnsapi = dnsapi
        self._instance = instance
        self._request = request
        self._callback = completed
        self.address = address
        self.status = self.hostname

    def stop(self) -> None:
        if self._request is None or self._dnsapi is None:
            return
        self._event.clear()
        try:
            result = int(self._dnsapi.DnsServiceDeRegister(
                ctypes.byref(self._request), None,
            ))
            if result == DNS_REQUEST_PENDING:
                self._event.wait(5)
        finally:
            if self._instance:
                self._dnsapi.DnsServiceFreeInstance(self._instance)
            self._dnsapi = None
            self._instance = None
            self._request = None
            self._callback = None
            self.address = None
            self.status = "stopped"


def create_mdns_publisher(name: str, port: int, secure: bool = False):
    publisher_type = WindowsMdnsPublisher if os.name == "nt" else MdnsPublisher
    return publisher_type(name, port, secure=secure)
