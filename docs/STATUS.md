# Peach 当前状态

最后核验：2026-08-26

## 运行态

- Windows 手动单写者构建已上线，Startup 入口为
  `C:\Users\longm\Desktop\peach\peach-app\dist\Peach\Peach.exe`；Mac 是 reader，菜单栏项和
  `peach.local` 正常提供服务，写入端点返回 409。
- **托盘必须以普通权限启动**。A: / B: 是 CloudDrive 挂在用户会话里的虚拟盘，
  提权后的令牌看不到它们（实测：管理员 PowerShell 里 `Get-ChildItem B:\` 失败，普通权限正常）。
  托盘提权时，它拉起的 `peach serve` 继承同一令牌，`/api/sources` 会把 115 和 PikPak
  报成 `online:false`，封面、播放和「接着看」卡片全部变成脱盘态；`R:` 是物理盘，不受影响，
  所以看上去只是「网盘挂不上」。代码侧没有可改的地方：快捷方式没勾「以管理员身份运行」、
  exe 清单是 `asInvoker`、注册表兼容性标志里也没有 RUNASADMIN，变提权只会是「这一次从已提权的
  父进程里启动」（子进程继承令牌）。判据：非提权 shell 读不到托盘进程的 `Path` / `CommandLine`。
  恢复办法：托盘菜单退出，再从资源管理器（或普通权限终端）重新启动。
- Windows 内置盘环境已完成：代码 `C:\Users\longm\Desktop\peach\peach-app`、运行数据
  `C:\Users\longm\Desktop\peach\peach-data`、worktree `C:\Users\longm\Desktop\peach\peach-worktrees`、
  共享账本传输点 `C:\Users\longm\Desktop\peach\peach-sync`。外置盘只提供 `R:\media`。
- HTTP：`0.0.0.0:80`；HTTPS：`192.168.50.162:443`。Windows 正式局域网名称为
  `peach-win.local`；2026-08-25 已部署 `version=0.6.4`、`ledger_sync=writer`，新增可保存 Mix、命名、排序、编辑和续播的持久播放列表；并保留此前对 Ledger
  同步通知把子进程 GBK 输出误按 UTF-8 解码所致乱码的修复。2026-08-22 的严格 HTTPS 首页、头像和海报
  验收均为 200；当时连续 120 秒浏览观测 local/shared generation 均保持29。
- mDNS 使用 Python zeroconf 的全合格网卡监听；生产显式固定发布地址，避免隧道网卡误选。没有发布 `lmd-dst.local`。
- macOS 菜单栏已按同一重构上线为 `0.6.2` reader，管理 `8900/8443` 并由 pf 提供
  `peach.local:80/443`。菜单提供「同步 Ledger」和「接管 Ledger 写入」；GET 正常、POST 返回409。
- Stash 仍运行于 `127.0.0.1:9999`，只作为过渡期可替换适配器。
- Python：3.14.7；FFmpeg/ffprobe 由
  `C:\Users\longm\Desktop\peach\peach-data\tools\ffmpeg` 管理，不再依赖 Stash 私有目录。
- 真实 ledger：`C:\Users\longm\Desktop\peach\peach-data\database\ledger.db`，Windows 迁移 `0000`–`0017`
  已应用，零待处理，完整性 `ok`。历史备份均在同一 `database` 目录，文件名保持不变。
  2026-08-25 复核 Mac 本地副本，`schema_migration` 同样到 `0016`。
  **追更两张表的迁移号已从 `0017` 改为 `0018`**：两条分支同时占用了 `0017`，
  远端是 `0017_persistent_playlists`。改号安全的判据是实测——2026-08-25 核对
  Mac 本地副本与共享副本（第 30 代）的 `schema_migration`，两边最高都是 `0016`，
  谁都没应用过 `0017`，所以没有触碰「已应用的迁移文件不得修改」这条线。
  `0018` 尚未对任何真实 ledger 执行；在此之前 `/follow` 会因缺表报错。
- 2026-08-25 已挂上 `/Volumes/peach-sync`（钥匙串账号 `peachsync`@`192.168.50.162`，
  guest 被拒，这条钥匙串记录是唯一的钥匙），并完成一次 `pull`：本地从第 29 代到第 30 代，
  `plan` 现为 `in-sync`。拉取前备份在 `database/ledger.pre-pull-gen30-20260825T080644Z.db`
  （121.4 MiB，完整性 ok，asset 81753）。选边有据：集合差显示共享一条 asset 都没多出来，
  本地多的 96 条全是 `location='115'` 的广告条目，是 Windows 在 29→30 代之间删掉的。
- `local_dirty` 的判据已按 ADR-0020 改成三层。原先只看 `(size, mtime_ns)`，实测既会
  **误报**（内容中性的 checkpoint、碰时间戳）也会**漏报**（已提交但还在 WAL 里的事务
  完全不改主库文件，`copy_database` 会连同 `-wal` 一起删掉，静默丢数据）。
- **历史记录**：Mac 本地副本自 2026-08-24 起就是 dirty 的（marker 记的是第 29 代、
  `mtime_ns=1787332506518044766`，实际库已是 `1787504652787227090`，大小未变），而共享传输点
  `/Volumes/peach-sync` 当前不可达。下次恢复同步时 `plan()` 会因「共享更新且本地有未回写改动」
  判成 `conflict`，必须由人选一边——Mac 只用来浏览，正确的选择是取 Windows 那一份。
  这个 latent conflict 先于追更改动存在，不是追更迁移造成的。
- 2026-08-25 发现 `http://peach.local/`（80）不通而 `:8900`/`:8443` 正常：`/etc/pf.anchors/gg.lmd.peach`
  规则文件还在（8-20 装的），但 `/etc/pf.conf` 里引用它的 `rdr-anchor` 行没了——系统更新会用
  模板重写 `/etc/pf.conf`，把追加的锚点行抹掉，而锚点文件是独立文件所以留了下来。
  症状是服务健康、端口正常、只有不带端口的入口打不开。重装用
  `sudo sh scripts/setup_macos_port80.sh install`（需要用户密码，智能体跑不了）。
- **接管 Ledger 写入不需要外置盘，但需要挂一次 `peach-sync`。** 两者不是一回事：
  `peach-sync` 是 Windows 内置盘上的 SMB 共享，外置盘 `/Volumes/RESOURCES` 只供媒体。
  2026-08-26 实测四种组合：共享没挂时接管被拒（`plan=offline`，`take_ownership` 要求
  `in-sync`）；挂上后接管成功；**接管之后再拔掉共享，本机照常可写**（`writer_device`
  读本地 marker 即可判定）。所以「不插盘长期在 Mac 上写」是成立的，只是切换写入端
  那一次要把共享挂上——只写本地 marker 会让 Windows 同时认为自己是写入端，那正是
  单写者复制要避免的分叉。
- **Mac 的 `peach-data/sources` 已迁到内置盘。** 旧目录原是指向
  `/Volumes/RESOURCES/peach-data/sources` 的断链，2026-08-26 已保留为
  `peach-data/sources.external-link-20260826`，并用本机私有目录替换运行入口；外置盘继续只承担
  媒体资源，不再是追更证据和浏览记录采集的前置条件。迁移前 `mkdir(exist_ok=True)` 会在断链上
  抛 `FileExistsError`；追更已能把这种证据失败降级成「未取得」，不会连同候选一起丢掉。
- 2026-08-26 从 2026-08-13/14 的迁移盘点与会话证据恢复了早期口味分析的位置：原始输入
  当时已从 `R:\Resources\Sources` 完整迁到 `R:\peach-data\sources`，共 67 个文件、
  约 421.5 MB；Mac 传回的 `mac/` 包含 `zen-places.sqlite`、`zen-history.tsv`、
  `zen-visits.tsv`、`safari-History.db` 和 `taste-raw.zip`，其余分在 `takeout/`、
  `browsers/`、`telegram/`、`follows/`、`inventories/`、`dedup/`、`reports/`。随后在 Windows
  实测 `R:` 已挂载为 `RESOURCES`（exFAT，约 1 TB），但 `R:\peach-data\sources`、旧
  `R:\Resources\Sources` 和回收站都没有这批文件，按已删除处理；Mac 上旧副本的现存状态
  **未取得**。
- 浏览记录增量刷新已实现：`scripts/taste_history.py` 用 SQLite backup API 一致性读取浏览器活库，
  原始 URL/标题只增量写入本机 `peach-data/sources/taste-history/history.sqlite`，聚合报告与
  creator/tag candidate 写 `peach-data/review/taste-history/`，不写 ledger。2026-08-26 Windows
  首批发现 Chrome 1、Firefox 4、Zen 2 共 7 个 profile，导入 382,781 次访问，时间范围
  2025-11-08 至 2026-08-26；报告不含完整 URL 或标题。同日 Mac 首批发现 Chrome、Safari、Zen
  各 1 个 profile，导入 171,818 次访问，时间范围 2025-11-08 至 2026-08-26；第二次刷新三者
  新增均为 0，增量去重成立。Safari 通过 SQLite backup 读取 34,496 次，没有 TCC 错误；Firefox
  Profiles 目录不存在，未发现可导入源。
- 追更的「查找」在只读端一度返回 409：`/api/follow/resolve` 只联网发现、不碰账本，
  却因为是 POST 被写入端闸门一并拦掉。已按 `READ_ONLY_POST_ROUTES` 白名单放行；
  真正会写的 `check`/`save`/`status`/`source` 仍受闸门管辖。
