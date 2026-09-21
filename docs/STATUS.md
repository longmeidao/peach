# Peach 当前状态

最后核验：2026-09-14

索引：`PRODUCT_BACKLOG.md`、`REUSE.md`、`HANDOFF.md`；BoardUI 见 `BOARD_UI.md`。

## 运行态

- 女优头像 545 张，脸宽中位数 320px，37 张带水印待复核；被顶掉的整套留在 `avatars-superseded/`（判据见 `SOURCING.md`）。
- 小图、资料骨架、官网图标、社媒品牌色与自动播放开关已实现，请求共用 Chrome UA；厂牌标识 198 张随仓库分发（ADR-0026）。
- Eightman 与 SO MODEL AGENT 已合为 8662，成员与关联作品保留，旧名仍可解析。
- 产地是独立维度，JAV 是它的投影：`region` 为空时按厂牌、创作者、番号逐层推断，不落库；韩国 MIB 已不算 JAV。

- Windows 是 ledger writer，入口是源码托盘（`pythonw -m peach.tray`，子服务用 venv 的 `peach.exe`），重启 `restart_windows_tray.py --source`；代码与数据在内置盘，外置盘只供 `R:\media`。
- 托盘必须普通权限启动：提权后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报脱盘。
- Windows HTTP `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名见 `[server].mdns_name`；线上版本 `0.33.0`、`ledger_sync=writer`，项目 CA 严格校验的 `/healthz` 通过。
- 经正式域名访问时 `/healthz` 返回 `configurable=true`；配置读写与选文件夹共用本机连接判据；托盘负责配置重载与正式 HTTPS 地址、端口。
- 首启和配置页按系统显示缺失依赖下载：CloudDrive、挂载驱动、FFmpeg/ffprobe、OpenSSL；Windows 已识别 CloudDrive 与 WinFsp。
- 文件检查覆盖本地与网盘，来源等分，确认用共享弹层；CloudDrive 分档建议共用首启与配置入口；来源接口需登录（401）。
- 可选密码已上线：首启可跳过，配置页可改可关，登录可记住设备；旧安装保留口令。
- macOS 是 reader，代码与 `peach-data` 在内置盘；`peach.local` 经 8900/8443 和 pf 提供 80/443，GET 正常、写入返回 409。
- 两端各用本机 CA，私钥与凭据不跨机同步；代码走 Git、账本走单写者复制、图片走 Syncthing，三条链路互不兜底。本机坐标在 `<数据根>/config.toml`；ADR-0023 第 1～3 阶段已在 Windows 生效。
- Windows 真实 ledger `peach-data/database/ledger.db`，2026-09-13 已应用到 `0031`；`asset_subtitle` 195 行（孤立 19），175 部带字幕轨。09-12 修掉 `local` 路径大小写重复，`asset` 80,761 行。
- Mac ledger 已授权从共享副本显式拉取并恢复 `in-sync`；`sources` 已迁内置盘，`archive`、`tools` 仍可指向外置盘。
- 前端按 ADR-0031 逐页迁往 `frontend/` 的 React + Tailwind + BoardUI 源码，只有 React 一档；产物进 Git，经 `/dist/{name}` 提供；改前端需 Node 24+（`docs/FRONTEND.md`）。
- 本机运行 Python 3.14；`requires-python` 下限 3.12，GitHub Actions 同时测 3.12 与 3.14；Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。
- 发行名 `peach`，目录名 `peach-app`。macOS 落后 master 一组有顺序的操作（待办「待执行的操作」第 30 条），做完前别重启菜单栏：无口令的 `peach serve --host 0.0.0.0` 会拒绝启动。
- 扫描与采集显示项目、动作与等待时长；无进展 120 秒预警，单项外部动作（资料 90 秒、封面 240 秒）超预算跳过该项计入可重试，「重试未完成项」重跑原任务失败集合。问题写入 `state/library-processing-<job_id>.issues.jsonl`（带标题与路径），接口按 `job_id` 分页，页面错误折叠给前 20 条与日志地址。已部署核对。
- Cloudflare 公网入口默认关闭，配置页启停，须先设访问密码；临时链接地址只写状态文件，命名隧道限源码环境、令牌只存设置文件。整站 `X-Robots-Tag: noindex` 加 `/robots.txt`。

## 批处理进度

账本与产物的现算数字由 hook 写进 `peach-data/state/job-status.md`（不进 Git，本机直接看），手动重算 `python scripts/job_status.py`。
