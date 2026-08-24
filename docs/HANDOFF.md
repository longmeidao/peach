# Peach 交接与长期工作约定

本文件只保存跨任务长期有效的事实和工作规则，不记录逐次聊天流水。

## 界面、媒体与复核的既定判据

- 卡片实体链接必须由同一个 `{kind,name}` 结构生成，禁止先独立选择显示名、再根据其他字段推断类型。此前 `FSDSS-376-C.mp4` 显示演员 `新ありな`，却因同时存在厂牌而生成 `/studios/新ありな`；真实 ledger 关系是演员 `新ありな`、厂牌 `FALENO`，错误只在前端映射。
- 卡片悬停控件出现时暂隐来源徽标和时长，避免两层信息互相遮挡；账本 `size` 为空或 0 时显示「大小未知」，不能伪装成 `0 MB`。标准卡标题保留固定两行高度，小图固定一行，防止同一网格上下跳动。
- 竖屏条整行占位（`grid-column:1/-1`），必须插在行边界上。曾经的做法是另拉一批横屏视频补满上一行余位，那批 ID 不在分页序列里，翻页必然出现重复卡，而且被当作 `scard` 渲染会把横屏画面压成竖框。行边界插入不额外请求、不重复；`SHORTS_ROW_OFFSET` 控制插在第几行之后。
- 排除竖屏是首页取景，不是全局过滤器。任何把 `exclude_vertical` 加进搜索或实体列表的改法都会让按名字搜一条竖屏视频返回 0 结果，`test_only_the_default_home_list_drops_portrait_videos` 守这条线。
- HLS 分片必须切在真实关键帧上。`-c copy` 只能在关键帧处下刀，而按固定 6 秒等分写播放列表会和实际切点对不上——实测本地片源有每 8.33 秒才一个关键帧的，目录说「6–12 秒」实际给的是别的区间，表现为进度条错位、段间画面重复或跳过。关键帧表由 `peach.mp4index.keyframe_seconds` 从 MP4 的 `moov/stss` 直接读出（0.01 秒量级），**不要用 `ffprobe -skip_frame nokey`：那会把整个文件解复用一遍，在挂载网盘上等于把片子拉一遍，正好抵消分片省流量的目的**。`moov` 可能在文件尾部，按 box 头 seek 定位，不要顺序读。读不出关键帧就返回 None 回退标准 Range，不猜。
- 分片用 `-copyts -muxdelay 0 -muxpreload 0` 保持时间戳连续。早先的 `-avoid_negative_ts make_zero` 让每段都从 0 秒开始自称，拖动进度条时容易跳错位置、音画不同步。
- 分片缓存写在 `stream_root/<asset>/<size>-<mtime>-<秒数>/<index>.ts`，不随响应删除：回放、断线重连和多设备都会重复请求同一段，每次重跑 FFmpeg 等于让 CloudDrive 再预取一次块。缓存按最后访问时间淘汰，指纹带文件大小和 mtime，换了片源自然失效。FFmpeg 并发有信号量闸门（默认 CPU 核数一半），播放器本身就会并发预取多段。
- 回收站的物理删除只有一条实现：`purge_assets()`，`/api/batch` 的 `delete` 和 `/api/trash/empty` 共用它。顺序固定为先删媒体文件、再删账本行，删不掉的文件整条跳过并在 `blocked` 里回报，前端必须把 `blocked` 显示出来。反过来先删行会留下没人认领的媒体文件，那是真正不可恢复的丢失；留一条指向缺失文件的回收站行至少还能看见和重试。`asset_search` 不列入 `ASSET_REFERENCE_TABLES`，FTS 行由 `0004` 的删除触发器负责。
- 复核候选文件名带批次日期，代码里只认前缀并取目录里最新的一份；把日期写死会让下一批生成后页面静默变空。候选行必须有稳定主键（`board`/`studio`/`entity_id`），缺主键的行跳过并计数，绝不退化成行号——行号会在 CSV 重排后把历史决定挪到别的条目上。候选目录走 `PeachSettings.candidate_root`，不是模块常量，否则测试会读到本机真实的 `peach-data/generated`。
- 批准的权威值只能来自候选文件本身，请求体里的 `creator`/`tags` 只当确认，不一致直接拒绝；只有 `status=candidate` 的创作者候选可以批准，`skip` 行必须在页面禁用批准。否则「批准候选 X」能写入与 X 无关的标签，而 `review_decision` 留痕仍写着 X 通过——留痕说通过、实际写了别的，是最糟的组合。未勾选即整条通过，但受 `REVIEW_APPLY_LIMIT` 约束，超限必须显式勾选。
- 抽帧的 bt709 覆盖重试只针对坏色彩元数据（stderr 命中 `reserved/unsupported/invalid` + 色彩词）。无条件重试会让网盘超时这类必然失败的文件每帧白跑第二次，单帧最坏耗时从 45 秒翻到 90 秒。判据依赖 stderr，所以不能丢弃 `capture_output` 的错误流。
- Logo 与头像在界面上都渲染成方框（厂牌方图、女优 160×160 圆头像），候选按实测像素比例处理，判据在 `peach.images.classify`：长宽比 ≤1.35 直接用，更长的补自身四角底色填成正方形（`pad_to_square`，不是刷白也不是裁切），短边 <128 才拒绝。只有 URL 没有实测尺寸不算候选。
- **AV 厂牌 Logo 的来源是厂牌自己的社交账号头像**：社交头像天然是正方形且由品牌本人发布。取证顺序是 handle → `unavatar.io` 解析出 `pbs.twimg.com` 真实地址 → 从平台 CDN 下载 → 实测，unavatar 只用于解析地址，provenance 两者都记（`scripts/fetch_studio_avatar_candidates.py`）。r18.dev 详情 JSON 只有 `maker.name`/`label.name` 和作品封面，没有 Logo 资源，已排除。
- **能解析不等于是对的品牌**：`@bazooka` 确实存在且能取到 400×400 头像，但那是 2007 年注册的通用账号，不是这个 AV 厂牌；Wikimedia 搜同名也给出 16:9 的泡泡糖品牌图。所以 handle 必须逐个取证确认，脚本默认不猜，`--guess-handles` 的产出一律标 `needs_confirmation` 且不自动采纳。查不到就留空。
- 社交 handle 只采信**厂牌自有域名页面上**的链接。日文维基条目的外链里混着引用来源的新闻站，直接抓会把新闻站自己的账号当成厂牌的——实测 `妄想族` 条目就抓出了 `@news_postseven` 与 `@taishurxjp`。官网链接也不必然指向主号：`gloryquest.tv` 链的是 `@lG_Ql`「社内クリエイティ部（BOT）」，头像压着 18+ 徽标，反而不如 `@gloryquest_av` 的干净字标合适。所以官网只用来确认归属，选哪个号仍要看图。
- AV 厂牌官网普遍先给年龄确认页，不穿过它只能拿到约 10 KB 的空壳。判据必须是锚文本而不是 URL：否定链接指向站外（实测 `dasdas.jp`、`muku.tv` 的「いいえ」都指向 dmm.com），肯定链接「はい（入室する）」指向站内，两者的 href 看不出区别。跟错就离开了厂牌域名，抓到的账号也就不再属于这个厂牌。实现见 `scripts/find_studio_socials.py`，`test_age_gate_is_crossed_by_the_affirmative_link_only` 守这条线。
- 二手结论不能当证据：搜索摘要曾称 `@EBODY_` 已注销，实测直接解析到 400×400 活跃头像。凡是「某账号/端点已失效」这类判断，取证方式是自己请求一次，不是转述搜索结果。
- **图集就是目录**：账本没有图集实体，也不需要一个。`<作品目录>\P\001.jpg` 这种约定在 A:/B: 上到处都是，所以 `/api/photos` 按 `path` 去掉文件名分组，图集 id 取该目录里最小的资产 id——稳定、可反查目录，又不用把真实路径发给前端（和 `q_item` 一致）。同名目录在两个来源下算两个图集：文件不同、计费口径也不同。叶子目录只写 `P`、`图片` 这类通用名时，标题取上一级目录名。
- **瀑布流只读缩略图，原图只在灯箱里读**。图片资产没有接触印相可裁，只能读原图；PikPak 一张动辄几 MB，一屏几十张就是几十兆计费流量。`/photo-thumb` 用 Pillow 缩到 640 宽存进 `photo_root`，每张只回源一次，`/photo` 只服务灯箱当前和相邻的大图。瀑布流用 CSS `column-count`：图片行没有 `width`/`height`，等宽多列流式排版正好不需要比例，也就不必等图加载完再算位置。
- 人工复核入口固定为 `/review`，候选 API 为 `GET /api/review`、`POST /api/review/decision`。候选来自本机 `peach-data/generated` 下的 CSV；每项尽量带代表封面与原视频入口，审核状态写 `review_decision`。元数据与创作者标签批准后写相应真相/投影，Logo、头像、身份和媒体失败只记录决定；封面抓取的成功、尺寸和缺失是机械状态，不进入人工复核。

