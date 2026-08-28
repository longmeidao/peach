# Peach 当前状态

最后核验：2026-08-28

本文件只保存当前运行态、已核验能力、仍需完成的工作和自动统计。已完成批次、旧测试数字与事故过程由 Git 历史保存，不在这里累积。

## 运行态

- Windows 是当前 ledger writer。启动入口为 `C:\Users\longm\Desktop\peach\peach-app\dist\Peach\Peach.exe`，代码、数据、worktree 和共享传输点都在 `C:\Users\longm\Desktop\peach\` 下；外置盘只提供 `R:\media`。
- 托盘必须以普通权限启动：提升权限后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报为脱盘。异常时从托盘退出，再由资源管理器或普通权限终端启动。
- Windows HTTP 为 `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名为 `peach-win.local`。线上服务版本最后核验为 `0.7.4`、`ledger_sync=writer`。
- macOS 是 reader，代码在 `~/Desktop/lmd.gg/peach/peach-app`，数据在相邻 `peach-data`；`peach.local` 经 8900/8443 和 pf 提供 80/443。GET 正常，写入端点返回 409。
- 2026-08-27 核对 macOS：服务子进程已跑当前 `master`，但菜单栏进程仍是旧代码。托盘层改动要生效，需手动退出菜单栏项后由 `.app` 或 `launchctl kickstart -k` 重启一次。
- 两端固定使用不同 mDNS 名和各自本机 CA；CA 私钥、服务器私钥和凭据不跨机同步。生成资产由 Syncthing 单向 Windows → Mac，Git 与 ledger 复制是另外两条链路。
- Windows 真实 ledger 为 `peach-data/database/ledger.db`，已应用到 `0021`，共 22 个迁移且 0 待处理。迁移前一致快照为 `database/ledger.pre-follow-alias-20260827-213205.db`，迁移入口另生成 `database/ledger.pre-migrate-20260827-214518.db`。
- Mac ledger 已于 2026-08-27 经授权从共享副本显式拉取并恢复 `in-sync`，writer 仍是 Windows。拉取前备份为 `database/ledger.pre-pull-gen32-20260827T062519Z.db`；前后 asset 81554、entity 8182、asset_entity 155541，完整性正常且外键违规为 0，证明原 conflict 仅是 SQLite 物理布局与 marker 漂移。
- Mac 的 `peach-data/sources` 已迁到内置盘；`archive`、`tools` 仍可指向外置盘。追更证据和浏览记录不再依赖外置盘。
- Stash 仍监听 `127.0.0.1:9999`，只作可替换适配器。Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。

## 已核验能力

- FastAPI 是唯一 Web server；Ledger 保存资产、规范身份、行为和复核决定。Stash 与 CloudDrive 都经适配层进入，扁平 creator/studio/tag 字段只作兼容投影。
- 本地浏览器支持 MP4/WebM/Ogg；AVI 等由 `TranscodeService` 缓存成 H.264/AAC MP4。远端 MP4 默认走标准 Range，显式 HLS 使用关键帧对齐片段，失败会回退 Range，永不改写原媒体。
- 首页、详情、实体资料、标签管理、照片、播放列表、统计、品味、复核、回收站、关注管理和关注观看共用同一 SPA 与 JSON 契约；桌面和 390×844 手机均在验收范围内。
- 多女优卡片叠放前 3 个头像，只显示第一位姓名和真实总人数，例如 `かわいゆい 等 37 人`；详情与沉浸模式仍保留完整或扩展后的出演信息。
- 当前源码的在线追更支持 FANBOX、Patreon、SubscribeStar、kemono/coomer/pawchive、rule34video、rule34.xxx、Rule34 Paheal 和 f95zone；FANBOX 可选 Cookie 用于公开详情被验证页拦截时复用用户会话，Gofile Premium API token 可展开 FANBOX/F95 外部文件页。两份凭据只发给各自站点。SimpCity 仍被 DDoS-Guard 阻塞，Peach 不绕过机器人验证。官方渠道只读取公开免费发布，不绕过登录或付费墙。
- Rule34.xxx 来源 ref 大小写不敏感；迁移会合并分批添加造成的重复来源并保留条目状态。F95 的 `Collection(s)` 后缀不进入作者名，五个来源可归到同一作者组。
- 关注作者显示名与头像优先取经过固定主机校验的官方 FANBOX/Pixiv 页面，归档站只作回退。官方主页只出现一个明确作者名时，主页账号自动记为有出处的关注别名；已有映射尤其是人工作决定不会被覆盖，只有名称相似时仍只给建议。只支持真实历史分页的来源才显示「抓更早一页」。
- reader 的 `/review` 通过严格 Peach CA HTTPS 读取 writer 的归一化 JSON 并原子缓存；决定按钮和所有关注写操作仍锁定，不同步 SQLite/WAL 或原始候选目录。
- macOS Ledger 同步在共享根判为 `offline` 时会先通过 NetFS 尝试挂载 `peach-sync`，再重新判定；挂载失败才保留原离线结果，过程中不停止服务。默认使用 `peach-win.local`，可由 `PEACH_SHARED_SMB_*` 覆盖；对应主机没有钥匙串记录时快速失败，不弹出阻塞认证框。
- Windows 托盘与 macOS 菜单栏均提供「同步开发进度」。Windows 会先快进并运行正式测试；涉及打包输入时先构建和检查新 EXE，再退出旧托盘完成可回滚替换，失败不会提前停止现有服务。
- 搜索使用 FTS5 trigram，短查询回退 LIKE 并覆盖规范名、别名和检索词。搜索历史在 reader 写入被拒时降级到页面内存，不产生未处理异常。
- 回收站的单项删除和清空共用 `purge_assets()`：先处理媒体文件，再提交 ledger；删不掉的文件保留可见状态并回报，避免静默遗留。
- 复核页覆盖元数据、创作者标签、Logo、头像、身份、番号目录、FC2 证据和媒体失败。抓取与 AI 结果仍是候选，批准后才写真相字段。
- 浏览历史增量采集使用 SQLite backup API 与固定版本 `browserexport==0.4.4`，一致性读取本机 Chrome／Firefox／Zen／Safari，也接受 Google Takeout ZIP 和 browserexport SQLite／JSON／JSONL 导出；原始 URL、标题和导出文件只留本机私有目录，聚合候选不写 ledger。

