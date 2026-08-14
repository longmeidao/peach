#!/usr/bin/env python3
"""实验性 FastAPI JSON 入口；不替换当前 rm-web.py 服务。"""
import argparse
from pathlib import Path

from peach.api import create_app
from peach.config import PeachSettings


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8900)
    parser.add_argument("--db", type=Path, default=Path(r"R:\Resources\Intake\ledger.db"))
    parser.add_argument("--token", default="")
    parser.add_argument("--docs", action="store_true")
    args = parser.parse_args(argv)

    import uvicorn
    app = create_app(PeachSettings(db_path=args.db, token=args.token, docs_enabled=args.docs))
    uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()