- PID 只是观测值，不是配置；每次停止或重启前必须重新核对命令行、父子关系和端口归属。
- macOS 独立运行环境：代码 `~/Desktop/lmd.gg/peach/peach-app`、数据 `~/Desktop/lmd.gg/peach/peach-data`、worktree `~/Desktop/lmd.gg/peach/peach-worktrees`。Python 3.14.7 + 独立 venv，FFmpeg 走 PATH。
- Mac 的 `peach-data` 实际形状与文档的通用分层有出入，排查前先看清：真实目录名是
  `artifacts`，`generated` 是指向它的符号链接；另有 `review`、`tmp` 两个本机目录；
  `sources` 已迁为本机私有目录，`archive`、`tools` 仍是指向 `/Volumes/RESOURCES/peach-data/`
  的符号链接，外置盘拔掉时后两者断链。浏览记录与追更证据不再依赖外置盘。
- 生成产物已由 Syncthing 单向同步：Windows send-only、Mac receive-only，五个文件夹
  `snapshots`、`posters`、`avatars`、`logos`、`covers`，Mac 侧根目录在 `peach-data/artifacts/`，
  Trash Can 版本保留 30 天。这条链路与账本复制、与 Git 都无关，三者互不兜底。

## 已核验代码与部署能力

- FastAPI 是唯一 Web server，提供首页、稳定 JSON 契约、标准 Range/HEAD、缩略图、海报、头像和 Logo。旧 `BaseHTTPRequestHandler`、动态 legacy loader 和启动时即席修表已删除。
- Ledger 是资产、身份、行为和知识真相。规范女优/厂牌/创作者/标签/系列使用 `entity`、`asset_entity`、`entity_external_ref`；扁平字段只作兼容投影。
- `MediaEngine` 统一管理本地文件和 Stash 公开协议适配器。浏览器本地 MP4/WebM/Ogg 直出；115/PikPak 已知时长的原生 MP4 由 `/api/stream-plan` 选择 6 秒 HLS 临时片段，AVI 等由 `TranscodeService` 缓存为 H.264/AAC MP4，原文件不改写。
- 真实 CloudDrive 作品 4289 已通过 `video/mp4`、1 KiB `206 Partial Content`、缩略图和海报检查；盘符可见性以 Peach `/stream` 为最终证据。
- SQLite FTS5 trigram 覆盖全部视频与图片资产；三字符以上走 FTS，短查询回退 LIKE。资产总数只看文末自动区块。
- 在线追更已从「有 adapter 没有源」变成可用表面（ADR-0019）：五类站点连接器
  （kemono/coomer/pawchive、rule34video、rule34.xxx、f95zone）、WIP/alt/跨站重复判定、
  `follow_source`/`follow_item` 两张表、`peach follow` 子命令和 `/follow` 页面。
  联网只在 `peach follow check` 与「检查更新」按钮触发。`FeedAdapter` 的 RSS/Atom 入口保留，
  但这七个来源实测都没有可用 feed——f95 的 `index.rss` 直接回「无法以该格式呈现」。
- 追更的两个待办不是代码问题：rule34.xxx 需要用户在
  `rule34.xxx/index.php?page=account&s=options` 生成 user_id + api_key 并写进
  `peach-data/secrets/follow/rule34xxx.json`；simpcity.cr 挂着 DDoS-Guard 浏览器质询，
  可用入口**未取得**，Peach 不绕机器人验证。f95zone 的发现实测不需要 cookies，
  只有取附件媒体需要登录会话。
- AI Provider 已拆为推理与 Agent 两层。`/api/providers` 无副作用且不泄露凭据；OpenCode Go 模型清单只在显式访问时拉取，当前不发推理请求。
- 手动单写者重构已完成双端部署：Windows 476 项测试通过，Mac 在保留两项本地 UI 修复后
  479 项测试通过。服务启动/浏览/退出不再同步；marker.device 指定唯一写入端，另一台 POST
  返回409；托盘只在显式同步或接管时复制。
- Windows 品牌资源已统一为附件生成的 `1024x1024` 正方形蜜桃图：`resources/peach-logo.png`、`resources/peach.ico`；Web favicon、托盘图标和 EXE 内嵌图标共用该资源。PyInstaller 打包产物为 `dist/Peach/Peach.exe`，桌面和 Startup 的 `Peach.lnk` 均按 FlowLens 的 `exe,0` 方式指向它；该 exe 只打包托盘自身，服务进程仍由项目 venv 承担，不是可移动的独立发行版。
- 版本唯一来源为 `src/peach/__init__.py::__version__`；Windows 当前部署和本地代码为 `0.6.4`，Mac 最近一次已核验部署为 `0.6.2`。没有 Git remote 时只报告本地开发版，不伪造更新能力。
- 本地 CA HTTPS 已部署。CA 包含 critical `CA:TRUE` 和签名用途并通过 OpenSSL 链验证。macOS/iOS 只安装 `peach-local-ca.crt`；不得传播任何私钥。
- 2026-08-24 安全与架构加固：TLS 目录 ACL 已备份，CA key/server key 禁用继承，只保留 `longm`、SYSTEM、Administrators；托盘仍由 `longm` 运行，80/443 与严格 CA HTTPS 复验通过。配置口令后使用 `/login` POST 设置 HttpOnly cookie，旧 `?t=` 只做一次兼容重定向。异常 500 不再把类型/消息外发；HLS 计划与长转码使用有界执行器，session 取消会终止 FFmpeg。
- Web 数据边界已开始分域：`LedgerDatabase` 由 `WebContract` 与 `LedgerRepository` 共用，事务统一回滚/关闭；活动写入与纯逻辑已拆到 `web_activity.py`、`web_logic.py`，JSON contract 使用显式 handler 注册表。回收站永久删除先同目录隔离媒体，SQLite commit 失败会恢复原名。
- Windows 代码、运行数据、venv、构建产物和 worktree 已从外置盘迁到内置盘；旧空 Inbox 和
  `Resources/Tools` 兼容表面已移除。外置盘的运行目录不再是当前入口。
- 项目已可在 macOS 上独立运行并全量通过测试。账本路径的盘符翻译收敛在 `src/peach/platform.py`；`R:` → `/Volumes/RESOURCES`、`B:`（115）→ `~/Desktop/IMSL/115`、`A:`（PikPak）→ `~/Desktop/IMSL/Pikpak`，可用 `PEACH_DRIVE_MAP` 覆盖。实测本地与 115 的真实资产均返回 `206`，缩略图 `200`；PikPak 挂载当时掉线，按脱盘正确返回 `503` + `X-Peach-Offline`。账本本身未改写。
- 跨 kind 重复身份已完成两轮合并（`scripts/merge_duplicate_identities.py`）。首轮是规范名完全相同的 35 组（备份 `ledger.pre-identity-merge-20260820-010944.db`）；2026-08-21 又审计「非空作品集合完全相同 + performer 别名等于 creator 名，或 creator 名由 performer 本名与账号别名组成」的变体，再合并 18 组。保留方只看 provenance 不看数量：`r18:performer` / `javbus:performer` 属于发行出演元数据，保留 performer；只有通用 `performer` 的 Stash 扁平断言则保留对应 creator。因此 `小千` 并入 creator `小千 Qian0791`（7 条）、`一个ren` 并入 creator `一个ren yigeren33`（284 条）；16 组有番号、片商和 JavBus 出演来源的重复名保留 performer。真实 Mac ledger 结果：entity 8218→8200、creator 1728→1712、performer 576→574、entity_alias 1125→1143；asset 和 asset_entity 不变，重写 16 条 JavBus `演员:` 兼容标签、删除 291 条已改归 creator 的假演员标签，asset_tag 88538→88247。备份 `ledger.pre-fuzzy-identity-merge-20260821-195651.db`，复核 CSV `generated/duplicate-identity-merge-20260821.csv`，复扫 0 组，`integrity_check=ok`、`foreign_key_check` 0 违规，同步状态 `in-sync`。
- 同 kind 的目录名投影已补齐（2026-08-24，Windows writer）。跨 kind 合并完成后，`R:\Media\<本名 + 账号名>` 这类目录仍各自留着第二条 **同为 creator** 的实体，`(kind, normalized_name)` 唯一约束拦不住它，于是 `/item/830` 的创作者和 `/creators` 索引都并排显示两条。`merge_duplicate_identities.py` 新增同 kind 判据：被丢弃方的作品集合完全落在保留方里、名字词集真包含保留方且多出的词全是保留方别名、被丢弃方只有 `legacy:asset` 断言且无别名无外部引用、且只匹配到唯一保留方。全库命中 2 组并已合并：`小桃 shixiaotaone`(7414) → `小桃`(7413)、`猫猫碎冰冰 & 趣趣`(7549) → `猫猫碎冰冰`(7548)。entity 8185→8183、creator 1703→1701、entity_alias 1523→1525，asset 81,657、asset_entity 155,894、asset_tag 88,049 不变；另按 ADR-0005 把 270 行扁平 `asset.creator` 从目录名改写成保留名。备份 `ledger.pre-same-kind-identity-merge-20260824.db`，复核 CSV `generated/duplicate-identity-merge-20260824.csv`，复扫 0 组，`integrity_check=ok`、外键违规 0，旧名 `shixiaotaone` 作为别名仍可搜到。
- `XX XX` 重复 person 名称已做全表面补漏：根因是 JavBus `.star-name` 节点内的重复文字被 `get_text(" ")` 拼接，且「画像を拡大する」控件文字未过滤；旧清理只覆盖 performer canonical 和作品集合完全相同的跨 kind 实体，没有覆盖 `asset.creator`、`演员:` 标签及重复别名。2026-08-22 Windows writer 实际合并 9 个发行来源支持的假 creator，清空 40 条重复 `asset.creator`，重写或删除全部重复/控件演员标签，清理 42 条无效重复别名；asset 81,753、asset_entity 156,147、performer 568 不变，entity 8,194→8,185、creator 1,712→1,703、asset_tag 88,178→88,177、entity_alias 1,565→1,523。`木村さん` 现为唯一 performer，关联两份 `300MIUM-1239`。备份 `ledger.pre-repeated-identity-names-20260822-103446.db`，复核 CSV `generated/duplicate-identity-merge-20260822.csv` 与 `generated/repeated-identity-name-repair-20260822.csv`；复扫跨 kind 0、重复投影 0，`integrity_check=ok`、外键违规 0。
- 番号体系女优姓名已全量审计并写入真实 Mac ledger（`scripts/localize_performer_names.py`）：574 位中 340 位直接中译、6 组同人旧名合并并中译、8 位用已核实日文名兜底、152 位原本已是映射名；35 位资料不足保持原名，27 位非发行账号不翻译。实际改名 353、增别名 416、重写 `演员:` 兼容标签 1,199；performer 574→568、entity 8200→8194，asset/asset_entity/asset_tag 不变，`integrity_check=ok`、外键违规 0。`Alice Shaku` 现为 `释爱丽丝`，旧罗马字、`釈アリス`、假名继续可解析。备份 `ledger.pre-performer-localization-20260821-203727.db`，复核 CSV `generated/performer-name-localization-20260821.csv`；私有映射固定 revision `8e2d5b7a…`，因上游未声明许可证不进 Git、不分发。
- 本地媒体根多余的一层已去掉（`scripts/flatten_media_level.py`，备份 `ledger.pre-flatten-media-20260820-011133.db`）：`R:\Media\创作者\<名字>` → `R:\Media\<名字>`。`R:\Media` 下原本只有 `创作者` 一个子目录、2552 条本地资产 100% 落在其下，这一层既不分类也不区分，且已名不副实（`合集-洛丽塔 多创作者` 等合集也在里面）。移动 35 个目录（同卷改名，只动元数据）、改写 2552 条路径，本地资产数不变、残留 `创作者` 层 0 条，五条真实资产复验 `206`。计划 CSV：`generated/flatten-media-level.csv`。
- 账本三副本已分离 Windows/macOS 本地工作副本与 Windows 内置盘共享传输点。三者当前均为
  generation 29，唯一写入端为 Windows，Mac 为 reader。generation 29 相比26只增加 asset
  10060 的合法播放遥测；真相/关系表一致。Windows 连续120秒、Mac连续172秒浏览均未改generation。
