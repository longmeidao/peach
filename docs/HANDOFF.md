# Peach 交接与长期工作约定

本文件只保存跨任务长期有效的事实和工作规则，不记录逐次聊天流水。

## 无摩擦接手

- Codex 自动读取项目层级中的 `AGENTS.md`；Claude Code 通过 `CLAUDE.md` 导入同一文件。
- 两个智能体使用同一入口、同一必读顺序，不再生成按日期命名的临时交接文档。
- 新任务直接以 `R:\peach-app` 为工作目录，并说：“接手 Peach，按项目入口文件继续 STATUS 中的下一任务。”
- 改变运行事实的任务同时更新 `docs/STATUS.md`；长期规则更新本文件、`docs/REUSE.md` 或 ADR。
- 用户不是消息中转站。结论、进度、待办和证据必须写入共享文档或机器可读产物。
- 面向用户阅读的文档叙述统一使用中文；代码标识、命令、协议和专有名词保留英文。

## 并行智能体与 Git 工作树

- Codex 负责架构、文件归属、审核、迁移、真实 ledger 写入、服务重启和最终验收；Claude 适合并行执行抽帧板阅读、候选元数据刮削、CSV 对账等边界明确的机械批次。
- 并行任务必须给出输入/输出路径、网络和费用策略、写入边界、验收条件。工作者只产出 `candidate`，不得自行标为 `approved`、执行 `--apply`、改迁移/ADR 或重启服务。
- 并行代码改动使用 `scripts/agent_worktree.py create` 创建独立 worktree。工作者提交并运行 `ready`；协调者审核后运行 `integrate`。完成顺序不能决定覆盖顺序。
- 工作者在报告 `ready` 前先把分支 rebase 到当前 `master` 并重跑测试；同文件修改在工作者分支解决，协调者只集成已经基于最新主线的原子提交。仓库启用 Git `rerere` 记录重复冲突的已确认解法，但它不能代替人工审核。
- 禁止 `git add .`、`git add -A`、目录或 glob 暂存。只暂存任务明确拥有的文件，并检查 `git diff --cached --name-status`。测试和对应实现必须原子提交。
- `bba0b77` 是已发生的反例：测试被误判为本任务文件而进入提交，对应 `probe.py` 未暂存，导致 HEAD 出现“测试指向不存在实现”。独立 worktree、暂存路径复核和实现/测试原子性因此是强制规则。
- 在 worktree 运行测试时，项目 venv 的 editable install 可能仍指向主目录。必须设置 `PYTHONPATH=<当前工作树>\src`，先输出 `peach.__file__` 核对来源，再运行测试。
- **唯一测试入口**：本仓库只使用 Python 标准库 `unittest`，完整命令为 `python -m unittest discover -s tests -p 'test_*.py' -v`；项目依赖不含 pytest，不得再凭通用习惯调用 pytest。健康检查契约固定为 `/healthz`，不是 `/health`。

## Claude 在本项目中的实际能力边界

2026-08-14 的真实执行证明 Claude 可以正常完成：

- 查看成人内容并分类行为、着装、身体属性、场景和制作风格；
- 从公开番号库刮削元数据并映射本地词表；
- 编写上述领域的代码、正则、批处理、对账和中文文本；
- 根据番号、文件名、画面水印、Logo 或发行元数据识别女优和厂牌。

此前“Claude 会拒绝露骨行为分类”的记录已废止。一次实际任务读取 30 张创作者板，为 27 位创作者、4,518 个视频写入 27,295 条 `vision_creator` 标签，含口交、足交、手交、乳交、骑乘和后入，最终 27/27 与 ledger 对账一致。

仍需遵守的边界：