## 本批修正与验证

- 0.7.5 将馆藏里同番号且带连续唯一后缀的 A/B、1/2、CD/Disc/Disk/DVD/Part/Pt/Vol 分卷派生为一张叠层卡片，标为“2 卷”而不是 Mix；卡片显示合计时长与大小，详情用“分卷”右侧队列按 A→B／1→2 切换。每卷仍是独立 asset 和播放会话，不拼接媒体、不写 ledger；重复标记、缺卷或字母/数字混用会拒绝自动合卡，重复文件页原有安全判定不变。Windows 真实 ledger 只读 POC 识别 82 组、197 个资产，含 `DVAJ-495-A/B`、`FC2-1464245-CD1/CD2` 等现有命名；`catalog` 375 项、正式 Windows 全量 1137 项均通过，13 项按平台跳过。
- 设置面板把圆角外框与内部滚动层分离，右侧滚动条不再把圆角切平。左侧导航可直接鼠标拖拽排序、逐项隐藏，并从全部顶层入口及统计、人工复核、疑似广告、重复文件、回收站、关注管理、高清版等具体页面中选择添加；窄栏和筛选抽屉继续共用同一份顺序。正式 Windows 全量测试 1133 项通过、13 项按平台跳过；临时账本浏览器实测隐藏 JAV、添加统计、拖拽事件链重排和 `/stats` 独占高亮均生效，桌面右侧上下圆角完整，390×844 无横向溢出且保留上下移动回退按钮，控制台无错误。集成后生产页面实时读取新资源，无需重启：HTTP 回环页实测外框 `16px` 圆角、内层独立滚动、导航拖拽属性、隐藏按钮和 7 个具体页面添加选项均生效，控制台无错误；80/443 持续监听，项目 CA 严格 HTTPS `/healthz` 返回 0.7.4、writer、非只读。调试遗留的 `127.0.0.1:8915` 临时服务已按监听 PID 清理，生产端口未中断。
- 照片标签不再先显示固定 3:4 的图集封面，直接按原图比例进入分页瀑布流；目录分组继续留在 API 兼容字段和旧深链中。JAV 女优、厂牌资料页复用首页的大图／小图／预览图按钮，切换时重画已载入卡片，不重复取数。
- 厂牌长条 Logo 的方图补边不再只看四角颜色：原图只要含透明像素就继续透明，完全不透明时才取整圈边缘主色。旧算法曾把贴边字样误认成底色，导致 `PREMIUM` 整张铺蓝、`HEYZO` 白字消失；17 个受影响的已安装 Logo 已从原图备份重建，错误版本另行备份。`/logo` 改为缓存但每次重载按 ETag 校验，避免固定 URL 继续显示替换前的旧图；项目 CA 严格 HTTPS 已确认两张响应与重建文件逐字节一致。
- 沉浸模式按用户提供的 YouTube Shorts 桌面截图重排：竖屏使用居中的 9:16 播放舞台，横屏使用在整个视口视觉居中的 16:9 大舞台；48 px 圆形操作按钮与文字分离，作者头像、身份和标题留在页面左下；390×844 手机继续使用全视口播放器。保留 Peach 的三项本地反馈、混合横竖屏队列和完整画面优先，不复制评论、分享、Remix 或订阅。
- 用户生产截图确认上一版横屏舞台贴右导致视觉失衡；同一截图还显示 HTTPS 服务 PID 47788 同时预读三部已切走的视频，子进程 PID 43080 正在转码 `IDBD-446_C.mkv`。根因是沉浸模式没有复用详情播放器已有的可取消 `session` 契约。本批为每个沉浸视频分配独立会话，并在切片、关闭、失败和页面离开时通知服务端取消。取证后 PID 43080 已自行退出；PID 47788 是正常 HTTPS 服务，不是下载器，3 秒复核读写增量均为 0，未强行终止任何进程。
- 正式 Windows 全量测试 1123 项通过、13 项按平台跳过。临时静态页面在 1440×900 下实测横屏舞台 922×518、中心偏差 0 px、无横向溢出；390×844 下舞台为完整视口且无横向溢出。浏览器控制台无错误；尚未重启生产服务。
- `5926ff4` 已合入 `master`：关注页改用与首页一致的作者头像和标签胶囊，压缩顶部间距；管理页不再残留目录标题；`深喉咙` 统一为 `深喉`；非视频主附件也会从同一发布的图片附件取预览图。
- Fiu758 只登记为厂牌 Logo 候选发现来源，不作真相源。17 个已安装横条 Logo 已原样备份并无损补成正方形；5 个损坏图片保持不动并进入错误报告。JAV 官方元数据批次生成 45 组候选，含 7 个日文系列名和 9 个官方标签，均未自动批准、未写 ledger 真相字段。
- 正式 Windows 测试入口跑完 1040 项，全部通过，13 项按平台跳过。桌面浏览器确认关注页顶部为 88px、无旧筛选控件、无横向溢出且目录标题隐藏；手机视口覆盖连续超时，截图验收为未取得，响应式源码契约测试已通过。
- 新 EXE 已部署到 Windows 生产入口，旧版备份为 `dist/Peach/Peach.pre-34932ec-20260827-190405.exe`。打包迁移为 21 个、0 待处理；80/443 已恢复到新托盘子进程，项目 CA 严格 HTTPS `/healthz` 为 writer，部署前后 ledger SHA-256 不变。生产 `/api/follow` 返回 277 个变体，其中 233 个带预览；新标签页确认首页式筛选、标题清理与桌面无溢出，手机视口覆盖仍未生效，手机截图验收为未取得。
- `58a4c4f`、`8da8c81` 已合入 `master`：Rule34.xxx 的 HTTP 200 空正文按零命中处理，管理页把查找结果合回添加区并统一标题字号；来源名称可回到原页面，同一作者只保留一个标题。多栏单位是作者组，组内来源保持单栏。正式 Windows 测试 1051 项通过、13 项跳过；生产桌面与 390×844 手机视口均无横向溢出，严格 HTTPS 为 writer，重启前后 ledger SHA-256 不变。
- `38dcc63`、`b3b028e` 已合入 `master`：关注筛选把「全部」放首位，来源只显示 favicon，作者和筛选横条支持鼠标拖动、滚轮与触摸横滚；卡片复用首页网格，操作按钮只在悬浮时出现，集合用 Mix 叠层和可滚动弹层，多选可批量保存、已看或忽略。批量接口兼容单项并在一个事务中处理所选条目。
- 更新后的正式 Windows 测试为 1051 项通过、13 项跳过。生产继续使用原 EXE，仅重启托盘加载源码；80/443、21 个迁移且 0 待处理、项目 CA 严格 HTTPS writer 均正常。桌面实测作者蓝框完整、筛选横滚从 0 到 640、悬浮操作与 Mix 不重叠、29 行集合弹层和单项多选正常；390×844 为 348px 单列且无页面横向溢出，手机截图捕获失败，视觉截图记为未取得。
- 浏览器验收在 Mix 入口尚被悬浮按钮覆盖时误触三次「标记已看」，`follow_item` 181、184、185 从 `new` 变为 `seen`；未保存到账本、未新增 asset。ledger SHA-256 从 `F8FBD87E...` 变为 `82D46DA2...`，需用户明确授权后才能恢复，当前不再写入。
- 关注名称查找会把下划线和连字符形式同时按分词形式查询；F95zone 站内索引仍未命中时，结果区给出同名 Google 查询入口，供人核对真实线程链接，不自动登记来源。正式 Windows 测试 1056 项通过、13 项跳过。
- `8bb4f91` 已合入 `master`：关注来源新增 FANBOX、Patreon、SubscribeStar；每条渠道以自定义勾选框控制是否参与更新检查，检查/移除改为单行图标；作者组在宽屏整体多栏，组内来源保持单栏并链接原页面；测试按 `follow`、`catalog`、`media`、`sync`、`metadata`、`tooling` 拆分，默认仍为全量。
- 合并当前主线后正式 Windows 全量测试 1083 项通过、13 项跳过。临时账本与 8912 端口的浏览器验收：1440px 为两个 467px 作者栏，390×844 为 320px 单栏；12 条来源均为 51px 单行，无页面或行级横向溢出；作者顶部边线均为 0，检查/移除均为 32×32 纯图标；SubscribeStar 开关可同步启停其检查按钮。临时服务和文件已删除。
- 真实 ledger 已授权应用 `0021`，并登记 InitialA 的 FANBOX 与 SubscribeStar 来源和 `FFXIVInitialA` 人工别名：FANBOX 首次发现 10 条，SubscribeStar 发现 7 条，其中新增 6 条、更新 1 条。当前 follow_source 12、follow_item 706、follow_author_alias 2，完整性正常。
- `d32f948` 已合入 `master`：FANBOX、Patreon、SubscribeStar 的官方主页只有一个明确作者名时会自动学习主页账号别名；多人主页不学习，自动证据不覆盖人工映射，模糊相似仍只给建议。关注域测试通过，全量 1086 项通过、13 项按平台跳过。
- 正式 EXE 已替换为 SHA-256 `83D5B176D2A53500D4697BF53589EE528FE9C872B7694EE2932D98C063EF3788`，上版备份为 `dist/Peach/Peach.pre-d32f948-20260827-215647.exe`；80/443 均恢复监听，项目 CA 严格 HTTPS `/healthz` 返回 200、writer、非只读，正式打包入口为 22 个迁移且 0 待处理。
- `a789efe` 已合入 `master`：关注卡片封面、标题、整张卡和 Mix 集合行统一打开 `/follow/item/{id}` 站内详情，不再以外站新窗口作为主交互；视频继续走 `/follow-stream`，来源页只留在详情侧栏。关注范围 358 项测试通过、1 项按平台跳过。正式 EXE 已替换为 SHA-256 `5231DF9898054FB1C62B87766994D06966CA09EBFF3146ED60F9630BC6B743B8`，上版备份为 `dist/Peach/Peach.pre-a789efe-20260827-221738.exe`；80/443、22 个迁移且 0 待处理、项目 CA 严格 HTTPS writer 和关注 API 均正常。生产页面实测无媒体与视频详情均不新增浏览器标签，关闭回到 `/follow`，桌面排版与首页详情一致；390×844 为单列且无横向溢出。浏览器自签 HTTPS 导航超时，视觉交互改由同一生产进程的 HTTP 回环入口验收；HTTPS 结论来自独立严格 CA 校验。验收未触发关注写操作，ledger SHA-256 仍为 `1B53408069EBCE5FB44156ABDA785D76A2E3C5DDABE0D30468A1DCB6D31CD600`。
- 迁移前已知的孤立 `follow_item` rowid 790 原本属于 `rule34xxx/initial_a`，缺失来源 id 恰好被新 FANBOX 来源复用为 12。2026-08-28 经授权，在一致备份 `database/ledger.pre-relink-follow-item-790-20260828-001728.db` 后将它重关联到现存 Rule34.xxx 来源 10；来源 10/12 的条目数由 100/11 变为 101/10，总数仍为 706。完整性与外键检查正常，严格 HTTPS 关注 API 返回该条为 `rule34xxx`、来源 10、状态 `new`。
- `b18e410` 已经由 `12fab62` 合入 `master`：关注详情的多视频集合改用首页 Mix 同款右侧队列，队列内直接切换；详情补回作者头像，来源收成标题旁外链图标，完整内容标签可点击并回到多选筛选。默认标签不再显示为全选，停用渠道保留在管理页但从关注流与计数中隐藏；InitialA 头像优先复用同作者官方 FANBOX 来源，最终回退为拉丁首字母；SubscribeStar 使用已验证的 32px favicon；FANBOX 子域链接的查找结果紧跟添加区显示。忽略操作统一改为划线眼睛，不再与关闭 X 混淆。关注域 360 项、正式 Windows 全量 1088 项均通过，1/13 项按平台跳过；1440×1000 与 390×844 浏览器验收均无横向溢出，多标签选择/取消、详情标签筛选、队列切换和管理页 FANBOX 查找均通过。
- 正式 EXE 已替换为 SHA-256 `40471E2DECF602EC72D5EAD548408C40AB0BD11AAF1FCEFDE492077E2BE70BC1`，上版备份为 `dist/Peach/Peach.pre-12fab62-20260828-011932.exe`；80/443 已由新进程恢复监听，打包迁移为 22 个、0 待处理，项目 CA 严格 HTTPS `/healthz` 返回 writer、非只读。生产关注 API 为 330 组、400 条，停用的 SubscribeStar 来源仍可管理但流内条目为 0；生产资源已包含 Mix 队列和新的忽略图标。部署前后 ledger SHA-256 均为 `8F0D4EE06379C406F601733EF2FDF21F7E9DA125C92DEAE211E73CD121E776A8`，本轮未写 ledger。
- `baa6c81`、`c07c2de` 已经由 `5d452b78`、`cddc23eb` 合入 `master`：F95zone 只把已验证的文件分发链接当成媒体，使用已保存的 F95 cookie 按当前 masked 协议解析同站跳转，cookie 不会发给 Gofile/Pixeldrain；关注卡片与详情只有在同组至少存在两个可直接播放的视频时才显示 Mix，线程回复数和一个外部文件页不再伪装成视频数。详情外链图标紧贴标题，说明文字使用不会被通用 `.fnote` 覆盖的独立间距。Gofile 官方内容接口仍需独立 Bearer token；两个实样返回 `error-notPremium`，因此只能确认外部文件页，文件列表与可播放视频未取得，不能据此生成 Mix。
- Windows 正式 EXE 已替换为 SHA-256 `63E84B344FD8900EED81D177DA2CDC31C26A83CE3358CFBA171F909052562348`，上版备份为 `dist/Peach/Peach.pre-cddc23eb-20260828-022410.exe`；主分支正式测试 1090 项通过、13 项按平台跳过，打包迁移 22 个、0 待处理，80/443 与项目 CA 严格 HTTPS writer 均正常。生产 DOM 实测 InitialA 单外链详情不显示 Mix，标题与外链图标间隔 5px；服务端已提供最终说明间距规则，但内置验收浏览器在禁用缓存后仍复用上一版 CSS，最终计算样式记为未取得。未触发生产“检查更新”，ledger SHA-256 与修改时间保持 `8F0D4EE06379C406F601733EF2FDF21F7E9DA125C92DEAE211E73CD121E776A8` / 2026-08-27 16:25:04 UTC。
- `f09e7aa` 已经由 `6ae030d` 合入 `master`：关注详情补齐真正的外链 SVG 图标，F95 已验证的 Gofile／Pixeldrain 文件页进入 `resource_urls` 并直接显示可点击链接；没有文件页时不再声称“已取得”。`/follow/item/{id}` 注册为 SPA 直达路由，刷新不再返回 404。名称查找会用归档 FANBOX 的数字 Pixiv 身份核对官方 FANBOX 资料，`LazyProcrastinator` 可发现 `https://lazyprocrast.fanbox.cc/`，不猜子域名；已有候选文案统一为“已经关注”。检查全部和单来源检查图标都在忙碌态使用同一旋转动画，但生产验收未实际触发检查更新。
- 正式 Windows 全量测试 1096 项通过、13 项按平台跳过；新 EXE 的打包迁移为 22 个、0 待处理。生产 EXE 已替换为 SHA-256 `BBDBB6EC7D3C2312E45F8F68B41BD5158749EF78D9A2C676F42FE7FED2D6A91F`，上版备份为 `dist/Peach/Peach.pre-6ae030d-20260828-031013.exe`；80/443 已恢复。项目 CA 的证书链和主机名校验通过，Schannel 因无法确认本地 CA 吊销状态而使用 `--ssl-revoke-best-effort`，`/healthz` 返回 writer，`/follow/item/190` 返回 200。
- 生产 API 共 330 组、400 条关注条目，4 条带外部文件页；item 565 显示 Gofile 与 Pixeldrain，item 190 返回真实 Rule34.xxx 来源 URL。生产浏览器实测标题旁外链图标为可见 16×16 SVG，文件页链接各带可见 15×15 图标，管理页查找可见官方 FANBOX 和“已经关注”，控制台无错误。验收未触发关注写操作，部署前后 ledger SHA-256 均为 `7389FC058C28651795E7AF77A7AD27CEED84A48E2B8AEF52767982E73957F80D`。
- `9051557` 已经由 `825348a` 合入 `master`：F95zone 回复只有在正文含论坛附件或已验证的文件站外链时才进入关注候选；引用块、纯讨论和普通网页链接会计入“跳过无资源”。附件直链同时作为预览图；历史纯讨论条目只在读取层隐藏，不删除 ledger。关注域 372 项、正式 Windows 全量 1100 项均通过，分别有 1/13 项按平台跳过。正式 EXE 已替换为 SHA-256 `D5447756E913704AD413FFFF7A57F1E10660D8B2CF7B3D57C2D6D2D8947372E7`，上版备份为 `dist/Peach/Peach.pre-825348a-20260828-095720.exe`；80/443、22 个迁移且 0 待处理、项目 CA 严格 HTTPS writer 和关注 API 均正常。生产流当前显示 151 组，其中 F95zone 资源条目 4 条；未触发检查更新，部署前后 ledger 哈希不变。
- `4dbd3c7`、`dcfae42`、`c495178` 已合入 `master`：版本由长期漏升的 `0.6.4` 升为 `0.7.0`；新增 Rule34 Paheal 来源、Gofile 独立 API token 输入与 Bearer 代理、FANBOX 正文外链和多图/多视频队列。外部媒体只经 `/follow-stream` 代理，token 不进入 URL 或关注 JSON。FANBOX `post.info` 若被验证页拦截，公开列表更新仍会入库并明确显示“媒体未取得”，不会拖垮整个作者来源。最终全量 1107 项通过、13 项按平台跳过；后续 FANBOX 修正的关注域 380 项通过、1 项跳过。
- 正式 EXE 已替换为 SHA-256 `59A8E43797EC6FDB13093465453DB09EF31EC64C3E8F49CAF5B1F328F55449DB`，备份为 `dist/Peach/Peach.pre-0.7.0-final-20260828-110113.exe`；22 个迁移且 0 待处理，生产健康检查为 writer、非只读，严格 HTTPS 浏览器可打开 `/follow`。真实 ledger 写入前备份为 `database/ledger.pre-follow-paheal-20260828-104302.db`（SHA-256 `423B470B5609FF08DB29D223114C1ED7066DABA2D86DD4ABC96D05D58F2A65DC`）；来源 13→14、条目 713→737，完整性正常、外键违规 0。重复添加大小写不同的 Paheal 链接仍复用来源 15 且新增 0；目标 7428820 与已停用 SubscribeStar 2639932 及同批媒体共享 `subscribestar:2639932`，去重键已在真实库和 API 验证。生产页面显示 Rule34 Paheal 来源、InitialA 作者筛选、右侧 8 视频详情队列和标题旁来源外链；手机视口本轮浏览器读取超时，视觉验收未取得。
- `8b7255c` 已合入 `master`：管理页新增 FANBOX Cookie 密码输入，Cookie 只发给 `api.fanbox.cc`，不会继承到 Gofile。Gofile 现场验证为 token 有效（`/accounts/getid` HTTP 200），但 `/contents/OS2Qz9` 返回 HTTP 401、`error-notPremium`；界面和检查结果改为按 Premium 套餐限制报告，不再误报 token 无效。关注域 382 项、正式 Windows 全量 1110 项通过，分别有 1/13 项按平台跳过。
- 0.7.1 正式 EXE 已替换为 SHA-256 `F3AB422B9004AA5AF4ACDE3BEF055E19D4D88D1E7BCEB5EDA478F39C687E6A38`，上版备份为 `dist/Peach/Peach.pre-0.7.1-20260828-131711.exe`；80/443 已恢复，打包迁移为 22 个、0 待处理，项目 CA 严格 HTTPS `/healthz` 返回 200、writer。生产凭据 API 显示 FANBOX `cookie` 可选输入、Gofile token 已配置。内置浏览器两次加载 `/follow-manage` 均超时，视觉验收未取得；本轮没有触发检查更新或写 ledger。
- `b0730af` 已经由 `a0a8ccc` 合入 `master`：0.7.2 将 FANBOX `post.info` 收窄到固定版本 `curl_cffi` 的 Firefox 传输；列表及其他来源仍走共用 HTTPX，不执行网页脚本、不求解机器人质询、不读取付费帖子。用管理页已保存的 Cookie 对 LazyProcrastinator 帖子 12228983 做只读复核，已取得 6 图、正文和 Gofile `OS2Qz9` 资源页，证明 Cookie 没填错，先前的 403／`general_error` 来自传输指纹。关注域 386 项、正式 Windows 全量 1114 项通过，分别有 1/13 项按平台跳过。
- 0.7.2 正式 EXE 已替换为 SHA-256 `F5F78CDACD9F466A6B8A423151F510F16D40A47BB052B984971D0F59D3EC51E6`，上版备份为 `dist/Peach/Peach.pre-0.7.2-20260828-142052.exe`；80/443 已恢复，打包迁移为 22 个、0 待处理，项目 CA 严格 HTTPS `/healthz` 返回 200、0.7.2、writer。生产凭据 API 显示 FANBOX Cookie 已配置、Gofile token 当前未配置；本轮没有触发检查更新，部署前后 ledger SHA-256 均为 `C2C6F09522305F682636379F43E74A4E60D9475C39FBE0FBC3505A7879CB963C`。本改动没有页面、CSS 或交互变化，桌面/手机视觉验收不适用。
- 2026-08-28 已完成全仓自研实现复用审计：浏览器历史、批处理 PID 锁、Rule34Video 媒体页和 FANBOX 正文模型有成熟替代或参考实现，进入替换队列；MP4 有界索引、固定项目 CA、SQLite 迁移、Gofile、系统网络监听、流媒体会话、单 writer 同步与 Windows 更新因已验证的 Peach 约束继续保留。详细候选、版本、真实 POC 与拒绝理由写入 `docs/REUSE.md`；本轮只改规则与文档，没有新增运行时依赖、部署、生产或 ledger 写入。
- 0.7.3 首项复用替换已完成：FANBOX 正文规范化固定参考 PixivUtil2 `v20251112` / `e537e96`，覆盖 image/text/file/article/video/entry、正文 blocks、四类 map 与旧 HTML；图片和视频进入现有多媒体切换，其他文件保留资源链接，URL 稳定去重。已保存 Cookie 对公开帖 12228983 的只读实测为 article、6 图、Gofile `OS2Qz9`；follow 391 项、正式 Windows 全量 1119 项通过，分别有 1/13 项按平台跳过。
- 0.7.3 正式 EXE 已替换为 SHA-256 `97EBAEE965794D100FA3BC7093B042EB36F1147CDEE1432C3504D7ECFB9D4582`，上版备份为 `dist/Peach/Peach.pre-0.7.3-20260828-152459.exe`；80/443 已由新进程恢复监听，打包迁移为 22 个、0 待处理，项目 CA 严格 HTTPS `/healthz` 返回 200、0.7.3、writer，`/follow` 返回 200。部署没有触发生产检查更新，部署前后 ledger SHA-256 均为 `BC98556370E285C2B627DBA3A36820E79AFF4599A33A265B0DBDDE520379A697`；本改动没有页面、CSS 或交互变化，桌面/手机视觉验收不适用。
- 0.7.4 追更详情的多图改为左右按钮、方向键和点状分页；多视频继续使用 Mix 右侧队列。直达详情按条目 ID 精确读取，启动时不再先绘制首页。关注入口统一使用 RSS 图标，左侧窄栏与筛选抽屉共用可在设置中调整的顺序。自动追更固定复用 APScheduler 3.11.3，只在 writer 启动，默认每小时、首次等待完整间隔，手动与自动检查共用互斥锁；设置页可关闭或调整为 15 分钟至每天，并显示最近/下次运行状态。正式全量 1130 项先发现 1 条点状分页圆角门槛，修正后覆盖该门槛的 `catalog` 368 项全部通过；全量其余 1129 项通过、13 项按平台跳过。
- 0.7.4 正式 EXE 已替换为 SHA-256 `027C985CD85B509BDEAD52D3FB209CBA25421B674BED96E0A97D97C82C8B2C1C`，上版备份为 `dist/Peach/Peach.pre-0.7.4-20260828-160731.exe`；80/443 已恢复，打包迁移为 22 个、0 待处理，项目 CA 严格 HTTPS `/healthz` 返回 200、0.7.4、writer。生产 `/follow/item/791` 返回 200，精确 API 恢复到 FANBOX 条目 791 及 6 张图片；自动更新已启用为每小时，下次运行时间可读且首次未立即执行。浏览器实测左右按钮、左右键、6 个圆点、刷新后保留详情、RSS 导航、设置中的侧栏排序与自动更新状态均正常，控制台无错误；侧栏顺序测试后已恢复原顺序。本轮没有手动触发关注检查。`migrate status` 在 16:05 将 WAL 检查点写回主库，主文件 SHA-256 由部署前快照值变为 `B1D499D5AA89D2BCB7A7311B167C726B07EA4FF0620E1FB467FC3F03519C487A`，部署重启后保持稳定；SQLite `integrity_check=ok`、外键违规 0，asset 81555、follow_item 1008。
- 管理页新增 `/taste`：以本机私有浏览历史和 Peach 播放、时长、评分、喜欢／不喜欢证据生成时间范围可切换的口味维度、Tag、创作者、女优、来源、不喜欢项、标签缺口与数据完整度；Peach 已有关联的排名可直接下钻筛选。支持读取本机浏览器、上传 Takeout／browserexport 导出和移除规范化数据源，均不把原始 URL／标题写入 ledger。变基到最新主线后正式 Windows 全量 1140 项通过、13 项按平台跳过；只读真实浏览历史与临时 ledger 副本实测 191,334 条浏览记录、354 个 Peach 项目和 7 个数据源合并成功，90 天范围收窄为 67,233 条，Tag 下钻到首页筛选正常。1440×900 为四列摘要、双列面板，390×844 为单列，均无横向溢出且控制台无错误。临时服务与副本已删除，未重启生产服务、未写真实 ledger。

