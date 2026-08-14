import unittest
from unittest.mock import patch

from peach.mdns import (
    DNS_REQUEST_PENDING, MdnsPublisher, WindowsMdnsPublisher,
    create_mdns_publisher,
)


class MdnsPublisherTests(unittest.TestCase):
    def test_registers_and_unregisters_peach_local(self):
        with patch("peach.mdns.Zeroconf") as zeroconf_type:
            publisher = MdnsPublisher(
                "Peach.local", 80, address_resolver=lambda: "192.0.2.10"
            )
            publisher.start()
            info = zeroconf_type.return_value.register_service.call_args.args[0]
            self.assertEqual(info.server, "peach.local.")
            self.assertEqual(info.port, 80)
            self.assertEqual(publisher.status, "peach.local")
            publisher.stop()
        zeroconf_type.assert_called_once_with(interfaces=["192.0.2.10"])
        zeroconf_type.return_value.unregister_service.assert_called_once_with(info)
        zeroconf_type.return_value.close.assert_called_once()

    def test_secure_publication_uses_https_service(self):
        with patch("peach.mdns.Zeroconf") as zeroconf_type:
            publisher = MdnsPublisher(
                "peach", 443, secure=True, address_resolver=lambda: "192.0.2.10"
            )
            publisher.start()
            info = zeroconf_type.return_value.register_service.call_args.args[0]
            self.assertEqual(info.type, "_https._tcp.local.")
            self.assertEqual(info.port, 443)
            publisher.stop()

    def test_rejects_invalid_hostname(self):
        with self.assertRaises(ValueError):
            MdnsPublisher("bad name", 80)

    def test_windows_native_registration_lifecycle(self):
        class Function:
            def __init__(self, action=None, result=None):
                self.action = action
                self.result = result

            def __call__(self, *args):
                return self.action(*args) if self.action else self.result

        class DnsApi:
            def __init__(self):
                self.DnsServiceConstructInstance = Function(result=123)
                self.DnsServiceFreeInstance = Function()
                self.DnsServiceRegister = Function(self._complete)
                self.DnsServiceDeRegister = Function(self._complete)

            @staticmethod
            def _complete(request_pointer, _cancel):
                request_pointer._obj.pRegisterCompletionCallback(0, None, None)
                return DNS_REQUEST_PENDING

        dnsapi = DnsApi()
        publisher = WindowsMdnsPublisher(
            "peach", 80, address_resolver=lambda: "192.0.2.10",
            dnsapi_factory=lambda: dnsapi,
        )
        publisher.start()
        self.assertEqual(publisher.status, "peach.local")
        self.assertEqual(publisher.backend, "windows-dns-sd")
        publisher.stop()
        self.assertEqual(publisher.status, "stopped")

    @patch("peach.mdns.os.name", "nt")
    def test_factory_uses_windows_native_backend(self):
        self.assertIsInstance(create_mdns_publisher("peach", 80), WindowsMdnsPublisher)


if __name__ == "__main__":
    unittest.main()