- 脱盘模式按来源逐个判定：`GET /api/sources` 报告可达性，前端置灰脱盘来源的筛选并在详情页显示「脱盘模式」面板。外置盘不在时 115/PikPak 的 78k 条云端资产仍然可用。

## 界面与交互现状

- 2026-08-26 接手并合入 Claude 的导航修复：抽屉与桌面窄栏共用 `navTo()`，抽屉里的关注、播放列表不再落入错误的首页状态；管理区按「统计 → 人工复核 → 疑似广告 → 重复文件 → 回收站 → 关注 → 高清版」排列。旧 `agent/claude/dup-keeper-options` 分支落后当前主线，不能整体合并；其保留 115/PikPak、整组回收能力主线已有，只移植仍缺的重复项完整路径显示。Vercel Web Interface Guidelines 复核后补齐跳到正文、图标按钮名称、路由标题、设置弹窗焦点闭环、搜索组合焦点、浏览器主题色与移动端 16 px 输入；追溯审计未发现这些行为修复发生回退，但发现 `design.md` 与 `command.md` 被错误合并成同一证据链，现已拆分为独立锁定来源。
- 首页、详情、标签管理（字母表/标签云）、女优墙、厂牌/创作者/系列资料页、统计、沉浸模式均为同一无构建单页表面，桌面与手机共享数据契约。
- 女优/厂牌/创作者/系列名称用于导航；只有内容标签直接叠加筛选。「换一批」是动作，不是筛选状态。
- 共演作品在卡片上叠放前 3 位女优头像并列出前 2 个名字，超出部分写「等 N 人」；契约每条卡片下发至多 `CARD_PERFORMERS`（当前 6）位并给出 `performer_total`。详情页逐行列出全部出镜者，每行带自己的头像，标签只写在第一行；超过 8 位时其余默认收起，一次点击展开，收起的行始终留在 DOM 里。沉浸模式的归属行同样列出前 3 位。
- 键盘快捷键：详情与沉浸模式共用一套播放键，左右按设置里的快进秒数快退/快进，空格暂停或继续（必须 `preventDefault`，否则空格会把页面滚下去）。沉浸模式保留上下切片，与横向快进方向不冲突。取当前视频只能用 `stage.querySelector('video')`：Video.js 挂载后会把 `<video id="vid">` 换成同 id 的 `<div class="video-js">`，真媒体元素是 `#vid_html5_api`，按 id 取会拿到那个 div，写 `currentTime` 读得回来但播放纹丝不动。输入框、文本域和可编辑区域内的按键一律不抢。
- 搜索下拉支持上下键选择、回绕和 `scrollIntoView`；回车优先用高亮项，没有高亮才回退到「空输入用当前推荐词」。列表每次重建都必须把高亮索引归零，否则索引会指向已不存在的行。
- 短查询的 LIKE 分支必须和 FTS 覆盖同样的身份写法：规范名、`entity_alias` 与 `entity_search_term` 都要比对。trigram 分词器要求三字起步，两字查询永远落在 LIKE 分支上，只补检索词救不了——「凉森」搜不到 `涼森れむ` 就是这么来的。
- 卡片身份女优优先；头像本身进入女优资料页。缺失厂牌 Logo 显示首字母，不用任意作品图冒充。
- 「喜欢/为什么喜欢」写 profile 级 `asset_preference`；原因非空会隐含喜欢，但 AI 不能直接改写用户原文。「稍后看」独立写 `watch_queue`。
- 自动 Mix 可复制为 profile 级持久播放列表；列表保存当时的稳定顺序，支持新建、改名、从详情加入、上移、下移、移出、删除和记录当前项。列表删除不删除视频，媒体被永久删除时对应列表项与续播引用会同步清理。
- 详情反馈是 Like、不喜欢、看过、稍后看、回收站五个 Lucide 图标；默认首页排除竖屏，竖屏入口保留完整竖屏集合。
- 长卡连续 hover 5 秒才放大并显示 ±10 秒和详情控制；短卡立即显示稍后看。沉浸模式使用经源码核验的 200 ms TikTok 滚动时序。
- 资料页新增「照片」标签（2026-08-24）：只有该实体真有图片时才出现，作品/照片各带数量。照片按图集（= 目录）分组，点开进 CSS `column-count` 瀑布流，点图开黑底灯箱，底部缩略图条 + 键盘左右键 + 双击放大由本地固定版本 Swiper 14.1.0 提供，脚本只在第一次开灯箱时注入。瀑布流一律读服务端缓存的 `/photo-thumb`（Pillow 缩到 640 宽，存 `photo_root`），只有灯箱当前和相邻的大图读 `/photo` 原图——PikPak 是计费来源。视图可寻址：`?media=photos&set=<图集 id>` 刷新和前进后退都回得到原处。
- 照片当前只覆盖已入账的云盘图片：54,064 张（A: PikPak 43,000、B: 115 11,064），672 个 ≥4 张的图集，44,793 张已挂到实体上，涉及 86 个创作者。`R:` 本地盘的图片**从未入账**（local 的 2,552 条全是 video，且 2,551 条带 `stash_scene_id`——本地是经 Stash 入库的，Stash 只索引视频），所以 `高桥千凛` 这类只在 `R:\Media\<名字>\V\...` 有视频的实体，照片标签是空的。
- 灯箱与头像垫底的四处缺陷已修（2026-08-24，均有页面源测试）：①竖图上下被裁——`max-height:100%` 被 grid 子项的自动最小尺寸（`min-height:auto` = 不得小于内容）盖掉，3072x4096 按宽度铺开有 2533px 高，容器被撑成原高，从 slide 到 img 每层补 `min-height:0` 后实测收成 570x760；②翻页按钮原来叫 `.photonav.next`，撞上详情页无前缀的 `.next`（padding/border/背景整块盖过来，图标偏 5px/2px），改名 `back`/`fwd`；③`.mediatabs`、`.photoback`、`.photoclose`、`.photonav` 的 svg 缺 `stroke:currentColor;fill:none`，被按默认 fill:black 画成黑块，`i-x` 这种开放路径直接消失（「关闭按钮没有 x」）；④头像兜底链停在 `onerror=null` 而不是 `remove()`，取不到图的 `<img>` 留在 DOM 里让 `:has(img)` 继续匹配，首字母垫底回不来、浏览器还把 alt 画出来（`loliburin` 的 `/entity-image` 与 `/avatar` 双 404，整个名字横在圆框里溢出）；四处调用点（卡片 `avatarInner`、资料页大圆框、关联艺人、`/performers` 索引）统一收敛到 `avatarInner`。同时按要求加了鼠标滚轮翻页和显式缩放条（Swiper 的 zoom 只有 in/out，先改 `maxRatio` 再 `in()` 等于设定倍数），并挂 `ResizeObserver` 让 Swiper 在窗口改尺寸后重量——它只在构造那一刻量一次容器。
- 跨 kind 合并判据已从「作品集合完全相同」放宽到「真子集」（2026-08-24）：多出的那几部通常只被 Stash 认成 performer、没有对应本地目录，是常态而非反证；名字那一重证据（别名等于 creator 名，或 creator 名由本名与账号别名拼成）继续兜底，包含方向与数量写进 `match_evidence` 供复核。全库 dry-run 命中 1 组：`哆米`(21) → creator `哆米 Dolmi24`（6/7 部）。`桉X合集` 仍不命中——多出的词「合集」不是 `桉X` 的已登记别名，判子集只说明文件重叠、说明不了那条目录就是这个人，留给人工。复核 CSV `generated/duplicate-identity-merge-20260824-subset.csv`。已按授权 `--apply`：entity 8183→8182、performer 568→567、entity_alias 1525→1526、asset_tag 88049→88042（移除 7 条 `演员:哆米` 扁平投影，身份已归 creator）；asset 81,657 与 asset_entity 155,894 不变——7 条关系只改了 entity_id，行数不动。备份 `ledger.pre-subset-identity-merge-20260824.db`，`integrity_check=ok`、外键违规 0、无孤儿关系，旧名 `哆米` 作为别名仍解析得到，`/item/2541` 已只剩一条身份。
- 参考 Beeg 的控件和表面层均已登记当前 CSS/JS hash。当前源码证明普通标签为透明底加 15% 白色内描边，厂牌为 5% 白色叠层加 10% 内描边；frost 只用于被选中的浮层，不再笼统套到所有胶囊。49 vh 页首光晕按实测像素重建，不复制许可不明的 Beeg 位图。
- 当前厂牌 Logo 覆盖 28/114，仍有 86 个待补。女优头像 P2 已把 Gfriends 补成候选 Provider：旧名字链、质量档位和长短边门槛继续复用；新增内容寻址缓存、JPEG/PNG 完整解码、SHA-256 精确去重、逐条 provenance、来源健康报告及 `/review` 可识别候选。它只写 `generated` 下的候选/缓存/报告，不安装头像、不写 ledger、不自动批准。
- 公共资料页 URL 已改为 `/performers/{name}`、`/studios/{name}`、`/creators/{name}`、`/series/{name}`；旧 `/entity/{kind}/{name}` 已删除。内部 JSON 兼容端点仍为 `/api/entity`。
- 收起详情或导航离开时会暂停视频、清空 `src`、调用 `load()` 并移除元素，不再留下后台播放/下载。详情打开时筛选栏取消 sticky，避免上滚遮住详情顶部。
- 标签统一使用同一圆角和内边距 token；厂牌/来源保留独立身份样式。选中框改为内描边，不会被卡片边缘或 hover 样式裁掉。
- 顶栏提供显式多选模式；`Ctrl`/⌘ 单项切换，`Shift` 在当前可见网格中连续范围选择。选中标记位于右上角，不覆盖来源徽标；回收站卡片会灰化并显示独立「回收站」标记。
- 详情身份按名称去重；女优与厂牌按内容宽度自然相邻，空间不足时自动换行；系列使用无外框、无下划线的图标链接显示全称，不复用内容标签胶囊。喜爱理由由反馈操作组中的图标展开，首页流和详情来源徽标只显示图标，侧栏来源筛选保留文字。两条观看进度只显示标题和百分比，常驻实现说明已删除。反馈操作组固定高度，不再被侧栏内容压成横线。标签隐藏只写 profile 覆盖，不破坏原始来源断言。
- 已完成首轮界面文案审计：删除标题复述、实现状态说明、随机示例占位符和模型自我声明；删除保护、隐私边界、流量成本及陌生状态说明继续保留。
- 侧栏、抽屉和粘性栏使用 Beeg 当前源码实测的透明层与 blur 数值；页面背景不再是纯黑，侧栏不再是纯灰。本轮没有为了装饰引入动画库，后续动效必须先复用审计并只表达状态/连续性。
- 详情中的本地来源图标已补齐 `stroke: currentColor` 和 `fill: none`，不再因 SVG 默认黑色而不可见。标签添加使用弹窗完成搜索、最近使用、全部标签、已选状态和键盘操作；侧栏入口简化为「艺人」「标签」，并删除装饰性分隔线。
- 首页创作者头像已移除常驻黑框，只在 hover/选中时显示状态描边。女优/厂牌/创作者/系列资料页打开后隐藏首页人物、厂牌和筛选栏；资料区取消巨型外框，桌面头像为 160 px，并在资料下展示真实标签与关联艺人。厂牌资料优先使用 Logo，只有缺失时才使用实体图，不再用代表作品截图冒充厂牌头像。
- 实体资料页标签只筛选当前实体作品，不再跳回首页做全局筛选；当前标签写入资料页查询参数，便于返回和分享。首页状态标签已精简为「全部、没看过、稍后看、已标记」，与右侧内容标签之间恢复语义分隔线。搜索框显示随机推荐关键词，不加「试试：」；空输入聚焦后按 Enter 会直接搜索当前推荐词。
- 资料页圆头像按检出的人脸取景（2026-08-22）：512 张实体图多为竖版，几何居中裁切会切掉头顶；`scripts/detect_avatar_faces.py` 用与封面同一套 Haar 离线检出 313 张，283 张有取景余量，sidecar `<kind>-<id>.face.json` 存归一化脸心与换算好的 object-position，换算公式只有一份（`web_contract.face_focus`）。`/api/entity` 以 `avatar_focus` 下发，未检出或未算过的实体维持几何居中；详情图回落代表作截图时会先摘掉内联取景。新增头像后重跑一次脚本即可补齐。
- 大结果集不再按总数一次构建：实体页每批 48、首页 60、艺人索引 120、标签索引 180、疑似广告 DOM 每批 60。实体与首页第二页起跳过全量总数统计；无限滚动有单请求锁，快速切换会丢弃迟到响应，顶部聚合复用 30 秒会话缓存。
- 详情播放器使用本地固定版本 Video.js 8.23.9，提供 ±10 秒、画中画和播放统计。远端原生 MP4 优先走 HLS 片段，HLS 失败仍回退标准 HTTP Range；不再把浏览器的开放区间伪截成 32 MiB。item 29297 的权威总时长固定为 28,639.916 秒（`7:57:19`），不再随缓存增长。
- 详情全屏覆盖播放器的 `76vh`/固定比例限制，视频按播放器尺寸渲染；加载或等待时显示基于 VHS/媒体请求的实际速度估算。沉浸模式横屏使用全视口 `object-fit:cover`，竖屏根据媒体真实宽高切到 `contain`，避免桌面宽屏裁掉上下画面；初次加载和切换下一条时显示 spinner 与速度，按钮采用 Shorts 取证的 tonal 圆角层级。
- 本批修复顶部品牌图与正文 Logo 不一致、竖屏推荐条固定在首批作品中间、竖屏卡片按实际宽高显示、卡片 hover 蓝色边框、半透明层过透、详情关闭时导航仍残留、ambient 上下断层和详情按钮 hover；搜索历史迁移到共享 `search_history` 表。
- 回收站有独立入口 `peach.local/trash`（后端 `/trash` 走 SPA，前端 `restoreRoute` 直接进 `state=trash`）。
- 疑似广告的判据有两个维度。文件名维度看「剥掉推广词后还剩不剩内容」（`promo_residue`）；
  目录维度看创作者位和路径——广告包的文件名往往干净（`极道世界.mp4`），唯一线索是旧导入器
  从目录名投影出来的创作者位，或 `bbsxv.xyz-DOCP-324` 这种「域名紧贴番号」的打包形态。
  裸域名水印目录（`www.98T.la@账号`、`huachishe.com@系列`）是转载来源标注，不算广告。
  `path` 只参与打分，不下发给前端。创作者位本身是推广站域名时，「有归属所以是正片」的减分
  不成立，两处对 creator 的信任都先排除它。`find_ads.py` 的对应判据是 D 与 E。
