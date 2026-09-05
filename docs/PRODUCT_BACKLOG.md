# Peach 产品待办

更新时间：2026-09-05。这里只记录尚未完成或只完成一部分的需求；运行数字以 `peach-data/state/job-status.md` 的自动区块为准。

## 已有骨架、尚未完成（6 项）

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
3. **在线追更**：`src/peach/follow_providers.py` 登记的十一个来源（FANBOX、SubscribeStar、Patreon、Kemono、Pawchive、Coomer、Rule34Video、Rule34.xxx、Rule34 Paheal、F95zone、SimpCity）、WIP/alt/跨站重复判定、`follow_source`/`follow_item`、`peach follow`、看的 `/follow` 与管的 `/follow-manage` 两个页面已上线，writer 用 APScheduler 按设置自动轮询，在线资产可就地播放。仍缺的是下载落地（凭据、流量与磁盘预算未定，见下面「待执行的操作」第 12 条）和 simpcity 的可用入口（DDoS-Guard，未取得）。
4. **首尾帧出处与不完整候选**：已有受限 FFmpeg 首尾抽帧、Windows 内置 OCR、证据帧缓存、来源/Full version 候选和 `/review`；仍需决定全库批次范围，并把用户批准后的不完整版判断接到更好版本目标。
5. **厂牌 Logo 补齐与持续校验**：14 个已确认社交 handle 已有内容缓存、provenance、精确/感知哈希、质量与重复门槛及健康报告；仍有 72 个厂牌没有可信 handle，必须继续从官网/公开来源取证，不能猜账号。
6. **口味证据持续刷新**：ledger 已实时记录搜索、播放、高潮、喜欢/理由、不合口味和稍后看；浏览器历史现可用 SQLite 一致性副本增量进入私有源库，并生成不含 URL/标题的 creator/tag candidate 与聚合报告。旧 2026-08-13 原始包已确认不在 Windows 外置盘；仍需在 Mac 开启 iCloud Safari、完成首次导入，并把两端每周刷新装成系统计划任务。AI 结论不得直接改真相字段。

## 尚未实现（26 项）

