# Peach 交接与长期工作约定

本文件只保存跨任务长期有效的事实和工作规则，不记录逐次聊天流水。

## 界面、媒体与复核的既定判据

- 卡片实体链接必须由同一个 `{kind,name}` 结构生成，禁止先独立选择显示名、再根据其他字段推断类型。此前 `FSDSS-376-C.mp4` 显示演员 `新ありな`，却因同时存在厂牌而生成 `/studios/新ありな`；真实 ledger 关系是演员 `新ありな`、厂牌 `FALENO`，错误只在前端映射。
- 卡片悬停控件出现时暂隐来源徽标和时长，避免两层信息互相遮挡；账本 `size` 为空或 0 时显示「大小未知」，不能伪装成 `0 MB`。标准卡标题保留固定两行高度，小图固定一行，防止同一网格上下跳动。
- 关注卡片、标题和 Mix 集合行都先打开 Peach 站内详情层；可播放媒体继续走 `/follow-stream`，关闭详情必须停止播放。外部来源页只作为详情侧栏里的次要入口，不能替代站内详情或成为卡片主点击行为。
- 竖屏条整行占位（`grid-column:1/-1`），必须插在行边界上。曾经的做法是另拉一批横屏视频补满上一行余位，那批 ID 不在分页序列里，翻页必然出现重复卡，而且被当作 `scard` 渲染会把横屏画面压成竖框。行边界插入不额外请求、不重复；`SHORTS_ROW_OFFSET` 控制插在第几行之后。
- 排除竖屏是首页取景，不是全局过滤器。任何把 `exclude_vertical` 加进搜索或实体列表的改法都会让按名字搜一条竖屏视频返回 0 结果，`test_only_the_default_home_list_drops_portrait_videos` 守这条线。
- HLS 分片必须切在真实关键帧上。`-c copy` 只能在关键帧处下刀，而按固定 6 秒等分写播放列表会和实际切点对不上——实测本地片源有每 8.33 秒才一个关键帧的，目录说「6–12 秒」实际给的是别的区间，表现为进度条错位、段间画面重复或跳过。关键帧表由 `peach.mp4index.keyframe_seconds` 从 MP4 的 `moov/stss` 直接读出（0.01 秒量级），**不要用 `ffprobe -skip_frame nokey`：那会把整个文件解复用一遍，在挂载网盘上等于把片子拉一遍，正好抵消分片省流量的目的**。`moov` 可能在文件尾部，按 box 头 seek 定位，不要顺序读。读不出关键帧就返回 None 回退标准 Range，不猜。
- 分片用 `-copyts -muxdelay 0 -muxpreload 0` 保持时间戳连续。早先的 `-avoid_negative_ts make_zero` 让每段都从 0 秒开始自称，拖动进度条时容易跳错位置、音画不同步。
- 分片缓存写在 `stream_root/<asset>/<size>-<mtime>-<秒数>/<index>.ts`，不随响应删除：回放、断线重连和多设备都会重复请求同一段，每次重跑 FFmpeg 等于让 CloudDrive 再预取一次块。缓存按最后访问时间淘汰，指纹带文件大小和 mtime，换了片源自然失效。FFmpeg 并发有信号量闸门（默认 CPU 核数一半），播放器本身就会并发预取多段。
- 回收站的物理删除只有一条实现：`purge_assets()`，`/api/batch` 的 `delete` 和 `/api/trash/empty` 共用它。顺序固定为先删媒体文件、再删账本行，删不掉的文件整条跳过并在 `blocked` 里回报，前端必须把 `blocked` 显示出来。反过来先删行会留下没人认领的媒体文件，那是真正不可恢复的丢失；留一条指向缺失文件的回收站行至少还能看见和重试。`asset_search` 不列入 `ASSET_REFERENCE_TABLES`，FTS 行由 `0004` 的删除触发器负责。
- 复核候选文件名带批次日期，代码里只认前缀并取目录里最新的一份；把日期写死会让下一批生成后页面静默变空。候选行必须有稳定主键（`board`/`studio`/`entity_id`），缺主键的行跳过并计数，绝不退化成行号——行号会在 CSV 重排后把历史决定挪到别的条目上。候选目录走 `PeachSettings.candidate_root`，不是模块常量，否则测试会读到本机真实的 `peach-data/generated`。
- 批准的权威值只能来自候选文件本身，请求体里的 `creator`/`tags` 只当确认，不一致直接拒绝；只有 `status=candidate` 的创作者候选可以批准，`skip` 行必须在页面禁用批准。否则「批准候选 X」能写入与 X 无关的标签，而 `review_decision` 留痕仍写着 X 通过——留痕说通过、实际写了别的，是最糟的组合。未勾选即整条通过，但受 `REVIEW_APPLY_LIMIT` 约束，超限必须显式勾选。
- **命中推广词不算广告，剥完还剩不剩内容才算**。判据在 `web_contract.promo_residue`：先去掉域名和联系方式套话，再数剩下的中日韩文字与字母。`点击观看 房间火爆` 剥完什么都不剩，`236953.xyz 推特新晋…「一个ren」《榨精美足》` 剥完仍是大段描述——后者是被打了站点水印的正片。三类实测误判据此排除：剧情里的「微信」（`还要微信跟老公汇报战果`）、开头是盗版站域名但正文真实、以及拿创作者账号名当番号比时长（`RAIKUN325` 不是番号，`REAL_CODE` 用与 `is_jav_code` 同一条分隔符规则挡掉）。域名正则结尾不能用 `\b`：`uuc82.com_2` 里 `m` 和 `_` 都是词字符，构不成边界。另外 `disposal` 同时承载「这是广告」和「这个来源我不喜欢」两种意图（`1726897607_*` 那批属后者），不能当作纯广告标注集来标定判据。`tests/test_ad_judgement.py` 守这条线。
- 抽帧的 bt709 覆盖重试只针对坏色彩元数据（stderr 命中 `reserved/unsupported/invalid` + 色彩词）。无条件重试会让网盘超时这类必然失败的文件每帧白跑第二次，单帧最坏耗时从 45 秒翻到 90 秒。判据依赖 stderr，所以不能丢弃 `capture_output` 的错误流。
- Logo 与头像在界面上都渲染成方框（厂牌方图、女优 160×160 圆头像），候选按实测像素比例处理，判据在 `peach.images.classify`：长宽比 ≤1.35 直接用，更长的补自身四角底色填成正方形（`pad_to_square`，不是刷白也不是裁切），短边 <128 才拒绝。只有 URL 没有实测尺寸不算候选。
- **AV 厂牌 Logo 的来源是厂牌自己的社交账号头像**：社交头像天然是正方形且由品牌本人发布。取证顺序是 handle → `unavatar.io` 解析出平台 CDN 真实地址 → 从 CDN 下载 → 实测，unavatar 只用于解析地址，provenance 两者都记（`scripts/fetch_studio_avatar_candidates.py`）。候选使用内容寻址缓存、SHA-256、同厂牌感知哈希和跨厂牌精确重复门槛；同图缩放/重编码记 unchanged，上游视觉真变化才重新进入 `/review`。无 handle、无图片、unchanged 和 duplicate 只写健康报告，不占人工队列。r18.dev 详情 JSON 只有 `maker.name`/`label.name` 和作品封面，没有 Logo 资源，已排除。
- **能解析不等于是对的品牌**：`@bazooka` 确实存在且能取到 400×400 头像，但那是 2007 年注册的通用账号，不是这个 AV 厂牌；Wikimedia 搜同名也给出 16:9 的泡泡糖品牌图。所以 handle 必须逐个取证确认，脚本默认不猜，`--guess-handles` 的产出一律标 `needs_confirmation` 且不自动采纳。查不到就留空。
- 社交 handle 只采信**厂牌自有域名页面上**的链接。日文维基条目的外链里混着引用来源的新闻站，直接抓会把新闻站自己的账号当成厂牌的——实测 `妄想族` 条目就抓出了 `@news_postseven` 与 `@taishurxjp`。官网链接也不必然指向主号：`gloryquest.tv` 链的是 `@lG_Ql`「社内クリエイティ部（BOT）」，头像压着 18+ 徽标，反而不如 `@gloryquest_av` 的干净字标合适。所以官网只用来确认归属，选哪个号仍要看图。
- AV 厂牌官网普遍先给年龄确认页，不穿过它只能拿到约 10 KB 的空壳。判据必须是锚文本而不是 URL：否定链接指向站外（实测 `dasdas.jp`、`muku.tv` 的「いいえ」都指向 dmm.com），肯定链接「はい（入室する）」指向站内，两者的 href 看不出区别。跟错就离开了厂牌域名，抓到的账号也就不再属于这个厂牌。实现见 `scripts/find_studio_socials.py`，`test_age_gate_is_crossed_by_the_affirmative_link_only` 守这条线。
- 二手结论不能当证据：搜索摘要曾称 `@EBODY_` 已注销，实测直接解析到 400×400 活跃头像。凡是「某账号/端点已失效」这类判断，取证方式是自己请求一次，不是转述搜索结果。
- **图集就是目录**：账本没有图集实体，也不需要一个。`<作品目录>\P\001.jpg` 这种约定在 A:/B: 上到处都是，所以 `/api/photos` 按 `path` 去掉文件名分组，图集 ID 取该目录里最小的资产 ID——稳定、可反查目录，又不用把真实路径发给前端（和 `q_item` 一致）。同名目录在两个来源下算两个图集：文件不同、计费口径也不同。叶子目录只写 `P`、`图片` 这类通用名时，标题取上一级目录名。
- **瀑布流只读缩略图，原图只在灯箱里读**。图片资产没有接触印相可裁，只能读原图；PikPak 一张动辄几 MB，一屏几十张就是几十兆计费流量。`/photo-thumb` 用 Pillow 缩到 640 宽存进 `photo_root`，每张只回源一次，`/photo` 只服务灯箱当前和相邻的大图。瀑布流用 CSS `column-count`：图片行没有 `width`/`height`，等宽多列流式排版正好不需要比例，也就不必等图加载完再算位置。
- 人工复核入口固定为 `/review`，候选 API 为 `GET /api/review`、`POST /api/review/decision`。候选来自 writer 本机 `peach-data/generated` 下的 CSV；每项尽量带代表封面与原视频入口，审核状态写 `review_decision`。元数据与创作者标签批准后写相应真相/投影，Logo、头像、身份和媒体失败只记录决定；封面抓取的成功、尺寸和缺失是机械状态，不进入人工复核。双机同时在线时，reader 的 `GET /api/review` 只通过 Peach CA 严格校验的 HTTPS 读取 writer 已归一化 JSON，先确认目标 `/healthz` 是 `ledger_sync=writer`，绕过外网代理并原子缓存到本机 `review/writer-review.json`；macOS 合并文件 CA 与系统/登录钥匙串中受信任的同名 Peach CA，只读取公钥证书，不导出私钥。launchd 主体被本地网络权限挡住时，使用系统 `/usr/bin/curl` 经回环 Stash 代理发起同一严格请求；仅限 HTTPS、8 MiB 上限，令牌走 stdin，非回环代理拒绝。writer 临时离线时只展示上次缓存。reader 永远禁用批准、跳过和拒绝，关注管理也禁用新增、检查、移除和凭据修改，并链接到 writer。不得为修复空页面而同步整个 `generated`、SQLite/WAL，或把真实写入端点加入 reader 白名单。