- 不处理真实未成年人；本库经用户确认只有成年人。`萝莉`、`学生`、`洛丽塔`、`制服` 是成年角色扮演/题材标签，不能仅凭这些字符串停止编目。
- 不从人脸识别私人真实身份。持久归属必须有番号、文件名、水印、厂牌、公开链接等非人脸证据。
- 本库经用户确认均为自愿成人内容。`泄露`、`流出`、`G3104` 等是营销或来源风格词，不是非自愿证据；只有文件级直接反证才停止并报告。
- 删除和其他不可逆/对外动作先生成带证据和置信度的复核产物，执行步骤单独授权。
- 单帧逐条判断、过暗/模糊画面、仅靠文件名区分片源水印与广告都属于弱项，应降低置信度或补抽帧，不应伪装成确定事实。

## 只存在于聊天中的结论等于不存在

- 得出结论的同一步必须写入 ledger、CSV 或其他持久产物。
- 结论被修正时，所有派生产物必须重建；只改说明文字不够。过期删除清单比没有清单更危险。
- verdict 旁必须保存证据和来源；完成前把声明意图与数据库实际行对账。
- 历史视觉逐条任务曾在聊天里说“已保存”，但 `asset_tag` 中 `source='vision'` 为 0；根因是根本没有写入步骤，不是模型拒绝。
- `disposal-candidates.csv` 曾在 `BNST033` 判断修正后未重建，仍把真实 3.2 GB 正片列为待删；这是必须同步所有派生产物的直接证据。

Claude 的 `.claude/settings.json` 已配置 Stop、StopFailure、SessionEnd hook，调用 `scripts/job_status.py --write --hook-event`。脚本只记录脱敏生命周期摘要，重新从 ledger/产物计算数字，并原子更新 `docs/STATUS.md` 的 `<!-- job-status -->` 受管区块；不复制 prompt、response 或凭据。强制杀进程/断电无法运行 hook，下次调用会修复计数。Codex 暂无等价项目结束 hook，仍由协调者在同一改动里更新文档；不要用脆弱日志监听器模拟。

## 参考产品证据登记

凡用户要求“模仿/参考/对齐”，必须先取得当前可复现证据：实时行为加 DOM/CSS/JS；源码不可得时才使用精确截图测量。记录 URL、日期、版本/hash、复用行为和 Peach 的主动差异。证据不可得就写 `未取得`，不得把猜测描述成忠实复刻。

