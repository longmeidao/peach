# Peach 交接与长期工作约定

本文件只保存跨任务长期有效的事实和工作规则，不记录逐次聊天流水。每条判据只写一句，
展开的测量值、命令和事故过程放在技能、参考快照、L2 文档和测试里。

## 界面、媒体与复核的既定判据

- 后台任务、进度容器与断线恢复见 `docs/REUSE.md`。

页面密度、控件、提示与响应式的实现门槛见 `.claude/skills/peach-web-ui/SKILL.md`，这里只留代码看不出来的判据。

- 截图与视觉验收的画面保护：审查遮挡（设置面板「安全」组，`#censorSetting`，localStorage `peach-censor`）默认关闭、不在导航栏。只有当本轮截图会交给会审查内容的模型（自动视觉审查或外发工具）时才开启，开完记得关；普通个人浏览一律不遮挡。
- 卡片实体链接必须由同一个 `{kind,name}` 结构生成，不许先独立选显示名、再按别的字段推断类型；账本 `size` 为空或 0 时显示「大小未知」，不伪装成 `0 MB`。
- 排除竖屏是首页取景而不是全局过滤器：`exclude_vertical` 进搜索或实体列表会让按名字搜竖屏视频返回 0 结果，`test_only_the_default_home_list_drops_portrait_videos` 守这条线。
- 竖屏条整行占位并且必须插在行边界上，由 `SHORTS_ROW_OFFSET` 控制插在第几行之后，不额外拉一批视频补上一行余位。
- 关注卡片、标题和 Mix 集合行都先打开站内详情层，可播放媒体走 `/follow-stream`，关闭详情必须停止播放；外部来源页只作详情侧栏的次要入口。
- HLS 分片必须切在真实关键帧上，关键帧表由 `peach.mp4index.keyframe_seconds` 直接读 MP4 的 `moov/stss`；禁止用 `ffprobe -skip_frame nokey`，那会把整个文件解复用一遍，在挂载网盘上等于把片子重拉一遍，读不出关键帧就回退标准 Range。
- 分片用 `-copyts -muxdelay 0 -muxpreload 0` 保持时间戳连续，不用 `-avoid_negative_ts make_zero`（每段都自称从 0 秒开始，拖动进度条会跳错位置）；缓存写在 `stream_root/<asset>/<size>-<mtime>-<秒数>/<index>.ts` 并按最后访问时间淘汰，FFmpeg 并发闸门默认 CPU 核数一半。
- 回收站的物理删除只有 `purge_assets()` 一条实现：先删媒体文件再删账本行，删不掉的整条跳过并在 `blocked` 里回报、前端必须显示；`asset_search` 的 FTS 行由迁移 `0004` 的触发器负责。
- 复核候选文件名带批次日期，代码只认前缀并按实际修改时间取最新一份，不按文件名字典序；候选行必须有稳定主键，缺主键的跳过并计数，绝不退化成行号；候选目录走 `PeachSettings.candidate_root`，不是模块常量。
- `metadata_fields` 的 `item_key` 不带候选身份，一条旧 approved 会盖住之后抓到的新来源值，所以判据是 `review_decision.note` 里记的 `candidate_key` 是否还在这一组：不在就清掉旧判定重新入队，读不出指向的自由文本一律放过。
- 批准的权威值只能来自候选文件本身，请求体里的 `creator`／`tags` 只当确认，不一致直接拒绝；只有 `status=candidate` 的行可批准，未勾选即整条通过但受 `REVIEW_APPLY_LIMIT` 约束。
- 命中推广词不算广告，剥完还剩不剩内容才算：判据在 `web_contract.promo_residue`，`tests/test_ad_judgement.py` 守这条线。`disposal` 同时承载「这是广告」和「这个来源我不喜欢」，不能当纯广告标注集来标定判据。
- 目录多余层的判据是名字冗余而不是「父目录只有一个子目录」，广告标记只剥头尾（`scripts/flatten_release_dirs.py`）；账本只记文件不记目录，任何目录计划落地前都要用真实文件系统复核父目录里有没有旁挂的封面、字幕和空目录。
- 抽帧的 bt709 覆盖只在 stderr 命中坏色彩元数据时重试，无条件重试会让网盘超时的文件每帧白跑第二次，所以不能丢弃 `capture_output` 的错误流。
- Logo 与头像都渲染成方框，候选按实测像素判定，只有 URL 没有实测尺寸不算候选；取源方向、门槛值与站点判据见 `docs/SOURCING.md`。
- 小圆标与厂牌大 logo 是两个位置、两种资产：圆标取站点自己声明的那一份并过内容外接框闸门，宽扁字标不参加圆标竞选，`/logo` 的 `variant` 只在真有两份时才分岔（细节见 `docs/SOURCING.md`）。
- 改了圆标的取图规则或合成方式必须同时加 `link_marks.RENDER_VERSION`：缓存保鲜期 30 天，不换键的话代码换了用户看到的仍是旧那张。
- 图集就是目录：账本没有图集实体，`/api/photos` 按 `path` 去掉文件名分组、ID 取该目录里最小的资产 ID，同名目录在两个来源下算两个图集。瀑布流只读 `/photo-thumb`（Pillow 缩到 640 宽、每张回源一次），原图只在灯箱读；灯箱复用 Swiper，必须等其 CSS 与 JS 都就绪再构造，否则首次打开多图会重叠。
- 人工复核入口固定为 `/review`，候选来自 writer 本机 `generated` 下的 CSV，状态写 `review_decision`；封面抓取的成功、尺寸和缺失是机械状态，不进人工复核。
- reader 只通过 Peach CA 严格校验的 HTTPS 读 writer 已归一化的 JSON 并原子缓存到本机，先确认目标 `/healthz` 是 `ledger_sync=writer`，writer 离线只展示上次缓存；reader 永久禁用批准、跳过、拒绝和关注管理的写入，不得为修空页面而同步整个 `generated`、SQLite/WAL 或放宽写端点白名单。
- 转载站水印域名不是番号：剥掉 TLD 后与 `IPX219C`、`MEYD911` 同形，`normalise_code_key` 会替它补连字符（`HHD800` → `HHD-800`），JAV 过滤、`display_code` 和 `clean_names` 重命名就全把水印当成作品标识。形态分不开，只有实证名单 `catalog_rules.REPOST_SITE_LABELS` 能分，存压缩形让 `BEI88` 与 `BEI-088` 同命中；加条目先用 `scripts/audit_domain_codes.py` 在真实 ledger 取 `<label>.<tld>` 或 `<label>@` 的路径证据。
- 「什么算番号」只在 `catalog_rules` 一份，脚本一律 import，同一条排除规则只加在其中一份上等于没加；改 `code` 走 `audit_domain_codes.py --apply --backup`，只写复核过的那份 CSV、按原值 `WHERE` 挡住漂移、存疑档不写，FTS 由 `AFTER UPDATE OF name,code` 触发器重建但要核对真跑过。
- 日文标题只认官方源会漏掉 DMM 未收录的作品，这类番号用 `--sources javbus` 单独补候选并写进分区文件，不另起通用批次——复核页只读最新一个通用批次，新文件会把上一批未复核的行挤掉。

