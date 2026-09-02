# 身份、来源与标识采集

本文件保存「从外部站点取得身份与标识」这件事的判据细节：脚本分工、实测反例、判词含义和不能走的路。
`docs/HANDOFF.md` 只留一句话的边界并指到这里；采集本身的限流、续跑与流量预算见
`.claude/skills/peach-batch-jobs/SKILL.md`，参考产品证据的登记方式见 `.claude/skills/peach-reference-evidence/SKILL.md`。

采集脚本一律只产出复核 CSV。写 `entity.canonical_name`、`asset.studio`、`entity_link` 或头像字节
都是另一次授权，判据见 `.claude/skills/peach-ledger-write/SKILL.md`。

## 命名与身份合并

- 规范名优先用有出处的简体中文通行名，暂无可靠中译时保留日文；旧艺名、罗马字、假名和繁体名降为别名。
  `no_avatar` 只表示没取得合格图片，不得阻止已核实姓名落库。
- 「这一页只有一位女优」永远不构成证据：库里大量番号是 BEST 合集，搜索无结果的页面仍会渲染推荐文章。
  精确回配命中优先于任何「唯一」推断，「唯一」只有在两个番号同证时才作数。
- `entity(kind, normalized_name)` 的唯一约束冲突通常不是 bug，而是同一人新旧艺名的信号：合并走
  `peach.entities.merge_entity`，保留作品多的一侧，迁移关系、别名、外部引用、链接和搜索词，旧称全留作别名。
  `entity_external_ref` 每个 provider 只留一条，同源的第二条被丢弃并报告，不静默覆盖。
- creator / performer 跨类重复不用「作品多的一侧」规则：只有两边非空作品集合完全相同，且 performer
  别名精确命中 creator 名，或 creator 名由 performer 本名与账号别名组成时才自动归并。
- `r18:performer` / `javbus:performer` 是正式发行出演元数据，保留 performer；通用 `performer` 是压平后的
  兼容断言，保留 creator。合并要同步 `asset.creator` 与 `演员:` 投影，否则已删实体仍会在详情页伪造链接。
- `XX XX` 是来源节点文字重复而不是合法别名：person 名进入 CSV、兼容字段或 `upsert_asset_entity` 前先
  收敛完整重复串，清理时同时审计 `asset.creator`、`演员:` 标签和 `entity_alias`。
- `merge_entity` 的两条陷阱：sqlite 连接默认 `foreign_keys=OFF`，子表行必须在函数内显式 DELETE；计数用
  `SELECT changes()` 而不是连接累计的 `total_changes`。合并不可逆，合并后 `PRAGMA foreign_key_check` 应为 0。
- 判断「账本已经有这个名字」要连罗马字一起看，不能用 `peach.entities.name_chain`。那个链按设计剔掉罗马字
  （拿罗马字去日文站查是白跑），但拿它当「已有」判据会把 `entity_alias` 里明摆着的 `Rin Natsuki` 再报一遍
  新别名。要全量就直接读 `canonical_name` 加 `entity_alias`。

## 番号目录、创作者与水印

- 番号目录被投影成创作者时判据只能是文件级证据而不是名字形态：唯一可靠的区分是目录内媒体文件名是否
  解析出同一个番号（`scripts/audit_code_creators.py`），存疑一律留复核 CSV。
- 画质前缀（`HD`／`FHD`／`4K`／`1080P`）和版本后缀（`-C`／`-CH`／`-UC`／`-SUB`）不是番号的一部分，
  提取器必须先剥这两层再匹配；界面把版本语义投影成「中字」「无码」「无码破解」，原始 `name`／`code`
  留给文件操作。缺连字符的紧凑 code 只有同时具备片商、发行日或 performer／studio／series 实体证据才恢复。
- 创作者是频道主而不是出镜者：文件名里可建创作者的只有 `RT_@X - 正文…`、明确标注的 `女主@X` 和正文里的
  中文名；末尾成串裸 `@A @B @C` 是互推，`📷：@X` 是摄影师，都不建。
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
- 可用来源实测结论：r18.dev、av-wiki.net、javdb.com、Gfriends 可用；javlibrary、missav、xslist 被
  Cloudflare 拦，njav 有验证墙，jav321 无独立女优字段。被 Cloudflare 拦的站一律放弃，不绕过机器人检测。
  Gfriends 只按 `Filetree.json` 和单张 raw 媒体当外部 Provider 用，不克隆图库、不把图片放进 Git。