- **Beeg 卡片控件（2026-08-15）**：当前根页面加载 `https://beeg.com/dist/main.9442c3b8.css`（SHA-256 `E585B07CA0C312C28903DB939144B26A3C4BFBC9499F5997BDDE168A197CDB34`）和 `main.9442c3b8.js`（SHA-256 `A7321F6E84D97417B588B6E98EEC86A15B30DC4C36B03537481CC55A4CF933E7`）。计时圈为 36 px、上/右 12 px、`rgba(0,0,0,.24)`、`saturate(180%) blur(12px)`、2 px 白色圆环；桌面 hover 放大 1.2。稍后看控件使用同类透明处理，位于右下 12 px。Peach 等到预览可用后才启用计时圈，按用户要求连续悬停 5 秒才放大；放大层保留 Peach 自己的居中 -10/+10/详情控件。
- **Beeg 表面层（2026-08-15，同一 CSS/hash）**：暗色背景 `rgb(2,4,8)`，表面 `rgb(34,34,34)`。当前压缩 JS 的 Button 组件证明：`plain/outlined` 是透明背景，`filled` 才使用 `rgba(245,250,255,.05)`；边框分别是 15% 和 10% 白色内描边。frost utility 的 `rgba(38,40,44,.72)` / `rgba(30,30,30,.72)` 只用于指定浮层，不能套到全部厂牌和标签。页首蓝绿背景是 `/dist/assets/glow.webp`（1000×563，SHA-256 `ACA7A914D82843EE4A655C35651931CDC0D42308EDC0F7CB16D8EC63C7AE3ECA`）以 `49vh` 铺放并向 `rgb(2,4,8)` 渐隐；Peach 不复制许可不明位图，使用本地 CSS 光晕。此前把“取到 frost token”误写成全部表面已对齐，现已纠正。
- **Beeg 实体资料页（2026-08-15）**：`view-source:https://beeg.com/DianaRider` 可取得 SPA 启动 HTML及上述当前 CSS/JS；原始 Vue source map 返回 404，明确记为 `未取得`。压缩 JS 中 `TagProfile` 的可复现结构是：无大外框卡片、桌面 160×160 圆头像、资料文字并排，别名/统计/简介/链接分层，关联实体另起一段。Peach 资料页据此隐藏首页三层筛选，在资料下显示馆藏已有标签、关联艺人和作品；不声称取得原始 Vue 文件。
- **失败报告规则（2026-08-15）**：浏览器工具拒绝 URL 不等于公网不可达；本机 `curl.exe` 的 Schannel 握手失败也不等于代理失效。本次使用同一 `127.0.0.1:7897` 代理的 Git curl 成功取得当前资产。任何取证、浏览器或视觉验证失败都必须立即报告失败步骤、原始错误、影响和替代路径；静态/API 测试不得冒充视觉验收。
- **TikTok 单列滚动（2026-08-15）**：当前 bundle `async/89993.30b4c2a9.js`（SHA-256 `C4D4867C5C6C89DCE560D429A4686427C911267DCBB2787AEB31B7BD333E9088`）使用 200 ms、`cubic-bezier(.2,.2,.4,.9)`、目标 `offsetTop`，滚动时临时禁用并恢复 `scrollSnapType`。Peach 复用时长和 easing，保留自己的两视频预载与 wheel/touch 队列。
- **Apple 播放控件（2026-08-15）**：Apple HIG “Playing video” 只支持熟悉、克制的传输控制语义，没有提供可复用的 `gobackward.10`/`goforward.10` Web SVG。Peach 使用固定版本的 Lucide 子集和明确的“后退/前进 10 秒”无障碍标签，不声称精确复制 iOS glyph。
- **Vercel 设计规范（2026-08-15）**：`https://vercel.com/design.md`（SHA-256 `07ED2923294AA326F65F9D9D4094B6E97BF7DE10C39ACD8BE935F2045C5A688F`）只作为评审清单：先用字体和间距建立层级、保持连续画布、避免任意图标瓷砖/嵌套卡片/微小灰字，动画只表达状态或连续性。
- **kill-ai-slop**：在 commit `96d1ca568a1db7e1ef9a381644c744440f816ee4` 上作为减法审计清单使用，不安装 skill、不复制 scanner。
- **Lucide**：通用操作和导航图标使用固定本地 `lucide-static` 1.31.0 子集（ISC）；许可见 `web/vendor/lucide-LICENSE.txt`。品牌/来源 Logo 和计时圈不属于通用图标。
- **Rule34 样式**：旧代码注释没有 DOM/CSS 证据，已删除“Rule34-style”声明。当前标签颜色是 Peach 自有语义。
- **T3 Code/CodexBar 用量**：这是复用决策，不是 Peach UI 复制。T3 Code 已提供 Codex + Claude 历史 token/成本界面；实时剩余额度使用官方 Provider 入口，Peach 不再造日志扫描器。
- **标签添加弹窗（2026-08-15）**：用户提供 macOS 标签管理弹窗截图，未提供产品名或可访问 URL，源码证据为 `未取得`。Peach 只复用截图可证实的交互层级：搜索、最近使用、全部标签、已选状态和键盘上下/Enter/Escape；不声称像素或源码级复刻。

## 智能体用量与任务路由

- 调度看官方配额窗口，不看 API 等价美元估算。Codex 使用 App Server `account/rateLimits/read`；Claude 使用 Claude Code 已登录用量界面。不得打印、复制或保存 OAuth token。
- Codex 负责架构、迁移、浏览器依赖网站、最终 review/apply 和长期任务；Claude 负责边界明确的刮削、归一化、候选 CSV 对账、文件名/番号/水印提取和经复核的风格板分类。
- 女优/创作者归属可使用发行番号、文件名、水印、厂牌、别名、公开链接和跨来源一致性。人脸最多用于同库一致性辅助，持久身份仍需非人脸证据。
- 目录名只是一条候选证据。当前扫描器已停止从目录生成创作者；历史 `legacy:asset` 关系使用 `scripts/audit_creator_attributions.py` 逐项审计。即使目录名与真实创作者同名，也不能把整个子树直接传播成创作者真相。
- 待办数量统一报告“可执行 / 被阻塞 / 合计”。例如 PikPak 的 4,740 与 10,196 不是矛盾：前者有时长可抽帧，另有 5,445 条缺时长需先 probe。