## 无摩擦接手

- Codex 自动读取项目层级中的 `AGENTS.md`；Claude Code 通过 `CLAUDE.md` 导入同一文件。技能只有 Claude 侧封装（`.claude/skills/`），Codex 不自动加载，只能靠 `AGENTS.md` 索引表主动读同一份文件。
- 正式测试入口只有 Windows `& .\scripts\test.ps1` 和 macOS/Linux `./scripts/test.sh`，不要另拼测试命令。日常用 `-Scope <域>` / `<域>` 只跑当前功能与公共门槛；跨域、迁移、共享测试设施、依赖、构建/发布或大面积改动跑默认 `full`。
- 两个智能体使用同一入口，按任务读取相关文档；交接更新长期文件。
- 新任务以当前机器真实的 `peach-app` 为工作目录，并说：「接手 Peach，按项目入口文件继续 STATUS 中的下一任务。」
- 改变运行事实的任务同时更新 `docs/STATUS.md`；长期规则更新本文件、`docs/REUSE.md` 或 ADR；可执行流程写成 `.claude/skills/<name>/SKILL.md`。分层判据见 ADR-0015，步骤见 `peach-context-rules`。
- 触发是概率性的：必须每次成立的规则要由脚本、测试或 hook 强制，不能只写成技能。
- 用户不是消息中转站。结论、进度、待办和证据必须写入共享文档或机器可读产物。

## 并行智能体与 Git 工作树