1. AI Provider 的真实调用、能力协商、Credential Manager 凭据和候选审核 UI。
2. 剩余单一创作者风格板复核、无标签内容补标。
3. 缺时长资源补 probe 后再生成接触表。
4. PikPak 计费抽样与下载边缘质量核验。
5. 复用 CommunityScrapers 一类公开刮削规则做元数据导入：只当只读规则语料，不重新引入 Stash 运行时依赖（ADR-0021）。
6. 剩余 status / suggest / ledger 逻辑移入应用边界后删除旧 CLI 表面。
7. 把常跑批处理折进 `peach` CLI：`probe`、`sheets`、`scrape_codes`、`fetch_jav_covers`、`taste_history`、`traffic_watch` 现在各是一个脚本入口，参数、限流与健康报告口径不统一。
8. 开源通用化的发布准备（ADR-0023 第 4 阶段）：清扫 `docs/` 与 `.claude/skills/` 里的局域网地址、主机名、账号名、备份文件名与个人目录，把只对一台机器成立的运行态移出仓库，并把 `tests/test_repo_hygiene.py` 的个人字面量门槛从 `src/peach/` 扩到文档与技能。许可证、贡献与安全说明、issue/PR 模板在仓库里；设置层、来源挂载点 ID 与可整体关闭的复制链路在 Windows 生效，macOS 待跑 `peach init --from-existing --mount local=<落点>`。
9. 女优高清头像的写入侧：`scripts/audit_performer_portraits.py` 已能出候选与实测证据，仍缺按复核结果复制头像文件那一步，以及实体合并后孤立头像的 relink（如 `8022 <- 8168`：只有旧 ID 的 provenance 名唯一命中当前实体、当前目标又不存在时才算候选，不覆盖、不删除旧文件）。
10. 文件名与网盘目录整理的落地：`scripts/clean_names.py` 与目录计划只出 dry-run CSV。真正改名要独立维护窗口——停同类任务、确认本机是 writer、SQLite backup、逐条同目录 rename 并同步账本 path/name、失败时文件名回滚，最后跑完整性、外键与路径存在性检查；不跨盘移动，也不按文件夹名猜创作者。
11. 来源与默认值通用化（ADR-0023 第 5 阶段候选）：`peach init` 的问答已按本机路径只声明 `local`，非交互路径写出的 `DEFAULT_LOCATION_ROOTS`（`R:\media`、`B:/`、`A:/`）仍是维护者的示例盘符。剩两件事：来源用「本地 / 远端挂载」类型字段代替代码里按 `local`/`115`/`pikpak` 名字点名（`web_resource_sync.py` 的 SQL、`media.py` 的 HLS 规则）；复制链路支持 win↔win、mac↔mac 与任意一台当写者，目前只验证过 Windows 写者 + macOS 读者。
12. 非 editable 安装的跨平台验收：wheel 资源与 Windows 基础依赖、仓库外 CLI 冒烟已就绪，仍需取得 macOS、Python 3.12 消费任务结果。
13. 健康检查生产验收：`db` 区分 missing、empty、available、unavailable，`?ready=1` 检查 schema 校验和；待部署后用项目 CA 验证 HTTPS 与损坏／未初始化状态。
14. 界面国际化：界面目前只有中文，先补英文。
15. 制品与更新渠道：Windows 独立测试包、首次引导与本机配置表单已实现，Release 消费任务只下载制品验收。剩余为 macOS 独立包、代码签名、独立测试包的自动更新、局域网配对和更完整的配置管理；本机打包托盘已按构建身份自行重建，版本号由 `integrate` 在本地集成时推进，标签仍由 `release_tag.py` 独家发出。测试包更新采用退出程序后完整解压新版，数据目录保持独立。
16. 「第一个小时」教程与故障排查文档：init → 声明来源根 → scan → 打开页面 → 手机信任 CA → 托盘/菜单栏自启动，每一步写清失败表现与对应的排查动作；截图用一套小的 SFW 演示数据集生成，不取自真实馆藏。
17. 项目网站：一页说明是什么、截图、安装入口与文档链接。
18. 口味导入引导：`/taste` 上传（Takeout ZIP、browserexport 兼容文件）与 `scripts/taste_history.py` 直读本机浏览器库两条路都能用，但没有面向陌生人的文档。需要一页「各浏览器怎么导出、多台设备怎么各自刷新」教程，把脚本折进 `peach` CLI（见第 7 条），并写明定时刷新的安装方式。
19. README 瘦身：把「依赖维护」「开发」两节移到 `CONTRIBUTING.md`，「目录」并入 `docs/ARCHITECTURE.md`，「主要页面」「关注与候选」压成一张表；README 只留是什么、边界、前置条件、安装、下载、文档入口与许可证。中英两份同步。
20. 局域网访问：HTTP 导航与 HTTPS 单一业务入口的候选代码已就绪，待生产部署验证。配对仍需一次性配对码或 HTTPS 地址二维码，减少设备首次访问时手输口令；现有口令生成、取用与非回环无口令拒绝启动不重复实现。
21. 全新安装的自动门槛：现有 `Test` 装的是 `-e ".[build,vision,maintenance-115,naming]"` 全套可选依赖、开着 pip 缓存、只跑单元测试，证明不了「陌生用户按 README 装完能用」。补三条互相独立的冒烟：① minimal source——全新 venv、`--no-cache-dir` 只装默认依赖、`peach init`（连跑两次验幂等）、`migrate status`、**离开仓库根目录**再 `peach serve`，请求 `/healthz`、`/`、`/api/items`，覆盖 3.12／3.14 × Windows／macOS 以及无 FFmpeg／OpenSSL／Node 的机器；② wheel——`python -m build` 后在不 checkout 源码的 job 里装 `dist/*.whl` 走同一条链路，它通过才能去掉 README 的 `-e` 硬要求（依赖第 12 条）；③ artifact-only——只下载刚构建的制品、不 checkout 源码地跑起来（依赖第 15 条）。消费方一律不许 checkout：工作目录会替漏文件的制品兜底，那是假通过。失败场景也要覆盖：数据根不可写、端口被占、账本损坏、未配置媒体目录、无 FFmpeg、非回环监听但无口令、两个 writer 同时起。
22. `peach doctor` 与分级 `/healthz`：`doctor`（另带 `--json`）逐项报版本、数据根可写性、配置文件合法性、数据库能否打开、schema 版本与待执行迁移、FFmpeg／ffprobe／OpenSSL 路径、挂载点可达性、端口占用、是否处在「局域网暴露但无口令」状态、后台任务最近一次失败；输出脱敏，不带口令、cookie、站点凭据和完整媒体路径。`/healthz` 相应从布尔改成分项状态（`database`／`schema`／`configured`／`ffmpeg`／`media_mounts`／`security`），与第 13 条一起做。
23. 性能基准：用 SFW 合成数据生成 1k／10k／100k／500k 四档库，nightly 测冷启动到 `/healthz`、目录页与详情页 p95、两字以上搜索 p95、本地 SSD 与网盘挂载的 Range 首字节、空闲 RSS、后台扫描时前台退化倍数、备份期间读请求不失败。门槛用「相对上一次基线下降超过 20%」，不给绝对毫秒数——不同机器不可比。数据集与第 16 条的演示数据集共用。
24. CI 的 Windows job 太慢，一次 push 的墙钟由它决定。同一批 2786 个用例在 `macos-latest`（arm64）上 57 秒，在 `windows-latest` 上 1475 秒，本机 Windows 是 324 秒——runner 比开发机还慢 4.6 倍。按时间戳差算，250 个用例（9%）吃掉 1119 秒，每个稳定在 4.5 秒上下，形状像每建一个临时文件被 Defender 扫一遍。两条路各自独立：一是在 Windows job 里对 runner 的临时目录加 `Add-MpPreference -ExclusionPath`，先量一轮确认是不是 Defender；二是把 `scripts/test_runner.py` 的域拆成矩阵分片并行跑，代价是每个分片重付一次装依赖的 37 秒。不要为了缩短墙钟把 Windows job 从矩阵里去掉：它是生产平台，也是唯一能拦住 Windows 独有回归的地方。
25. 托盘子服务的日志不轮转：`ServiceManager` 以追加模式打开 `logs/tray-<服务>.out.log` 与 `.err.log`，本机一周就长到 28 MB，`tray-scan.out.log` 与 `windows-source-sync.log` 同样只增不减。在起服务前按大小轮转，超过阈值改名保留一代即可；写文件的是子进程的 stdout，不经 `logging`，所以 `RotatingFileHandler` 用不上。
26. 借鉴 vercel.com/<team>/~/deployments 的令牌式筛选与排序。那一行不是一排互斥药丸，而是「Add Filter + 若干条已添加的维度令牌（Author／Environment／Status）」，每个令牌自带下拉，维度可叠加、可逐个摘掉，另有独立的日期区间与状态汇总（`6/7`）。2026-09-05 实测它的三态：未生效 `1px dashed rgba(0,0,0,.21)` 透明底，悬停／聚焦换成 `#FFFFFF` 实底加 `1px solid rgba(0,0,0,.08)`，下拉展开时 `gray-200` 底配实线——虚线读作「建议但没应用」，实心读作「已生效」。
    首页大概率不合适：`.tagbar` 那一排是单选（`全部`／`没看过`／`稍后看` 恒有一个生效），把没选中的三个画成虚线会读成「三个待处理的筛选」；而且这套「填亮 = 生效」要成立，页面底色得比控件低一档——Vercel 的仪表盘底是 `#FAFAFA`，Peach 的 `--ground` 是纯白，没有可填的更亮档。真正对得上的是多维叠加的场景：`/follow-manage` 的来源／状态／WIP 组合筛选，和 `/review` 的候选筛选。先在这两处试，别动首页。

