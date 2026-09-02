# Peach 产品待办

更新时间：2026-09-02。这里只记录尚未完成或只完成一部分的需求；运行数字以 `peach-data/state/job-status.md` 的自动区块为准。

## 已有骨架、尚未完成（6 项）

1. **寻找更好版本**：已经能逐条标记「高清 / 无水印 / 完整版」等目标；后续仍需相似内容匹配、候选去重、来源发现和人工替换确认。
2. **现代自适应播放**：Video.js、Range、统计面板和面向 115/PikPak 原生 MP4 的按需 HLS 清单已经上线；自适应码率、多路清单、快速首帧和来源层大块预取优化仍未完成。
3. **在线追更**：`src/peach/follow_providers.py` 登记的十一个来源（FANBOX、SubscribeStar、Patreon、Kemono、Pawchive、Coomer、Rule34Video、Rule34.xxx、Rule34 Paheal、F95zone、SimpCity）、WIP/alt/跨站重复判定、`follow_source`/`follow_item`、`peach follow`、看的 `/follow` 与管的 `/follow-manage` 两个页面已上线，writer 用 APScheduler 按设置自动轮询，在线资产可就地播放。仍缺的是下载落地（凭据、流量与磁盘预算未定，见 STATUS 下一批工作）和 simpcity 的可用入口（DDoS-Guard，未取得）。
4. **首尾帧出处与不完整候选**：已有受限 FFmpeg 首尾抽帧、Windows 内置 OCR、证据帧缓存、来源/Full version 候选和 `/review`；仍需决定全库批次范围，并把用户批准后的不完整版判断接到更好版本目标。
5. **厂牌 Logo 补齐与持续校验**：14 个已确认社交 handle 已有内容缓存、provenance、精确/感知哈希、质量与重复门槛及健康报告；仍有 72 个厂牌没有可信 handle，必须继续从官网/公开来源取证，不能猜账号。
6. **口味证据持续刷新**：ledger 已实时记录搜索、播放、高潮、喜欢/理由、不合口味和稍后看；浏览器历史现可用 SQLite 一致性副本增量进入私有源库，并生成不含 URL/标题的 creator/tag candidate 与聚合报告。旧 2026-08-13 原始包已确认不在 Windows 外置盘；仍需在 Mac 开启 iCloud Safari、完成首次导入，并把两端每周刷新装成系统计划任务。AI 结论不得直接改真相字段。

## 尚未实现（8 项）

1. AI Provider 的真实调用、能力协商、Credential Manager 凭据和候选审核 UI。
2. 剩余单一创作者风格板复核、无标签内容补标。
3. 缺时长资源补 probe 后再生成接触表。
4. PikPak 计费抽样与下载边缘质量核验。
5. 复用 CommunityScrapers 一类公开刮削规则做元数据导入：只当只读规则语料，不重新引入 Stash 运行时依赖（ADR-0021）。
6. 剩余 status / suggest / ledger 逻辑移入应用边界后删除旧 CLI 表面。
7. 把常跑批处理折进 `peach` CLI：`probe`、`sheets`、`scrape_codes`、`fetch_jav_covers`、`taste_history`、`traffic_watch` 现在各是一个脚本入口，参数、限流与健康报告口径不统一。
8. 开源通用化：设置层与首次运行向导、用来源挂载点 ID 取代账本里的 Windows 盘符、单写者复制链路可整体关闭、个人路径与主机名清扫。

合计：**14 项开放需求**，其中 6 项已有骨架，8 项尚未实现。已完成的需求不在这里留痕，去 Git 历史查。