操作步骤与平台陷阱统一见 `.claude/skills/peach-worktree/SKILL.md` 和
`.claude/skills/peach-cross-platform/SKILL.md`。保留的事故证据只有 `bba0b77`：测试先提交、实现漏暂存，
因此隔离工作树、逐文件暂存复核和实现/测试原子提交是强制边界；其余已由脚本或测试守住的复盘从常驻上下文清退。

## 只存在于聊天中的结论等于不存在

- 复核结论写入带证据和来源的 CSV 或其他持久产物；真实 ledger 写入须另满足授权与备份门槛，执行后对账。
- 结论被修正时所有派生产物必须重建，只改说明文字不够：过期的删除清单比没有清单更危险。
- 直接证据：视觉逐条任务在聊天里说「已保存」但 `asset_tag` 的 `source='vision'` 为 0，根本没有写入步骤；`disposal-candidates.csv` 在 `BNST033` 修正后未重建，把真实 3.2 GB 正片列为待删。
- 解析用的固定件必须是抓回来的那份 HTML，不能照记忆重画：那样只能证明代码和记忆一致，会出现测试全绿而线上一个字段都没采到（实例见 `docs/SOURCING.md`）。
- Claude 的 `.claude/settings.json` 配了 Stop、StopFailure、SessionEnd hook，用 `${CLAUDE_PROJECT_DIR}/.venv/Scripts/python.exe` 调 `scripts/job_status.py --write --hook-event`：只记脱敏生命周期摘要，重新从 ledger 与产物算数字，原子写入 `peach-data/state/job-status.md`，不复制 prompt、response 或凭据。
- 那份产物不进 Git，`docs/STATUS.md` 只留一行指针；隔离工作树没有 `.venv`，工作者会话不写这份状态，机器级进度只由主检出的会话记录。强制杀进程或断电时 hook 不运行，下次调用会补上。

## 中文文档写作规范

- 全部中文内容（README、`docs/`、ADR、技能正文、界面文案）按用户级技能 tech-doc-style-chinese 写作：
  事实优先、可扫读、不新增原文没有的数字与结论；规则只作用于可见正文，代码、路径、字段和命令原样保留。
- 来源 https://github.com/Fenng/Tech-Doc-Style-Chinese （MIT），本机装在用户级 `skills/tech-doc-style-chinese`（upstream `a6f5b60`，2026-08-07）；Codex 自行安装到 `$CODEX_HOME/skills/` 同名目录。
- 检查器两层：用户级 `scripts/lint_copy_rules.py` 用主项目 venv 跑，参数 `README.md AGENTS.md docs
  .claude\skills`，`error` 清零、`style` 人工判断，不是门槛；`scripts/check_copy_final_state.py`
  是门槛，判据与放行标记见 `peach-context-rules`。
- Peach 覆盖上游默认三处：智能体入口文件保留称呼「你」（术语表已定义其含义）；`DOM/CSS/JS` 是证据 <!-- copy-lint-disable-line -->
  三元组的固定写法，不展开成 JavaScript；`对齐`、`复盘` 是已注册的项目术语与技能触发词，不替换。
  其余上游黑话词（兜底、落盘、闭环、链路）一律改写成具体机制。

## 参考产品证据登记

快照、URL、版本、SHA、未取得面与 Peach 的有意差异统一登记在 `docs/reference-sources.json` 和
`docs/reference-snapshots/`，每份快照自带「Peach 采用与差异」一节；获取、失效复核与接受更新的流程见
`.claude/skills/peach-reference-evidence/SKILL.md`。本文件不复制会随上游变化的测量值，只登记哪件事看哪份快照。
React 渲染的规格页、用户截图这类给不出可重抓字节的实测不进登记表，但要在快照正文写明理由——`tests/test_reference_updates.py` 会拒绝既没登记也没说明的快照。

