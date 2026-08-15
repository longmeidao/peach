# Peach 当前状态

最后核验：2026-08-15

## 运行态

- 生产入口：Windows 当前用户 Startup 中的 `Peach.lnk`，启动 `R:\peach-app\.venv\Scripts\pythonw.exe -m peach.tray`。当前版本 `0.3.0`。
- HTTP：`0.0.0.0:80`；HTTPS：`192.168.50.162:443`。`peach.local` 是唯一正式局域网名称，发布为 `192.168.50.162`。
- mDNS 使用 Python zeroconf 的全合格网卡监听；生产显式固定发布地址，避免隧道网卡误选。没有发布 `lmd-dst.local`。
- Stash 仍运行于 `127.0.0.1:9999`，只作为过渡期可替换适配器。
- Python：3.14.7；FFmpeg/ffprobe 由 `R:\peach-data\tools\ffmpeg` 管理，不再依赖 Stash 私有目录。
- 真实 ledger：`R:\peach-data\database\ledger.db`，迁移 `0000`–`0009` 已应用，零待处理。最近可恢复数据库备份：`R:\peach-data\database\ledger.pre-checksum-reconcile-20260815-121210.db`。
- PID 只是观测值，不是配置；每次停止或重启前必须重新核对命令行、父子关系和端口归属。

## 已核验代码与部署能力

- FastAPI 是唯一 Web server，提供首页、稳定 JSON 契约、标准 Range/HEAD、缩略图、海报、头像和 Logo。旧 `BaseHTTPRequestHandler`、动态 legacy loader 和启动时即席修表已删除。
- Ledger 是资产、身份、行为和知识真相。规范女优/厂牌/创作者/标签/系列使用 `entity`、`asset_entity`、`entity_external_ref`；扁平字段只作兼容投影。
- `MediaEngine` 统一管理本地文件和 Stash 公开协议适配器。浏览器原生 MP4/WebM/Ogg 直出；AVI 等由 `TranscodeService` 缓存为 H.264/AAC MP4，原文件不改写。
- 真实 CloudDrive 作品 4289 已通过 `video/mp4`、1 KiB `206 Partial Content`、缩略图和海报检查；盘符可见性以 Peach `/stream` 为最终证据。
- SQLite FTS5 trigram 已覆盖 81,873 个资产；三字符以上走 FTS，短查询回退 LIKE。
- `FeedAdapter` 已支持显式、有界 RSS/Atom 发现、条件请求和不可变快照；尚未配置真实订阅，也不会启动时自动写 ledger。
- AI Provider 已拆为推理与 Agent 两层。`/api/providers` 无副作用且不泄露凭据；OpenCode Go 模型清单只在显式访问时拉取，当前不发推理请求。
- Windows 托盘已部署：单击打开 Peach，右键提供状态、重启、日志、版本/更新和退出；Per-Monitor V2 DPI 在创建窗口前启用，更新检查在后台线程执行并使用非模态通知。
- 版本唯一来源为 `src/peach/__init__.py::__version__`。本批删除旧公共 `/entity/...` 路由，按 pre-1.0 破坏性接口变更规则升至 `0.3.0`；没有 Git remote 时只报告本地开发版，不伪造更新能力。
- 本地 CA HTTPS 已部署。CA 包含 critical `CA:TRUE` 和签名用途并通过 OpenSSL 链验证。macOS/iOS 只安装 `peach-local-ca.crt`；不得传播任何私钥。
- 项目代码、运行数据、本地媒体已分离为 `R:\peach-app`、`R:\peach-data`、`R:\media`。旧空 Inbox 和 `Resources/Tools` 兼容表面已移除。

## 界面与交互现状

