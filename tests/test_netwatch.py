import sys
import threading
import time
import unittest

from peach.netwatch import NETWORK_CHANGE, NetworkChangeWatcher


class NetworkChangeWatcherTests(unittest.TestCase):
    def test_key_is_the_system_network_change_notification(self):
        self.assertEqual(NETWORK_CHANGE, b"com.apple.system.config.network_change")

    @unittest.skipUnless(sys.platform == "darwin", "Darwin 通知只在 macOS 上存在")
    def test_start_subscribes_and_stop_returns_promptly(self):
        """stop() 不能等到下一次网络事件才生效。

        select 只盯通知描述符的话，没有网络变化时线程会一直阻塞，退出要等到用户下次
        换网络——所以另开了一根管道专门用来叫醒它。
        """
        watcher = NetworkChangeWatcher(lambda: None)
        self.assertTrue(watcher.start())
        time.sleep(0.3)
        started = time.monotonic()
        watcher.stop()
        self.assertLess(time.monotonic() - started, 3.0)

    @unittest.skipUnless(sys.platform == "darwin", "Darwin 通知只在 macOS 上存在")
    def test_double_start_is_a_no_op(self):
        watcher = NetworkChangeWatcher(lambda: None)
        self.addCleanup(watcher.stop)
        self.assertTrue(watcher.start())
        self.assertFalse(watcher.start())

    @unittest.skipUnless(sys.platform == "darwin", "Darwin 通知只在 macOS 上存在")
    def test_a_failing_callback_does_not_kill_the_watcher(self):
        """回调挂掉不该带走整个托盘。"""
        calls = []

        def boom():
            calls.append(1)
            raise RuntimeError("boom")

        watcher = NetworkChangeWatcher(boom)
        self.addCleanup(watcher.stop)
        watcher.start()
        time.sleep(0.2)
        self.assertTrue(watcher._thread.is_alive())

    @unittest.skipIf(sys.platform == "darwin", "非 macOS 才走这条")
    def test_unsupported_platform_reports_itself(self):
        watcher = NetworkChangeWatcher(lambda: None)
        self.assertFalse(watcher.supported)
        self.assertFalse(watcher.start())


if __name__ == "__main__":
    unittest.main()