- 相关推荐算法：`openaver-related-ranking`，固定 revision，只参考 Tag IDF 与结构化共同点，MMR 和稳定破同分是 Peach 自加，不复制上游界面或源码。
- 网格、控件半径、语义 token 与中间省略：`vercel-geist-grid`、`vercel-geist-controls-measured`、`vercel-geist-middle-truncate`；中间省略只用于路径、URL、ID、SHA 这类首尾都有信息的值，必须显式 `data-middle-truncate`，标题、说明、人名和标签保留末尾省略。
- 统计与口味两页的层级，Note／Progress／Switch／Fieldset／Scroller／Empty State 的语义，按钮尺寸档与三态、主题选择器与下拉几何：`vercel-geist-semantics-measured`、`vercel-geist-note-progress-switch-analytics`、`vercel-geist-fieldset-scroller-empty-state`。
- 分类切换条属于 Tabs 的 secondary 变体而不是分段器：`vercel-geist-tabs-secondary-measured`。
- 表格、排行与面包屑：`vercel-geist-table-ranking`、`vercel-geist-breadcrumbs`；同形可比较数据才用语义 `table` 并保持 tabular numerals，内容标签是固定 Top 排行和直接筛选，不伪装成可排序数据表。
- 设置 Dialog 动效、搜索期 Spinner、后台 Loading Dots 与 busy 按钮：`vercel-geist-command-search-loading`；中性说明 Note：`vercel-notifications-note`；具名动作 Toast：`vercel-geist-toast`；写操作前的确认弹层：`vercel-geist-modal-measured`。
- 资料页阅读顺序与照片入口：`beeg-profile-layout`；JAV 标题显示语义：`jav-title-user-screenshot`；卡片悬停的快退／快进控件：`hover-seek-controls-user-screenshot`（beeg 现网没有这个控件，只依据用户截图）。
- 播放器控制栏、设置浮层、影院与全屏几何：`youtube-player-controls-user-screenshot`；沉浸页版式：`youtube-shorts-immersive-user-screenshot`；播放统计滚动历史：`youtube-stats-buffer-measured`。Peach 不复制没有实际能力的字幕、睡眠定时或自动播放按钮。
- 追更与文件站的凭据与解析边界：`f95-masked-gofile-media`、`follow-fanbox-gofile-paheal`、`fanbox-browser-transport`、`rule34-follow-tags-and-collections`；厂牌 Logo 候选发现：`fiu758-studio-logo-discovery`，只作发现来源不作真相源。
- 通用评审清单与报告型页面版式：`vercel-web-interface-guidelines`、`vercel-report-design`（`vercel.com/design.md`）。
- 默认 Note、只读提示和 info 入口统一复用本地 Lucide 圆圈 `i`，显式使用 2px 描边与圆端点保证圆点可见，不复制未开放许可的 Geist 私有 SVG。
- 沉浸与详情播放每次加载都带独立 `session`，切片、关闭、失败和页面离开时取消旧会话：只清浏览器的 `src` 不足以停止 CloudDrive 预读或 FFmpeg。Mix 只按已解析且可播放的视频计数，不按回复数或网盘页数计数。
- FANBOX 正文统一先经过 `peach.fanbox.normalize_fanbox_post`，数据模型固定参考 PixivUtil2 `v20251112` / `e537e96`：只有图片和视频进入可切换媒体，压缩包等文件只留资源链接，重复 URL 按正文首次出现顺序去重。
- FANBOX Cookie 与 Gofile token 都是本机可选凭据，只进各自站点的请求头，不进 URL、证据、ledger 公开投影或浏览器 JSON；只允许公开 JSON，不解机器人质询、不执行网页脚本、不读付费内容。
- Gofile 当前把 contents API 限给 Premium：`error-notPremium` 要按套餐限制报告，不能误报成 token 无效；未取得文件列表时保留分享页，不得声称已经取得视频。
- 同一篇 FANBOX 可含多个 Gofile 文件夹：作品级仍是一个来源合集，媒体保留文件夹 id 与正文标签并在详情队列内分段，不拆作品也不压平混排。

## 批处理边界

失败值、磁盘闸门、限流、续跑、流量与进程规则统一见
`.claude/skills/peach-batch-jobs/SKILL.md`；当前批次数量与运行进度只写 `peach-data/state/job-status.md`。

- 采集脚本的整页 HTML 缓存与限速集中在 `peach.page_cache.Site`：判据改一行就要重跑，缓存在手才能让重跑读离线数据、不再打外站。
- 传输错误由 `Site` 自己退让重试，采集脚本不必各写一遍；HTTP 状态码不重试，404 重试三次仍是 404，只是白花三倍流量。

## 身份、来源与标识采集

判据细节、实测反例、判词含义和不能走的路见 `docs/SOURCING.md`，这里只留边界。