- javdatabase 的入口必须是账本里的番号，不能按名字拼 slug。它一个艺名一页，slug 与人不是一对一：
  `/idols/rin-natsuki/` 打开的是 `Rin Oka` 的资料页；站内搜索也不给 idol 页，只回作品列表。链路固定为
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
- 判词四种：`ok` 进装入队列、`已有`（同平台同 handle，不分主机写法与大小写）、`conflict`（账本同平台是
  另一个 handle）、`未取得`（页面失败或没有社媒）。
- 来源本身可能是过期数据：目录站抄的 X 账号很多已封停、本人早换新号，所以 X 的 `ok`／`conflict` 行都用
  登出页 og 标签验活——活号有 `og:title` 和指向 `profile_images` 的 `og:image`，不存在的 handle 只回一个
  没有任何 og 的 JS 壳，看不出死活。拿不到 og 时再不走缓存地取对照账号 `x.com/X`：对照正常才敢判
  「疑似失效」，对照也空就是限流写「未取得」。Instagram／TikTok／YouTube 登出页什么都不给，只能写「未验」。
- 判据（平台名单、handle 归一、`twitter.com→x.com` 别名、标签写法、X 死活）集中在 `peach.social_links`，
  `normalize_link_hosts.py`、`harvest_performer_links.py` 都从它取；`harvest_social_avatars.py` 和
  `import_stash_entities.py` 还各留着一份旧抄本。装入用 `install_entity_links.py` 吃
  `directory-links-<日期>.csv`，`-review.csv` 是全部判词供人看，两者都不直接写账本。
- javmodel.com 不是社媒来源，别再当候选来源试：走代理能取到 200（直连超时），但唯一的 twitter 链接是
  分享按钮，本人账号一个都没有。Instagram↔X 互补要等目录数据装入后从账本自身做，不在采集脚本里。
- 按名字发现追更来源时，站上的标识符写法以站方接口为准，不由手柄推定：rule34.xxx 用官方 tag 补全
  （公开、不需要 user_id/api_key、返回值自带帖子数）反查真实标签，只接受抹掉分隔符并折叠大小写后与
  查询词相同的那个，同前缀的别人不算命中；补全一次只回十条，热门前缀会把完整写法挤掉，有凭据时才用
  直接查标签兜底。f95zone 的 `latest_data.php` 只索引 Latest Updates 的五个分类，艺术家的 Collection 帖
  只有带登录 cookie 的站内搜索看得到（无 cookie 时 `/search/` 返回 403）；没有 cookie 就跳过它并保留
  Google 外链，不把「查不到」写成「站上没有」。

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
  不同製作商记「不一致」交人处理——`K M Produce` 出 ケイ・エム・プロデュース 与 スクープ，那是一个
  账本名底下混了两家。
- 番号页 404 是那一页的事，不是这家厂牌查不到。印证只能靠跨前缀，但顶替 404 要靠同前缀：`code_groups`
  因此一个前缀一组、组内最多 `--depth`（默认 3）个，组内第二、三个不参与印证、只在前一个取不到时接手。
  第一版少了这一层，`Alice JAPAN` 被 `DVAJ-185` 一页 404 判成「未取得」，而 `DVAJ-495` 直接给出
  `アリスJAPAN`。反过来说，一个厂牌所有前缀的多个番号都 404 时，先怀疑账本而不是 javbus：那批英文
  文件名、韩国演员的片子被刮削器套上了同前缀的 JAV 厂牌名（`Kichu`／CHU、`Crystal Eizo`／HA），
  查不到是因为那个厂牌名本来就不属于这些片子。
