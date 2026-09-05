# 抓取复用与复现审计

核验日期：2026-09-05；代码基线：`349048f`。架构方案见 [ADR-0024](adr/0024-mark-manifest-not-bundled-bytes.md)，逐入口结论见 [审计 CSV](scraping-audit.csv)。本次交付是文档与只读取证，不表示抓取服务、GUI 或依赖已升级。

## 范围与结论

扫描 `scripts/harvest_*.py`、`fetch_*.py`、`scrape_*.py`，加上有来源请求的头像审计、厂牌本地化、Babepedia 匹配与链接重发现，共 **17 个业务入口**。同时核对共享 HTTP、页面缓存、图像候选缓存、Javinizer-Go 适配、关注连接器和凭据 GUI。发布检查、连通性验收、纯离线导入／安装脚本不计入业务抓取入口；这个分母不代表 Git 历史中的全部脚本或所有 provider 类。

按每个脚本的最高风险归类，互不重复：

| 分类 | 数量 | 判定含义 |
| --- | --- | --- |
| 外部成熟能力复用缺口 | 2 | Instagram 未完成成熟头像接口验证；域名归属使用自写后缀算法且有反例 |
| 内部基础能力重复 | 5 | 封面、图标、名册、人物链接与厂牌社媒头像各自计算请求节拍，与共享能力并存 |
| 复现／生命周期缺口 | 2 | FC2 Cookie 仅 CLI 接入；官网探测的 client 关闭边界有缺陷 |
| 未发现足以判为重复造轮子的证据 | 8 | 有直接复用、固定上游参考或明确领域差异；不是永久豁免 |

因此当前能够具体指认的复用问题涉及 **7/17 个入口**，另有 2 个入口的复现或运行缺口。不能把「写了 Python 脚本」「使用站点专用选择器」「没有直接依赖整个下载器」都算作错误。

## 复用问题

### 社媒头像：缺的是成熟能力验证

`harvest_social_avatars.py` 声明 Instagram 只记录链接，`harvest_studio_icons.named_avatars` 消费人工提供的 CDN 地址。当前源码和 REUSE 未登记 Instaloader／gallery-dl 头像解析的成功 POC 或拒绝证据，因此不能把局部 `web_profile_info` 429 和页面小图推导成自动解析不可行。

Instaloader 4.15.3 的 `Profile.profile_pic_url` 实现含 `hd_profile_pic_url_info` 与 `profile_pic_url_hd` 分支；gallery-dl 也有 `InstagramAvatarExtractor`，支持 `/USER/avatar/` 与登录／匿名分支。它们都是应比较的成熟能力，但本轮未读取用户 Cookie、未执行登录态跨账号 POC，不能把「已有接口」写成「本机和所有用户均验证成功」。该问题在统计中归入社媒入口，图标入口不重复计数。

用户提供的 Bambi 图片直链与本机 `agency-avatars.json` 的图片文件编号一致；本轮前一阶段不带 Cookie、严格 TLS 请求返回 200、JPEG、1000×1000、92,068 字节，原图 SHA-256 为 `fc004f50edd9a3d684582eacf72b0521883ba42d40307304db062dc0cc931c1f`。文档不保存临时签名 URL。证据仅证明该直链在核验时可下载，不证明所有账号的地址发现成功。

首选验证 Instaloader，不同时加入两套正式 Instagram 运行时。记录 Python／桌面包兼容性、依赖体积、会话导入、限流与账号身份结果后决定采用；GUI 会话导入不是手工维护 CDN URL。

### 链接重发现：自写公共后缀判断有反例

`rediscover_entity_links.registrable` 用末两段／三段域名和固定标签集合判断站点归属。直接执行当前函数：`a.github.io` 与 `b.github.io` 均返回 `github.io`，独立租户因此被 `same_site` 判为同站。`www.t-powers.co.jp` 与 `t-powers.co.jp` 的正例仍通过，单测只覆盖常见日文域名不足以证明通用正确。

采用 PSL 支持的成熟实现前先做小样本 POC；tldextract 为候选，必须开启 private suffix 处理并固定可离线使用的 PSL 快照，不能照搬其默认参数。可注册域相同也不等于实体归属相同，账号页与共享主机路径仍需独立身份核验。

### JAV 封面：重复的是限流基础，不是高清策略

`fetch_jav_covers.HostLimitedTransport` 自持 host→next_request，而 `scripting.HostLimiter` 已有主机匹配、时钟注入和线程锁。应扩展共享限流器的默认主机策略、连接生命周期和预算接口后复用，不能直接替换导致未配置主机不限速。

高清候选聚合本身有充分复用证据：REUSE 已登记 Javinizer-Go 固定 revision 的 DMM 映射和 MDCX 的 Prestige 协议模型。离线快照、严格番号核对、Range 尺寸探测和像素比较属于 Peach 质量策略，保留。

