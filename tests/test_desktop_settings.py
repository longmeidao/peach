"""本机启动、卸载范围与公共代理的隔离回归。"""
import json
import base64
import os
import subprocess
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from peach import desktop_startup, desktop_uninstall, peach_proxy, scraping_access, settings_file


class DesktopSettingsTests(unittest.TestCase):
    def test_configuration_order_and_danger_area_share_the_ui_contract(self):
        root = Path(__file__).resolve().parents[1]
        configuration = (root / 'frontend/src/islands/configuration.tsx').read_text(encoding='utf-8')
        names = ['<StartupSettings', '<ConfigurationForm', '<MountStatus', '<PeachProxy', '<AccessSettings', '<ReleaseUpdates', '<Facts', '<UninstallSettings']
        # 定位配置主页面，排除同文件中组件定义的内部 JSX。
        page = configuration[configuration.index('export function Configuration('):]
        self.assertEqual(sorted(names, key=page.index), names)
        css = (root / 'web/css/23-configuration.css').read_text(encoding='utf-8')
        self.assertIn('[data-fieldset-type="error"]{border-color:var(--drop)}', css)
        self.assertGreater(css.index('[data-fieldset-type="error"]>:is('), css.index('.configfieldset>.geist-fieldset-footer{'))
        self.assertIn('.configselect{width:min(320px,100%)}', css)
        self.assertIn('.configdirectories .fcollapsebody{padding:12px 4px 4px}', css)

    def test_cleanup_risk_colors_follow_the_operation_effect(self):
        root = Path(__file__).resolve().parents[1]
        app = (root / 'web/app.js').read_text(encoding='utf-8')
        links = app[app.index('function linkManagerMarkup'):app.index('function resourceSyncMarkup')]
        sync = app[app.index('function resourceSyncMarkup'):app.index('async function openTaste')]
        self.assertIn('data-fieldset-type="error"', links)
        renderer = (root / 'frontend/src/resource-sync.ts').read_text(encoding='utf-8')
        self.assertIn('resourceScanHtml(payload,fmtSize)', sync)
        self.assertIn("{label: '清理内容'}", renderer)
        self.assertIn('class="geist-button primary" type="button" id="resourceApply"', renderer)
        self.assertIn("danger:false,onConfirm", sync)
        self.assertIn('cleanupemptyfolders" data-geist-fieldset data-fieldset-type="error"', app)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.data = self.root / 'data'
        self.data.mkdir()
        self.program = self.root / 'Peach'
        (self.program / '_internal').mkdir(parents=True)
        (self.program / '_internal/standalone.txt').touch()
        (self.program / 'Peach.exe').touch()
        self.config = SimpleNamespace(data_root=self.data, path=self.data / 'config.toml', locations={'local': (str(self.root / 'media'),)}, mounts={},
                                      directory=lambda key: self.data / key)

    def test_uninstall_plan_keeps_media_and_can_preserve_all_data(self):
        keep = desktop_uninstall.plan(self.config, delete_data=False, program=self.program)
        self.assertEqual(keep['directories'], [])
        full = desktop_uninstall.plan(self.config, delete_data=True, program=self.program)
        self.assertEqual(len(full['directories']), len(settings_file.DIRECTORY_KEYS))
        self.assertNotIn(str(self.root / 'media'), full['directories'])

    def test_uninstall_refuses_media_overlap_external_storage_and_source_tree(self):
        self.config.locations = {'local': (str(self.data / 'sources/media'),)}
        with self.assertRaisesRegex(ValueError, '媒体'):
            desktop_uninstall.plan(self.config, delete_data=True, program=self.program)
        self.config.locations = {}
        self.config.directory = lambda key: self.root / key
        with self.assertRaisesRegex(ValueError, '外部'):
            desktop_uninstall.plan(self.config, delete_data=True, program=self.program)
        (self.program / '.git').mkdir()
        with self.assertRaisesRegex(ValueError, '程序目录'):
            desktop_uninstall.plan(self.config, delete_data=False, program=self.program)

    def test_proxy_private_address_is_shared_but_direct_source_bypasses_it(self):
        peach_proxy.save(self.root, {'mode': 'proxy', 'proxy': 'http://user:password@127.0.0.1:7890'})
        self.assertNotIn('password', json.dumps(peach_proxy.describe(self.root)))
        peach_proxy.save(self.root, {'mode': 'proxy', 'proxy': ''})
        with patch('peach.scraping_access.httpx.Client') as factory:
            scraping_access.client_for(self.root, 'dmm')
            self.assertIn('proxy', factory.call_args.kwargs)
            scraping_access.save(self.root, 'dmm', {'network': 'direct'})
            scraping_access.client_for(self.root, 'dmm')
            self.assertNotIn('proxy', factory.call_args.kwargs)
            self.assertFalse(factory.call_args.kwargs['trust_env'])

    def test_legacy_proxy_conflict_requires_selection_without_writing_secrets(self):
        from peach.follow_secrets import CredentialStore
        store = CredentialStore(self.root)
        for source, port in [('dmm',7890),('mgstage',7891)]:
            path = store.path_for('scraping-' + source)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'network':'proxy','proxy':f'http://127.0.0.1:{port}'}))
        self.assertTrue(peach_proxy.describe(self.root)['needs_selection'])
        with self.assertRaisesRegex(ValueError, '来源代理'):
            peach_proxy.client_options(self.root)
        peach_proxy.save(self.root, {'mode':'direct'})
        self.assertEqual(peach_proxy.client_options(self.root), {'trust_env':False})

    def test_startup_preserves_explicit_data_root_and_validates_booleans(self):
        program, args, _ = desktop_startup.target(self.config, executable=self.program / 'Peach.exe')
        self.assertEqual(args, ['--data-root', str(self.data)])
        self.assertEqual(program.parent, self.program)
        with self.assertRaises(ValueError):
            desktop_startup.save(self.config, enabled='false', silent=True)

    def test_configuration_actions_require_local_origin_and_uninstall_confirmation(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from peach import routes_configuration
        from peach.routes_auth import require_auth
        app = FastAPI()
        app.include_router(routes_configuration.router)
        app.dependency_overrides[require_auth] = lambda: None
        app.state.web_contract = SimpleNamespace()
        with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1',123)) as client, \
                patch.object(routes_configuration, 'managed_configuration', return_value=False), \
                patch.object(settings_file, 'load_config', return_value=self.config), \
                patch.object(desktop_uninstall, 'request', return_value={'accepted':True}) as remove:
            self.assertEqual(client.post('/api/configuration/uninstall',json={'delete_data':True}).status_code,400)
            self.assertEqual(client.post('/api/configuration/uninstall',json={'delete_data':True,'confirmation':'卸载 Peach'},
                                         headers={'origin':'https://other.invalid'}).status_code,403)
            remove.assert_not_called()
            self.assertEqual(client.post('/api/configuration/uninstall',json={'delete_data':False,'confirmation':'卸载 Peach'}).status_code,200)
            remove.assert_called_once_with(self.config,False)
            self.assertEqual(client.post('/api/configuration/startup',json={'enabled':'false','silent':True}).status_code,400)
            self.assertEqual(client.post('/api/configuration/peach-proxy',json={'mode':'proxy','proxy':'invalid'}).status_code,400)

    def test_startup_does_not_overwrite_another_installation(self):
        with patch.object(desktop_startup, 'startup_directory', return_value=self.root), patch.object(desktop_startup, 'shortcut', side_effect=[
            {'enabled':False}, {'enabled':True,'target':str(self.root / 'Other.exe')}]), self.assertRaisesRegex(ValueError, '另一份'):
            desktop_startup.windows_entry(self.config, self.program / 'Peach.exe')

    @unittest.skipUnless(os.name == 'nt', 'Windows 原生快捷方式')
    def test_native_shortcut_round_trip_in_temporary_directory(self):
        path = self.root / '启动 fixture.lnk'
        program = str(self.program / 'Peach.exe')
        written = desktop_startup.shortcut('write', path, target=program, arguments='--silent', directory=str(self.program))
        # 写完立刻核对文件就在这个路径上。只在 remove 之后断言不存在的话，`Save()` 把
        # 快捷方式落到别处或压根没落地都照样通过，runner 上红的正是这一段。
        self.assertTrue(written['enabled'])
        self.assertTrue(path.is_file(), sorted(item.name for item in self.root.iterdir()))
        result = desktop_startup.shortcut('read', path)
        self.assertEqual(Path(result['target']).resolve(), Path(program))
        self.assertEqual(result['arguments'], '--silent')
        desktop_startup.shortcut('remove', path, expected=result['target'])
        self.assertFalse(path.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows 原生快捷方式')
    def test_a_failed_shortcut_call_reports_what_powershell_said(self):
        """失败的消息带上脚本自报的原因、异常类型和行号，不只给一句「请检查权限」。

        权限不足、`WScript.Shell` COM 起不来、路径没落地、扩展名不是 `.lnk`——这几种
        在只有一句提示的消息里长得一模一样。CI 的 Windows runner 上这一步失败过，日志里
        除了那句提示什么都没有，无从判断是哪一种。

        判据落在脚本 `catch` 出来的那一行 JSON 上，不看退出码也不看 stderr：Windows
        PowerShell 5.1 成功那一次也往 stderr 写 `#< CLIXML` 的进度流，照它取原因只会拿到
        「正在准备首次使用模块。」。
        """
        with self.assertRaises(OSError) as raised:
            desktop_startup.shortcut('write', self.root / '不是快捷方式.txt',
                                     target=str(self.program / 'Peach.exe'))
        message = str(raised.exception)
        self.assertIn('启动项未能保存', message)
        self.assertIn('Expected shortcut', message)
        self.assertRegex(message, r'第 \d+ 行')
        self.assertNotIn('CLIXML', message)

    @unittest.skipUnless(os.name == 'nt', 'Windows 系统卸载助手')
    def test_native_uninstall_removes_only_temporary_owned_program_and_data(self):
        for key in settings_file.DIRECTORY_KEYS:
            path = self.config.directory(key)
            path.mkdir()
            (path / 'fixture.txt').write_text('fixture')
        self.config.path.write_text('fixture')
        unrelated = self.data / 'personal.txt'
        unrelated.write_text('preserve')
        media = self.root / 'media'
        media.mkdir()
        (media / 'video.mp4').write_text('preserve')
        job = desktop_uninstall.plan(self.config, delete_data=True, program=self.program)
        shell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        result = subprocess.run([str(shell), '-NoProfile', '-NonInteractive', '-EncodedCommand',
                                 base64.b64encode(desktop_uninstall._SCRIPT.encode('utf-16-le')).decode('ascii')],
                                input=json.dumps(dict(job, pid=2147483647)).encode('utf-8'), capture_output=True, timeout=25,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.program.exists())
        self.assertFalse(self.config.path.exists())
        self.assertTrue(unrelated.is_file())
        self.assertTrue((media / 'video.mp4').is_file())
