# 身份、来源与标识采集

本文件保存「从外部站点取得身份与标识」这件事的判据细节：脚本分工、实测反例、判词含义和不能走的路。
`docs/HANDOFF.md` 只留一句话的边界并指到这里；采集本身的限流、续跑与流量预算见
`.claude/skills/peach-batch-jobs/SKILL.md`，参考产品证据的登记方式见 `.claude/skills/peach-reference-evidence/SKILL.md`。

采集脚本一律只产出复核 CSV。写 `entity.canonical_name`、`asset.studio`、`entity_link` 或头像字节
都是另一次授权，判据见 `.claude/skills/peach-ledger-write/SKILL.md`。

**没有哪个来源是绝对的**，javdb、laoshi、jae、R18 都只是参考，各带自己的可信度：名录站抄来的
社媒账号可能是三年前的旧号，资料页的名字可能是转载渠道改过的。同一条事实由两个互不相干的来源
给出才是最强的证据，只有一个来源说的一律当候选，冲突时不按站名分高低——按这条事实本身还能不能
另找一个来源印证。已经进账本的那一侧也不例外：它当初也只是某个来源的一次判定。

具体的例子：**判 X 账号是不是本人官方号，粉丝量是第一道筛子。** 官方号的粉丝量不会太少，
`matumoto_arrows` 这种数量级明显偏低的就该疑。2026-09-04 实测两例——松本一香账本里的
`MatuMoto_Ich1ka` 才是官方，javdb 给的 `matumoto_arrows` 驳回；铃村爱里反过来，javdb 给的
`airi_mgr` 在活、账本原有的 `naxsuzumura` 已疑似失效，按 javdb 那条装入。冲突不能一刀切成
「以账本为准」或「以新来源为准」。

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
- 上游名字里的零宽字符在 `canonicalize_entity_name` 一处剥掉，不在各脚本里各修一遍。
  `str.strip()` 不认它们是空白，`normalized_name` 于是带着一个看不见的字符：界面上和普通名字
  一模一样，但 `upsert_asset_entity` 按 `normalized_name` 找不到已有实体，同一个人存成两条，
  按名字搜也一个都搜不到。剥 U+200B／U+200C／U+2060／U+FEFF；**U+200D 不剥**，emoji 的家庭与
  职业序列靠它连字，剥掉会把创作者名字里的一个字形拆成两三个。账本里的两个存量
  （performer 7786 的别名、creator 7513 的规范名）已清，备份 `ledger.pre-zero-width-names-20260904.db`。

## 番号目录、创作者与水印

- 番号目录被投影成创作者时判据只能是文件级证据而不是名字形态：唯一可靠的区分是目录内媒体文件名是否
  解析出同一个番号（`scripts/audit_code_creators.py`），存疑一律留复核 CSV。
- 画质前缀（`HD`／`FHD`／`4K`／`1080P`）和版本后缀（`-C`／`-CH`／`-UC`／`-SUB`）不是番号的一部分，
  提取器必须先剥这两层再匹配；界面把版本语义投影成「中字」「无码」「无码破解」，原始 `name`／`code`
  留给文件操作。缺连字符的紧凑 code 只有同时具备片商、发行日或 performer／studio／series 实体证据才恢复。
