---
name: peach-web-ui
description: 在新增、修改或复核 Peach 页面、控件、提示、错误、数据面板、响应式布局或视觉样式时使用。
---

# Peach Web UI 复用门槛

最后复核：2026-09-03

## 开工顺序

1. 读取相关页面、`web/js/ui-components.js`、`web/app.css` 与 `tests/test_web_ui.py`，先找现成控件、token 和行为。
2. 外部产品被称为参考时同时执行 `peach-reference-evidence`；没有当前可复现证据就写 `未取得`，不补动画、间距或交互猜测。
3. 视觉与交互先过 `docs/reference-snapshots/vercel-web-interface-guidelines.md` 的 Focus States、Forms、Animation、Content 四节，以及 `vercel-report-design.md`（即 `vercel.com/design.md`）的「Reject generated-design reflexes」；第三方逆向测量的 DESIGN.md（如 design-bites）不作证据。
4. 新控件先检查 `docs/reference-snapshots/vercel-geist-controls-measured.md`、`vercel-geist-semantics-measured.md`、`vercel-geist-note-progress-switch-analytics.md` 与 `vercel-geist-command-search-loading.md`。

## 组件选择

| 需求 | 使用 | 不要使用 |
| --- | --- | --- |
| 字段、卡片、分区旁的持久反馈 | Note | Toast、空状态 |
| 页面／系统级问题与恢复动作 | Banner | Note |
| 短暂操作回执 | Toast | 持久 Note |
| 销毁确认 | Modal／现有 confirm | Toast |
| 已知总量的进行状态 | Progress | 装饰性蓝条 |
| 用户触发动作等待结果 | Spinner | 旋转原操作图标、Loading Dots |
| 后台任务仍在推进 | Loading Dots | Spinner、假百分比 |
| 整页或大区块首次等待内容结构 | Skeleton | Spinner、Loading Dots |
| 2–3 个互斥视图 | Switch（radio） | Toggle |
| 布尔开关 | Toggle | Switch |
| 无布局高度变化的菜单 | Menu／Listbox，无动画 | Collapse 动画 |
| 带搜索语义的输入 | Search Input（搜索图标前缀；搜索中原位换 Spinner） | 无图标裸输入 |
| 全屏命令／设置覆盖层 | 有锁定证据的 Dialog motion | 把同一动画套给普通菜单 |
| 展开正文或分组 | Collapse | 自造 easing |
| 一组输入／候选及其底部动作 | Fieldset | 自造卡片 Footer |
| 固定高度区域中的溢出内容 | Scroller | 页面级滚动或嵌套滚动区 |
| 没有数据或结果 | Empty State（图标、标题、说明同组） | 裸灰字或把说明拆到组件外 |
| 图标含义与补充说明 | Tooltip | 让浮层撑宽页面 |

## 实现门槛

