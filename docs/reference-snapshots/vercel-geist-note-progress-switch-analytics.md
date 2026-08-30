# Vercel Geist Note／Progress／Switch 与 Analytics 证据（2026-08-30）

## 取得方式与锁定值

- 官方页：<https://vercel.com/geist/note>、<https://vercel.com/geist/progress>、<https://vercel.com/geist/switch>。
- Windows Schannel 路径反复返回凭据错误，本次固定使用仓库外已有的 OpenSSL curl 入口 `C:\Users\longm\.local\bin\curl-ossl.cmd`，请求头为 `Accept: text/html,application/xhtml+xml` 与 `User-Agent: Mozilla/5.0`。
- 页面 HTML SHA-256：Note `18FF709BAE3813D8153DE2631793280614B1290941E4BD11D67026EC17E2B5FC`；Progress `2DD846E2EC4A8ADF7D3FD1F5C6CE4ACCEA95E29D71881DF8AC6F6874290AD744`；Switch `075696BCEEB320D2267179AA86E1B037D7607C977DA7B1E6B93366A9990EF6A5`。
- 登录态 Analytics：<https://vercel.com/sandun-bingshi/lmd-gg/analytics?environment=all>，由 Codex 内置浏览器读取 DOM；导航、筛选、指标按钮、数据分组与空状态均已取得。
- 登录态 Speed Insights：<https://vercel.com/sandun-bingshi/lmd-gg/speed-insights> 未取得。浏览器点击后 10 秒超时且未导航；直接请求 307 到登录页。不得把 Analytics 或公开宣传页臆测成该页面的真实实现。

## 可复用语义

### Note

- Note 是紧邻字段、卡片或分区的持久上下文；底层状态改变前持续存在。
- `error` 表示用户必须修复的问题，`warning` 表示需要理解后果，`success` 表示已通过检查，普通中性说明使用默认或 `secondary`。
- 页面／系统级且带动作的问题用 Banner，瞬时确认用 Toast，销毁确认用 Modal；不要把这些表面都画成 Note。
- 一条 Note 只讲一个概念；标签 1–2 个词，正文用一句主动句说明影响。Note 不加临时关闭按钮。

### Progress

- Progress 只用于已知总量的确定性进度；必须提供真实 `value`、`max`、文本单位与 `progressbar` 无障碍值。
- 1–3 秒未知进度使用 Spinner，行内保存使用 Loading Dots，比例／配额才考虑 Gauge；不能拿装饰性蓝条冒充进度。
- 阈值颜色必须来自同一业务阈值，阶段 stop 必须代表真实、有名称的阶段。

### Switch

- Switch 是 2–3 个互斥视图的分段选择器，使用 radio 语义、共享 `name`，初始恰好一个选中。
- 布尔开／关使用 Toggle；超过 3 项或长标签使用 Tabs／Select。
- 控件宽度必须容得下最长标签，图标项也必须有可访问名称；图标解释可复用 Tooltip。

### Analytics 数据面板

- 页面先提供环境、日期范围等全局筛选，再给 Visitors／Page Views／Bounce Rate 等并列摘要指标。
- 数据区以有边界的面板承载；面板标题有独立 header 分隔线，正文承载指标、tablist、表格或空状态。
- Pages／Routes／Hostnames、Referrers／UTM Parameters、Countries、Devices／Browsers、Operating Systems、Events、Flags 使用 tablist 在同层信息间切换，而不是把所有维度堆成装饰性 Bento。

## Peach 有意差异

- Peach 是无构建的原生 HTML／CSS／ES module，不引入 Geist React 包；复用语义、状态与可测量层级，统一实现位于 `web/js/ui-components.js`。
- `/stats` 当前没有环境与日期参数，不复制无消费者的筛选器；先把现有统计改成 header/body 数据面板。
- 库存统计保留网格以利用宽屏，但去掉大写字距标题、半透明卡片与装饰阴影；窄屏仍单列且不得产生页面横向滚动。
- 关注页的可关闭历史失败是页面级 Banner，不是 Note；检查失败明细、资源同步失败和口味加载失败使用持久 error Note。
