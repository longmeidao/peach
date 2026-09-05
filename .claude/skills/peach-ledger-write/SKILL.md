---
name: peach-ledger-write
description: 在用户说迁移、migrate、--apply、合并实体、merge_entity、改真相字段、批量删除、清空回收站，或任何要写真实 ledger 的动作之前使用。
---

# 真实 ledger 写入流程

最后复核：2026-08-21
证据来源：`docs/HANDOFF.md`「数据安全」「身份合并与来源分工」、ADR-0005、ADR-0015、ADR-0017。

真实库：当前写入者本机 `PEACH_DATA_ROOT/database/ledger.db`（WAL）。绝不能把共享传输副本或
另一台机器的副本当当前真实库；测试只用临时 SQLite 与临时媒体。

## 迁移

1. SQLite 备份到当前本机 `PEACH_DATA_ROOT/database/ledger.pre-<用途>-<时间戳>.db`。
2. 记录迁移前 asset/tag 计数。
3. `PRAGMA integrity_check`。
4. `peach migrate status` 核对版本。
5. 应用后重复计数并做服务 smoke test，前后差异逐条解释。
6. 复核通过后清退旧备份：`scripts/prune_ledger_backups.py --apply`（缺省只列计划）。规则在
   `peach.ledger_backups`：最近 5 份、24 小时内、比 `ledger.db` 更新的都留，其余连同 `-wal`／`-shm`
   删；账本 `integrity_check` 不是 ok 一份都不删。Windows 托盘每次启动按同一规则自动跑。

已应用的迁移文件不得修改。`0007` 曾在应用后被改写注释导致校验和漂移，必须用备份重放并逐条
对比后才校正 `schema_migration`。任何后续变更一律新增版本号。

## 真相字段写入

- 改写 `entity.canonical_name` 与迁移同级：`--apply` 必须同时给 `--backup`。
- AI 与刮削结果只能作为带来源和置信度的候选，不直接改写真相字段。
- 运维脚本默认 dry-run：`scrape_codes.py` 默认只写复核 CSV，`clean_names.py` 默认只生成
  改名计划且 `--apply` 前备份 SQLite 并在数据库更新失败时回滚文件名。

## 实体合并

- `entity(kind, normalized_name)` 唯一约束冲突通常不是 bug，而是同一人的新旧艺名信号。
- 合并走 `peach.entities.merge_entity`：保留作品多的一侧，迁移关系、别名、外部引用、链接和
  搜索词，旧称全部留作别名。`entity_external_ref` 每个 provider 只保留一条，同源第二条丢弃
  并报告，不静默覆盖。
- 合并不可逆：先取得用户授权并备份。
- 两条实现陷阱：sqlite 连接默认 `foreign_keys=OFF`，子表行必须在函数内显式 DELETE，否则留下
  孤儿 `entity_alias` / `entity_external_ref`；计数用 `SELECT changes()`，不能用
  `total_changes`（连接累计值，会虚报数百倍）。
- 合并后立即 `PRAGMA foreign_key_check`，应为 0。

## 删除

- 物理删除只有一条实现 `purge_assets()`，`/api/batch` 的 `delete` 与 `/api/trash/empty` 共用。
- 顺序固定：先删媒体文件、再删账本行。删不掉的文件整条跳过并在 `blocked` 里回报，前端必须
  显示 `blocked`。反过来先删行会留下无人认领的媒体文件，那才是不可恢复的丢失。
- `asset_search` 不列入 `ASSET_REFERENCE_TABLES`，FTS 行由 `0004` 的删除触发器负责。
- 不可逆动作先产出带证据和置信度的复核产物，执行步骤单独授权。

## 结论必须写入文件

得出结论的同一步就写入 ledger、CSV 或其他持久产物；结论被修正时所有派生产物必须重建。
只存在于聊天里的结论等于不存在，过期的删除清单比没有清单更危险。