## 无摩擦接手

- Codex 自动读取项目层级中的 `AGENTS.md`；Claude Code 通过 `CLAUDE.md` 导入同一文件。
- 正式测试入口只有 Windows `& .\scripts\test.ps1` 和 macOS/Linux `./scripts/test.sh`；不要另拼测试命令。日常用 `-Scope <域>` / `<域>` 只跑当前功能与公共门槛；跨域、迁移、共享测试设施、依赖、构建/发布或大面积改动跑默认 `full`。
- 两个智能体使用同一入口、同一必读顺序，不再生成按日期命名的临时交接文档。
- 新任务以当前机器真实的 `peach-app` 为工作目录，并说：「接手 Peach，按项目入口文件继续 STATUS 中的下一任务。」不得把 Windows 迁移前的 `R:\peach-app` 当跨平台固定路径。
- 改变运行事实的任务同时更新 `docs/STATUS.md`；长期规则更新本文件、`docs/REUSE.md` 或 ADR；可执行流程写成 `.claude/skills/<name>/SKILL.md`。分层判据见 ADR-0015，步骤见 `peach-context-rules`。
- 七个技能只有 Claude 侧封装（`.claude/skills/`），Codex 不自动加载，只能靠 `AGENTS.md` 的索引表主动读取同一份文件。Codex 侧封装的做法与验收写在 `docs/STATUS.md` 的下一批工作，本文件不复制第二份。
- 无论哪个 harness，触发都是概率性的：必须每次成立的规则要由脚本、测试或 hook 强制，不能只写成技能。
- 用户不是消息中转站。结论、进度、待办和证据必须写入共享文档或机器可读产物。

