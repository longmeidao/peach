# Geist 设置区块取证

2026-09-06。实时浏览器访问 Fieldset 返回 `js execution timed out`；改用 HTTPX 读取官方 HTML/CSS。浏览器实时动画未取得，动画参数复用已登记的 `vercel-geist-semantics-measured.md`。本文件是人工测量笔记，不在 `docs/reference-sources.json` 中登记为上游快照。

| 来源 | HTML SHA-256 |
| --- | --- |
| https://vercel.com/geist/fieldset | 6a5bde91b9d131014d4837763227457711eee2575e68994a1d9c51a44948aa0c |
| https://vercel.com/geist/select | 921c1730ceea0220ab6507e93c636d5821bcc56bfbc97633cc4b40d8c842d52a |
| https://vercel.com/geist/collapse | ac9f84000a4a71bfabe70ac493e8f67bfc86e2b3e13cebf2daf401a59bf5b638 |

共同 CSS：`https://vercel.com/vc-ap-b3331f/_next/static/immutable/chunks/0ggp-66pwlt2m.css`，SHA-256 `ec205bee3ef6e6f0920703d79055cd9251990ecb23e12515a9ed041068245a28`。

- Error Fieldset 根带 `data-fieldset-type="error"`、红色 400 边框；正文使用背景 100；footer 使用红色 100 底、红色 400 顶边、红色 900 文字。危险按钮为实底，整卡并非全铺深红。
- Select 标签在上方，`mb-2` 对应 8px；原生选择器 `w-full` 跟随容器，文字截断、右侧留箭头位置。规范没有要求统一的固定像素宽度。
- Collapse 文档明确要求开合过渡。Peach 复用 `wireCollapse` 的高度与箭头 200ms `ease-in-out`、`aria-expanded`、`aria-controls` 和关闭时 `inert`。
- [Vercel General settings](https://vercel.com/docs/project-configuration/general-settings) 将通用设置作为独立类别。分类适合大量设置；Peach 当前采用按用途排列的 Fieldset，不再在同页叠加重复分类标题。

## Peach 采用与差异

配置顺序为自启、媒体与挂载、网络代理、访问控制、检查更新、运行信息、卸载。代理容器选用 `min(320px,100%)`，这是 Peach 布局决定；菜单固定与触发器等宽并复用已有键盘及视口定位。代理地址标签使用既有 8px 间距。卸载区与确认按钮使用项目危险色；目录明细复用已有 Collapse，不使用原生瞬间展开。