- 首页、详情、标签管理（字母表/标签云）、女优墙、厂牌/创作者/系列资料页、统计、沉浸模式均为同一无构建单页表面，桌面与手机共享数据契约。
- 女优/厂牌/创作者/系列名称用于导航；只有内容标签直接叠加筛选。“换一批”是动作，不是筛选状态。
- 卡片身份女优优先；头像本身进入女优资料页。缺失厂牌 Logo 显示首字母，不用任意作品图冒充。
- “喜欢/为什么喜欢”写 profile 级 `asset_preference`；原因非空会隐含喜欢，但 AI 不能直接改写用户原文。“稍后看”独立写 `watch_queue`。
- 详情反馈是 Like、不喜欢、看过、稍后看、待删候选五个 Lucide 图标；真正删除仍需经复核 CSV 独立执行。
- 长卡连续 hover 5 秒才放大并显示 ±10 秒和详情控制；短卡立即显示稍后看。沉浸模式使用经源码核验的 200 ms TikTok 滚动时序。
- 参考 Beeg 的控件和表面层均已登记当前 CSS/JS hash。Peach 使用实测的深色背景、frost 透明度和 blur 数值，并明确记录主动差异。
- 当前厂牌 Logo 覆盖 28/114，仍有 86 个待补；女优头像质量评分和联网高清头像仍是后续任务。
- 公共资料页 URL 已改为 `/performers/{name}`、`/studios/{name}`、`/creators/{name}`、`/series/{name}`；旧 `/entity/{kind}/{name}` 已删除。内部 JSON 兼容端点仍为 `/api/entity`。
- 收起详情或导航离开时会暂停视频、清空 `src`、调用 `load()` 并移除元素，不再留下后台播放/下载。详情打开时筛选栏取消 sticky，避免上滚遮住详情顶部。
- 标签统一使用同一圆角和内边距 token；厂牌/来源保留独立身份样式。选中框改为内描边，不会被卡片边缘或 hover 样式裁掉。
- 详情身份按名称去重，标签可逐项隐藏或手动添加；隐藏只写 profile 覆盖，不破坏原始来源断言。高潮按钮使用 Health Icons 的 CC0 领域图标和独立暖粉强调色。
- 侧栏、抽屉和粘性栏使用 Beeg 当前源码实测的透明层与 blur 数值；页面背景不再是纯黑，侧栏不再是纯灰。本轮没有为了装饰引入动画库，后续动效必须先复用审计并只表达状态/连续性。

## 数据与批处理

- 真实资产 81,847 条，其中视频 24,967 条。迁移后的完整性检查为 `ok`，外键违规为 0。
- 已核对并删除 `asce/The.Great.Escape.S04` 正常向剧集：13 个视频、13 个字幕、16 个派生图，同步清理 26 条 ledger 资产。原因是旧导入器把集合目录 `asce` 投影为创作者，再把创作者板上的低置信标签批量传播。`0009` 已移除 `asce` 假创作者及其 `vision_creator` 断言，保留其他独立来源标签。
- 番号刮削已处理 1,104 个非 FC2 番号，715 条取得数据；所有 330 个 FC2 在三来源样本中零命中，因此默认跳过。
- 创作者视觉板已处理 30 张，27 位创作者写入 27,295 条 `vision_creator` 标签，覆盖 4,518 个视频；置信度固定为 0.6，区别于逐条证据。
- `find_ads.py` 只生成候选，不删除。当前 82 条、约 1.5 GB；77 条确认、5 条存疑。`BNST033.mp4` 已从错误待删结论中排除。
- 115 时长修复后，未知时长不再写 0，而写失败值 `-1`；`--redo zero|failed|all` 可重试。
- 115/PikPak 抽帧主要成本是 CloudDrive 块预取流量：实测九帧接触表约为 115 285 MB、PikPak 163 MB。PikPak 全量抽帧约 773 GB，暂不启动。
- `RM-TrafficWatch` 常驻心跳已改用 `pythonw.exe` 隐藏运行。默认 200 GB 守卫统计代理流量；直连来源需显式 `--count-direct`。

## 验证基线

