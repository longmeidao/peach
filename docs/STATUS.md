# Peach 当前状态

最后核验：2026-09-03

本文件写「现在是什么样」，不按批次累积：待办去 `docs/PRODUCT_BACKLOG.md`，长期规则去
`docs/HANDOFF.md` 与 `docs/REUSE.md`，已完成批次与事故由 Git 历史保存。

## 运行态

- Windows 是当前 ledger writer，入口 `dist\Peach\Peach.exe`；代码、`peach-data`、worktree 和共享传输点同在一个顶层目录，外置盘只提供 `R:\media`。
- 托盘必须以普通权限启动：提升权限后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报为脱盘。
- Windows HTTP 为 `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名为 `peach-writer.local`；线上服务版本 `0.7.13`、`ledger_sync=writer`。
- macOS 是 reader，代码与 `peach-data` 都在内置盘；`peach.local` 经 8900/8443 和 pf 提供 80/443，GET 正常、写入端点返回 409。
- 托盘与菜单栏层的改动不会随服务子进程一起生效，要手动退出菜单栏项后由 `.app` 或 `launchctl kickstart -k` 重启一次。
- 两端各用本机 CA，私钥与凭据不跨机同步；代码走 Git、账本走单写者复制、图片产物走 Syncthing，三条链路互不兜底。本机坐标在 `<数据根>/config.toml`；ADR-0023 第 1～3 阶段已合入并在 Windows 生效，macOS 待跑 `peach init --from-existing --mount local=<落点>`。
- Windows 真实 ledger 为 `peach-data/database/ledger.db`，已应用到 `0024`（外键 ON DELETE 与索引），0 待处理。
- Mac ledger 已授权从共享副本显式拉取并恢复 `in-sync`；`sources` 已迁到内置盘，`archive`、`tools` 仍可指向外置盘。
- 服务运行期不连 Stash，媒体解析只有 `FilesystemBackend` 一条路径（ADR-0021）；只剩两个离线导入脚本按需连它，见 `docs/STASH.md`。
- 前端按 ADR-0022 以 Preact island 逐岛迁往 `frontend/`（Vite + TypeScript），产物 `web/dist/peach-ui.js` 进 Git、经 `/dist/{name}` 提供，`/quality-goals` 已迁；改前端需 Node 24+，见 `docs/FRONTEND.md`。
- 运行 Python 3.14，`requires-python`、本机 venv 和 GitHub Actions 的两个 job 同口径；Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。

## 已核验能力

一条一句，不带日期，只写别处没有的判据：README、`docs/HANDOFF.md`、`docs/REUSE.md`、
`docs/OPERATIONS.md` 和 ADR 已经写下的不在这里重复，出处用 `git log -S` 查。

- 本地浏览器支持 MP4/WebM/Ogg，AVI 等由 `TranscodeService` 缓存成 H.264/AAC MP4，永不改写原媒体；ffprobe 探测后可直接复制的流不重编码，其余在 Windows 走 CUDA/NVDEC。
- 远端 MP4 默认走标准 Range，显式开启的 HLS 使用关键帧对齐片段并在失败时回退 Range。
- 所有页面共用同一 SPA 与 JSON 契约，文本 gzip、资产 ETag；路由清单在 `README.md`。
- Logo、侧栏「首页」和沉浸模式关闭统一清除分类、搜索与 JAV 筛选，首页默认稳定随机、换批才换种子，再点当前排序回到随机。
- 桌面与 390×844 手机同在验收范围内，手机操作按钮保持 44 px 命中区。
- 同番号的分卷派生（A/B、1/2、CD/Disc/DVD/Part/Vol、「首卷裸名 + 后续卷 `-2`/`-3`」）折叠成一张卡并按时长排除完整版；首页、搜索、资料页网格与版次队列、角标计数共用同一套判定。
- 普通多女优卡片叠放前 3 个头像、只显示第一位姓名和真实总人数；JAV 小图是整页版式，混入的非番号作品统一为标题、身份、标签三行固定高度。
- JAV 详情持有 `asset.catalog_title`／`original_title` 与官方 Tag 身份，官方标记用常规字重，身份区收齐到同一内容起点。
- JAV 官方封面重探只在面积更大时替换，失败保留原图。
- 播放器按 YouTube 锁定源码对齐控件、状态、图标形变、设置面板动画与悬停提示，倍速五格到 3.0，窄屏按播放器宽度折叠留黑边，沉浸模式按 Shorts 版式，竖屏用居中 9:16 舞台，播放统计两页共用、按传输方式分口径。
- 图片灯箱在本地照片和关注在线图片间复用同一套 Swiper，在线图片只显示来源、合集序号和浏览器实际解析结果；照片标签按原图比例进入分页瀑布流。
- 统计与口味两页按登录态 Vercel Analytics／Speed Insights 的当前页面重做，排行与数据源共用父网格的引导线。
- 口味页顶部给出结论与可点入口：浏览与 Peach 两侧的共同信号、可探索标签、待补证据的下一步动作。
- 操作回执统一复用终态 Toast：等待态只在触发按钮内显示 Spinner，用 `aria-busy` 阻止重复请求而不禁用按钮。
- 实体链接可安装：`entity_link` 表、`q_entity` 的 `links` 契约、资料页 favicon 与管理页链接管理成套；死链区分「搬走了」和「没了」，`rediscover_entity_links.py` 从站点索引页上溯找新锚。
- 外链圆标与厂牌标识取站点自己声明的那份资产，宽扁字标不参加小圆标的竞选；`/logo` 的 `variant` 把厂牌标识分成 `icon` 与 `logo` 两档，只有真有两份时才分岔。
- 厂牌标识由契约位 `has_logo` 决定出不出图：没装标识的厂牌一个 `<img>` 都不发，改用首字母底板，不靠 404 摘。
- 关注检查分两阶段：列表阶段落 partial 行，详情补全按 provider 额度只补新行和未补齐行。
- `/api/related` 用 Tag IDF 加 MMR 排序并缓存；搜索使用 FTS5 trigram，短查询回退 LIKE 并覆盖规范名、别名和检索词，搜索历史在 reader 写入被拒时降级到页面内存。
- 复核页覆盖元数据、创作者标签、Logo、头像、身份、番号目录、FC2 证据和媒体失败；抓取与 AI 结果仍是候选，批准后才写真相字段，元数据候选保留 MetaTube 目录证据且不下载 URL。
- 外部来源 genre 只在 `peach.genre_taxonomy` 投影，日英来源词共用一套既有词表，非内容分类排除、未收录原文回传登记。
- 补抓按番号发行面分流来源，要求来源认得出所查番号、冷却按连败触发且会过期；无码发行站的片与粘连的版次标记也给得出徽章。
- reader 的 `/review` 通过严格 Peach CA HTTPS 读取 writer 的归一化 JSON 并原子缓存；决定按钮和所有关注写操作仍锁定。
- macOS Ledger 同步在共享根判为 `offline` 时先经 NetFS 挂载 `peach-sync` 再重判，挂载失败才保留离线结果，不弹阻塞认证框。
- 浏览历史增量采集使用 SQLite backup API 与 `browserexport`，也接受 Google Takeout ZIP；原始 URL 与标题只留本机私有目录，聚合候选不写 ledger。

## 批处理进度

账本与产物的现算数字由 Stop/SessionEnd hook 写进 `peach-data/state/job-status.md`（不进 Git，本机直接看）；手动重算跑 `python scripts/job_status.py`。
