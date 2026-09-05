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
            command = [str(executable), "serve", "--host", "127.0.0.1", "--port", str(port),
                       "--no-ledger-sync", "--no-mdns"]
            process = subprocess.Popen(command + ["--setup"], cwd=root, env=environment, stdout=log, stderr=log)
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
                base = f"http://127.0.0.1:{port}"
                deadline = time.monotonic() + 40
                while True:
                    try:
                        with opener.open(base + "/healthz", timeout=1) as response:
                            health = json.load(response)
                        break
                    except (OSError, urllib.error.URLError):
                        if process.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError((root / "runtime.log").read_text(errors="replace"))
                        time.sleep(.25)
                with opener.open(base + "/", timeout=5) as response:
                    assert 'action="/setup"' in response.read().decode("utf-8")
                form = {"media_dir": str(media), "media_location": "115", "port": str(port)}
                request = urllib.request.Request(base + "/setup",
                    data=urllib.parse.urlencode(form).encode(), headers={"Origin": base})
                with opener.open(request, timeout=60) as response:
                    assert "设置完成" in response.read().decode("utf-8")
                assert (data / "database" / "ledger.db").is_file()
                process.terminate()
                process.wait(timeout=15)
                process = subprocess.Popen(command, cwd=root, env=environment, stdout=log, stderr=log)
                deadline = time.monotonic() + 40
                while True:
                    try:
                        with opener.open(base + "/healthz", timeout=1) as response:
                            health = json.load(response)
                        break
                    except (OSError, urllib.error.URLError):
                        if process.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError((root / "runtime.log").read_text(errors="replace"))
                        time.sleep(.25)
                for path in ("/", "/app.css", "/app.js", "/dist/peach-ui.js", "/api/items"):
                    with opener.open(base + path, timeout=10) as response:
                        assert response.status == 200, path
                with opener.open(base + "/api/configuration", timeout=5) as response:
                    configuration = json.load(response)
                assert configuration['media_sources'][0]['location'] == '115'
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
                                  "checks": ["oobe", "migrations", "serve", "automatic-login", "pages", "island", "items", "clouddrive-configuration"]}))
            finally:
                process.terminate()
                process.wait(timeout=15)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