## 下一批工作

1. 另行授权后先备份 ledger，再把 `follow_item` 181、184、185 从 `seen` 恢复为 `new`，复核状态计数、完整性与新哈希。
2. 继续按复用审计依次替换 PID 锁和 Rule34Video 媒体页；每项固定版本/revision、首个消费者和隔离测试同批落地。
3. 分类剩余 44 个无预览变体，区分确无图片与来源解析遗漏。
4. 另行确认后在生产关注页检查 LazyProcrastinator FANBOX，把已验证的 6 图、正文与 Gofile `OS2Qz9` 资源页写入关注候选；Gofile token 当前未配置，且此前验证的账户不是 Premium，21 个视频仍未取得。
5. 在 `/review` 人工处理本批 JAV 日文系列名、官方标签及现有创作者标签、FC2、Javinizer、Logo、头像和媒体失败候选；未经批准不写真相字段。
6. 将 Windows writer 的最新副本同步到共享传输点，再让 Mac reader 拉取；同步前后核对迁移版本、计数、完整性与 writer 身份。
7. 在 Mac Finder 以 `smb://peach-win.local/peach-sync` 连接一次并保存钥匙串记录，再重启菜单栏进程，核对自动挂载、reader 锁定、HTTPS、mDNS 和真实 LAN 客户端。
8. 在实现下载器前先确定媒体凭据、流量与磁盘预算。
9. Windows writer 运行 PikPak 夜跑前重算 probe/抽帧队列，并按 `peach-batch-jobs` 设置流量与系统盘闸门。
10. 继续拆分 `web_contract.py` 的 catalog、stats、activity、review、trash 领域，保持路由和现有契约测试不变。
11. 补做 HLS 首帧、seek、自适应码率及桌面/手机视觉验收。
12. 外置盘挂载后先只读盘点 `R:\Media\<名字>\P\...` 图片规模；扫描写真 ledger，需另行授权。

