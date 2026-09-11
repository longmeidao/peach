# Peach 当前状态

最后核验：2026-09-10

索引：`PRODUCT_BACKLOG.md`、`REUSE.md`、`HANDOFF.md`。

## 运行态

- BoardUI：状态演示 `/state-preview`；生产未切换，验收见 `BOARD_UI.md`。

- 设置与反馈已部署；自动更新设置未部署。

- 女优头像 545 张，脸宽中位数 320px；被顶掉的整套留在 `avatars-superseded/`，挑图与换源判据见 `SOURCING.md`。
- 小图、资料骨架、官网图标、X 原色与自动播放开关已实现；请求共用 Chrome UA。厂牌标识 198 张随仓库分发（ADR-0026）。
- Eightman 与 SO MODEL AGENT 已合为 8662，成员与关联作品保留，旧名仍可解析。

- Windows 是 ledger writer，入口 `dist\Peach\Peach.exe`；代码与数据在内置盘，外置盘只提供 `R:\media`。
- 托盘必须以普通权限启动：提升权限后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报为脱盘。
- Windows HTTP 为 `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名见 `[server].mdns_name`；线上版本 `0.27.1`、`ledger_sync=writer`，项目 CA 严格校验的 `/healthz` 通过。
- Web 源码 `3766e718` 已重启；托盘 `3766e718`。
- 本机经正式域名访问时 `/healthz` 返回 `configurable=true`；配置读取、保存与选文件夹共用本机连接判据。托盘负责配置重载，正式 HTTPS 地址与端口保持托盘管理。
- 首启和配置页按系统显示缺失依赖下载：CloudDrive、挂载驱动、FFmpeg/ffprobe、OpenSSL；Windows 已识别 CloudDrive 与 WinFsp。
- 文件检查覆盖本地与网盘，来源等分；确认使用共享弹层。CloudDrive 分档建议共用首启与配置入口；来源接口需登录（401）。
- 可选密码已上线：首启可跳过；配置页可修改、关闭；登录可记住设备。旧安装保留口令。
- macOS 是 reader，代码与 `peach-data` 都在内置盘；`peach.local` 经 8900/8443 和 pf 提供 80/443，GET 正常、写入端点返回 409。
- 两端各用本机 CA，私钥与凭据不跨机同步；代码走 Git、账本走单写者复制、图片产物走 Syncthing，三条链路互不兜底。本机坐标在 `<数据根>/config.toml`；ADR-0023 第 1～3 阶段已合入并在 Windows 生效。
- Windows 真实 ledger 为 `peach-data/database/ledger.db`，已应用到 `0024`（外键 ON DELETE 与索引），0 待处理。
- Mac ledger 已授权从共享副本显式拉取并恢复 `in-sync`；`sources` 已迁到内置盘，`archive`、`tools` 仍可指向外置盘。
- 代码任何一处都不再连 Stash，媒体解析只有 `FilesystemBackend` 一条路径（ADR-0021）；Stash 遗留的数据缺陷与许可证边界见 `docs/STASH.md`。
- 前端按 ADR-0022 以 Preact island 逐岛迁往 `frontend/`（Vite + TypeScript），产物 `web/dist/peach-ui.js` 进 Git、经 `/dist/{name}` 提供，`/quality-goals` 已迁；改前端需 Node 24+，见 `docs/FRONTEND.md`。
- 本机运行 Python 3.14；`requires-python` 下限 3.12，GitHub Actions 同时测 3.12 与 3.14；Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。
- 发行名 `peach`，目录名 `peach-app`；Windows venv 已按发行名重装。macOS 落后 master 一组有顺序的操作（待办「待执行的操作」第 30 条），做完之前别重启菜单栏：没有口令的 `peach serve --host 0.0.0.0` 会拒绝启动。
- 扫描与采集显示当前项目、动作与等待时长；无进展 120 秒页面预警，单项外部动作（资料 90 秒、封面 240 秒）超预算只跳过该项并计入可重试；「重试未完成项」按原任务失败集合重试。完整问题写入 `state/library-processing-<job_id>.issues.jsonl`，每条带标题与路径，接口按 `job_id` 分页读取；页面把前 20 条与日志地址收在错误提示的折叠里。已部署核对。

## 批处理进度

账本与产物的现算数字由 Stop/SessionEnd hook 写进 `peach-data/state/job-status.md`（不进 Git，本机直接看）；手动重算跑 `python scripts/job_status.py`。