- `find_ads.py` 在 macOS 上曾整体失准：账本路径是 Windows 口径，`os.path.dirname` 不认反斜杠，
  目录恒为空串，判据 A/E 永不命中，判据 B 的「同目录」分组退化成跨整个库比对。已改用
  `PureWindowsPath`，两个平台结果一致，`test_ledger_paths_are_split_with_windows_semantics_on_any_host` 守这条线。
- 只读 409 的文案已分层：响应体 `error` 保持 `ledger read-only`，`detail` 保留内部诊断原话，
  新增 `message` 给界面直接展示——说明写入端是谁、本机为何只读、下一步去写入端操作或在托盘
  「接管 Ledger 写入」。前端 `api()` 优先取 `message`，冲突状态则指向「同步 Ledger」。
- 复核页 `cover_sources` 这一层的通过/跳过/拒绝此前全部 400：`w_review_decision` 的类别白名单
  漏了它。已放行（只记 `review_decision`，不碰真相字段）。
- 疑似广告是处置队列：队列说明行随页面正常滚走，不复用普通作品列表的 sticky 排序栏。批量或详情加入回收站后会立即刷新队列；Ledger 冲突等非 2xx 写入会明确报错，不再把错误 JSON 当成功后让条目原样出现。
- 回收站的两条删除路径此前从未真正执行过，已修复：`media.py` 漏 `from functools import lru_cache` 导致整个包 import 失败；`ASSET_REFERENCE_TABLES` 从未定义，`/api/batch` 的 `delete` 必然 `NameError`；`/api/trash/empty` 只加了 dispatch 分支、`w_empty_trash` 没有函数体。现已统一到 `purge_assets()` 并补齐数据层测试。之前「API 写读删已复核」的说法不成立，属于未验证即结论。
- 管理界面 `/review` 已覆盖元数据字段、创作者标签、厂牌 Logo、女优头像、西方身份、番号目录、FC2 评论标记、FC2 跨号相似和媒体失败；每项尽量显示代表封面并可打开原视频。封面抓取成功、尺寸和缺失改回机械状态，不再占人工复核。Javinizer-Go 元数据按「番号 × 字段」并列演员、厂牌、系列、发行日期和标签候选，官方/官方镜像 tag 优先；批准必须选中具体来源值并留下 provenance。
- HLS 除开头一两段外全部失败过，2026-08-18 已修复。`-copyts` 保留原始时间轴后，FFmpeg 把 `-t` 当成绝对结束时刻而不是片段时长，每段的 `-t` 都约等于一个片段长，起点超过它的片段一律「已经过期」，FFmpeg 以退出码 0、空 stderr 写出 0 字节，服务端只能报一句没有内容的 `ffmpeg failed`。实测 asset 6562（6,332 秒）：片段 0、1 返回 200，片段 2 与 300 都是 503；片段缓存目录里 6562、29914、19490 三个资产也都只留下 `0.ts` 与 `1.ts`。所以症状不只是拖不动，播到约 20 秒就会断。修法是保留 `-copyts`、把 `-t 时长` 换成绝对终点 `-to 起点+时长`；删掉 `-copyts` 同样能出片，但首个 PTS 会退回 0.069，每段都自称从 0 开始，正是当初引入 `-copyts` 要解决的拖动跳位。隔离实例实测片段 2、300、633 全部返回 200（47.2 MB、41.1 MB、69.3 MB），手工核验片段 300 首个 PTS 为 2997.995，绝对位置与跨段连续性都对。生产托盘已于 2026-08-18 重启并复验：asset 6562 的片段 2、300 与 asset 29914 的片段 5 均返回 200。
- 同批把静默失败改为自陈：FFmpeg 退出码 0、stderr 全空却写出 0 字节时，错误信息带上 `returncode`、字节数与 `ss`/`to`，不再只说 `ffmpeg failed`。上面那个缺陷能藏这么久，正是因为日志里那句话什么都没说。
- 远端 MP4 已改为默认标准 Range，HLS 转为按需（`/api/stream-plan?mode=hls`），见 ADR-0016。起因是 asset 22716（115 的 HEVC 重制 MP4）在详情页黑屏：分片全部 200、数据进了缓冲、时间轴照走，但 `videoWidth=0`、解码 0 帧、无 error 事件。`-c copy` 把 HEVC 原样装进 MPEG-TS，而 Chromium 的 MSE 不支持 TS 里的 HEVC；同一浏览器实测 `video/mp2t; codecs="hvc1…"` 为 `false`、`video/mp4; codecs="hvc1…"` 为 `true`，直接 Range 播同一文件解码 997 帧、拖动后继续出帧。文件名含 `HEVC` 的 115 视频有 248 条、PikPak 2 条，此前全部受影响。生产重启后复验 22716：默认计划为 `range`，`mode=hls` 仍给出 76 段计划，播放列表返回 200；详情页取到 `/stream?id=22716`、`readyState=4`、`1920×1080`，当前帧平均亮度 147.1、非黑像素 99.3%。
- HLS 分片改为关键帧对齐：`peach.mp4index` 从 MP4 `moov/stss` 直接读关键帧表（实测 0.01 秒，`moov` 在尾部也能定位），播放列表报真实时长；时间戳改用 `-copyts` 保持跨段连续；片段缓存写入磁盘并按最后访问时间淘汰；FFmpeg 并发加信号量闸门。读不出关键帧的片源直接回退标准 Range，`/api/stream-plan` 也只在计划成立且带 session 时才宣告 HLS。
- 厂牌 Logo 来源改为厂牌自己的社交账号头像（`scripts/fetch_studio_avatar_candidates.py`）。已确认 14 个 handle 并**逐张看图核对品牌归属**后落盘：Deep's、Hunter、Alice JAPAN、E-BODY、Glory Quest、K M Produce、TMA、Aroma Planning、M's Video Group、DAHLIA、Milu、Das、Muku、ROCKET；其中 Das 与 Muku 由 `scripts/find_studio_socials.py` 穿过官网年龄门后取得，Deep's 也由官网独立复证。Logo P4 新增内容寻址缓存、逐条 provenance、格式/尺寸/方形归一、SHA-256、同厂牌感知哈希、跨厂牌精确重复门槛和健康报告；真实刷新 86 行时 14 个确认来源全部 unchanged、72 个无 handle、变化/重复/错误均 0。机械空结果和 unchanged 不再占 `/review`，只有新图、视觉真变化或 needs_confirmation 才进入。映射表 `peach-data/generated/studio-x-handles.csv`，图片 `generated/studio-logos/`；其余 72 个无可信 handle，继续留空待取证。
- Logo 归属的判据是图不是 handle：`@ms_harapekori` 看不出与 M's Video Group 的关系，看图确认是对的；`@OFFICEKS` 能取到 400×400 但图只有色块无品牌文字，而同名公司有多家，因此判为未取得。`@bazooka`、`@bibibi_25` 同理被排除。
- 复核层已加固：候选按前缀取最新批次（不再写死日期）、缺主键的行跳过并计数（不再退化成行号）、只有 `status=candidate` 的 creator 候选可批准、批准的 creator/tags 以候选文件为权威（请求体只作确认）、未勾选整条通过受 `REVIEW_APPLY_LIMIT=500` 约束、写入改为 `executemany` 并在完成后 `cache_bust()`。`vision_creator_review` 已纳入统计标签覆盖和 Top 标签口径。`/api/review` 走缓存，创作者预览由一次分组查询取代 42 次三重 LEFT JOIN。候选目录改由 `PeachSettings.candidate_root` 提供，测试不再读真实 `generated` 目录。

