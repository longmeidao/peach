# Peach 当前状态

最后核验：2026-09-06

本文件只记录运行态；待办见 `docs/PRODUCT_BACKLOG.md`，已定型的行为判据见 `docs/REUSE.md`，长期知识见 `docs/HANDOFF.md`。

## 运行态

- HTTPS 就绪；未打标签。开发验证默认 `auto`。

- Windows 是当前 ledger writer，入口 `dist\Peach\Peach.exe`；代码、`peach-data`、worktree 和共享传输点同在一个顶层目录，外置盘只提供 `R:\media`。
- 托盘必须以普通权限启动：提升权限后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报为脱盘。
- Windows HTTP 为 `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名见 `[server].mdns_name`；线上版本 `0.12.1`、`ledger_sync=writer`，项目 CA 严格校验的健康与就绪检查通过。
- 2026-09-06 从 `34341c78` 载入源码运行态，通过 `scripts/restart_windows_tray.py` 正常重启现有托盘并重新取得 HTTP/HTTPS 子服务所有权；本次未替换 EXE。换二进制走 `scripts/deploy_windows_tray.py`，且要单独授权。
- 本机经正式域名访问时 `/healthz` 返回 `configurable=true`；配置读取、保存与选文件夹共用本机连接判据。托盘负责配置重载，正式 HTTPS 地址与端口保持托盘管理。
- 缺失依赖下载提示已接入首启和配置页：CloudDrive、当前系统挂载驱动、FFmpeg/ffprobe，以及首次设置缺少 OpenSSL 的提示。Windows 实测安装检测识别到 CloudDrive 与 WinFsp；桌面及 390×844 预览通过，生产浏览器导航取证超时。全量 3278 项通过、17 项跳过，集成补测 1754 项通过、2 项跳过，前端 16 项通过。
- 首次设置提供可跳过的历史记录导入指南；数据管理首屏与实际卡片共用 Fieldset 排版，网盘同步与重复文件网盘保留操作按来源显隐，界面使用「本地数据库」。影响域 1762 项通过、2 项跳过，前端 67 项通过；桌面深浅色与 390×844 预览通过，正式页面浏览器读取超时。未执行真实资源同步、清理或浏览器历史采集。
- 口令闸门在 Windows 已生效：不带口令的请求回 401（`/healthz` 除外），设备用 `peach token` 登录一次。
- macOS 是 reader，代码与 `peach-data` 都在内置盘；`peach.local` 经 8900/8443 和 pf 提供 80/443，GET 正常、写入端点返回 409。
- 两端各用本机 CA，私钥与凭据不跨机同步；代码走 Git、账本走单写者复制、图片产物走 Syncthing，三条链路互不兜底。本机坐标在 `<数据根>/config.toml`；ADR-0023 第 1～3 阶段已合入并在 Windows 生效。
- Windows 真实 ledger 为 `peach-data/database/ledger.db`，已应用到 `0024`（外键 ON DELETE 与索引），0 待处理。
- Mac ledger 已授权从共享副本显式拉取并恢复 `in-sync`；`sources` 已迁到内置盘，`archive`、`tools` 仍可指向外置盘。
- 服务运行期不连 Stash，媒体解析只有 `FilesystemBackend` 一条路径（ADR-0021）；只剩两个离线导入脚本按需连它，见 `docs/STASH.md`。
- 前端按 ADR-0022 以 Preact island 逐岛迁往 `frontend/`（Vite + TypeScript），产物 `web/dist/peach-ui.js` 进 Git、经 `/dist/{name}` 提供，`/quality-goals` 已迁；改前端需 Node 24+，见 `docs/FRONTEND.md`。
- 本机运行 Python 3.14；`requires-python` 下限 3.12，GitHub Actions 同时测 3.12 与 3.14；Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。
- 发行名 `peach`，目录名 `peach-app`；Windows venv 已按发行名重装。macOS 落后 master 一组有顺序的操作（待办「待执行的操作」第 30 条），做完之前别重启菜单栏：没有口令的 `peach serve --host 0.0.0.0` 会拒绝启动。

## 批处理进度

账本与产物的现算数字由 Stop/SessionEnd hook 写进 `peach-data/state/job-status.md`（不进 Git，本机直接看）；手动重算跑 `python scripts/job_status.py`。