## 并行智能体与 Git 工作树

操作步骤与平台陷阱统一见 `.claude/skills/peach-worktree/SKILL.md` 和
`.claude/skills/peach-cross-platform/SKILL.md`。保留的事故证据只有 `bba0b77`：测试先提交、实现漏暂存，
因此隔离工作树、逐文件暂存复核和实现/测试原子提交是强制边界；其余已由脚本或测试守住的复盘从常驻上下文清退。

## 只存在于聊天中的结论等于不存在

- 得出结论的同一步必须写入 ledger、CSV 或其他持久产物。
- 结论被修正时，所有派生产物必须重建；只改说明文字不够。过期删除清单比没有清单更危险。
- verdict 旁必须保存证据和来源；完成前把声明意图与数据库实际行对账。
- 历史视觉逐条任务曾在聊天里说「已保存」，但 `asset_tag` 中 `source='vision'` 为 0；根因是根本没有写入步骤，不是模型拒绝。
- `disposal-candidates.csv` 曾在 `BNST033` 判断修正后未重建，仍把真实 3.2 GB 正片列为待删；这是必须同步所有派生产物的直接证据。

Claude 的 `.claude/settings.json` 已配置 Stop、StopFailure、SessionEnd hook，调用 `scripts/job_status.py --write --hook-event`。脚本只记录脱敏生命周期摘要，重新从 ledger/产物计算数字，并原子更新 `docs/STATUS.md` 的 `<!-- job-status -->` 受管区块；不复制 prompt、response 或凭据。强制杀进程/断电无法运行 hook，下次调用会修复计数。Codex 暂无等价项目结束 hook，仍由协调者在同一改动里更新文档；不要用脆弱日志监听器模拟。

## 中文文档写作规范

- 全部中文内容（README、`docs/`、ADR、技能正文、界面文案）按用户级技能 tech-doc-style-chinese 写作：
  事实优先、可扫读、不新增原文没有的数字与结论；规则只作用于可见正文，代码、路径、字段和命令原样保留。
- 来源 https://github.com/Fenng/Tech-Doc-Style-Chinese （MIT），本机已安装到
  `%USERPROFILE%\.claude\skills\tech-doc-style-chinese`，对应 upstream commit `a6f5b60`（2026-08-07）。
  Claude 按 description 自动加载；Codex 需自行安装一份到 `$CODEX_HOME/skills/tech-doc-style-chinese`：
  `npx -y skills add https://github.com/Fenng/tech-doc-style-chinese -a codex -g`，或按同名目录 `git clone`。
- 检查器是该技能目录下的 `scripts/lint_copy_rules.py`，用主项目 venv 跑，参数 `README.md AGENTS.md docs
  .claude\skills`。它只覆盖高频规则，`error` 必须清零，`style` 提示需人工判断，不作为提交门槛。
