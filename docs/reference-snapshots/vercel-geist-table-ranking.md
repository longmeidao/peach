# Vercel Geist Table 与首页布局证据（2026-08-30）

## 请求与取得通道

- 目标：`https://vercel.com/geist/table`、`https://vercel.com/home`。
- 登录态内置浏览器先后两次读取 Table，均在 30 秒超时并重置控制连接；可交互 DOM、计算样式与截图未取得。
- 直接读取 Table 返回 HTTP 400，原因是该入口声明的 `text/markdown` 内容类型不受读取通道支持；正文未取得。
- 官方索引结果取得 Table 当前的使用原则：同形、可比较的数据使用语义 table；可排序表头使用 button；数字使用 tabular numerals；空态置于表格外；名称采用专名或名词短语。
- Vercel Home 当前 HTML 已取得，只确认共享对齐线与分区清晰的页面层级；没有取得可复用的标签排行组件，因此不从首页猜测排行像素或交互。

## Peach 采用与差异

- 使用空间的四个位置属于同形可比较数据，使用原生 `table`，列为位置、已用、可用与使用率；数字列使用 tabular numerals。
- 内容标签是固定 Top 30 排行并可直接筛选，不提供虚假的列排序；桌面以两栏有序列表提高扫描密度，DOM 顺序保持排名顺序，390px 手机回到单栏。
- 表格与排行都复用 Peach 既有 `--line-soft`、字号和 1100px 阅读列，不复制未取得的 Vercel 像素、动效或内部组件实现。

## 复核入口

- https://vercel.com/geist/table
- https://vercel.com/home