## 批处理失败值与流量边界

- 测量失败不能写成下游可误认的正常值。`probe.py` 曾把“ffprobe 无时长”写成 `duration=0`，导致数据同时退出 `duration IS NULL` probe 队列又进不了 `duration>2` 抽帧队列。现在失败写 `-1`，并提供 `--redo zero|failed|all`。
- 两组状态数字看似矛盾时，先查是否有两边查询都遗漏的状态，不要直接认定其中一组错误。
- 2026-08-15 的 115 抽帧曾把系统盘写到零：接触表在 `R:\peach-data`，真正膨胀的是 CloudDrive 位于系统盘的稀疏读取缓存。`file_buffer_disk_cache_max_bytes` 现为 50 GiB、策略为 LRU；CloudDrive 退出时会重写配置，后续必须复核该值是否保留。
- 起跑前一次 `require_free_space` 不是运行期闸门。`DiskGuard` 默认每 20 秒重读 `C:` 实际余量；`probe.py`、`sheets.py` 和 `creator_boards.py` 触线后停止取新任务、保留已完成结果并返回退出码 3，不能伪报正常完成。
- Windows 查询已消失 PID 可能抛 `OSError(winerror=87)`，不是 `ProcessLookupError`。`PidFileLock` 必须把它识别为陈旧锁并安全清理。
- 2026-08-15 经 mihomo 实测：115 单文件 ffprobe 约 25 MB，九帧接触表约 285 MB；PikPak 单文件 probe 12–52 MB，九帧约 163 MB/13.7 秒。PikPak 抽帧的主要约束是字节而非耗时。
- `-probesize`/`-analyzeduration` 无法减少 CloudDrive 固定块预取。创作者板在未知时长时可回退到 60 秒 seek，因此无需先花约 207 GB 做全量 PikPak probe。
- 200 GB 守卫默认只统计代理流量，能覆盖 PikPak，不能看到直连 115；需要覆盖直连来源时显式使用 `--count-direct`，且不要在同一直接计量窗口混跑不同来源。
- 短促测试无法刻画会累积的限流。r18 在 12 个请求的实测里 1.0 秒间隔全过，据此把默认从 2.0 降到 1.0，结果连跑约 18 分钟后开始被拒，556 位里 203 位被判成假阴性；改回 2.0 秒连跑 62 分钟稳定。限流参数只能用与真实批次同量级的运行来标定。
- 限流是各主机自己的事，不是整个任务的属性。`HostLimiter` 按主机各记一个下次可发时刻，线程等 r18 的空档时去查 av-wiki 和 javdb，实测 12 位从约 8 秒/位降到 4.4 秒/位。r18 每位要两个请求，这是并发压不掉的下限。
- 长任务必须能续跑。一次未捕获的 TLS EOF 曾让 62 分钟的批量结果归零：网络异常要降级为空值而不是抛出，结果要定期落盘，`--resume` 只把成功判定当作已完成——`no_name` 这类多半是限流假阴性，冻结在复核文件里就再无重试机会。

## 身份合并与来源分工