- 来源返回的番号必须和查询的番号比对过才算命中。javbus 一侧是拿番号做关键词搜索取首个结果，搜不到就
  返回近似的别人（`SA-104 → AVSA-104`、`CHU-101 → CHUC-101`、`AR-301 → STAR-3016`），2026-09-02 实测
  68 次匹配 58 次番号根本不对，整个 `B:\MVP\MIB\`（韩国内容）因此被写上日本厂牌、系列和标题，还靠这些
  假证据升级成 JAV。判据是 `catalog_rules.same_release_code()`，它容忍片商数字前缀、DMM 的 `h_` 标记、
  补零和重制尾字母这些良性差异；来源没给 id 的不拦（缺证据不是反证）。
- 同一部作品有两种番号写法，账本存哪种不代表来源索引哪种。`259LUXU-1642` 的三位数字前缀标的是 DMM 上的
  发行方，不属于作品身份，来源站各只收其中一种写法；`catalog_rules.code_query_variants()` 在两种写法间
  回退，评审键始终用账本的规范写法。去前缀总是安全的（只是丢掉本来就有的一段），补前缀要凭空填三位数字，
  只对 `MAKER_NUMBER_PREFIX` 登记过的字母段做，新增一行之前先在账本里确认该字母段只属于一个发行方。
- 创作者是频道主而不是出镜者：文件名里可建创作者的只有 `RT_@X - 正文…`、明确标注的 `女主@X` 和正文里的
  中文名；末尾成串裸 `@A @B @C` 是互推，`📷：@X` 是摄影师，都不建。
- 发行平台既不是厂牌也不是创作者。FC2、myfans 这类是卖东西的地方，站上有实际卖主（出品者）的那个账号才是
  creator；平台本身只能当来源／平台实体，链接按 `catalog` 登记，不给它找「厂牌官网」——那条路对它本来就不
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
- 可用来源实测结论：r18.dev、av-wiki.net、Gfriends 可用；javlibrary、missav、xslist 被
  Cloudflare 拦，njav 有验证墙，jav321 无独立女优字段。被 Cloudflare 拦的站一律放弃，不绕过机器人检测。
  javdb.com 抓得到，但它自己按出口 IP 封速率（2026-09-04 封 3～7 日），只能小批量慢跑，见下文。
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
- **jae.tokyo 的女优名录是第三个来源**（用户 2026-09-04 指定，同一站的厂牌名录见下一节）。三届的资料页
  各不相同：2014 是 `jae2014/actress/NNN.html`，社媒和博客混在正文的 `<a>` 里；2015 是
  `jae2015/actress.html` 的 `offActress` 弹层，`actressLinkBtn` 一个按钮一条链接；2017 是
  `jae2017/actress/NNN.html`，人像在 `img_area`、链接在 `link_area`。391 页跑一遍，命中账本 145 人。
- **`jae2014/*` 直连会被重置**（`WinError 10054`），所以 jae 进了 `PROXY_SOURCES`；另两届直连能通，但同
  一个来源不分届走两套出口没有意义。
- **注释里的链接不算这个人的。** AIKA 那页 2017 的 HTML 注释里躺着 園田みおん 的博客和 神咲詩織 的
  Instagram——上一届的模板被复制过来注掉了。按 `<a>` 硬取会把三个人的账号装到一个人头上，解析前先剥注释。
- **页面写明是博客的就按博客算，不看主机名。** `classify()` 只认 `BLOG_HOSTS`，而
  `alicejapan.co.jp` 的子域、`plaza.rakuten.co.jp`、`takasyo.blog.jp` 都是本人博客却不在名单里；页面上
  那行「公式ブログ」比主机名更接近事实。标签照账本里现有那 23 条写「博客」，页面另外点出博客名时
  （`公式ブログ「旬の果実」`）才带上那个名字，`オフィシャルブログ` 这类泛称原样落进去会让同一件东西在
  界面上出现三种写法（`harvest_directory_links.owned_link`）。
- **主机名一律小写。** jae 的资料页上写着 `https://Instagram.com/…`，`entity_link` 的 UNIQUE 只认字面，
  照抄进去就是同一个账号的第二条记录（`social_links.canonical_url`）。路径和 handle 不动——X 的 handle
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
  这种账号当本人账号挂着，验活也是「活」——它确实活着，只是不是这个人的。证据里标一句不够：
  `installable()` 只看 verdict 和 alive，标注留在证据里照样会装进账本，jae 8 条、javdb 3 条
  这样的链接就是这么进去的。判据落在 `probe_rows`（`FAN_ACCOUNT`），命中就降级成 `应援账号`
  这个自己的判定。名录型来源不核实社媒归属，这一道只能自己做。已经装进去的 11 条于
  2026-09-04 删除（备份 `ledger.pre-fan-account-removal-20260904.db`）。
- **javdb.com 是按名字进的来源，不是能翻的名录。** 站上没有可枚举的女优列表，入口是账本里的名字：
  逐个写法搜 `search?f=actor&q=`，结果卡片的 `title` 一栏就是这个人在站上的全部写法，不点进去就能判
  身份。名字链要整条搜完再放弃——账本的规范名多是简体（`三上悠亚`），javdb 上是 `三上悠亜`／`三上悠亞`，
  `name_key()` 不做简繁转换，只搜规范名一个都搜不到（`harvest_directory_links.collect_javdb`）。
- **同名两条记录不取第一个。** 同一位女优在站上常有「有碼」「無碼」两条，搜索结果把两条都给出来；
  两页都进判定，撞上的账号会落成 `conflict` 进复核表。取第一个是默默替用户挑了一位。
- **一部分资料页要登录，回的是登入页而不是 401。** 不注册账号，那一页记一行「未取得」并写明是谁——
  「搜过、站上没有这个人」「搜到了但要登录」「没搜」是三件事，不分开写下一轮还得重搜一遍。
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
  来源下限不许压，撞 403 仍然整个来源收工，不在封禁期里换着节点连打——那是拿多个出口凑一个超速
  批次，等于用另一种方式压掉下限。本机在 Clash 留了 `🎬 JavDB` 策略组，`javdb.com`、`jdbstatic.com`、
  `jdbimgs.com` 三条 `DOMAIN-SUFFIX` 指向它，换出口不动脚本；脚本经系统代理出网
  （`Site` 的 `via_proxy` 走 `httpx(trust_env=True)`），策略组一切换下一轮就生效。
- **javdb 的限额规律与自己的速度上限。** 那一轮的时间线（缓存 mtime）：03:22:01 起 8 分钟取到
  124 页，中位间隔 1.23 秒、最快 0.76 秒，逐分钟成功数 44 / 15 / 6 / 0 / 0 / 0 / 7 / 50 / 2，
  第 124 页之后整站每条路径都回 403。可读出三件事：额度按出口 IP 累计而不是按路径；封之前
  不发 `Retry-After`、不降速、不给验证码，中间那两次 68 秒和 260 秒的停顿也没换回额度；
  触发点在每分钟 40～50 页这个量级。所以规则是硬编码的来源下限而不是命令行默认值——
  `harvest_directory_links.SOURCE_INTERVAL` 给 javdb 定 5.0 秒（每分钟 12 页，约为触发速率的
  四分之一），`--interval` 只能往上加、压不过它。
- **撞上 403／429／503 就整个来源收工。** `Site.request()` 对状态码不重试，封了之后接着翻
  只会每位女优每个名字写法各撞一次 403：那一轮实测又跑了好几分钟，一条有用的都没产出。
  `rate_limited()` 命中即 `break`，已取到的页照常进判定，不丢这一轮的成果。
  封禁期过后调大 `--limit` 接着跑，缓存命中不花请求，不需要断点参数。
- **javdb 的圆头像 250×250，进不了头像竞赛。** 44 条人像候选里只有 1 人（立花美凉）账本里还没有头像，
  250×250 也过不了自动线（正方需 ≥400）。为这一条把 `jae` 路线泛化成通用人像路线不值当，
  `harvest_social_avatars.py` 暂不接这个来源。

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
  少了这一层，`Alice JAPAN` 就会被 `DVAJ-185` 一页 404 判成「未取得」，而 `DVAJ-495` 直接给出
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
- 页面上没有的信息，判据里补不出来，只能由用户确认。`SOD Create` 的官网就是母公司站
  `www.sod.co.jp`（200、成人站、标题 `SOFT ON DEMAND（ソフト・オン・デマンド）`），而 `SOD Create`
  这个串整站不出现——通用判据到此只能判「标题与正文都没有厂牌名」，缺的那条是「这个厂牌属于哪家公司」。
  放宽通用判据去接住它，等于把 `hunter.com`、`bazooka.com`、`madonna.com` 一起放进来。所以走
  `harvest_studio_sites.CONFIRMED_SITES`：一行一个厂牌，写清地址与用户确认的日期和理由，它只替掉最后
  那道「页面得自述厂牌名」，状态码、空壳、停放页／自述不可用、域名回显四道照旧要过——确认的是「这个地址
  属于这家公司」，不是「这个地址此刻返回什么都算数」。确认地址排在所有推导候选前面，命中就不再走那串死域名。
- 作品数少的厂牌不等于不用补链接。`--min-assets` 是为全量扫描定的阈值，账本里 BangBus、BangBros18
  各只有 1 部视频，OPPAI、MonstersOfCock 各 2 部，它们照样出现在厂牌页那个 160px 大位上。要定点补时走
  `--only <canonical_name>...`：指名就不看作品数，名字对不上直接失败而不是静默跳过。
- FC2-PPV 的「只有小图标」已查到底，剩下的是取舍而不是取证：`adult.contents.fc2.com`、
  `contents.fc2.com`、`fc2.com/en/`、`video.fc2.com` 四个主机声明的都是同一份
  `static.fc2.com/share/image/favicon.ico`（16×16，内容 14×14／比 1.00，独角兽头才是真正的标识），
  页面里引用的更大资产全是横向字标（189×68／比 3.05、690×68／比 11.20），本来就属于 `logo` 位。唯一
  又方又大的是 `id.fc2.com/apple-touch-icon.png`（114×114／比 1.00），两道闸门都过，但它是「独角兽 +
  FC2 文字」的纵向锁定图，缩到 28px 文字糊成一团，且挂在 FC2 ID 而不是 PPV 市场的主机上——是「过闸门
  不等于合适」那一类。`blog.fc2.com`、`live.fc2.com`、`static.fc2.com` 上也没有单独的大尺寸独角兽资产
  （`apple-touch-icon`、`favicon-192`、`icon.png` 全 404）。所以这不是「发现流程没找对」，是站上确实没有。
- FC2 的两个位置各用一份非官网来源，两个地址都由用户 2026-09-03 当场指定，取回时间同日：
  `icon` 位是 `storage.googleapis.com/datanyze-data//technologies/8ef39cbce34aece41d279b6e8e7dbb77aea3086e.png`
  （400×400 RGBA、内容比 1.07、纯红色独角兽没有文字，sha256 `ddaa3216…f449462`、40901 B），已写进
  `site_icons.HOST_OVERRIDES` 的 `fc2.com`。服务端回的 content-type 是 `application/octet-stream`，
  解得开靠 `link_marks.decode` 里 PIL 的嗅探——按 content-type 决定要不要解会把这一枚整个丢掉，
  `test_an_octet_stream_png_is_still_a_png` 守这条。`logo` 位是
  `images.seeklogo.com/logo-png/42/1/fc2-logo-png_seeklogo-429409.png`（600×600 P 模式、独角兽 +「FC2」
  文字、内容比 3.02，sha256 `6911574c…6c6f1b7`、8916 B），写进 `harvest_studio_icons.LOGO_SOURCES` 而不是
  `HOST_OVERRIDES`：那张表管「按主机发现图标」的例外，这一份管「这个厂牌的大字标在哪」，键的含义和取用
  位置都不同。曾用 App Store 的「FC2動画」商店图标（512×512、内容比 1.00、sha256 `ac318e2b…c99538`），
  2026-09-03 被用户否决——背景多了胶片图案；地址仍可复现（iTunes Lookup API），但不要再拿回来用。
  没采信的来源与原因：seeklogo 同站那份 2000×662 是字标不用，用户指定的 429409 这份是 600×600 方形锁定图、
  装 `logo` 位；Wikimedia 的 `File:FC2_Logo.jpg` 是同名的另一家（Fiction Collective Two）、
  simpleicons／vectorlogo.zone／iconduck 全 404 或已死、brandfetch 与 clearbit 要凭据或连不上、
  Google／DuckDuckGo 的 favicon 服务只回 16×16、`unavatar.io` 拿到的三个 FC2 账号头像是鸭子和房子的
  吉祥物画不是独角兽、Google Play 那几个 FC2 应用图标里独角兽只是角标。

- 指定标识来源按**形状**分两张表，不是按画质。三个取用位（`.entityportrait`、`.idface`、筛选片）
  都是 `object-fit:cover` 的方框，宽扁字标原样装进去只剩正中间几个字母。所以
  `LOGO_SOURCES` 是原样装的方标（`MIN_LOGO_SHORT_EDGE=96`，低于它就是缩略图），
  `WORDMARK_SOURCES` 是过 `images.bake_square` 烤成方图后两位共用的宽扁字标，下限同 icon 位的 32。
  拿 406×86 去撞 96 那道闸门是判错了题：问题不在它小，在于它不该走原样装的那条路。
- 大不等于好。同一枚标识的大尺寸版常是带底色的横幅——MGStage 首页轮播位的 `top/jackson.jpg`
  是 400×80 洋红底，烤方后补出两大块洋红，标识只剩正中一条；通用位 `jackson.gif` 160×54
  白底纯字标，小四倍却是对的那一张。两份都烤出来看过再选，别按像素数挑。
- 发行平台自己的厂牌名录是官方字标的广度来源：MGStage `/ppv/makers.php` 按 50 音分十一页，
  共 351 家，规格统一 180×54；`osusume` 是站方推荐位、和音节页整片重合，靠 slug 去重；
  50 音导航条自己也是 gif、和厂牌字标混在同一批 `<img>` 里，只能按文件名排掉；
  `【独占】` 是销售身份不是厂牌名的一部分。整站有年龄门，不带 `adc=1` 只回一张确认页。
- 名录给日文名、账本记罗马字，桥是文件名里的 slug。`harvest_mgstage_makers.py` 四路匹配：
  slug 归一相等、日文名相等、罗马字对上别名、唯一前缀候选（slug 是缩写时，如 `waap` 对
  `Waap Entertainment`）。**归一成空串必须当不可比**：纯日文名折掉非 ASCII 后都是空串，
  不排掉的话 351 家会全部对成同一家，复核件看着满满当当、一条都不能用——首轮探测报过 332 个
  「匹配」，实际 29 个。前缀候选比前三路弱，判据要写进复核件让人能分辨：`きらきらワイフ` 撞上的
  `kira*kira`、`おっぱいちゃん` 撞上的 `OPPAI` 都是另外两家真实厂牌。
- 351 对 29 的卡点在账本不在名录：129 个厂牌只有 16 条别名、几乎没有日文名，而同一家常以罗马字名
  与日文名各存一个实体（`Prestige` 5630 / `プレステージ` 8610），资产数与标识各挂一半。
  先补日文别名、再合并重复实体，同一份名录的覆盖面会一次性抬上去。

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
  取 `icon`，厂牌页那个 160 px 大位取 `logo`。129 个厂牌里只有 42 个有图、其中 17 个由
  `normalize_studio_logos.py` 补过方，所以绝大多数厂牌两个位置拿到的仍是同一张。
- **Logo 文件一律是不透明方图，页面三处一律 cover。** 边距和底色烤进文件，页面不再各自补救。
  唯一入口是 `peach.images.bake_square`，`classify_plate` 给出它据以分流的判定：
  - `mark`（有透明像素，如 PREMIUM 的全透明底蓝色字标）——按 alpha 外接框裁掉透明边，居中放到**白色
    不透明**方底上，内容占边长 `PLATE_CONTENT_RATIO`（0.76，四周各留约 12%），像素不缩放，出不透明 PNG。
  - `tile`（完全不透明，如 M's Video Group 400×400 黑底方块、Natural High 红底、Hon Naka 64×64 青底）——
    底色是设计的一部分：接近方形的原字节返回，长条按边缘主色补方（`pad_to_square`）。不刷白。
  写入侧只有两条路径，规则同一条：`harvest_studio_icons.py` 的 `install()` 落盘前烤，
  `normalize_studio_logos.py` 对历史文件回溯（目录下所有 `*.img`，含 `.icon.img`／`.logo.img`）。
  两者都幂等——烤出来的产物再跑一次不再有动作。女优头像等照片不走这条路径，不加白边。
  矢量标识（4 个 `image/svg+xml`：DarkRoomVR、TeamSkeetXReislin、TeenFidelity、VirtualTaboo）不栅格化，
  复核件上记 `vector` 原样留着——烤底按像素判透明和取外接框，矢量得先定目标尺寸再栅格，那是另一件事。
  真实目录的 dry-run 实测 27 个待改：26 个 `mark` 待烤白底（Attackers、PREMIUM、MOODYZ、HEYZO、
  Natural High、BangBus／BangBros18 各三份变体等），`pikpak.img` 116×68 是唯一的不透明长条待补方。
  已经是不透明方图的（M's Video Group 那类整块 tile）不进复核件。回溯真实目录需另行授权。
  页面三处取图位（品牌小圆片 `.brandpill .mk`、身份格 `.idface`、厂牌页 160 px 大位 `.entityportrait`）
  的 `img` 统一 `object-fit: cover` 铺满方框，不加 inset、不加 padding、不改 contain：文件已经带够边距，
  页面再补一层就在图自带的底之外多围出一圈框，而三处各自补救的结果必然互相不一致。占位底色
  （`#CFCFCF`、`#fff`、`--overlay-5`）与首字母回落只在取不到图时露出来。
- **没装标识的厂牌一个 `<img>` 都不输出。** 可用性随资料一起下发：`/api/tops` 的 `studios[].has_logo`、
  `/api/item` 的 `entity_refs.studio[].has_logo` 与 `has_studio_logo`（非规范厂牌只有扁平 `studio`
  字段，那格单独一个标志，漏了它那条路径会从「本来能取到图」退化成永远只显示首字母）、`/api/entity`
  厂牌页的 `has_logo`。判据是 `WebContract.has_logo()`：一次 `os.scandir` 出的目录索引
  （`logo_index()`，和封面的 `cover_index()` 同一个套路，TTL 90 秒，复核批准 `cache_bust()` 后立刻可见），
  落盘名统一走 `previews.logo_key`——取图、可用性判定和批准落地只能有一份规则，各写一遍正则的代价是
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
  地址——`web/app.js` 的 `entityFaceImg()`，所有取图位（顶栏圆头像 `.av .ring`、身份格人物位、
  共演者小圆框、资料页 160 px 大位、索引页格子、口味榜行、复核卡片那张脸、沉浸模式署名圈）
  经 `avatarInner()` 共用它，两样都取不到就一个 `<img>` 都不出，首字母垫底直接露出来。
  旧写法一个作品详情页实测 9 个 404（1 个厂牌实体图、4 个人物实体图、4 个头像），首页手机视口
  2 个，`/performers` 滚三屏 5 个，同样不带缓存头。
  `avatarInner()` 对缺席的 `has_image` 按「没图」处理：宽容缺席只会让下一个忘了挂标志的端点
  悄悄退回无条件出图，而这种退化在页面上看不出来——图照样显示，代价全在 404 里。
  端点挂标志用 `web_catalog` 的 `entity_ref()`（身份引用带上 `has_image`）和
  `attach_avatar_availability()`（一次批量取 `snapshot_path`，不逐行 N+1）；榜行这种
  `entity_id`／`representative_asset_id` 直接长在行上的形状，判据仍是同一对函数。
  两条判据形状不一样，不能混为一谈：
  - 实体图是纯粹的「在不在」。`avatar_root` 一次 `os.scandir` 出 casefold 索引
    （`avatar_root_index().entity_images`），落盘名统一走 `previews.entity_image_key`，
    kind 是名字的一部分——creator 的图写成 `performer-<id>.img` 是永远读不到的；认得的种类只有
    `previews.ENTITY_IMAGE_KINDS` 那几种。`.ct`、`.provenance.json`、`.face.json` 是边车，不算图。
  - 头像是按需生成的，「目录里没有」只说明还没裁过。所以 `has_avatar` = 已经裁好的 `<id>.jpg`
    **或** 印相还在盘上（同一个 `has_snapshot`）。把后者也判成没有，等于把「点一下就现裁一张」
    那条路永远关掉。生成中途的 `<id>.<格>.tmp.jpg` 不算数。剩下预测不了的 404 只有生成本身失败
    那一种（没有 ffmpeg、六格全黑），所以 `data-drop="self"` 兜底链一条都不能撤。
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
  「仍是字标」——判错的结论比没有结论更糟，因为没人会再去查。所以 `scripts/harvest_studio_icons.py`
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
- **字标补白**（用户 2026-09-03 定的口径：不是 icon 也可以装 icon，尽量不要落入无图）：方标一个都没做成、
  却取回过短边 ≥ `MIN_SHORT_EDGE` 的宽扁字标时，用 `peach.images.bake_square` 烤成方图装上，判词
  `字标补白`，`content_aspect` 照记（那个数就是「这枚其实是字标」的提示）。同一份方图再出一行
  `logo`（判词 `ok`）装进 `<safe>.logo.img`：不出这行大位会回落到 `<safe>.img`，BangBus 页顶上挂的就成了
  母品牌 BANGBROS。两位装的都是方图：页面三处取图位都是 cover 的方框，298×50 的宽条直接装上去只剩
  中间的「NG」两个字母。用户指定的 logo 来源做成时优先。留第一份而不是最大的一份：
  `best_mark` 的遍历顺序已经是「覆盖表 → 声明 → 根路径猜测」。BangBus（298×50／比 6.60）与 BangBros18
  （298×50／比 6.06）走的就是这条，来源是 `bangbros.com/websites` 服务端渲染进 HTML 的 `*_LOGO` 资产
  （注意 `/` 转义）。MonstersOfCock 那一页没有对应的 logo 资产，`site-api.project1service.com/v1/collections`
  只给照片 avatar/banner，频道页顶部那张 `assets/brand/1151/banners/…jpg` 是 1920×400 的照片横幅不是标识，
  `www.monstersofcock.com` 是同一套 Aylo 壳（favicon 同样是「1」、无 apple-touch-icon），所以它记
  **未取得**、继续回落现有的 `MonstersOfCock.img`，不用推测顶替。
- **展会名录**（用户 2026-09-04 指定 `jae.tokyo`，Japan Adult Expo 的参展厂牌名录）：2014／2015／2017
  三届各带一套厂商自己交的 logo，页面结构每届不同——2014 是 `exhibitor/` 里 `<li><a><h2>名字</h2>` 加
  `images/logo/*.jpg`（270×180，`alt` 不可靠），2015 是 `maker.html` 里 `offMaker` 弹层的
  `makerLogo`／`makerRightTitle`／`makerLinkBtn`（188×188），2017 是 `maker.html` 的 `alt` 加详情页
  `makaer/NNN.html` 的 `name_area` 与 `class="pop"` 官网链接（320×320）。2016 那届 `exhibition.html`
  只有图、HTML 里没有名字，认不出是谁家的，不取。211 条名录条目对上账本 26 家没有任何图的厂牌
  （名字对不上却是同一家的按厂牌自称对：名录里 `ムーディーズ` 写作 `MOODYZ`、`SODクリエイト` 写作
  `ソフト・オン・デマンド株式会社`、`Momotaro Eizo` 写作 `桃太郎映像出版`），同一家出现在多届时取像素
  最多的那一届，逐张在白底上看过认得出是哪家才写进 `LOGO_SOURCES`。
- **指定 logo 来源自己就是入场理由，小位从大位那张烤。** `harvest_targets()` 收三类：补白过的、有链接
  但没图的、有指定 logo 来源但没图的。第三类是为这 26 家开的——它们在账本里绝大多数连一条
  official／catalog 链接都没有，只按前两类收一条都收不到，`site_icons` 的发现流程也走不到它们，
  两个位置一直空着。`icon_from_logo()` 在小位
  自己没做成、大位的指定来源做成了时，把同一张过 `bake_square` 装进 `icon` 位。判「补没补白」看源图
  长宽比与 `images.MAX_ASPECT`（`ok` 恰好等于这一张一个像素都没动过），不看内容比：名录 2014 那届是
  整幅不透明的 jpg，`content_aspect` 对它一律回 0，分不出方图和长条。复核件的 `studio` 列改从
  `LOGO_SOURCE_NAMES` 取，没有链接的厂牌拿不到别的名字。
- **落盘名保留假名与汉字。** `previews.logo_key` 按 `\w` 归一，标点仍然变下划线，长度上限 60 不变。
  只留 `[A-Za-z0-9_-]` 的话，非 ASCII 的每个字符换一个下划线，名字里只剩「几个字」这一个信息：
  129 个厂牌撞成 12 组，`プレステージ` 与 `ムーディーズ` 同为 `______`、`シロウトTV` 与 `ラグジュTV`
  同为 `____TV`；撞了不报错，后装的那张盖掉先装的，PRESTIGE 的位置就挂上 MOODYZ 的牌子。
  已装的 60 张都是 ASCII 名，键一个都没变。
- **同一批详情页的官网链接照厂牌自称对回账本，逐条判 kind。** 211 条名录里 125 条带官网，按名字与别名
  （NFKC 归一、去掉空白与 `・.,'"()[]/&+*!?:-`）对上账本 33 家。目录站与配信平台不是官网：`mgstage.com`、
  `indies-av.co.jp`、`dmm.co.jp`、`fanza.com` 四个主机，以及路径里带 `/works/list/` 的按厂商筛出来的作品
  列表，都进 `catalog`——JET映像 那条指向 `mousouzoku-av.com`，而那个域名是妄想族自己的官网。母公司站内的
  厂牌页（`km-produce.com/l_06_bazooka.php`、`/million/`）算 official，它就是这个厂牌在网上唯一的门面；
  站内搜索串（`?s=OREA`）、配信站筛选列表（`ppv_advanced.php?`）、周边商品列表（`goods_list.php?`）和
  配信平台首页（`indies-av.co.jp/`，名录给桃太郎映像出版填的就是它）都不是这家的页面，不装。
  `entity_link` 的 UNIQUE 按 URL 字面判，`http://www.x.com/` 与 `https://x.com/` 装进去是同一家官网
  并排两条，所以还要自己按主机去重（Prestige、MOODYZ、Wanz Factory、kawaii、Fitch、OPPAI 六家因此不装）。
  剩 24 条过 `install_entity_links.py`，逐条探活后实装 20 条：BAZOOKA、DOC、million 三条 404，
  MARRION 超时，2014／2015 那两届的地址十年后有一部分已经不在了。
- 判词分档、每一档对应不同的下一步：`ok`、`字标补白`（可装，见上）、`只有小图标`（FC2 全站只有 16×16，
  该去找更大的资产）、`平台通用图标`（见上）、`仍是字标`、`未取得`（一份字节都没取回，`Fetcher` 自己数
  取回几份才判得出来）、`无官网链接`。只有前两档会被 `--install` 落盘。`best_mark` 只回结果不回理由，
  退回原因由 `SquareMark` 就地记下，否则复核件上只剩一个空判词。过闸门也不等于适合：某批七个通过的
  候选六个内容比在 1.00～1.15，Fitch 是 1.84——它其实是「Fitch + 标语」的字标，只是恰好压在 2.2 以下，
  所以 `studio-icons-<日期>.csv` 带 `content_aspect` 列，接近上限的行要人眼看过接触表再定。
- 反色圆标的锯齿有三层成因，少修一层都还是毛的：遮罩用了 `alpha >= 128` 的二值化（把源图自带的抗锯齿
  中间值一刀砍光）、二值图在源分辨率 48×48 上生成再拉到 64（把台阶一起放大）、字形没有与圆做
  `composite`（白像素溢出圆外，圆边被啃出缺口）。现在 alpha 原样当连续遮罩，整套合成在 8 倍超采样画布上
  做完再一次性 LANCZOS 缩下来，成品尺寸 64 → 128（容器 32 px CSS，3x 屏要 96 px）。改了取图规则或合成
  方式必须同时加 `link_marks.RENDER_VERSION`：缓存保鲜期是 30 天，不换键的话代码换了用户看到的仍是旧那张。

## 缓存与重试

- 整页 HTML 缓存与限速走 `peach.page_cache.Site`（按 URL sha1 落盘，`cookies` 用来带过年龄门）。它放在
  `src/peach/` 而不是某个采集脚本里：目录链接采集和厂牌名回查两个脚本都用它。采集脚本的判据
  改一行就要重跑，缓存在手才能让重跑走离线数据、不再打外站。
- 退让重试也在这一层：经代理取 javdatabase 实测约三次里有一次 TLS `UNEXPECTED_EOF`，一次抖动打死整批是
  这个项目犯过两回的错，所以 `Site` 自己重试传输错误（默认 2 次、`backoff` 递增），采集脚本不必各写
  一遍。HTTP 状态码不重试——404 重试三次仍是 404，只是白花三倍流量。
- 解析用的固定件必须是抓回来的那份 HTML。javdatabase 的资料行真身是
  `<b>JP:</b> 涼森れむ  - <b>Alt:</b> Iwatani Shiki, …<br>`，按记忆写成 `JP: 名字` 的固定件会让正则被紧跟的
  `</b>` 顶掉：测试全绿而线上一个日文名、一个旧艺名都没采到，只回罗马字。照着记忆重画的固定件只能证明
  代码和记忆一致。