## 数据与批处理

- 迁移后的完整性检查为 `ok`，外键违规为 0。资产与视频计数只写在文末自动区块，正文不复制。
- 已核对并删除 `asce/The.Great.Escape.S04` 正常向剧集：13 个视频、13 个字幕、16 个派生图，同步清理 26 条 ledger 资产。原因是旧导入器把集合目录 `asce` 投影为创作者，再把创作者板上的低置信标签批量传播。`0009` 已移除 `asce` 假创作者及其 `vision_creator` 断言，保留其他独立来源标签。
- 番号刮削已处理 1,104 个非 FC2 番号，715 条取得数据；所有 330 个 FC2 在三来源样本中零命中，因此默认跳过。
- 创作者视觉板已处理 30 张，27 位创作者写入 27,295 条 `vision_creator` 标签，覆盖 4,518 个视频；置信度固定为 0.6，区别于逐条证据。
- `find_ads.py` 只生成候选，不删除。当前 82 条、约 1.5 GB；77 条确认、5 条存疑。`BNST033.mp4` 已从错误待删结论中排除。
- 115 时长修复后，未知时长不再写 0，而写失败值 `-1`；`--redo zero|failed|all` 可重试。
- 2026-08-15 的 115 接触表批次已正常结束：处理 982、失败 34、耗时 3.19 小时，锁文件已释放；托盘重启没有中断该任务。剩余量继续以文末自动区块的实时口径为准。
- 115/PikPak 抽帧主要成本是 CloudDrive 块预取流量：实测九帧接触表约为 115 285 MB、PikPak 163 MB。PikPak 全量抽帧约 773 GB，暂不启动。
- 2026-08-22 已把 PikPak 下一批范围收窄为「全量重跑 probe → 官方封套 + 九帧缩略图」，不继续跑标签、人物归属或其他元数据刮削。Mac reader 只在账本副本上做了 1 条真实媒体抽样：506 MiB / 1,769 秒视频耗时 11.69 秒，Stash 计得下载 120.9 MiB、上传约 0.10 MiB，路线为香港代理链；封套 `KUZU-25010` 用 3.25 秒确认未取得，下载约 14 KiB。全量夜跑交给 Windows writer，第一晚保留 200 GB 流量上限，见 `docs/PIKPAK.md`。
- `RM-TrafficWatch` 常驻心跳已改用 `pythonw.exe` 隐藏运行。默认 200 GB 守卫统计代理流量；直连来源需显式 `--count-direct`。
- JAV 浏览模式已就位：顶栏「番」入口切换 `state.jav`，列表要求番号形态再加厂牌、女优、系列或发行日期等发行证据；FC2 ID 单独成立。只有 creator `MIB` 的 `JI-103` 不再误入。模式恒不含竖屏，资料页、`/api/tops` 与 `/api/facets` 继承同一口径。
- 版式切换（正封 4:3 / 封套 16:9 / 预览图）只在 JAV 语境出现，按钮长在排序行里跟着 `renderCount()` 一起重建——放独立容器会被重画覆盖。取景按图片自身宽高比分流：整张封套约 1.48 取右侧，竖版正封约 0.70 整张用，`onload` 写 `data-frame`，服务端不另存这个比例。
- 顶部三层跟着「换一批」的同一个种子轮换。只失效缓存不够：`q_tops` 是 `ORDER BY n DESC` 的确定性查询，实测两次请求结果完全相同。改为放大候选池到展示位的 4 倍再按种子确定性抽样，同种子可重复、不同种子换人、无种子退回严格前 N。
- 封面抓取默认跳过 FC2：三源实测零命中（见 HANDOFF），400 个必然落空的请求每次续跑都会重试一遍；`--all-codes` 仍可强制尝试。队列的形态判据与 `web_contract.is_jav_code` 共用一份实现。已落盘张数与待抓队列只看 `docs/OX-WINDOWS-JAV.md` 的实测快照，起跑前重算。
- 抓取此前两次死在半路：第一次静默丢掉全部进度，第二次拿到堆栈 `httpx.ConnectError: UNEXPECTED_EOF_WHILE_READING`——一个番号的 SSL 抖动让整个三小时的任务退出，日志停在半路看起来像跑完了。现已按条吞掉异常记进 CSV 再继续，长跑批处理不因单条连接问题整体退出。
- FC2 的数据线走 fc2cmadb（`scripts/fetch_fc2_metadata.py`，需登录 cookie，只写 CSV 不写 ledger）。页面是 Laravel + Inertia，数据在 `<script type="application/json">` 里，不用解析 HTML。正文能拿到标题、发售日、时长、卖家与封面；真正的价值在评论区的两类人工标记：`<video_id>　演员名`（全角空格分隔，一行可多人）与 `3312576-4 = 2471432` 的等价关系。
- 等价关系同时是合集判据。`FC2PPV-3312576` 是 21 段合集，本地按 `-1.mp4` 分片存。**合集封面不下发给分片**，否则 21 段不同内容会显示同一张图；判为合集时 `cover_url` 留空，分片回落到自己的缩略图。
- 只抓库里有的 442 个作品页，但每页评论全量留存：一页评论常给几十个 video_id 标演员，本地只对上两三个，只留对得上的等于把评论区的价值丢掉。产出候选 CSV（复核页 `fc2_markings` 层）、按 video_id 汇总的收获 CSV，以及原始评论 JSONL——留原文是因为解析规则一定会漏掉某种写法，有原文就不必重爬。
- 线上实测补了三种写法：全角等号 `＝2407240`（主语省略即本页）、「一行名字 + 若干作品链接」的作品集式标记（多指向姊妹站 fc2ppvdb），以及 `comments.data` 与 `article.comments` 重叠导致同一条评论投两票——票数是这批候选唯一的置信度信号，翻倍等于把它作废。演员常标在别的作品页上，候选行的演员由全量收获回填。跨号 P2 将全部等价 pair 留在 evidence，只把两边都有本地资产的关系送进 `fc2_similarity` 复核；exact hash 可单独成候选，弱相似必须同时满足时长、体积、分辨率和共同演员，合集/分片绝不自动合并。
- 番号目录冒充创作者的清理已对生产 ledger 执行（`scripts/audit_code_creators.py`，备份 `ledger.pre-codecreator-20260818-184741.db`）。命中 44 个：31 个判为番号、2 个判为站点作品号、11 个判为存疑只入 CSV。写入删创作者关系 121 条、删实体 33 个、清扁平字段 121 条，`code` 净增 31（另外 65 条已有值，脚本只填空缺不覆盖）。asset、asset_tag、performer 计数一条未变，完整性 `ok`、外键违规 0。`HD-abp-758`、`pppd-937ch`、`PRED-785ch`、`Carib-040221-001-FHD` 等假身份已消失，`banbi_555`、`raikun325`、`luckydog22` 等真实上传者与全部 pixiv 画师保留。复核 CSV：`peach-data/generated/code-creator-review.csv`。
- 判据不看名字形态，只看文件级证据：目录内的媒体文件名必须解析出同一个番号。`HD-` 是画质前缀、`-CH` 是中文字幕版后缀，两者都会让番号提取放弃，于是 `code` 留空、目录名顶替身份。形态相同但真相不同的 `banbi_555`（myfans 账号）和 `AH18`（pixiv 画师，path 是 URL）因此不会命中。
- 日文汉字身份已补简体检索词（`scripts/add_chinese_search_terms.py`，备份 `ledger.pre-cnterms-20260818-210036.db`）：280 条写入 `entity_search_term`（performer 208、creator 71、series 1），`entity_search_term` 52 → 332，asset 与 entity 计数一条未变，完整性 `ok`、外键违规 0。实测搜「凉森」由 0 条变 24 条，「铃村」15 条、「七泽」10 条，日文原写法「涼森」仍是 24 条无回归，反例「凉宫」仍为 0。映射表只覆盖本库身份里实际出现的字，表外的字原样保留；日文独有字（`凪`、`辻`、`雫`、`笹`、`咲`、`栞`、`冴`、`榊`）没有简体对应，不列。
- 上述旧脚本只做字形归一、不做译名的问题已由 2026-08-21 全量姓名映射批次收尾；仍未命中的 35 位保持原名，不用字形转换冒充中译。
- `entity_search_term.purpose` 有 CHECK 约束，只接受 `discovery` / `source_lookup`；检索用途一律写 `discovery`，与既有的 52 条 stash 检索词一致。
- 西方网黄回配 babepedia 的候选已产出（`scripts/match_babepedia_creators.py`，只写 CSV 不写 ledger）：195 个拉丁名 creator 中命中 19 个、需人工确认 8 个、确认无档案 165 个、限流未取得 3 个。判据只认 `<title>`；页面上的 `/babe/` 链接全是 `thumbshot` 相关推荐，实测查 `SexySaffron` 会抓出毫无关系的 `Brianna_Marchant`，一律不采信。待修：去尾部数字属于有损变体，`fantia-3760310` 经它削成 `fantia` 后误配到 `Rio Hcup Fantia`，须封顶为「需人工确认」。
- 目录创作者审计覆盖全部 66,252 条历史关系：58,803 条为仅目录候选、6,621 条缺少路径交叉核验、745 条 TokyoDolls 错挂「捅主任」已解除、83 条「足交仙人」已按文件名/水印证据归到 `suzuq`。逐项和汇总 CSV 位于 `peach-data/review/creator-attribution-*-20260815.csv`；没有删除媒体或标签。
- `DiskGuard` 已进入主线并接入 `probe.py`、`sheets.py`、`creator_boards.py`：默认每 20 秒复查系统盘实际余量，触线后停止领取新任务、保留已完成结果并返回退出码 3。CloudDrive 当前缓存上限 50 GiB、策略 LRU；本轮核验时没有上述旧代码长任务在运行。
- 机械识别批次已接手：读取 42 个未处理创作者板，生成 `peach-data/generated/creator-tags-candidate-20260817.csv`；仅输出 `candidate/skip`，未写入 ledger。现有 `creator-tags-review.csv` 的 `applied` 记录不重复处理，聚合目录和广告板保留 `skip`。
- Logo/头像机械候选已导出：`studio-logo-candidate-20260817.csv` 含 86 个缺失厂牌，`performer-avatar-candidate-20260817.csv` 含 20 个 `no_avatar/avatar_rejected` 女优；均只保留来源候选，不写真相字段。
- 115 抽帧 worker 已接入 `resolve_case_insensitive`：小样本通过后完成 33 条 9 帧批次，31 条成功登记 snapshot、2 条仍失败（asset `12510`、`18349`），未伪报成功；日志 `peach-data/logs/sheets-20260817-171917.log`。
- 这 2 条失败已于 2026-08-18 用 FFmpeg 直接复现定因，两条是不同问题，都不是路径或色彩元数据：
  - `18349`（`B:\xxr\1(14)(1).mp4`）：ledger 记的是 `752.24` 秒、`1280×720`，ffprobe 实测为 `110.87` 秒、`1920×1072`，只有 `size` 98,246,962 两边一致。`make_sheet` 按 ledger 时长算的 9 个采样点里有 8 个落在文件末尾之后，只抽到 1 帧，触发 `len(captured) < 2` 判失败。t=61.8 秒实测能抽出 11,405 字节的帧，片源可用；要修的是 ledger 的时长与分辨率，不是抽帧代码。
  - `12510`（`捅主任` 目录下的 `好色™ Tv.mp4`）：FFmpeg 报 `stream 0, missing mandatory atoms, broken header`，`profile`、`pix_fmt` 均为 `unknown`、`level=-99`，解码器建不起来，任何时间戳都抽不出帧。片源本身损坏，不再重试。