- 「搜不到就去 Google 加 `公式`／`official`」这条路目前未取得：内置 WebSearch 只回美国过滤结果，
  `CHU-101 AV メーカー 公式` 返回航空公司与收缩包装机；脚本化爬搜索引擎撞不绕过机器人识别的门槛。
  javbus `/search/` 只给模糊前后缀命中，javdatabase `/movies/<code>/` 对这几个番号全 404。要走这条路
  得先有一个能用的搜索出口，别再重试同一组工具。
- AV 厂牌 Logo 的来源是厂牌自己的社交账号头像：社交头像天然是正方形且由品牌本人发布。取证顺序是
  handle → `unavatar.io` 解析出平台 CDN 真实地址 → 从 CDN 下载 → 实测，unavatar 只用于解析地址，
  provenance 两者都记（`scripts/fetch_studio_avatar_candidates.py`）。候选使用内容寻址缓存、SHA-256、
  同厂牌感知哈希和跨厂牌精确重复门槛；同图缩放或重编码记 unchanged，上游视觉真变化才重新进入 `/review`。
  无 handle、无图片、unchanged 和 duplicate 只写健康报告，不占人工队列。r18.dev 详情 JSON 只有
  `maker.name`／`label.name` 和作品封面，没有 Logo 资源，已排除。
- `pbs.twimg.com` 的尺寸后缀不是「有这么大」的证据。无后缀的那一份是上传原图（最大档），带后缀的地址在
  原图更小时返回的仍是原图——`セレブの友` 的 `_400x400` 和无后缀都是 242×242，而 unavatar 给的偏偏是
  `_200x200`（8068 B vs 12302 B）。所以一律从无后缀原图起、按 `peach.social_links.twimg_tiers` 的档位往下
  退（旧头像有过只剩缩略图的），`resolved_url` 记实际取到的那一档，全档缺失才算取图失败。厂牌 Logo
  （`fetch_studio_avatar_candidates.py`）与演员社媒头像（`harvest_social_avatars.py`）共用这一份判据。
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
  部分——域名由厂牌名推出来时这两者永远互相包含，那样写会把整类真站判成回显。
- 判成「没有官网」之前先分清是站点的回答还是链路的抖动，并且把每次尝试的理由都留下。
  `www.naturalhigh.co.jp` 第一次 `ReadTimeout`、同一地址随后 200 且标题正是厂牌名；一次抖动写成
  `未取得`，下游会把这个空结论当成事实。`probe` 因此只对传输层异常按 `page_cache.Site` 的口径重试
  （`retries=2, backoff=2.0`），HTTP 状态码是站点的回答，不重试。同理，`未取得` 的行不能只留最后一次
  尝试的理由——`SOD Create` 曾只剩一句 `取不到：ConnectError`，而真正有信息的那次
  （`www.sod.co.jp` → 200、标题 `SOFT ON DEMAND`）已被覆盖，人看到复核件时无从判断；现在候选判词按
  顺序拼成证据链写进 `note`，只有确认的行才留单条理由。
- 作品数少的厂牌不等于不用补链接。`--min-assets` 是为全量扫描定的阈值，账本里 BangBus、BangBros18
  各只有 1 部视频，OPPAI、MonstersOfCock 各 2 部，它们照样出现在厂牌页那个 160px 大位上。要定点补时走
  `--only <canonical_name>...`：指名就不看作品数，名字对不上直接失败而不是静默跳过。
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
  一道内容比例闸门（`link_marks.MAX_CONTENT_ASPECT`），宽扁字标不参加小圆标的竞选——它属于厂牌页那个
  大 logo 位（`/logo`）。同一个品牌在两个位置用两份资产不是不一致，是两个位置本来就要两种东西。
- 过闸门后再分两条通道：成品方形图标（threads 那枚黑底圆角白字）原样放行，圆由 CSS 的
  `.entitylinkicon` 裁，服务端再画一次只会把人家设计好的底色换掉；透明单色字形才做「品牌色圆底 +
  白色主体」。