- Peach 覆盖上游默认三处：智能体入口文件保留称呼「你」（术语表已定义其含义）；`DOM/CSS/JS` 是证据 <!-- copy-lint-disable-line -->
  三元组的固定写法，不展开成 JavaScript；`对齐`、`复盘` 是已注册的项目术语与技能触发词，不替换。
  其余上游黑话词（兜底、落盘、闭环、链路）一律改写成具体机制。

## 参考产品证据登记

具体快照、URL、版本、SHA 与 Peach 差异统一登记在 `docs/reference-sources.json` 和
`docs/reference-snapshots/`；获取、失效复核与接受更新的流程见
`.claude/skills/peach-reference-evidence/SKILL.md`。本文件不再复制会随上游变化的测量值。
**Vercel Geist Grid（2026-08-28）**：官方页 `https://vercel.com/geist/grid` 的实时 DOM 使用资源类
`grid-module__AMTIxG__grid`；网格引导线由父级统一拥有，单元透明、0 圆角，示例按阅读顺序逐行排列，
并明确要求各断点可预测重排、可点击单元独立显示 focus。Peach 复用共享边线与 3／2／1 列重排，
但 Tag 仍保留 6px 小圆角，普通排行不复制演示页的大留白或装饰性引导线。
YouTube Shorts 沉浸页使用用户截图记录 `docs/reference-snapshots/youtube-shorts-immersive-user-screenshot.md`：竖屏复用中央 9:16 舞台和外置动作列，横屏使用在整个视口视觉居中的 16:9 舞台并把动作列收进视频右侧；Peach 保留自己的反馈语义，不复制订阅或社交动作。沉浸视频每次加载都要带独立 `session`，切片、关闭、失败和页面离开时取消旧会话；只清浏览器的 `src` 不足以停止 CloudDrive 预读或 FFmpeg。
F95 masked 链接与 Gofile 文件列表的凭据边界见 `f95-masked-gofile-media`；Mix 只按已解析且
可播放的视频计数，不按回复数或网盘页数计数。
FANBOX 多图、Gofile Bearer API、Paheal 标签页与跨站出处键见
`follow-fanbox-gofile-paheal`。FANBOX Cookie 是本机可选凭据，只发给 FANBOX API；
FANBOX `post.info` 的 Firefox 传输边界与复用依据见 `fanbox-browser-transport`；只允许公开
JSON，不解机器人质询、不执行网页脚本、不读取付费帖子。
FANBOX 正文统一先经过 `peach.fanbox.normalize_fanbox_post`：数据模型固定参考 PixivUtil2
`v20251112` / `e537e96`，覆盖 image/text/file/article/video/entry 及各类 map；只有图片和视频
进入可切换媒体，压缩包等文件只保留为资源链接，重复 URL 按正文首次出现顺序去重。
Gofile token 是另一份本机可选凭据，只进 Gofile 请求头，不进 URL、证据、ledger 的公开投影
或浏览器 JSON。Gofile 当前把 contents API 限给 Premium；`error-notPremium` 要按套餐限制
报告，不能误报成 token 无效。未取得文件列表时保留分享页，不得声称已经取得视频。

## 批处理边界

失败值、磁盘闸门、限流、续跑、流量与进程规则统一见
`.claude/skills/peach-batch-jobs/SKILL.md`；当前批次数量与运行进度只写 `docs/STATUS.md`。

## 身份合并与来源分工

