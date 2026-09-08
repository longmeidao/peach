# Peach 产品待办

更新时间：2026-09-08。这里只记录尚未完成或只完成一部分的需求；运行数字以 `peach-data/state/job-status.md` 的自动区块为准。

## BoardUI 正式前端迁移

用户已授权正式前端全量迁移，保留设置中的「使用旧版 UI」，应用后刷新生效。以现有 Preact/Vite 架构实施；审查所有页面和原有设计意图，覆盖管理、视频详情、设置、响应式布局及关联选项。布尔开关对应 Board Switch，互斥选择对应 Segmented Control；其余控件逐项取证与映射。玻璃默认折射，「增加对比度」使用实色背景。数值配置支持合法范围内自定义，可关闭功能用 Switch，开启才展示数字输入。

正式工作树已实现共享视觉层、管理与详情卡片、设置布局、数值输入和旧版隔离；18984 使用该工作树的完整构建快照进行只读验收。生产尚未切换。Remix Icon 候选审查在预览 `/icon-review.html`，现有已选图标保留至用户筛选。迁移不包含版本号或其他分支发布工作。

统计与口味已接入 Stat Cards、可展开排名、雷达、媒体库与网盘环形卡；浏览历史支持时间范围、真实访问热图和网站到创作者线索的流向。侧栏使用同一导航的 60/260px 宽窄态，手机从左侧滑入。设置滚动渐隐、手机输入字号、焦点环留白及登录保持时长已接入。Pro 组件使用公开行为的独立适配，范围见 [Board 适配](BOARD_UI.md)。

侧栏底部固定设置和明暗开关，顶部独立按钮控制展开；媒体库图标负责打开选择面板，首页入口使用 Peach logo。路径可命名分组并选择图标，网盘默认图标由本机提供；库选择限定作品列表与筛选项。统计、口味和维护任务保持全局。关注提供默认视图与表格视图，共享作者分组、排序、多选和批量删除；默认视图可收起作者，表格视图表头可排序，最近观看标题可跳转视频。详情优先响应 Esc，手机排序栏可横向滚动。预览不保存真实配置。

## 已有骨架、尚未完成（6 项）

- Windows 独立测试包的局域网访问与 mDNS：按用户要求先恢复本机访问，后续加入此功能；测试域名与开发环境隔离。首启页的局域网选项与当前测试包限制不一致，也在此项闭环。