## 无摩擦接手

- Codex 自动读取项目层级中的 `AGENTS.md`；Claude Code 通过 `CLAUDE.md` 导入同一文件。
- 两个智能体使用同一入口、同一必读顺序，不再生成按日期命名的临时交接文档。
- 新任务以当前机器真实的 `peach-app` 为工作目录，并说：「接手 Peach，按项目入口文件继续 STATUS 中的下一任务。」不得把 Windows 迁移前的 `R:\peach-app` 当跨平台固定路径。
- 改变运行事实的任务同时更新 `docs/STATUS.md`；长期规则更新本文件、`docs/REUSE.md` 或 ADR；可执行流程写成 `.claude/skills/<name>/SKILL.md`。分层判据见 ADR-0015，步骤见 `peach-context-rules`。
- 技能目前只有 Claude 侧封装（`.claude/skills/`），Codex 不自动加载，只能靠 `AGENTS.md` 的索引表
  主动读取同一份文件。Codex 接手时自行确认当前版本的技能机制与目录约定，把这几个技能封装成
  Codex 侧可自动触发的形式，内容仍指向同一份 `SKILL.md`，不复制第二份正文；确认不了就保留索引
  表作为回退，并在此处写明未取得。
- 无论哪个 harness，触发都是概率性的：必须每次成立的规则要由脚本、测试或 hook 强制，不能只写成技能。
- 用户不是消息中转站。结论、进度、待办和证据必须写入共享文档或机器可读产物。

## 并行智能体与 Git 工作树

操作步骤（创建工作树、暂存边界、ready/integrate、唯一测试入口）见
`.claude/skills/peach-worktree/SKILL.md`。本节只保留决定这些规则的事实与证据。

