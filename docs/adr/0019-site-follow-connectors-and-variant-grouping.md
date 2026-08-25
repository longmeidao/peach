# ADR-0019：站点追更连接器与变体分组

- 状态：Accepted
- 日期：2026-08-25
- 关系：细化并扩展 [ADR-0007](0007-online-follow-feed-adapter.md)

## 背景

ADR-0007 定下第一类追更连接器复用 RSS/Atom，并把「只发现候选、不写真相」立成边界。
真正要追的七个来源里，**没有一个提供可用的 RSS/Atom**——f95zone 的
`/threads/{id}/index.rss` 实测返回 `The requested page cannot be represented in this
format.`，其余站点根本没有 feed 入口。继续等 feed 等于这条能力永远不落地。

同时，只把抓到的条目按时间平铺是不够的：实测 rule34video 上 LazyProcrastinator 的
24 条记录里，`Fiona - Paizuri` 与 `Fiona - Paizuri (Nude)` 是同一个作品的两个版本，
f95 线程的 9 条回复是同一个作品的历次动态，同一作品还会同时出现在 rule34video 和
rule34.xxx 上。不区分这三种关系，界面就只是一堆重复条目。

## 决策

### 来源接入

- 每个站点一个连接器，共用 `FollowCandidate` DTO 与 `_BaseConnector` 的超时、有界读取、
  条件请求和状态判定。站点专用选择器留在各自的连接器里，**不塞进通用 feed adapter**
  （ADR-0007 已否决那条路）。
- 联网只在显式调用时发生：CLI 的 `peach follow check` 和 Web 的
  `POST /api/follow/check`。服务启动、健康检查、普通浏览和首页「换一批」都不联网。
- **不绕过任何机器人验证。** rule34.xxx 网页版挂着 Cloudflare Turnstile，因此只走官方
  dapi 并要求账号自己的 API key；simpcity.cr 挂着 DDoS-Guard 浏览器质询，连接器只登记
  不可用并原样报出原因，不做质询求解。
- 凭据从 `peach-data/secrets/follow/<provider>.json` 读，只进请求头或查询参数，
  **绝不进快照、日志、`request_url` 或 ledger**。dapi 只接受查询参数，因此记录下来的是
  脱敏副本。

### 变体分组

条目之间只有三种关系，判据各不相同：

| 关系 | 判据 | 例子 |
| --- | --- | --- |
| 同作品的另一版本（alt/WIP） | 标题里的变体标记 | `Fiona - Paizuri (Nude)` |
| 同作品的另一次动态 | 来源语义为 `release` | f95 线程的 9 条回复 |
| 跨站的同一作品 | 归一化标题相同、来源不同 | rule34video ↔ rule34.xxx |

- `semantics` 区分两类来源：`work`（rule34、kemono——每条是独立作品，`v2` 判为 alt）
  与 `release`（f95、simpcity——每条是同一作品的一次发布，版本从标题摘出并排除在分组键外）。
- 来源自己声明的关系优先于标题判据：booru 的 `parent_id` 用并查集把父子帖连成一个分量，
  统一取分量内最小的 `release_key`，**不会被标题判据拆散**。
- 判据保守，宁可少合并：括号只在命中已知标记、创作者别名或版本模式时才剥离；标题末尾的
  裸数字算作品序号而不是版本；`work` 语义下同一来源出现两个都没有变体标记的 main 就整组
  按 `external_id` 拆开。

### 精度与凭据要照实说

- rule34video 列表页只给「1 周前」。换算值写成 `published_precision='approximate'`，
  界面显示为「约 …」，**不冒充站点给出的精确发布时间**。
- f95zone 的发现不需要 cookies（实测 `/threads/{id}/latest` 无凭据完整返回回复正文与
  外链），但取媒体需要——附件和 `masked` 跳转都要会话，正文里就写着
  `You must be registered to see the links`。候选因此带 `media_needs_credential`，
  下载动作必须先看这个标志，不能拿 403 的附件冒充「已保存」。

### 写入边界

`follow_item` 的 `status` 停在 `new`/`seen` 时不影响任何 asset。只有
`save_asset(confirm=True)` 写真相，且只 INSERT 一条 `location='online'` 的新 asset 并
回填 `asset_id`，不改写既有真相字段，也不下载媒体。重复抓到不覆盖用户已经做过的判断。

## 站点实测证据（2026-08-25）

按 `peach-reference-evidence` 登记。全部为当日实测的一次性抓取结论，站点改版后需重新取证。

| 来源 | 入口 | 凭据 | 结论 |
| --- | --- | --- | --- |
| kemono.cr / coomer.st / pawchive.pw | `/api/v1/{service}/user/{id}/posts` | 无 | 默认 `Accept` 回 403，响应体写明抓取应带 `Accept: text/css`；kemono 回 `{"posts": […]}`，pawchive 回裸列表 |
| rule34video.com | `/models/{slug}/` | 无 | KVS 引擎无公开 API；`.time` 是时长、`.added` 是相对提交时间、`[data-preview]` 是预览片 |
| rule34.xxx | `https://api.rule34.xxx/index.php?page=dapi&s=post&q=index` | user_id + api_key | 网页版挂 Turnstile；无 key 时 API 返回 `Missing authentication`；booru 帖子无标题，`parent_id` 是站点维护的变体关系 |
| f95zone.to | `/threads/{id}/latest` + `latest_alpha/latest_data.php` | 发现不需要，取媒体需要 | 主贴版本号滞后于回复；`index.rss` 返回「无法以该格式呈现」；`h1.p-title-value` 去掉 `.label` 才是线程标题 |
| simpcity.cr | — | — | DDoS-Guard 浏览器质询，**未取得**可用入口 |

lazyp 的跨站身份链已核实：ledger `entity` 6405 `LazyProcrast` ← pixiv 用户 30917150
← kemono `fanbox/30917150` `LazyProcrastinator`；rule34video `/models/lazyprocrastinator/`；
f95zone 线程 50685，`creator` 字段写作 `LazyProcrastinator/LazyProcrast`。
同一个人在 rule34video 上就有 `[Lazyprocrastinator]`、`(Lazyprocastinator)`、
`[LazyProcrast]` 三种拼法，所以别名剥离必须模糊匹配。

## 拒绝方案

- 求解 Turnstile / DDoS-Guard 质询，或用无头浏览器绕过机器人验证。
- 把站点专用 HTML 规则塞进 `FeedAdapter`。
- 抓取结果直接写 ledger 真相字段或自动升级为 `approved`。
- 靠标题相似度做跨站合并的模糊匹配——两个作品并成一张卡片比多出一张卡片糟糕得多，
  所以只在归一化标题**完全相同**时才判为同一作品。
- 用相对时间换算值冒充精确发布时间。

## 后果

七个来源里五个可用、一个需要用户的 API key、一个被机器人验证挡住并如实标记。追更从
「有 adapter 但没有源」变成可以逐日使用的界面。代价是每个站点的 HTML/JSON 结构成了
Peach 的维护面：连接器解析不出任何条目时一律报错而不是报「本次没有更新」，站点改版
因此会立刻暴露，而不是静默变成一个永远没有新内容的追更页。