- 规范名用最新艺名，旧名一律降为别名。r18 记录的是作品发行当时的艺名且不会回溯更新，所以改过名的女优在 r18 上永远是旧名；av-wiki 的 URL slug 就是罗马字，可与 r18 一样做精确回配，并给出现用名。
- “这一页只有一位女优”永远不构成证据。库里大量番号是 BEST 合集（一部片可列 8~11 位），搜索无结果的页面仍会渲染推荐文章，改名后 slug 也会变。同一个错误判据在 javdb、av-wiki 两处各犯过一次，都是靠 dry-run 拦下的：一次让两位不同女优被认成同一人，一次让 5 位里错 3 位。精确回配命中优先于任何“唯一”推断，“唯一”只有在两个番号同证时才作数。
- `entity(kind, normalized_name)` 的唯一约束冲突通常不是 bug，而是信号：两个实体其实是同一人的新旧艺名。合并走 `peach.entities.merge_entity`，保留作品多的一侧，迁移关系/别名/外部引用/链接/搜索词，并把所有旧称留作别名。`entity_external_ref` 每个 provider 只能留一条，同源的第二条会被丢弃并报告，不能静默覆盖。合并不可逆，必须先取得用户授权并备份。
- 改写 `entity.canonical_name` 属于真相字段写入，与迁移同级：`--apply` 必须同时给 `--backup`。
- 头像与厂牌 Logo 的取源方向相反。头像去精心整理的图库（Gfriends 约 10.7 万张，目录名首字符即质量档位），不要回官方站——同一张脸 DMM 官方只给 125×125，图库存的是 500×500 起，最高 1500×2125。Logo 是品牌标识，官网与维基才是权威来源。
- 头像门槛按长短边分别判定（长边 ≥500 且短边 ≥300）。竖构图人像宽度天然小，套用为方图设的“短边 ≥512”会拒掉 `0-Hand-Storage`(334×501)、`8-GRAPHIS`(360×508) 这些最优来源。
- 可用来源实测（2026-08-15）：r18.dev、av-wiki.net、javdb.com、Gfriends 可用；javlibrary、missav、xslist 被 Cloudflare 拦，njav 有验证墙，jav321 无独立女优字段。被 Cloudflare 拦的站一律放弃，不绕过机器人检测。
- 打创作者级标签前必须先验证这个 creator 是不是聚合目录。按 ledger 路径的下级目录分布判断：`Myfans` 下含至少 4 位不同创作者，`RiaKurumi` 是女优而非创作者且作品分属 cospuri／fellatiojapan／spermmania 三个厂牌。给聚合目录打统一风格标签就是 `asce` 事故的重演。

## 流量与代理诊断工具

- Windows 上后续所有代理/流量诊断统一优先使用 FlowLens（Mihomo Traffic Monitor），面板地址 `http://127.0.0.1:9091/`。
- FlowLens API：`/api/v1/connections`、`/api/v1/summary`、`/api/v1/status`。按应用、网址、节点、规则以及 PikPak 检查实时和累计流量，并查看节点延迟。
- FlowLens 只观测经过 Mihomo 的连接。`DIRECT` 仍然属于经过 Mihomo，会被观测到；完全绕过 Mihomo 的连接必须标注「未观测」，不能推断为零。
- Windows 不再把 NetLimiter、Proxifier 或依赖网页常驻的 Zashboard 作为默认方案。
- macOS 的流量诊断统一使用 Stash Dashboard。

## 数据安全

- 真实 ledger：`R:\peach-data\database\ledger.db`，WAL 模式。正常浏览会合法写入播放/行为字段。
- 测试必须使用临时 SQLite 和临时媒体；不得写真实 ledger。
- 真实迁移前依次执行 SQLite 备份、asset/tag 计数、`PRAGMA integrity_check`、迁移版本检查、服务 smoke test。
- 正式迁移 `0000`–`0010` 已应用。`0003` 增加默认 profile、稍后看、实体链接和搜索词；`0004` 增加 FTS5 trigram；`0005` 回填晚到兼容标签；`0006` 增加 `asset_preference`；`0007` 从创作者身份中移除结构文件夹名 `门槛`、`视频`、`宣传文件`；`0008` 增加 profile 级标签隐藏；`0009` 移除结构集合目录 `asce` 的假创作者关系和低置信 `vision_creator` 传播；`0010` 把 83 条“足交仙人”按水印和文件名证据归到 `suzuq`，并从 745 条 TokyoDolls 资产解除错误的“捅主任”关系，均不删除媒体和标签。
- `0007` 曾在应用后、提交前被改写注释/格式，导致校验和漂移。本次用迁移前备份重放当前 `0007`，对 298 条受影响资产与生产结果逐条对比，差异为 0 后才校正 `schema_migration` 校验和，然后正常应用 `0008`、`0009`。已应用迁移文件从此不得修改，任何后续变更必须新增版本。
- 媒体和运行数据只在 `R:\media`、`R:\peach-data`，不进入仓库。

