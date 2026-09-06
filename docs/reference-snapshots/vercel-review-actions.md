# 复核操作与折叠

人工取证笔记，React 页面运行后的 DOM 与计算样式不能作为可重抓的源字节，不登记进 `docs/reference-sources.json`。核验于 2026-09-06。

- 官方入口：https://vercel.com/geist/button 、https://vercel.com/geist/select 、https://vercel.com/geist/collapse 。
- 本机 Chrome 取得三页 DOM 与控件计算样式；原始资料归档于 `attic/evidence/20260906-studio-monitor/`。
- Button 示例高度 32／36／40px；默认主动作深底浅字，错误动作使用红色。Select 用于固定列表的单项选择，Collapse 用于展开正文。
- Peach 复用已有 Button、Select 和 `wireCollapse`。批量操作独立于分类 Tabs，统一来源只选择候选，通过按钮提交；拒绝使用危险动作色，跳过使用已有提示色。