- 规范名优先使用有出处的简体中文通行名，暂无可靠中译时保留日文，旧艺名、罗马字、假名和繁体名都降为别名。姓名写入不得再和头像成功绑定：`no_avatar` 只表示没取得合格图片，不得阻止已核实姓名落库。多个实体精确命中同一姓名映射时按同人走 `merge_entity`，资料不足时保留原名、不猜译。
- 「这一页只有一位女优」永远不构成证据。库里大量番号是 BEST 合集（一部片可列 8~11 位），搜索无结果的页面仍会渲染推荐文章，改名后 slug 也会变。同一个错误判据在 javdb、av-wiki 两处各犯过一次，都是靠 dry-run 拦下的：一次让两位不同女优被认成同一人，一次让 5 位里错 3 位。精确回配命中优先于任何「唯一」推断，「唯一」只有在两个番号同证时才作数。
- `entity(kind, normalized_name)` 的唯一约束冲突通常不是 bug，而是信号：两个实体其实是同一人的新旧艺名。合并走 `peach.entities.merge_entity`，保留作品多的一侧，迁移关系/别名/外部引用/链接/搜索词，并把所有旧称留作别名。`entity_external_ref` 每个 provider 只能留一条，同源的第二条会被丢弃并报告，不能静默覆盖。合并不可逆，必须先取得用户授权并备份。creator / performer 跨类重复不用「作品数多的一侧」规则：只有两边非空作品集合完全相同，且 performer 别名精确命中 creator 名，或 creator 名由 performer 本名与账号别名组成时，才能自动归并；`r18:performer` / `javbus:performer` 是正式发行出演元数据，保留 performer，通用 `performer` 是 Stash 压平后的兼容断言，保留 creator。合并时必须同步 `asset.creator` 与 `演员:` 兼容投影，否则已删实体仍会在详情页伪造链接。`XX XX` 是来源节点文字重复，不是合法别名：person 名进入 CSV、兼容字段或 `upsert_asset_entity` 前先收敛完整重复串，JavBus 的「画像を拡大する」控件文字必须丢弃；清理要同时审计 `asset.creator`、`演员:` 标签和 `entity_alias`，upsert 按稳定外部引用、规范名、唯一别名依次复用实体。重复 creator 与发行 performer 即使因多版本导致作品集合不同，只要重复串精确命中 performer 名/别名且有发行来源，也属于高置信合并。
- 改写 `entity.canonical_name` 属于真相字段写入，与迁移同级：`--apply` 必须同时给 `--backup`。
- 头像与厂牌 Logo 的取源方向相反。头像去精心整理的图库（Gfriends 约 10.7 万张，目录名首字符即质量档位），不要回官方站——同一张脸 DMM 官方只给 125×125，图库存的是 500×500 起，最高 1500×2125。Logo 是品牌标识，官网与维基才是权威来源。
- 头像门槛按长短边分别判定（长边 ≥500 且短边 ≥300）。竖构图人像宽度天然小，套用为方图设的「短边 ≥512」会拒掉 `0-Hand-Storage`(334×501)、`8-GRAPHIS`(360×508) 这些最优来源。Gfriends 只按 `Filetree.json` 和单张 raw 媒体作为外部 Provider 使用，不克隆约 700 MB 图库、不把图片放进 Git。`audit_performer_portraits.py` 把合格图放入候选专用内容寻址缓存，每条另存 provider、名字命中档、上游 ID/URL、尺寸、MIME、SHA-256 与 policy version；与当前头像或同批其他实体字节完全相同的图只留审计证据，不进入 `/review`。每批另写来源健康 CSV；脚本没有写 ledger 或安装 `generated/avatars` 的路径。
- 可用来源实测（2026-08-15）：r18.dev、av-wiki.net、javdb.com、Gfriends 可用；javlibrary、missav、xslist 被 Cloudflare 拦，njav 有验证墙，jav321 无独立女优字段。被 Cloudflare 拦的站一律放弃，不绕过机器人检测。
- 番号目录被投影成创作者时，判据只能是文件级证据，不能是名字形态。`HD-abp-758`、`pppd-937ch`、`banbi_555`、`AH18` 四者形态相同，真相完全不同：前两个是发行目录（`HD-` 是画质、`-CH` 是中文字幕版，都会让番号提取放弃），第三个是 myfans 账号，第四个是 pixiv 画师。唯一可靠的区分是「目录内的媒体文件名是否解析出同一个番号」——账号目录里放的是作品标题，天然不命中；pixiv 行的 `path` 是 URL，先按这一点排除。`scripts/audit_code_creators.py` 就是这条判据的实现，存疑一律留复核 CSV。
- 画质前缀（`HD`/`FHD`/`4K`/`1080P`）和版本后缀（`-C`/`-CH`/`-UC`/`-SUB`）不是番号的一部分。番号提取器必须先剥这两层再匹配，否则 `code` 留空、目录名顶替身份，两个错误一起发生。
- **创作者是频道主，不是出镜者**；文件名里的 `@账号` 多数是蹭流量的引流号。可建创作者的只有`RT_@X - 正文…`（X 是转推原作者）、`女主@X`（明确标注的出镜者）和正文里的中文名；末尾成串裸 `@A @B @C` 是互推、`📷：@X` 是摄影师，都不建。据此删过 8 个假创作者（`KawasawaSen`、`ToBulma`、`Xiaoxiaofoer`、`MitsumeDoji`、`ToukaYuan`、`jiaoshiwb`、`yohuo001`、`yszl_0107`）。
- **转载渠道水印不是创作者水印**。已确认属于电报群与盗版站的：`@FLshe11`、`@SFJT68`、`@hmfl8`、`@zupi8888`、`52ywy.com`、`5snn.com`、`9P3456.com`。目录名同样可能是伪装，已证实的有`梦比优斯奥特曼（日配）`→MyElla、`宇宙英雄奥特曼`→RecklessDome、`电化学_金属腐蚀…`→梅麻呂3D，判定优先级是画面水印 > 作品名联网反查 > 文件名文本。
- 打创作者级标签前必须先验证这个 creator 是不是聚合目录。按 ledger 路径的下级目录分布判断：`Myfans` 下含至少 4 位不同创作者，`RiaKurumi` 是女优而非创作者且作品分属 cospuri／fellatiojapan／spermmania 三个厂牌。给聚合目录打统一风格标签就是 `asce` 事故的重演。
- `merge_entity` 已于 2026-08-17 回到主线 `src/peach/entities.py`（此前只存在于未合并的 `agent/claude/performer-portraits` 分支；配 `tests/test_entity_merge.py`）。两条陷阱：①不得依赖外键级联清理子表——sqlite 连接默认 `foreign_keys=OFF`，真实执行曾留下 5 条孤儿 `entity_alias`/`entity_external_ref` 行，所有子表行必须在函数内显式 DELETE；②计数用 `SELECT changes()`，不能用 `total_changes`（那是整个连接的累计值，会虚报数百倍）。合并前必须 SQLite 备份，合并后立即 `PRAGMA foreign_key_check` 应为 0。

## 流量与代理诊断工具

