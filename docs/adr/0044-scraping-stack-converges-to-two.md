# ADR-0044：刮削栈收敛：官方站自写、社区站 amane、Javinizer-Go 退场

- 状态：Accepted
- 日期：2026-09-23

## 背景

到 2026-09-22 为止，番号资料一共有三套取法并存：Peach 自写的解析器（r18.dev、一本道、FC2 与
两处存档站、AVBase、JavBus、javdb、Seesaa）；amane 桥子进程（fc2club、freejavbt、airav、avsox，
ADR-0043）；Javinizer-Go v1.5.x 单来源 JSON CLI（`scripts/scrape_codes.py` 的 `--profile` 组合，
问 dmm、libredmm、mgstage、javlibrary、jav321、tokyohot、aventertainment、caribbeancom、dlgetchu、
javstash）。三套各有自己的凭据、限流、冷却与错误分档，同一个番号在采集任务和批量脚本里走的不是
同一条链：采集任务按 `metadata_routes` 分档短路，批量脚本按 Javinizer 的 scraper 组合逐家问到底。
Javinizer-Go 那一路还要求本机装一份特定大版本的二进制并单独维护 YAML 配置，账本里最后一批经它
写入的 provenance 停在 2026-09 上旬。

用户 2026-09-23 决定收敛到两套：官方与半官方站由 Peach 自己解析；社区站经 amane 桥；Javinizer-Go 退场。

## 决策

- **归属判据**：来源是发行方或发行方目录的镜像（r18.dev、一本道、FC2 商品页、fc2cmadb、JavArchive
  这类只对一个发行面负责的站）由 Peach 自写解析器持有，因为它们的字段就是账本真相字段的直接证据，
  形状变了要当天知道。转载、索引与聚合站（fc2club、freejavbt、airav、avsox 及其后继）经 amane 桥，
  Peach 只持有站名到 `SOURCE_SPECS` 的映射与字段翻译，不再为社区站写第二份 HTML 解析器。
- **一条链**：一个番号问谁、什么顺序、何时停只由 `metadata_routes` 决定；采集任务与
  `scripts/scrape_codes.py` 用同一份 `LibraryMetadataProvider`、同一套凭据、限流与冷却，
  `scrape_codes` 只保留批量、快照落盘、健康统计与字段候选排序。`--sources` 点名的来源限于链上能问的
  成员，点名即每家都问、不短路。
- **Javinizer-Go 退场**：删除子进程适配器、版本判定、二进制查找、`--binary`／`--config` 与所有以其
  scraper 组合命名的 profile。它曾问过的十个来源名留在 `metadata_policy.HISTORICAL_SOURCES` 与
  `SOURCE_SPECS`，只为结算（`chain_rank`）与复核页仍认得账本里 `javinizer:<站>:<字段>` 那一万多行
  provenance 的级别；当前链不向它们发请求。`javinizer:` 前缀是整条刮削链的 provenance 写法，不改写。
- **自写社区解析器逐站退场的验收条件**：AVBase、JavBus、javdb 三家的自写解析器暂留，任何一家改经
  amane 桥前必须在同一批番号上取到三条证据：桥给出的字段集合覆盖自写解析器当前给出的字段；命中率
  不低于自写（按 `metadata-source-health-*.csv` 的 `succeeded`／`attempted`）；被限流或封禁时的
  表现不差于自写（冷却写回同一份 `scraping_access` 记录、鉴权墙仍分到 `auth` 一档）。三条齐了写进
  `docs/SOURCING.md` 再删代码；缺一条写「未取得」，解析器留着。
- **封面层独立于资料来源**：`jav_cover_fetch`、`best_cover`、`verified_cover` 与它们的图源汇总不随
  资料链变化；`sources/metadata/javinizer-go/**` 下的旧快照只作离线证据继续被读取（`cover_url`、
  `content_id`、厂牌），不再有任何一条路往里写 Javinizer 形状的新快照——`scrape_codes` 写进同一目录
  的新快照 `provider` 记解析器名、`provider_version` 记 Peach 版本，`result` 形状不变。
- **不删磁盘**：旧快照与 `peach-data/tools/javinizer/**` 下的二进制不删，历史由 Git 与磁盘各自保存。

## 被否决的方案

- 保留 Javinizer-Go 作「官方站的第三份兜底」：它问的十个来源里，dmm 与 libredmm 已由 r18.dev 覆盖，
  mgstage 与 caribbeancom 尚无 Peach 解析器——但「尚无」的代价是再维护一份二进制、一份 YAML 与一套
  错误分档，而它最近一年在这些站上的命中都是靠登录态；需要时按本 ADR 的归属判据自写，不靠它续命。
- 把自写的 AVBase、JavBus、javdb 解析器与 Javinizer-Go 一起删掉：三家现在是有码与素人链的社区那一档，
  amane 桥对这三站的字段与命中率尚未按上面的验收条件量过，删了就是拿猜测顶替证据。
- 让 `scrape_codes` 保留自己的一套来源组合（profile）与采集任务并行：同一个番号两条链两种答案，
  复核页上无法解释「为什么批量给的和任务给的不同」。

## 后果

- 影响面：`src/peach/metadata.py`、`metadata_policy.py`、`metadata_routes.py`、`metadata_seesaa.py`、
  `scripts/scrape_codes.py`、对应测试与 `docs/REUSE.md`、`docs/SOURCING.md`。设置页没有 Javinizer-Go
  的卡片或 API，前端无改动。
- ADR-0006 把 Javinizer-Go 定为默认查询适配器、把 `REGISTERED_SOURCES` 定为登记位，ADR-0024 的复用表
  把它列为番号元数据的正式基础；两处由本 ADR 取代，登记位改为 `SOURCE_SPECS`，链的成员由
  `metadata_routes.ROUTES` 决定。
- `scrape_codes` 默认按番号内容类型走链并逐档短路，与采集任务同一判据；官方一档取齐必填标量后
  不再向社区站发请求，批量的社区站请求数因此下降，代价是官方答全的番号不再有社区候选并排比对——
  需要比对时用 `--sources` 点名。