- 采集脚本一律只产出复核 CSV；写 `entity.canonical_name`、`asset.studio`、`entity_link` 或头像字节都是另一次授权。
- 规范名优先用有出处的简体中文通行名，旧艺名、罗马字、假名和繁体名降为别名；`no_avatar` 只表示没取得合格图片，不阻止已核实姓名落库。
- 实体合并不可逆：走 `peach.entities.merge_entity`，必须先取得用户授权、先备份，合并后 `PRAGMA foreign_key_check` 应为 0；改写 `entity.canonical_name` 与迁移同级，`--apply` 必须同时给 `--backup`。
- 「这一页只有一位女优」「这个 handle 存在」「站上没有」都不是证据：精确回配优先于任何唯一性推断，二手结论要自己请求一次才算取证，查不到就写「未取得」。
- 名字与厂牌名都由站点给出，不由罗马音或 slug 推定；一律跨来源同证，单页 404 只说明那一页取不到。
- 被 Cloudflare 拦或有验证墙的站一律放弃，不绕过机器人检测。

## 流量与代理诊断工具

- 抓取与 Cookie GUI 见 [审计](SCRAPING_AUDIT.md)。

- Windows 用 FlowLens（`http://127.0.0.1:9091/`；API `/api/v1/connections`、`/summary`、`/status`）查流量。经 Mihomo 的 `DIRECT` 可观测；绕过它的记「未观测」，不推断为零。
- macOS 的流量诊断统一使用 Stash Dashboard。

## 数据安全

- 真实 ledger 是当前写入者本机 `peach-data/database/ledger.db`（WAL 模式），正常浏览会合法写入播放与行为字段；平台绝对路径以 `docs/STATUS.md` 为准。
- 测试必须使用临时 SQLite、媒体和全部缓存根，不得写真实 ledger 或 `generated`；FastAPI 测试须显式传入 snapshots、posters、photo-thumbs、transcodes、stream-segments、按 asset 生成的头像与 covers。
- 可重建缓存的删除边界由当前数据库路径拥有，生产库只可清理同一 `peach-data` 下的缓存，边界外一律跳过：一次漏配曾在清空回收站的测试里删掉真实 JAV 封面。
- 已应用的迁移文件不得修改，任何后续变更必须新增版本；真实迁移与缓存删除的操作序列见 `docs/OPERATIONS.md`。
- 外键 `ON DELETE` 是安全网不是删除路径：运行时连接不开 `PRAGMA foreign_keys`，物理删除仍走 `ASSET_REFERENCE_TABLES` 与 `web_playlists` 的显式 DELETE；重建被别人引用的父表要在迁移首行写 `-- peach:foreign_keys=off`，改名那步开 `PRAGMA legacy_alter_table=ON`，判据见 `0025`。
- 外置盘目标只保存 `media`，代码、运行数据、venv 和 worktree 在两台机器各自的内置盘；`peach-data` 不进入仓库，也不整体交给文件同步，分通道边界见 ADR-0017。

## 运行与部署

命令、顺序、失败表现和踩过的坑见 `docs/OPERATIONS.md`，这里只留边界。

- 源码部署由项目 venv 持有服务，刷新入口为 `scripts/restart_windows_tray.py`。独立测试包自带运行环境，数据在用户目录；配置更改由托盘消费标记并重启子服务。
- 「同步开发进度」（GitHub）和「同步 Ledger」（SMB 共享）是两条独立通道，任一方不可达都不该拖住另一方；服务只观察角色不自动复制。
- 两台机器可以同时跑服务，但同时写入会很快冲突转只读；「接管 Ledger 写入」的短路与拒绝条件见 OPERATIONS。
- `src/peach/__init__.py::__version__` 是版本唯一来源；自动更新只做 `merge --ff-only`，不 stash、不 rebase、不 `--force`，工作区脏或两边分叉就原样报出来交给人——并行工作树和主检出共用同一个对象库。
- 本机坐标在 `<数据根>/config.toml`（环境变量 > 它 > 内建默认），`src/peach/` 不写死本机字面量或家庭 IP。`[media.mounts]` 按 `asset.location` 给本机落点，Windows 上整表为空；`replication.enabled` 默认关，关掉即整条复制链路不装配。首次运行问答与扫描是 `peach.onboarding`／`peach.scan` 的纯逻辑，CLI 与托盘设置页共用。
- `.local` 用本机 CA 而不是 Let's Encrypt，证书与私钥留在本机 `peach-data/secrets` 且按设计不跨机共享；FastAPI 是唯一 Web server，探测本机服务必须绕过系统代理，否则代理会替服务回 503。
- 网盘目录整理后必须经「管理 → 资源同步」显式对账，不做后台静默删除；源文件缺失的 asset 和垃圾文件候选都只能先进回收站，清空回收站才永久删除账本行。
- 长任务只停止自己拥有且命令行匹配的 Python/FFmpeg 进程树，禁止全机终止 FFmpeg；转码只写缓存，永不改写原媒体。
- 验证分开报告：静态/单元/API、桌面浏览器、390×844 手机、生产服务是否已重启。