- 优先扩展 `web/js/ui-components.js`，不要为同一语义复制一次性 class 和模板。
- 颜色、字号、圆角、浮层层级只用 `:root` 已有 token；新 token 必须证明现有词汇无法表达。
- 字重只有 400／500／600 三档，标题也是 600；圆角只用 `--badge-radius`／`--control-radius`／`--surface-radius`／`--floating-radius`／`--pill-radius` 加 `50%` 与 `0`，带边框容器里的头尾条用 `calc(… - 1px)` 保持同心。两者的字面值由 `tests/test_web_ui.py` 拒绝，归属判据见 `:root` 注释。
- 单色优先：`--tungsten` 只给焦点环、链接、进度／数据与 Toggle 开态。按下／选中用 `--ink-2` 底 `--ground` 字（行与列表项用 `--hover` 底），主动作用 `--ink` 底 `--ground` 字且每屏最多一个，悬停边提亮到墨色 28%，标题悬停下划线不变蓝，计数徽章中性灰。其它选择器引用 `--tungsten` 由 `tests/test_web_ui.py` 拒绝；实测见 `vercel-geist-semantics-measured.md`「选中态与开关色」。
- `outline:0`／`outline:none` 只允许出现在同一规则给出替代焦点样式的地方（`box-shadow` 或子元素 outline），或输入框由带 `:focus-within` 的容器接管焦点时；reduced motion 由全局 `@media (prefers-reduced-motion:reduce)` 统一关闭，不逐处补。
- Progress 必须有真实 `value/max`、可见单位与 `aria-valuemin/max/now`；分隔线放在完整指标（含进度条）之后。
- Switch 必须共享 radio `name`、初始一个 `checked`、键盘可用；布尔状态继续使用 Toggle。
- 菜单每项包含与入口相同的图标和文字，菜单内部滚动、`overscroll-behavior:contain`，不得把浏览器页面撑出滚动条。
- Spinner 只反馈用户直接触发的动作，触发器统一调用 `setActionBusy()`：写入 `aria-busy=true` 与 `aria-disabled=true`、视觉变灰、拦截重复触发，同时保持可聚焦；请求等待期不得再用原生 `disabled`，它只留给缺输入、无权限等动作确实不可执行的状态。未知时长的后台抓取使用 Loading Dots。整页或大区块首次取数使用 Skeleton 预留最终结构。Spinner／Loading Dots 保留可见状态文字；Skeleton 只保留给辅助技术的状态名，不另画「正在读取」文案。三者都尊重 reduced motion。
- 用户写操作只在服务端终态成功后调用共享 `actionReceipt()` 发一条过去时 Toast；可由安全逆操作完整恢复的状态提供 8 秒“撤销”，永久删除、凭据、保存到账本等不伪造撤销。仅打开面板／菜单／Dialog 不算操作完成，不发 Toast；失败除短 Toast 外仍在原位置保留原因与重试入口。
- 同一次页面进入只呈现一段等待态；深链启动与页面取数复用同一个 Skeleton，禁止 Spinner 再切换成 Loading Dots 或 Skeleton。
- Skeleton 只覆盖真正等待的内容区；静态标题、导航和能同步得到的筛选控件立即显示。骨架必须复用最终容器的宽度、列数与对齐方式：卡片网格横向铺满，居中面板仍居中，不得用一列通用占位替代不同页面结构。
- 关注来源标签先服从来源记录的类型：只有明确标为 `general` 的标签才能进入卡片、顶部筛选和在线标签页，`artist`／`character`／`copyright`／`metadata` 与未知类型不得靠词形猜成 `general`。通用词清理是第二道门槛，只处理已经确认的 `general`；详情可显示全部来源标签，并按真实类型着色。
- 分页末尾、空页和“没有更多内容”是中性终止状态，用可关闭 Note；只有需要恢复或处理的故障才能进入红色 error Note。
- 弹层标题栏与滚动正文分层：标题分隔线属于卡片全宽，滚动条只属于正文。
- 没有直接证据不得新增动效；参考产品无动画的菜单保持无动画。
- Fieldset 的正文统一 20px 内边距；标题条与底部操作条同为 `--fieldset-bar-h`（52px）、竖直居中、左 20px 右 16px。标题放在框体里，不用原生 `<legend>`：它会在上边框上开缺口，同组卡片内容高度不同时缺口位置也跟着不齐。同组卡片必须同高，变化内容只放一个纵向 Scroller。
- 界面不解释数字是怎么算出来的。口径、免责、隐私声明、「不会做什么」和「按什么汇总」都不写：这个库只有一个用户，定口径的就是他本人。只留他要据以决定或操作的东西——读数本身、不可逆动作的作用范围、正在发生的事。单位跟着数字走（`497 项`），不另起一行说明。
- 上一次跑完的结果不常态显示。它是那一刻的快照，进页面就铺开会被读成现在的状态，而页面上没有任何东西说它是旧的；只有仍在进行的任务才自动接管页面。
- Empty State 的标题和说明必须同处组件内；全页空态与上方工具条统一留 16px，不得再套一层空卡片。
- 任何先请求再重绘整页的入口都必须绑定导航代际；只比较 `location.pathname` 不能防住“离开后快速返回同一路径”的旧响应。

## 验收门槛

1. 为语义、DOM、ARIA、复用模块和响应式规则补页面源测试；数据语义变更另补 API／数据层测试。
2. Windows 只从隔离 worktree 根运行 `& .\scripts\test.ps1`；本轮跨多个页面或改规范时跑默认 `full`。
3. 在本地预览检查桌面与 390×844：页面宽度不大于视口、弹层不越界、菜单内部滚动、键盘 focus 可见、控制台无错误。
4. 按 `peach-surfaces` 报告数据层、API、页面、契约、测试与文档各表面；未部署不得称为生产已生效。
