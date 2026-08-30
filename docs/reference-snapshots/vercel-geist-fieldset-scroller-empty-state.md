# Vercel Geist Fieldset／Scroller／Empty State 证据

- 取证日期：2026-08-30
- 官方页面：<https://vercel.com/geist/fieldset>、<https://vercel.com/geist/scroller>、<https://vercel.com/geist/empty-state>
- 官方 HTML SHA-256：Fieldset `F8EEB7F54882944131CF9D65EF0EC2A04121FFC011285E0B6B9CD07A552671AE`；Scroller `1BFF2EB9B2D0FA05B737043458A7536B1E263176784C592E13E1180A09A13826`；Empty State `5DAC2EB1E7CC748994FAE9A25CCC2AFD6066BBF29CC93715FF5CA1AC73880B9C`

## 已取得

- Fieldset 根节点使用 `data-geist-fieldset`，正文与页脚分别使用 `data-geist-fieldset-content`、`data-geist-fieldset-footer`。正文内边距 20px；副说明上 8px、下 20px；Footer 最小高度 56px，内边距为上／右／下 12px、左 20px，并以顶部发丝线与正文分隔。
- Fieldset 的官方说明是“把相关表单控件放入有边框的卡片，并可附带 footer actions”。因此 Peach 人工复核卡使用 fieldset；各卡固定同高，变化内容留在正文 Scroller，判定按钮留在固定 Footer。
- Scroller 根、遮罩、正文分别使用 `data-geist-scroller`、overlay、`data-geist-scroller-container`；纵向示例固定 220px。正文只在指定轴滚动、隐藏原生滚动条并使用约 40px 边缘渐隐提示剩余内容；键盘焦点顺序保持 DOM 顺序。
- Empty State 由图标 tile、标题、说明和可选 actions 组成。官方图标为 32px、tile 内边距 10px；标题与说明间距 8px，说明最大宽度 340px。标题下的解释不能拆到组件外。

## 未取得

登录态浏览器已取得 Fieldset 页面 DOM；随后读取 `getComputedStyle` 时控制器在 20 秒后超时并重置，故浏览器计算样式与页面截图未取得。没有用目测值补齐；以上尺寸来自同日下载并锁定哈希的官方 HTML／CSS 资源。

## Peach 适配

- 不引入 Geist React 运行时；共享原生 ES module 输出 Empty State／Scroller 结构，CSS 复用已锁定的层级、间距和 ARIA。
- 人工复核卡统一为 440px 高，正文 20px 内边距并纵向滚动，Footer 最小 56px；大量预览不再另套第二个滚动区。
- 回收站、普通零结果、重复文件、复核、高清版、播放列表与关注页空态统一包含标题和说明；页面工具条与空态之间统一为 16px。
- 异步页面使用导航代际 token；即使快速离开又返回相同路径，旧请求也不能覆盖新页面。
