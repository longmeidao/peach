# Peach 当前状态

最后核验：2026-09-14

只记运行状态。待办见 `PRODUCT_BACKLOG.md`，判据见 `REUSE.md`，长期约定见 `HANDOFF.md`。

## 运行态

- 女优头像 545 张（中位脸宽 320px，37 张带水印待复核）；被顶掉的在 `avatars-superseded/`。
- 数据管理页「整理」（ADR-0039）可预览、执行、回滚上一批，真实库未执行过。
- 产地是独立维度，JAV 是它的投影：`region` 为空时按厂牌、创作者、番号逐层推断，不落库；韩国 MIB 不算 JAV。
- Windows 是 ledger writer，入口是源码托盘（`pythonw -m peach.tray`），重启 `restart_windows_tray.py --source`；代码与数据在内置盘，外置盘只供 `R:\media`。
- 托盘须普通权限启动：提权令牌看不到 CloudDrive 的 `A:`/`B:`，会误报脱盘。
- Windows HTTP `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名见 `[server].mdns_name`；线上版本 `0.33.0`、`ledger_sync=writer`，项目 CA 严格校验的 `/healthz` 通过。
- 经正式域名访问时 `/healthz` 返回 `configurable=true`；配置读写与选文件夹共用本机连接判据；托盘负责配置重载与正式 HTTPS 地址、端口。
- 首启和配置页按系统显示缺失依赖下载：CloudDrive、挂载驱动、FFmpeg/ffprobe、OpenSSL；Windows 已识别 CloudDrive 与 WinFsp。
- 文件检查覆盖本地与网盘，来源等分，确认用共享弹层；CloudDrive 分档建议共用首启与配置入口；来源接口需登录（401）。
- 可选密码：首启可跳过，配置页可改可关，登录可记住设备。
- macOS 是 reader，代码与 `peach-data` 在内置盘；`peach.local` 经 8900/8443 和 pf 提供 80/443，GET 正常、写入返回 409。
- 两端各用本机 CA，私钥与凭据不跨机同步；代码走 Git、账本单写者复制、图片走 Syncthing；本机坐标在 `<数据根>/config.toml`。
- Windows 真实 ledger `peach-data/database/ledger.db`，2026-09-13 已应用到 `0031`；`asset_subtitle` 195 行（孤立 19），175 部带字幕轨，`asset` 80,761 行。
- Mac ledger 已授权从共享副本显式拉取并恢复 `in-sync`；`sources` 已迁内置盘，`archive`、`tools` 仍可指向外置盘。
- 前端按 ADR-0031 逐页迁往 `frontend/` 的 React + Tailwind + BoardUI 源码；产物进 Git，经 `/dist/{name}` 提供；改前端需 Node 24+（`docs/FRONTEND.md`）。
- 本机运行 Python 3.14；`requires-python` 下限 3.12，CI 同时测 3.12 与 3.14；Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。
- amane 桥（ADR-0048）装在 `peach-data/tools/amane-bridge/`，四类番号链都经它问。
- 发行名 `peach`，目录名 `peach-app`。macOS 落后 master 一组有顺序的操作（待办「待执行的操作」第 30 条），做完前别重启菜单栏：无口令的 `peach serve --host 0.0.0.0` 会拒绝启动。
- 扫描与采集显示项目与等待时长；无进展 120 秒预警，单项外部动作（资料 90 秒、封面 240 秒）超预算跳过并可重试；问题写入 `state/library-processing-<job_id>.issues.jsonl`。
- 账本版本号 `0038` 待迁，迁前口味、复核等聚合按 90 秒过期；补女优资料后继每轮存量至多 16 条。
- 实体种子（ADR-0075）由扫描结算的 `seed-import` 后继导入，只填空并换旧种子行；不一致与重复身份在 `generated/seed-landing.csv`。
- Cloudflare 公网入口默认关闭，配置页启停，须先设访问密码；临时链接地址只写状态文件，命名隧道限源码环境、令牌只存设置文件。整站 `X-Robots-Tag: noindex` 加 `/robots.txt`。
- FC2PPV-DB 与 JAVten 经本机 Chrome 过 Cloudflare 验证（ADR-0065），profile 在 `secrets/browser/`，不用贴 Cookie。

## 批处理进度

账本与产物的现算数字由 hook 写进 `peach-data/state/job-status.md`（不进 Git，本机直接看），手动重算 `python scripts/job_status.py`。
