# Stash 遗留：继承的缺陷与许可证边界

Peach 的代码已经完全不连 Stash：服务运行期的 adapter 按 ADR-0021 删除，两个离线导入脚本与
`src/peach/stash.py` 于 2026-09-08 退役（ADR-0021 修订）。ADR-0002 定下的六步去依赖路线
到此全部完成，序号只留给两份 ADR 引用。是否卸载 Stash 进程和它的 generated 数据是纯粹的
本机运维决定，与 Peach 无关。这份文档只回答两件事：从 Stash 继承下来的哪些缺陷仍在影响
数据，以及分发前必须处理的许可证边界。2026-08-14 的完整审计留在 Git 历史里。

数据一律保留：`media_binding` 表、`asset.stash_scene_id` 列和 `source='stash:*'` 的断言都是
溯源，不清理。

## 从 Stash 继承的已知缺陷

- Stash 的身份模型是平的：上传者、合集和演员塞进同一个自由文本字段（`演员:` 前缀）。导入
  进来的断言因此需要 `scripts/merge_duplicate_identities.py` 这类工具收拾，规范实体才是真相。
- `asset_tag` 的唯一键是 `(asset_id, tag)`，`INSERT OR IGNORE` 存不下同一断言的多个来源，
  provenance 只能靠 `source` 列近似表达。
- `asset.rating` 的量纲是 Stash 的 rating100（0–100），五颗星按 20 的倍数写；撤销写 NULL。

## 许可证边界

Stash v0.31.1 是 AGPL-3.0。Peach 从未复制它的 Go 实现，历史上只通过公开协议调用过独立进程。
当前 Peach-managed FFmpeg 是从本机既有构建复制的 GPLv3/x264/x265 shared bundle，完整
`LICENSE.txt` 已保留且仅供此个人实例运行；它不进入 Git，也不能在未处理源码、许可证和通知
义务前作为 Peach 安装包分发——ADR-0023 的发布准备阶段要先解决这一条。

官方依据：[Stash 架构](https://github.com/stashapp/stash/blob/develop/docs/ARCHITECTURE.md)、[Scene schema](https://github.com/stashapp/stash/blob/v0.31.1/graphql/schema/types/scene.graphql)、[AGPL-3.0](https://raw.githubusercontent.com/stashapp/stash/v0.31.1/LICENSE)、[FFmpeg 法律说明](https://www.ffmpeg.org/legal.html)。
