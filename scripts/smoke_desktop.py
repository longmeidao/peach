"""仅用标准库在临时目录验证桌面制品，不读取真实馆藏。"""
from __future__ import annotations

import argparse
import json
import http.cookiejar
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import urllib.parse


def wait_health(opener, base: str, process: subprocess.Popen, log_path: Path) -> dict:
    deadline = time.monotonic() + 40
    while True:
        try:
            with opener.open(base + "/healthz", timeout=1) as response:
                return json.load(response)
        except (OSError, urllib.error.URLError):
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(log_path.read_text(errors="replace"))
            time.sleep(.25)


def lan_base(port: int) -> str:
    routed = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        routed.connect(("192.0.2.1", 80))
        return f"http://{routed.getsockname()[0]}:{port}"
    finally:
        routed.close()


def assert_requires_login(opener, base: str) -> None:
    """登录之后 `/api/items` 返回 200，只说明它能返回 200。

    密码这道门是不是真的关着，得在还没登录的时候敲一次。
    """
    try:
        with opener.open(base + "/api/items", timeout=10) as response:
            raise AssertionError(f"未登录拿到了 /api/items：{response.status}")
    except urllib.error.HTTPError as error:
        assert error.code == 401, f"未登录访问 /api/items 应为 401，实际 {error.code}"


def assert_standalone_tunnel(configuration: dict) -> None:
    tunnel = configuration['tunnel']
    assert tunnel['enabled'] is False
    assert tunnel['state'] == 'stopped'
    assert tunnel['available'] is True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="peach-desktop-") as directory:
        root = Path(directory).resolve()
        data = root / "data"
        media = root / "media"
        media.mkdir()
        environment = dict(os.environ, PEACH_DATA_ROOT=str(data), PYTHONIOENCODING="utf-8")
        environment.pop("PYTHONPATH", None)
        # 制品不得借助用户安装的 Python、Git、Node、FFmpeg 或 OpenSSL。
        environment["PATH"] = os.environ.get("SystemRoot", "/usr") + ("/System32" if os.name == "nt" else "/bin")
        with (root / "runtime.log").open("wb") as log:
            with socket.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                port = reservation.getsockname()[1]
            setup_command = [str(executable), "serve", "--host", "127.0.0.1", "--port", str(port),
                             "--no-ledger-sync", "--no-mdns", "--setup"]
            process = subprocess.Popen(setup_command, cwd=root, env=environment, stdout=log, stderr=log)
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
                base = f"http://127.0.0.1:{port}"
                health = wait_health(opener, base, process, root / "runtime.log")
                with opener.open(base + "/", timeout=5) as response:
                    assert 'action="/setup"' in response.read().decode("utf-8")
                password = "standalone-smoke-password"
                form = {"media_dir": str(media), "media_location": "115", "host": "2",
                        "port": str(port), "mdns_name": "peach", "access_enabled": "y",
                        "access_password": password, "access_confirm": password}
                request = urllib.request.Request(base + "/setup",
                    data=urllib.parse.urlencode(form).encode(), headers={"Origin": base})
                with opener.open(request, timeout=60) as response:
                    assert "设置完成" in response.read().decode("utf-8")
                assert (data / "database" / "ledger.db").is_file()
                process.terminate()
                process.wait(timeout=15)
                command = [str(executable), "serve", "--host", "0.0.0.0", "--port", str(port),
                           "--no-ledger-sync"]
                process = subprocess.Popen(command, cwd=root, env=environment, stdout=log, stderr=log)
                health = wait_health(opener, base, process, root / "runtime.log")
                # mDNS 这两行是服务自报：这个脚本只用标准库，发不出组播查询，也就
                # 验不到「局域网里真的解析得到 peach.local」。反查要 zeroconf，归
                # `tests/test_desktop_settings.py` 那一侧。
                assert health["mdns_backend"]
                assert health["mdns_service_host"] == "peach.local"
                with opener.open(lan_base(port) + "/healthz", timeout=5) as response:
                    assert json.load(response)["ok"]
                assert_requires_login(opener, base)
                login = urllib.request.Request(base + "/login",
                    data=urllib.parse.urlencode({"token": password, "days": "0"}).encode(),
                    headers={"Origin": base})
                with opener.open(login, timeout=10) as response:
                    assert response.status == 200
                for path in ("/", "/app.css", "/app.js", "/dist/peach-ui.js", "/api/items"):
                    with opener.open(base + path, timeout=10) as response:
                        assert response.status == 200, path
                with opener.open(base + "/api/configuration", timeout=5) as response:
                    configuration = json.load(response)
                assert configuration['media_sources'][0]['location'] == '115'
                assert_standalone_tunnel(configuration)
                second = root / 'pikpak'
                second.mkdir()
                sources = configuration['media_sources'] + [{'location': 'pikpak', 'path': str(second)}]
                request = urllib.request.Request(base + "/api/configuration",
                    data=json.dumps({'media_sources': sources, 'port': port,
                                     'revision': configuration['revision']}).encode(),
                    headers={"Origin": base, 'Content-Type': 'application/json'})
                with opener.open(request, timeout=10) as response:
                    assert json.load(response)['saved']
                with opener.open(base + '/api/configuration', timeout=5) as response:
                    saved = json.load(response)
                assert [row['location'] for row in saved['media_sources']] == ['115', 'pikpak']
                assert (data / "config.previous.toml").is_file()
                assert (data / "state" / "configuration-reload.request").is_file()
                print(json.dumps({"ok": True, "version": health.get("version"),
                                  "checks": ["oobe", "migrations", "lan-bind", "mdns", "password-login", "unauthenticated-api", "pages", "island", "items", "clouddrive-configuration", "cloudflared-sidecar"]}))
            finally:
                process.terminate()
                process.wait(timeout=15)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