- 两条都已按上述结论收尾（备份 `peach-data/database/ledger.pre-duration-fix-20260818-103252.db`）：
  - `18349` 由 `probe.py --asset 18349` 重探改正，`duration` 752.24 → 110.866667、分辨率 1280×720 → 1920×1072、`fps` 25 → 30，情境层随之由「短/720P」变为「速食/2K」。随后 `sheets.py --asset 18349` 重抽成功，产物 `snapshots\cloud\115\45\4519ff7e5d496e1b.jpg` 为 1440×804（3×3 九帧、120,876 字节）并已登记 `snapshot_path`。写入前后 asset 81,770、video 24,890、asset_tag 88,542、entity 8,286 均不变，`integrity_check` 为 `ok`、外键违规 0，只有这一行的事实字段发生变化。
  - `12510` 经 `/api/review/decision` 写入 `review_decision`（`category=media_failure`、`status=rejected`），note 记录了 FFmpeg 原始报错，`applied_assets` 为 0，不动任何真相字段。`/review` 媒体失败层的待办由 2 条降为 1 条，即这条已判定的坏片源。
- `probe.py` 与 `sheets.py` 都新增了 `--asset`：按 id 点名处理，绕过各自的批量筛选，计费来源与 `online` 边界照旧生效。`probe` 的 `--redo` 只认 0 和 -1，够不着 `18349` 这种「看着正常但是错的」时长；`sheets` 点名时还会绕过「产物已存在」短路，否则重抽会被上一次的错结果短路掉。两者都有测试。
- 由此暴露的代码缺陷已修：`scripts/sheets.py` 的 `make_sheet` 改为返回「是否成功 + 原因」，一帧都解不出记 `broken_source`、解得出一部分记 `duration_mismatch`，另有 `tile_failed`、`no_duration`、`exception`。worker 逐条写 `[fail] asset <id> <原因> <路径>`，批次结束再打一行原因分布。之前只累加失败计数，两种完全不同的故障在日志里长得一样。
- 番号体系女优身份已回填真实 ledger（备份 `ledger.pre-performer-merge-20260815.db`）：556 位中 496 位改为日文规范名，写入 980 条别名（罗马字、假名、曾用名）、496 条外部引用，缓存高清头像 498 张（14 → 512）。完整性 `ok`、外键违规 0、资产数 81,847 不变；实体 606 → 604。
- 名字取自 r18 `combined=` 端点的罗马字精确回配（425 位），av-wiki 的 URL slug 回配补 63 位，javdb 多番号交集补 6 位，双源确认 9 位。r18 记录的是拍摄当时的艺名，av-wiki 用于纠正到现用艺名，旧名一律降为别名。
- 头像来自 Gfriends 图库（10.7 万张、51 个质量分档目录），门槛为长边 ≥500 且短边 ≥300。竖构图人像不能套方图的短边 512 门槛，否则会拒掉 `0-Hand-Storage`(334×501) 与 `8-GRAPHIS`(360×508) 这些最优来源。5 位所有候选都不过门槛，宁缺毋滥。
- 撞名两组已按用户授权合并：`橋本ありな`/`新ありな` 与 `黒川さりな`/`百永さりな` 各自是同一人的新旧艺名各成一个实体。合并由 `peach.entities.merge_entity` 执行，保留作品多的一侧，四种旧称全部留作别名。
- 番号版本后缀已规范化并落库（备份 `ledger.pre-code-suffix-20260815.db`）：226 条文件名带 `-C`/`-CH`/`-UC`/`-U`/`-4K` 后缀，补齐 21 条缺失 `code`、新增 215 条标签，「中文字幕」由 18 条升到 223 条。`-C` 经证实是同一作品的另一个版本而非分卷：`abw-104.mp4` 与 `abw-104-C.mp4` 同为 12,725 秒、6.12 GB 对 9.80 GB。
- 画质后缀（`-4K`/`-FHD`）刻意不打标签，画质由 probe 从流信息推导；与现有 `code` 冲突的 2 条只报告不覆盖；UUID 文件名按整串形态排除，否则 `DCE7230C-730E-…` 会被解析成 `DCE-7230`。
- 待打标创作者板按路径结构先做了聚合筛查：56 张 pending 中 9 张是平台/群组目录（1,504 条），已标 `skip` 并记录证据；`Myfans` 下含至少 4 位不同创作者，`RiaKurumi` 实为女优且作品分属三个厂牌。其余 47 位为单一创作者，已完成 `ukiru`(343 条)、`EddyS__z`(204 条) 两位的 candidate。
- 2026-08-17 身份合并批次（备份 `ledger.pre-dupmerge-20260817.db`）：`merge_entity` 实现与测试回到主线后，按 `performer-identity-20260815.csv` 的核对结论执行——5 对同人合并（白咲碧、立花美涼、前田かおり、小花のん、丘咲エミリ，保留资产多的一侧，重复串旧写法全部留作别名）、25 位 `XX XX` 重复串 canonical_name 去重、2 个非人名 entity 删除（`画像を拡大する` 是网站 UI 文本、`Kuchiku * Reverse Bunny` 是服装词）。完成后 FK 违规 0、完整性 `ok`、performer 实体 604→597。首批执行曾留下 5 条外键孤儿行（merge_entity 原实现依赖 FK 级联，sqlite 连接默认 FK 关闭），已随代码修复一并清理。

