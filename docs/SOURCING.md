# 身份、来源与标识采集

## 采集判据

本文件保存「从外部站点取得身份与标识」这件事的判据细节：脚本分工、实测反例、判词含义和不能走的路。
采集本身的限流、续跑与流量预算见 `.claude/skills/peach-batch-jobs/SKILL.md`，
参考产品证据的登记方式见 `.claude/skills/peach-reference-evidence/SKILL.md`。

采集脚本一律只产出复核 CSV。写 `entity.canonical_name`、`asset.studio`、`entity_link` 或头像字节
都是另一次授权，判据见 `.claude/skills/peach-ledger-write/SKILL.md`。

**没有哪个来源是绝对的**，javdb、laoshi、jae、R18 都只是参考，各带自己的可信度：资料页的名字
可能是转载渠道改过的。同一条事实由两个互不相干的来源给出才是最强的证据，只有一个来源说的一律
当候选；冲突时不按站名分高低，按这条事实本身还能不能另找一个来源印证：已经进账本的那一侧
也不例外，它当初也只是某个来源的一次判定。

具体的例子：**判 X 账号是不是本人官方号，粉丝量是第一道筛子。** 官方号的粉丝量不会太少，
`matumoto_arrows` 这种数量级明显偏低的就该疑。2026-09-04 实测两例：松本一香账本里的
`MatuMoto_Ich1ka` 才是官方，javdb 给的 `matumoto_arrows` 驳回；铃村爱里反过来，javdb 给的
`airi_mgr` 在活、账本原有的 `naxsuzumura` 已疑似失效，按 javdb 那条装入。冲突不能一刀切成
「以账本为准」或「以新来源为准」。

## Seesaa Wiki 作品证据

`scripts/scrape_codes.py --profile seesaa` 使用素人系総合 Wiki 的公开搜索与作品表格，产出既有
`metadata-field-candidates` CSV。可通过 `--wiki-pages-file` 预取目录页；页内全部作品复用同一次请求，
`--wiki-max-requests` 默认 80，每次最多 4 MiB、请求间隔至少 2 秒。成功页缓存可续跑，
`--refresh` 重取页面；403、429 与机器人验证停止本批联网，未取得不冻结成永久无结果。

番号通过作品表的 `NO` 列精确回配，支持既有数字前缀／补零规范化。`ACTRESS` 的链接显示名是
出演候选，链接目标只保留为身份核验线索；EUC-JP 页面按来源编码解码。含未知出演者的名单仅留
原文证据；冲突行报告错误。`TITLE`、`RELEASE` 可出标题／日期候选；`SUBTITLE` 不冒充完整标题。
封面 URL、人物页链接、备注和跨平台编号保留在原始快照及候选证据中，不下载图片、不自动合并人物或作品。

Seesaa 是托管平台，以下 Wiki 由各自维护者编辑，不能按平台名当成互相独立的印证：