- 厂牌标识按位置分 icon / logo 两份，但只在真的有两份时才分岔。`/logo?studio=X` 的可选 `variant`：
  `icon` 先找 `<safe>.icon.img`、`logo` 先找 `<safe>.logo.img`，都回落到既有的 `<safe>.img`；不带参数与
  加这个参数之前完全一致，认不出的值也按不带处理。页面上小地方（来源角标、筛选片、身份格、卡片徽标）
  取 `icon`，厂牌页那个 160 px 大位取 `logo`；宽条字标仍按 `peach.images.pad_to_square` 补成方图。
  129 个厂牌里只有 42 个有图、其中 17 个是 `normalize_studio_logos.py` 补白过的字标，所以绝大多数厂牌
  两个位置拿到的仍是同一张。
- 补方形小标要借 `link_marks` 的内容比闸门，但不能借它的尺寸下限。`MIN_DESIGNED_SIZE=96` 是为
  `/link-mark` 那种 128 px 圆标定的；JAV 厂牌站的 favicon 普遍只有 32×32 或 64×64，直接套 `render_mark`
  会把 HEYZO、Idea Pocket、MOODYZ、Prestige、Wanz Factory、Tameike Goro 六个全退掉，还在复核件上记成
  「仍是字标」——判错的结论比没有结论更糟，因为没人会再去查。所以 `scripts/harvest_studio_icons.py`
  只借真正表达 icon／字标之分的 `content_aspect` 与 `MAX_CONTENT_ASPECT`，尺寸另设 `MIN_SHORT_EDGE=32`
  （要顶的位置本来就只有 28～32 px）、像素原样不放大，`MIN_DESIGNED_SIZE` 不要为这个调用方去动。
- 判词分三档、对应三种不同的下一步：`未取得`（一份字节都没取回，`Fetcher` 自己数取回几份才判得出来）、
  `只有小图标`（FC2 全站只有 16×16，该去找更大的资产）、`仍是字标`。`best_mark` 只回结果不回理由，
  退回原因由 `SquareMark` 就地记下，否则复核件上只剩一个空判词。过闸门也不等于适合：某批七个通过的
  候选六个内容比在 1.00～1.15，Fitch 是 1.84——它其实是「Fitch + 标语」的字标，只是恰好压在 2.2 以下，
  所以 `studio-icons-<日期>.csv` 带 `content_aspect` 列，接近上限的行要人眼看过接触表再定。
- 反色圆标的锯齿有三层成因，少修一层都还是毛的：遮罩用了 `alpha >= 128` 的二值化（把源图自带的抗锯齿
  中间值一刀砍光）、二值图在源分辨率 48×48 上生成再拉到 64（把台阶一起放大）、字形没有与圆做
  `composite`（白像素溢出圆外，圆边被啃出缺口）。现在 alpha 原样当连续遮罩，整套合成在 8 倍超采样画布上
  做完再一次性 LANCZOS 缩下来，成品尺寸 64 → 128（容器 32 px CSS，3x 屏要 96 px）。改了取图规则或合成
  方式必须同时加 `link_marks.RENDER_VERSION`：缓存保鲜期是 30 天，不换键的话代码换了用户看到的仍是旧那张。

## 缓存与重试

- 整页 HTML 缓存与限速走 `peach.page_cache.Site`（按 URL sha1 落盘，`cookies` 用来带过年龄门）。它原先
  长在 `harvest_directory_links.py` 里，厂牌名回查是第二个用户，已上提到 `src/peach/`。采集脚本的判据
  改一行就要重跑，缓存在手才能让重跑走离线数据、不再打外站。
- 退让重试也在这一层：经代理取 javdatabase 实测约三次里有一次 TLS `UNEXPECTED_EOF`，一次抖动打死整批是
  这个项目犯过两回的错，所以 `Site` 自己重试传输错误（默认 2 次、`backoff` 递增），采集脚本不必各写
  一遍。HTTP 状态码不重试——404 重试三次仍是 404，只是白花三倍流量。
- 解析用的固定件必须是抓回来的那份 HTML。javdatabase 的资料行真身是
  `<b>JP:</b> 涼森れむ  - <b>Alt:</b> Iwatani Shiki, …<br>`，第一版按记忆写成 `JP: 名字`，正则被紧跟的
  `</b>` 顶掉，测试全绿而线上一个日文名、一个旧艺名都没采到，只回罗马字。照着记忆重画的固定件只能证明
  代码和记忆一致。
