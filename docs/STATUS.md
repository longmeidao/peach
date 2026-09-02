# Peach 当前状态

最后核验：2026-09-03

本文件按「现在是什么样」写，不按批次累积；已完成批次与事故过程由 Git 历史保存。

## 运行态

- Windows 是当前 ledger writer，启动入口为 `dist\Peach\Peach.exe`；代码、`peach-data`、worktree 和共享传输点都在同一个顶层目录下，外置盘只提供 `R:\media`。
- 托盘必须以普通权限启动：提升权限后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报为脱盘。
- Windows HTTP 为 `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名为 `peach-win.local`；线上服务版本 `0.7.13`、`ledger_sync=writer`。
- macOS 是 reader，代码与相邻的 `peach-data` 都在内置盘；`peach.local` 经 8900/8443 和 pf 提供 80/443，GET 正常、写入端点返回 409。
- 托盘与菜单栏层的改动不会随服务子进程一起生效，要手动退出菜单栏项后由 `.app` 或 `launchctl kickstart -k` 重启一次。
- 两端使用不同 mDNS 名和各自本机 CA，私钥与凭据不跨机同步；代码走 Git、账本走单写者复制、图片产物走 Syncthing，三条链路互不兜底。
- Windows 真实 ledger 为 `peach-data/database/ledger.db`，已应用到 `0023`，共 24 个迁移且 0 待处理。
- Mac ledger 已授权从共享副本显式拉取并恢复 `in-sync`，writer 仍是 Windows；`sources` 已迁到内置盘，`archive`、`tools` 仍可指向外置盘。
- 服务运行期不再连接 Stash，媒体解析只有 `FilesystemBackend` 一条路径（ADR-0021）；只剩两个离线导入脚本在需要时才连它，见 `docs/STASH.md`。
- 前端按 ADR-0022 以 Preact island 逐岛迁往 `frontend/`（Vite + TypeScript），产物 `web/dist/peach-ui.js` 进 Git、经 `/dist/{name}` 提供，`/quality-goals` 已迁；改前端需 Node 24+，见 `docs/FRONTEND.md`。
- 运行 Python 3.14，`requires-python`、本机 venv 和 GitHub Actions 的两个 job 同口径；Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。

## 已核验能力

一条一句，不带日期；出处用 `git log -S` 查。

- FastAPI 是唯一 Web server；Ledger 保存资产、规范身份、行为和复核决定，扁平 creator/studio/tag 字段只作兼容投影。
- CloudDrive 经挂载点进入；Stash 适配层已删除，历史断言以 `source='stash:*'` 留在账本里。
- 本地浏览器支持 MP4/WebM/Ogg，AVI 等由 `TranscodeService` 缓存成 H.264/AAC MP4，永不改写原媒体；ffprobe 探测后可直接复制的流不重编码，其余在 Windows 走 CUDA/NVDEC。
- 远端 MP4 默认走标准 Range，显式开启的 HLS 使用关键帧对齐片段并在失败时回退 Range。
- 首页、详情、实体资料、标签管理、照片、播放列表、统计、口味、复核、回收站、关注管理和关注观看共用同一 SPA 与 JSON 契约。
- Logo、侧栏「首页」和沉浸模式关闭统一清除分类、搜索与 JAV 筛选，首页默认稳定随机、换批才换种子，再次点击当前排序会回到随机。
- 桌面与 390×844 手机同在验收范围内，手机操作按钮保持 44 px 命中区。
- 管理区归并为「数据管理」一页，人工复核、回收站、高清版、垃圾文件、重复文件和空文件夹是同一件事的不同步骤，一次刷新只放一段骨架。
- 「垃圾文件」有独立 `/junk-files` 路由，按视频、图片、压缩包、音频、网址和其它分类；「不是垃圾」按 asset 存成可撤销的复核决定，不扩散成来源或域名白名单。
- 同番号的分卷派生（A/B、1/2、CD/Disc/DVD/Part/Vol，以及「首卷裸名 + 后续卷 `-2`/`-3`」）折叠成一张卡并按时长排除完整版，首页、搜索和资料页网格用的是同一套判定，版次队列与角标计数口径一致。
- 普通多女优卡片叠放前 3 个头像、只显示第一位姓名和真实总人数；JAV 小图是整页版式，混入的非番号作品统一为标题、身份、标签三行固定高度。
- JAV 详情持有 `asset.catalog_title`／`original_title` 与官方 Tag 身份，官方标记用常规字重，身份区收齐到同一内容起点。
- JAV 官方封面的规范化流程已写进项目技能：已有封面可按宽度进入重探队列，只有像素面积更大的新候选才原子替换，失败或更小的候选保留原图。
- 播放器按 YouTube 锁定源码对齐控件、状态与设置面板，沉浸模式按 Shorts 版式，竖屏用居中 9:16 舞台，播放统计含连接速度、网络活动与缓冲健康。
- 图片灯箱在女优／厂牌本地照片和关注在线图片间复用同一套 Swiper，在线图片只显示来源、合集序号和浏览器实际解析结果；照片标签直接按原图比例进入分页瀑布流。
- 统计与口味两页按登录态 Vercel Analytics／Speed Insights 的当前页面重做，排行与数据源共用父网格的引导线。
- 操作回执统一复用终态 Toast：等待态只在触发按钮内显示 Spinner，用 `aria-busy` 阻止重复请求而不禁用按钮。
- 在线追更的完整来源清单在 `README.md`，在线资产可就地播放；FANBOX 可选 Cookie 与 Gofile Premium token 只发给各自站点，SimpCity 仍被 DDoS-Guard 阻塞。
- 关注作者显示名与头像优先取经过固定主机校验的官方页面，归档站只作回退；Rule34.xxx 的来源 ref 大小写不敏感，F95 的 `Collection(s)` 后缀不进入作者名，五个来源可归到同一作者组。
- 实体链接可安装：`entity_link` 表、`q_entity` 的 `links` 契约、资料页 favicon 渲染与管理页链接管理成套；死链区分「搬走了」和「没了」，`rediscover_entity_links.py` 从站点索引页上溯找新锚。
- 外链圆标与厂牌标识取站点自己声明的那份资产，宽扁字标不参加小圆标的竞选；`/logo` 的 `variant` 把厂牌标识按位置分成 `icon` 与 `logo` 两档，只有真的有两份时才分岔。
- 运维脚本共用 `peach.scripting`（只读连接、`--db/--apply/--backup`，apply 强制备份）；AST 门槛拒绝写死数据根和无 `--apply` 的 DML 脚本。
- 关注检查分两阶段：列表阶段落 partial 行，详情补全按 provider 额度只补新行和未补齐行。
- 采集脚本的整页 HTML 缓存与限速集中在 `peach.page_cache.Site`，传输错误自己退让重试，HTTP 状态码不重试。
- `/api/related` 用 Tag IDF 加 MMR 排序（生产实测 0.48 秒），人脸检出使用 YuNet；搜索使用 FTS5 trigram，短查询回退 LIKE 并覆盖规范名、别名和检索词，搜索历史在 reader 写入被拒时降级到页面内存。
- 回收站的单项删除和清空共用 `purge_assets()`：先处理媒体文件再提交 ledger，删不掉的文件保留可见状态并回报。
- 复核页覆盖元数据、创作者标签、Logo、头像、身份、番号目录、FC2 证据和媒体失败；抓取与 AI 结果仍是候选，批准后才写真相字段。
- 元数据候选保留 MetaTube 模型里的目录证据，不映射真相字段、不下载 URL。
- reader 的 `/review` 通过严格 Peach CA HTTPS 读取 writer 的归一化 JSON 并原子缓存；决定按钮和所有关注写操作仍锁定。
- macOS Ledger 同步在共享根判为 `offline` 时先经 NetFS 尝试挂载 `peach-sync` 再重新判定，挂载失败才保留离线结果，且不弹出阻塞认证框。
- Windows 托盘与 macOS 菜单栏均提供「同步开发进度」；Windows 先快进并跑正式测试，涉及打包输入时先构建校验新 EXE，再退出旧托盘完成可回滚替换。
- 浏览历史增量采集使用 SQLite backup API 与固定版本 `browserexport==0.4.4`，也接受 Google Takeout ZIP；原始 URL 与标题只留本机私有目录，聚合候选不写 ledger。

## 下一批工作

1. 查清 2026-09-02 那 191 行 `javinizer:%:tag` 的去向（javbus −172、r18dev −19，无可归因的写入者）。先重跑「读计数 → sqlite_backup → 再读计数」确认是否可复现。
2. 在 `/review` 处理 5 个被跳过的标题偏移值：`MY-101`、`MY-102`、`MY-103`、`MY-104`、`SAR-103`。
3. 另行授权后执行 `scripts/flatten_release_dirs.py --apply --backup <备份路径>`：296 个目录操作（collapse 167、rename 129）落在 CloudDrive 挂载上，影响账本路径 3374 条。执行前重跑 dry-run，191 条未挂载的会随挂载状态变化。
4. 另行授权后先备份 ledger，修正 4 组已核实姓名：恢复 `星谷瞳`、`福山美佳`、`平沢すず` 的规范名；从 `かわいゆい` 移除错误的 `河合ゆい` 别名与 r18 外部引用，清退错误头像及 provenance 后重新生成候选；同步 actor tag 与检索投影。
5. 另行授权后先备份 ledger，再把 `follow_item` 181、184、185 从 `seen` 恢复为 `new`，复核状态计数、完整性与新哈希。
6. 继续按复用审计依次替换 PID 锁和 Rule34Video 媒体页；每项固定版本/revision、首个消费者和隔离测试同批落地。
7. 分类剩余 44 个无预览变体：确无图片还是解析遗漏。
8. 另行确认后在生产关注页检查 LazyProcrastinator FANBOX，把已验证的 6 图、正文与 Gofile `OS2Qz9` 资源页写入关注候选；Gofile token 未配置且账户不是 Premium，21 个视频仍未取得。
9. 在 `/review` 人工处理 JAV 日文系列名、官方标签及现有创作者标签、FC2、Javinizer、Logo、头像和媒体失败候选；未经批准不写真相字段。
10. 将 Windows writer 的最新副本同步到共享传输点，再让 Mac reader 拉取；同步前后核对迁移版本、计数、完整性与 writer 身份。
11. 在 Mac Finder 以 `smb://peach-win.local/peach-sync` 连接一次并保存钥匙串记录，再重启菜单栏进程，核对自动挂载、reader 锁定、HTTPS 与 mDNS。
12. 在实现下载器前先确定媒体凭据、流量与磁盘预算。
13. Windows writer 运行 PikPak 夜跑前重算 probe/抽帧队列，并按 `peach-batch-jobs` 设置流量与系统盘闸门。
14. 补做 HLS 首帧、seek、自适应码率与双端视觉验收。
15. 外置盘挂载后先只读盘点 `R:\Media\<名字>\P\...` 图片规模；扫描写真 ledger，需另行授权。
16. 重做品味分析页的视觉再决定是否合入：`agent/codex/taste-analysis`（cd3effe）功能可用但版式不过关，重做时以该分支 `taste_history.py` 的分析逻辑为底。
17. 决定 `attic/instances/20260828-taste-preview` 的去留：含 122 MB 账本副本（按真相源快照对待，删除需另行确认）与 153 MB `sources`；28 个预览日志可随时清。
18. 另行授权后运行 `scripts/normalize_link_hosts.py --database <ledger> --apply --backup <落点>`，把 296 条 twitter 写法收成 x.com（290 改写、6 删除），随后重启托盘并在真实浏览器验收 `/link-mark` 的清晰度与边缘。
19. 用户复核 `directory-links-<日期>.csv` 后用 `install_entity_links.py` 装入社媒链接；`conflict` 且账本旧号「疑似失效」的行由用户决定换号，随后可对账本现有全部 X 链接跑一遍同样的验活。
20. 用户复核 `studio-names-<日期>.csv` 的 26 条厂牌改名后另行授权；3 条不一致按「一个账本名混了两家」处理，5 条 404 未取得，搜索兜底要先有一个能用的搜索出口。
21. 9 个字标厂牌的官网已查出 8 条（`studio-sites-<日期>.csv`），用户复核后授权 `install_entity_links.py` 装入，再重跑 `scripts/harvest_studio_icons.py`；SOD Create 与 FC2-PPV 各剩一条要用户裁决，判据见 `docs/SOURCING.md`。复核时重点看 `content_aspect` 接近上限的行。
22. 把 javdatabase 的 idol 页接进社媒／官网候选：183 页缓存里 139 页带 X 链接、138 页带另一个官方站，由番号定位、不需要离线比名。实现复用 `peach.social_links` 的判据与 `install_entity_links.py` 的 `FIELDS`，排掉四个整站广告主机。

## 批处理进度

账本与产物的现算数字由 Stop/SessionEnd hook 写进 `peach-data/state/job-status.md`（不进 Git，本机直接看）；手动重算跑 `python scripts/job_status.py`。
