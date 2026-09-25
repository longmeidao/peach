import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from peach.jobs import process_alive
from peach.process_job import assign_to_job, close_job, create_kill_on_close_job

ROOT = Path(__file__).resolve().parents[1]

#: 一个最小的「托盘」：用真的 ServiceManager 拉起一个睡着的子服务，报出它的 PID 后原地等着被杀。
TRAY_STAND_IN = """
import sys, time
from pathlib import Path
from unittest import mock
from peach.tray import ServiceManager, ServiceSpec

spec = ServiceSpec("http", "http://127.0.0.1:9/healthz",
                   (sys.executable, "-c", "import time; time.sleep(120)"), True)
manager = ServiceManager((spec,), log_dir=Path(sys.argv[1]),
                         health_get=mock.Mock(side_effect=OSError("down")))
manager.start_missing()
print(manager._owned["http"].pid, flush=True)
time.sleep(120)
"""


def descendants(root: int) -> set[int]:
    from peach.windows_restart import _process_paths_and_parents
    _paths, parents = _process_paths_and_parents()
    found, frontier = set(), [root]
    while frontier:
        current = frontier.pop()
        for process_id, parent in parents.items():
            if parent == current and process_id not in found:
                found.add(process_id)
                frontier.append(process_id)
    return found


def wait_until(predicate, seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


@unittest.skipUnless(os.name == "nt", "Job Object 是 Windows 能力，其余平台三个函数都是空操作")
class KillOnCloseJobTests(unittest.TestCase):
    def sleeper(self) -> subprocess.Popen:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"],
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        return child

    def test_closing_the_job_ends_the_processes_in_it(self):
        child = self.sleeper()
        job = create_kill_on_close_job()
        self.assertIsNotNone(job)
        assign_to_job(job, child)
        close_job(job)
        self.assertIsNotNone(child.wait(timeout=10))

    def test_a_force_killed_tray_takes_its_services_along(self):
        """`Stop-Process -Force` 打托盘时收尾代码一行不跑，只有内核关 Job 句柄这一步还在。

        2026-09-25 就是这样留下两棵孤儿服务，继续占着 80/443 跑旧代码。
        """
        with tempfile.TemporaryDirectory() as directory:
            environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"),
                           "PEACH_DATA_ROOT": directory}
            tray = subprocess.Popen(
                [sys.executable, "-c", TRAY_STAND_IN, directory], stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding="utf-8", env=environment,
                creationflags=subprocess.CREATE_NO_WINDOW)
            self.addCleanup(lambda: tray.poll() is None and tray.kill())
            service = int(tray.stdout.readline())
            # venv 的 python.exe 是个转发器，真正的解释器是它再起的子进程。
            wait_until(lambda: descendants(service))
            tree = {service} | descendants(service)
            tray.kill()
            tray.wait(timeout=10)
            tray.stdout.close()
            self.assertTrue(wait_until(lambda: not any(process_alive(pid) for pid in tree)),
                            f"托盘被强杀后这些服务进程还活着：{sorted(tree)}")


if __name__ == "__main__":
    unittest.main()
