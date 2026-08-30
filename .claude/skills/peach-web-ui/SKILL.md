---
name: peach-web-ui
description: 在新增、修改或复核 Peach 页面、控件、提示、错误、数据面板、响应式布局或视觉样式时使用。
---

# Peach Web UI 复用门槛

最后复核：2026-08-30

## 开工顺序

1. 读取相关页面、`web/js/ui-components.js`、`web/app.css` 与 `tests/test_web_ui.py`，先找现成控件、token 和行为。
2. 外部产品被称为参考时同时执行 `peach-reference-evidence`；没有当前可复现证据就写 `未取得`，不补动画、间距或交互猜测。
3. 新控件先检查 `docs/reference-snapshots/vercel-geist-controls-measured.md`、`vercel-geist-semantics-measured.md` 与 `vercel-geist-note-progress-switch-analytics.md`。

## 组件选择

| 需求 | 使用 | 不要使用 |
| --- | --- | --- |
| 字段、卡片、分区旁的持久反馈 | Note | Toast、空状态 |
| 页面／系统级问题与恢复动作 | Banner | Note |
| 短暂操作回执 | Toast | 持久 Note |
| 销毁确认 | Modal／现有 confirm | Toast |
| 已知总量的进行状态 | Progress | 装饰性蓝条 |
| 未知总量短等待 | Spinner／Loading Dots | 假百分比 |
| 2–3 个互斥视图 | Switch（radio） | Toggle |
| 布尔开关 | Toggle | Switch |
| 无布局高度变化的菜单 | Menu／Listbox，无动画 | Collapse 动画 |
| 展开正文或分组 | Collapse | 自造 easing |
| 图标含义与补充说明 | Tooltip | 让浮层撑宽页面 |

## 实现门槛

- 优先扩展 `web/js/ui-components.js`，不要为同一语义复制一次性 class 和模板。
- 颜色、字号、圆角、浮层层级只用 `:root` 已有 token；新 token 必须证明现有词汇无法表达。
- Progress 必须有真实 `value/max`、可见单位与 `aria-valuemin/max/now`；分隔线放在完整指标（含进度条）之后。
- Switch 必须共享 radio `name`、初始一个 `checked`、键盘可用；布尔状态继续使用 Toggle。
- 菜单每项包含与入口相同的图标和文字，菜单内部滚动、`overscroll-behavior:contain`，不得把浏览器页面撑出滚动条。
- 弹层标题栏与滚动正文分层：标题分隔线属于卡片全宽，滚动条只属于正文。
- 没有直接证据不得新增动效；参考产品无动画的菜单保持无动画。

## 验收门槛

1. 为语义、DOM、ARIA、复用模块和响应式规则补页面源测试；数据语义变更另补 API／数据层测试。
2. Windows 只从隔离 worktree 根运行 `& .\scripts\test.ps1`；本轮跨多个页面或改规范时跑默认 `full`。
3. 在本地预览检查桌面与 390×844：页面宽度不大于视口、弹层不越界、菜单内部滚动、键盘 focus 可见、控制台无错误。
4. 按 `peach-surfaces` 报告数据层、API、页面、契约、测试与文档各表面；未部署不得称为生产已生效。