## 验证基线

- 2026-08-25 Windows `0.6.4`：`& .\scripts\test.ps1` 全量 641 项通过、12 项按平台跳过；新增迁移、数据事务、API、页面源、媒体删除引用与 PyInstaller 资源根测试均通过。
- 当前主分支基线：2026-08-25 于 macOS 主目录实测 `./scripts/test.sh` 全量 608 项通过、4 项按平台跳过。不接受「只跑本批相关」的缩水口径。覆盖版本、托盘、迁移、mDNS、媒体转码、Provider、DiskGuard、语义路由、标准 Range、Video.js、稳定时长、详情播放释放、多选、实体资料、分页性能边界、搜索历史、广告判据，以及回收站的还原/彻底删除/清空与删不掉文件的降级。
- 前一生产版本已分别通过 HTTP/HTTPS health、`peach.local` 解析、真实 CloudDrive Range、桌面 1280×720 和手机 390×844 检查。本次 HLS 代码已切换生产托盘；真实资产 `31222/MIDE-981-C.mp4` 的中段 HLS 片段在严格 CA HTTPS 下返回 `200`、约 9.7 MB，响应后的临时文件已清理。尚未完成浏览器 seek 和手机 HLS 视觉验收。
- 浏览器验收不得写真实喜欢、反馈或播放数据；需要交互写入时使用隔离 ledger 副本。
- 并行 worktree 测试必须设置 `PYTHONPATH=<当前工作树>\src` 并核对 `peach.__file__`，否则 editable install 可能误加载主目录旧代码。
- 2026-08-18 重启生产托盘并复验：HTTP `/healthz` 与项目 CA 严格校验的 HTTPS `/healthz` 都返回 `0.6.1`、`db=available`，`peach.local` 解析为 `192.168.50.162`，80/443 由新托盘子进程监听。注意 Windows 上的 `curl --cacert` 走 schannel 会因「revocation status is unknown」失败，那是 schannel 对私有 CA 的吊销检查限制，不是链校验失败；改用 Python `ssl.create_default_context(cafile=...)`（`check_hostname`、`CERT_REQUIRED` 均开）可完成同等严格校验并返回 200。不得因 schannel 失败就改用 HTTP 成功来声称 HTTPS 通过。
- 本批已重启生产托盘。HTTP 与 HTTPS `/healthz` 均返回 `0.6.1`；HTTPS 使用项目 CA 严格校验，`peach.local` 解析为 `192.168.50.162`，80/443 分别由新托盘子进程监听。生产只读 Range 对 item 29297 返回 `206`、精确 `bytes 0-1048575/4590823524`；HLS plan/中段片段对 item 31222 已在 HTTPS 下通过；桌面与 390×844 的旧 direct 播放验收仍未替换为 HLS seek 验收。
- 本批在隔离服务、真实 ledger 只读条件下完成桌面默认视口与 390×844 手机验收：Prestige 总数 248 时首批只构建 48 张、追加后 96 张；桌面和手机均无横向溢出。女优页标签筛选前后头像 URL 保持不变并只重建作品区；标签页手机完成态为 169 项，四种旧模糊时长标签为 0。浏览器控制台错误/警告为 0。
- 详情播放释放和 sticky 遮挡在隔离 ledger 浏览器中验收；生产浏览器只做无写入首页/样式检查，未污染真实播放、喜欢或反馈数据。
- 2026-08-17 批代码改动（merge_entity 回归主线、sheets 色彩元数据重试、media 大小写不敏感匹配）模块级 `unittest` 全部通过：`test_entity_merge` 4 项、`test_scripts` 16 项、`test_media` 9 项等。唯一可信入口是各平台的 `test.ps1` / `test.sh`。（当时把「全量 discover 会挂起」归因为运行器竞态，已被证伪，成因见 `docs/HANDOFF.md`。）
- 2026-08-19 发现「测试通过」曾有一段并不成立：`test_rm_web.py` 与 `test_web_ui.py` 各有一处 `if __name__ == "__main__": unittest.main()` 被插在类中间，其后缩进 4 格的 16 条测试被解析成 if 块语句，从写下起就没被收集过——不报错、不告警，其中包括复核页三类候选的全部数据层断言。修正后全量由 355 升到 371 且全绿。`tests/test_test_collection.py` 用 AST 禁止这种形状，避免再出现「绿灯但没覆盖」。

- 2026-08-21 macOS 最新基线：`./scripts/test.sh` 全量 468 项通过、3 项跳过；Windows 当前状态提交
  `& .\scripts\test.ps1` 全量 460 项通过、12 项按平台跳过；上下文预算检查通过。
