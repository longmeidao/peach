# BoardUI 适配

Peach 使用 Board 的视觉与组件语义，保留 Vite、Preact、FastAPI 和现有媒体行为。Board 的公开实现依赖 React Aria，不能把组件名称相同当作 Preact 可直接替换的证明。本次由共享 HTML 控件、原生键盘行为与 Preact 数值控件适配；没有新增 React 运行时。

## 控件对应

| Peach / Geist 语义 | Board 对应 | 实施方式 |
| --- | --- | --- |
| Toggle，布尔开关 | Switch | 42×24 轨道、18px 滑块、内嵌标记；保留 checkbox 与 switch 语义 |
| Switch，互斥分段 | Segmented Control | 单选 radio，轨道内选中背景；方向键沿用原生行为 |
| Button / Icon Button | Button / Icon Button | 主动作蓝色，危险操作沿用危险色；纯图标按钮清除默认内边距 |
| Input / Input 前后缀 | Input adornment | 单位在框内尾部，分隔背景；独立数字输入保持可访问名称 |
| 数值范围说明 | Invalid + HintText | 合法范围验证；错误时显示锚定字段的小提示，修正后消失 |
| Select | Select | 保留已实现的列表键盘、焦点与菜单定位，使用 Board 尺寸与表面 |
| Checkbox / Radio | Checkbox / Radio | 保留原生状态与选择范围；共享颜色与焦点 |
| Tabs / 页面导航 | Tabs | 管理导航下划线，配置与设置按内容分区 |
| Fieldset | 卡片正文与操作区组合 | 标题在框内，操作区用相邻色阶，不增加框中框 |
| Modal | Settings Modal / Dialog | 设置左侧分区、右侧标题及独立滚动；业务确认保留后果和错误恢复 |
| Toast | Notification | 短暂操作回执沿用现有通知通道 |
| Note / Banner | 字段反馈 / Announcement | 数据错误与恢复动作留在发生位置 |
| Tooltip | Tooltip | 保留含义与键盘焦点可见性 |
| Table | Table / Data Table | 保留选择、排序、批处理和实际数据 |
| Tag / Badge | Chip / Badge | 标签与状态语义分开，保留可操作范围 |
| Sidebar / Drawer | Sidebar 的收起与展开 | 一个按钮控制同一导航，移动端使用遮罩 |
| Spinner / Skeleton / Progress | 原有等价反馈 | 不虚构进度，保持业务请求时机 |
| Scroller / Collapse | 溢出滚动 / 展开分组 | 保留键盘、溢出和展开行为 |
| 视频播放器、照片灯箱、沉浸队列 | 无直接替代 | 保留专用交互，仅统一外围卡片与控件 |

## 设计边界

- `web/board.css` 是可独立关闭的视觉层。设置「使用旧版 UI」后应用并刷新，首屏加载前决定是否启用。
- 「增加对比度」关闭透明与折射；系统降低透明度偏好也使用实色。折射只作用于导航背景，不扭曲文字。
- 设置标题与控件在桌面同排，手机宽度不足时换行。单位与数值属于同一输入框；可关闭的功能显示开关，关闭时隐藏数值。
- 数值非法时不保存；关闭搜索记录后不读取或记入搜索记录，关闭相关推荐后不请求该模块。
- Board 免费源码以官网声明的 MIT 条款使用；Pro 图表与模板不取用收费源码。项目自有图表不宣称来自 Pro，也不承诺 Pro 更新权益。
- Remix Icon 固定为 4.9.1，按包内 Remix Icon License v1.0 登记；官网所写的 Apache 2.0 不代替实际包许可证。保留已确认图标，候选由 `attic/evidence/20260908-boardui-preview/boardui-full/icon-review.html` 审查。

## 参考证据

2026-09-08 读取官方公开注册表，原始文件在 `attic/evidence/20260908-boardui-preview/board-reference/`。

| 来源 | SHA-256 |
| --- | --- |
| https://www.boardui.com/r/input.json | ac1e66c9ed15f9db2750dd528bc894c856ac84e79f72ff4acb96f14b1ab9c249 |
| https://www.boardui.com/r/switch.json | 3412c1910b2fa7f5d17404bf50bd2503e9ca097cf9d741366379cf18e09ebeb6 |
| https://www.boardui.com/r/segmented-control.json | 62300be25310fef31962ddc237818739a2efd0d0143dd0832f3d1a2166c28e38 |
| https://www.boardui.com/r/button.json | 89cc2c176d1d94d481bbfc6e34f233ccf109c10d319533cc7c1e98923b6e7d69 |

Input 的上游错误信息位于字段下方，并通过 `errorMessage` 关联；锚定的小提示是用户指定的 Peach 差异。设置布局来自公开 `settings-modal.json`：871×614、274px 导航、32px 内容边距、24px 外圆角。原始设置参考保存在同目录下 `boardui-full/settings-reference.json`。

## 验收边界

- 数值设置的 155 项前端测试通过，包含非法值不保存、关闭恢复、异步读取值恢复；构建与类型检查通过。
- 18984 直接服务正式工作树。桌面已检查设置、首页、详情、统计、口味、数据管理、关注管理、配置与复核；390×844 已检查设置、详情、标签与事务所索引，没有页面横向溢出。
- 设置关闭图标中心偏差为 0；纯图标控件不覆盖工具栏业务显隐。旧版模式关闭 Board 样式，增加对比度时导航 `backdrop-filter` 为 `none`，退出两种状态均已核对。
- 预览只读，未写真实 ledger、配置或凭据；脱盘状态下真实播放未验证。生产入口与版本号未改。