合计：**32 项开放需求**，其中 6 项已有骨架，26 项尚未实现。已完成的需求不在这里留痕，去 Git 历史查。

## 待执行的操作（32 项）

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
21. 厂牌标识规则：logo 文件一律不透明方图（`images.bake_square`），页面三处一律 cover。另行授权后跑 `normalize_studio_logos.py --apply --backup <落点>` 回溯真实目录：27 改、4 个 SVG 不动。
22. 把 javdatabase 的 idol 页接进社媒／官网候选：183 页缓存里 139 页带 X 链接、138 页带另一个官方站，由番号定位、不必离线比名。复用 `peach.social_links` 的判据与 `install_entity_links.py` 的 `FIELDS`，排掉四个整站广告主机。
23. 人工判 `domain-code-review.csv` 里 `WX17` 那 269 条水印存疑行，脚本不给提案。
24. 给账本厂牌补日文别名。MGStage 名录 351 家只对上 29 家，卡点是账本 118 个厂牌只有 27 条别名、几乎没有日文名——补完别名再对一次，覆盖面会一次性抬上去。
25. 其他厂牌官网的厂标与演员资料广度扫描（SOD、FALENO、Attackers、S1、Moodyz 等），用户 2026-09-04 定为「先做 b 看效果」之后的下一轮。
26. 用 javtiful 的 `/ja/actress/<slug>` 补演员的罗马字↔日文配对：315 页约 7560 位，切语言前缀就出日文名。厂牌名不随语言切换，这条只服务演员别名。
27. 37 位演员在 javdb 上只有日文名（`同形`），另有 5 位未取得，中文名要换来源：javtiful 的 `/ja/actress/<slug>`（第 26 条）或 javdatabase 的 idol 页。复核产物 `peach-data/review/javdb-cn-names-20260904.csv` 逐行带 verdict 和证据，可直接筛。
28. macOS 标识 `io.github.longmeidao.peach.*` 在 Mac 上生效：代码已在 master（`src/peach/appid.py` 是唯一来源，`install_macos_agent.py` 与 `setup_macos_port80.sh` 会自己清掉遗留标签），命令与四项核对见 `docs/OPERATIONS.md`「桌面入口与发布」。放进第 30 条的维护窗口一起做；两台机器都跑过之后删掉 `peach.appid` 里的遗留标签表和用到它的分支。这是换生产入口，执行前要在同一轮拿到用户确认。
29. `peach-data/review/composite-names-20260904.csv` 里还剩 28 条 creator 规范名带括号，括号里是读音或罗马音（`Egami(えがみ)`、`永地(eichi)`、`猫屋(NEKOYA)`），用户定了不拆——它们不像艺名那样各自独立，是同一个名字的注音。同一份 CSV 里 575 条 tag 是角色的作品出处消歧，10 条 series 括号里是厂牌或载体消歧（拆了会把三个 `AV DEBUT` 撞成一个），都不要动。剩下真正待判的只有 performer 规范名 `Mana(23)` 一条：数字是去重后缀还是名字的一部分要看源站。
30. Mac 追上 master 的一组操作，按顺序做完再重启菜单栏——做完之前不要重启：master 上的 `peach serve --host 0.0.0.0` 没有口令会拒绝启动，reader 会直接消失。① `git pull` 到 master；② `pip uninstall -y peach-app && pip install -e ".[macos]"`；③ 先把 Windows 的 `peach-data/secrets/auth-token` 复制到 Mac 数据根的同一路径——reader 取 writer 复核结果发的是自己的口令，两边必须是同一份，而 `--from-existing` 找不到文件会自己生成一份不同的；④ `peach init --from-existing --mount local=<落点>`；⑤ 重启菜单栏，核对 `/healthz`、`/review` 能读到 writer，手机与 Mac 浏览器各登录一次。第 28 条的标签改名可以放进同一个维护窗口。
31. 给事务所补一个 `/agencies` 索引页。现在进事务所页的入口只有女优页上的那个名字，57 家里没有关系的那几十家等于只能靠猜地址。`q_index` 的 `performers` 分支按作品数排、带头像，事务所要的是按成员数排；`openIndex` 里 `people`、`entityKind`、加载文案三处是按 kind 写死的，加一种就要各动一处。
32. `install_entity_links.py` 的可达性门槛按「非 200 就跳过」执行，而同文件的 `is_gone()` 明确写着 403／5xx／连接错误不能当「页面没了」。首批 703 条里 137 条因此没装，其中 31 条 twitter.com、23 条 t-powers.co.jp。把跳过分成「确证没了」和「这次没取到」两档：后者留进待复查队列，配合 `rediscover_entity_links.py` 对 t-powers／nax-pro／mines-pro 这些已经搬家的域名上溯找新锚，再装一次。