- 2026-08-22 Javinizer-Go P0 已部署到 Windows：真实 ledger limit=10 生成 43 组（演员10、厂牌10、系列4、发行日期10、标签9）及10份 raw JSON，错误0。2026-08-24 复核时这43组仍为候选，`metadata_fields` 批准数0，因此真实 `release_date` 仍为0条、`javinizer:*:tag` 仍为0条；旧 `r18` 标签已有2,371条。详情已经消费 `release_date` 与批准后的内容标签，人工批准后直接显示。
- Javinizer-Go P1 来源策略层已实现：锁定 v1.5.1 的14源白名单，新增 baseline（默认仍仅 r18dev）、censored、uncensored、fc2 显式 profile；兼容 `--sources`，冲突与未知 source 在联网前拒绝。五个 Peach 字段分别按 policy 排序，候选携带 source profile、policy version、field rank、source kind 与显式 official。每批无论有无错误都写 `metadata-source-health-*.csv`，按 source 区分快照复用、联网成功、空结果、错误、冷却跳过、耗时与五字段命中。没有批量批准、自动写库或 schema 迁移。
- Windows 无外置盘生产验收：HTTP 与严格 CA HTTPS `/healthz` 返回 200，账本、FFmpeg、115 和
  PikPak 可用，只有 `local` 来源离线；115 HTTP 与 PikPak 严格 HTTPS 各完成 1 KiB `206` Range。
- 双机同时在线时两个名字互不串台；`peach-win.local` 与 `peach.local` 分别只由
  `192.168.50.162`、`192.168.50.88` 应答。
- 两台机器的 worktree 各自独立，按分支本机重建，不跨机器复制。2026-08-25 macOS 侧完成一轮清空：
  39 个 worktree 与 41 条分支全部删除，只留 `master`。删除前逐条核对——32 条已并入 `origin/master`，
  2 条的补丁已被压缩合并（`git cherry` 判定），7 条真有独有提交的逐条比对后处置，见下。

## 下一批工作

基础设施本机化、显式 writer/reader、运行中安全手动同步和生成资产的跨机同步都已完成。剩余基础设施
边界是 durable artifact 拆分与 macOS 拔盘后的完整验收。部分历史运维脚本仍硬编码 `R:\peach-data`，
在改为读取 `PeachSettings` 前不得对当前账本盲目执行。

文末自动区块只能在 writer 上、外置盘挂着时重算。2026-08-25 在 Mac reader 上实测：账本口径的数字
与线上一致，但产物表全部退化成「未生成」——那些 CSV 不在 Mac 的 `artifacts` 下。在这种条件下跑
`job_status.py --write` 会把已有行覆盖成空值，看起来像产物丢了。

2026-08-24 脚本审计发现 7 个脚本在仓库内无直接文件名引用，但零引用不能证明已废弃；它们可能是人工运维入口。逐个核对真实调用、产物和替代入口后才删除，禁止批量移动到 `scripts/archive/`。

1. 创作者板的机械识别已做完：`creator-tags-review.csv` 里 42 条 pending 全部产出 candidate（34 candidate、8 skip，见 `creator-tags-candidate-20260817.csv`），没有未覆盖的板。剩下的是用户在 `/review` 页面逐条复核，点「通过」才写 `asset_tag/asset_entity`。注意天花板：全库 7,622 条无标签视频里创作者板最多覆盖约 2,800 条，其余既无创作者也无有效番号（384 个 FC2 + 约 330 个 `WX` 业余码，三源实测零命中）。
2. FC2 评论标记与跨号相似分别在 `/review` 的 `fc2_markings`、`fc2_similarity` 层逐条复核。匿名评论一律不自动升级；库外 video_id 保留 evidence 等待入库。仍未做的是把复核通过的演员写进 `entity`/`asset_entity`，以及由用户决定后执行实际跨号关系写入。
3. 首尾帧出处 P3 已形成最小闭环：`audit_video_endcards.py` 默认拒绝无界全库运行，按 asset/limit 使用 Peach FFmpeg 抽首尾帧，Windows 内置英语 OCR 识别来源 URL、handle 和 `Full version available`，帧/OCR sidecar 可续用，并产候选与健康 CSV；`/review` 的「片尾/出处证据」同时显示证据帧和原视频，批准只记录决定。真实 115 回归 asset `13724` 在 505.607 秒识别出 `Full version available on: fansly.com/smuzililpussy`，两帧 OCR 成功、错误 0，ledger/quality goal/复核决定均不变。未做全库批次，也未把判断自动写成更好版本目标。
4. 继续人工补齐姓名审计留下的 35 位未解析发行女优；这些多为艺名、账号式拼写或上游未收录，现状刻意保留原名，不能为追求“全中文”而猜译。头像仍有 15 位图库未收录、5 位所有候选不过质量门槛；姓名与头像进度不得再互相阻塞。
5. 通过官方/公开来源补齐 86 个厂牌 Logo，保留来源和质量门槛。Logo 与头像的取源方向相反：头像应取整理好的图库，Logo 是品牌标识，官网与维基才是权威来源。
6. Windows writer 执行 PikPak 视觉夜跑：先用 `probe.py --redo all` 重探当前 5,445 条失败/零时长，再只跑官方封套与九帧缩略图。generation 29 的 Mac 副本基线为可直接抽 4,740、需重探 5,445、短于等于 2 秒 11；Windows 起跑前重算。第一晚以 200 GB 流量守卫与 40 GiB 系统盘闸门为硬上限，允许安全中止和续跑，不承诺一夜全量完成。
7. Web 契约层的结构债，按当前实测行数排序，改动前先看清代价：`src/peach/web_contract.py`
   已到 2,414 行（2026-08-23 评审时是 1,980，`web_activity.py`/`web_logic.py` 拆出去之后仍在长），
   `web/app.js` 2,599 行，`src/peach/repository.py` 100 行只包一层数据库边界。拆分方向是按领域切成
   catalog 查询 / stats / activity 写入 / review 状态机 / trash，`web_contract.py` 只留分发门面，
   路由字符串与函数签名不动，现有契约层测试应零修改通过。行数预算由
   `tests/test_context_budget.py` 管入口文件，不管这两个文件，所以只能靠这条记着。

8. HLS `stream-plan` 和按需 TS 片段已接入现有 Video.js 内置 VHS。片段时间窗的绝对终点问题已修并已切生产（见上节）；自适应码率、多路清单、首帧/seek 的桌面与手机验收仍未完成。CloudDrive 约 100 MiB 固定块预取仍是来源层成本，服务端分片只能避免整部 MP4 Range，不会消除来源层块预取。
9. 在真实生产浏览器补做 `/review` 的 1280×720/390×844 最终视觉确认，再人工批准 Windows r18dev 小批候选；确认来源质量后逐个启用 Javinizer 已有 scraper，不新增 Peach 私有站点解析器。
10. 追更接下来三件事，按依赖顺序：(a) **先在 Windows 写入端**备份后 apply 迁移 `0018`
    （`peach migrate upgrade --yes`，无 `--yes` 会拒绝改动真实 ledger），Mac 之后走
    「同步 Ledger」拉取；Mac 只作 reader 浏览时也可以本地先 apply，它换来的只是
    `/follow` 页面能渲染——写入端点在 reader 上照旧 409；
    (b) ~~核对 rule34.xxx 的真实响应~~ **2026-08-26 已完成**：用账号 key 实测，字段名与
    文档一致，但内容推翻了两个按文档写下的判断——`image` 15/15 是哈希、`parent_id` 15/15
    是 0，而 `source` 13/15 有值。分组键因此改为优先取 `source` 归一出的跨站键
    （`fanbox:12304831`，与 kemono 的 post id 同一命名空间），详见 ADR-0019；
    (c) 再接 APScheduler 做定时轮询。媒体下载能力已在设计里留位
    （`media_url` + `media_needs_credential`），但没有实现下载器，也没有定流量与磁盘预算。
    lazyp 的四个来源已在临时库跑通端到端：kemono 50 条、rule34video 24 条、f95 9 条动态，
    折成 74 张作品卡片。AI 结果继续只作为候选。
11. `R:` 本地盘的图片仍未入账：`scripts/ledger.py scan` 本来就按扩展名把图片记成 `medium='image'`，但 `local` 这一路是经 Stash 入库的，Stash 只索引视频，所以 `R:\Media\<名字>\P\...` 这类照片目录一条都没有。等外置盘挂上后先只读列一遍目录规模，再决定扫描批次；扫描写真实 ledger，按 `peach-ledger-write` 单独授权。盘不在时不得凭目录约定推断照片存在与否。
12. Codex 侧封装技能：`.claude/skills/` 下的七个技能目前只有 Claude 会按 description 自动触发，
    Codex 只能靠 `AGENTS.md` 索引表主动读。由 Codex 接手时确认当前版本的技能机制与目录约定，
    封装成 Codex 侧可自动触发的形式并指向同一份 `SKILL.md`；机制不存在或确认不了就写 `未取得`，
    保留索引表回退。规范见 `docs/adr/0015-agent-context-layering.md`。

## 批处理进度（自动生成）

<!-- job-status:start -->

<!-- 由 scripts/job_status.py 生成，勿手改；数字现算于账本与产物 -->
<!-- generated 2026-08-26T05:44Z -->

- 最近自动交接：`claude` / `Stop` / `completed`，2026-08-26T05:23:36+00:00。
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
