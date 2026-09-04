"""在仅安装 wheel 的解释器中，从源码树外验证资源、迁移和 HTTP 关键入口。"""
import json
import os
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="peach-wheel-") as directory:
        root = Path(directory).resolve()
        os.environ["PEACH_DATA_ROOT"] = str(root / "data")
        from fastapi.testclient import TestClient
        import peach
        from peach.api import create_app
        from peach.config import MIGRATIONS_DIR, PeachSettings
        from peach.migrations import upgrade
        assert "site-packages" in Path(peach.__file__).parts, peach.__file__
        assert "_resources" in MIGRATIONS_DIR.parts, MIGRATIONS_DIR
        database = root / "ledger.db"
        assert upgrade(database, MIGRATIONS_DIR)
        settings = PeachSettings(db_path=database, configured=True, token="wheel-smoke")
        client = TestClient(create_app(settings))
        try:
            assert client.get("/healthz").status_code == 200
            ready = client.get("/healthz?ready=1")
            assert ready.status_code == 200, ready.text
            assert client.get("/api/items").status_code == 401
            headers = {"X-Token": "wheel-smoke"}
            assert client.get("/api/items", headers=headers).status_code == 200
            assert client.get("/", headers=headers).status_code == 200
            assert settings.page_path.is_file()
            assert (settings.page_path.parent / "app.js").is_file()
            assert (settings.page_path.parent / "dist" / "peach-ui.js").is_file()
            assert any(settings.vendor_path.iterdir())
            print(json.dumps({"module": peach.__file__, "ready": ready.json(),
                              "checks": ["migrations", "web", "vendor", "island", "auth", "items"]}))
        finally:
            client.close()


if __name__ == "__main__":
    main()