本轮实施顺序（评审来源：[外部复评](https://chatgpt.com/c/6a9ad810-6148-83e9-95dd-6b58ef28e7ec)，按当前源码核对；候选实现与生产验收分开）：

- 运行与一致性：HTTP 只跳转 HTTPS；业务与调度由单一应用拥有；成功提交后失效缓存；缓存有界；可更新图片可复验；列表参数有上下界。
- 数据与查询：标签、实体筛选从关系索引驱动；随机排序有唯一次序；重复索引与外键启用先做副本验证；补固定规模基准。
- 安装与诊断：下面第 12、13、21、22、23 项按依赖实施，覆盖最小源码安装、wheel 资源、仓库外启动、就绪检查。独立桌面制品及操作系统 VM 验收仍按第 15、21 项推进。
- 抓取可复现性：按 [ADR-0024](adr/0024-mark-manifest-not-bundled-bytes.md) 落地来源配置与清单。
  `/scraping` 已有定点高清封面、FC2 Cookie 粘贴／文件导入和封面来源网络配置；剩余来源还需接入
  统一配置、会话有效性验证与完整批量 GUI。清单导入导出、标准模式与 Javinizer-Go 工具配置待实施。
  Instagram 成熟解析器须有独立用户会话 POC；Windows/macOS 干净安装和二次运行缓存命中是交付条件。
- 后续结构：显式 API 模型、前端构建与高频页面迁移、候选分页、任务持久化按垂直功能实施；不为 AppContext 或文件尺寸单独做全仓搬迁。
  当前已实现运行缓存、关系筛选、wheel 资源、仓库外冒烟和分级健康检查；Windows 基础依赖安装通过。真实库只读对照七轮中位数：标签 195.5→25.5 ms、创作者 148.8→45.6 ms、女优 162.7→15.7 ms、厂牌 162.0→19.6 ms，返回 ID 与总数一致；这不是浏览器端延迟。
- Linux 首版候选为 headless、预挂载媒体与独立 wheel。外部容器用了替身依赖，其结果不构成锁定依赖和 Linux 的正式支持证据，优先级低于 Windows/macOS。

外部评审提到的空口令拒绝启动、secret 文件读取、count=0 已有实现；不重复登记。shuffle_key 改变随机浏览的序列语义，先测关系筛选收益再决定。真实 ledger 迁移、双机复制取消和系统级安装另有明确授权边界。

1. **寻找更好版本**：已经能逐条标记「高清 / 无水印 / 完整版」等目标；后续仍需相似内容匹配、候选去重、来源发现和人工替换确认。
2. **现代自适应播放**：Video.js、Range、统计面板和面向 115/PikPak 原生 MP4 的按需 HLS 清单已经上线；自适应码率、多路清单、快速首帧和来源层大块预取优化仍未完成。
3. **在线追更**：`src/peach/follow_providers.py` 登记的十一个来源（FANBOX、SubscribeStar、Patreon、Kemono、Pawchive、Coomer、Rule34Video、Rule34.xxx、Rule34 Paheal、F95zone、SimpCity）、WIP/alt/跨站重复判定、`follow_source`/`follow_item`、看的 `/follow` 与管的 `/follow-manage` 两个页面已上线，writer 用 APScheduler 按设置自动轮询，在线资产可就地播放。仍缺的是下载落地（凭据、流量与磁盘预算未定，见下面「待执行的操作」第 12 条）；SimpCity 已能凭用户自己的登录 cookie 发现更新与按名字搜线程；帖子里的网盘链接显示为按钮，图片不论挂在站方图床还是第三方图站都经代理就地查看（不带凭据、拒绝内网地址）。仍缺的是多图楼层的图片轮播（连接器只记录图片地址列表，未投影成 `media_items`）。
4. **首尾帧出处与不完整候选**：已有受限 FFmpeg 首尾抽帧、Windows 内置 OCR、证据帧缓存、来源/Full version 候选和 `/review`；仍需决定全库批次范围，并把用户批准后的不完整版判断接到更好版本目标。
5. **厂牌 Logo 补齐与持续校验**：14 个已确认社交 handle 已有内容缓存、provenance、精确/感知哈希、质量与重复门槛及健康报告；仍有 72 个厂牌没有可信 handle，必须继续从官网/公开来源取证，不能猜账号。
6. **口味证据持续刷新**：ledger 已实时记录搜索、播放、高潮、喜欢/理由、不合口味和稍后看；浏览器历史现可用 SQLite 一致性副本增量进入私有源库，并生成不含 URL/标题的 creator/tag candidate 与聚合报告。旧 2026-08-13 原始包已确认不在 Windows 外置盘；仍需在 Mac 开启 iCloud Safari、完成首次导入，并把两端每周刷新装成系统计划任务。AI 结论不得直接改真相字段。

## 尚未实现（24 项）

1. AI Provider 的真实调用、能力协商、Credential Manager 凭据和候选审核 UI。
2. 剩余单一创作者风格板复核、无标签内容补标。
3. 缺时长资源补 probe 后再生成九宫格。
4. PikPak 计费抽样与下载边缘质量核验。
5. 复用 CommunityScrapers 一类公开刮削规则做元数据导入：只当只读规则语料，不重新引入 Stash 运行时依赖（ADR-0021）。
6. 把常跑批处理折进 `peach` CLI：`probe`、`sheets`、`scrape_codes`、`fetch_jav_covers`、`taste_history`、`traffic_watch` 现在各是一个脚本入口，参数、限流与健康报告口径不统一。
7. 开源通用化的发布准备（ADR-0023 第 4 阶段）：清扫 `docs/` 与 `.claude/skills/` 里的局域网地址、主机名、账号名、备份文件名与个人目录，把只对一台机器成立的运行态移出仓库，并把 `tests/test_repo_hygiene.py` 的个人字面量门槛从 `src/peach/` 扩到文档与技能。许可证、贡献与安全说明、issue/PR 模板在仓库里；设置层、来源挂载点 ID 与可整体关闭的复制链路在 Windows 生效，macOS 待跑 `peach init --from-existing --mount local=<落点>`。
   - 公开分发：待项目相对稳定，安装、升级、数据迁移及跨平台回归稳定后，同批推进 PyPI 包发布和 WinGet 登记；现阶段仅记录计划，不上传或登记。发布前确认发行名，调整禁止上传标记，完善自动构建、版本发布与两端安装验收。
   - 名称候选：首选 `peach-media`，备选 `peach-library`、`peach-shelf`、`longmeidao-peach`；WinGet 应用 ID 建议 `longmeidao.Peach`。名称尚未定案或注册，发布时复核可用性；产品显示名继续使用 Peach。
8. 女优高清头像的写入侧：`scripts/audit_performer_portraits.py` 已能出候选与实测证据，仍缺按复核结果复制头像文件那一步，以及实体合并后孤立头像的 relink（如 `8022 <- 8168`：只有旧 ID 的 provenance 名唯一命中当前实体、当前目标又不存在时才算候选，不覆盖、不删除旧文件）。
9. 文件名与网盘目录整理的落地：`scripts/clean_names.py` 与目录计划只出 dry-run CSV。真正改名要独立维护窗口——停同类任务、确认本机是 writer、SQLite backup、逐条同目录 rename 并同步账本 path/name、失败时文件名回滚，最后跑完整性、外键与路径存在性检查；不跨盘移动，也不按文件夹名猜创作者。
10. 来源与默认值通用化（ADR-0023 第 5 阶段候选）：`peach init` 的问答已按本机路径只声明 `local`，非交互路径写出的 `DEFAULT_LOCATION_ROOTS`（`R:\media`、`B:/`、`A:/`）仍是维护者的示例盘符。剩两件事：来源用「本地 / 远端挂载」类型字段代替代码里按 `local`/`115`/`pikpak` 名字点名（`web_resource_sync.py` 的 SQL、`media.py` 的 HLS 规则）；复制链路支持 win↔win、mac↔mac 与任意一台当写者，目前只验证过 Windows 写者 + macOS 读者。
11. 非 editable 安装的跨平台验收：wheel 资源与 Windows 基础依赖、仓库外 CLI 冒烟已就绪，仍需取得 macOS、Python 3.12 消费任务结果。
12. 健康检查生产验收：`db` 区分 missing、empty、available、unavailable，`?ready=1` 检查 schema 校验和；待部署后用项目 CA 验证 HTTPS 与损坏／未初始化状态。
13. 界面国际化：界面目前只有中文，先补英文。
14. 制品与更新渠道：Windows 独立测试包、首次引导与本机配置表单已实现，Release 消费任务只下载制品验收。剩余为 macOS 独立包、代码签名、独立测试包的自动更新、局域网配对和更完整的配置管理；本机打包托盘已按构建身份自行重建，版本号与标签都由 `release_tag.py` 在发布点独家发出，每个版本号对应一份制品并在 `CHANGELOG.md` 有一节。测试包更新采用退出程序后完整解压新版，数据目录保持独立。本条关闭是 ADR-0012「1.0 门槛」第 8 项。
15. 「第一个小时」教程与故障排查文档：init → 声明来源根 → scan → 打开页面 → 手机信任 CA → 托盘/菜单栏自启动，每一步写清失败表现与对应的排查动作；截图用一套小的 SFW 演示数据集生成，不取自真实馆藏。
16. 项目网站：一页说明是什么、截图、安装入口与文档链接。
17. 口味导入引导：`/taste` 上传（Takeout ZIP、browserexport 兼容文件）与 `scripts/taste_history.py` 直读本机浏览器库两条路都能用，但没有面向陌生人的文档。需要一页「各浏览器怎么导出、多台设备怎么各自刷新」教程，把脚本折进 `peach` CLI（见第 7 条），并写明定时刷新的安装方式。
    首次设置提供可选的浏览器历史导入指南，口味页可随时展开；读取与导入由用户触发。CLI 整合、各浏览器详细导出教程和定时刷新仍待实施。
    数据管理的网盘同步仅显示并扫描已配置网盘；空文件夹清理支持本地。重复文件的网盘保留操作同时要求来源已配置、组内存在对应文件。
18. README 瘦身：把「依赖维护」「开发」两节移到 `CONTRIBUTING.md`，「目录」并入 `docs/ARCHITECTURE.md`，「主要页面」「关注与候选」压成一张表；README 只留是什么、边界、前置条件、安装、下载、文档入口与许可证。中英两份同步。
19. 局域网访问：HTTP 导航与 HTTPS 单一业务入口的候选代码已就绪，待生产部署验证。配对仍需一次性配对码或 HTTPS 地址二维码，减少设备首次访问时手输口令；现有口令生成、取用与非回环无口令拒绝启动不重复实现。
20. 全新安装的自动门槛：现有 `Test` 装的是 `-e ".[build,vision,maintenance-115,naming]"` 全套可选依赖、开着 pip 缓存、只跑单元测试，证明不了「陌生用户按 README 装完能用」。补三条互相独立的冒烟：① minimal source——全新 venv、`--no-cache-dir` 只装默认依赖、`peach init`（连跑两次验幂等）、`migrate status`、**离开仓库根目录**再 `peach serve`，请求 `/healthz`、`/`、`/api/items`，覆盖 3.12／3.14 × Windows／macOS 以及无 FFmpeg／OpenSSL／Node 的机器；② wheel——`python -m build` 后在不 checkout 源码的 job 里装 `dist/*.whl` 走同一条链路，它通过才能去掉 README 的 `-e` 硬要求（依赖第 12 条）；③ artifact-only——只下载刚构建的制品、不 checkout 源码地跑起来（依赖第 15 条）。消费方一律不许 checkout：工作目录会替漏文件的制品兜底，那是假通过。失败场景也要覆盖：数据根不可写、端口被占、账本损坏、未配置媒体目录、无 FFmpeg、非回环监听但无口令、两个 writer 同时起。
21. `peach doctor` 与分级 `/healthz`：`doctor`（另带 `--json`）逐项报版本、数据根可写性、配置文件合法性、数据库能否打开、schema 版本与待执行迁移、FFmpeg／ffprobe／OpenSSL 路径、挂载点可达性、端口占用、是否处在「局域网暴露但无口令」状态、后台任务最近一次失败；输出脱敏，不带口令、cookie、站点凭据和完整媒体路径。`/healthz` 相应从布尔改成分项状态（`database`／`schema`／`configured`／`ffmpeg`／`media_mounts`／`security`），与第 13 条一起做。
22. 性能基准：用 SFW 合成数据生成 1k／10k／100k／500k 四档库，nightly 测冷启动到 `/healthz`、目录页与详情页 p95、两字以上搜索 p95、本地 SSD 与网盘挂载的 Range 首字节、空闲 RSS、后台扫描时前台退化倍数、备份期间读请求不失败。门槛用「相对上一次基线下降超过 20%」，不给绝对毫秒数——不同机器不可比。数据集与第 16 条的演示数据集共用。
23. CI 的 Windows job 太慢，一次 push 的墙钟由它决定。同一批 2786 个用例在 `macos-latest`（arm64）上 57 秒，在 `windows-latest` 上 1475 秒，本机 Windows 是 324 秒——runner 比开发机还慢 4.6 倍。按时间戳差算，250 个用例（9%）吃掉 1119 秒，每个稳定在 4.5 秒上下，形状像每建一个临时文件被 Defender 扫一遍。两条路各自独立：一是在 Windows job 里对 runner 的临时目录加 `Add-MpPreference -ExclusionPath`，先量一轮确认是不是 Defender；二是把 `scripts/test_runner.py` 的域拆成矩阵分片并行跑，代价是每个分片重付一次装依赖的 37 秒。不要为了缩短墙钟把 Windows job 从矩阵里去掉：它是生产平台，也是唯一能拦住 Windows 独有回归的地方。
24. 借鉴 vercel.com/<team>/~/deployments 的令牌式筛选与排序。那一行不是一排互斥药丸，而是「Add Filter + 若干条已添加的维度令牌（Author／Environment／Status）」，每个令牌自带下拉，维度可叠加、可逐个摘掉，另有独立的日期区间与状态汇总（`6/7`）。2026-09-05 实测它的三态：未生效 `1px dashed rgba(0,0,0,.21)` 透明底，悬停／聚焦换成 `#FFFFFF` 实底加 `1px solid rgba(0,0,0,.08)`，下拉展开时 `gray-200` 底配实线——虚线读作「建议但没应用」，实心读作「已生效」。
    首页大概率不合适：`.tagbar` 那一排是单选（`全部`／`没看过`／`稍后看` 恒有一个生效），把没选中的三个画成虚线会读成「三个待处理的筛选」；而且这套「填亮 = 生效」要成立，页面底色得比控件低一档——Vercel 的仪表盘底是 `#FAFAFA`，Peach 的 `--ground` 是纯白，没有可填的更亮档。真正对得上的是多维叠加的场景：`/follow-manage` 的来源／状态／WIP 组合筛选，和 `/review` 的候选筛选。先在这两处试，别动首页。

合计：**30 项开放需求**，其中 6 项已有骨架，24 项尚未实现。已完成的需求不在这里留痕，去 Git 历史查。

## 待执行的操作（38 项）

需要另行授权、外部条件或人工判断才能做的具体操作与复核批次，比上面的需求细一层；做完就删，不在这里留痕。待办只放这一处：`docs/STATUS.md` 每次会话开头都要读，队列不该常驻在那种入口文件里。

1. 查清 2026-09-02 那 191 行 `javinizer:%:tag` 的去向（javbus −172、r18dev −19，无可归因的写入者）。先重跑「读计数 → sqlite_backup → 再读计数」看是否可复现。
2. 在 `/review` 处理 5 个被跳过的标题偏移值：`MY-101`～`MY-104`、`SAR-103`。
3. 另行授权后跑 `scripts/flatten_release_dirs.py --apply --backup <落点>`：296 个目录操作（collapse 167、rename 129）落在 CloudDrive 挂载上，影响账本路径 3374 条。执行前重跑 dry-run，191 条未挂载的随挂载状态变化。
4. 另行授权后先备份 ledger，修正 4 组已核实姓名：恢复 `星谷瞳`、`福山美佳`、`平沢すず` 的规范名；`かわいゆい` 移除错误的 `河合ゆい` 别名与 r18 外部引用，清退错误头像及 provenance 后重新生成候选；同步 actor tag 与检索投影。
5. 另行授权后先备份 ledger，把 `follow_item` 181、184、185 从 `seen` 恢复为 `new`，复核状态计数、完整性与新哈希。
6. 按复用审计依次替换 PID 锁和 Rule34Video 媒体页；每项固定版本/revision、首个消费者和隔离测试同批落地。
7. 分类剩余 44 个无预览变体：确无图片还是解析遗漏。
8. 另行确认后在生产关注页检查 LazyProcrastinator FANBOX，把已验证的 6 图、正文与 Gofile `OS2Qz9` 资源页写入关注候选；Gofile token 未配置且账户不是 Premium，21 个视频仍未取得。
9. 在 `/review` 人工处理 JAV 日文系列名、现有创作者标签、FC2、Javinizer、Logo、头像和媒体失败候选；未经批准不写真相字段。
10. 将 Windows writer 的最新副本同步到共享传输点，再让 Mac reader 拉取；同步前后核对迁移版本、计数、完整性与 writer 身份。
11. 在 Mac Finder 以 `smb://peach-writer.local/peach-sync` 连接一次并保存钥匙串记录，再重启菜单栏进程，核对自动挂载、reader 锁定、HTTPS 与 mDNS。
12. 在实现下载器前先确定媒体凭据、流量与磁盘预算。
13. Windows writer 运行 PikPak 夜跑前重算 probe/抽帧队列，并按 `peach-batch-jobs` 设置流量与系统盘闸门。
14. 补做 HLS 首帧、seek、自适应码率与双端视觉验收。
15. 外置盘挂载后先只读盘点 `R:\Media\<名字>\P\...` 图片规模；扫描写真 ledger，需另行授权。
16. 重做品味分析页的视觉再决定是否合入：`agent/codex/taste-analysis`（cd3effe）功能可用但版式不过关，以该分支 `taste_history.py` 的分析逻辑为底。
17. 决定 `attic/instances/20260828-taste-preview` 的去留：含 122 MB 账本副本（按真相源快照对待，删除需另行确认）与 153 MB `sources`；28 个预览日志可随时清。
18. 另行授权后跑 `scripts/normalize_link_hosts.py --apply --backup <落点>`，把 296 条 twitter 写法收成 x.com（290 改写、6 删除），随后重启托盘并在真实浏览器验收 `/link-mark` 的清晰度与边缘。
19. 用户复核 `directory-links-<日期>.csv` 后用 `install_entity_links.py` 装入社媒链接；`conflict` 且账本旧号「疑似失效」的行由用户决定换号，随后可对账本现有全部 X 链接跑同样的验活。
20. 用户复核 `studio-names-<日期>.csv` 的 26 条厂牌改名后另行授权；3 条不一致按「一个账本名混了两家」处理，5 条 404 未取得，搜索兜底要先有一个能用的搜索出口。
21. 厂牌标识规则：logo 文件一律不透明方图（位图 `images.bake_square`、矢量 `images.bake_square_vector`），产物再过 `images.refit_plate` 摆到圆形图位里看得全的位置，页面三处一律 cover。另行授权后跑一次 `normalize_studio_logos.py --apply --backup <落点>`，2026-09-08 dry-run 报 52 张待改：46 张重新摆位（自带大留白的裁掉、顶到边的补到外接圆）、4 张 SVG 包方底（DarkRoomVR、TeamSkeetXReislin、TeenFidelity、VirtualTaboo，前两张白字标配深底）、HEYZO 从备份原图重烤改配深底、pikpak 重补方。
22. 把 javdatabase 的 idol 页接进社媒／官网候选：183 页缓存里 139 页带 X 链接、138 页带另一个官方站，由番号定位、不必离线比名。复用 `peach.social_links` 的判据与 `install_entity_links.py` 的 `FIELDS`，排掉四个整站广告主机。
23. 人工判 `domain-code-review.csv` 里 `WX17` 那 269 条水印存疑行，脚本不给提案。
24. 给账本厂牌补日文别名。MGStage 名录 351 家只对上 29 家，卡点是账本 118 个厂牌只有 27 条别名、几乎没有日文名——补完别名再对一次，覆盖面会一次性抬上去。
25. 其他厂牌官网的厂标与演员资料广度扫描（SOD、FALENO、Attackers、S1、Moodyz 等），用户 2026-09-04 定为「先做 b 看效果」之后的下一轮。
26. 用 javtiful 的 `/ja/actress/<slug>` 补演员的罗马字↔日文配对：315 页约 7560 位，切语言前缀就出日文名。厂牌名不随语言切换，这条只服务演员别名。
27. 37 位演员在 javdb 上只有日文名（`同形`），另有 5 位未取得，中文名要换来源：javtiful 的 `/ja/actress/<slug>`（第 26 条）或 javdatabase 的 idol 页。复核产物 `peach-data/review/javdb-cn-names-20260904.csv` 逐行带 verdict 和证据，可直接筛。
28. macOS 标识 `io.github.longmeidao.peach.*` 在 Mac 上生效：代码已在 master（`src/peach/appid.py` 是唯一来源，`install_macos_agent.py` 与 `setup_macos_port80.sh` 会自己清掉遗留标签），命令与四项核对见 `docs/OPERATIONS.md`「桌面入口与发布」。放进第 30 条的维护窗口一起做；两台机器都跑过之后删掉 `peach.appid` 里的遗留标签表和用到它的分支。这是换生产入口，执行前要在同一轮拿到用户确认。
29. `peach-data/review/composite-names-20260904.csv` 里还剩 28 条 creator 规范名带括号，括号里是读音或罗马音（`Egami(えがみ)`、`永地(eichi)`、`猫屋(NEKOYA)`），用户定了不拆——它们不像艺名那样各自独立，是同一个名字的注音。同一份 CSV 里 575 条 tag 是角色的作品出处消歧，10 条 series 括号里是厂牌或载体消歧（拆了会把三个 `AV DEBUT` 撞成一个），都不要动。剩下真正待判的只有 performer 规范名 `Mana(23)` 一条：数字是去重后缀还是名字的一部分要看源站。
30. Mac 追上 master 的一组操作，按顺序做完再重启菜单栏——做完之前不要重启：master 上的 `peach serve --host 0.0.0.0` 没有口令会拒绝启动，reader 会直接消失。① `git pull` 到 master；② `pip uninstall -y peach-app && pip install -e ".[macos]"`；③ 先把 Windows 的 `peach-data/secrets/auth-token` 复制到 Mac 数据根的同一路径——reader 取 writer 复核结果发的是自己的口令，两边必须是同一份，而 `--from-existing` 找不到文件会自己生成一份不同的；④ `peach init --from-existing --mount local=<落点>`；⑤ 重启菜单栏，核对 `/healthz`、`/review` 能读到 writer，手机与 Mac 浏览器各登录一次。第 28 条的标签改名可以放进同一个维护窗口。
31. 事务所改名复核：Wish/GIRFY、LiStarPRO/GRANZPRO 缺可核验官网；LIGHT 与 ELTRA/EST 存在分流，不能整体合并；Prime Agency/GG 有歧义，Cruse Group 官网证书链未取得。原始请求与逐条结论位于顶层 `attic/reviews/20260906-portrait-agency/agency-review.csv`。只对取得证据且获用户批准的记录执行合并。
    2026-09-06 核对 wish-promotion.jp 已是其他内容站，不能作为现官网。15 条现官网链接使用共用 Chrome UA 重查，13 条返回 200；Cruse Group 证书链与 Prime Agency TLS 连接仍未取得。
32. `install_entity_links.py` 的可达性门槛按「非 200 就跳过」执行，而同文件的 `is_gone()` 明确写着 403／5xx／连接错误不能当「页面没了」。首批 703 条里 137 条因此没装，其中 31 条 twitter.com、23 条 t-powers.co.jp。把跳过分成「确证没了」和「这次没取到」两档：后者留进待复查队列，配合 `rediscover_entity_links.py` 对 t-powers／nax-pro／mines-pro 这些已经搬家的域名上溯找新锚，再装一次。
33. 托盘自重建被测试记录门槛卡住：2026-09-05 22:54 托盘为 0.8.5 起的那次「同步开发进度」全量 3181 个用例全绿，`scripts/test_runner.py` 却因验证前后主检出的内容或依赖快照不一致判本次记录无效、退出码 1，托盘按测试失败处理，没有打包也没有换 EXE，并且同一 HEAD 不再重试；同一时段两次 `auto` 记录也是空的 `validated`。第二次（23:14 起，HEAD 5a4b37f8）跑到一半，协调者于 23:17:42 把 0.8.6 合进了同一个主检出，全量因此 6 个用例失败、记录再次无效；失败用例名未取得，第三次尝试一开始就把日志覆盖了。机制已确认：托盘在主检出跑全量，`integrate` 的 `integration.lock` 与全量的 `full-suite.lock` 互不排斥，任何一次集成都会改掉正在验证的树。要做三件事：集成前等主检出里正在跑的全量结束（或让两把锁互斥），并把「记录无效」和「用例失败」在退出码或输出上分开，让托盘对前者重试而不是放弃；托盘的日志只写 stderr，没有落盘，22:43 那次托盘连同两个服务一起消失的原因也因此未取得，给托盘补一份 `logs/tray.log`。现场：线上服务 0.8.5 正常，托盘 EXE 仍是 21:08 打的 0.8.1，`pyproject.toml` 与 `windows_update.py` 的改动没进 EXE。
34. 封面来源头像逐条复核：37 张仍来自 `cover-fallback`，完整初始清单位于 `attic/reviews/20260906-portrait-agency/remaining-cover-avatars.csv`。41 张被封面覆盖的 Gfriends 人像已从备份恢复，包括日向真凛，恢复记录见同目录 `cover-restore-result.json`。采集器将封面保留为未验证候选，安装函数拒绝把封面写成人物头像。
35. 首要原则审查（2026-09-07，George Pickett 的 prompt，覆盖整个 `peach-app`）的剩余清理项。零风险的删除已随分支 `agent/claude/provider-registry-review` 落地，完整报告与判断依据在顶层 `attic/reviews/20260907-first-principles/review.md`；下面每条独立，可单独派工作树：
    - follow：`connector_headers` 形参、`blocked_reason` 基类钩子、`FollowCandidate.version` 输入字段只有测试在用；`KemonoConnector.HOSTS`／`SubscribeStarConnector.HOSTS` 与登记表 `url_hosts` 是同一份主机表的第二份；Rule34Video 自带的探测循环可并入 `enrich()`；425／429 进 `_send` 的可重试集后两段手写重试可删。
    - follow 弱假设：ETag／304 机制 2026-09-08 只读核查：45 条来源 `etag` 全空、`last_status` 从未出现 `not_modified`，只有 f95zone 的 7 条存下 `last_modified`——条件头有站点在回、304 没有站点回过，机制保留，不再列为待删。六处「读时修旧行」兼容层（`archive_file_url`、`_legacy_history_end`、`_f95_has_resource`、`split_posts`、`author_display_text` 修正、`f95_attachment_media_items`）换成一次带备份的迁移，需 ledger 写授权。
    - Web：`serve --no-ledger-sync`／`--ledger-sync-seconds` 处理代码已删、参数还在，托盘五处与 `docs/OPERATIONS.md` 仍在传——必须和托盘重建同批做，旧 EXE 拉起新代码的窗口期会被 argparse 拒收；四个域 Protocol（`LinkContract`、`PlaylistContract`、`ResourceSyncContract`、`ReviewContract`）换成直接用 `WebContract`，`ContractConformanceTests` 随之删；`same_origin`、来源在线判定、回环判定各有三份，各留一份；`_read_answers`／`_validate` 里「只发 media_dirs」的旧表单分支生产不可达，只靠测试活着；access `legacy` 模式的 `tok` cookie 只被接受不被升级，定截止日删接受分支；`legacy_snapshot_roots` 的运行期前缀重映射已随 2026-09-08 的 `snapshot_path` 切换删除。
    - 桌面：换 EXE 两条路径（`replace_windows_tray.py` + `windows_update` 内联备份，与 `windows_restart.swap_tray_binary`）留校验更强的后者；`test_runner.py` 把「记录无效」与「用例失败」分成不同退出码（第 33 条的根因）；`sync.py` 的 `PUSH_INTERVAL_SECONDS`／`push_if_needed`／`interval` 生产只传 0；`scripts/manage_tray_startup.ps1` 已由 `desktop_startup.py` 接管（同时改 ADR-0011 与 `docs/OPERATIONS.md`）；三张「哪些路径算运行时」清单合成一处。
    - 领域层：`catalog_rules` 里站名交替串、TLD 列表、`_CODE_DATE` 各写两份；`transcodes.requires_conversion`／`browser_path` 是同一段缓存逻辑；`code_variants` 在 `jav_cover_fetch` 与 `catalog_rules` 各一份；`library_processing` 是第三条 r18 请求路径且跨模块拿私有 `_fetch`；`metadata_seesaa.RoutedMetadataProvider` 只有 `scrape_codes.py` 用，内联。
    - scripts：`audit_creator_attributions.py`（查的 `legacy:asset` 已无写入者）、`apply_metadata_tags.py`（绕过 `/review`）、`creator_tags.py --apply-review`（与 `web_review` 判据不同的第二条写路，`--export-review` 要留）建议删；`backfill_rule34_tag_types.py` 2026-09-08 已跑完全部待补条目，连接器早已在入库时取类型，脚本可删；7 处绕开 `scripting.open_for_write`、5 处自拼只读 URI、5 处手写线性重试要接上共享实现；`audit_video_endcards.py`、`audit_fc2_similarity.py`、`localize_series_names.py`、`find_ads.py` 还会用但文档没登记，归到 `peach-batch-jobs` 或 `docs/SOURCING.md`。
    - tests：约 3 700 条源码文本断言集中在 `test_web_ui.py`（近 90 天 20% 的提交都在改它）与 `test_follow_web.py`；页面断言设施两处各写一份；`test_fastapi_api.BASE_SCHEMA` 手写 19 张表已漂移，31 个文件手写 `CREATE TABLE` 而 `tests/support/ledger.py` 只有 14 个在用。方向是触碰时迁到 `test_web_js.py` 与 `fresh_ledger()`，不整体重写；`check_copy_final_state.py` 的词表不拦「过去／此前」。
    - 前端：9 处 `await import('/dist/peach-ui.js')` 与文件顶部静态 import 并存（`test_frontend_build.py` 与 `test_web_ui.py` 钉住了这种写法，要同改）；`wireNavigationDrag` 与 `ui-components.wireDragReorder` 双实现；`refreshStore` 零消费；`.fnote` 在 21 与 22 号 CSS 互相覆盖。
    - 文档：同一条规则最多写在 15 处（测试入口）；`CLAUDE.md` 正文与 AGENTS、worktree 技能重复；`peach-ledger-write`、`peach-reference-evidence`、`peach-worktree` 引用的 HANDOFF 节名已不存在；`docs/STATUS.md` 版本行落后；本文件有 7 对重复条目（7↔18、12↔21②、13↔22、9↔34、8↔30、28↔30）与一节评审记录；`docs/PIKPAK.md` 是按日期的 runbook，流程该归 `peach-batch-jobs`。
36. 域映射门槛只覆盖 `web/` 与 `frontend/`。同一个漏洞在别的前缀上照样成立：`tests/test_babepedia_match.py` 读 `scripts/match_babepedia_creators.py` 却只登记在 metadata 域，改那个脚本时 `auto` 选的是 tooling；`tests/test_frontend_build.py` 读 `docs/CLOUDDRIVE.md`，而 `.md` 一律归 checks。按 `test_runner.repository_paths_read_by` 全树扫一遍，`scripts/`、`docs/`、`.github/`、`resources/` 四类共约三十处。要补的是 `AUTO_SCOPE_PREFIXES` 本身——把逐个脚本映射到它真正的域，像 `scripts/localize_performer_names.py` 那两条那样——补完再把 `tests/test_test_planning.py` 那条门槛的前缀白名单去掉。
37. 归一后要用户判的 10 张厂牌标识：AttractiveLLC ×3、C-more_Entertainment ×3、Bambi_Promotion ×2、Deep_s、Tameike_Goro。补到内容外接圆这条规则在「设计上就出血到边」的标识上会把内容推离边缘，逐张判词在 `peach-data/review/refit-review-20260908.csv`，原图在 `peach-data/archive/logos-pre-refit-20260908/`，对比页 `build/logo_compare.html` 的第一节。占宽和圆外损失都分不开 C-more（0.98／0.97）与 MARRION（0.95／0.94），所以没加窄化条件——先由用户定还原哪几张，再按定下来的形状写判据和测试。
38. 补底到 64 的 7 张还没落盘：`normalize_studio_logos.py --apply` 要用户自己跑（DorcelClub.img、Flower 三张、LINX.img、HEYZO.icon、Prestige.icon，逐张前后见对比页第三节）。