- Windows 上后续所有代理/流量诊断统一优先使用 FlowLens（Mihomo Traffic Monitor），面板地址 `http://127.0.0.1:9091/`。
- FlowLens API：`/api/v1/connections`、`/api/v1/summary`、`/api/v1/status`。按应用、网址、节点、规则以及 PikPak 检查实时和累计流量，并查看节点延迟。
- FlowLens 只观测经过 Mihomo 的连接。`DIRECT` 仍然属于经过 Mihomo，会被观测到；完全绕过 Mihomo 的连接必须标注「未观测」，不能推断为零。
- Windows 不再把 NetLimiter、Proxifier 或依赖网页常驻的 Zashboard 作为默认方案。
- macOS 的流量诊断统一使用 Stash Dashboard。

## 数据安全

- 真实 ledger 是当前写入者本机 `peach-data/database/ledger.db`，WAL 模式。正常浏览会合法写入播放/行为字段；平台绝对路径以 `docs/STATUS.md` 为准。
- 测试必须使用临时 SQLite 和临时媒体；不得写真实 ledger。
- 真实迁移前依次执行 SQLite 备份、asset/tag 计数、`PRAGMA integrity_check`、迁移版本检查、服务 smoke test。
- 已应用与待应用迁移以 `docs/STATUS.md` 和实际 `migrate status` 为准，不在长期上下文复制会过期的版本清单。
- `0007` 曾在应用后、提交前被改写注释/格式，导致校验和漂移。本次用迁移前备份重放当前 `0007`，对 298 条受影响资产与生产结果逐条对比，差异为 0 后才校正 `schema_migration` 校验和，然后正常应用 `0008`、`0009`。已应用迁移文件从此不得修改，任何后续变更必须新增版本。
- 外置盘目标只保存 `R:\media`；代码、运行数据、venv 和 worktree 在两台机器各自的内置盘。`peach-data` 不进入仓库，也不整体交给文件同步。分通道边界见 ADR-0017。

## 运行与部署

