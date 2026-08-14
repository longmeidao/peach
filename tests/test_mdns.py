import unittest
from unittest.mock import MagicMock, patch

from peach.mdns import MdnsPublisher, create_mdns_publisher, lan_ipv4


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

    def test_explicit_address_avoids_tunnel_route(self):
        with patch("peach.mdns.Zeroconf") as zeroconf_type:
            publisher = create_mdns_publisher(
                "peach", 80, address="192.168.50.162",
            )
            publisher.start()
            self.assertEqual(publisher.address, "192.168.50.162")
            publisher.stop()
        zeroconf_type.assert_called_once_with()

    def test_tunnel_route_falls_back_to_real_host_interface(self):
        fake_socket = MagicMock()
        fake_socket.getsockname.return_value = ("198.18.0.1", 50000)
        with patch("peach.mdns.socket.socket", return_value=fake_socket), patch(
            "peach.mdns.socket.gethostname", return_value="host",
        ), patch(
            "peach.mdns.socket.gethostbyname_ex",
            return_value=("host", [], ["172.31.112.1", "192.168.56.1", "192.168.50.162"]),
        ):
            self.assertEqual(lan_ipv4(), "192.168.50.162")


if __name__ == "__main__":
    unittest.main()