## 运行与部署

- 日常入口是当前用户 Startup 中的 `Peach.lnk`，使用项目 venv 的 `pythonw.exe -m peach.tray`。不再并存系统服务、计划任务或注册表 Run。
- 托盘单击打开 HTTPS；菜单提供状态、重启、日志、更新检查和退出。托盘只终止自己创建的 Peach 服务进程。
- 创建 Win32 窗口前必须启用 Per-Monitor V2 DPI。正常动作不弹模态 MessageBox；更新检查在后台线程执行，用 pystray 原生非模态通知反馈。
- `src/peach/__init__.py::__version__` 是版本唯一来源；采用 pre-1.0 SemVer。Git commit 是构建标识，`vX.Y.Z` 是本地发布点。更新检查只 fetch/比较，并行 worktree 模式下不自动覆盖安装。
- `scripts/manage_tray_startup.ps1` 是唯一自启动管理入口。托盘管理 HTTP `0.0.0.0:80` 和 HTTPS `192.168.50.162:443`，服务日志写入 `R:\peach-data\logs\tray-*.log`。
- `peach serve` 用 Python zeroconf 发布唯一入口 `peach.local`；生产显式使用 `--mdns-address 192.168.50.162` 固定 A 地址，但保留 `Zeroconf()` 全合格网卡监听。mDNS 验收必须包含单元测试、运行态 health、DNS-SD、主机名解析和真实 LAN 客户端。
- `.local` 使用本地 CA，不使用 Let's Encrypt。证书/私钥保存在 `R:\peach-data\secrets`。macOS/iOS 只安装并信任 `peach-local-ca.crt`，不得分发 CA key 或服务器 key。
- FastAPI 是唯一 Web server。不得恢复平行 `http.server` 或动态 legacy loader。
- FFmpeg/ffprobe 依次从显式环境变量、`R:\peach-data\tools\ffmpeg\bin`、`PATH` 解析；不得回退到 Stash 私有目录。
- 长任务只停止自己拥有且命令行匹配的 Python/FFmpeg 进程树，禁止全机终止 FFmpeg。
- 导入运维脚本不得触发文件、网络或数据库副作用。`scrape_codes.py` 默认写可续跑复核 CSV；`clean_names.py` 先预览，`--apply` 前备份 SQLite。
- 切换服务前检查 80、443、8900、9999 端口和实际进程归属。
- 115/PikPak 播放依赖 CloudDrive 的 `B:`/`A:`；盘符对 Windows token 可见性不同，最终以 Peach 对已知作品的 `/stream` 实测为准。
- 浏览器不支持的 AVI 等容器由 `TranscodeService` 缓存为 H.264/AAC MP4，再通过同一 Range 端点提供；永不改写原媒体。
- 数据库元数据不得插值到 inline JavaScript 事件属性。真实厂牌名中的撇号曾直接造成 Firefox 语法错误。
- 验证分开报告：静态/单元/API、桌面浏览器、390×844 手机、生产服务是否已重启。

## 当前架构真相