## 批处理进度（自动生成）

<!-- job-status:start -->

<!-- 由 scripts/job_status.py 生成，勿手改；数字现算于账本与产物 -->
<!-- generated 2026-08-27T07:08Z -->

- 最近自动交接：`claude` / `SessionEnd` / `other`，2026-08-27T07:08:40+00:00。
- 资产 81554 条，其中视频 24674 条。
- 待抽帧（可抽 / 缺时长待 probe / 合计）：
  - `local`：3 / 1 / 4
  - `115`：11 / 139 / 150
  - `pikpak`：8881 / 1310 / 10191
  PikPak 的策略组已可切 DIRECT：2026-08-15 实测走代理时 9 帧 163 MB / 13.7 秒，走直连时 30.5 MB / 64.2 秒——慢约 4.7 倍但流量少约 5 倍且不占代理预算。全量抽帧仍是 773 GB 量级（代理口径），按创作者采样 88 板直连约 2.7 GB。115 一直走直连，同样动作约 285 MB 一张接触表。
- 无内容标签视频 7442 条（占视频 30%）。
- `asset_tag` 来源分布：`vision_creator` 27004、`pixiv_tag` 19753、`name` 19271、`stash` 15450、`r18` 2254、`performer` 1589、`follow` 1376、`r18:performer` 1126、`javbus:performer` 37。
- 番号 1462 个，其中 1155 个有厂牌（79%）。

| 产物 | 行数 | 生成时间 | 说明 |
| --- | ---: | --- | --- |
| `code-scrape.csv` | 1135 | 08-22 10:39 | 番号刮削结果 |
| `name-clean.csv` | 7 | 08-22 10:42 | 文件名净化清单 |
| `ad-candidates.csv` | 82 | 08-14 22:53 | 广告候选（confidence 分级） |
| `disposal-candidates.csv` | 54 | 08-14 22:53 | 待处置候选（含「保留」判定） |
| `creator-tags-review.csv` | 86 | 08-15 18:35 | 创作者标签待审 |

<!-- job-status:end -->
