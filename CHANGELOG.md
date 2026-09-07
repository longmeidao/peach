# 变更日志

本文件记录 Peach 每个发布版本里值得使用者知道的变化。

格式遵循 [Keep a Changelog 1.1.0](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循
[Semantic Versioning 2.0.0](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。分组标题是
「新增 / 变更 / 弃用 / 移除 / 修复 / 安全」，对应规范的 Added / Changed / Deprecated /
Removed / Fixed / Security。

版本号只在发布点推进：每个 `X.Y.Z` 都对应一份可下载的制品，主线上的其它提交由 commit
标识（ADR-0012）。`## [未发布]` 收的是已经进了主线、还没发出去的变化。

条目草稿由 `python scripts/changelog.py` 从提交主题生成，措辞由人改成使用者读得懂的话；
只改开发过程的提交（文档、测试、重构、构建）不进本文件。

## [未发布]

### 新增

- 配置页新增桌面快捷方式开关，可直接创建或移除桌面图标。
- 可折叠的区块标题统一带上展开箭头。

### 修复

- 桌面快捷方式创建或移除失败时报出真实原因，而不是只说失败。
- 配置页里的危险操作（移除媒体文件夹等）统一走同一个二次确认。
- 忙态提示会说明正在进行的动作；禁用的开关与按钮给出正确的颜色和光标。

## [0.27.1] - 2026-09-06

Windows 独立测试包的第四个预发布。这一版及更早版本的逐条变化见 Git 历史与
[GitHub Releases](https://github.com/longmeidao/peach/releases)。

[未发布]: https://github.com/longmeidao/peach/compare/v0.27.1...HEAD
[0.27.1]: https://github.com/longmeidao/peach/releases/tag/v0.27.1