- Ledger 拥有真相和行为；Stash 是可替换适配器，不新增直接 GraphQL helper 或 Stash 私有 FFmpeg 路径。
- Stash 调用统一经过 `StashClient`；外部 Scene ID 和来源进入 `media_binding`。
- 规范女优/厂牌/标签/创作者进入 `entity`、`entity_external_ref`、`asset_entity`；扁平 `asset_tag` 和 creator/studio 字段只是兼容投影。
- 详情、筛选、搜索、facets、索引、统计、榜单和相关推荐使用规范关系。
- 女优、厂牌、创作者、系列名称进入资料页；首页内容标签直接筛选首页，实体资料页的标签只筛选当前实体作品，并保留在 `/performers/{name}?tag=...` 等当前资料页 URL。`source_reference` 是私有来源，不开放为下载链接。
- “稍后看”写 `watch_queue`；“喜欢/为什么喜欢”写 profile 级 `asset_preference`。AI 只能把口味说明转成带来源/置信度/复核状态的候选，不能改写用户原文。
- Web 公共路由使用 `/performers/{name}`、`/studios/{name}`、`/creators/{name}`、`/series/{name}`；删除 `/entity/{kind}/{name}`。收起详情或导航离开时必须 pause、清空 `src`、调用 `load()` 并移除 video，不能只隐藏 DOM。
- “换一批”、统计、沉浸、全部女优、全部标签是动作/目的地，不显示为持续筛选状态。顶部只保留“没看过、稍后看、已标记”等需要主动进入的紧凑状态；“看过”和“疑似广告”不占首页快捷位。
- 长卡连续 hover 5 秒才放大并显示 seek；短卡立即提供“稍后看”。实体文字链接必须消费点击，不能冒泡为展开视频。
- 卡片身份女优优先：先使用 `performer_entities` 头像和链接，再回退到创作者/厂牌代表图。
- 喜欢与原因属于同一 profile 偏好；非空原因隐含喜欢，但原文不能直接冒充推荐特征。
- 详情实体采用一行一个身份，小头像/Logo 紧邻名称，不使用独立大边框卡片。旧短/中/长片标签不再显示，时长筛选只使用分钟区间。
- 反馈使用 Lucide 紧凑图标工具栏。“待删”只表示候选，真正删除必须经过复核 CSV 的独立 apply。
- 界面文案不复述标题、控件或实现状态，不用随机示例占位符和模型自我声明；只保留影响决策、防止数据损失、说明隐私/费用或解释陌生状态的文字。
- 桌面筛选抽屉只在指针进入可见 72 px 侧栏后打开，不恢复内容区隐藏热区。
- 厂牌 Logo 使用带来源的官方缓存；缺失时显示首字母，不得用任意作品图冒充。当前规范厂牌覆盖 28/114，继续走复核队列。
- 实体头像优先 `generated/avatars/<kind>-<entity_id>.img`；Stash 默认剪影和搜索结果缩略图不能作为头像。
- 厂牌归一化使用 `scripts/canonicalize_studios.py`，默认 dry-run，apply 前备份。`PREMIUM` 是独立厂牌；只把 Prestige Premium 和日文 Prestige 写法归并到 `Prestige`。
- FastAPI 与前端逻辑分离、单体部署；在线来源和 AI 只通过显式适配器进入。
- `FeedAdapter` 是首个追更连接器，显式、有界发现 RSS/Atom；不在应用启动时轮询，不直接写 ledger。
- AI 推理 API 与本地 coding/agent runtime 是不同层，不能伪装成一个等价接口。
- 3 字符以上搜索使用 FTS5 trigram；更短文本回退 LIKE。FTS 写入由迁移 trigger 维护，不在 Web 启动时修补。
- 详情身份按规范化名称去重：同一个名字已显示为女优时，不再重复显示“创作者”。标签的 × 写入 profile 级隐藏覆盖，不删除刮削/识别断言；+ 新增标签以 `web-user` 同步写入兼容层与规范实体层。
- 卡片多选有显式模式；普通点击打开详情，`Ctrl`/⌘ 切换单项，`Shift` 以上次选中为锚点选中当前可见网格范围。批量操作仍必须二次确认。待删只是候选，但卡片必须灰化并显示状态，不能仅靠不显眼的小点。
- `/tags` 是独立标签管理页，默认字母表模式，也可切换标签云；两种模式都显示数量并进入首页组合筛选。
- 高潮按钮复用 Health Icons 官方 `outline-24px/contraceptives/sperm.svg`，来源 `resolvetosavelives/healthicons`，CC0。一般操作继续使用本地 Lucide 子集。

