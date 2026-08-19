import unittest
from unittest.mock import MagicMock, patch

from peach.mdns import MdnsPublisher, answers_on_network, create_mdns_publisher, lan_ipv4


class MdnsPublisherTests(unittest.TestCase):
    def test_registers_and_unregisters_peach_local_on_all_interfaces(self):
        with patch("peach.mdns.Zeroconf") as zeroconf_type, \
                patch("peach.mdns.answers_on_network", return_value=True):
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

    def test_address_change_republishes_so_dhcp_moves_are_followed(self):
        """换 Wi-Fi、DHCP 换地址都只改地址、不通知进程。

        不复查的话 `peach.local` 会一直指向旧地址；zeroconf 的套接字也绑在旧接口上，
        所以是整体重建而不是只换地址字段。
        """
        addresses = iter(["192.0.2.10", "192.0.2.10", "198.51.100.7"])
        current = ["192.0.2.10"]

        def resolver():
            current[0] = next(addresses, current[0])
            return current[0]

        with patch("peach.mdns.Zeroconf") as zeroconf_type, \
                patch("peach.mdns.answers_on_network", return_value=True):
            publisher = MdnsPublisher(
                "peach", 80, address_resolver=resolver, refresh_seconds=0,
            )
            publisher.start()
            self.assertEqual(publisher.address, "192.0.2.10")
            self.assertEqual(publisher.refresh(), "unchanged")
            self.assertEqual(publisher.refresh(), "republished")
            self.assertEqual(publisher.address, "198.51.100.7")
            publisher.stop()
        self.assertEqual(zeroconf_type.call_count, 2)

    def test_losing_the_network_withdraws_the_record_instead_of_keeping_a_stale_one(self):
        """留着一条指向旧地址的记录比没有记录更糟：客户端会一直连一个不存在的地方。"""
        states = iter(["192.0.2.10"])

        def resolver():
            try:
                return next(states)
            except StopIteration:
                raise RuntimeError("no publishable LAN IPv4 address") from None

        with patch("peach.mdns.Zeroconf"), \
                patch("peach.mdns.answers_on_network", return_value=True):
            publisher = MdnsPublisher(
                "peach", 80, address_resolver=resolver, refresh_seconds=0,
            )
            publisher.start()
            self.assertEqual(publisher.status, "peach.local")
            self.assertEqual(publisher.refresh(), "unavailable")
            self.assertEqual(publisher.status, "unavailable")
            self.assertIsNone(publisher.address)

    def test_a_pinned_address_never_republishes(self):
        """生产上显式钉住地址时复查必须是空转，不能自己换成别的网卡。"""
        with patch("peach.mdns.Zeroconf") as zeroconf_type, \
                patch("peach.mdns.answers_on_network", return_value=True):
            publisher = create_mdns_publisher(
                "peach", 80, address="192.0.2.10", refresh_seconds=0,
            )
            publisher.start()
            self.assertEqual(publisher.refresh(), "unchanged")
            self.assertEqual(publisher.refresh(), "unchanged")
            publisher.stop()
        self.assertEqual(zeroconf_type.call_count, 1)

    def test_secure_publication_uses_https_service(self):
        with patch("peach.mdns.Zeroconf") as zeroconf_type, \
                patch("peach.mdns.answers_on_network", return_value=True):
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
        with patch("peach.mdns.Zeroconf") as zeroconf_type, \
                patch("peach.mdns.answers_on_network", return_value=True):
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


class ReachabilityTests(unittest.TestCase):
    """注册成功不等于对外可见。

    macOS 的「本地网络」隐私门会静默掐掉多播：从终端起的进程继承终端已授权的身份，
    launchd 起的作业是另一个主体、没有弹窗可点，于是 zeroconf 自认为注册成功、实际
    一个包都发不出去。`/healthz` 报着 `peach.local`，手机却怎么都解析不到——这种
    「自称成功」比直接失败难查得多，所以要自己发一次查询验一验。
    """

    def test_status_says_unreachable_when_nothing_answers(self):
        with patch("peach.mdns.Zeroconf"), \
                patch("peach.mdns.answers_on_network", return_value=False):
            publisher = MdnsPublisher(
                "peach", 80, address_resolver=lambda: "192.0.2.10", refresh_seconds=0)
            publisher.start()
            self.assertEqual(publisher.status, "unreachable")
            publisher.stop()

    def test_status_is_the_hostname_when_the_record_answers(self):
        with patch("peach.mdns.Zeroconf"), \
                patch("peach.mdns.answers_on_network", return_value=True):
            publisher = MdnsPublisher(
                "peach", 80, address_resolver=lambda: "192.0.2.10", refresh_seconds=0)
            publisher.start()
            self.assertEqual(publisher.status, "peach.local")
            publisher.stop()

    def test_probe_never_raises_on_a_dead_socket(self):
        with patch("peach.mdns.socket.socket", side_effect=OSError("no multicast")):
            self.assertFalse(answers_on_network("peach.local", timeout=0.1))


if __name__ == "__main__":
    unittest.main()