- Codex 负责架构、文件归属、审核、迁移、真实 ledger 写入、服务重启和最终验收；Claude 适合并行执行抽帧板阅读、候选元数据刮削、CSV 对账等边界明确的机械批次。
- 并行任务必须给出输入/输出路径、网络和费用策略、写入边界、验收条件。工作者只产出 `candidate`，不得自行标为 `approved`、执行 `--apply`、改迁移/ADR 或重启服务。
- 完成顺序不能决定覆盖顺序。仓库启用 Git `rerere` 记录重复冲突的已确认解法，但它不能代替人工审核。
- `bba0b77` 是已发生的反例：测试被误判为本任务文件而进入提交，对应 `probe.py` 未暂存，导致 HEAD 出现「测试指向不存在实现」。独立 worktree、暂存路径复核和实现/测试原子性因此是强制规则。
- 「全量 unittest discover 会挂起 / 会话输出消失」这条 2026-08-17 的结论已被证伪，成因另在别处。连跑三次全量 197 项均正常结束，通过时输出仅 6.9 KB。真实机制是 `tests/test_web_ui.py` 对整页做 `assertIn`：`self.page` 是约 189 KB 的 `index.html`，unittest 的失败消息会把整个容器原样打印，**一条断言失败就产出 195 KB 输出**，工具管道遇到超大输出会转存成文件，看起来就像输出消失。已改为有界的 `assertPageContains`/`assertPageLacks`，同样的失败现在是 861 字节。这不影响「唯一入口是 `& .\scripts\test.ps1`」的结论，但不要再把它归因于运行器竞态。
- Windows 上探测进程存活**绝不能用 `os.kill(pid, 0)`**。`signal.CTRL_C_EVENT == 0`，所以这个 Unix 经典写法实际调用 `GenerateConsoleCtrlEvent(CTRL_C_EVENT, ...)`：对控制台组内的 PID 会把 Ctrl+C 发给整个进程组（信号异步投递，`KeyboardInterrupt` 要到下一次控制台 I/O 才浮出，看起来像凭空报错）；对非组长的活进程则报 WinError 87，而旧代码把 87 当作「进程已死」，活着的任务会被判定为已死、锁被后来者抢走。`PidFileLock._running` 已改用 `OpenProcess` + `GetExitCodeProcess`，`test_liveness_probe_never_signals_its_own_console` 守这条线。这个故障只在真实控制台里出现，重定向和无控制台环境永远不复现——不要因为工具管道跑得过就认为没问题。
- 含中文的 `.ps1` 必须带 UTF-8 BOM。没有 BOM 时 Windows PowerShell 5.1 按 ANSI（简中系统即 GBK）读文件，中文被解成乱码后引号配对错乱，脚本在解析期就失败并闪退；报错行还会落在纯 ASCII 的语句上（实测 `test.ps1` 报在第 18 行的 `Join-Path`，真正的坏行在别处），极难定位。pwsh 7 默认按 UTF-8 读无 BOM 文件，同一份字节实测 7.6.3 解析通过、5.1 报 2 处错误。所以**默认终端是 pwsh 7 也不能免疫**：双击 `.ps1` 或右键「使用 PowerShell 运行」走的是文件关联的 `powershell.exe`（5.1），解析失败后窗口立即关闭，连报错都来不及看。`test_powershell_scripts_with_chinese_carry_a_utf8_bom` 守这条线。
- 「归一化」与「判形态」是两件事，混用会让判据自己打自己：`normalise_code` 补上分隔符后，`RAIKUN325`（myfans 账号名，241 个文件）变成 `RAIKUN-325` 就通过了番号检查，`BANBI_555` 同理。分隔符正是区分番号与账号名的唯一线索，归一化把它抹掉了，所以形态判定必须看原值，归一化只服务封面查找那类需要稳定键的场景；两处各犯过一次，现已共用 `is_jav_code`。代价是 `SOAN045`、`DTW024` 这类漏写分隔符的真番号会被判为非 JAV，二者结构相同无法自动区分，宁可漏掉几个也不能把账号作品塞进 JAV 模式。同理，前端「刷新」要区分重取与换一批：`q_tops` 是 `ORDER BY n DESC` 的确定性查询，失效缓存后重取还是同一批人，必须放大候选池再按种子确定性抽样，缓存键带上种子与口径，否则几套结果互相顶掉。
- 上一条只写成知识没有强制机制，于是同类写法又长了回来。AST 审计发现 6 处仍是裸 `text=True`，其中 `src/peach/versioning.py` 是生产代码——它读 git 输出，而本仓库的提交信息就是中文的，拿 `282f8d9` 自己的标题即可复现 `stdout=None`。已全部锁定 UTF-8，并加 `tests/test_subprocess_encoding.py` 扫全仓强制。该守卫只认 `subprocess.*` 字面调用，包装器（如 `VersionManager._git` 走注入的 `self._execute`）看不见，那个盲点由同文件里一条显式断言补。父进程指定 UTF-8 只决定如何解码，不能改变子进程的输出编码；Windows 托盘调用 Peach 自己的 Python CLI 时还必须传 `PYTHONIOENCODING=utf-8`，否则管道输出仍是 GBK，Ledger 同步通知会出现替换字符。
- 权限规则里的反斜杠必须双写。匹配器把 `\` 当转义字符，JSON 写 `"& .\\scripts\\test.ps1"` 解码成单反斜杠后 `\s`、`\t` 不再是字面反斜杠，规则匹配不上，非交互会话直接判拒、任务中断。正确写法是 JSON 里 `"& .\\\\scripts\\\\test.ps1"`；旁证是自动生成过的可用规则 `'R:\\\\media\\\\创作者'` 与 `\\(Get-ChildItem`，路径和括号一律双写。用正斜杠写的规则不受影响。改完要新开会话才生效——配置在会话启动时加载。
- `.claude/settings.local.json` 在 `.gitignore` 里，26 个 worktree 无一带有它，所以写在那里的允许规则只在主工作树生效——而项目规矩要求测试在 worktree 里跑。`& .\scripts\test.ps1` 的允许规则因此放在被跟踪的 `.claude/settings.json`，随代码进入每个 worktree。手工拼 venv 路径的命令（`python.exe -m unittest *` 等）刻意不上提到共享配置：那是 AGENTS.md 明令禁止的路径，共享化等于给违规开绿灯。
- 2026-08-17：PowerShell 工具会在调用中途被 session teardown 掐断，丢失的结果被错标成用户拒绝
  （`anthropics/claude-code` issue 83486，前台长 timeout 和后台写法都中过）。改从 Bash 侧跑
  `pwsh -NoProfile -File ./scripts/test.ps1`，实测全量 203 项 21 秒通过。入口不变，仍禁止手工拼 venv 路径。

## Claude 在本项目中的实际能力边界

2026-08-14 的真实执行证明 Claude 可以正常完成：

- 查看成人内容并分类行为、着装、身体属性、场景和制作风格；
- 从公开番号库刮削元数据并映射本地词表；
- 编写上述领域的代码、正则、批处理、对账和中文文本；
- 根据番号、文件名、画面水印、Logo 或发行元数据识别女优和厂牌。

此前「Claude 会拒绝露骨行为分类」的记录已废止。一次实际任务读取 30 张创作者板，为 27 位创作者、4,518 个视频写入 27,295 条 `vision_creator` 标签，含口交、足交、手交、乳交、骑乘和后入，最终 27/27 与 ledger 对账一致。

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
- 2026-08-17 已按此规范整改存量文档：154 处弯引号与 ASCII 引号改为直角引号「」，黑话与 `id`
  大小写共 16 处改写。整改只动措辞，不动事实、数字与限制。

## 参考产品证据登记

凡用户要求「模仿/参考/对齐」，必须先取得当前可复现证据：实时行为加 DOM/CSS/JS；源码不可得时才使用精确截图测量。记录 URL、日期、版本/hash、复用行为和 Peach 的主动差异。证据不可得就写 `未取得`，不得把猜测描述成忠实复刻。

- **Beeg 卡片控件（2026-08-15）**：当前根页面加载 `https://beeg.com/dist/main.9442c3b8.css`（SHA-256 `E585B07CA0C312C28903DB939144B26A3C4BFBC9499F5997BDDE168A197CDB34`）和 `main.9442c3b8.js`（SHA-256 `A7321F6E84D97417B588B6E98EEC86A15B30DC4C36B03537481CC55A4CF933E7`）。计时圈为 36 px、上/右 12 px、`rgba(0,0,0,.24)`、`saturate(180%) blur(12px)`、2 px 白色圆环；桌面 hover 放大 1.2。稍后看控件使用同类透明处理，位于右下 12 px。Peach 等到预览可用后才启用计时圈，按用户要求连续悬停 5 秒才放大；放大层保留 Peach 自己的居中 -10/+10/详情控件。
- **Beeg 表面层（2026-08-15，同一 CSS/hash）**：暗色背景 `rgb(2,4,8)`，表面 `rgb(34,34,34)`。当前压缩 JS 的 Button 组件证明：`plain/outlined` 是透明背景，`filled` 才使用 `rgba(245,250,255,.05)`；边框分别是 15% 和 10% 白色内描边。frost utility 的 `rgba(38,40,44,.72)` / `rgba(30,30,30,.72)` 只用于指定浮层，不能套到全部厂牌和标签。页首蓝绿背景是 `/dist/assets/glow.webp`（1000×563，SHA-256 `ACA7A914D82843EE4A655C35651931CDC0D42308EDC0F7CB16D8EC63C7AE3ECA`）以 `49vh` 铺放并向 `rgb(2,4,8)` 渐隐；Peach 不复制许可不明位图，使用本地 CSS 光晕。此前把「取到 frost token」误写成全部表面已对齐，现已纠正。
- **Beeg 实体资料页（2026-08-15）**：`view-source:https://beeg.com/DianaRider` 可取得 SPA 启动 HTML及上述当前 CSS/JS；原始 Vue source map 返回 404，明确记为 `未取得`。压缩 JS 中 `TagProfile` 的可复现结构是：无大外框卡片、桌面 160×160 圆头像、资料文字并排，别名/统计/简介/链接分层，关联实体另起一段。Peach 资料页据此隐藏首页三层筛选，在资料下显示馆藏已有标签、关联艺人和作品；不声称取得原始 Vue 文件。
- **Beeg 照片页（2026-08-24）**：`https://beeg.com/DianaRider?media=photos` 的浏览器通道被本机策略拒绝（`preview_start` 返回 `blocked by policy`），改用 Git curl 取得同一版资产：启动 HTML 7,124 字节，`main.9442c3b8.css` SHA-256 与 2026-08-15 登记值一致，`main.9442c3b8.js` SHA-256 `A7321F6E84D97417B588B6E98EEC86A15B30DC4C36B03537481CC55A4CF933E7`。可复现的是数据形状：照片按「图集（set）」寻址，客户端取 `/photos?set=<id>` 和 `/photo/<id>`，缩略图由 `thumbs.externulls.com` 按 `/photos/<id>/to.webp?size_new=<宽>x<高>` 现取现缩。**照片栅格的列数、间距和灯箱行为均为 `未取得`**：那部分由 Vue 运行时渲染，静态 bundle 里没有对应选择器，本轮也没有可用的浏览器通道去实测。Peach 只复用「图集优先 + 缩略图按尺寸单独取」这两条结构决定，展示改成用户要求的瀑布流与黑底灯箱，不声称复刻其栅格。
- **失败报告规则（2026-08-15）**：浏览器工具拒绝 URL 不等于公网不可达；本机 `curl.exe` 的 Schannel 握手失败也不等于代理失效。本次使用同一 `127.0.0.1:7897` 代理的 Git curl 成功取得当前资产。任何取证、浏览器或视觉验证失败都必须立即报告失败步骤、原始错误、影响和替代路径；静态/API 测试不得冒充视觉验收。
- **重复错误复盘（2026-08-16）**：反复出现的 pytest、错误 `/health`、worktree 错找 `.venv` 或加载主目录源码、PowerShell `$HOME` 大小写冲突、`foreach {}` 后直接接管道、Schannel 失败后改用 HTTP 冒充 HTTPS，以及浏览器不可用却继续报视觉通过，根因都是「文字提醒没有变成执行门槛」。测试入口已收敛为 `scripts/test.ps1`，自动定位主 venv 并拒绝错误源码；其他禁用模式写入项目 `AGENTS.md`，以后必须由可执行检查、真实端点/CA 校验和失败即时报告共同拦截，不能再靠操作者记忆。
- **TikTok 单列滚动（2026-08-15）**：当前 bundle `async/89993.30b4c2a9.js`（SHA-256 `C4D4867C5C6C89DCE560D429A4686427C911267DCBB2787AEB31B7BD333E9088`）使用 200 ms、`cubic-bezier(.2,.2,.4,.9)`、目标 `offsetTop`，滚动时临时禁用并恢复 `scrollSnapType`。Peach 复用时长和 easing，保留自己的两视频预载与 wheel/touch 队列。
- **Apple 播放控件（2026-08-15）**：Apple HIG 「Playing video」 只支持熟悉、克制的传输控制语义，没有提供可复用的 `gobackward.10`/`goforward.10` Web SVG。Peach 使用固定版本的 Lucide 子集和明确的「后退/前进 10 秒」无障碍标签，不声称精确复制 iOS glyph。
- **Vercel 设计规范（2026-08-15）**：`https://vercel.com/design.md`（SHA-256 `07ED2923294AA326F65F9D9D4094B6E97BF7DE10C39ACD8BE935F2045C5A688F`）只作为评审清单：先用字体和间距建立层级、保持连续画布、避免任意图标瓷砖/嵌套卡片/微小灰字，动画只表达状态或连续性。
- **kill-ai-slop**：在 commit `96d1ca568a1db7e1ef9a381644c744440f816ee4` 上作为减法审计清单使用，不安装 skill、不复制 scanner。
- **Lucide**：通用操作和导航图标使用固定本地 `lucide-static` 1.31.0 子集（ISC）；许可见 `web/vendor/lucide-LICENSE.txt`。品牌/来源 Logo 和计时圈不属于通用图标。
- **Rule34 样式**：旧代码注释没有 DOM/CSS 证据，已删除「Rule34-style」声明。当前标签颜色是 Peach 自有语义。
- **T3 Code/CodexBar 用量**：这是复用决策，不是 Peach UI 复制。T3 Code 已提供 Codex + Claude 历史 token/成本界面；实时剩余额度使用官方 Provider 入口，Peach 不再造日志扫描器。
- **标签添加弹窗（2026-08-15）**：用户提供 macOS 标签管理弹窗截图，未提供产品名或可访问 URL，源码证据为 `未取得`。Peach 只复用截图可证实的交互层级：搜索、最近使用、全部标签、已选状态和键盘上下/Enter/Escape；不声称像素或源码级复刻。
- **YouTube 详情参考（2026-08-17）**：实时取得 `https://www.youtube.com/watch?v=dQw4w9WgXcQ` 当前页面 HTML；页面使用 `Roboto`、暗色详情播放器与高对比控制条，播放器资源预加载 `hqdefault.jpg`，当前页面 bundle 版本由 WIZ 配置标识为 `youtube.web-front-end-critical_20260811.08_p0`。用户同时提供详情/卡片截图。Peach 只复用可复现的层级原则：详情操作采用连续圆角操作组、hover 提亮、active 使用蓝色语义；播放区 ambient 使用模糊画面并向上下渐隐。未复制 YouTube 品牌、播放器源码或登录能力。
- **YouTube Shorts 播放/动作栏参考（2026-08-17）**：实时取得 `https://www.youtube.com/shorts/BJynPKgwfyA`，页面 `INNERTUBE_CLIENT_VERSION=2.20260813.05.00`；协作浏览器快照未取得，但运行时 DOM/CSS 可复核。`#shorts-player` 为 `396×704`，视频 `object-fit:cover`；右侧动作容器宽 `72px`、左右内边距 `12px`；动作按钮为 `48×48px`、`rgba(255,255,255,.1)`、圆角 `24px`，文字位于独立的垂直标签容器；全屏按钮同为 `48px` 圆形。Peach 复用 48px tonal 圆形和克制的动作层级；横屏片源全视口 cover，竖屏片源按真实宽高切到 contain 保留完整画面，并保留自己的 Lucide 图标、色彩 token、横竖屏混流和业务反馈语义。
- **Javinizer-Go 元数据 Provider（2026-08-22）**：取得官方仓库 `https://github.com/javinizer/javinizer-go`、v1.5.1 release 与 tag commit `f57985c8c98a0ad7283f72854c249b8612300637`；macOS arm64 SHA-256 `6197d78c…f179d`、Windows amd64 SHA-256 `4d5b0bc6…1abca` 均与发布值一致。Windows 必须锁定 subprocess UTF-8，且 r18dev 要显式绑定 `scrapers.r18dev.proxy.profile` 才走 7897。`IPX-535` 已验证真实单来源 JSON；Peach 只发送规范番号、逐源留原始证据，并为演员/厂牌/系列/发行日期/内容标签形成字段候选，官方 tag 优先，批准后才写 ledger，不使用其 organizer。
## 智能体用量与任务路由

- 调度看官方配额窗口，不看 API 等价美元估算。Codex 使用 App Server `account/rateLimits/read`；Claude 使用 Claude Code 已登录用量界面。不得打印、复制或保存 OAuth token。
- Codex 负责架构、迁移、浏览器依赖网站、最终 review/apply 和长期任务；Claude 负责边界明确的刮削、归一化、候选 CSV 对账、文件名/番号/水印提取和经复核的风格板分类。
- 女优/创作者归属可使用发行番号、文件名、水印、厂牌、别名、公开链接和跨来源一致性。人脸最多用于同库一致性辅助，持久身份仍需非人脸证据。
- 目录名只是一条候选证据。当前扫描器已停止从目录生成创作者；历史 `legacy:asset` 关系使用 `scripts/audit_creator_attributions.py` 逐项审计。即使目录名与真实创作者同名，也不能把整个子树直接传播成创作者真相。
- 待办数量统一报告「可执行 / 被阻塞 / 合计」。例如 PikPak 的 4,740 与 10,196 不是矛盾：前者有时长可抽帧，另有 5,445 条缺时长需先 probe。

## 批处理失败值与流量边界

- 测量失败不能写成下游可误认的正常值。`probe.py` 曾把「ffprobe 无时长」写成 `duration=0`，导致数据同时退出 `duration IS NULL` probe 队列又进不了 `duration>2` 抽帧队列。现在失败写 `-1`，并提供 `--redo zero|failed|all`。
- 两组状态数字看似矛盾时，先查是否有两边查询都遗漏的状态，不要直接认定其中一组错误。
- 2026-08-15 的 115 抽帧曾把系统盘写到零：接触表在 `R:\peach-data`，真正膨胀的是 CloudDrive 位于系统盘的稀疏读取缓存。`file_buffer_disk_cache_max_bytes` 现为 50 GiB、策略为 LRU；CloudDrive 退出时会重写配置，后续必须复核该值是否保留。
- 起跑前一次 `require_free_space` 不是运行期闸门。`DiskGuard` 默认每 20 秒重读 `C:` 实际余量；`probe.py`、`sheets.py` 和 `creator_boards.py` 触线后停止取新任务、保留已完成结果并返回退出码 3，不能伪报正常完成。
- Windows 查询已消失 PID 可能抛 `OSError(winerror=87)`，不是 `ProcessLookupError`。`PidFileLock` 必须把它识别为陈旧锁并安全清理。
- 2026-08-15 经 mihomo 实测：115 单文件 ffprobe 约 25 MB，九帧接触表约 285 MB；PikPak 单文件 probe 12–52 MB，九帧约 163 MB/13.7 秒。PikPak 抽帧的主要约束是字节而非耗时；Windows 夜跑步骤见 `docs/PIKPAK.md`。
- `-probesize`/`-analyzeduration` 无法减少 CloudDrive 固定块预取。创作者板在未知时长时可回退到 60 秒 seek，因此无需先花约 207 GB 做全量 PikPak probe。
- 200 GB 守卫默认只统计代理流量，能覆盖 PikPak，不能看到直连 115；需要覆盖直连来源时显式使用 `--count-direct`，且不要在同一直接计量窗口混跑不同来源。
- 短促测试无法刻画会累积的限流。r18 在 12 个请求的实测里 1.0 秒间隔全过，据此把默认从 2.0 降到 1.0，结果连跑约 18 分钟后开始被拒，556 位里 203 位被判成假阴性；改回 2.0 秒连跑 62 分钟稳定。限流参数只能用与真实批次同量级的运行来标定。
- 限流是各主机自己的事，不是整个任务的属性。`HostLimiter` 按主机各记一个下次可发时刻，线程等 r18 的空档时去查 av-wiki 和 javdb，实测 12 位从约 8 秒/位降到 4.4 秒/位。r18 每位要两个请求，这是并发压不掉的下限。
- 长任务必须能续跑。一次未捕获的 TLS EOF 曾让 62 分钟的批量结果归零：网络异常要降级为空值而不是抛出，结果要定期写入文件，`--resume` 只把成功判定当作已完成——`no_name` 这类多半是限流假阴性，冻结在复核文件里就再无重试机会。

## 身份合并与来源分工

- 规范名优先使用有出处的简体中文通行名，暂无可靠中译时保留日文，旧艺名、罗马字、假名和繁体名都降为别名。姓名写入不得再和头像成功绑定：`no_avatar` 只表示没取得合格图片，不得阻止已核实姓名落库。多个实体精确命中同一姓名映射时按同人走 `merge_entity`，资料不足时保留原名、不猜译。
- 「这一页只有一位女优」永远不构成证据。库里大量番号是 BEST 合集（一部片可列 8~11 位），搜索无结果的页面仍会渲染推荐文章，改名后 slug 也会变。同一个错误判据在 javdb、av-wiki 两处各犯过一次，都是靠 dry-run 拦下的：一次让两位不同女优被认成同一人，一次让 5 位里错 3 位。精确回配命中优先于任何「唯一」推断，「唯一」只有在两个番号同证时才作数。
- `entity(kind, normalized_name)` 的唯一约束冲突通常不是 bug，而是信号：两个实体其实是同一人的新旧艺名。合并走 `peach.entities.merge_entity`，保留作品多的一侧，迁移关系/别名/外部引用/链接/搜索词，并把所有旧称留作别名。`entity_external_ref` 每个 provider 只能留一条，同源的第二条会被丢弃并报告，不能静默覆盖。合并不可逆，必须先取得用户授权并备份。creator / performer 跨类重复不用「作品数多的一侧」规则：只有两边非空作品集合完全相同，且 performer 别名精确命中 creator 名，或 creator 名由 performer 本名与账号别名组成时，才能自动归并；`r18:performer` / `javbus:performer` 是正式发行出演元数据，保留 performer，通用 `performer` 是 Stash 压平后的兼容断言，保留 creator。合并时必须同步 `asset.creator` 与 `演员:` 兼容投影，否则已删实体仍会在详情页伪造链接。`XX XX` 是来源节点文字重复，不是合法别名：person 名进入 CSV、兼容字段或 `upsert_asset_entity` 前先收敛完整重复串，JavBus 的「画像を拡大する」控件文字必须丢弃；清理要同时审计 `asset.creator`、`演员:` 标签和 `entity_alias`，upsert 按稳定外部引用、规范名、唯一别名依次复用实体。重复 creator 与发行 performer 即使因多版本导致作品集合不同，只要重复串精确命中 performer 名/别名且有发行来源，也属于高置信合并。
- 改写 `entity.canonical_name` 属于真相字段写入，与迁移同级：`--apply` 必须同时给 `--backup`。
- 头像与厂牌 Logo 的取源方向相反。头像去精心整理的图库（Gfriends 约 10.7 万张，目录名首字符即质量档位），不要回官方站——同一张脸 DMM 官方只给 125×125，图库存的是 500×500 起，最高 1500×2125。Logo 是品牌标识，官网与维基才是权威来源。
- 头像门槛按长短边分别判定（长边 ≥500 且短边 ≥300）。竖构图人像宽度天然小，套用为方图设的「短边 ≥512」会拒掉 `0-Hand-Storage`(334×501)、`8-GRAPHIS`(360×508) 这些最优来源。
- 可用来源实测（2026-08-15）：r18.dev、av-wiki.net、javdb.com、Gfriends 可用；javlibrary、missav、xslist 被 Cloudflare 拦，njav 有验证墙，jav321 无独立女优字段。被 Cloudflare 拦的站一律放弃，不绕过机器人检测。
- 番号目录被投影成创作者时，判据只能是文件级证据，不能是名字形态。`HD-abp-758`、`pppd-937ch`、`banbi_555`、`AH18` 四者形态相同，真相完全不同：前两个是发行目录（`HD-` 是画质、`-CH` 是中文字幕版，都会让番号提取放弃），第三个是 myfans 账号，第四个是 pixiv 画师。唯一可靠的区分是「目录内的媒体文件名是否解析出同一个番号」——账号目录里放的是作品标题，天然不命中；pixiv 行的 `path` 是 URL，先按这一点排除。`scripts/audit_code_creators.py` 就是这条判据的实现，存疑一律留复核 CSV。
- 画质前缀（`HD`/`FHD`/`4K`/`1080P`）和版本后缀（`-C`/`-CH`/`-UC`/`-SUB`）不是番号的一部分。番号提取器必须先剥这两层再匹配，否则 `code` 留空、目录名顶替身份，两个错误一起发生。
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
- 正式迁移 `0000`–`0014` 已应用。`0003` 增加默认 profile、稍后看、实体链接和搜索词；`0004` 增加 FTS5 trigram；`0005` 回填晚到兼容标签；`0006` 增加 `asset_preference`；`0007` 从创作者身份中移除结构文件夹名 `门槛`、`视频`、`宣传文件`；`0008` 增加 profile 级标签隐藏；`0009` 移除结构集合目录 `asce` 的假创作者关系和低置信 `vision_creator` 传播；`0010` 把 83 条「足交仙人」按水印和文件名证据归到 `suzuq`，并从 745 条 TokyoDolls 资产解除错误的「捅主任」关系；`0011` 记录更好版本目标；`0012` 增加跨访问端共享搜索历史；`0013` 将旧待删状态统一为回收站，默认查询排除回收站，清空回收站才永久删除；`0014` 清理明确的创作者 URL 后缀并保留旧名 alias。
- `0007` 曾在应用后、提交前被改写注释/格式，导致校验和漂移。本次用迁移前备份重放当前 `0007`，对 298 条受影响资产与生产结果逐条对比，差异为 0 后才校正 `schema_migration` 校验和，然后正常应用 `0008`、`0009`。已应用迁移文件从此不得修改，任何后续变更必须新增版本。
- 外置盘目标只保存 `R:\media`；代码、运行数据、venv 和 worktree 在两台机器各自的内置盘。`peach-data` 不进入仓库，也不整体交给文件同步。分通道边界见 ADR-0017。

## 运行与部署

- Windows 日常入口是当前用户 Startup 中的唯一 `Peach.lnk`，指向 `C:\Users\longm\Desktop\peach\peach-app\dist\Peach\Peach.exe`。`R:\peach-app` 是迁移前的旧位置，不再用作运行入口。
- Windows 发布入口使用 `scripts/build_windows.ps1`：先用 `scripts/generate_brand_assets.py` 从原始附件生成正方形 `resources/peach-logo.png` 和多尺寸 `resources/peach.ico`，再构建单一 `dist/Peach/Peach.exe`。无参数运行托盘，`serve`/`migrate` 运行 CLI；桌面快捷方式由 `scripts/create_desktop_shortcut.ps1` 创建，图标使用 `Peach.exe,0`，行为与 FlowLens 的快捷方式一致；Startup 安装仍由 `scripts/manage_tray_startup.ps1` 负责。
- `dist/Peach/Peach.exe` 是本机打包入口，不是可移动的独立发行版：托盘只打包了自己，服务进程仍由项目 venv 的 `peach.exe` 承担（`_peach_executable()` 从 exe 位置逐级向上找 `.venv\Scripts\peach.exe`）。脱离同一台机器的项目 `.venv` 复制不会工作，不要按「单文件绿色版」对外描述。
- 托盘单击打开 HTTPS；macOS/Windows 菜单都提供「同步 Ledger」「接管 Ledger 写入」、状态、重启、日志和退出。HTTP/HTTPS 服务只观察角色，不自动复制；手动同步先停止自己创建的服务，再用 SQLite backup API 与原子替换复制，最后恢复服务。共享源在 macOS smbfs 上必须以 immutable 已关闭快照读取；共享目标不能由 SQLite 直接打开事务连接。健康端口不归本托盘时拒绝接管。
- 创建 Win32 窗口前必须启用 Per-Monitor V2 DPI。正常动作不弹模态 MessageBox；更新检查在后台线程执行，用 pystray 原生非模态通知反馈。
- `src/peach/__init__.py::__version__` 是版本唯一来源；采用 pre-1.0 SemVer。Git commit 是构建标识，`vX.Y.Z` 是本地发布点。更新检查只 fetch/比较，并行 worktree 模式下不自动覆盖安装。
- `scripts/manage_tray_startup.ps1` 是唯一自启动管理入口。托盘管理 HTTP `0.0.0.0:80` 和当前路由选出的 LAN IPv4 上的 HTTPS 443；显式参数、`PEACH_LAN_ADDRESS`、`lan_ipv4()` 依次覆盖。服务日志写入本机 `peach-data/logs`。
- `peach serve` 按平台发布固定主机名：macOS 为 `peach.local`，Windows 为 `peach-win.local`。Windows 不在源码钉家庭 IP，仍保留 `Zeroconf()` 全合格网卡监听。mDNS 验收必须包含单元测试、运行态 health、DNS-SD、主机名解析和真实 LAN 客户端。
- `.local` 使用本地 CA，不使用 Let's Encrypt。证书/私钥保存在本机 `peach-data/secrets`。TLS 私钥禁用 ACL 继承，只允许实际服务身份、SYSTEM、Administrators；当前 Windows 服务身份是 `longm`。macOS/iOS 只安装并信任 `peach-local-ca.crt`，不得分发 CA key 或服务器 key。
- FastAPI 是唯一 Web server。不得恢复平行 `http.server` 或动态 legacy loader。配置 `--token` 时通过 `/login` POST 取得 HttpOnly cookie；旧 `?t=` 只做一次兼容重定向，dependency 统一 JSON contract 鉴权但不替代登录流程。
- FFmpeg/ffprobe 依次从显式环境变量、本机 `peach-data/tools/ffmpeg/bin`、`PATH` 解析；不得回退到 Stash 私有目录。
- 长任务只停止自己拥有且命令行匹配的 Python/FFmpeg 进程树，禁止全机终止 FFmpeg。
- 导入运维脚本不得触发文件、网络或数据库副作用。`scrape_codes.py` 默认写可续跑复核 CSV；`clean_names.py` 先预览，`--apply` 前备份 SQLite。
- 切换服务前检查 80、443、8900、9999 端口和实际进程归属。
- 115/PikPak 播放依赖 CloudDrive 的 `B:`/`A:`；盘符对 Windows token 可见性不同，最终以 Peach 对已知作品的 `/stream` 实测为准。
- 浏览器不支持的 AVI 等容器由 `TranscodeService` 缓存为 H.264/AAC MP4，再通过同一 Range 端点提供；永不改写原媒体。
- 数据库元数据不得插值到 inline JavaScript 事件属性。真实厂牌名中的撇号曾直接造成 Firefox 语法错误。前端 API 包装必须先检查 HTTP 状态再返回 JSON；冲突只读时写端点会返回 `409` 和错误 JSON，把它当普通成功对象会清空选择并重载，用户只会看到条目原样回来。批量处置和详情反馈必须保留当前选择并明确显示失败原因。
- 验证分开报告：静态/单元/API、桌面浏览器、390×844 手机、生产服务是否已重启。

## 当前架构真相

- Ledger 拥有真相和行为；Stash 是可替换适配器，调用统一经过 `StashClient`，外部 Scene ID 和来源进入 `media_binding`，不新增直接 GraphQL helper 或 Stash 私有 FFmpeg 路径。规范女优/厂牌/标签/创作者进入 `entity`、`entity_external_ref`、`asset_entity`；扁平 `asset_tag` 和 creator/studio 字段只是兼容投影。
- 详情、筛选、搜索、facets、索引、统计、榜单和相关推荐使用规范关系；JAV 入口除番号形态外还要求厂牌、女优、系列或发行日期等发行证据，FC2 ID 单独成立，creator-only 的 `JI-103` 不算 JAV。
- 女优、厂牌、创作者、系列名称进入资料页；首页内容标签直接筛选首页，实体资料页的标签只筛选当前实体作品，并保留在 `/performers/{name}?tag=...` 等当前资料页 URL。`source_reference` 是私有来源，不开放为下载链接。
- 「稍后看」写 `watch_queue`；「喜欢/为什么喜欢」写 profile 级 `asset_preference`。AI 只能把口味说明转成带来源/置信度/复核状态的候选，不能改写用户原文。
- Web 公共路由使用 `/performers/{name}`、`/studios/{name}`、`/creators/{name}`、`/series/{name}`；删除 `/entity/{kind}/{name}`。收起详情或导航离开时必须 pause、清空 `src`、调用 `load()` 并移除 video，不能只隐藏 DOM。
- 「换一批」、统计、沉浸、全部女优、全部标签是动作/目的地，不显示为持续筛选状态。顶部只保留「没看过、稍后看、已标记」等需要主动进入的紧凑状态；「看过」和「疑似广告」不占首页快捷位。
- 长卡连续 hover 5 秒才放大并显示 seek；短卡立即提供「稍后看」。实体文字链接必须消费点击，不能冒泡为展开视频。
- 卡片身份女优优先：先使用 `performer_entities` 头像和链接，再回退到创作者/厂牌代表图。
- 喜欢与原因属于同一 profile 偏好；非空原因隐含喜欢，但原文不能直接冒充推荐特征。
- 详情身份按规范化名称去重；女优与厂牌按内容宽度自然相邻，空间不足时自动换行；创作者独立分组。系列使用无外框、无下划线的 `tags` 图标链接显示全称，不复用标签胶囊或头像格。喜爱理由由反馈操作组中的图标展开；首页流与详情的来源只显示图标，完整名称与费用留在 title/ARIA，侧栏来源筛选保留文字。观看进度只显示标题和百分比，反馈操作组不得作为可收缩的 Flex 项；寻找高清版直接切换标记，并在管理区 `/quality-goals` 汇总。旧短/中/长片标签不再显示，时长筛选只使用分钟区间。
- 反馈使用 Lucide 紧凑图标工具栏。删除操作统一进入回收站；普通查询排除回收站，回收站入口的「清空回收站」才永久删除媒体与对应 ledger 关系。
- 界面文案不复述标题、控件或实现状态，不用随机示例占位符和模型自我声明；只保留影响决策、防止数据损失、说明隐私/费用或解释陌生状态的文字。
- 桌面筛选抽屉只在指针进入可见 72 px 侧栏后打开，不恢复内容区隐藏热区。
- 厂牌 Logo 使用带来源的官方缓存；缺失时显示首字母，不得用任意作品图冒充，覆盖进度见 `docs/STATUS.md`。
- 实体头像优先 `generated/avatars/<kind>-<entity_id>.img`；Stash 默认剪影和搜索结果缩略图不能作为头像。
- 厂牌归一化使用 `scripts/canonicalize_studios.py`，默认 dry-run，apply 前备份。`PREMIUM` 是独立厂牌；只把 Prestige Premium 和日文 Prestige 写法归并到 `Prestige`。
- FastAPI 与前端逻辑分离、单体部署；在线来源和 AI 只通过显式适配器进入。
- `FeedAdapter` 是首个追更连接器，显式、有界发现 RSS/Atom；不在应用启动时轮询，不直接写 ledger。
- AI 推理 API 与本地 coding/agent runtime 是不同层，不能伪装成一个等价接口。
- 3 字符以上搜索使用 FTS5 trigram；更短文本回退 LIKE。FTS 写入由迁移 trigger 维护，不在 Web 启动时修补。
- 详情身份按规范化名称去重：同一个名字已显示为女优时，不再重复显示「创作者」。标签的 × 写入 profile 级隐藏覆盖，不删除刮削/识别断言；+ 新增标签以 `web-user` 同步写入兼容层与规范实体层。
- 卡片多选有显式模式；普通点击打开详情，`Ctrl`/⌘ 切换单项，`Shift` 以上次选中为锚点选中当前可见网格范围。批量操作仍必须二次确认。待删只是候选，但卡片必须灰化并显示状态，不能仅靠不显眼的小点。
- `/tags` 是独立标签管理页，默认字母表模式，也可切换标签云；两种模式都显示数量并进入首页组合筛选。
- 高潮按钮复用 Health Icons 官方 `outline-24px/contraceptives/sperm.svg`，来源 `resolvetosavelives/healthicons`，CC0。一般操作继续使用本地 Lucide 子集。
- 账本路径大小写不一致时的重新匹配实现在 `peach.media.resolve_case_insensitive`（同目录 casefold 匹配，`lru_cache` 512 条；NTFS 上 `is_file()` 已不敏感，正常不触发），`FilesystemBackend.file_for` 与 `scripts/sheets.py`、`scripts/probe.py` 的 worker 都已接入。这两个脚本直接用账本路径跑 FFmpeg、不走 MediaEngine，新增同类脚本时必须自己调用，否则大小写敏感的挂载层（CloudDrive/APFS）会抽帧失败。
- `scripts/sheets.py` 抽帧遇到 `prim:reserved` 非法色彩元数据会自动带 bt709 声明重试（`_capture_frame`）：正常文件走原命令零影响，失败帧才重试，不能为了「修复」把色彩覆盖无条件加到所有输入上。

## Web 性能边界

- 页面不得按结果总数一次构建全部卡片。首页默认每批 60，可在设置中改为 30/60/90；短片栏 18、相关推荐默认 20（可选 12/20/30）、沉浸队列 60、实体作品 48、艺人索引 120、标签索引 180。疑似广告候选可在服务端统一评分，但浏览器也必须按当前首页批量分段追加。
- 实体页的总数只用于标题和首批分页判断，第二页起请求使用 `count=0`，通过多取一条判断是否还有下一页，不得重复执行全量 `COUNT(*)`。首页无限滚动同样只在首批计算总数。
- `q_tops`、艺人索引和实体关联艺人的代表图必须使用单条相关子查询取得，禁止按每个人物再发一次 SQL 的 N+1 实现。
- 首页聚合数据在浏览器会话中合并并缓存 30 秒；相邻筛选复用同一进行中的请求。所有页面表面的异步响应都必须核对请求序号和当前路由，迟到的旧响应不得覆盖新状态或再次重建 DOM。
- 所有返回首页的入口必须复用 `showHomeSurfaces()`，同时清除实体页状态、隐藏统计/索引页，并恢复 `#tiers` 与 `#tagbar`。统计页会把这两层写成内联 `display:none`，不能只靠重新取首页数据恢复，否则 Logo 回首页会留下空白顶栏。
- 顶部标签条只能横向滚动，纵向必须隐藏溢出；卡片身份只显示在头像/名称链接，不得再复制成内容标签。搜索推荐词必须是能直接提交的真实关键词，例如 `ABW`，不得写成无法命中的说明短语 `ABW 番号`。
- 「已标记」是正向收藏入口，只包含 profile 的 `liked=1` 或至少记录过一次高潮的作品；不喜欢、看过和待删分别属于负反馈、观看状态和处置流程，不得混入。
- 无限滚动同一时间只允许一个追加请求；先判断加载锁再递增 offset，避免快速触发时跳页。图片继续使用原生 `loading=lazy`。只有本地资源可使用真视频 hover；115/PikPak 等远端源必须使用本地接触印相。滚动、换页、隐藏页面或替换卡片 DOM 时，统一停止 hover 并释放 `src`。
- 2026-08-15 实测：Prestige 显示 248 个总结果时首屏只构建 48 张卡片，点击「载入更多」后为 96；艺人索引 120 条约 311 ms，Prestige 第二页 48 条且跳过总数统计约 94 ms。具体耗时随 ledger 和磁盘状态变化，只把批量边界作为稳定契约。
- 0.5.5 起，标签筛选行与排序/换批行都常驻顶栏下方，不再按滚动方向隐藏；两行在原始位置保持透明，只在真正吸顶后加半透明黑色磨砂底与分隔线，分别占位，不能盖住卡片内容。窄屏上的结果数量和全部排序按钮必须同处一条横向滚动带，文字不折行、按钮不压缩成竖排。
- 0.6.1 起，首页每批 60 个普通作品中只插入 1 个自动 Mix 卡片，不额外请求 60 份队列，也不计入作品分页数。卡片复用本批已有种子，点击时才并行请求种子详情与一次 `/api/related`，队列上限 29 个，避免 N+1 和首屏批量构建。Mix 使用 `/mix/{seed_id}/{item_id}`，刷新和前进/后退可恢复同一队列；桌面端播放器右侧显示当前项着色的滚动列表，窄屏列表移到播放器下方。普通详情继续显示「接着看」，Mix 内不再重复渲染第二份相关推荐。
- Mix 视觉证据来自用户于 2026-08-16 提供的 YouTube 截图 `codex-clipboard-8f6cbb25-399a-4f91-9c2a-a6972484ed50.png` 与 `codex-clipboard-baeb854e-3e27-43fb-9e6a-aa14830c248a.png`：普通流卡片有两层轻微上移的堆叠边、右下角 Mix 标识；打开后右侧是有当前项状态的滚动列表。Peach 有意保留自己的色彩 token、详情反馈区和本地元数据，不复制 YouTube 品牌、推荐文案或登录能力。
- 首页、女优、厂牌等普通卡片统一由 `wireCards` 调用 `openItem`。只有沉浸/短片等显式传入 `onClick` 的场景允许覆盖。隐藏的 hover 工具必须 `pointer-events:none`，只在实际显示时恢复命中，避免截走海报详情点击。
- 详情媒体用随机 `session` 标识同一次播放；收起详情、路由切换或替换详情时，前端必须清空 video 后调用 `/api/stream-cancel`，服务端取消该 session 下全部 Range/HLS 片段请求并拒绝迟到请求。只移除 DOM 不能保证 CloudDrive 停止读盘。
- 115/PikPak 继续采用视频网站式按需加载，不增加「点击后才拉流」的额外门槛。已知时长的原生 MP4 通过 `/api/stream-plan` 进入 6 秒 HLS VOD 清单；每个 TS 片段由 FFmpeg 对挂载文件执行目标时间 seek，响应后删除临时文件。不能把 HLS 失败伪装成成功，播放器必须回退标准 `/stream` Range；也不能再次人工截短 `Content-Range`。
- 详情播放器固定复用本地 Video.js 8.23.9（Apache-2.0），不依赖 CDN。控制栏总时长优先采用 ledger 探测值；item 29297 的 `moov/mvhd` 位于文件头，真实总时长为 28,639.916 秒，说明旧「越播越长」不是媒体缺少头部元数据。统计面板同时区分 HLS 与 HTTP Range，并继续读取内置 VHS 的请求、带宽和字节统计。
- 详情播放器全屏时必须覆盖 `76vh` 和 `aspect-ratio` 限制，否则浏览器全屏会留下底部黑区；沉浸模式横屏片源使用全视口 `object-fit:cover`，竖屏片源必须按视频真实宽高切到 `contain`，不能裁掉上下画面。加载速度显示优先使用 Video.js VHS `stats.bandwidth`，再回退到当前 session 的 `PerformanceResourceTiming`，不把 FlowLens API 耦合进页面。
- Peach 测试唯一入口是 `& .\scripts\test.ps1`；脚本内部运行标准库 `unittest`，仓库不依赖 `pytest`。健康检查端点是 `/healthz`，不是 `/health`。
- 2026-08-18 回环实测（`/stream?id=823`，取前 200 MiB）：直接读盘 761 MiB/s、Peach HTTP 136 MiB/s、Peach HTTPS 142 MiB/s。TTFB：`/healthz` 36 ms、`/stream` 首块 40 ms、中段 Range 41 ms、`/api/items?limit=60` 167–405 ms。结论是吞吐不构成瓶颈（千兆 LAN 上限本来就低于它），感知慢要从并发槽位、缓存策略和每请求固定开销去找，不要再重复测吞吐。
- 当前部署的三个已知延迟来源，改动前先看清代价：`/stream` 带 `Cache-Control: no-store`，浏览器无法复用任何已下载片段；uvicorn 只提供 HTTP/1.1 且未安装 `httptools`（回落到纯 Python h11），浏览器对同源限 6 条连接；Starlette `FileResponse` 的 `chunk_size` 是 64 KiB，每块一次线程池读、ASGI send 和可能的 Python TLS 加密。hover 每次悬停产生 1 条 `/stream` 加 7 次 `currentTime` 跳段，共 8 个不可复用的 Range 请求，必须计入连接预算。Windows 千兆线路理论上限约 125 MB/s；115 实测单文件由 CloudDrive 启动 2 条约 2 MB/s 的 CDN 连接，`max_download_speed_kbyps=0` 表示未设本地限速。卡顿先查 FlowLens 是否有详情关闭后的残留下载，再查 Range/缓存，不把单连接速度直接归因于本地带宽。

## 本机服务、系统代理与双机广播
- **对本机服务的 HTTP 探测必须 `trust_env=False`**。代理客户端（Stash、HapiGo、Surge）会设置 macOS 系统级 HTTP 代理，httpx 默认经 `urllib.getproxies()` 读它，探测 `127.0.0.1` 的请求被送进代理、由代理回 503——服务活着却被判「未运行」。2026-08-21 实测如此，修复在 `peach.tray.ServiceManager.healthy`，`test_health_check_never_goes_through_a_proxy` 守门。任何新写的健康检查/回环探测都适用同一条。
- **macOS 系统代理例外列表必须包含 `*.local` 和 `192.168.50.0/24`**。浏览器走系统代理时，代理核心解析不了 mDNS 名字，`http://peach.local` 会被代理回 503（终端直连正常，所以只有浏览器坏）。用 `networksetup -setproxybypassdomains <服务> "*.local" "localhost" "127.0.0.1" "192.168.50.0/24"` 设置，`scutil --proxy` 的 `ExceptionsList` 复查。代理客户端重设系统代理后这一列表可能被清掉，排查浏览器打不开 `.local` 时先看这里。
- **双机广播分工：macOS 固定 `peach.local`，Windows 固定 `peach-win.local`**。默认值已收敛到 `peach.config.MDNS_NAME`，`PEACH_MDNS_NAME` 只做临时覆盖。服务可以同时跑（账本单写者复制兜底），但两边同时写入会很快冲突转只读。
- **两台机器各有独立的本机 CA**（secrets 按设计不共享）。iPhone/iPad 必须信任「当前正在服务的那台」的 CA 才能用 HTTPS；换机器服务后要装对应的 `peach-local-ca.crt` 并在「证书信任设置」开完全信任。核对指纹：`openssl x509 -in .../peach-local-ca.crt -noout -fingerprint`。菜单栏状态行逐个点名每个服务：`HTTP 正常 · HTTPS 异常（状态码 503）`，异常附最近一次失败原因；不要改回只报「未运行」。
## 恢复入口

项目重构时已从活动目录删除 deprecated 脚本和按日期文档，Git 历史仍可恢复。旧 `_SHARED_STATE` 已迁到 `R:\peach-data\state`。重构前根仓库元数据暂存于 `R:\peach-data\archive\peach-root-repo-backup-20260814`，仅作恢复证据。