## 当前架构真相

- Ledger 拥有真相和行为；服务运行期媒体解析只有文件系统一条路径，ADR-0021 已删 Stash 适配层，`src/peach/stash.py` 仅剩两个离线导入脚本使用。
- 规范女优、厂牌、标签、创作者进入 `entity`、`entity_external_ref`、`asset_entity`；扁平 `asset_tag` 和 creator/studio 字段只是兼容投影。
- FastAPI 与前端保持单体部署，在线来源和 AI 只通过显式适配器进入；AI runtime 与推理 API 的协议边界见 ADR-0003。
- 前端按 ADR-0022 走 strangler 迁移：新逻辑进 `frontend/` 的 Vite + TypeScript + Preact 岛，按岛替换现有页面，不做整站重写；面向陌生人分发的阶段划分见 ADR-0023。
- 当前页面、路由、交互与性能实现只写 `docs/STATUS.md`，由 API 和 `tests/test_web_ui.py` 守住；本文件不复制易过期的版本号、像素值和控件清单。
- `/taste` 只读合并 Peach 行为与本机私有浏览历史，明确以浏览器记录为主要画像、Peach 内部为辅助证据，两者分别排序，不把「不合口味」自动归因或降权到 Tag。
- 查询词里的负号项整体排除，下划线是组合词边界的一部分，不得把 `-ai_generated` 拆成正向 `generated`；模糊时长旧 Tag 只作兼容识别，不进入口味、索引、详情和筛选状态。
- 原始 URL 与标题不进入页面或 ledger；上传原件保存在 `sources/taste-history/imports`，移除数据源只清理规范化分析库，不删原件。浏览器数据库解析固定复用 `browserexport==0.4.4`，运行中浏览器先由 SQLite backup API 取一致快照。本机发现不等于跨机同步，跨机数据要显式导出、传输并按来源去重合并。
- 追更连接器、凭据、变体和跨站归组以 ADR-0019 为准；关注页顶部标签筛选与卡片只用来源明确标记为 `general` 的内容标签，详情页与在线索引保留全部来源标签并按类型着色，未知类型不猜成 `general`。
- 自动追更固定使用 APScheduler 3.11.3，只在 ledger writer 启动，频率保存在 `peach-data/state/follow-schedule.json`，默认每小时且启动后等待一个完整间隔，不要改成启动即抓；任务保持 `coalesce=True`、`max_instances=1`，与手动检查共用 `WebContract.follow_check_lock`，reader 只显示不可用状态。
- 账本路径兼容和抽帧失败处理统一见 `.claude/skills/peach-cross-platform/SKILL.md` 与 `.claude/skills/peach-batch-jobs/SKILL.md`。

## Web 性能边界

- 列表必须分批构建；首批才计算总数，后续多取一条判断是否还有下一页。无限滚动同一时间只允许一个追加请求。
- 聚合查询禁止按实体发 N+1 SQL；相邻请求可复用缓存，但异步响应必须核对请求序号和当前路由，旧响应不得覆盖新页面。
- 远端媒体 hover 只读本地预览；离开详情、换页或替换 DOM 时停止播放并取消当前 stream session，不能让 CloudDrive 继续读盘。
- 当前批量大小、播放器版本、像素值与性能测量属于实现快照，统一留在测试、`docs/STATUS.md` 或参考快照，不写入长期上下文。

## 恢复入口

项目重构时已从活动目录删除 deprecated 脚本和按日期文档，Git 历史仍可恢复。旧 `_SHARED_STATE` 和重构前的
根仓库元数据备份都在各机 `peach-data` 的 `state`／`archive` 下，只作恢复证据；那两个目录的当前位置以
`docs/STATUS.md` 为准，Mac 的 `archive` 是指向外置盘的符号链接，盘不在时读不到不等于备份没了。