### 厂牌图标：重复取数器需要收口

`harvest_studio_icons.Fetcher` 自行实现连接请求、固定间隔、重试、内存缓存；`page_cache.Site`、共享 HTTP 和来源限流器已有对应基础。它直接 `client.get` 全量读取，也没有统一响应上限。保留一次首页解析产生多个候选、图片判形和候选质量策略；下载、错误分类、字节上限和缓存作用域收口。

`Site` 本身只适合当前公共页面缓存，不能不加作用域和 TTL 就拿来缓存登录资料。统一不是把所有调用生硬塞进现有类，而是在这些已用模块上补齐共用契约。

### 三个入口重复计算请求节拍

`harvest_agency_rosters.Site` 自持 `_last`，`harvest_performer_links.run` 与 `fetch_studio_avatar_candidates.main` 各自持有 `last`，三处均重复「interval 减去 monotonic 时间差，再 sleep」；这正是 `scripting.RateLimiter.wait` 已覆盖的能力。事务所名册、人物页身份和 unavatar 本身的复用成立，不因一个限流重复就重写整个入口。

审计只把独立节拍实现计为重复；来源特有的退避策略、单纯调用 sleep 或小型 HTTP 包装不自动计入。因此 Babepedia 的失败策略留待统一错误语义，而不凭其出现 sleep 就增加重复数量。

## 两个独立缺口

- `fetch_fc2_metadata.py` 已复用 HTTPX 和标准库 `MozillaCookieJar`；评论里的跨号关系与分片判断是领域逻辑，未发现成熟依赖完整覆盖的证据。问题是它的 `--cookies`、网络错误、预算和续跑没有接入 GUI／共享服务，不能因此称其整套解析是在造轮子。
- `harvest_studio_sites.probe` 创建 `HttpxTransport(crawler_client())`，finally 调 `http.close()`；共享 `HttpxTransport` 对注入 client 设置 `_owns_client=False`，因此这次 close 不会关闭实际 client，调用者又未关闭它。当前实现不能保证每个请求立即释放连接。先修正所有权并复测原失败序列，再判断是否需要每请求独立 client；不能依据现有文字断言 HTTPX 池会必然泄漏。

## 已有复用与历史证据

- `scrape_codes.py` 调 `JavinizerGoProvider`，由外部 Javinizer-Go v1.5.1 查询，Peach 只做身份、字段候选、来源健康和复核。不是自研整套 JAV scraper。
- `fetch_studio_avatar_candidates.py` 使用 unavatar 解析地址、平台 CDN 下载及 `LogoCandidateCache`。公共服务是可变化依赖，需要无 API key 可用性与服务失败测试；本轮没有把它认定为长期免费保证。
- Gfriends 索引与头像审计复用原始索引、Pillow 和 `AvatarCandidateCache`；目录名录／本地化入口复用 `page_cache.Site`、`minnano_av`、`javdb`、名字链和 OpenCC。事务所名册的同名 `Site` 是脚本自有类，计入上面的内部重复。身份消歧仍需 Peach 承担。
- FANBOX 已使用 curl_cffi 和 PixivUtil2 固定正文模型；Rule34Video 已部分使用 yt-dlp；其余归档／booru 官方接口及 Gofile 边界已在 REUSE 登记。这里只核对复用入口，不把本轮审计当成所有在线 provider 的端到端验收。
- Git 中可指认的基础收口包括 `80b04d2`（UA／主机限流）、`053aed5`（番号归一化）、`c374601`（CSV）、`bdeddbc`（头像档位）。存在历史重复与后续收口证据，但不能把已删除实现重复算进当前 17 个入口。 <!-- copy-lint-disable-line -->

## 无代理刮削的实际机制

Javinizer-Go v1.5.1 示例配置默认启用 r18dev，使用面向刮削器的 JSON 与专用 UA；支持按来源代理、CDN Referer、缓存和 r18 dump。**可用的聚合数据／本地缓存可以减少访问每个原站，不会让被阻断的原站凭空可达。** dump 需要先取得，缓存中的封面 URL 与原图字节也是两种资源。Peach 目前未证明已经接入其 dump 管理。

Movie Data Capture 的当前配置提供代理开关、超时／重试、来源优先级和仅补缺图；这些是选源与缓存策略，不是任意地区无代理可达的保证。本次只用其配置作行为对照，不把整个应用加入 Peach。上游绕过验证的可选分支不在 Peach 采用范围内。

高清与代理没有必然关系。对维护者来说，多问几个高清源增加了遇到地域或网络限制的机会；普通用户可以先用可达源填齐。即使需要代理，也应由来源连接诊断决定，不能降低已能直接取得的高清图。

### 本机小样本