- Windows 日常入口是当前用户 Startup 中的唯一 `Peach.lnk`，指向 `C:\Users\longm\Desktop\peach\peach-app\dist\Peach\Peach.exe`。`R:\peach-app` 是迁移前的旧位置，不再用作运行入口。
- Windows 发布入口使用 `scripts/build_windows.ps1`：先用 `scripts/generate_brand_assets.py` 从原始附件生成正方形 `resources/peach-logo.png` 和多尺寸 `resources/peach.ico`，再构建单一 `dist/Peach/Peach.exe`。无参数运行托盘，`serve`/`migrate` 运行 CLI；桌面快捷方式由 `scripts/create_desktop_shortcut.ps1` 创建，图标使用 `Peach.exe,0`，行为与 FlowLens 的快捷方式一致；Startup 安装仍由 `scripts/manage_tray_startup.ps1` 负责。
- `dist/Peach/Peach.exe` 是本机打包入口，不是可移动的独立发行版：托盘只打包了自己，服务进程仍由项目 venv 的 `peach.exe` 承担（`_peach_executable()` 从 exe 位置逐级向上找 `.venv\Scripts\peach.exe`）。脱离同一台机器的项目 `.venv` 复制不会工作，不要按「单文件绿色版」对外描述。PyInstaller 的资源直接位于 `sys._MEIPASS`，没有源码树的 `src/` 层；打包后的 `migrate`、Web 与品牌资源必须从这里解析，不能再对 `config.py` 固定取 `parents[2]`。
- 托盘单击打开 HTTPS；macOS/Windows 菜单都提供「同步开发进度」「同步 Ledger」「接管 Ledger 写入」、状态、重启、日志和退出。**两个「同步」不能合并成一个按钮**：一个走 GitHub、一个走 SMB 共享，任一方不可达都不该拖住另一方。Windows 开发同步先快进并跑正式测试；服务代码通过后才重启，打包输入变更时另构建新 EXE、检查迁移资源，再由独立助手等旧托盘退出后替换，启动失败自动恢复备份；失败保留待应用标记供下次点击重试。HTTP/HTTPS 服务只观察角色，不自动复制；手动同步先用 `sync.resolve()` 只读判定这次会不会真的复制：`offline` 不是结论——macOS 重启后 SMB 共享不会自己挂回来，托盘按 `SHARED_SMB_HOST`／`SHARED_SMB_SHARE`／`SHARED_SMB_USER` 补挂一次再重判，真挂不上才回话。挂载走 `osascript` 的 `mount volume`（同样经 NetFS 自建挂载点、取钥匙串，但不像 `open smb://` 那样弹 Finder 窗口），并且**先查一次钥匙串**：没有对应记录时 NetFS 不报错，而是弹认证框一直等，于是一次后台点击既卡到超时又在用户面前推出一个密码框。钥匙串记录按主机名存，同一台机器的 IP 和 mDNS 名是两条不同的记录。补挂后仍是 `offline`，以及 `conflict`／`in-sync`，一律直接回话，**不停服务**——停一停再启回来换不到任何东西，只换来一次十几秒的断网页和一条「同步失败」。会复制时才停止自己创建的服务，用 SQLite backup API 与原子替换复制，最后恢复服务。「接管 Ledger 写入」只在共享盘不可达时短路，因为 `in-sync` 对它正是要做的那一次。共享源在 macOS smbfs 上必须以 immutable 已关闭快照读取；共享目标不能由 SQLite 直接打开事务连接。健康端口不归本托盘时拒绝接管。
- 创建 Win32 窗口前必须启用 Per-Monitor V2 DPI。正常动作不弹模态 MessageBox；更新检查在后台线程执行，用 pystray 原生非模态通知反馈。
- `src/peach/__init__.py::__version__` 是版本唯一来源；采用 pre-1.0 SemVer。Git commit 是构建标识，`vX.Y.Z` 是本地发布点。「检查更新」只 fetch/比较；「同步开发进度」只做 `merge --ff-only`，不 stash、不 rebase、不 `--force`——并行工作树和主检出共用同一个对象库与 reflog，任何改写历史的「顺手解决」都会把别的分支一起拖下去。工作区脏或两边分叉时原样报出来交给人。快进动到 `tray.py`／`menubar.py`／`versioning.py`／`certs.py`／`netwatch.py`／`config.py`／`pyproject.toml` 时**只重启子服务追不上**，托盘要靠 `launchctl kickstart -k` 重启自己，顺序必须是先 `stop_owned()` 再 kickstart（反过来，新托盘会看到一组健康但 `_owned` 为空的服务，此后每次同步都被自己的归属检查挡掉）。kickstart 的前提是 launchd 报的 pid 等于自己的 pid，不是「plist 存在」——从终端跑起来的托盘 kickstart 会在旁边**再**起一个。
- `scripts/manage_tray_startup.ps1` 是唯一自启动管理入口。托盘管理 HTTP `0.0.0.0:80` 和当前路由选出的 LAN IPv4 上的 HTTPS 443；显式参数、`PEACH_LAN_ADDRESS`、`lan_ipv4()` 依次覆盖。服务日志写入本机 `peach-data/logs`。
- `peach serve` 按平台发布固定主机名：macOS 为 `peach.local`，Windows 为 `peach-win.local`。Windows 不在源码钉家庭 IP，仍保留 `Zeroconf()` 全合格网卡监听。mDNS 验收必须包含单元测试、运行态 health、DNS-SD、主机名解析和真实 LAN 客户端。
- `.local` 使用本地 CA，不使用 Let's Encrypt。证书/私钥保存在本机 `peach-data/secrets`。TLS 私钥禁用 ACL 继承，只允许实际服务身份、SYSTEM、Administrators；当前 Windows 服务身份是 `longm`。macOS/iOS 只安装并信任 `peach-local-ca.crt`，不得分发 CA key 或服务器 key。
- FastAPI 是唯一 Web server。不得恢复平行 `http.server` 或动态 legacy loader。配置 `--token` 时通过 `/login` POST 取得 HttpOnly cookie；旧 `?t=` 只做一次兼容重定向，dependency 统一 JSON contract 鉴权但不替代登录流程。
- FFmpeg/ffprobe 依次从显式环境变量、本机 `peach-data/tools/ffmpeg/bin`、`PATH` 解析；不得回退到 Stash 私有目录。
- **生成产物走 Syncthing 单向同步，和账本、和 Git 是三条互不兜底的链路**。Windows send-only、Mac receive-only，五个文件夹 `snapshots`、`posters`、`avatars`、`logos`、`covers`；Mac 侧根目录在 `peach-data/artifacts/`（`generated` 是指向它的符号链接，不要把符号链接本身设成同步目录），Trash Can 版本保留 30 天。`.stignore` 不跨设备同步，两端每个目录各放一份。方向是固定的：Mac 不发布正式产物，在 Mac 上生成的图片不会回到 Windows。
- 长任务只停止自己拥有且命令行匹配的 Python/FFmpeg 进程树，禁止全机终止 FFmpeg。
- 导入运维脚本不得触发文件、网络或数据库副作用。`scrape_codes.py` 默认写可续跑复核 CSV；`clean_names.py` 先预览，`--apply` 前备份 SQLite。
- 切换服务前检查 80、443、8900、9999 端口和实际进程归属。
- 115/PikPak 播放依赖 CloudDrive 的 `B:`/`A:`；盘符对 Windows token 可见性不同，最终以 Peach 对已知作品的 `/stream` 实测为准。
- 浏览器不支持的 AVI 等容器由 `TranscodeService` 缓存为 H.264/AAC MP4，再通过同一 Range 端点提供；永不改写原媒体。
- 数据库元数据不得插值到 inline JavaScript 事件属性。真实厂牌名中的撇号曾直接造成 Firefox 语法错误。前端 API 包装必须先检查 HTTP 状态再返回 JSON；冲突只读时写端点会返回 `409` 和错误 JSON，把它当普通成功对象会清空选择并重载，用户只会看到条目原样回来。批量处置和详情反馈必须保留当前选择并明确显示失败原因。
- 验证分开报告：静态/单元/API、桌面浏览器、390×844 手机、生产服务是否已重启。

## 当前架构真相

