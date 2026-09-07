"""验证选测边界、分片完整性与临时账本隔离。"""
from pathlib import Path
import contextlib
import io
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import ci_plan, test_runner as runner
from support.ledger import fresh_ledger


class TestPlanningTests(unittest.TestCase):
    def test_dependency_changes_require_full_but_tool_version_does_not(self):
        source = '[project]\nrequires-python=">=3.12"\ndependencies=["demo==1"]\n[tool.uv]\nrequired-version="==1"\n'
        for replacement, expected in ((source.replace('==1"\n', '==2"\n'), ('packaging',)),
                                      (source.replace('demo==1', 'demo==2'), ('full',)),
                                      (source.replace('>=3.12', '>=3.14'), ('full',)),
                                      ('[invalid', ('full',))):
            with self.subTest(replacement=replacement):
                scopes, _ = runner.scopes_for_changes(['pyproject.toml'], contents={
                    'pyproject.toml': (source, replacement)})
                self.assertEqual(scopes, expected)
        self.assertEqual(runner.scopes_for_changes(['pyproject.toml'])[0], ('full',))

    def test_matrix_keeps_full_mainline_and_platform_floor(self):
        result = ci_plan.plan('push', ['web/app.js'])
        rows = result['matrix']['include']
        self.assertEqual(len([r for r in rows if r['scope'] == 'full']), 2)
        self.assertTrue(all(r['os'] == 'macos-latest' for r in rows if r['scope'] == 'full'))
        self.assertTrue(any(r['python'] == '3.12' and r['scope'] == 'core' for r in rows))
        self.assertEqual(len(result['wheel_matrix']['include']), 2)

    def test_dependency_and_manual_runs_cover_both_systems(self):
        for event, paths in [('push', ['uv.lock']), ('pull_request', ['migrations/0025.sql']),
                             ('workflow_dispatch', [])]:
            result = ci_plan.plan(event, paths)
            self.assertTrue(result['wide'])
            self.assertEqual({r['os'] for r in result['matrix']['include'] if r['scope'] == 'full'},
                             {'macos-latest', 'windows-latest'})
            self.assertEqual(len(result['wheel_matrix']['include']), 4)

    def test_pull_request_uses_changed_domains(self):
        rows = ci_plan.plan('pull_request', ['src/peach/follow_store.py'])['matrix']['include']
        self.assertTrue(any(r['scope'] == 'auto' for r in rows))
        self.assertFalse(any(r['scope'] == 'full' for r in rows))
        self.assertEqual(runner.scopes_for_changes(['scripts/localize_performer_names.py'])[0], ('metadata',))

    def test_missing_git_base_selects_wide_matrix(self):
        with patch.object(sys, 'argv', ['ci_plan.py', '--event', 'push', '--base', 'missing']), \
             patch.object(runner, 'changed_files', side_effect=subprocess.CalledProcessError(1, 'git')), \
             patch.dict(ci_plan.os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()) as output:
            ci_plan.main()
        self.assertTrue(ci_plan.json.loads(output.getvalue())['wide'])

    def test_venv_interpreter_path_keeps_environment_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            suffix = 'Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'
            executable = root / '.venv' / suffix
            executable.parent.mkdir(parents=True)
            executable.touch()
            with patch.object(Path, 'resolve', side_effect=AssertionError('不能解引用 venv 解释器')):
                self.assertEqual(runner.test_evidence.interpreter(root), executable)

    def test_shards_cover_every_case_once_including_supplements(self):
        def ids(suite):
            for case in suite:
                if isinstance(case, unittest.TestSuite):
                    yield from ids(case)
                else:
                    yield case.id()
        # 使用实际域注册验证交集和补充用例，不执行其中的测试。
        serial = list(ids(runner.build_suite('follow', 'tooling')))
        shards = [list(ids(runner.build_suite('follow', 'tooling', shard_index=i, shard_count=2)))
                  for i in range(2)]
        self.assertEqual(len(serial), len(set(serial)))
        self.assertFalse(set(shards[0]) & set(shards[1]))
        self.assertCountEqual(serial, shards[0] + shards[1])

    def test_partial_run_does_not_issue_verification_record(self):
        with patch.object(runner, 'build_suite', return_value=unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])), \
             patch.object(runner.test_evidence, 'inputs', side_effect=AssertionError('分片不能签发证据')):
            self.assertEqual(runner.main(['--scope', 'full', '--shard-count', '2']), 0)

    def test_a_test_reading_a_web_source_runs_when_that_source_changes(self):
        """断言 `web/`、`frontend/` 文件的测试，必须登记在改那个文件会选到的域里。

        域表是人手维护的，漏登记不会报错，只会在 CI 上红：`tests/test_follow_web.py` 读
        `web/app.js`，却只登记在 follow 域，于是改了 `web/app.js` 跑 `auto` 时它根本不在
        选中的文件里。这一条按测试源码里真实存在的路径拼接反查，把漏登记变成本地就红。

        判据只覆盖这两个前缀：域表对它们是按目录映射的，除此以外没有第二条路让测试被选
        中。`src/peach/` 有按模块名的推断，`scripts/`、`docs/` 那些落在 tooling 与 checks
        的兜底上，同一个漏洞在那边也成立，但要补的是域表本身，不在本条范围内。
        """
        watched = ('web/', 'frontend/')
        for path in sorted((runner.ROOT / 'tests').glob('test_*.py')):
            read = [item for item in runner.repository_paths_read_by(path.read_text(encoding='utf-8'))
                    if item.startswith(watched)
                    and not any(item.startswith(prefix) for prefix in runner.FULL_ONLY_PREFIXES)]
            for item in read:
                scopes, why = runner.scopes_for_changes([item])
                selected = {chosen.name for scope in scopes for chosen in runner.selected_files(scope)}
                self.assertIn(path.name, selected, f'{path.name} 读 {item}，但 {why} 选不到它')

    def test_template_copies_have_independent_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            first, second = fresh_ledger(root, 'first.db'), fresh_ledger(root, 'second.db')
            for path in (first, second):
                connection = sqlite3.connect(path)
                try:
                    self.assertEqual(connection.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                    if path == first:
                        connection.execute('CREATE TABLE isolation_probe(value TEXT)')
                        connection.commit()
                    else:
                        self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='isolation_probe'").fetchone())
                finally:
                    connection.close()