- 当前主分支基线：95 项隔离测试通过，inline JavaScript 语法检查通过；版本、托盘、迁移、mDNS、媒体转码、Provider、语义路由、详情播放释放和数据边界均有测试。
- 前一生产版本已分别通过 HTTP/HTTPS health、`peach.local` 解析、真实 CloudDrive Range、桌面 1280×720 和手机 390×844 检查。
- 浏览器验收不得写真实喜欢、反馈或播放数据；需要交互写入时使用隔离 ledger 副本。
- 并行 worktree 测试必须设置 `PYTHONPATH=<当前工作树>\src` 并核对 `peach.__file__`，否则 editable install 可能误加载主目录旧代码。
- 本批已重启生产托盘。HTTP/HTTPS health 均返回 `0.3.0`；新语义路由返回 200，旧 `/entity/...` 返回 404；`peach.local` 解析为 `192.168.50.162`，zeroconf health 正常；真实作品 4289 的 1 KiB Range 返回 `206 video/mp4`。
- 生产桌面 1280×720：无横向溢出，选中内描边未裁切，标签圆角一致，侧栏/抽屉透明渐变生效。生产手机 390×844：无横向溢出，侧栏隐藏、内容零左缩进、标签圆角一致。浏览器控制台无 warning/error。
- 详情播放释放和 sticky 遮挡在隔离 ledger 浏览器中验收；生产浏览器只做无写入首页/样式检查，未污染真实播放、喜欢或反馈数据。

## 下一批工作

1. 继续 115 抽帧任务：`python scripts/sheets.py --location 115 --workers 4`。任务可续跑，当前剩余数量以文末自动区块为准。
2. 首尾帧额外抽样：识别水印、出处和 `full version available`，生成带证据的“不完整版/剪辑版”候选。首个回归样本为 115 的 `04_Stepsistercaughtmejerkingoff,deepthroat,throatpie.mp4` 片尾。
3. 完成女优头像质量权重：经验证的联网高清头像 → 其他高质量公开头像 → 观看最多作品的人脸感知裁图 → 清晰关键帧。
4. 通过官方/公开来源补齐 86 个厂牌 Logo，保留来源和质量门槛。
5. 增加 Media Engine stream-plan API，再复用 hls.js 或 Shaka Player 接入 HLS/DASH；不得自己造播放器协议层。
6. 配置并评估 Stash CommunityScrapers/元数据 Provider，确认缺口后才写新来源适配器。
7. 配置可复核的真实追更源，之后再接 APScheduler；AI 结果继续只作为候选。
8. 发布前继续删减仅在构建阶段有用的解释性文字，只保留会影响决策、防止数据损失或解释陌生状态的内容。

## 批处理进度（自动生成）

<!-- job-status:start -->

<!-- 由 scripts/job_status.py 生成，勿手改；数字现算于账本与产物 -->
<!-- generated 2026-08-15T04:12Z -->

- 最近自动交接：`claude` / `Stop` / `completed`，2026-08-15T01:56:09+00:00。
- 资产 81847 条，其中视频 24967 条。
- 待抽帧（可抽 / 缺时长待 probe / 合计）：
  - `local`：4 / 1 / 5
  - `115`：1334 / 139 / 1473
  - `pikpak`：4751 / 5445 / 10196
  PikPak 计费且走代理（`*.mypikpak.net`）；2026-08-15 实测 9 帧接触表 163 MB / 13.7 秒，即约 18 MB、1.5 秒一帧。瓶颈是流量不是时间：全量抽帧约 773 GB，按创作者采样 88 板约 14 GB / 20 分钟。115 走直连，同样动作约 285 MB 一张接触表。
- 无内容标签视频 7622 条（占视频 31%）。
- `asset_tag` 来源分布：`vision_creator` 27004、`pixiv_tag` 19753、`name` 19107、`stash` 15450、`r18` 2538、`performer` 1887、`follow` 1376、`r18:performer` 1216、`javbus:performer` 50。
- 番号 1434 个，其中 1158 个有厂牌（81%）。

| 产物 | 行数 | 生成时间 | 说明 |
| --- | ---: | --- | --- |
| `code-scrape.csv` | 1104 | 08-14 16:17 | 番号刮削结果 |
| `name-clean.csv` | 287 | 08-14 16:18 | 文件名净化清单 |
| `ad-candidates.csv` | 82 | 08-14 22:53 | 广告候选（confidence 分级） |
| `disposal-candidates.csv` | 54 | 08-14 22:53 | 待处置候选（含「保留」判定） |
| `creator-tags-review.csv` | 86 | 08-14 22:30 | 创作者标签待审 |

<!-- job-status:end -->
