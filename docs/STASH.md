# Stash 去依赖：只剩第 6 步

服务运行期已经不连 Stash（ADR-0021）。这份文档只回答三件事：还剩什么没退役、从 Stash
继承下来的哪些缺陷仍在影响数据、以及分发前必须处理的许可证边界。2026-08-14 的完整审计
（运行态快照、逐项能力对照、当时的 GraphQL 与二进制依赖计数）留在 Git 历史里，那些数字
已经随重构失效，不在这里保留第二份。

## 还剩什么

六步路线的前五步已完成。第 5 步的结论是 adapter 从来没有生效过——真实账本 `media_binding`
是 0 行，而 `StashAdapter.stream_candidates` 第一步就读 `external_id("stash")`，对全部资产都
返回空，它的唯一调用方又只被测试调用过；2546 个 `asset.stash_scene_id` 从未迁进
`media_binding` 是直接原因。所以不需要影子期，直接删除，详见 ADR-0021。ADR-0002 与
ADR-0021 都按序号引用这份路线，序号因此保留：

1. 集中 GraphQL adapter，独立 FFmpeg resolver——已完成。
2. 正规化实体、关系、provenance 与 external_ref，把 Stash 知识单向导回 ledger——已完成。
3. 用原生 probe、预览、标准 Range 与 HLS 覆盖本地和网盘——已完成。
4. 整理工具一律先写 ledger——已完成。
5. 关闭 adapter——已完成（ADR-0021）。
6. **未完成**：两个离线导入脚本 `scripts/ledger.py stash` 与 `scripts/import_stash_entities.py`
   仍需要 Stash 进程活着才能跑。它们退役之后才谈得上卸载 Stash 和它的 generated 数据。

数据一律保留：`media_binding` 表、`asset.stash_scene_id` 列和 `source='stash:*'` 的断言都是
溯源，不清理。

## 从 Stash 继承的已知缺陷

- Stash 的身份模型是平的：上传者、合集和演员塞进同一个自由文本字段（`演员:` 前缀）。导入
  进来的断言因此需要 `scripts/merge_duplicate_identities.py` 这类工具收拾，规范实体才是真相。
- `asset_tag` 的唯一键是 `(asset_id, tag)`，`INSERT OR IGNORE` 存不下同一断言的多个来源，
  provenance 只能靠 `source` 列近似表达。

## 许可证边界

Stash v0.31.1 是 AGPL-3.0。Peach 只通过公开协议调用独立 Stash 进程，不复制它的 Go 实现。
当前 Peach-managed FFmpeg 是从本机既有构建复制的 GPLv3/x264/x265 shared bundle，完整
`LICENSE.txt` 已保留且仅供此个人实例运行；它不进入 Git，也不能在未处理源码、许可证和通知
义务前作为 Peach 安装包分发——ADR-0023 的发布准备阶段要先解决这一条。

官方依据：[Stash 架构](https://github.com/stashapp/stash/blob/develop/docs/ARCHITECTURE.md)、[Scene schema](https://github.com/stashapp/stash/blob/v0.31.1/graphql/schema/types/scene.graphql)、[AGPL-3.0](https://raw.githubusercontent.com/stashapp/stash/v0.31.1/LICENSE)、[FFmpeg 法律说明](https://www.ffmpeg.org/legal.html)。
