"""本机启动、卸载范围与公共代理的隔离回归。"""
import json
import base64
import ctypes
import os
import subprocess
import sys
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
        empty = app[app.index('empty:`<section'):app.index("review:entryCard('review')")]
        self.assertNotIn('data-fieldset-type="error"', empty)
        self.assertIn('data-cleanup-empty-scan', empty)
        self.assertIn('class="danger" data-cleanup-empty hidden', empty)
        self.assertIn("{dry_run:true}", app)

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
            desktop_startup.save(self.config, enabled='false', silent=True, desktop=False)
        # 三个开关一视同仁。`desktop` 缺省会静默删掉桌面图标，所以它不给默认值，
        # 路由漏传就在这里变成 400，而不是替用户做决定。
        with self.assertRaises(ValueError):
            desktop_startup.save(self.config, enabled=False, silent=True, desktop=None)

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

    def test_a_shortcut_aimed_at_the_packaged_entry_still_counts_as_this_installation(self):
        """`dist/Peach/Peach.exe` 和 `pythonw.exe -c "…peach.tray…"` 是同一份 Peach 的两个入口。

        源码安装里 `target()` 只给出后者。按字面比目标路径，配置页会把自己先前放在桌面上
        的图标判成「另一份 Peach 安装」并锁住那颗开关，用户连关掉它都不行；本机的桌面图标
        就是这么被锁住的（0.29.0 上线后实测）。所以源码安装的归属判到整个项目目录。
        """
        program = Path(sys.executable).with_name('pythonw.exe')
        packaged = (settings_file.PROJECT_ROOT / 'dist/Peach/Peach.exe').resolve()
        with patch.object(desktop_startup.distribution, 'standalone', return_value=False):
            self.assertTrue(desktop_startup.owned_target(packaged, program))
            self.assertFalse(desktop_startup.owned_target((self.program / 'Peach.exe').resolve(), program))
        # 独立发行版没有项目目录这层放宽：那份包只认自己那个 exe。
        with patch.object(desktop_startup.distribution, 'standalone', return_value=True):
            self.assertFalse(desktop_startup.owned_target(packaged, program))

    @unittest.skipUnless(os.name == 'nt', 'Windows known folder')
    def test_desktop_directory_comes_from_the_known_folder_not_the_home_path(self):
        """桌面目录问 shell 要，不拼 `%USERPROFILE%\\Desktop`。

        开了 OneDrive 备份的 Windows 11 把桌面重定向到 `%USERPROFILE%\\OneDrive\\Desktop`，
        拼出来那个目录用户根本看不到。判据取 shell 自己的答案：`SHGetKnownFolderPath`
        一旦失败，函数会静默退回拼路径，只断言「返回了个存在的目录」是看不出来的。
        """
        shell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        result = subprocess.run(
            [str(shell), '-NoProfile', '-NonInteractive', '-Command',
             "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);[Environment]::GetFolderPath('Desktop')"],
            capture_output=True, text=True, encoding='utf-8', timeout=25,
            creationflags=subprocess.CREATE_NO_WINDOW, check=True)
        self.assertEqual(desktop_startup.desktop_directory(), Path(result.stdout.strip()))

    @unittest.skipUnless(os.name == 'nt', 'Windows 原生快捷方式')
    def test_desktop_shortcut_has_its_own_switch_and_yields_to_another_installation(self):
        """桌面图标由第三个开关单独管，参数固定 `--show`，遇到别人的图标不覆盖。

        `--show` 跟「静默启动」无关：静默只管开机那一次，桌面图标是用户特意去点的。托盘
        已经在跑时 `tray.main()` 拿不到单实例锁，`--show` 那一支正好打开网页。

        桌面上摆着另一份安装的 `Peach.lnk` 时，要求开启照实拒绝，要求关闭则跳过它——那个
        图标本来就不是这份安装放的，不能因为它挡在那儿连「开机自启」都存不下。
        """
        startup = self.root / 'startup'
        startup.mkdir()
        program = self.program / 'Peach.exe'
        icon = self.root / 'Peach.lnk'
        with patch.object(desktop_startup, 'desktop_directory', return_value=self.root), \
                patch.object(desktop_startup, 'startup_directory', return_value=startup), \
                patch.object(desktop_startup, 'target', return_value=(program, ['--data-root', str(self.data)], self.program)):
            state = desktop_startup.save(self.config, enabled=False, silent=True, desktop=True)
            self.assertTrue(state['desktop'])
            self.assertTrue(icon.is_file(), sorted(item.name for item in self.root.iterdir()))
            self.assertIn('--show', desktop_startup.shortcut('read', icon)['arguments'])
            self.assertEqual(sorted(item.name for item in startup.iterdir()), [])
            self.assertTrue(desktop_startup.desktop_snapshot(self.config)['desktop'])

            other = self.program / 'Other.exe'
            other.touch()
            desktop_startup.shortcut('write', icon, target=str(other), directory=str(self.program), expected=str(program))
            with self.assertRaisesRegex(ValueError, '另一份'):
                desktop_startup.save(self.config, enabled=False, silent=True, desktop=True)
            self.assertEqual(desktop_startup.desktop_snapshot(self.config),
                             {'desktop': False, 'desktop_message': '桌面快捷方式属于另一份 Peach 安装'})
            desktop_startup.save(self.config, enabled=True, silent=True, desktop=False)
            self.assertEqual(len(list(startup.iterdir())), 1)
            self.assertTrue(icon.is_file())

    def _shortcut_round_trip(self, name):
        path = self.root / name
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
    def test_native_shortcut_round_trip_in_temporary_directory(self):
        self._shortcut_round_trip('startup fixture.lnk')

    @unittest.skipUnless(os.name == 'nt', 'Windows 原生快捷方式')
    def test_native_shortcut_round_trip_survives_a_non_ascii_name(self):
        """中文名的往返，判据按系统 ANSI 码页给，不按平台给。

        `WScript.Shell` 的 `Save()` 把路径降级到 `GetACP()`，编不出来的字符按字一个换成
        `?`，而 `?` 是 Windows 的非法文件名字符，于是报 `Unable to save shortcut
        "...\\?? fixture.lnk"`。本机 ACP 是 936，中文编得出来；GitHub 的 windows-latest
        是西欧码页，同一个名字在那儿必失败。本机用泰文和希伯来文复现过同一条错误消息
        （2026-09-07），确认是码页而不是权限、COM 或 stdin 解码。

        生产的启动项文件名是 `Peach-<12 位十六进制>.lnk`，只有用户目录段可能带非 ASCII；
        中文用户名的机器 ACP 就是 936，编得出来。这里不为 WSH 的这条限制换实现。
        """
        name = '启动 fixture.lnk'
        codepage = ctypes.windll.kernel32.GetACP()
        try:
            name.encode(f'cp{codepage}')
        except (UnicodeEncodeError, LookupError):
            self.skipTest(f'系统 ANSI 码页 cp{codepage} 表示不了「{name}」，WScript.Shell 存不下')
        self._shortcut_round_trip(name)

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
