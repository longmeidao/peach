<p align="center">
  <img src="resources/peach-logo.png" alt="Peach" width="96">
</p>

<h1 align="center">Peach</h1>

<p align="center">把磁盘、挂载网盘与关注来源里的媒体，整理成只属于自己的私人馆藏。</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/releases">下载 Windows 测试包</a> ·
  <a href="#功能预览">功能预览</a> ·
  <a href="#文档">文档</a> ·
  <a href="README.en.md">English</a>
</p>

Peach 是面向单人的本地优先媒体馆藏应用。它在浏览器里统一搜索、播放、整理和追更已有媒体，馆藏、观看记录与复核决定保存在本机 SQLite ledger 中。

> **18+** 面向管理成人内容馆藏的成年人。仓库不包含媒体或站点数据；来源连接器要求使用者拥有相应访问权，不绕过付费墙、机器人验证或其他访问控制。

## 能做什么

<table>
  <thead>
    <tr>
      <th width="180" nowrap>功能</th>
      <th>简介</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="180" nowrap><strong>视觉馆藏</strong></td>
      <td>以封面浏览视频与图集，按作品、女优、厂牌、创作者、系列和标签搜索；馆藏筛选、身份补全与大图模式在同一页完成。</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>播放与关联</strong></td>
      <td>播放本地磁盘和挂载网盘媒体，在详情页查看人物、厂牌、标签与相关作品；支持稍后看、观看状态、Mix、播放列表和角落小窗。</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>人物与身份</strong></td>
      <td>把头像、别名、外部链接与作品关系整理到人物资料页，外部身份候选保留来源并交给用户复核。</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>采集与补全</strong></td>
      <td>扫描文件夹并识别 NFO、本地海报和已有资料；从来源补充封面、头像与元数据，确认后才写入馆藏。</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>多来源关注</strong></td>
      <td>登记官方或归档来源，集中查看同一创作者在不同站点的更新，并在 Peach 内保存内容。</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>界面与多端</strong></td>
      <td>支持明暗主题、自定义配色和响应式页面，可在桌面、平板与手机浏览；重复项、失效文件、回收站和外部候选集中复核。</td>
    </tr>
  </tbody>
</table>

## 获取 Peach

Windows x64 独立测试包在 [GitHub Releases](https://github.com/longmeidao/peach/releases) 提供；Windows 与 macOS 也可从源码运行，源码方式需要 Python 3.12 或更高。下载、校验与配置见 [Windows 测试版](docs/TESTING_DESKTOP.md) 和 [运行与配置](docs/OPERATIONS.md)。

## 数据边界

媒体保留在原目录，馆藏、身份、观看记录和人工决定保存在本机 SQLite ledger；外部元数据与 AI 结果先作为带来源和置信度的候选，凭据不进入 Git、日志或 API 返回。Peach 面向单人自托管，不提供公开站点或团队权限模型。

## 文档

[Windows 测试版](docs/TESTING_DESKTOP.md) · [运行与配置](docs/OPERATIONS.md) · [来源采集](docs/SOURCING.md) · [变更日志](CHANGELOG.md) · [开发约定](AGENTS.md) · [架构决策](docs/adr/)

开发验证统一使用 Windows `& .\scripts\test.ps1` 或 macOS/Linux `./scripts/test.sh`。

## 许可证

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao。

固定的第三方前端文件保留上游许可证与来源记录，见 [web/vendor](web/vendor/)。
