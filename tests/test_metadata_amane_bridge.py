"""amane 桥脚本本身：一次子进程、一行 JSON、退出码分档。不装 amane，塞假的 Runtime 进去。"""
from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "amane-bridge" / "bridge.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("amane_bridge_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # dataclass 解析 `from __future__ import annotations` 下的字段类型要在 sys.modules 里找到它。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bridge = load_bridge()


class FakeSourceError(Exception):
    def __init__(self, reason, *, http_status=None, detail="", url=""):
        super().__init__(detail)
        self.reason, self.http_status, self.detail, self.url = reason, http_status, detail, url


class FakeMetadata:
    def __init__(self, **fields):
        self.fields = fields

    def model_dump(self, mode="json"):
        return dict(self.fields)


def make_runtime(outcomes):
    """`outcomes[站名]` 是要返回的资料、None（没有）或要抛的异常。"""
    class Crawler:
        site = ""

        def __init__(self, *, client, config):
            self.client, self.config = client, config

        async def fetch(self, query, options):
            outcome = outcomes[self.site]
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

    def crawler(site):
        return type(f"{site}Crawler", (Crawler,), {"site": site})

    return bridge.Runtime(
        crawler=crawler, make_client=lambda proxy, timeout, rate: {"proxy": proxy},
        query=lambda number: {"number": number}, options=lambda language: {"language": language},
        source_error=FakeSourceError, version="0.16.1")


def run_main(argv, runtime):
    out = io.StringIO()
    code = bridge.main(argv, runtime=runtime, out=out)
    lines = [line for line in out.getvalue().splitlines() if line.strip()]
    return code, lines


class BridgeContractTests(unittest.TestCase):
    def test_the_failure_reasons_are_the_upstream_sixteen(self):
        self.assertEqual(len(bridge.FAILURE_REASONS), 16)
        self.assertEqual(len(set(bridge.FAILURE_REASONS)), 16)

    def test_a_hit_prints_one_json_line_and_exits_zero(self):
        runtime = make_runtime({
            "fc2club": FakeMetadata(number="FC2-PPV-1", title="標題", actors=[{"name": "A", "gender": "female"}]),
            "avsox": None,
        })
        code, lines = run_main(["--number", "FC2-PPV-1", "--sites", "fc2club,avsox"], runtime)
        self.assertEqual(code, bridge.EXIT_FOUND)
        self.assertEqual(len(lines), 1)
        report = json.loads(lines[0])
        self.assertEqual(report["number"], "FC2-PPV-1")
        self.assertEqual(report["amane"], {"version": "0.16.1"})
        self.assertEqual(report["sites"]["fc2club"]["status"], "found")
        self.assertEqual(report["sites"]["fc2club"]["metadata"]["title"], "標題")
        self.assertEqual(report["sites"]["avsox"], {"status": "not_found", "reason": "not_found",
                                                   "elapsed_s": report["sites"]["avsox"]["elapsed_s"]})

    def test_all_misses_exit_two_and_any_error_without_a_hit_exits_three(self):
        runtime = make_runtime({"avsox": None, "airav": None})
        code, _ = run_main(["--number", "ABW-1", "--sites", "avsox,airav"], runtime)
        self.assertEqual(code, bridge.EXIT_NOT_FOUND)
        runtime = make_runtime({
            "avsox": None,
            "airav": FakeSourceError("cloudflare_blocked", http_status=403, detail="blocked", url="https://x/y"),
        })
        code, lines = run_main(["--number", "ABW-1", "--sites", "avsox,airav"], runtime)
        self.assertEqual(code, bridge.EXIT_FAILED)
        record = json.loads(lines[0])["sites"]["airav"]
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["reason"], "cloudflare_blocked")
        self.assertEqual(record["http_status"], 403)
        self.assertEqual(record["url"], "https://x/y")

    def test_an_unknown_reason_is_kept_in_detail_under_unexpected(self):
        record = bridge.failure_record(FakeSourceError("brand_new_reason", detail="x" * 600))
        self.assertEqual(record["reason"], "unexpected")
        self.assertTrue(record["detail"].startswith("brand_new_reason: xxx"))
        self.assertLessEqual(len(record["detail"]), 500)

    def test_a_crash_inside_one_site_does_not_take_the_batch_down(self):
        runtime = make_runtime({"avsox": RuntimeError("boom"), "freejavbt": FakeMetadata(number="ABW-1", title="t")})
        code, lines = run_main(["--number", "ABW-1", "--sites", "avsox,freejavbt"], runtime)
        self.assertEqual(code, bridge.EXIT_FOUND)
        report = json.loads(lines[0])
        self.assertEqual(report["sites"]["avsox"]["reason"], "unexpected")
        self.assertIn("RuntimeError: boom", report["sites"]["avsox"]["detail"])

    def test_usage_errors_exit_four_with_a_json_error(self):
        runtime = make_runtime({})
        code, lines = run_main(["--number", "ABW-1", "--sites", "nosuchsite"], runtime)
        self.assertEqual(code, bridge.EXIT_USAGE)
        self.assertEqual(json.loads(lines[0]), {"error": "未知站名：nosuchsite"})
        code, lines = run_main(["--number", "  ", "--sites", "avsox"], runtime)
        self.assertEqual(code, bridge.EXIT_USAGE)
        self.assertIn("error", json.loads(lines[0]))
        code, _ = run_main(["--sites", "avsox"], runtime)
        self.assertEqual(code, bridge.EXIT_USAGE)

    def test_the_proxy_reaches_the_client_factory(self):
        seen = {}

        def make_client(proxy, timeout, rate):
            seen.update(proxy=proxy, timeout=timeout, rate=rate)
            return None

        runtime = make_runtime({"avsox": None})
        runtime = bridge.Runtime(crawler=runtime.crawler, make_client=make_client, query=runtime.query,
                                 options=runtime.options, source_error=runtime.source_error)
        run_main(["--number", "ABW-1", "--sites", "avsox", "--proxy", "http://127.0.0.1:7897",
                  "--timeout", "12", "--rate", "1.5"], runtime)
        self.assertEqual(seen, {"proxy": "http://127.0.0.1:7897", "timeout": 12.0, "rate": 1.5})


if __name__ == "__main__":
    unittest.main()