- Ledger 拥有真相和行为；Stash 是可替换适配器，调用统一经过 `StashClient`，外部 Scene ID 和来源进入 `media_binding`，不新增直接 GraphQL helper 或 Stash 私有 FFmpeg 路径。规范女优/厂牌/标签/创作者进入 `entity`、`entity_external_ref`、`asset_entity`；扁平 `asset_tag` 和 creator/studio 字段只是兼容投影。
- FastAPI 与前端保持单体部署，在线来源和 AI 只通过显式适配器进入；AI runtime 与推理 API 的协议边界见 ADR-0003。
- 当前页面、路由、交互与性能实现只写 `docs/STATUS.md`，由 API 和 `tests/test_web_ui.py` 守住；本文件不再复制易过期的版本号、像素值和控件清单。
- `/taste` 只读合并 Peach 行为与本机私有浏览历史，且明确以浏览器记录为主要画像、Peach 内部为辅助证据；两者分别排序，不把“不合口味”自动归因或降权到 Tag。查询词里的负号项整体排除，下划线是组合词边界的一部分，不得把 `-ai_generated` 拆成正向 `generated`；游戏作品名等内容词按实际语义归类。模糊时长旧 Tag 只作兼容识别，禁止进入品味、索引、详情和筛选状态。时间窗使用当前资产的 `last_played` 和浏览访问时间；画像、补标签缺口和排名都只是候选。原始 URL／标题不进入页面或 ledger；上传原件保存在 `sources/taste-history/imports`，移除数据源只清理规范化分析库，不删除原件。浏览器数据库解析固定复用 `browserexport==0.4.4`，运行中浏览器仍先由 Peach 的 SQLite backup API 取得一致快照。macOS 与 Windows 的本机发现能力不等于跨主机同步；跨机数据必须显式导出、传输并按来源去重合并。
- 追更连接器、凭据、变体和跨站归组以 ADR-0019 为准。Rule34.xxx 来源身份大小写不敏感；作者显示名与头像优先经固定主机校验的官方页面，归档站只回退。
- 自动追更固定使用 APScheduler 3.11.3，只在 ledger writer 启动。频率保存在 `peach-data/state/follow-schedule.json`，默认每小时且启动后等待一个完整间隔；不要改成启动即抓。任务必须保持 `coalesce=True`、`max_instances=1`，并与手动检查共用 `WebContract.follow_check_lock`，reader 只显示不可用状态。
- 账本路径兼容和抽帧失败处理统一见 `.claude/skills/peach-cross-platform/SKILL.md` 与 `.claude/skills/peach-batch-jobs/SKILL.md`。

## Web 性能边界

- 列表必须分批构建；首批才计算总数，后续多取一条判断是否还有下一页。无限滚动同一时间只允许一个追加请求。
- 聚合查询禁止按实体发 N+1 SQL；相邻请求可复用缓存，但异步响应必须核对请求序号和当前路由，旧响应不得覆盖新页面。
- 远端媒体 hover 只读本地预览；离开详情、换页或替换 DOM 时停止播放并取消当前 stream session，不能让 CloudDrive 继续读盘。
- 当前批量大小、播放器版本、像素值与性能测量属于实现快照，统一留在测试、`docs/STATUS.md` 或参考快照，不写入长期上下文。

## 本机服务、系统代理与双机广播
- **对本机服务的 HTTP 探测必须 `trust_env=False`**。代理客户端（Stash、HapiGo、Surge）会设置 macOS 系统级 HTTP 代理，httpx 默认经 `urllib.getproxies()` 读它，探测 `127.0.0.1` 的请求被送进代理、由代理回 503——服务活着却被判「未运行」。2026-08-21 实测如此，修复在 `peach.tray.ServiceManager.healthy`，`test_health_check_never_goes_through_a_proxy` 守门。任何新写的健康检查/回环探测都适用同一条。
- **macOS 系统代理例外列表必须包含 `*.local` 和 `192.168.50.0/24`**。浏览器走系统代理时，代理核心解析不了 mDNS 名字，`http://peach.local` 会被代理回 503（终端直连正常，所以只有浏览器坏）。用 `networksetup -setproxybypassdomains <服务> "*.local" "localhost" "127.0.0.1" "192.168.50.0/24"` 设置，`scutil --proxy` 的 `ExceptionsList` 复查。代理客户端重设系统代理后这一列表可能被清掉，排查浏览器打不开 `.local` 时先看这里。
- **双机广播分工：macOS 固定 `peach.local`，Windows 固定 `peach-win.local`**。默认值已收敛到 `peach.config.MDNS_NAME`，`PEACH_MDNS_NAME` 只做临时覆盖。服务可以同时跑（账本单写者复制兜底），但两边同时写入会很快冲突转只读。
- **两台机器各有独立的本机 CA**（secrets 按设计不共享）。iPhone/iPad 必须信任「当前正在服务的那台」的 CA 才能用 HTTPS；换机器服务后要装对应的 `peach-local-ca.crt` 并在「证书信任设置」开完全信任。核对指纹：`openssl x509 -in .../peach-local-ca.crt -noout -fingerprint`。菜单栏状态行逐个点名每个服务：`HTTP 正常 · HTTPS 异常（状态码 503）`，异常附最近一次失败原因；不要改回只报「未运行」。
## 恢复入口

项目重构时已从活动目录删除 deprecated 脚本和按日期文档，Git 历史仍可恢复。旧 `_SHARED_STATE` 和重构前的根仓库元数据备份 `peach-root-repo-backup-20260814` 都在各机 `peach-data` 的 `state`/`archive` 下，只作恢复证据。**不要再按 `R:\peach-data\...` 去找**：那是迁到内置盘之前的位置，Windows 现在是 `C:\Users\longm\Desktop\peach\peach-data`，Mac 的 `archive` 是指向外置盘的符号链接，盘不在时读不到不等于备份没了。