| 来源 | 已核验的用途 |
| --- | --- |
| [素人系総合 Wiki](https://seesaawiki.jp/w/sougouwiki/) | 厂牌作品表、合集名单、名义与人物页链接、日期、图片及跨平台线索；已接入脚本 |
| [このAV女優の名前教えてwiki](https://seesaawiki.jp/av_neme/) | DMM、MGS、S-Cute、舞ワイフ出演名义核验 |
| [AV女優大辞典wiki](https://av-help.memo.wiki/) | 女优与出演作品索引 |
| [AV女優の名前特定wiki](https://seesaawiki.jp/av_name/) | FANZA 素人作品番号与出演者对应 |
| [AV女優パーフェクトWiki](https://seesaawiki.jp/av_video/) | 作品、厂牌、系列索引及出演者线索 |
| [シロウトTV・ナンパTV](https://seesaawiki.jp/pre_shiro/) | MGS 相关作品的出演名义核验 |
| [人妻系まとめ](https://hitoduma-matome.memo.wiki/)／[素人AV女優名鑑](https://shiroutoav.memo.wiki/) | 特定类别人物与作品线索 |
| [VR作品](https://seesaawiki.jp/vr_video/)／[成人映画](https://seesaawiki.jp/nikkatsu/)／[NHpedia](https://seesaawiki.jp/nhpedia/) | VR、成人电影、跨性别演员等分领域索引 |

表内入口取页于 2026-09-06。平台首页的游戏、小说、生成模型教程和场所服务 Wiki
不适用于现有视频作品元数据补全。

## K-MIB 官网作品与演员

韩国 MIB 的番号问 JAV 目录站必错，官网 [k-mib.com](https://www.k-mib.com/) 是唯一可信来源。
`scripts/harvest_kmib.py` 解析 `peach-data/sources/k-mib/` 下的快照（列表页、`video/<idx>.html`、
`star/<idx>.html`、`images/`），解析器在 `peach.metadata_kmib`。

- `--fetch` 联网补快照：同主机间隔 1.5 秒，已有的跳过，403、429 立即停止本批。robots.txt 只挡
  `/_adm/` 与登录页。
- 缺省只读，写 `kmib-catalog.csv`（全站作品与账本对照，官网没有的账本番号记「未取得」）、
  `kmib-performers.csv` 与 `kmib-metadata-field-candidates.csv`。
- `--apply` 先备份 ledger，再补空番号、按 ADR-0018 自动批准官网候选、装缺失封面，给已关联
  MIB 作品的演员装官网资料页链接和头像，给 MIB 装官网链接和 logo。候选的 item_key 带 `:kmib`
  后缀：这批番号的 `<番号>:<字段>` 已被 JAV 错配候选的拒绝决定占用。
- 合作厂牌（JS MEDIA、Studio REAL、SETFLIX、PEEKO、MMP、JO GLOBAL）的 Actor 栏常写厂牌名，
  按厂牌名与番号前缀记为 maker；这些前缀不属于 `KOREAN_MIB_PREFIXES`。
- 分类只投影到已有词表。Fetish、Kiss、Sex Toy、Ahegao、Tiny Girl、Oil、Femdom 作为未收录
  提示随候选进复核。
- 双词罗马音艺名（`Mao Hamasaki`、`Sarina Momonaga`）过不了艺名形态门槛，由人工复核；
  后者按别名对到 `藤木真央`，身份待确认。

## 哪些行不该进 JAV 刮削

库内采集拿去问 JAV 来源之前过一道 `catalog_rules.scrapes_as_jav`，它只拦一种：**创作者作品的
文件名被读成了番号**。`sumwall95 masturbation_1.mp4` 出 `SUMWALL-095`、`aerith 2412a.mp4`
（角色名加年月）出 `AERITH-2412`，形态上和厂牌番号毫无区别，`is_jav_code` 一律认。判据是
「归在某个创作者名下、没有厂牌也没有其他发行证据、写法又不属于任何发行体系」；FC2 商品号、
素人平台的三位数字前缀、MGStage 的 `STP`／`SIRO`、日期式番号一概放行，创作者的文件名撞不出
这几种形状。2026-09-22 只读盘点：账本 2851 部有番号的资产里这样的 126 部（`oscarkim123` 的
cosplay 105 部、`sunwall` 的剪辑 19 部），真番号零误伤；同一天那轮失败清单 778 部里正好这 126 部。

**不要改用 `is_jav_asset`。** 那个判「算不算一部已坐实的 JAV 发行物」，要求发行证据先落库，
用来决定浏览时归到哪一类。刮削入口用它会死锁：证据本来就是刮回来的，没刮过就没证据。
同一份盘点里它会把 `300NTK-625`、`300MIUM-698`、`476MLA-179` 这些真素人番号一起关在门外。

## 按内容类型的来源链

过了上面那道门之后，问谁、什么顺序、何时停，由 `peach.metadata_routes` 一张表决定。
它只管**查询侧**；取回来的值怎么排序、分歧听谁的在 `peach.metadata_policy` 与落库那一侧，
两条轴不要混。最直观的例子是 javbus：结算上它是备选来源（ADR-0035），查询上却排在 javdb
前面，因为 javdb 按出口 IP 计配额、主机间隔单独设（见下文），先问便宜的两家不影响结算，只影响谁先撞限流。

类型只看番号形状与本机证据（路径、文件名、账本厂牌），不等元数据到齐：一旦改成「先拿到
元数据再判断」，没有元数据的番号就永远轮不到该问的那家。

| 类型 | 判据 | 链（从左到右） | 这条链为什么不含 |
| --- | --- | --- | --- |
| censored | 其余厂牌番号 | （本机证据认得时）prestige／faleno／dahlia，都不认时 makers → r18dev → avbase → javbus → javdb | 1pondo（无码片商）、fc2（另一套商品号）、mgstage（对有码号是转售店） |
| amateur | `300MIUM-1239` 这类三位数字前缀，加 `SIRO`／`STP`／`STN` | mgstage → r18dev → avbase → javbus → javdb | makers 与三家片商站（素人号不归它们） |
| uncensored | 日期式番号、`HEYZO-1380`、Tokyo-Hot 的 `n0780` | （证据指着一本道时）1pondo → avbase → javbus → javdb → avsox | r18dev：无码番号在它上面没有 |
| fc2 | `FC2` 开头的商品号 | fc2 → fc2cmadb → javarchive → fc2club → javdb | r18dev（实测 85 条全空）、avbase 与 javbus（对 FC2 零产出） |
| kmib | `KOREAN_MIB_PREFIXES` 里的前缀 | 一家都不问 | 全部：番号与日本片同形，问回来的是别的作品 |

几处容易问错的地方：

- **`ABF`／`ABW`／`ABP` 是有码不是素人。** mgstage 首页同时挂有码号与素人号，按站点归类
  会把整个 Prestige 判成素人。素人只认三位数字前缀与 MGS 那三个字母前缀。
- **一本道要本机证据。** 日期式番号本身不带片商，一本道与カリビアンコム 同形，问错那家
  答回来的是同一天发行的另一部片。指不着就直接落到综合索引。
- **三家片商站只问自家番号。** Prestige、FALENO、DAHLIA 对任何番号都发请求，番号字母前缀在
  `metadata_routes.MAKER_EVIDENCE` 里、或账本厂牌与路径写着这家才问它；有一家认了就不再问 `makers`。
  `makers` 按 amane 自带的片商表路由，前缀不在表里桥内零 HTTP，只花一次子进程（实测 0.8 秒）。
- **国产、欧美、里番没有链。** Peach 一家对应来源都没接，写一条空链只会让人以为问过了。

何时停：官方与发行方那几家逐个成档，一档把**这一行还缺的必填标量**（标题、演员、厂牌、
发行日期）给全了就不问下一档；只给了一半照旧往下问，否则那一行只能等人工去填。综合索引
那一档整档一起问，不逐家短路，因为免复核要两家取值一致（ADR-0030、ADR-0034），封面互证要两个
不同图源（ADR-0032），问到第一家就停等于把这两条判据的样本降到下限。这一行要的本来就只有
标签或封面时，第一家给了就停（ADR-0033）。例外只有一条：FALENO、DAHLIA 官网不给类别，缺标签的行
在片商站答完标量后再问一次 r18.dev；下一档是综合索引就照样停。

上一趟存下的原始快照（`<数据根>/sources/library-metadata/<番号>-<来源>.json`）还新鲜就
直接用，不发请求。有效期与「说过没有」的记忆同一个（7 天），两边同时到期才不会出现
「没有」已经过期、「有」还压着旧值；「重试未完成项」要的就是新答复，强制重问。

用户可以整条替换某个类型的链：`process_library(route_overrides='censored=r18dev,javdb')`，
文本写法是 `类型=来源,来源`，分号隔开多条，也接受同形状的映射。替换是整条替换不是逐项
合并：逐项合并的表现是「删不掉一家」，想摘掉 javdb 得先知道内建表里有它。类型名或来源名
写错直接报错：静默忽略的表现是「设置改了没生效」，比报错难查得多。

来源链的取舍参考了 amane 的 `docs/dev/content-routes.md`，证据登记在
`docs/reference-sources.json` 的 `amane-content-routes`。

fc2club、avsox 两站（以及只能由覆盖点名的 freejavbt、airav）不是 Peach 自己的解析器，
由 amane 经 `tools/amane-bridge/` 的子进程回答（ADR-0043）：链上它们合成一档 `amane`，一次子进程
并发问完；上游报的 `rate_limited` 按 429 那一档、`cloudflare_*` 与 `ip_banned` 按 403 那一档写进
同一份冷却记录，正在冷却的站不带进子进程。桥的 venv 在「来源和凭证」页那张卡重建，钉住的版本
只由人改。2026-09-22 经代理实测：`HEYZO-1380` 经 avsox 7.3 秒走完桥 → 链 → 候选，标题、演员、
厂牌、发行日与标签齐全；fc2club 对 `FC2-PPV-4610638`／`1015014`／`3143302` 都说没有，freejavbt
对有码番号说没有，airav 的搜索地址当天回 404。记录在 `build/agent-verification/amane-chain-realtest.json`。
fc2ppvdb 不在链上：同日对三个商品号都回 HTTP 526（站方证书问题），用户判定该站已不可访问（ADR-0043 修订）。

有码与素人链的官方档第一家也经桥（ADR-0048，每个站只有一个归属）：`makers`（amane 的 `official`，二十九家
片商官网）、`prestige`、`faleno`、`dahlia`、`mgstage` 合成一档 `amane_official`，分级是 official，结算上片商站
排在 dmm 与 r18.dev 之前。Prestige 回的日期是 MGS 配信开始日（ABW-032 答 2020-11-11，发行日 2020-12-11），
只记在 `extra['delivery_date']`，发行日留给 r18.dev。地区限制与站方裸回的 401/403 都算「被挡」：归 `auth` 一档、
整站按 403 那一档冷却，不冻进「没有」的记忆。2026-09-23 经代理实测五站都取到自家番号，
dmm、giga、kin8 不进链，理由与数据见 ADR-0048 与 `build/agent-verification/amane-official-stage.md`。

## 站点解析器契约

自写解析器与 amane 桥的站套同一个形状（`src/peach/sources/`，ADR-0044「实施：解析器契约」）：
一个站一个类，`fetch(code, session=)` 取到作品页、`parse(page, code)` 读出记录、`query()` 串起来；
站名、主域与图床、请求间隔、是否带 Cookie、页面上限与档位全在 `SiteConfig` 里，是数据不是常量；
返回只有一种 `SiteRecord`，`payload()` 投影成来源快照那份 dict，候选、来源链结算、封面层与账本
读到的东西不变；失败只有一张 `FailureReason` 表（十二档），`REASON_KINDS` 把它映到
`MetadataProviderError` 的 `auth` / `unavailable` / `not_found` 三档，`COOLDOWN_ACTIONS` 说哪几档要把
整站写进 `scraping_access` 的冷却记录（`cloudflare_challenge`、`ip_banned`、`geo_restricted` 按 403 那一档翻倍，
`rate_limited` 按 429 那一档）。冷却期（`SourcePaused`）、动作预算与连接失败由传输层抛出，契约原样放过，
所以按站的限流与封禁表现由传输层一处决定。配置与 `SOURCE_SPECS`、`SOURCE_LABELS`、`PROVIDER_NAMES`、
`scraping_access.SOURCES`、`SOURCE_INTERVALS` 里同一站的那几行由 `tests/test_metadata_sources.py` 守住一致。

下表各站全部已套契约：自写的九站登记在 `sources.SITE_SOURCES`，经桥的九站在 `metadata_amane`。

| 站 | 状态 | 位置 | 说明 |
| --- | --- | --- | --- |
| JavBus | 已套契约 | `sources/javbus.py` | 年龄门归 `auth_required`；404 与番号对不上归 `not_found` |
| javdb | 已套契约 | `sources/javdb.py` | 搜索页与详情页两跳都在 `fetch` 里；登录页归 `auth_required`，详情页番号与搜索结果不一致归 `parse_error`；主机间隔 3 秒进配置 |
| fc2club、freejavbt、airav、avsox | 已套契约（经桥） | `metadata_amane.py` | amane 的十六档 reason 经 `AMANE_REASONS` 一对一翻成契约细档，桥的一站先套进 `SiteRecord` 再投影；`SITE_CONFIGS` 只持有站名、界面名与档位，主域与 Cookie 由 amane 管 |
| makers、prestige、faleno、dahlia、mgstage | 已套契约（经桥） | `metadata_amane.py` | 档位 `official`（`OFFICIAL_SITES`）；`http_error` 带 401/403 经 `contract_reason` 归 `auth_required`；prestige 的 `release` 进 `extra['delivery_date']` |
| AVBase | 已套契约 | `sources/avbase.py` | 搜索页一跳，`__NEXT_DATA__` 里挑出本作与它自己的商品条目；搜索无命中归 `not_found`，Cloudflare 验证页归 `cloudflare_challenge`，别的结构对不上归 `parse_error`；不给时长，`runtime` 留空 |
| r18.dev | 已套契约 | `sources/r18dev.py` | 作品 JSON 与 combined 页两跳，日文写法、女优头像模板与 genre 取日文原词都在这一站里；`content_id` 对不上归 `parse_error`；档位 `official_mirror`，页面上限 2 MiB |
| 一本道 | 已套契约 | `sources/onepondo.py` | 作品 JSON 一跳；认不出作品号、404 与 `MovieID` 对不上归 `not_found`，回的不是 JSON 归 `parse_error`；档位 `official`，页面上限 1 MiB 进配置 |
| FC2 | 已套契约 | `sources/fc2.py` | 商品页一跳，下架页与 `sku` 对不上归 `not_found`；番号、时长、原件地址与占位件判定是三站共用的函数，也在这里；页面上限 2 MiB |
| fc2cmadb | 已套契约 | `sources/fc2cmadb.py` | 作品页之后在 `query()` 里带握手头点名 `actresses` 再问一跳，那一跳失败按没有女优交回；评论区的演员、等价与合集解析也在这里，`scripts/fetch_fc2_metadata.py` 从这里取 |
| JavArchive | 已套契约 | `sources/javarchive.py` | 搜索页加作品页两跳；`records()` 把搜索命中的每一条转存各交一份记录，某一条 404 或对不上就跳过 |
| Seesaa 作品表 | 已套契约 | `sources/seesaa.py` | 只由 `scrape_codes --profile seesaa` 或 `--sources sougouwiki` 点名，provenance 是 `sougouwiki`；`rows()` 把一页作品表的每一行各读成一份记录，读过的表记在实例里供后面的番号先找；会话的传输是 `WikiPages`（页缓存、本批请求限额、撞墙停网），不在 `scraping_access.SOURCES` 里；失败沿用 `budget`、`blocked`、`ambiguous`、`incomplete_search` 等分档，不折成三档：它们落进批处理的错误表与健康表，`budget` 与 403/429 还决定本批停网 |

FC2 三站先后问、资料取齐即停、封面问到底的流程仍在 `LibraryMetadataProvider.fc2`，按 `metadata_routes.FC2_STAGE`
逐站调 `records()`；各站只管自己的取页与解析。

## FC2 作品资料与封面

FC2 不是 JAV：番号是卖家自己的投稿号，JAV 目录站按它去查要么没有、要么撞上别的片。实测
r18.dev 对 85 个 FC2 番号全空，AVBase 与 JavBus 对本地这批一律「没有这个番号」，javdb 收了
一部分但配额紧。库内采集（`peach.library_processing`）对 FC2 番号因此只问下面三处，解析器在
`peach.sources.fc2`、`peach.sources.fc2cmadb` 与 `peach.sources.javarchive`，都不要凭据：

- 发行方自己那一页 `adult.contents.fc2.com/article/<video_id>/`，资料在 `ld+json` 的 Product
  里，一次请求给标题、说明、卖家、商品标签、时长、販売日和封面原图（实测 2350×2352）。
  核 `sku`：站上的商品号会被复用给别的投稿。
- 下架的商品页仍回 200 且不再带 Product，这不是抓取失败。接着问镜像站
  `fc2cmadb.com/articles/<video_id>`（Laravel + Inertia，props 树在 `application/json` 里），
  它留着下架作品的同一批字段（`FC2-PPV-3189161` 实测取回 3456×1942 的原图）。标题与标签由
  站方用户维护，按社区来源登记，取值进复核。女優那一栏在浏览器里只对登录用户显示，采集带上
  「来源和凭证」里配的登录 Cookie；游客补问这一栏眼下也回（2026-09-23 实测 `2851534`、`3518061`）。
  官方商品页没有演员栏，所以官方页答上而这一行还缺演员时，也接着问镜像要这一栏。
- 镜像也没有的落到 JavArchive。它的作品地址里夹着站内文章号和标题（`/926949-FC2-PPV-4137487-…-pn.html`），
  拼不出来，所以先问 `/search?q=<番号>` 再取那一条作品页；商品号按数字边界比，`4137487` 不能
  命中 `41374870`。搜索结果只有标题和一张缩略图，作品页才有标签、发行日、时长和封面位，所以这一跳
  省不得。这一档给标题、封面，以及正文那块资料里转存者填了的标签、発行日与时长：填不填是他的自由，
  2026-09-22 实测 4 部里只有 `4030617` 是齐的（10 个标签、2023/11/21、50:03），另外三部整块空着。
  卖家和商品说明站上没有，正文余下几段是转载来的网盘链接，一概不取；演员一栏也没有。
  封面在 `img.javstore.net` 上，**认位置不认文件名**：`div.fisrst_sc` 里那张排前、schema.org 的
  `image` 排后。转存者的命名没有统一：`4137487pl.jpg` 沿用 FC2 自己的 `pl`/`ps`，`FC2PPV-4030617.jpg`
  与 `FC2PPV835964-2.jpg` 是他自己起的，按名字认的话 4 部里 3 部一张都取不到。`_s.jpg` 结尾的排除，
  那是正文里标着 `Preview` 的多帧长条拼图。`FC2-PPV-4137487` 在 fc2cmadb 是 404、这里有，封面比官方
  原图差一档，所以排在最后。`robots.txt` 全站放行。文件名不用来认，只用来否：名字里五到七位的
  独立数字段都不是本番号时，那是别的作品的图（`FC2-PPV-1512205` 与 `1931440` 都取到过 `2184960PL.gif`，
  本机共 10 张），`is_cross_product_cover` 按这条拦。那里存的 GIF 多是预览动画，官方档的
  `best_cover` 与社区档的 `picture()` 下完整张后一律不收，卡片封面只要静态图。
- 同一个商品站上常有好几条，不同转存者各发一次，文章号、番号写法、标题和图都各不相同，先后没有
  质量含义。搜索命中的每一条都取：第一条那张未必还在（2026-09-22 实测 `1436028` 的 `/641159-` 是
  404，`/800025-` 上有 1280×720）。走到这一档时前两处已经都说没有，多那一两页换的是这个番号有没有
  封面。地址里的标题有的已经是 `%e3%80%90` 这种编码、有的是原字，拼之前统一编一遍。

资料那一步答上就停，封面那一步把链问到底。给出地址的那一档常常下不来图：站上标着没有商品图，
或者地址还在、FC2 的存储上那张已经删了，而这一层判不出来，能不能用要等 `best_cover` 量过才知道
（2026-09-22 实测 `FC2-PPV-3232110` 从 fc2cmadb 拿到的地址是 404，JavArchive 上另有一张
1417×829）。所以封面要的是链上全部图源，由它择优；资料那步问过的档不再问第二遍，多问那一档
顺带多一批标签（ADR-0030）。

前两处的封面都指向 `storage*.contents.fc2.com` 上卖家自己传的那个文件，所以按官方图对待，不走
社区来源的两图源印证（ADR-0030）。镜像有时给的是 `contents-thumbnail*.fc2.com/w276/` 包装过的
地址，解析器把包装拆掉取原件；站上没有商品图的条目它挂的是自己那张 `no-image.jpg` 占位件，还是
个站内相对地址，当封面交下去只会换来一句「来源连接未取得」，所以解析时就判成没有图（2026-09-22
实测 21 个取不到封面的番号里有 15 个是它）。

演员只有镜像站给。官方商品页和 JavArchive 都没有演员栏，标题里的名字是卖家写的宣传语。镜像
那一栏是 Inertia 的延迟 prop，首屏 HTML 里没有，要带上这一页自报的握手版本号点名 `actresses`
把它单独再问一次（约 1 KB；2026-09-22 实测 `4030617`、`2110084`、`835964` 三处都有人）。响应里
另附一串曾用名，只取正名：一位女优挂着十几个别名，摊进演员栏就成了十几个人。评论区那条线走
`scripts/fetch_fc2_metadata.py`，另有等价标记与合集判定。带分段后缀的番号
（`FC2-PPV-3312576-1`）认不出商品号，一处都不问：合集封面套给每一段，就是 21 个不同内容顶着
同一张图。

演员栏上镜像排在 javdb 前面（`metadata_policy.FIELD_SOURCE_PRIORITY`）：javdb 那一侧常是转载站
起的称呼，`FC2-PPV-1449453` 它写 `Chisa`、镜像写 `大村阿美香`，`2629971` 它写中文 `安娜`、镜像写
原名 `あんな`。账本里已有的演员社区来源换不动，两边不一的由 `scripts/fc2_cast_review.py` 列进
`generated/fc2-cast-candidates.csv`，在复核页「资料字段」里逐条批。freejavbt 不进这条链：它改版
后 amane 的解析器认不出作品页，而作品页上演员那一栏写的是「暫無女優資料」（2026-09-23 实测
`3518061`、`3910812`、`4137487`）。

## 一本道作品资料与封面

无码番号在 r18.dev 上没有，目录站给日期式番号的发行日是转售商的上架日（`092415_001` javdb 报
2016-06-16，而番号自己写着 2015-09-24）。一本道的前端读的就是一份公开 JSON，不用解析 HTML、
不要凭据：`www.1pondo.tv/dyn/phpauto/movie_details/movie_id/<id>.json`，一次给标题、说明、
女优（日文与罗马字）、系列、发行日、时长和站内标签。解析器在 `peach.sources.onepondo`，
下架的作品直接 404，落到社区来源（javdb 收了一部分）。

**问哪一家由本机证据决定。** 一本道与カリビアンコム 都按 `MMDDYY_nnn` 编号，番号本身分不出
是谁家的；分隔符是压制组的文件名带进来的，不是片商标识。所以只在这一行的路径、文件名或账本
厂牌里出现 `1pon`／`一本道` 时才问官网，否则照旧走 r18.dev 与社区来源。2026-09-21 实测：本机
4 个カリビアンコム 番号在一本道全部 404，8 个一本道番号全部命中，`071213_625` 官网已下架。

封面只有站点自己那张 16:9 剧照（`str.jpg`，实测 960×540）。无码片商不出封套，`thum_b.jpg` 是
120×197 的列表缩略图；两张都不是 JAV 那种竖版封面，取大的那张，按官方图对待。

## 本机采集入口

GUI 与 `scripts/fetch_jav_covers.py` 共用 `peach.jav_cover_fetch`；不需要把开发者的映射文件或
Cookie 复制到新用户电脑。已有成功元数据快照优先，缺快照的公开来源可联网查询。

- R18、DMM、Prestige、MGStage 的封面 HTTP 路径使用按来源的系统代理／应用直连／自定义代理配置。
  DMM 连接检查分别报告页面与高清 CDN；HTTPX 环境代理不等于系统 PAC，应用直连也不能排除 TUN。
- 收 Cookie 的来源（JavDB、JavBus、FC2CMADB、Instagram）其粘贴与 Netscape 文件导入复用 CredentialStore；
  仅保存当前来源域内未过期项目。保存动作本身不校验登录会话是否有效。
- GUI 封面任务每次只接受馆藏命中的一个番号，复用 BackgroundJob；最多 80 个请求、32 MiB，
  请求发出前检查 180 秒截止时间。只在完整图与探测尺寸相同、可完整解码且面积更大时原子替换。
  原始字节不降采样；成功边车记录原图与安装摘要，24 小时内摘要匹配则不重复下载。
- 429 的 Retry-After 冷却落本机文件，新 transport 也遵守；失败不删除已有封面。
  程序重启不自动重放写入任务，未完成任务由用户重新发起。

该配置覆盖封面 HTTP 与 FC2 CLI。amane 桥子进程、其它采集脚本与 curl_cffi 连接器
各用自己的配置。Instagram 的 Instaloader 匿名 POC 对 Bambi、LINX 返回 ConnectionException；
独立用户登录会话未取得。自动适配器不进入正式依赖。

测试步骤见 [Windows 测试版](TESTING_DESKTOP.md)，架构完整要求见
[ADR-0024](adr/0024-mark-manifest-not-bundled-bytes.md)。

即时 r18 厂牌证据与本机快照使用同一来源路由，Prestige 与 MGS 都参加候选比较；
原始图片没有派生降采样。

## 无番号视频的联网识别

`scripts/scrape_codes.py` 只认番号；没有番号的视频（`B:\xxr`、PikPak 里的推特与
Telegram 资源）走 `scripts/identify_resources.py` 的两段式流程，识别结果仍进
`/review` 的「资料字段」，批准才写真相字段：

1. `worklist` 只读账本，按文件名生成搜索写法（原样名、摘推广头尾、分隔符换空格、
   无空格英文按大小写拆词、剥尾部画质标签）并标出同目录配套图片，可直接作海报；
   `metadata_hits` 数出创作者／标题／厂牌／系列／演员里已有几项，默认把少的排前面，
   `--sparse-only` 只留一项都没有的条目，识别优先做这些；
2. 智能体或人联网核对后按 `asset_id,field,value,source_url,confidence,note` 填回 CSV；
3. `ingest` 合并进 `generated/library-metadata-field-candidates.csv`，候选来源
   `websearch`、`asset_path` 钉住具体文件，无番号资产的复核与落库靠这条路径。

字段限于 title／original_title／performers／studio／series／release_date；有番号的
视频仍走 `scrape_codes.py` 的 JAV 来源。网页搜索在智能体侧执行，脚本不发请求、
不写账本。2026-09-10 对 `B:\xxr\0208 (23)\梓怡-…mp4` 的只读 POC 取得标题
「背着老公和合租室友的狂欢」、女优「梓怡」、厂牌「麻豆传媒」，来源 madou.io 与
av911.tv，三条候选已进复核队列。

## 命名与身份合并

- 规范名优先用有出处的简体中文通行名，暂无可靠中译时保留日文；旧艺名、罗马字、假名和繁体名降为别名。
  `no_avatar` 只表示没取得合格图片，不得阻止已核实姓名落库。
- 「这一页只有一位女优」不构成证据：库里大量番号是 BEST 合集，搜索无结果的页面仍会渲染推荐文章。
  精确回配命中优先于任何「唯一」推断，「唯一」只有在两个番号同证时才作数。
- `entity(kind, normalized_name)` 的唯一约束冲突通常不是 bug，而是同一人新旧艺名的信号：合并走
  `peach.entities.merge_entity`，保留作品多的一侧，迁移关系、别名、外部引用、链接和搜索词，旧称全留作别名。
  `entity_external_ref` 每个 provider 只留一条，同源的第二条被丢弃并报告，不静默覆盖。
- creator / performer 跨类重复不用「作品多的一侧」规则：只有两边非空作品集合完全相同，且 performer
  别名精确命中 creator 名，或 creator 名由 performer 本名与账号别名组成时才自动归并。
- `r18:performer` / `javbus:performer` 是正式发行出演元数据，保留 performer；通用 `performer` 是压平后的
  兼容断言，保留 creator。合并要同步 `asset.creator` 与 `演员:` 投影，否则已删实体仍会在详情页伪造链接。
- r18.dev 的罗马字字段本身就是「现用名 (曾用名, 曾用名)」这个渲染格式，一个字段装了一个人的若干个艺名；假名与汉字写法各自成行，罗马字只有这一份。落库时按 `peach.entities.split_composite_person_name` 拆开，签名是「括号前有空格、括号内逗号分隔、两侧都是罗马字」。同一个字面形状在账本里还承载厂牌消歧（`AV DEBUT（本物人妻）`）、角色出处（`アスナ(SAO)`）、接稿状态和去重后缀，只能靠这条签名收窄。
- `XX XX` 是来源节点文字重复而不是合法别名：person 名进入 CSV、兼容字段或 `upsert_asset_entity` 前先
  收敛完整重复串，清理时同时审计 `asset.creator`、`演员:` 标签和 `entity_alias`。
- `merge_entity` 的两条陷阱：sqlite 连接默认 `foreign_keys=OFF`，子表行必须在函数内显式 DELETE；计数用
  `SELECT changes()` 而不是连接累计的 `total_changes`。合并不可逆，合并后 `PRAGMA foreign_key_check` 应为 0。
- 判断「账本已经有这个名字」要连罗马字一起看，不能用 `peach.entities.name_chain`。那个链按设计剔掉罗马字
  （拿罗马字去日文站查是白跑），但拿它当「已有」判据会把 `entity_alias` 里明摆着的 `Rin Natsuki` 再报一遍
  新别名。要全量就直接读 `canonical_name` 加 `entity_alias`。
- 别名按来源分三类，界面上只有用户自己敲的那一类可撤销（`user:alias`，写入端点 `/api/entity-alias`）：
  刮削（`r18:performer` 等）和合并（`merge:*`、`avdb-actor-mapping@<rev>`）留下的是这条实体当初为什么
  长这样的记录，不给一次点击删掉。自由文本进的是别名表而不是 `canonical_name`，因为那是真相字段，
  只在这条实体已有的名字里挑（`/api/entity-name`）。头像图库按整条名字链逐个查并取并集，所以少一行
  别名就少一批候选：同一个人常按好几种写法各存一批，命中即停会让排在后面那几个名下的图整批出不来。
- 上游名字里的零宽字符在 `canonicalize_entity_name` 一处剥掉，不在各脚本里各修一遍。
  `str.strip()` 不认它们是空白，`normalized_name` 于是带着一个看不见的字符：界面上和普通名字
  一模一样，但 `upsert_asset_entity` 按 `normalized_name` 找不到已有实体，同一个人存成两条，
  按名字搜也一个都搜不到。剥 U+200B／U+200C／U+2060／U+FEFF；**U+200D 不剥**，emoji 的家庭与
  职业序列靠它连字，剥掉会把创作者名字里的一个字形拆成两三个。账本里的两个存量
  （performer 7786 的别名、creator 7513 的规范名）已清，备份 `ledger.pre-zero-width-names-20260904.db`。

## 番号目录、创作者与水印

- 番号目录被投影成创作者时判据只能是文件级证据而不是名字形态：唯一可靠的区分是目录内媒体文件名是否
  解析出同一个番号（`scripts/audit_code_creators.py`），存疑一律留复核 CSV。
- 番号只补给目录里的视频。发行目录里还混着论坛文宣、下载器广告和封面图（`Tokyo-Hot n0780-HD` 里有两张），
  番号写到它们头上有两个后果：库里它们冒充这部片的文件，垃圾复核又因为「自己带真番号」判定目录证据不
  成立，把它们挡在队列外。写入走 `field_owners` 署名 `script:code-creators`，用户改过的格子不再被覆盖。
- 画质前缀（`HD`／`FHD`／`4K`／`1080P`）和版本后缀（`-C`／`-CH`／`-UC`／`-SUB`）不是番号的一部分，
  提取器必须先剥这两层再匹配；界面把版本语义投影成「中字」「无码」「无码破解」，原始 `name`／`code`
  留给文件操作。缺连字符的紧凑 code 只有同时具备片商、发行日或 performer／studio／series 实体证据才恢复。
- 素人系日期式番号（`MMDDYY_NNN`／`MMDDYY-NNN`）的分隔符是片商标识，属于身份：一本道、パコパコママ、
  カリビアンコムPR 用 `_`，カリビアンコム 用 `-`，同一天同一序号是两部不同影片。JavDB 自己就分开保存
  （仓库外的 `attic/evidence/20260911-javdb-api-probe/probe-result.json`：搜 `092415-001`，首位返回的是一本道的
  `092415_001`）。`catalog_rules` 的归一化、身份比对和查询变体一律原样保留分隔符，也不生成另一种写法的
  变体：用错分隔符搜到的是别的片；只有来源给出不带分隔符的纯数字串时两种才都算命中，缺一个字符不是反证。
  野生文件名的写法会漂移（同一部一本道既有 `1pon-092415-001-fhd1`，也有 `1pondo-092415_001-FHD`），
  所以剥番号显示标题时两种分隔符都放行，落进 `code` 的值则保留文件名给出的那一个。
- 日期式番号的六位是 `MMDDYY`，月日必须成立才算这一形态。只看位数的话，手机录像
  `VID_20220818_125735_816.mp4` 里的 `125735_816`（12 月 57 日）就是一条一本道番号。
- Tokyo-Hot 的编号没有厂牌字母段，规范写法是小写：本编 `n1234`／`k1234` 补零到四位，Red Hot 支线
  写成 `red-123`。javbus 的作品页地址就是 `/n1234`，参考实现 NeoAVDC（MIT，仓库外的
  `attic/tools/20260911-参考项目/NeoAVDC/src/main/number/parseNumber.ts` 的 `TOKYOHOT_NUM_RE`）同样
  输出小写 `n####`；`k` 与 `red` 两支在本机账本里一条没有，它们在 javdb／javbus 上的写法**未取得**实证。
  编号只有一个字母，形态挡不住 `no0037_01` 这类名字，所以只在两个位置上认它：名字开头，或名字里
  已经写着 `tokyo-hot`。
- 西片按「厂牌／系列 + 发行日」命名（`DorcelClub.24.12.02.Christy.White.XXX.1080p`），这是身份不是番号：
  `catalog_rules.western_release_identity` 给出 `DORCELCLUB.2024-12-02`，`release_identity` 认它，
  番号提取一律返回空。两位年份按 70 分界展开，四位年份原样。只在 token 开头认，不在 token 中段搜：
  账本里的 `E078. Redhead.Sucking.Big.Cock.And.Hard.Sex.2019.10.15` 中段搜会得到系列名 `Sex`。
- 只说明「这是什么文件」的词（`IMG`、`VID`、`VIDEO`、`NO`、`PART`）与番号主体同形，集中在
  `catalog_rules.CODE_BODY_STOPWORDS`；画质词归 `_QUALITY_HEAD`、转载站标识归 `REPOST_SITE_LABELS`，
  三份名单各管一类，提取时依次过一遍。新增条目先用本机临时工具 `build/parse_shapes_audit.py`
  （不随仓库分发）的 `stems` 在真实账本上取误判证据；创作者昵称（`sumwall95`、`retsu_dao`）同样撞这个形态，逐个塞进名单只会得到一张不收敛的表。
- 推广域名在番号的头、尾和方括号三种位置都出现（`www.98t.la@ABW-358-U`、`ABP-762-fuckbe.com`、
  `[xxx.cc]ABC-123`），番号提取与目录判重共用 `strip_promo_markers` 这一层，各剥一半会让叠了两层的
  `[98t.tv][98t.tv]ABW-251` 在其中一处漏网。
- 来源返回的番号必须和查询的番号比对过才算命中。javbus 一侧是拿番号做关键词搜索取首个结果，搜不到就
  返回近似的别人（`SA-104 → AVSA-104`、`CHU-101 → CHUC-101`、`AR-301 → STAR-3016`），2026-09-02 实测
  68 次匹配 58 次番号根本不对，整个 `B:\MVP\MIB\`（韩国内容）因此被写上日本厂牌、系列和标题，还靠这些
  假证据升级成 JAV。判据是 `catalog_rules.same_release_code()`，它只归一已核验的前缀别名、DMM 的 `h_` 标记、
  补零和重制尾字母这些良性差异；来源没给 id 的不拦（缺证据不是反证）。复核队列这一侧按同一条判据
  剔候选（ADR-0035）：候选全被剔掉的行整行不进队列，点了也写不进去的东西摆在那儿只是要人再认一遍。
- javbus 是备选来源（`metadata_policy.FALLBACK_SOURCES`）：同一个字段上还有别家可用时它的取值不当证据，
  只有它一家时才轮到它；这一步排在番号日期判据之后。剔完之后来源全是官方的字段，自动写入可以替换账本
  已有的值，规则名记 `adr-0035-official-replaces-*`；community 来源仍然只补空（ADR-0035）。
- 韩国 MIB 的编号（`catalog_rules.KOREAN_MIB_PREFIXES`）资料与封面都不问 JAV 来源。`HA-101`、`MY-102`
  撞上番号完全相同的日本作品，番号核验照样通过，只能按编号前缀整体不问；刮削、扫描与采集、页面取封面、
  封面批次和按日志恢复五个入口都按 `is_korean_mib_code()` 拦。封面的跨作品判据同时比字母段和数字段：
  `YUJ-101 → yuj00011`、`435MFC-135 → h_1711mfcc00027` 字母对上、数字不对，都是别的片。
- `catalog_rules.code_query_variants()` 仅扩展搜索词；每次返回都以账本原始编号校验，缓存和网络结果同样受检。
  前缀等价表与查询表分开：已核验的 LUXU、BAZX、HA 写法可归一，其他数字前缀保留。
  MGStage 官方商品详情路径中的完整编号可佐证其省略前缀的展示 id；封面、标题和搜索 URL 不作身份依据。
  DMM／r18dev 只给 `content_id` 时，其编码内的厂牌段可用于核对裸番号，不能抹掉查询中的 MGStage 前缀。
  `390JAC-040` 是 MGStage 配信，`JAC-040`／DMM `118jac040` 是另一部 DVD 合集，JNT 同样不得按裸编号合并。
  无法证实的变体返回 `identity_mismatch`，保留原始快照但不生成字段候选。
- 创作者是频道主而不是出镜者：文件名里可建创作者的只有 `RT_@X - 正文…`、明确标注的 `女主@X` 和正文里的
  中文名；末尾成串裸 `@A @B @C` 是互推，`📷：@X` 是摄影师，都不建。
- 发行平台既不是厂牌也不是创作者。FC2、myfans 这类是卖东西的地方，站上有实际卖主（出品者）的那个账号才是
  creator；平台本身只能当来源／平台实体，链接按 `catalog` 登记，不给它找「厂牌官网」，那条路对它本来就不
  成立（`harvest_studio_sites.PLATFORM_ENTITIES` 直接判「不适用（发行平台）」，一个请求都不发，也不静默跳过）。
  账本里有些 FC2 作品标着女优、有些评论里也提到人，那是 **performer** 身份，不能顺手把平台记成创作者：
  一旦记了，这个平台下所有卖主的作品都会挂到同一个「创作者」名下，和聚合目录打统一标签是同一类事故。
- 转载渠道水印不是创作者水印，目录名同样可能是伪装；判定优先级是画面水印 > 作品名联网反查 > 文件名文本。
- 打创作者级标签前必须先按 ledger 路径的下级目录分布验证这个 creator 是不是聚合目录：给聚合目录打统一
  风格标签就是 `asce` 事故的重演。

## 女优名字与头像来源

- 头像去精心整理的图库取，Logo 反过来只认品牌自己：官网与厂牌自有社交账号才是权威来源。
- 候选按实测像素判定（`peach.images.classify`）：短边 < 128 拒绝，头像另按长边 ≥ 500、短边 ≥ 300 判，
  竖构图人像套用方图门槛会拒掉最优来源；只有 URL 没有实测尺寸不算候选。
- `audit_performer_portraits.py` 把合格图放进候选专用的内容寻址缓存，每条另存 provider、名字命中档、
  上游 ID/URL、尺寸、MIME、SHA-256 与 policy version；与当前头像字节相同的只留审计证据，不进 `/review`，
  脚本没有写 ledger 的路径。
- `fill_portrait_gaps.py` 走完从缺口到装上的这一段：没装过头像的人里，名字链在图库只命中一张的
  直接装上（复用挑图弹层那三步 `avatar_picker.choices`／`resolve`／`install`，所以证据、缓存与取景
  sidecar 的口径和手工换图完全一致），命中好几张的一张都不装，改产一份对照表（`--sheet`）：候选图
  并排摆着，旁边是她在这个库里的作品链接。默认 dry-run，`--apply` 才写头像文件；账本连接按只读开，
  这一趟不写 ledger。
- **图库按名字存图，同名的是不同的人。** `ななみ` 这种单名命中 22 张，那 22 张是 22 个人，自动挑
  等于随机给她安一张别人的脸，所以「只找出一张」是唯一敢自动装的判据。单名即使只命中一张，证据也
  只有「键完全相同」这一条，装上之后仍要在资料页上认一眼；对着作品认人这件事机器做不了。
- **它的取数判据是「盘上没有 `performer-<id>.img`」，所以一张装上去的差图会把更好的源永久挡在门外。**
  2026-09-05 社媒采集把作品封面裁片装进了一批空槽位，这些人从此不算缺口；Gfriends 索引里有其中
  一部分的正脸照，宫下玲奈那一档 1176×1803，一次都没被考虑过。缺口审计答不了「在位那张够不够好」，
  换源要另起一轮普查：按 provenance 的 `provider` 认出封面裁片，按 sidecar 认出检不出脸、脸太小、
  源图太小，再逐个问一次图库。
- **抓回来的头像带别人的水印，要在字节里去掉，不是靠取景遮住。** 页面按脸取景后，底部那条
  `PRIVATE.com`、`TEAMSKEET.COM` 多半落在取景框外，但看不见不等于不在：导出、换取景规则或
  任何改用整图的地方都会把它带出来。`scripts/scrub_avatar_watermarks.py` 默认只看不写，
  产出一份候选 CSV 加一叠左右对照的标注图，人确认后再 `--apply`；原图连三个边车整套搬进
  `avatars-superseded/`，provenance 补一段 `watermark_scrubbed`，取景 sidecar 按新图重算。
  检出与移除的判据、模型来源和实测数字见 REUSE.md「头像水印检出」。
- **移除优先裁边，能裁就不 inpaint。** 那一批里 37 张有检出。裁切一个像素都不伪造，inpaint 会；
  而且 inpaint 的结果在这批图上普遍不好看：`performer-7911` 左边一列名字水印只抹掉汉字、
  留下半透明的 `Ai Yuzuki`，比原样更难看。
  裁切线受两条约束：不许切进人脸框加留白（脸框取自 `peach.face_detect`），不许把图裁得只剩
  70% 面积以下；逐边独立判定，一条边裁不动不影响别的边。
- **检出器抓不到半透明水印，所以这条流程是半自动的，人工补框是正路不是补丁。**
  往 `--marks` 的 CSV 里补一行 `file,x,y,w,h` 就行，人工框不受分数、尺寸和位置先验约束，因为那些
  判据是用来质疑检出器的，不该用来推翻已经看过图的判断。实测 `performer-7911` 补一个
  `0,0,62,508` 的整条左边框，四处水印一次全裁掉。
- **一张图上检出超过 4 处文字就整张放过，不动一个像素。** 那不是带水印的头像，是作品封面被当成
  头像装了进去，满屏宣传文字全被检出（实测 620 张里 14 张，最多的一张 32 处）。去水印解决不了
  这个问题，涂一遍只会把一张错图变成一张糊掉的错图；它们要的是换源，就是上一条说的那批封面裁片。
- **审计脚本那道「长边 ≥ 500」是源头门槛，不是显示门槛。** 它拦的是缩略图级来源；拿它当显示
  门槛会把一张脸宽 208px 的 382×382 挡在门外，让在位那张脸只有 55px 的封面裁片继续占着位子。
  显示侧的尺寸约定见 `docs/FRONTEND.md`。
- **挑图按检出的人脸宽度，不按画布面积。** 1280×795 合照里那张脸可能远小于 500×600 单人照里的；
  检不出脸的一律不装，官方图也一样。换图只在赢家那张脸更宽时才动手，填不满圆框的赢家只在在位的
  检不出脸时当保底装上。取景 sidecar 必须跟着图一起换（`/review` 的批准落地自 0.17.2 起也检一次脸），
  理由见下文「换图必须换 sidecar」。
- 可用来源实测结论：r18.dev、av-wiki.net、Gfriends 可用；javlibrary、missav、xslist 被
  Cloudflare 拦，njav 有验证墙，jav321 无独立女优字段。被 Cloudflare 拦的站一律放弃，不绕过机器人检测。
  javdb.com 抓得到，但它自己按出口 IP 封速率，判据见下文。
  既有库采集只在官方渠道落空时按番号问 AVBase、JavBus 与 javdb：javdb 主机间隔由用户定
  （`library_processing.SOURCE_INTERVALS`，2026-09-22 起 3 秒，两个主机一起改），javdb 与 AVBase 回 403
  就整源停下，资料与封面的比对规则见 ADR-0030、ADR-0032。
  **FC2 的商品号只问 javdb**（`community_catalog.community_sources_for`）：2026-09-22 清点本机 1213 份来源证据，
  AVBase 那 86 份、JavBus 那 37 份全是厂牌番号，对 FC2 一份都没给过，javdb 给了 166 份。
  javdb 对 FC2 补的是演员（167 份里 51.5% 有）与发行日，厂牌、标签、封面一份都不给，所以它问得慢却砍不掉。
  一轮采集的长短等于 javdb 请求数乘这个间隔：`HostLimiter` 等的是「距上次满 N 秒」，别家的往返落在这个窗口里
  被吸收，所以跳过两家省的是配额和撞 Cloudflare 的次数，不是时间；同理把几家改成并行也省不出时间。
  2026-09-22 按 5 秒实测一轮 565 部走 3349 秒（5.93 秒/部），其中 javdb 约 731 次请求折合 3655 秒，两者相差 9%。
  停多久按次数翻倍：第一次 `scraping_access.FIRST_BLOCKED_PAUSE`（15 分钟），连着再撞才翻到 `SOURCES` 的
  `blocked_pause` 上限（javdb 24 小时、AVBase 6 小时），通了一趟就把记录清掉重新起算。
  **上限不能当首停时长**：实际封期常常短得多，2026-09-22 实测 javdb 记下的 24 小时才走了 6.6 小时，
  用同一套 client 问首页和两条搜索全回 200，而那一轮 778 部片的 1432 条失败全部写着「来源正在冷却」。
  冷却期抛的是 `SourcePaused` 而不是 `NotFound`，所以「7 天内不再问」的记忆（`library-metadata-misses.json`）
  一条都不记：盲等期里跑的每一轮都白跑，下一轮从头再问同样这批。
  **javdb 的 403 不是传输指纹造成的，所以不给它换 curl_cffi（2026-09-22 对照实验）。**
  起因是 amane 的 POC（`docs/reference-snapshots/amane-crawlers-poc.md`）在同一个代理出口下用 curl_cffi
  轮换浏览器指纹拿到了 javdb 完整详情页，据此怀疑 Peach 撞的 403 出在 HTTPX 的 TLS/HTTP2 指纹上。
  实验取四页（SSIS-950 的搜索页与详情页 `/v/zK3x8E`、深田えいみ 的演员搜索页与资料页 `/actors/pRMq`），
  四组配置各走一遍：HTTPX 带 Cookie（当前生产路径）、HTTPX 不带、curl_cffi `chrome136` 带 Cookie、
  curl_cffi `chrome136` 不带；另有一组 curl_cffi 指纹硬写 Peach 的 UA 字符串只走两张搜索页。
  全程走 `peach_proxy` 的 `mode=environment`（127.0.0.1:7897），按 5 秒主机间隔共发 28 次请求。
  **十六个格子全部 HTTP 200，没有一张 Cloudflare 挑战页、没有一张登录页**：搜索页 27.8–49.3 KB，
  详情页 89.2–90.1 KB（`sources/javdb.py` 的面板正则各解出 8 个字段），资料页 78.5–79.4 KB
  （`javdb.all_names` 各解出 `深田詠美 / 深田えいみ / 天海こころ`）。UA 与 TLS 指纹不一致的那一组也是 200。
  两种 transport 的差别只剩响应体几百字节的抖动和界面语言：带 Cookie 的回简体，不带的回繁体。
  实验时 `scraping-javdb.cooldown.json` 不存在，即 javdb 不在冷却期；amane 那次成功同样落在冷却已过的窗口里。
  这与本节既有数字相互印证：一轮 565 部片打 731 次 javdb 请求能整轮跑完，封是打到一定量之后才来的，
  这是按出口 IP 计的速率配额的形状，指纹识别会在第一次请求就拒。
  **未取得**：封期之内两种 transport 的对照。要取得就得先把出口 IP 打进封锁，这一条不做，
  所以「已经被封之后换指纹能不能立刻通」仍然未知。脚本与原始结果留在仓库外的
  `attic/evidence/20260922-javdb-transport-fingerprint/`。
  失败原因分开说：官方各版本只回「准备中」占位图是作品多半已下架（MIDE-594）；两个图源各有图但 dHash 对不上是
  「不是同一张图」，不用。社区来源的图只出自一个图源时照样装上，`.scraping.json` 的 `verified_by` 为空即未经印证
  （IPX-060 只有 javdb）。JavBus 有年龄门，2026-09-15 实测番号页不带 Cookie 回答题式年龄验证页；javdb 有登录墙。
  两家的 Cookie 由用户在浏览器里过门或登录后贴进采集设置，公开采集随请求带上。MIDE-594 在 JavBus 有封面
  （2026-09-15 人工核对），IPX-060 在 JavBus 是 404。`sources/metadata/javinizer-go/` 下的 JavBus、javdb 旧快照只借厂牌选官方渠道，
  封面不当官方候选：JavBus 搜不到原番号时返回的是别的作品。
  Gfriends 只按 `Filetree.json` 和单张 raw 媒体当外部 Provider 用，不克隆图库、不把图片放进 Git。
  索引缓存按 mtime 计龄（一天），取不到新索引就退回旧缓存并在输出里告警；那一轮的「未收录」
  记 error 不记 no_match，否则 `--resume` 会把一次网络失败固化成永久答案。
- **DMM 女优一览页可达，但它的头像只有 125×125，只适合身份绑定的首次头像（2026-09-11 实测）。**
  `https://www.dmm.co.jp/mono/dvd/-/actress/=/keyword=<假名行>/` 经 Peach 的 `dmm` 来源设置
  回 200、125 KB 的完整列表页（一页 120 位，带站内 actress id 与括号里的旧艺名），没有出现
  区域拦截那句「このページはお住まいの地域からご利用になることができません」；
  `pics.dmm.co.jp/mono/actjpgs/<罗马字>.jpg` 不带 Referer 也回 200，确认无防盗链。
  问题在尺寸：`actjpgs/<名>.jpg` 是 125×125、`actjpgs/medium/<名>.jpg` 是 100×100，长边 ≥500、
  短边 ≥300 的高清候选门槛和 320px 的显示门槛都过不了。而且这批图 Gfriends 已经整批收着：
  `z-DMM(步)` 7011 条、`z-DMM(骑)` 14596 条，就排在质量档位的最后一档。所以不为它另起高清
  provider：同一个来源接第二遍，还少了档位排序和 AI 修复版。取证与重放脚本在仓库外的
  `attic/evidence/20260911-dmm-actress-probe/`。新导入是更窄的例外：r18.dev 同一人物对象直接给
  DMM id、名字和文件名时，缺头像的实体可先装这张官方缩略图，随后仍由换头像页升级。页面上的
  一页 120 位日文名、旧艺名和站内 ID 继续用于名字链与消歧。
- javdatabase 的入口必须是账本里的番号，不能按名字拼 slug。它一个艺名一页，slug 与人不是一对一：
  `/idols/rin-natsuki/` 打开的是 `Rin Oka` 的资料页；站内搜索也不给 idol 页，只回作品列表。查询顺序固定为
  番号 → `/movies/<code>/` → 页面上给出的 idol 链接 → 名字，每一步都由上一步的页面给出
  （`scripts/harvest_javdatabase_names.py`）。一部作品可挂多位女优，番号对上不等于整页名字都属于这个人：
  要求 idol 页的名字里至少有一个已在账本这个人的名字链上才收，对上账本多个人时记「需人工消歧」。
  它能给的是日文原名加旧艺名的罗马字；厂牌名反过来不能用它，它自己就把 `セレブの友` 写成 `Celeb no Tomo`。

## 目录型来源与社媒链接

补女优社媒走「目录型来源整站抓一遍、离线比名、复核 CSV 装入」，不逐人搜索
（`scripts/harvest_directory_links.py`）。

- laoshi.ink 按 sitemap 抓全部女优页（ld+json `sameAs` 加正文外链），bstar-pro.com 过一次年龄门抓 models
  列表与每页；HTML 按 URL sha1 缓存在 `peach-data/state/directory-links/<来源>/`，重跑不再打外站。
- 页面上的名字（中文名、日文名、别名）按 `peach.social_links.name_key`（NFKC、casefold、去空白）与账本
  `canonical_name` 及 `name_chain` 匹配，一页命中两个实体记「需人工消歧」而不是猜。
- 站点自己的社媒账号（laoshi 首页那几枚）先从每页外链里减掉，否则会给每个女优装上站方的 X。
- **一个字段的值只描述它自己那一行。** minnano-av 资料表里「所属事務所」和「公式サイト」是两件事：
  白石亚子的事务所是 T-POWERS，公式サイト填的却是 Prestige 的専属宣传页。此前把事务所名当成每条
  official 链接的标签，资料页上就出现一个同时替两家公司说话的控件：文字写着 T-POWERS，图标（按域名取）
  和落点都是 Prestige。实测 23 条这样贴错，另有 5 条博客和平台账号因为不在平台表里被当成了官网。
- official 链接的标签改成按域名归属写（`peach.social_links.host_owners`）。两种证据：厂牌实体自己挂的
  官网链接直接指认，其次是女优 official 链接里已成共识的那些（同一域名上 `OWNER_QUORUM` 条以上写同一个
  名字）。共识要够多条才作数，因为孤证会自我确认，香西咲个人站 `saki-k.com` 只出现过一次、恰好被贴了
  T-POWERS，采信它等于把错误当证据再用一遍。归属未取得时才退回事务所名，那时它至少不和已知事实矛盾。
- 事务所名住在 `entity.metadata_json.agency`，带 `source` 与 `checked_at`。女优会移籍，按最新覆盖；
  标签的语义是「点过去会看到什么」，装不下「她签在谁名下」。已入库的错标由 `scripts/repair_link_labels.py`
  修，默认只出复核 CSV。
- 结论那一侧是实体：`scripts/install_agencies.py` 把这些名字装成 `entity.kind='agency'`，归属写进
  `entity_membership`（主键在成员一侧，一个人只有一条现役归属，移籍是覆盖）。原文留在 `metadata.agency`
  当证据，两者都在，结论错了才有得回溯。事务所不进 `asset_entity`，因为作品是成员拍的，给作品另存一个
  事务所字段就会漂移，而漂移的那份没人会发现。
- 事务所名里的括号按同一条规则拆：括号外是现用名，括号里的读音和括号后跟着的 `旧・`／`元・` 都是别名。
  旧称撞上另一家的现用名时不写别名：`GG(旧・Prime Agency)` 的旧称正是仍在营业的 `Prime Agency`，
  写进去会让按名字找人落到错的那一家。
- 反向那一问（「这家有哪些人」）走 `scripts/harvest_agency_rosters.py`，一次取一家，比按人逐个问省两个
  数量级的请求。minnano-av 没有事务所索引页，站内编号只出现在女优页「所属事務所」那一格的链接里，所以先
  拿这家已知成员搜出编号，并核对那一格写的名字确实是这家：核名用上一条的括号规则，`KRONE(クローネ)` 拆开
  才对得上账本的规范名加别名，而 `GG(旧・Prime Agency)` 里的旧名不作数。编号写进
  `entity_external_ref(provider='minnano-av', external_kind='production')`，下一趟不必再问。
- 名册页 `actress_list.php?production=<编号>` 一页 30 位，人名读 JSON-LD 的 `CollectionPage`：正文那几个
  `<a>` 的文字是「名字 + 女優情報」，拿它对账本一个都对不上。翻页地址取 `<link rel="next">` 并还原
  `&amp;`，但终点不能听它的：站点在最后一页之后照旧给出 `page=6`、`page=7`，超范围的页返回的就是最后一页
  那几位（production=573 实测第 5 页 9 位、之后原样重复），所以走到「这一页没有新人」为止。翻完的人数和
  `numberOfItems` 对不上要分清是页数封顶还是站点自己的名册有重号（T-POWERS 声明 420 位，去重后 410 位）。
- 名册名字对回账本要连别名一起对：对不上的记「不在库」（占名册绝大多数，默认收成一行计数），一个写法对上
  两个人记「重名」，账本里已经归属别家的记「另有归属」留给人判。`--apply` 只补空着的那一位。
- 事务所会拆、会改名。移籍走 `scripts/resync_performer_agency.py`：按 `--agency` 选整家或 `--only` 点名，
  重问一遍女优页的「所属事務所」，只覆盖 `entity.metadata_json.agency`；变成实体和归属仍由
  `install_agencies.py` 的 REPLACE 落地，两边各拆一次名字就会得出两种结论。检索必须走 `name_chain`，
  账本的规范名是简体中文而站点只认日文写法：只拿规范名去问，LIGHT 那 14 位有 11 位落在「未取得」。
  站上那一格是空的记「站上没有事务所」，不清账本：解约和站点这天不显示这一格，在页面上分不开。
- 「所属事務所」只记现在签在谁名下，退役后转进个人经纪公司的人，那一格写的是她自己的公司（三上悠亜 →
  株式会社Miss），不是 AV 事务所。这种由 `scripts/reject_agency.py` 按复核 CSV 驳回：驳回记进她的
  `metadata.agency_rejected`，撤掉归属，那家没人了就删实体；查实了 AV 时期的事务所就在 `replacement`
  列写上，同一次改挂过去（三上悠亜是 ONE'S DOUBLE，本人 2018 年推文为证）。驳回记在人身上，实体
  删了判断还在；上面写元数据、建实体、补名册三条路径都经 `peach.entities.rejected_agencies` 跳过它，
  判词记「已驳回」。
- LIGHT 于 2026-09-05 实测已拆成两家：`ELTRA(エルトラ)旧・LIGHT`（production=1251，10 位）与
  `EST(エスト)旧・LIGHT`（production=1252，25 位）。名册采集器按括号规则拒绝把任何一家认成 LIGHT，
  这是对的：旧名同时属于两家继承者，认下去就把三家并成了一家。两家的门面各自独立取证：ELTRA 已建站
  `https://eltra.jp/`（社媒 `x.com/eltra_official`），站上自己的艺人名单 10 位覆盖账本这 5 位，与
  minnano-av 的 production=1251 相互印证；EST 至今没有官网，只有 `x.com/EST_prod`，页面上链着
  LIGHT 的旧账号 `light_promg`，这条线索本身就是拆分的旁证。
- 官网取成员 official 链接里标签等于本家名字的那些，用它们的域名根地址，不用某位女优的个人页：
  那是她的页面，不是这家公司的首页。名字拆过之后要按原文再查一次，否则 `ACT(アクト)` 这类明明有站却查不到。
- 判词四种：`ok` 进装入队列、`已有`（同平台同 handle，不分主机写法与大小写）、`conflict`（账本同平台是
  另一个 handle）、`未取得`（页面失败或没有社媒）。
- 来源本身可能是过期数据：目录站抄的 X 账号很多已封停、本人早换新号，所以 X 的 `ok`／`conflict` 行都用
  登出页 og 标签验活：活号有 `og:title` 和指向 `profile_images` 的 `og:image`，不存在的 handle 只回一个
  没有任何 og 的 JS 壳，看不出死活。拿不到 og 时再不走缓存地取对照账号 `x.com/X`：对照正常才敢判
  「疑似失效」，对照也空就是限流写「未取得」。Instagram／TikTok／YouTube 登出页什么都不给，只能写「未验」。
- 判据（平台名单、handle 归一、`twitter.com→x.com` 别名、标签写法、X 死活）集中在 `peach.social_links`，
  `normalize_link_hosts.py`、`harvest_performer_links.py` 都从它取；`harvest_social_avatars.py`
  还留着一份旧抄本。装入用 `install_entity_links.py` 吃
  `directory-links-<日期>.csv`，`-review.csv` 是全部判词供人看，两者都不直接写账本。
- javmodel.com 不是社媒来源，别再当候选来源试：走代理能取到 200（直连超时），但唯一的 twitter 链接是
  分享按钮，本人账号一个都没有。Instagram↔X 互补要等目录数据装入后从账本自身做，不在采集脚本里。
- 按名字发现追更来源时，站上的标识符写法以站方接口为准，不由手柄推定：rule34.xxx 用官方 tag 补全
  （公开、不需要 user_id/api_key、返回值自带帖子数）反查真实标签，只接受抹掉分隔符并折叠大小写后与
  查询词相同的那个，同前缀的别人不算命中；补全一次只回十条，热门前缀会把完整写法挤掉，有凭据时才改用
  直接查标签补上。f95zone 的 `latest_data.php` 只索引 Latest Updates 的五个分类，艺术家的 Collection 帖
  只有带登录 cookie 的站内搜索看得到（无 cookie 时 `/search/` 返回 403）；没有 cookie 就跳过它并保留
  Google 外链，不把「查不到」写成「站上没有」。
- **敲半个名字就能出建议的，只有本机清单和 rule34.xxx 的公开补全这两处。** 本机那份是
  `discover` 顺带下的整站创作者清单（kemono、pawchive、coomer），2026-09-12 实测三份合计 42 万个名字，
  按 casefold 排好表后二分取前缀区间：首次建表 0.84 秒、常驻 57 MB，之后每次查询 4 毫秒；敲字这条路
  **不下载清单**，没下过就是少一组。站上那份走 `api.rule34.xxx/autocomplete.php?q=`，同一条路径挂在
  主域名下被 Cloudflare 拦成 403，只有 `api.` 子域回 200 JSON；它回的是标签不是作者名录（`lewdga` 给出
  `lewdgatta`／`lewdgazer`／`lewdgala`），所以界面要写明这一组是标签。两者都不需要凭据。
- **rule34.xxx 上谁是作者只有站方的分类说得准，而那要凭据。** 补全只回名字和帖子数，按词形猜会错：
  2026-09-12 实测 `lewd`（8548 帖）是 general、`lewd_dorky` 是 character、`lewdtuber` 是 metadata，而名字里
  带 `artist` 的 `lewdchuu_(artist)` 是巧合。分类在 `index.php?page=dapi&s=tag&q=index&name=`，不带
  `user_id`＋`api_key` 回的是 `"Missing authentication"`。三个坑：`json=1` 被忽略只回 XML；`names=`
  不被识别，它会忽略过滤吐一批无关标签；`name_pattern=` 是两边通配的子串匹配且按 id 截断，`lewdga%`
  能带回 `gustav3lewdgallery`，`lewd%` 取满 1000 条里一条真前缀都没有，`orderby` 也不生效，所以只能
  按精确名逐条问。每条 0.32 秒，并发八路后十条 0.70 秒；分类是站上改一次就定的事实，问过就记住。
- **gelbooru 不是 rule34.xxx 的超集，不能拿它替换或前置。** 两站同源但各收各的：实测 `lewd` 在
  rule34.xxx 是 `lewdrex`／`lewdiboo`，在 gelbooru 是 `lewdamone`／`lewdkuma`，同名标签的帖数也差一截
  （`lewdgatta` 380 对 74）。gelbooru 的 `index.php?page=autocomplete2&term=` 确实公开且自带 `category`，
  但 `limit` 不生效、恒回 10 条，拿它的前缀结果给 rule34.xxx 的候选标分类只覆盖 0/10（`lewd`）到
  2/10（`ria`）；改成逐条精确问也只认出 2/10，还要 1.66 秒。候选名单必须来自 rule34.xxx：Peach 在那
  一站建订阅，给出它没有的名字就是误导。
- **F95zone 的站内搜索按整词匹配，半个名字要靠尾部通配。** 2026-09-12 实测 `strauz` 命中 0 条，而
  `strauzek`、`Mr_Strauz` 与 `strauz*` 都命中同样 3 条，所以各种写法都空手之后补一轮 `词*`；四个字符
  以上才加，三个字母加通配等于把半个站搜回来，命中一屏也认不出是哪个作者。
- **线程标题的作者在末尾方括号里。** 站点的约定是 `作品名 [版本或日期] [作者]`：
  `Strauzek Collection [2026-09-04] [Mr_Strauz]` 的作者是 `Mr_Strauz`，整串当作者名会让关注列表上
  顶着一行线程标题。从右往左找第一个不像版本号、日期和 `Completed`／`Unity` 这类站点标签的方括号段；
  作者位里并列两个手柄（`[LazyProcrastinator/LazyProcrast]`）时第一个当显示名，其余是别名候选。
  没有可用方括号时才退回主体，剥掉 `[Collection Request]` 这类前缀标签和 `Models Collection` 这类
  容器措辞（`follow_store.f95_author_name`）。
- **作者的头像与别处身份只在首楼，而且要登录才看得见。** 首楼的发帖人是搬运工不是作者（实测 `63802`
  是 `equalizzoR`、`50685` 是 `thesuperfatcat`），XenForo 的发帖人头像因此不能当作者头像。正文的链接区
  才是名片：带 cookie 时 `63802` 给出 `patreon/strauzek`、`twitter/strauzek`、`twitter/Mr_Strauz` 和
  F95 会员页，游客态这三条站外链接全被换成 `/login/`，有的版块对游客整个关闭（`189698` 回登录页）。
  名片里有 FANBOX 创作者 id 或 pixiv 数字 id 时头像取 FANBOX（`50685`、`87212`、`295303` 三条有）；
  没有时取 X 与 Patreon，两家都不带凭据：X 登出页的 og:image 按下文「`pbs.twimg.com` 的尺寸后缀」
  那条退档，Patreon 公开的 `api/campaigns?filter[vanity]=` 给 `avatar_photo_image_urls.original`。两家各取到能用
  的最大一档后比实际像素留大的（`13899` 的 X 原图 400×400、Patreon 原图 256×256）；SubscribeStar
  **未取得**。认哪些主机算身份写死在
  `follow_sources.profile_link_identity`：论坛正文是谁都能贴链接的地方，放开主机等于把别人贴的地址
  当成作者。
- **jae.tokyo 的女优名录是第三个来源**（人工指定来源，同一站的厂牌名录见下一节）。三届的资料页
  各不相同：2014 是 `jae2014/actress/NNN.html`，社媒和博客混在正文的 `<a>` 里；2015 是
  `jae2015/actress.html` 的 `offActress` 弹层，`actressLinkBtn` 一个按钮一条链接；2017 是
  `jae2017/actress/NNN.html`，人像在 `img_area`、链接在 `link_area`。391 页跑一遍，命中账本 145 人。
- **`jae2014/*` 直连会被重置**（`WinError 10054`），所以 jae 进了 `PROXY_SOURCES`；另两届直连能通，但同
  一个来源不分届走两套出口没有意义。
- **注释里的链接不算这个人的。** AIKA 那页 2017 的 HTML 注释里躺着 園田みおん 的博客和 神咲詩織 的
  Instagram，是上一届的模板被复制过来注掉了。按 `<a>` 硬取会把三个人的账号装到一个人头上，解析前先剥注释。
- **页面写明是博客的就按博客算，不看主机名。** `classify()` 只认 `BLOG_HOSTS`，而
  `alicejapan.co.jp` 的子域、`plaza.rakuten.co.jp`、`takasyo.blog.jp` 都是本人博客却不在名单里；页面上
  那行「公式ブログ」比主机名更接近事实。标签照账本里现有那 23 条写「博客」，页面另外点出博客名时
  （`公式ブログ「旬の果実」`）才带上那个名字，`オフィシャルブログ` 这类泛称原样落进去会让同一件东西在
  界面上出现三种写法（`harvest_directory_links.owned_link`）。
- **主机名一律小写。** jae 的资料页上写着 `https://Instagram.com/…`，`entity_link` 的 UNIQUE 只认字面，
  照抄进去就是同一个账号的第二条记录（`social_links.canonical_url`）。路径和 handle 不动：X 的 handle
  大小写不敏感，但那是用户当初复核过的写法。
- 装入结果：队列 68 条，逐条验活后装上 53 条（`entity_link` 646 → 699，备份
  `ledger.pre-jae-performer-links-20260904.db`，`integrity_check ok`），15 条死链跳过。另有 10 条
  `conflict`（账本里同平台是另一个 handle：三田杏、初美沙希×2、加藤桃香、园田美樱、岬奈奈美、新有菜、
  明里䌷、神ユキ、纱仓真菜）和 1 条「需人工消歧」留在 `-review.csv` 里等人核。
- **名录人像进的是头像竞赛，不是另一条装入路径。** `-portraits.csv` 由
  `harvest_social_avatars.py` 的 `jae` 路线读走，和 X、babepedia 的候选在同一套内容寻址缓存里按
  短边排名比大小；jae 的 600×1000 竖版人像稳赢 X 的 240×240，145 条人像里 5 人产生候选、装上 4 张
  （其余早已有头像，`load_targets` 不收）。竖版全身宣传照的取景交给人脸 sidecar，见 REUSE.md「人脸取景」。
- **X 的显示名写着「応援」的是粉丝号，不是本人。** 名录页把 `篠田ゆう様💝応援アカウント`
  这种账号当本人账号挂着，验活也是「活」：它确实活着，只是不是这个人的。证据里标一句不够：
  `installable()` 只看 verdict 和 alive，标注留在证据里照样会装进账本，jae 8 条、javdb 3 条
  这样的链接就是这么进去的。判据落在 `probe_rows`（`FAN_ACCOUNT`），命中就降级成 `应援账号`
  这个自己的判定。名录型来源不核实社媒归属，这一道只能自己做。已经装进去的 11 条于
  2026-09-04 删除（备份 `ledger.pre-fan-account-removal-20260904.db`）。
- **javdb.com 是按名字进的来源，不是能翻的名录。** 站上没有可枚举的女优列表，入口是账本里的名字：
  逐个写法搜 `search?f=actor&q=`，结果卡片的 `title` 一栏就是这个人在站上的全部写法，不点进去就能判
  身份。名字链要整条搜完再放弃，因为账本的规范名多是简体（`三上悠亚`），javdb 上是 `三上悠亜`／`三上悠亞`，
  `name_key()` 不做简繁转换，只搜规范名一个都搜不到（`harvest_directory_links.collect_javdb`）。
- **javdb 的演员 id 在作品详情页就拿得到，不必另走一趟资料页。** 演員一栏每个名字都挂着
  `/actors/<id>`，`sources.javdb.actresses` 取名字时顺手带出来，名字精确匹配到这条
  资产已关联的人物实体才登记成 `entity_external_ref(provider='javdb', external_kind='performer')`。
  人物页的 JavDB 入口就是靠它拼的（`peach.entry_links`），另开一页只是把同一页再取一遍，
  而 javdb 的配额最紧。历史数据走 `scripts/backfill_performer_entry_ids.py`：javdb 页面缓存与
  `review/agency-rosters.csv` 的 `actress_id` 各补一路，先出 dry-run CSV 再 `--apply`。
- **同名两条记录不取第一个。** 同一位女优在站上常有「有碼」「無碼」两条，搜索结果把两条都给出来；
  两页都进判定，撞上的账号会落成 `conflict` 进复核表。取第一个是默默替用户挑了一位。
- **一部分资料页要登录，回的是登入页而不是 401。** 不注册账号，那一页记一行「未取得」并写明是谁：
  「搜过、站上没有这个人」「搜到了但要登录」「没搜」是三件事，不分开写下一轮还得重搜一遍。
- **要登录的那一页就是「無碼」那条孪生记录。** 2026-09-04 中文名那一轮的 28 条 `要登录` 逐条核过，
  全部是同一位女优的無碼记录，现名栏只有日文写法；有碼那条公开，中文名从它那里就取得到。
  所以为了取中文名去登录没有增量。这一条只对名字成立：無碼记录的作品列表仍在墙后。
- **社媒按钮只在 `section-addition` 那一块里。** 整页别处的站外链接是广告、姊妹站和 RTA 标签，
  每一页都有一份完全相同的。
- 60 位的实测结果：`已有` 20、`ok` 18（验活后装上 17 条，`entity_link` 699 → 716，备份
  `ledger.pre-javdb-performer-links-20260904.db`，`integrity_check ok`）、`命中但无社媒` 18、
  `未取得` 26、`conflict` 5、`需人工消歧` 1。Instagram 是这个来源的主要增量，jae 那轮几乎全是 X 和博客。
- **跑到第 60 位时出口 IP 被站方封了 3～7 日**（`403`，页面写「基於你的異常行為」并建议换节点）。
  已取的 123 页留在 `state/directory-links/javdb/`，判定可离线重放（实测 `网络 0 / 缓存 123`），
  剩下 476 位按下一条的判据接着抓。
- **按出口 IP 计的速率配额和机器人判定是两件事，判据不同。** Cloudflare 与验证墙判的是「你是不是
  机器人」，绕它要伪装成另一种客户端，一律放弃；javdb 这道判的是「这个出口发得太快」，换节点只是
  换一条线路重新计配额，没有伪装、也没有声称自己是别人。所以换出口可用，配额本身照守：5.0 秒的
  来源下限不许压，撞 403 仍然整个来源收工，不在封禁期里换着节点连打，那是拿多个出口凑一个超速
  批次，等于用另一种方式压掉下限。本机在 Clash 留了 `🎬 JavDB` 策略组，`javdb.com`、`jdbstatic.com`、
  `jdbimgs.com` 三条 `DOMAIN-SUFFIX` 指向它，换出口不动脚本；脚本允许经环境代理出网
  （`Site` 的 `via_proxy` 允许 HTTPX 读取环境代理，不保证读取系统代理或 PAC）；应用路由与实际出口
  分开验证，新用户配置边界见 ADR-0024。
- **javdb 的限额规律与自己的速度上限。** 那一轮的时间线（缓存 mtime）：03:22:01 起 8 分钟取到
  124 页，中位间隔 1.23 秒、最快 0.76 秒，逐分钟成功数 44 / 15 / 6 / 0 / 0 / 0 / 7 / 50 / 2，
  第 124 页之后整站每条路径都回 403。可读出三件事：额度按出口 IP 累计而不是按路径；封之前
  不发 `Retry-After`、不降速、不给验证码，中间那两次 68 秒和 260 秒的停顿也没换回额度；
  触发点在每分钟 40～50 页这个量级。所以规则是硬编码的来源下限而不是命令行默认值：
  `harvest_directory_links.SOURCE_INTERVAL` 给 javdb 定 5.0 秒（每分钟 12 页，约为触发速率的
  四分之一），`--interval` 只能往上加、压不过它。
- **撞上 403／429／503 就整个来源收工。** `Site.request()` 对状态码不重试，封了之后接着翻
  只会每位女优每个名字写法各撞一次 403：那一轮实测又跑了好几分钟，一条有用的都没产出。
  `rate_limited()` 命中即 `break`，已取到的页照常进判定，不丢这一轮的成果。
  封禁期过后调大 `--limit` 接着跑，缓存命中不花请求，不需要断点参数。
- **javdb 的圆头像 250×250，进不了头像竞赛。** 44 条人像候选里只有 1 人（立花美凉）账本里还没有头像，
  250×250 也过不了自动线（正方需 ≥400）。为这一条把 `jae` 路线泛化成通用人像路线不值当，
  `harvest_social_avatars.py` 暂不接这个来源。

### 从 javdb 取中文名（`harvest_javdb_cn_names.py`）

- **页面结构：`actor-section-name` 是现名，紧随的 `section-meta` 是旧艺名，最后一个是影片数。**
  两者必须分开取：`JULIA` 那页的旧名里有 `京香じゅりあ`，混成一串就分不出「这是她的中文名」
  和「这是她用过的旧艺名」。解析在 `peach.javdb`，与 `harvest_directory_links.py` 共用一份。
- **现名栏并列的两个名字不一定是同一个名字的两种写法，也可能是两个艺名。**
  `美空あやか` 那页的现名栏是 `一之瀨亞美莉, 美空あやか`，把它当成「中文写法 + 日文写法」，
  就会给美空あやか安上一之濑亚美莉的中文名。判据是首个汉字串必须能在对侧找到（`same_person`），
  对不上的落 `不同名`，规范名不在现名栏里的落 `改艺名` 单独看。
- **比名字时字形要折两次，opencc 一次不够。** 它只管繁简，日本新字体不在它的职责里：
  `永瀬` 转不成 `永濑`、`姫川` 转不成 `姬川`，少一层就把同一个人判成两个人。
  两层都走 `peach.kanji`＋opencc `t2s`，落库的写法另走 `simplify_kanji`。
- **`?locale=zh-CN` 只切界面语言。** 女优名是数据不跟着变，`愛音麻里亞` 在简体界面下仍是繁体，
  简体要自己转。
- 95 位假名规范名的实测结果（134 行 / 88 位）：`ok` 34、`同形（站上只有日文名）` 48 行 37 位、
  `要登录` 28、`旧名` 9、`改艺名` 9 行 8 位、`未取得` 5、`不同名` 1。落库取 `ok`、`改艺名`、`旧名`
  三档：改名 50、新增别名 71、扁平 `演员:` 标签重写 86、冲突跳过 1，备份
  `ledger.pre-javdb-cn-names-20260904.db`，`integrity_check ok`、`foreign_key_check 0`。
- **旧艺名的中译只有资料页有，账本一个字都没有。** 刮削源给日文与罗马字；avdb 映射表每人只给一个
  `zh_cn`，它的 `keyword` 逗号列表只用于匹配、从不落 `entity_alias`；改统称时降为别名的又是日文原
  规范名。于是 `橋本ありな` 在账本里、`桥本有菜` 不在，按后者搜不到人。`--aliases` 在同一趟抓取里把
  现名底下那一栏的中文写法取成候选（2026-09-12 实测 `javdb.com/actors/RJM8`：`橋本ありな`、
  `上乃木まな`、`岩谷志季`、`橋本有菜`）。那一栏站上不给标签，旧艺名与昵称混放（`KxPb` 那行只有一个
  爱称 `傻梦`），解析层分不开也不筛，候选只记 `origin=别名栏`，认不认得这个写法是复核的人的事。
  `--scope all` 把范围放开到已经有中文规范名的人，她们才是
  缺第二个写法的那一批；`--only` 按名字链上任一写法或实体 id 点名一位，不受范围限制，两次请求出结论。
- **别名候选在搜到多页时一个都不产（`多页`）。** 规范名那一份把两页都记下来让人挑，别名这一份不能：
  别名进的是身份，配错了人比缺一个写法更难查回来。撞上另一条实体名下的写法记 `占用`，那是两条该不该
  合并的问题，不由采集这一步决定。页面上没有新写法的也留一行 `无新写法`：查过没查出东西，和还没轮到
  她是两件事。
- 落库是另一个脚本、另一次授权：
  `apply_alias_candidates.py --candidates <csv> --revision <批次> --apply --backup`。
  来源记 `javdb-actor-page@<批次>`（`peach.javdb.ALIAS_SOURCE` 是那个前缀），与
  `localize_performer_names.py` 写的 `javdb-actor-page@javdb-202609` 同一形状，也与界面上可撤销的
  `user:alias` 分得开。批次号必须在命令行里给：解析判错时，认得出批次才能按 `source` 把那一趟整批
  撤回。四种不写：这条实体已有这个写法、写法归另一条实体、账本里的统称已经不是 CSV 里那个
  （快照过期，该重抓）、实体不在或不是 performer。

## 厂牌名与厂牌标识

- 厂牌的日文原名是查出来的，不是转写出来的。罗马音回日文没有唯一解（`Hon Naka` 可以是 `本中` 也可以是
  `ほんなか`），所以 `scripts/localize_studio_names.py` 不做音译：拿该厂牌作品的番号打
  `www.javbus.com/<CODE>` 读 `製作商` 字段，一个厂牌尽量取两个不同前缀的番号（同前缀必然同一家，
  证明不了什么），两页一致才敢提改名。javbus 有年龄门，不带 `age=verified` 只回一张 21 KB 确认页；
  番号页必须走代理，直连超时。
- 那七种判词别混成一件事：来源给汉字或平假名才改名（`Celeb no Tomo→セレブの友`，26 例）；纯片假名只是
  英文品牌的外来语写法，保留账本里的英文原名（`ムーディーズ` 不顶 `MOODYZ`，30 例）；来源自己也写拉丁的
  （`V＆R PRODUCE→V＆RPRODUCE`）差的只是空格与符号，不是去罗马音；账本里压根没有 JAV 番号的西方厂牌与
  FC2-PPV 记「不适用（非番号体系）」，把这 17 个写成「未取得」等于拿不适用伪装取证失败；两个番号给出
  不同製作商记「不一致」交人处理：`K M Produce` 出 ケイ・エム・プロデュース 与 スクープ，那是一个
  账本名底下混了两家。
- 番号站转写的罗马音和意译都不算英文，优先级低于日文原名；只有厂牌自己用的英文名才保留（用户 2026-09-23：
  `PREMIUM` 用英文，`Celeb no Tomo` 用日文）。判据是厂牌自称：官网或官方 X 显示名写片假名、拉丁名只是它的
  罗马音的，同样改回日文（`Akinori→アキノリ`、`Milu→ミル`、`Das→ダスッ！`）；官网自己写拉丁的保留
  （`BALTAN`、`GENEKI`）。所以「纯片假名」判词只是默认值，不是结论，改判直接写进复核件的 verdict 列。
  `merge_studio_name_variants.py` 的 class B 用同一口径：日文侧含汉字或平假名就保留日文侧，纯片假名保留英文侧。
  判「改名」的行由
  `scripts/apply_studio_name_localization.py` 落库：规范名、旧写法降别名、扁平 `asset.studio` 与
  `--logo-root` 下的标识一起改；复核件过期（现名已变、实体已合并）或日文名撞上别家的行只报不改。
- 番号页 404 是那一页的事，不是这家厂牌查不到。印证只能靠跨前缀，但顶替 404 要靠同前缀：`code_groups`
  因此一个前缀一组、组内最多 `--depth`（默认 3）个，组内第二、三个不参与印证、只在前一个取不到时接手。
  少了这一层，`Alice JAPAN` 就会被 `DVAJ-185` 一页 404 判成「未取得」，而 `DVAJ-495` 直接给出
  `アリスJAPAN`。反过来说，一个厂牌所有前缀的多个番号都 404 时，先怀疑账本而不是 javbus：那批英文
  文件名、韩国演员的片子被刮削器套上了同前缀的 JAV 厂牌名（`Kichu`／CHU、`Crystal Eizo`／HA），
  查不到是因为那个厂牌名本来就不属于这些片子。
- 搜官网与 X 账号用日文名，不用罗马音：内置浏览器打开
  `html.duckduckgo.com/html/?kl=jp-jp&q=<日文名> AVメーカー 公式`，2026-09-23 这样查到 20 多家的官网或
  账号（证据在 `peach-data/review/studio-site-seeds-20260923.csv`）。Google 弹机器人验证，不绕过；内置
  WebSearch 只回美国过滤结果，拿番号或罗马音搜返回的是航空公司与收缩包装机。
- AV 厂牌 Logo 的来源是厂牌自己的社交账号头像：社交头像天然是正方形且由品牌本人发布。取证顺序是
  handle → `unavatar.io` 解析出平台 CDN 真实地址 → 从 CDN 下载 → 实测，unavatar 只用于解析地址，
  provenance 两者都记（`scripts/fetch_studio_avatar_candidates.py`）。候选使用内容寻址缓存、SHA-256、
  同厂牌感知哈希和跨厂牌精确重复门槛；同图缩放或重编码记 unchanged，上游视觉真变化才重新进入 `/review`。
  无 handle、无图片、unchanged 和 duplicate 只写健康报告，不占人工队列。r18.dev 详情 JSON 只有
  `maker.name`／`label.name` 和作品封面，没有 Logo 资源，已排除。
- `pbs.twimg.com` 的尺寸后缀不是「有这么大」的证据。无后缀的那一份是上传原图（最大档），带后缀的地址在
  原图更小时返回的仍是原图：`セレブの友` 的 `_400x400` 和无后缀都是 242×242，而 unavatar 给的偏偏是
  `_200x200`（8068 B vs 12302 B）。所以一律从无后缀原图起、按 `peach.social_links.twimg_tiers` 的档位往下
  退（旧头像有过只剩缩略图的），`resolved_url` 记实际取到的那一档，全档缺失才算取图失败。厂牌 Logo
  （`fetch_studio_avatar_candidates.py`）与演员社媒头像（`harvest_social_avatars.py`）共用这一份判据。
- **头像候选按脸的像素宽挑，画布只是它没得比时的退路。** 头像最终落在 64–160 px 的圆框里，认不认得出
  是谁取决于那张脸有多少像素，与这张图多大无关。`performer-8711` 是实测反例：装着的 640×960 全身站姿
  照脸只有 67 px 宽，同一个人另有一张 540×810 半身照、画布小 15% 而脸有 160 px 上下，按画布挑，赢的
  是唯一看不清脸的那张。判据在 `harvest_social_avatars.rank_key`，脸宽由 `peach.face_detect` 的 YuNet 量
  （同 SHA 只量一次），并写进候选 CSV 的 `face_width` 列供复核的人直接看。检不出脸记 0，排在任何量得
  到的候选之后；整批都是 0（模型缺席、清一色侧脸）时排序原样落回画布口径，并在运行统计里说明本轮是
  按画布挑的。单人作品封面这条退路走同一把尺：JAV 双联封面右半幅剧照里的脸常常只有几十像素。
- **头像目录是几条管线共用的，`--apply` 只往好里换。** `--force` 的语义是「已有头像也参加竞选」，
  它覆盖的却是**所有**已装头像，包括别的管线装的，而 `harvest_social_avatars.py` 的候选池（X 的
  400×400、jae 的 320×500、作品封面）比 `verified-photo-page` 那类整版人像差一大截。2026-09-06 实测
  一趟 `--force --apply`：换掉 350 张，其中 282 张脸变小，脸宽中位数从 262 px 掉到 139 px，风见步的
  640×960 半身照被换成 JBS-023 的双联封面。现在写盘前先按同一把 `rank_key` 量一次盘上那张，脸没有
  更大就不覆盖，运行统计里报「在位的更好未覆盖」多少张。在位那张的脸宽优先读现成的取景 sidecar，
  没有才真检一遍。
- **换图必须换 sidecar**。取景 sidecar 与选图判据同出一次 YuNet 检出（`peach.avatar_face`），装头像时
  一并写出；给不出新记录就把旧的删掉。留着上一张图的脸框，页面会拿它给这一张取景、放大到一个空
  位置上，而这在界面上与「这张图本来就该这么显示」看不出区别。`scripts/detect_avatar_faces.py` 从
  批量生成入口退成补齐入口，检测与形状都不再由它自己定义。
- 能解析不等于是对的品牌：`@bazooka` 确实存在且能取到 400×400 头像，但那是 2007 年注册的通用账号，
  不是这个 AV 厂牌。所以 handle 必须逐个取证确认，脚本默认不猜，`--guess-handles` 的产出一律标
  `needs_confirmation` 且不自动采纳，查不到就留空。
- AV 厂牌官网普遍先给年龄确认页，不穿过它只能拿到约 10 KB 的空壳。判据必须是锚文本而不是 URL：否定
  链接指向站外（实测 `dasdas.jp`、`muku.tv` 的「いいえ」都指向 dmm.com），肯定链接「はい（入室する）」
  指向站内，两者的 href 看不出区别。实现见 `scripts/find_studio_socials.py`，
  `test_age_gate_is_crossed_by_the_affirmative_link_only` 守这条线。
- 猜域名找官网的每一道拒绝判据都要能说出「谁是它的反例」，而拒绝判据本身也会误伤真站。
  `scripts/harvest_studio_sites.py` 现在拦停放页（`kawaii.com - domain for sale`，关键词在正文第
  81683 字节却写在标题里）、拦自述不可用的页（`bangbus.com`、`monstersofcock.com` 回 200、82 KB、
  正文成人词齐全，标题只有 `Site Unavailable`，而「域名由厂牌名推出 + 是成人站」那条替代路径会把它们
  确认成官网，所以 `BROKEN_TITLE` 必须拦在停放页判据之后）、拦标题只回显域名的通用站（`prestige.com`
  标题就是 `prestige.com`，真站是 `prestige-av.com`）。最后这条的判据必须是「标题原样印着域名，且除
  域名之外什么都没说」，不能拿 normalise 后的标题去比 normalise 后的主机：`www.naturalhigh.co.jp` 的
  标题 `NATURAL HIGH（ナチュラルハイ）` normalise 成 `naturalhigh`，必然是 `naturalhighcojp` 的一
  部分：域名由厂牌名推出来时这两者永远互相包含，那样写会把整类真站判成回显。
- 判成「没有官网」之前先分清是站点的回答还是网络的抖动，并且把每次尝试的理由都留下。
  `www.naturalhigh.co.jp` 第一次 `ReadTimeout`、同一地址随后 200 且标题正是厂牌名；一次抖动写成
  `未取得`，下游会把这个空结论当成事实。`probe` 因此只对传输层异常按 `page_cache.Site` 的口径重试
  （`retries=2, backoff=2.0`），HTTP 状态码是站点的回答，不重试。同理，`未取得` 的行不能只留最后一次
  尝试的理由：`SOD Create` 曾只剩一句 `取不到：ConnectError`，而真正有信息的那次
  （`www.sod.co.jp` → 200、标题 `SOFT ON DEMAND`）已被覆盖，人看到复核件时无从判断；现在候选判词按
  顺序拼成证据链写进 `note`，只有确认的行才留单条理由。
- 页面上没有的信息，判据里补不出来，只能人工确认。`SOD Create` 的官网就是母公司站
  `www.sod.co.jp`（200、成人站、标题 `SOFT ON DEMAND（ソフト・オン・デマンド）`），而 `SOD Create`
  这个串整站不出现，通用判据到此只能判「标题与正文都没有厂牌名」，缺的那条是「这个厂牌属于哪家公司」。
  放宽通用判据去接住它，等于把 `hunter.com`、`bazooka.com`、`madonna.com` 一起放进来。所以走
  `harvest_studio_sites.CONFIRMED_SITES`：一行一个厂牌，写清地址与人工确认的日期和理由，它只替掉最后
  那道「页面得自述厂牌名」，状态码、空壳、停放页／自述不可用、域名回显四道照旧要过：确认的是「这个地址
  属于这家公司」，不是「这个地址此刻返回什么都算数」。确认地址排在所有推导候选前面，命中就不再走那串死域名。
- 作品数少的厂牌不等于不用补链接。`--min-assets` 是为全量扫描定的阈值，账本里 BangBus、BangBros18
  各只有 1 部视频，OPPAI、MonstersOfCock 各 2 部，它们照样出现在厂牌页那个 160px 大位上。要定点补时走
  `--only <canonical_name>...`：指名就不看作品数，名字对不上直接失败而不是静默跳过。
- 名字里一个拉丁字母都没有的厂牌，得靠汉字与假名自己参与比对，否则整整一类都判不出来。`normalise` 若只
  留 ASCII 字母数字，这些厂牌的 token 就是空串，`site_verdict` 第一步便判「没有可比对的字母数字」；它们的
  域名又推不出来（`slugs` 拿不到拉丁词），`--seeds` 是唯一入口，于是「推不出来的用 `--seeds` 喂，走同一条
  验证」这条路对它们是断的：人工查到的地址取回什么都只能写成未取得。账本 130 个有作品的厂牌里有 19 个
  是这个形状（`一本道`、
  `カリビアンコム`、`スーパーモデルメディア`、`俺の素人`……）。`normalise` 现在留下汉字、平假名、片假名和
  长音符 `ー`；`・`（U+30FB）住在片假名区里但它是分隔符，和全角括号、`【】` 同类，照旧剥掉。
- 页面不会知道账本挑了哪个写法当规范名，所以 `entity_alias` 要一起参与「页面自述厂牌名」那一道。
  `东京热` 的规范名是简体，`www.tokyo-hot.com` 的标题是 `年齢確認 | Tokyo-Hot 東京熱 無修正オリジナル
  徹底凌辱動画`：简体的「热」和日文新字体的「熱」逐字比不上，而账本早就记着 `東京熱`、`Tokyo-Hot`、
  `Tokyo Hot` 三个别名。拿别名一起比不放松任何判据：每个别名都是账本里这个实体自己的名字，不是从页面上
  猜出来的。判词写「对上的是别名『X』」而不是「页面写作『X』」：normalise 剥掉分隔符之后 `Tokyo Hot`
  和页面上的 `Tokyo-Hot` 是同一个串，说成页面原文就不准了。
- 无码站写「アダルト動画」「無修正」，不写「アダルトビデオ」。少了这两个词，`www.1pondo.tv` 这种标题
  （`一本道 | 美を追求する高画質アダルト動画サイト`）厂牌名自述得清清楚楚的真官网只能判 weak，原因仅仅
  是站上用的是「動画」而不是「ビデオ」。这两个词同样不会出现在 Hunter Engineering、Bazooka、麦当娜
  那三个同名站上，成人语境这条判据的分辨力没有变松。
- 账本记罗马音、站上只用日文原名的，不进 `CONFIRMED_SITES`：那是账本名字错了。`えむっ娘ラボ` 在账本里
  曾记作 `M Girls' Lab`，这个串整站不出现（`https://mko-labo.net/top`，标题
  `トップ | 調教、全身奉仕、醜態...M女専門のAVメーカー【えむっ娘ラボ】公式`）；换回日文名后页面自述就对得上。
  白名单只留「厂牌属于哪家公司」这种页面上没有的信息；有别名就走 `aliases`，那是页面上能查证的路。
- 2026-09-21 定点跑了四家无码厂牌（`--only 一本道 东京热 カリビアンコム "M Girls' Lab"` 加一份 seeds），
  四行全 ok：`www.1pondo.tv`、`www.tokyo-hot.com`、`www.caribbeancom.com`、`mko-labo.net/top`。复核件在
  `peach-data/review/studio-sites-20260921.csv`，seeds 在同目录 `studio-site-seeds-20260921.csv`。
  账本里 130 个厂牌仍有 83 个一个 `entity_link` 都没有，这四家的链接与标识都还没有写进账本。
- FC2-PPV 的「只有小图标」已查到底，剩下的是取舍而不是取证：`adult.contents.fc2.com`、
  `contents.fc2.com`、`fc2.com/en/`、`video.fc2.com` 四个主机声明的都是同一份
  `static.fc2.com/share/image/favicon.ico`（16×16，内容 14×14／比 1.00，独角兽头才是真正的标识），
  页面里引用的更大资产全是横向字标（189×68／比 3.05、690×68／比 11.20），本来就属于 `logo` 位。唯一
  又方又大的是 `id.fc2.com/apple-touch-icon.png`（114×114／比 1.00），两道闸门都过，但它是「独角兽 +
  FC2 文字」的纵向锁定图，缩到 28px 文字糊成一团，且挂在 FC2 ID 而不是 PPV 市场的主机上，属于「过闸门
  不等于合适」那一类。`blog.fc2.com`、`live.fc2.com`、`static.fc2.com` 上也没有单独的大尺寸独角兽资产
  （`apple-touch-icon`、`favicon-192`、`icon.png` 全 404）。所以这不是「发现流程没找对」，是站上确实没有。
- FC2 的两个位置各用一份非官网来源，两个地址都是人工指定来源，2026-09-03 指定并于同日取回：
  `icon` 位是 `storage.googleapis.com/datanyze-data//technologies/8ef39cbce34aece41d279b6e8e7dbb77aea3086e.png`
  （400×400 RGBA、内容比 1.07、纯红色独角兽没有文字，sha256 `ddaa3216…f449462`、40901 B），已写进
  `site_icons.HOST_OVERRIDES` 的 `fc2.com`。服务端回的 content-type 是 `application/octet-stream`，
  解得开靠 `link_marks.decode` 里 PIL 的嗅探；按 content-type 决定要不要解会把这一枚整个丢掉，
  `test_an_octet_stream_png_is_still_a_png` 守这条。`logo` 位是
  `images.seeklogo.com/logo-png/42/1/fc2-logo-png_seeklogo-429409.png`（600×600 P 模式、独角兽 +「FC2」
  文字、内容比 3.02，sha256 `6911574c…6c6f1b7`、8916 B），写进 `harvest_studio_icons.LOGO_SOURCES` 而不是
  `HOST_OVERRIDES`：那张表管「按主机发现图标」的例外，这一份管「这个厂牌的大字标在哪」，键的含义和取用
  位置都不同。曾用 App Store 的「FC2動画」商店图标（512×512、内容比 1.00、sha256 `ac318e2b…c99538`），
  2026-09-03 不采用：背景多了胶片图案；地址仍可复现（iTunes Lookup API），但不要再拿回来用。
  没采信的来源与原因：seeklogo 同站那份 2000×662 是字标不用，人工指定的 429409 这份是 600×600 方形锁定图、
  装 `logo` 位；Wikimedia 的 `File:FC2_Logo.jpg` 是同名的另一家（Fiction Collective Two）、
  simpleicons／vectorlogo.zone／iconduck 全 404 或已死、brandfetch 与 clearbit 要凭据或连不上、
  Google／DuckDuckGo 的 favicon 服务只回 16×16、`unavatar.io` 拿到的三个 FC2 账号头像是鸭子和房子的
  吉祥物画不是独角兽、Google Play 那几个 FC2 应用图标里独角兽只是角标。
- 指定标识来源按**形状**分三张表，不是按画质。三个取用位（`.entityportrait`、`.idface`、筛选片）
  都是 `object-fit:cover` 的方框，宽扁字标原样装进去只剩正中间几个字母。所以
  `LOGO_SOURCES` 是原样装进大位的方标（`MIN_LOGO_SHORT_EDGE=96`，低于它就是缩略图），
  `WORDMARK_SOURCES` 是过 `images.bake_square` 烤成方图后两位共用的宽扁字标，下限同 icon 位的 32，
  `ICON_SOURCES` 只管小位、大位照旧。拿 406×86 去撞 96 那道闸门是判错了题：问题不在它小，
  在于它不该走原样装的那条路。
- **两个位置要的可能是同一张图里并排的不同两块。** `シロウトTV` 在 Prestige 名录那份 200×55 里，
  左边是黑框「素」方标（主体 41×49）、右边是横排字标：`bake_square` 的 `refit_plate` 按内容裁一遍，
  落地 64×64 正是那枚「素」，顶 28 px 的筛选片刚好；而展会那份 414×414 的横条字标缩到 28 px 只剩
  一团糊，它该待的是 160 px 的大位。一张表管两位表达不了这种分工，`ICON_SOURCES` 因此存在。
- 大不等于好，但也别把「小」当结论。MGStage 首页轮播位的 `top/jackson.jpg` 是 400×80 洋红底，
  烤方后补出两大块洋红，标识只剩正中一条；通用位 `jackson.gif` 180×54 白底纯字标，小四倍却更对。
  母公司 Prestige 名录那份 `banner-jackson.jpg` 1024×346 既是白底纯字标又够大，三份里它最好。
  都烤出来看过再选，别按像素数挑。
- **换掉已装的图要逐张比过，还要能被收进目标集。** `harvest_targets` 按「有没有 `<safe>.img`」
  收人，改掉指定表里的地址单靠那一条收不到：文件在，人就进不来，复核件上连一行都不会出现。
  `restated_sources` 拿装图时写的 provenance 边车（`source_url`）和表里现在写的比，对不上才收；
  装完边车就一致，下一轮自己退出。写盘时那道「只认更大的」守卫对指定来源不设（`PINNED_KINDS`）：
  它防的是自动发现的网络抖动，而指定表里的地址是人逐张看过写进去的，换上一张小的也是想要的结果。
- 发行平台自己的厂牌名录是官方字标的广度来源：MGStage `/ppv/makers.php` 按 50 音分十一页，
  共 351 家，规格统一 180×54；`osusume` 是站方推荐位、和音节页整片重合，靠 slug 去重；
  50 音导航条自己也是 gif、和厂牌字标混在同一批 `<img>` 里，只能按文件名排掉；
  `【独占】` 是销售身份不是厂牌名的一部分。整站有年龄门，不带 `adc=1` 只回一张确认页。
- 发行商自己的名录同样是这一类来源，入口和 MGStage 并排登记在
  `harvest_maker_directories.DIRECTORIES`（2026-09-22 实测）。Prestige `/api/maker` 一次回
  11 家 JSON，`codeName` 就是现成的罗马字 slug，图是 `/api/media/maker/banner-<slug>.jpg`
  200×55 白底字标（Jackson 那张例外，1024×346）；`/maker` 与 `/maker/<slug>` 都是客户端
  渲染的空壳、标题完全一样，从 HTML 认不出谁是谁，所以走 API 而不是抓页面。KMP `/label`
  一页列完 42 家，名字在 `alt` 上，大半是 SVG，矢量哪个尺寸都清楚，不按后缀筛；厂牌图住在
  `/img2018/label/<slug>/` 或 `/file/label_<时间戳>.<后缀>`，站头页脚那两张 KMP 自家标识走
  `/wp-content/themes/`，按路径分得开。**存名录入口不存图片地址**：`file/label_1727404339.png`
  那串是时间戳，厂牌换一次标识地址就变，重跑一次拿到的才是当下那份。
- 名录给日文名、账本记罗马字，桥是文件名里的 slug。`harvest_maker_directories.py` 四路匹配：
  slug 归一相等、日文名相等、罗马字对上别名、唯一前缀候选（slug 是缩写时，如 `waap` 对
  `Waap Entertainment`）。**归一成空串必须当不可比**：纯日文名折掉非 ASCII 后都是空串，
  不排掉的话 351 家会全部对成同一家，复核件看着满满当当、一条都不能用。首轮探测报过 332 个
  「匹配」，实际 29 个。前缀候选比前三路弱，判据要写进复核件让人能分辨：`きらきらワイフ` 撞上的
  `kira*kira`、`おっぱいちゃん` 撞上的 `OPPAI` 都是另外两家真实厂牌。
- **名录对不上账本，多数时候是账本里没有那家，不是账本缺日文别名。** 402 条对上 45 家，剩下 357 条
  按子串加 0.8 编辑距离这种宽松判据重算，只翻出 11 个疑似配对、逐条看全是假的。MGStage 是素人／
  企划平台，账本里未对上的那 96 家多是 FANZA 系（MOODYZ、Idea Pocket、S1、Attackers）。要覆盖它们
  得另找入口，补别名解决不了（2026-09-22 量过，backlog 第 24 条记着数）。
- FANZA 的厂牌一览 `www.dmm.co.jp/mono/dvd/-/maker/=/keyword=<音>/` 按 50 音分 44 页、839 家，
  带 `age_check_done=1` 才过年龄门，**且必须走代理**：直连回的是「お住まいの地域からご利用に
  なれません」，200 状态码、2.8 KB，不带年龄门那一页的任何特征，只按状态码判会当成正常页。
  它给的是日文名加 `article=maker/id=<N>`，**没有厂牌标识图**，详情页上也只有作品封面，
  所以它是名字来源不是标识来源。同站 `digital/videoa/-/maker/` 那条路连年龄门都过不去。
- 351 对 29 的卡点在账本不在名录：厂牌实体几乎没有日文别名，名录给的又全是日文名。补日文别名能把
  同一份名录的覆盖面一次性抬上去，待办见 `docs/PRODUCT_BACKLOG.md`「待执行的操作」第 24 条。
- **重复实体按写法与书写系统两类合并，一律留英文／罗马音那一侧**（2026-09-04，
  `merge_studio_name_variants.py`，11 对，备份 `ledger.pre-studio-variant-merge-20260904.db`）。
  写法变体（`AVS collector's` 对 `AVS collector’s`）的比较键是 NFKC 加符号折叠，**一个假名都不能丢**：
  只留 ASCII 的折法把 `シロウトTV` 与 `ラグジュTV` 双双折成 `tv`，合出来的是两家真实厂牌搅在一起，
  不可逆。日文名／罗马字名（`ムーディーズ` 对 `MOODYZ`）唯一的身份保证是共用番号前缀，前缀属于厂牌，
  是本机可核验的证据；转写不参与判断，罗马音回日文没有唯一解。撞上两家以上一律交人工。
  合并同时改写扁平 `asset.studio`，否则下一次刮削照着投影把旧实体再建一遍。
- **合并之后标识要跟着改挂。** 标识按 `logo_key(canonical_name)` 命名存盘，被丢弃那一侧手上的方标在合并
  那一刻起没人认领，而保留方的大位空着就回落到补白字标：`プレステージ` 拿着 jae.tokyo 那张 320×320，
  `Prestige` 缺的正是它。`merge_studio_name_variants.py --logo-root` 按复核件搬运，保留方缺哪个变体补
  哪个、已有的一个字节都不动，`.ct` 与 `.provenance.json` 随图走（少了 `.ct`，`/logo` 答不出
  Content-Type）。
- 妄想族自家的发行目录 `mousouzoku-av.com/maker/list/<50音>/` 是 official 级方标来源：213 家，
  一律 `contents/maker/id<N>/logo_l.jpg`、200×200，直接够 `LOGO_SOURCES` 的门槛，不必烤方。
  `wa` 那一页回 500，其余九页正常。名录写 `厂牌/发行集团`（`Asia/妄想族`），账本写罗马字
  （`Asia / Mousouzoku`），按斜杠左半对；173 家挂妄想族、39 家挂エマニエル，都是同人／独立厂牌，
  与账本只交出 4 家。同人目录的价值在方标质量，不在覆盖面。
- javtiful（`/channels`、`/actresses`）是聚合站，图不能当标识用。频道卡片是站方生成的字体图
  （2026-09-04 抽样：Attackers 一枚 512×288 白底黑字，没有厂牌自己的字形），演员卡片是 280×280
  的露出剧照，两类都不适合当头像或厂标。它的名字表倒是真的：`/actresses` 315 页约 7560 位，
  `/channels` 13 页约 312 家，切 `/ja/` 前缀后**演员名**给日文（`hatano-yui` → `波多野結衣`），
  可以当罗马字↔日文的配对来源；厂牌名不随语言切换，补日文别名指望不上它。

## 站点圆标与图标合成

- 外链圆标取站点自己声明的那一份，不是根目录猜到的第一份。顺序是首页
  `<link rel=icon|apple-touch-icon|mask-icon>` 与 `msapplication-TileImage` → web app manifest 的
  `icons[]` → 老规矩位置（`/apple-touch-icon.png`、`/favicon.ico`），排序按「主机覆盖表 → 矢量 →
  位图按尺寸 → 根路径猜测 → mask-icon」。两条排序规则各有实测反例：矢量必须压过任何位图且与 `rel`
  无关，因为 threads 把 512 viewBox 的成品图标声明成 `rel="icon"`；声明过的必须压过根路径猜测，因为
  T-POWERS 根目录的 `/apple-touch-icon.png` 是带文字的横向锁定图，而它 `<link>` 里声明的那个才是紧凑
  标识，两个都是 180，并列时字标会因为路径短而排前。`rel="mask-icon"` 按规范是纯黑剪影，当成品图标用
  会得到一枚全黑方块，所以永远排最后，轮到它时走字形通道。
- 发现流程按设计只读声明，不去正文里翻图；确实需要指定来源的（av-event 的吉祥物只出现在年龄确认页正文、
  FANZA 的资产托在 p-smith.com）走 `site_icons.HOST_OVERRIDES`，每加一行都要写清为什么发现流程不够，
  否则那张表会长成一份没人更新的手工 favicon 清单。一次发现最多真的下载 `MAX_FETCH` 个候选：取回来了
  却不合格才算用掉一次，404 不算。
- 「最高清」不等于「最合适」，判据是内容外接框而不是画布。FANZA 是这条的反例：
  `p-smith.com/apple-touch-icon/fanza.png` 是 200×200，但内容是一条约 4:1 的「FANZA」字标，塞进 32 px
  圆里就是一条糊掉的红杠；48×48 的 `pinned/favicon_r18.ico` 只有单个「F」，反而清楚。所以排序之后还有
  一道内容比例闸门（`link_marks.MAX_CONTENT_ASPECT`），宽扁字标不参加小圆标的竞选，它属于厂牌页那个
  大 logo 位（`/logo`）。同一个品牌在两个位置用两份资产不是不一致，是两个位置本来就要两种东西。
- 过闸门后再分两条通道：成品方形图标（threads 那枚黑底圆角白字）原样放行，圆由 CSS 的
  `.entitylinkicon` 裁，服务端再画一次只会把人家设计好的底色换掉；透明单色字形才做「品牌色圆底 +
  白色主体」。
- 厂牌标识按位置分 icon / logo 两份，但只在真的有两份时才分岔：`<safe>.icon.img`、`<safe>.logo.img`
  都回落到既有的 `<safe>.img`。存盘后缀说明不了清晰度：Prestige 的 `icon` 只有 42 px、MOODYZ 与
  Wanz Factory 的只有 64 px，而它们的裸文件分别是 632 / 403 / 238 px。绝大多数厂牌两个位置拿到的
  仍是同一张。取图位与 `variant` 参数的页面约定见 `docs/FRONTEND.md`。
- **Logo 文件一律是不透明方图。** 边距和底色烤进文件，页面不再各自补救。
  位图的唯一入口是 `peach.images.bake_square`，`classify_plate` 给出它据以分流的判定：
  - `mark`（有透明像素，如 PREMIUM 的全透明底蓝色字标）：按 alpha 外接框裁掉透明边，居中放到不透明
    方底上，内容占边长 `PLATE_CONTENT_RATIO`（0.76，四周各留约 12%），像素不缩放，出不透明 PNG。
  - `tile`（完全不透明，如 M's Video Group 400×400 黑底方块、Natural High 红底、Hon Naka 64×64 青底）：
    底色是设计的一部分：接近方形的原字节返回，长条按边缘主色补方（`pad_to_square`）。不刷白。
  两条路的产物都再过一遍 `refit_plate`，因为方图**摆得不对**和**不是方图**是两件事：小圆片铺满的是
  整张画布不是内容，源站 favicon 常自带大留白（Flower 的金环占宽 0.24、いんすた 0.30、Planet_Plus 0.31、
  まんまんランド 0.55、EST 0.56），铺进 32 px 圆片就小得认不出；反过来顶到边的实心方标四角落在圆外，
  MARRION 的金框和 Tushy 的「T」直接看不见。内容占宽低于 `PLATE_MIN_SPAN`（0.6）裁到内容框、四周留
  12%；内容落在内切圆之外的比例超过 `PLATE_CIRCLE_LOSS`（0.025）把画布补到内容的外接圆；这一趟的
  产物不到小圆片要的实像素（`PLATE_MIN_SIDE`，64 = 32 CSS px 在 2 倍屏上的实像素）就用自己的底色
  补到那个数，浏览器不必再放大它。第三条判的是产物、不是原图：受影响的图有一半是**先裁小才不够用**
  的（Flower 是 180 的画布上一圈 43 px 的金环，裁掉留白落在 55），按原图短边判就永远轮不到它们，
  得再跑一趟才补上，而归一脚本承诺幂等。补边的上限卡在 `PLATE_MIN_SPAN`：再往外撑，内容占宽就掉到
  0.6 以下，成了第一条要裁的那种大留白，两条规则会在同一张图上来回拉锯。2026-09-08 实测命中 7 张：
  DorcelClub 57→64、Flower 三张 55→64、LINX 63→64；HEYZO.icon 39→50、Prestige.icon 42→53
  是撞上这个上限停下的。同一批 150 个文件连跑三趟：第一趟 7 张，第二、三趟 0 张。像素一律
  不缩放，所以裁出来的更小但更清晰、补出来的更大而清晰度不变。断点都是实测的：占宽下一档 FC2-PPV
  0.62 起看着正常，圆外损失落在 T-POWERS 0.019 与 TEPPAN 0.034 之间，圆形图标（Wanz Factory 0.008）
  不受影响。内容框按行列统计，只有零星几个像素的行列不算内容，因为有损压缩在纯色区留下的淡斑点会把
  逐像素外接框撑满整张画布（EST 的字样只占纵向 249 行，斑点却让框横跨 685 行）。
  写入侧只有两条路径，规则同一条：`harvest_studio_icons.py` 的 `install()` 写盘前烤，
  `normalize_studio_logos.py` 对历史文件回溯（目录下所有 `*.img`，含 `.icon.img`／`.logo.img`）。
  两者都幂等：烤出来的产物再跑一次不再有动作。女优头像等照片不走这条路径，不加白边。
  `install()` 只收位图：矢量烤不出方图，它按「拒绝安装」处理，所以目录里那 4 张 SVG 是更早的遗留，
  归一由 `normalize_studio_logos.py` 补上。
  矢量标识（4 个 `image/svg+xml`：DarkRoomVR、TeamSkeetXReislin、TeenFidelity、VirtualTaboo）
  走 `peach.images.bake_square_vector`：同样的 76% 边距，但方底由外层 SVG 给，原文档整个塞进
  嵌套 `<svg>`，一个节点都不改写，因为栅格化会把「放多大都清晰」这个唯一优势丢掉。内容框直接取
  `viewBox`：4 张渲染后实测，决定方框边长的长边都是 tight 的（横向占满 0.97～1.00），
  纵向留白只影响居中。矢量没有像素可读，外层根元素上留 `data-peach-plate="1"` 让重跑据此跳过，
  不靠这个标记就会越套越多。`viewBox`、`width`／`height` 都没有的空壳量不出比例，仍记 `vector`
  原样留着。
- **底色按内容明暗判，位图和矢量同一条规则**（`images._plate_color`；矢量先栅格化一张 256 px 探针数
  像素，产物仍是矢量）。只有笔画直接挨着底色的稀疏标识会被底色吞掉：内容框里的不透明覆盖低于
  `PLATE_SOLID_COVER`（0.9）才判底色，白底上还看得见的比例低于 `PLATE_VISIBLE_RATIO`（0.7）就配深底
  `#111111`。DarkRoomVR 的「DARK ROOM」、TeamSkeetXReislin 的「TEAM」、HEYZO 的「HEY」都是白笔画，
  白底可见率实测 0.20、0.52、0.44，配白底等于把半个标识抹掉。自带整块底的另说：Fitch 的白卡片覆盖
  0.98、Hunter 的迷彩方块 1.00，它们的边界是自己画的，外面那圈只是画框，配深底反而让那块底浮在黑里。
- **归一从原图开始。** 装上去的文件如果记着备份原图、备份又还在本机，`normalize_studio_logos.py` 拿
  备份当输入：烤底毁掉的透明通道和配错的底色在产物上判不回来，从原图重来才能让算法的改进落到已经
  装好的文件上（HEYZO 就是这么修回来的）。边车继续指向原图，别把指针改指到这一轮备份的归一产物。
  边车的 `action` 是认来路的稳定标识不是描述：`bake-white-plate`、`pad-to-square`、`refit-plate`、
  `plate-vector`。`harvest_studio_icons.padded_studios` 按 `pad-to-square` 认「这一张的源图是条状字标」，
  把重新摆位记成补方等于污染那份名单，所以三条位图路径分开记；每张已装位图的来路记在
  `*.img.normalization.json`。回溯已装文件是写操作，走 `normalize_studio_logos.py --apply`。
- **已装的方标太小要再问一趟。** 小圆片是 32 CSS px，2 倍屏 64 实像素；`harvest_studio_icons.py`
  把短边不够这个数的厂牌一并收进目标（`INSTALLED_SHORT_EDGE`、`small_installed_marks`），量的是小位
  真会取到的那一份（`<safe>.icon.img` 优先，没有才回落 `<safe>.img`；`.logo.img` 归大位不参与）。
  写盘另有 `_shorter_than_installed` 守卫，所以再问一趟只可能换上更大的，问不到就在复核件上留判词。
  2026-09-08 实测命中三家：DorcelClub 57、Prestige 42、HEYZO 32。
- **这三家的来源已经问到底，结论分三种**（2026-09-08 实测）。DorcelClub 站上挂着 180×180 的
  apple-touch-icon，够用；取不到的原因在账本：这个厂牌一条链接都没有（entity 5586），采集从零链接
  出发走不到它的站，补一条 `official` 链接就能自己取回。Wanz Factory 与 HEYZO 更大的方标**未取得**：
  官网只有 64×64／32×32 的 favicon（wanz-factory.com 的 `/favicon.ico` 回 0 字节，声明的那枚在
  `/favicons/wanz-factory/`），header 那张是 181×38／339×58 的横向字标，JAE 2014／2015 名录里 Wanz
  那一枚是同一条橙底字标、里面那个「W」章不到 64 px，截出来比手上这张更小；Wanz 那张 64 px 自己就是
  放大件（半分辨率往返 RMS 1.63，同为 64 px 的 Hon Naka 13.65、Idea Pocket 15.37 是真实像素）。
  Prestige 官网 header 是一份 SVG（`/_nuxt/img/logo.*.svg`），那是大位可用的资产，小位仍是字标。
- **页面三处取图位统一铺满，不各自补救。**
  三处（品牌小圆片 `.brandpill .mk`、身份格 `.idface`、厂牌页 160 px 大位 `.entityportrait`）
  的 `img` 统一 `object-fit: cover` 铺满方框，不加 inset、不加 padding、不改 contain：文件已经带够边距，
  页面再补一层就在图自带的底之外多围出一圈框，而三处各自补救的结果必然互相不一致。占位底色
  （`#CFCFCF`、`#fff`、`--overlay-5`）与首字母回落只在取不到图时露出来。
  「原生尺寸 + 模糊补底」（`data-fit-native`）只装在后两处大位上。它的前提是文件比框小，而小圆片
  在 2 倍屏上只要 64 实像素，目录里够不到的只有那三张；按原生摆，换来的是清晰、代价是标识小一半，
  而自带白卡片的 Prestige 42 与 DorcelClub 57 一旦不铺满就露出方角。小图糊的根子在文件，
  该换的是文件；换不到更大的一份，就按 `PLATE_MIN_SIDE` 用这张图自己的底色把画布补到 64 实像素，
  笔画一个像素都不缩放。
- **没装标识的厂牌一个 `<img>` 都不输出。** 可用性随资料一起下发：`/api/tops` 的 `studios[].has_logo`、
  `/api/item` 的 `entity_refs.studio[].has_logo` 与 `has_studio_logo`（非规范厂牌只有扁平 `studio`
  字段，那格单独一个标志，漏了它那条路径会从「本来能取到图」退化成永远只显示首字母）、`/api/entity`
  厂牌页的 `has_logo`。判据是 `WebContract.has_logo()`：一次 `os.scandir` 出的目录索引
  （`logo_index()`，和封面的 `cover_index()` 同一个套路，TTL 90 秒，复核批准 `cache_bust()` 后立刻可见），
  存盘文件名统一走 `previews.logo_key`：取图、可用性判定和批准落地只能有一份规则，各写一遍正则的代价是
  「装上了却取不到」或「说有图但回 404」。旧写法是无条件出图、等 `/logo` 回 404 再由 `image-fallback`
  换成首字母：首页实测 31 个 `/logo` 请求里 21 个是 404，而 404 那条响应不带缓存头，每次重绘再打一整轮。
  门槛在 `tests/test_studio_icon_variants.py` 的 `LogoAvailabilityTests`（可用性与取图在同一个目录上
  必须给同一个答案）和 `tests/test_web_ui.py` 的两条页面源测试（取图位必须带 `studio=` 与 `variant=`，
  且必须先问过 `has_logo`）。
- **人的那张脸同一条规矩：先问过再出图。** `/entity-image` 与 `/avatar` 由 `WebContract` 的
  `has_entity_image()` / `has_avatar()` 判定，随资料下发为 `has_image` 与 `has_avatar`
  （`/api/tops` 的 `performers[]`／`studios[]`、`/api/items` 与 `/api/item` 的 `entity_refs`、
  `/api/entity` 的本体与 `related_performers`、`/api/index` 的人物行、`/api/taste` 的创作者与
  女优两排、`/api/review` 里 `ENTITY_REVIEW_KINDS` 那两类的候选行）。页面只有一处拼这两个
  地址：`web/app.js` 的 `entityFaceImg()`，所有取图位（顶栏圆头像 `.av .ring`、身份格人物位、
  共演者小圆框、资料页 160 px 大位、索引页格子、口味榜行、复核卡片那张脸、沉浸模式署名圈）
  经 `avatarInner()` 共用它，两样都取不到就一个 `<img>` 都不出，首字母垫底直接露出来。
  旧写法一个作品详情页实测 9 个 404（1 个厂牌实体图、4 个人物实体图、4 个头像），首页手机视口
  2 个，`/performers` 滚三屏 5 个，同样不带缓存头。
  `avatarInner()` 对缺席的 `has_image` 按「没图」处理：宽容缺席只会让下一个忘了挂标志的端点
  悄悄退回无条件出图，而这种退化在页面上看不出来：图照样显示，代价全在 404 里。
  端点挂标志用 `web_catalog` 的 `entity_ref()`（身份引用带上 `has_image`）和
  `attach_avatar_availability()`（一次批量取 `snapshot_path`，不逐行 N+1）；榜行这种
  `entity_id`／`representative_asset_id` 直接长在行上的形状，判据仍是同一对函数。
  两条判据形状不一样，不能混为一谈：
  - 实体图是纯粹的「在不在」。`avatar_root` 一次 `os.scandir` 出 casefold 索引
    （`avatar_root_index().entity_images`），存盘文件名统一走 `previews.entity_image_key`，
    kind 是名字的一部分，creator 的图写成 `performer-<id>.img` 是永远读不到的；认得的种类只有
    `previews.ENTITY_IMAGE_KINDS` 那几种。`.ct`、`.provenance.json`、`.face.json` 是边车，不算图。
  - 头像是按需生成的，「目录里没有」只说明还没裁过。所以 `has_avatar` = 已经裁好的 `<id>.jpg`
    **或** 印相还在盘上（同一个 `has_snapshot`）。把后者也判成没有，等于把「点一下就现裁一张」
    那条路永远关掉。生成中途的 `<id>.<格>.tmp.jpg` 不算数。剩下预测不了的 404 只有生成本身失败
    那一种（没有 ffmpeg、六格全黑），所以 `data-drop="self"` 这套失败时撤图的处理一条都不能撤。
  复核卡片那张脸的 kind 由 `web_review.ENTITY_REVIEW_KINDS` 和页面的 `ENTITY_REVIEW_CATEGORIES`
  各留一份，必须逐字一致：一边判成 creator、另一边按 performer 取图，就是标志说有图而请求照样
  404。`tests/test_web_ui.py` 比对这两张表。
  门槛在 `tests/test_previews.py` 的 `EntityImageAvailabilityTests` / `AvatarAvailabilityTests`
  （同一个临时目录上可用性与取图必须给同一个答案）、`tests/test_rm_web.py` 与
  `tests/test_web_review.py` 的端点标志测试，以及
  `tests/test_web_ui.py` 的 `test_no_face_image_is_emitted_before_the_server_says_it_can_be_fetched`
  （页面源里每一处 `/entity-image`／`/avatar` 附近都得有可用性判据）。
- 补方形小标要借 `link_marks` 的内容比闸门，但不能借它的尺寸下限。`MIN_DESIGNED_SIZE=96` 是为
  `/link-mark` 那种 128 px 圆标定的；JAV 厂牌站的 favicon 普遍只有 32×32 或 64×64，直接套 `render_mark`
  会把 HEYZO、Idea Pocket、MOODYZ、Prestige、Wanz Factory、Tameike Goro 六个全退掉，还在复核件上记成
  「仍是字标」。判错的结论比没有结论更糟，因为没人会再去查。所以 `scripts/harvest_studio_icons.py`
  只借真正表达 icon／字标之分的 `content_aspect` 与 `MAX_CONTENT_ASPECT`，尺寸另设 `MIN_SHORT_EDGE=32`
  （要顶的位置本来就只有 28～32 px）、像素原样不放大，`MIN_DESIGNED_SIZE` 不要为这个调用方去动。
- **共享主机守卫**：主机级发现只能代表主机，代表不了挂在同一主机路径下的频道。`bangbros.com/websites/`
  下的 BangBus、BangBros18、MonstersOfCock 三条 official 链接，`discover()` 一上来 `origin(url)` 就把路径
  丢了，三个厂牌坍缩成同一个主机，取到的三份 sha256 逐字相同（三个现有的 `<safe>.img` 原图也是同一份
  `671eb6ba…`，296×82 的 BANGBROS 母品牌字标，同一症状的另一处）。落到的那一枚是
  `bangbros.com/favicon.ico`：64×64、内容比 1.00，两道闸门都过，可它是 Aylo／Project 1 Service 站点模板的
  通用图标（蓝色六边形「1」，`www.bangbus.com`、`www.monstersofcock.com` 两个独立域回同一份
  `a61e1e88…`），和任何频道无关。所以链接带非根路径时，`harvest_studio_icons.py` 给
  `site_icons.best_mark(accept=...)` 挂一道守卫：`site_icons.HOST_SCOPE` 的候选一律不算数，判词
  `平台通用图标`，证据写明取到的是哪个主机的哪一份加 sha256。`/link-mark` 那个位置本来就是按主机的
  （`cache_key` 也按主机），不受这条约束。`HOST_OVERRIDES` 的键因此支持「主机 + 路径前缀」并取最长匹配。
- **来源顺序按分辨率择优，不按正式程度死排**（厂牌页大位是方图，头像够清晰就能当 icon 用）。`harvest_studio_icons.icon_row` 一条链走下来：官网声明的图标 → 首页 header 的
  `<img>` → 人指定的社媒头像 → 页面上挂着的 X 账号头像。短边到 `GOOD_ENOUGH_SHORT_EDGE=360` 就停：
  公司格最宽 180 CSS px，2 倍屏 360 实像素之后在页面上没有分别，每多问一个来源就多敲一次别人的门。
  没到线才把余下的来源问完，然后按短边取最大的那一枚，但要大出 `BETTER_BY=1.5` 倍才顶掉排在前面的：
  声明的 114 对上头像的 119，那点差别看不出来而来源的正式程度有差；bambi 声明的 16×16 对上 400×400
  的 X 头像才是该换的那种差距。2026-09-05 实测这条链把 Bambi Promotion 从 119 提到 400（X 头像原图）、
  LINX 从 63 提到 532（站点自己的 `logo_tekikaku.webp`，声明的 favicon 里没有它）。
- **大不能压过形，两位各挑各的**。顶替者还要不比被顶的那枚宽出 `ASPECT_SLACK=1.1` 倍。eltra.jp 声明的
  `ELTRA_icon.png` 是 300×300 纯皇冠（内容比 1.13），header 那张 `ELTRA_logo.png` 是 800×536 的皇冠加
  ELTRA 字样（1.50）；只比短边的话 536 大出 1.79 倍就把小位顶了，而小位是 28 px 的方框，那张装进去只剩
  一行认不出的字母。反过来那张正是大位要的完整标识，它两道闸门都过、进不了 `policy.wordmark`，所以
  `hunt_logo_row` 从这一趟的收获里另挑最大一枚，判词 `这一趟取到的最大一枚`。
- **一条官网都没有的公司改用社媒头像**。`ICON_LINK_KINDS` 之外还有 `FALLBACK_LINK_KIND="social"`，只在这家
  没有 official／catalog 时才用：那条链接本身就是账号主页，直接取头像，不问声明的图标和 header（X 那两样
  对每个账号都一样）。有官网的一概不走：账本里 453 条社媒绝大多数挂在艺人身上，混进来就成了运营的自拍。
  EST 靠这条拿到 1134×1129（`pbs.twimg.com/profile_images/…/GyqWkfql.jpg`，2026-09-05 实测），
  在此之前它只会记成「无官网链接」。twimg 的头像地址不带签名，和 Instagram 那种解一次过一次的不一样。
- **可达性探测要扛住 TLS 抖动**。`install_entity_links.resolves` 对传输层异常重试三次、状态码一次成局：
  eltra.jp 2026-09-05 连着两趟被记成「打不开，不写入」，而每次重试一下就 200，一条复核过的官网因此
  差点进不了账本。同一条规矩下 `site_logos.logo_images` 丢掉 `data:` 占位图：懒加载占位顶着标识那张
  `<img>` 的 class，词形闸门拦不住，取字节又打不开，白等两轮重试再记一次「取不回来」。
- **Instagram 头像分开验证地址发现与字节下载**。资料页可能提供多个尺寸；小图 URL 改参失败
  不能证明高清版本不存在。嵌入页和资料页都可能混有观看者或推荐账号，必须按目标账号关联字段。
  现有 `--avatars` 读取本机 `peach-data/state/agency-avatars.json`，是人工地址输入，并非通用解析器。
  成熟解析器、Cookie GUI 与签名地址刷新按 [ADR-0024](adr/0024-mark-manifest-not-bundled-bytes.md)
  实施；1000×1000 原图实测及当前验证边界见 [抓取审计](SCRAPING_AUDIT.md)。未完成跨账号 POC
  时只记「地址发现未取得」，不得写成平台像素上限；账号归属仍需区分公司号与艺人号。
- **字标补白**（不是 icon 也可以装 icon，尽量不要落入无图）：方标一个都没做成、
  却取回过短边 ≥ `MIN_SHORT_EDGE` 的宽扁字标时，用 `peach.images.bake_square` 烤成方图装上，判词
  `字标补白`，`content_aspect` 照记（那个数就是「这枚其实是字标」的提示）。同一份方图再出一行
  `logo`（判词 `ok`）装进 `<safe>.logo.img`：不出这行大位会回落到 `<safe>.img`，BangBus 页顶上挂的就成了
  母品牌 BANGBROS。两位装的都是方图：页面三处取图位都是 cover 的方框，298×50 的宽条直接装上去只剩
  中间的「NG」两个字母。人工指定的 logo 来源做成时优先。留第一份而不是最大的一份：
  `best_mark` 的遍历顺序已经是「覆盖表 → 声明 → 根路径猜测」。BangBus（298×50／比 6.60）与 BangBros18
  （298×50／比 6.06）走的就是这条，来源是 `bangbros.com/websites` 服务端渲染进 HTML 的 `*_LOGO` 资产
  （注意 `/` 转义）。MonstersOfCock 那一页没有对应的 logo 资产，`site-api.project1service.com/v1/collections`
  只给照片 avatar/banner，频道页顶部那张 `assets/brand/1151/banners/…jpg` 是 1920×400 的照片横幅不是标识，
  `www.monstersofcock.com` 是同一套 Aylo 壳（favicon 同样是「1」、无 apple-touch-icon），所以它记
  **未取得**、继续回落现有的 `MonstersOfCock.img`，不用推测顶替。
- **展会名录**（人工指定来源 `jae.tokyo`，Japan Adult Expo 的参展厂牌名录）：2014／2015／2017
  三届各带一套片商自己交的 logo，页面结构每届不同：2014 是 `exhibitor/` 里 `<li><a><h2>名字</h2>` 加
  `images/logo/*.jpg`（270×180，`alt` 不可靠），2015 是 `maker.html` 里 `offMaker` 弹层的
  `makerLogo`／`makerRightTitle`／`makerLinkBtn`（188×188），2017 是 `maker.html` 的 `alt` 加详情页
  `makaer/NNN.html` 的 `name_area` 与 `class="pop"` 官网链接（320×320）。2016 那届 `exhibition.html`
  只有图、HTML 里没有名字，认不出是谁家的，不取。211 条名录条目对上账本 26 家没有任何图的厂牌
  （名字对不上却是同一家的按厂牌自称对：名录里 `ムーディーズ` 写作 `MOODYZ`、`SODクリエイト` 写作
  `ソフト・オン・デマンド株式会社`、`Momotaro Eizo` 写作 `桃太郎映像出版`），同一家出现在多届时取像素
  最多的那一届，逐张在白底上看过认得出是哪家才写进 `LOGO_SOURCES`。其中 `ラグジュTV`、`million`、
  `BAZOOKA`、`俺の素人` 四家的图由母公司名录供（Prestige 与 KMP，见上面那条），展会这批留 20 家。
- **指定 logo 来源自己就是入场理由，小位从大位那张烤。** `harvest_targets()` 收三类：补白过的、有链接
  但没图的、有指定 logo 来源但没图的。第三类是为这 26 家开的，它们在账本里绝大多数连一条
  official／catalog 链接都没有，只按前两类收一条都收不到，`site_icons` 的发现流程也走不到它们，
  两个位置一直空着。`icon_from_logo()` 在小位
  自己没做成、大位的指定来源做成了时，把同一张过 `bake_square` 装进 `icon` 位。判「补没补白」看源图
  长宽比与 `images.MAX_ASPECT`（`ok` 恰好等于这一张一个像素都没动过），不看内容比：名录 2014 那届是
  整幅不透明的 jpg，`content_aspect` 对它一律回 0，分不出方图和长条。复核件的 `studio` 列改从
  `LOGO_SOURCE_NAMES` 取，没有链接的厂牌拿不到别的名字。
- **存盘文件名保留假名与汉字。** `previews.logo_key` 按 `\w` 归一，标点仍然变下划线，长度上限 60 不变。
  只留 `[A-Za-z0-9_-]` 的话，非 ASCII 的每个字符换一个下划线，名字里只剩「几个字」这一个信息：
  129 个厂牌撞成 12 组，`プレステージ` 与 `ムーディーズ` 同为 `______`、`シロウトTV` 与 `ラグジュTV`
  同为 `____TV`；撞了不报错，后装的那张盖掉先装的，PRESTIGE 的位置就挂上 MOODYZ 的牌子。
  已装的 60 张都是 ASCII 名，键一个都没变。
- **同一批详情页的官网链接照厂牌自称对回账本，逐条判 kind。** 211 条名录里 125 条带官网，按名字与别名
  （NFKC 归一、去掉空白与 `・.,'"()[]/&+*!?:-`）对上账本 33 家。目录站与配信平台不是官网：`mgstage.com`、
  `indies-av.co.jp`、`dmm.co.jp`、`fanza.com` 四个主机，以及路径里带 `/works/list/` 的按片商筛出来的作品
  列表，都进 `catalog`：JET映像 那条指向 `mousouzoku-av.com`，而那个域名是妄想族自己的官网。母公司站内的
  厂牌页（`km-produce.com/l_06_bazooka.php`、`/million/`）算 official，它就是这个厂牌在网上唯一的门面；
  站内搜索串（`?s=OREA`）、配信站筛选列表（`ppv_advanced.php?`）、周边商品列表（`goods_list.php?`）和
  配信平台首页（`indies-av.co.jp/`，名录给桃太郎映像出版填的就是它）都不是这家的页面，不装。
  `entity_link` 的 UNIQUE 按 URL 字面判，`http://www.x.com/` 与 `https://x.com/` 装进去是同一家官网
  并排两条，所以还要自己按主机去重（Prestige、MOODYZ、Wanz Factory、kawaii、Fitch、OPPAI 六家因此不装）。
  剩 24 条过 `install_entity_links.py`，逐条探活后实装 20 条：BAZOOKA、DOC、million 三条 404，
  MARRION 超时，2014／2015 那两届的地址十年后有一部分已经不在了。
- 判词分档、每一档对应不同的下一步：`ok`、`字标补白`（可装，见上）、`只有小图标`（FC2 全站只有 16×16，
  该去找更大的资产）、`平台通用图标`（见上）、`仍是字标`、`未取得`（一份字节都没取回，`Fetcher` 自己数
  取回几份才判得出来）、`无官网链接`。只有前两档会被 `--install` 写盘。`best_mark` 只回结果不回理由，
  退回原因由 `SquareMark` 就地记下，否则复核件上只剩一个空判词。过闸门也不等于适合：某批七个通过的
  候选六个内容比在 1.00～1.15，Fitch 是 1.84。它其实是「Fitch + 标语」的字标，只是恰好压在 2.2 以下，
  所以 `studio-icons-<日期>.csv` 带 `content_aspect` 列，接近上限的行要人眼看过九宫格再定。
- 反色圆标的锯齿有三层成因，少修一层都还是毛的：遮罩用了 `alpha >= 128` 的二值化（把源图自带的抗锯齿
  中间值一刀砍光）、二值图在源分辨率 48×48 上生成再拉到 64（把台阶一起放大）、字形没有与圆做
  `composite`（白像素溢出圆外，圆边被啃出缺口）。现在 alpha 原样当连续遮罩，整套合成在 8 倍超采样画布上
  做完再一次性 LANCZOS 缩下来，成品尺寸 64 → 128（容器 32 px CSS，3x 屏要 96 px）。改了取图规则或合成
  方式必须同时加 `link_marks.RENDER_VERSION`：缓存保鲜期是 30 天，不换键的话代码换了用户看到的仍是旧那张。

## 番号发现源（Feed）

Feed 只回答一个问题：**最近出了哪些番号**。它不下载、不碰媒体文件，产物是一条番号加一个
可点开的作品页地址，刮削仍走既有的来源链。取证在 2026-09-22 做完，脚本与原始结果留在仓库外的
`attic/evidence/20260922-feed-sources-probe/`；每个来源最多问两次，JavDB 因为要存一份页面
供离线分析多问了一次。

### 可用的两类

- **原生 RSS：sukebei.nyaa.si**（`https://sukebei.nyaa.si/?page=rss&c=2_2&f=0`，2026-09-22）。
  HTTP 200、`application/xml`、84 KB、RSS 2.0，一页 75 条。`guid` 是条目永久链接
  （`https://sukebei.nyaa.si/view/4719097`），`pubDate` 是 RFC 822 带时区的真实时间，**天然满足
  两层去重里的条目身份那一层**。标题形如 `HMN-071 新人 帶來超稀有妹子…戶川步[有碼高清中文字幕]`，
  番号在最前面。整段丢给 `catalog_rules.release_code_from_text` 只认出 3 条（75 条里），
  先按空白与括号切词元再逐个试则认出 50 条（66.7%），**这是 Feed 必须自己做词元扫描的直接理由**，
  不能照搬「整段文本 → 番号」那条路径。认不出的多半是无码番号、素人片与合集，不是解析缺陷。
  `c=2_2` 是分类，`f=0` 是不过滤；换分类或加 `q=` 关键词就是另一个订阅，形状不变。
  **它不给 `ETag` 也不给 `Last-Modified`**，所以对它来说 304 那一层不生效，只能靠条目身份去重。
- **伪 Feed：JavDB 演员页**（`https://javdb.com/actors/<javdb_id>`，2026-09-22）。
  HTTP 200、78,466 字节，一页 40 部作品。每部是
  `<a href="/v/5nr8mp" class="box" title="…">` 加 `<div class="video-title"><strong>PBD-528</strong>…</div>`
  加 `<div class="meta">2026-10-20</div>`：`/v/<id>` 当条目身份、`<strong>` 里就是干净的番号、
  `.meta` 是发行日。40 条里 39 条取得番号（97.5%），剩下一条是番号栏本身为空。
  **它按发行日排在前面，所以「还没发行的作品」会先出现**：上面第一条的 2026-10-20 就在取证日之后，
  空壳的发行日可以晚于今天，这不是脏数据。
  账本里已经有 `entity_external_ref` 的 `javdb` id（`entry_links.provider_ids`），订阅不必让用户
  手抄地址。限流按本文「可用来源实测结论」那一节：主机间隔 3 秒、403 就整源停下，冷却判据在
  `scraping_access`，不要因为 Feed 是后台任务就另开一套。
  **加 `?sort_type=4` 会拿到一份 27 KB 的页面，一条作品都解不出**；同一轮里不带参数的请求仍是
  78 KB 的完整页。所以演员页伪 Feed 一律用不带查询串的地址。

### 已核实不可用

| 来源 | 地址 | 结果 |
| --- | --- | --- |
| FANZA / DMM | `/rss/-/digital-videoa/` | 404；`/rss/` 与新作列表页都 302 到年龄确认页 |
| MGStage | `/rss/mgs.xml`、`/feed/` | 都 404，首页不声明任何 feed |
| 一本道 / 10musume / カリビアンコム / パコパコママ | `/rss/movies.xml`、`dyn/phpauto/movie_lists/list_newest_30.json` | 全 404；首页不声明 feed。`dyn/phpauto/movie_details` 仍然可用（`peach.sources.onepondo`），**但同族没有新作列表路径** |
| Tokyo-Hot | `/product/rss/` | 404，首页不声明 feed |
| RSSHub 公共实例 | `rsshub.app/javdb/...`、`rsshub.app/javbus/...` | 403，公共实例整站挡在 Cloudflare 后面。自建实例没有验证，不作为 Peach 的前置条件 |
| javlibrary | `/cn/rss.xml` | 403（与本文既有结论一致：被 Cloudflare 拦，不绕） |
| JavBus | `/rss` | 302 到 `driver-verify` 人机验证页 |
| AVBase | `/rss.xml` | 404，首页不声明 feed |
| javtrailers | `/rss` | 404 |
| OneJAV | `/rss` | 500 |
| 色花堂 | `forum.php?mod=rss&fid=36` | 200 但只有 1.8 KB 的 HTML，不是 feed |

**DUGA 是个反例，值得单记**：`https://duga.jp/news.xml` 是这一轮里唯一由首页
`<link rel="alternate">` 正经声明出来的 RSS，标题就叫「DUGA 新着作品」，13 条，`pubDate` 齐全，
看起来完全可用。但条目标题一个番号都不带（`DOC はる`、`部下のOLがM性感で働いていたので（3）`），
番号只能从链接里取，而链接里那个是 DUGA 的站内商品号：`ppv/doc-2376`、`ppv/paradisetv-5258`、
`ppv/mousouzoku2-1625`。它们长得和厂牌番号一模一样，`release_code_from_text` 会照单全收，
产出 `DOC-2376`、`PARADISETV-5258` 这类**在任何刮削来源上都不存在的假番号**。
所以判据不是「这个源有没有 RSS」，而是「条目里那串东西是不是真的番号」。
一个源在接进来之前必须先看一眼它的番号长什么样，不能只看解析成功率。

## 缓存与重试

- 整页 HTML 缓存与限速走 `peach.page_cache.Site`（按 URL sha1 命名存盘，`cookies` 用来带过年龄门）。它放在
  `src/peach/` 而不是某个采集脚本里：目录链接采集和厂牌名回查两个脚本都用它。采集脚本的判据
  改一行就要重跑，缓存在手才能让重跑走离线数据、不再打外站。
- 退让重试也在这一层：经代理取 javdatabase 实测约三次里有一次 TLS `UNEXPECTED_EOF`，一次抖动打死整批是
  这个项目犯过两回的错，所以 `Site` 自己重试传输错误（默认 2 次、`backoff` 递增），采集脚本不必各写
  一遍。HTTP 状态码不重试：404 重试三次仍是 404，只是白花三倍流量。
- 解析用的固定件必须是抓回来的那份 HTML。javdatabase 的资料行真身是
  `<b>JP:</b> 涼森れむ  - <b>Alt:</b> Iwatani Shiki, …<br>`，按记忆写成 `JP: 名字` 的固定件会让正则被紧跟的
  `</b>` 顶掉：测试全绿而线上一个日文名、一个旧艺名都没采到，只回罗马字。照着记忆重画的固定件只能证明
  代码和记忆一致。
- DMM 图片主机（`pics.dmm.co.jp`、`awsimgsrc.dmm.co.jp`／`.com`）在国内的直连可达性随运营商走：2026-09
  itdog 实测电信、联通直连正常，中国移动大多在 TLS 握手后被断开。量尺寸时每张候选都断在连接上、没有一家
  回过话，`best_cover` 抛 `CoverConnectError`：它说的是线路，续跑照常重试，新作那一行与采集页据此指去
  DMM / FANZA 的连接方式，不报成官方没有图。
