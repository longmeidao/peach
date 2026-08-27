# Peach 当前状态

最后核验：2026-08-27

本文件只保存当前运行态、已核验能力、仍需完成的工作和自动统计。已完成批次、旧测试数字与事故过程由 Git 历史保存，不在这里累积。

## 运行态

- Windows 是当前 ledger writer。启动入口为 `C:\Users\longm\Desktop\peach\peach-app\dist\Peach\Peach.exe`，代码、数据、worktree 和共享传输点都在 `C:\Users\longm\Desktop\peach\` 下；外置盘只提供 `R:\media`。
- 托盘必须以普通权限启动：提升权限后的令牌看不到 CloudDrive 的 `A:` / `B:`，会把 PikPak 和 115 误报为脱盘。异常时从托盘退出，再由资源管理器或普通权限终端启动。
- Windows HTTP 为 `0.0.0.0:80`，HTTPS 为当前 LAN IPv4 的 443，mDNS 名为 `peach-win.local`。线上服务版本最后核验为 `0.6.4`、`ledger_sync=writer`。
- macOS 是 reader，代码在 `~/Desktop/lmd.gg/peach/peach-app`，数据在相邻 `peach-data`；`peach.local` 经 8900/8443 和 pf 提供 80/443。GET 正常，写入端点返回 409。
- 2026-08-27 核对 macOS：服务子进程已跑当前 `master`，但菜单栏进程仍是旧代码。托盘层改动要生效，需手动退出菜单栏项后由 `.app` 或 `launchctl kickstart -k` 重启一次。
- 两端固定使用不同 mDNS 名和各自本机 CA；CA 私钥、服务器私钥和凭据不跨机同步。生成资产由 Syncthing 单向 Windows → Mac，Git 与 ledger 复制是另外两条链路。
- Windows 真实 ledger 为 `peach-data/database/ledger.db`，已应用到 `0020`。迁移前备份为 `database/ledger.pre-migrate-20260827-153611.db`，旧生产 EXE 备份为 `dist/Peach/Peach.pre-82eb548-20260827-153611.exe`。
- Mac ledger 已于 2026-08-27 经授权从共享副本显式拉取并恢复 `in-sync`，writer 仍是 Windows。拉取前备份为 `database/ledger.pre-pull-gen32-20260827T062519Z.db`；前后 asset 81554、entity 8182、asset_entity 155541，完整性正常且外键违规为 0，证明原 conflict 仅是 SQLite 物理布局与 marker 漂移。
- Mac 的 `peach-data/sources` 已迁到内置盘；`archive`、`tools` 仍可指向外置盘。追更证据和浏览记录不再依赖外置盘。
- Stash 仍监听 `127.0.0.1:9999`，只作可替换适配器。Windows FFmpeg/ffprobe 位于 `peach-data/tools/ffmpeg`，macOS 走 PATH。

## 已核验能力

- FastAPI 是唯一 Web server；Ledger 保存资产、规范身份、行为和复核决定。Stash 与 CloudDrive 都经适配层进入，扁平 creator/studio/tag 字段只作兼容投影。
- 本地浏览器支持 MP4/WebM/Ogg；AVI 等由 `TranscodeService` 缓存成 H.264/AAC MP4。远端 MP4 默认走标准 Range，显式 HLS 使用关键帧对齐片段，失败会回退 Range，永不改写原媒体。
- 首页、详情、实体资料、标签管理、照片、播放列表、统计、复核、回收站、关注管理和关注观看共用同一 SPA 与 JSON 契约；桌面和 390×844 手机均在验收范围内。
- 多女优卡片叠放前 3 个头像，只显示第一位姓名和真实总人数，例如 `かわいゆい 等 37 人`；详情与沉浸模式仍保留完整或扩展后的出演信息。
- 在线追更支持 kemono/coomer/pawchive、rule34video、rule34.xxx 和 f95zone；SimpCity 仍被 DDoS-Guard 阻塞，Peach 不绕过机器人验证。
- Rule34.xxx 来源 ref 大小写不敏感；迁移会合并分批添加造成的重复来源并保留条目状态。F95 的 `Collection(s)` 后缀不进入作者名，五个来源可归到同一作者组。
- 关注作者显示名与头像优先取经过固定主机校验的官方 FANBOX/Pixiv 页面，归档站只作回退。只支持真实历史分页的来源才显示「抓更早一页」。
- reader 的 `/review` 通过严格 Peach CA HTTPS 读取 writer 的归一化 JSON 并原子缓存；决定按钮和所有关注写操作仍锁定，不同步 SQLite/WAL 或原始候选目录。
- macOS Ledger 同步在共享根判为 `offline` 时会先通过 NetFS 尝试挂载 `peach-sync`，再重新判定；挂载失败才保留原离线结果，过程中不停止服务。默认使用 `peach-win.local`，可由 `PEACH_SHARED_SMB_*` 覆盖；对应主机没有钥匙串记录时快速失败，不弹出阻塞认证框。
- Windows 托盘与 macOS 菜单栏均提供「同步开发进度」。Windows 会先快进并运行正式测试；涉及打包输入时先构建和检查新 EXE，再退出旧托盘完成可回滚替换，失败不会提前停止现有服务。
- 搜索使用 FTS5 trigram，短查询回退 LIKE 并覆盖规范名、别名和检索词。搜索历史在 reader 写入被拒时降级到页面内存，不产生未处理异常。
- 回收站的单项删除和清空共用 `purge_assets()`：先处理媒体文件，再提交 ledger；删不掉的文件保留可见状态并回报，避免静默遗留。
- 复核页覆盖元数据、创作者标签、Logo、头像、身份、番号目录、FC2 证据和媒体失败。抓取与 AI 结果仍是候选，批准后才写真相字段。
- 浏览历史增量采集使用 SQLite backup API，一致性读取本机浏览器和 Takeout；原始 URL/标题只留本机私有库，聚合候选不写 ledger。

## 本批修正与验证

- `5926ff4` 已合入 `master`：关注页改用与首页一致的作者头像和标签胶囊，压缩顶部间距；管理页不再残留目录标题；`深喉咙` 统一为 `深喉`；非视频主附件也会从同一发布的图片附件取预览图。
- Fiu758 只登记为厂牌 Logo 候选发现来源，不作真相源。17 个已安装横条 Logo 已原样备份并无损补成正方形；5 个损坏图片保持不动并进入错误报告。JAV 官方元数据批次生成 45 组候选，含 7 个日文系列名和 9 个官方标签，均未自动批准、未写 ledger 真相字段。
- 正式 Windows 测试入口跑完 1040 项，全部通过，13 项按平台跳过。桌面浏览器确认关注页顶部为 88px、无旧筛选控件、无横向溢出且目录标题隐藏；手机视口覆盖连续超时，截图验收为未取得，响应式源码契约测试已通过。
- 新 EXE 已部署到 Windows 生产入口，旧版备份为 `dist/Peach/Peach.pre-34932ec-20260827-190405.exe`。打包迁移为 21 个、0 待处理；80/443 已恢复到新托盘子进程，项目 CA 严格 HTTPS `/healthz` 为 writer，部署前后 ledger SHA-256 不变。生产 `/api/follow` 返回 277 个变体，其中 233 个带预览；新标签页确认首页式筛选、标题清理与桌面无溢出，手机视口覆盖仍未生效，手机截图验收为未取得。
- `58a4c4f`、`8da8c81` 已合入 `master`：Rule34.xxx 的 HTTP 200 空正文按零命中处理，管理页把查找结果合回添加区并统一标题字号；来源名称可回到原页面，同一作者只保留一个标题。多栏单位是作者组，组内来源保持单栏。正式 Windows 测试 1051 项通过、13 项跳过；生产桌面与 390×844 手机视口均无横向溢出，严格 HTTPS 为 writer，重启前后 ledger SHA-256 不变。
- `38dcc63`、`b3b028e` 已合入 `master`：关注筛选把「全部」放首位，来源只显示 favicon，作者和筛选横条支持鼠标拖动、滚轮与触摸横滚；卡片复用首页网格，操作按钮只在悬浮时出现，集合用 Mix 叠层和可滚动弹层，多选可批量保存、已看或忽略。批量接口兼容单项并在一个事务中处理所选条目。
- 更新后的正式 Windows 测试为 1051 项通过、13 项跳过。生产继续使用原 EXE，仅重启托盘加载源码；80/443、21 个迁移且 0 待处理、项目 CA 严格 HTTPS writer 均正常。桌面实测作者蓝框完整、筛选横滚从 0 到 640、悬浮操作与 Mix 不重叠、29 行集合弹层和单项多选正常；390×844 为 348px 单列且无页面横向溢出，手机截图捕获失败，视觉截图记为未取得。
- 浏览器验收在 Mix 入口尚被悬浮按钮覆盖时误触三次「标记已看」，`follow_item` 181、184、185 从 `new` 变为 `seen`；未保存到账本、未新增 asset。ledger SHA-256 从 `F8FBD87E...` 变为 `82D46DA2...`，需用户明确授权后才能恢复，当前不再写入。
- 关注名称查找会把下划线和连字符形式同时按分词形式查询；F95zone 站内索引仍未命中时，结果区给出同名 Google 查询入口，供人核对真实线程链接，不自动登记来源。正式 Windows 测试 1056 项通过、13 项跳过。

## 下一批工作

1. 用户授权后先备份 ledger，再把 `follow_item` 181、184、185 从 `seen` 恢复为 `new`，复核状态计数、完整性与新哈希。
2. 补做关注页 390×844 手机截图；同时分类剩余 44 个无预览变体，区分确无图片与来源解析遗漏。
3. 在 `/review` 人工处理本批 JAV 日文系列名、官方标签及现有创作者标签、FC2、Javinizer、Logo、头像和媒体失败候选；未经批准不写真相字段。
4. 将 Windows writer 的 `0020` 副本同步到共享传输点，再让 Mac reader 拉取；同步前后核对迁移版本、计数、完整性与 writer 身份。
5. 在 Mac Finder 以 `smb://peach-win.local/peach-sync` 连接一次并保存钥匙串记录，再重启菜单栏进程，核对自动挂载、reader 锁定、HTTPS、mDNS 和真实 LAN 客户端。
6. 为追更接入 APScheduler；在实现下载器前先确定媒体凭据、流量与磁盘预算。
7. Windows writer 运行 PikPak 夜跑前重算 probe/抽帧队列，并按 `peach-batch-jobs` 设置流量与系统盘闸门。
8. 继续拆分 `web_contract.py` 的 catalog、stats、activity、review、trash 领域，保持路由和现有契约测试不变。
9. 补做 HLS 首帧、seek、自适应码率及桌面/手机视觉验收。
10. 外置盘挂载后先只读盘点 `R:\Media\<名字>\P\...` 图片规模；扫描写真 ledger，需另行授权。

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
