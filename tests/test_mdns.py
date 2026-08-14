import unittest
from unittest.mock import patch

from peach.mdns import MdnsPublisher, create_mdns_publisher


class MdnsPublisherTests(unittest.TestCase):
    def test_registers_and_unregisters_peach_local_on_all_interfaces(self):
        with patch("peach.mdns.Zeroconf") as zeroconf_type:
            publisher = MdnsPublisher(
                "Peach.local", 80, address_resolver=lambda: "192.0.2.10"
            )
            publisher.start()
            info = zeroconf_type.return_value.register_service.call_args.args[0]
            self.assertEqual(info.server, "peach.local.")
            self.assertEqual(info.port, 80)
            self.assertEqual(publisher.status, "peach.local")
            self.assertEqual(publisher.backend, "zeroconf-all-interfaces")
            publisher.stop()
        zeroconf_type.assert_called_once_with()
        zeroconf_type.return_value.register_service.assert_called_once_with(
            info, allow_name_change=True,
        )
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

    def test_factory_uses_verified_zeroconf_backend(self):
        self.assertIsInstance(create_mdns_publisher("peach", 80), MdnsPublisher)


if __name__ == "__main__":
    unittest.main()