主机权限下执行公开请求，每个目标每条路线一次，传输失败重试一次，严格 TLS，最多读取 64 KiB，不带 Cookie、不写 ledger。图片尺寸取自真实图片头，未用 URL 字样推断，也未将这次头部探测当作整图完整性校验。

| 目标 | 不使用应用环境代理 | 使用当前环境代理 | 已测图片尺寸 |
| --- | --- | --- | --- |
| r18.dev：ABW-232 JSON | ConnectError，2 次 | 403 HTML，1 次 | 未取得元数据 |
| DMM mono：ABW-232 | 200，1 次 | 200，1 次 | 800×539 |
| DMM 高清：GYAN-017 | 206，1 次 | 206，1 次 | 2184×1464 |
| Prestige：ABW-232 图片 | ConnectTimeout，2 次 | 206，1 次 | 1024×690 |

进程存在 HTTP_PROXY／HTTPS_PROXY／ALL_PROXY，但不输出其值。沙箱中的无代理请求均连接失败，故以主机权限复测结果作为上表依据；这仍未排除 TUN 或上游路由。FlowLens 的出口证据未取得，不能称「物理无代理」。r18 使用的是有界通用 UA HTTP 探测，未取得 Javinizer-Go 专用 UA／dump 的等价现场结果，不据此宣称其 provider 不可用。

本机取证脚本和脱敏 JSON 位于 `attic/evidence/20260905-scraping-reproducibility/`，不进入发行版。实际网络结果只适用于该时刻和主机，不能外推到中国大陆、台湾或其他地区的所有用户。

## 新用户复现差距

| 能力 | 当前源码 | ADR-0024 要求 |
| --- | --- | --- |
| Cookie GUI 粘贴／撤销 | `/follow-manage` 已有表单；写入运行 Peach 的主机；GET 只返回状态 | 共用该存储与接口扩展来源，避免第二套密钥文件格式 |
| Cookie 有效性 | 已配置主要是字段存在性 | 保存与有效分开；独立有界验证、过期和需验证状态 |
| Cookie 文件导入 | FC2 CLI 使用 Netscape 文件 | GUI 域限制导入、说明会话位置；不接受不可信 pickle |
| 浏览器直接导入 | 未发现统一 GUI | 经用户选择后调用成熟库；平台不支持则文件／粘贴回退 |
| 网络选项 | `Site.via_proxy`、HTTPX 环境、CLI 子进程等多条路径 | 按来源明确网络模式，各 transport 与子进程一致 |
| 高清模式 | 封面脚本有 Range 和全候选比较，图标有够用线 | 标准与最高可得画质独立选择；共享候选、预算和缓存 |
| 工具安装 | `resolve_javinizer_binary` 查版本固定目录、环境变量或 PATH | 干净机器 GUI 诊断依赖并安装经校验的平台制品，失败保留公开来源 |
| 一次性映射／日志 | 部分路径依赖本机候选 CSV、人工 handle 和成功 URL | 导出可公开来源定位与身份线索，缺失可从原站重新发现 |

实施顺序：连接生命周期与归属正确性 → 共用网络／缓存／预算 → GUI 配置与依赖诊断 → Instagram POC → 清单导出和干净机器验收。不得先批量引入新依赖或重写全部站点解析器。

## 外部核验入口

- [Javinizer-Go v1.5.1 配置](https://github.com/javinizer/javinizer-go/blob/v1.5.1/configs/config.yaml.example)：来源、代理与 CDN Referer；固定 revision 的高清差异见 REUSE。
- [Instaloader 4.15.3 头像实现](https://github.com/instaloader/instaloader/blob/v4.15.3/instaloader/structures.py)、[安装依赖](https://github.com/instaloader/instaloader/blob/v4.15.3/setup.py)、[MIT 许可证](https://github.com/instaloader/instaloader/blob/v4.15.3/LICENSE)、[会话导入](https://instaloader.github.io/cli-options.html#login-download-private-profiles)、[429 限制](https://instaloader.github.io/troubleshooting.html)。
- [gallery-dl Instagram 提取器](https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/instagram.py)：GPL-2.0，对照源码，未复制或引入；采用前锁定 revision 与真实输入验证。
- [Movie Data Capture 配置](https://github.com/mvdctop/Movie_Data_Capture/blob/master/config.ini)：只作策略对照，不作为安装推荐或当前站点可达性证据。
- [HTTPX 环境变量](https://www.python-httpx.org/environment_variables/)、[代理](https://www.python-httpx.org/advanced/proxies/)：环境和显式代理的语义。
- [Public Suffix List](https://publicsuffix.org/list/)、[tldextract](https://github.com/john-kurkowski/tldextract)：域归属候选；含 private suffix 的 POC 与固定版本验收仍需实施。