## Web 性能边界

- 页面不得按结果总数一次构建全部卡片。首页每批 60、短片栏 18、相关推荐 20、沉浸队列 60、实体作品 48、艺人索引 120、标签索引 180；疑似广告候选可在服务端统一评分，但浏览器每次只追加 60 张卡片。
- 实体页的总数只用于标题和首批分页判断，第二页起请求使用 `count=0`，通过多取一条判断是否还有下一页，不得重复执行全量 `COUNT(*)`。首页无限滚动同样只在首批计算总数。
- `q_tops`、艺人索引和实体关联艺人的代表图必须使用单条相关子查询取得，禁止按每个人物再发一次 SQL 的 N+1 实现。
- 首页聚合数据在浏览器会话中合并并缓存 30 秒；相邻筛选复用同一进行中的请求。首页、顶部聚合、索引和实体页都有请求序号，迟到的旧响应不得覆盖新状态或再次重建 DOM。
- 无限滚动同一时间只允许一个追加请求；先判断加载锁再递增 offset，避免快速触发时跳页。图片继续使用原生 `loading=lazy`。只有本地资源可使用真视频 hover；115/PikPak 等远端源必须使用本地接触印相。滚动、换页、隐藏页面或替换卡片 DOM 时，统一停止 hover 并释放 `src`。
- 2026-08-15 实测：Prestige 显示 248 个总结果时首屏只构建 48 张卡片，点击“载入更多”后为 96；艺人索引 120 条约 311 ms，Prestige 第二页 48 条且跳过总数统计约 94 ms。具体耗时随 ledger 和磁盘状态变化，只把批量边界作为稳定契约。
- 0.5.5 起，标签筛选行与排序/换批行都常驻顶栏下方，不再按滚动方向隐藏；两行在原始位置保持透明，只在真正吸顶后加半透明黑色磨砂底与分隔线，分别占位，不能盖住卡片内容。
- 首页、女优、厂牌等普通卡片统一由 `wireCards` 调用 `openItem`。只有沉浸/短片等显式传入 `onClick` 的场景允许覆盖。隐藏的 hover 工具必须 `pointer-events:none`，只在实际显示时恢复命中，避免截走海报详情点击。
- 详情媒体用随机 `session` 标识同一次播放；收起详情、路由切换或替换详情时，前端必须清空 video 后调用 `/api/stream-cancel`，服务端取消该 session 下全部 Range 请求并拒绝迟到请求。只移除 DOM 不能保证 CloudDrive 停止读盘。
- 115/PikPak 继续采用视频网站式按需 Range，不增加“点击后才拉流”的额外门槛。远端 session 的单次 Range 响应上限为 32 MiB，避免浏览器的开放区间请求让 CloudDrive 一路读到文件尾；移动端 390 px 下，结果数与排序拆成两行，排序横向滚动，禁止按钮逐字换行。
- Peach 测试唯一入口是 `python -m unittest discover -s tests -v`；仓库不依赖 `pytest`。健康检查端点是 `/healthz`，不是 `/health`。
- Windows 千兆线路理论上限约 125 MB/s。115 实测单文件由 CloudDrive 启动 2 条约 2 MB/s 的 CDN 连接；`max_download_speed_kbyps=0` 表示未设本地限速。卡顿排查先看 FlowLens 是否存在关闭详情后仍下载的旧连接，再查 Range/缓存，不把单连接速度直接归因于本地带宽。

## 恢复入口

项目重构时已从活动目录删除 deprecated 脚本和按日期文档，Git 历史仍可恢复。旧 `_SHARED_STATE` 已迁到 `R:\peach-data\state`。重构前根仓库元数据暂存于 `R:\peach-data\archive\peach-root-repo-backup-20260814`，仅作恢复证据。
