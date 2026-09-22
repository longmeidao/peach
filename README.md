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

## 功能预览

https://github.com/user-attachments/assets/a97049bd-ddaf-4844-99ca-b18e97957d2a

<p align="center"><a href="docs/assets/peach-overview.mp4">下载 58 秒功能介绍视频</a></p>

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
      <td>扫描文件夹并识别 NFO、本地海报和已有资料；从来源补充封面、头像与元数据，确认后才写入馆藏。开启推送发现后，本机新文件与 CloudDrive2 通知到的网盘新文件几秒内入库，定期扫描仍在背后兜底。</td>
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

Windows x64 独立测试包在 [GitHub Releases](https://github.com/longmeidao/peach/releases) 提供；Windows 与 macOS 也可从源码运行，源码方式需要 Git、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和 Python 3.12 或更高。下载、校验与配置见 [Windows 测试版](docs/TESTING_DESKTOP.md) 和 [运行与配置](docs/OPERATIONS.md)。

源码运行（下例用 Python 3.14，uv 会自动下载缺失的解释器）：

```powershell
git clone https://github.com/longmeidao/peach.git peach-app
cd peach-app
uv sync --locked --python 3.14
& .\.venv\Scripts\peach-tray.exe
```

macOS 把后两条换成 `uv sync --locked --python 3.14 --extra macos` 和 `./.venv/bin/peach-tray`。托盘会打开首次设置页，在那里选媒体文件夹、访问范围和端口。

FFmpeg 与 ffprobe 需自行安装：缺少时仍可浏览和播放浏览器兼容格式，转码、探测与缩略图不可用。源码部署的数据默认在仓库同级的 `peach-data/`，独立测试包放在 `%LOCALAPPDATA%\Peach\peach-data`，`PEACH_DATA_ROOT` 可指定其他位置。局域网与 HTTPS 访问见 [运行与配置](docs/OPERATIONS.md)；更新与卸载在「设置 → 这台电脑 → 更新与维护」，独立包的步骤见 [Windows 测试版](docs/TESTING_DESKTOP.md)。

## 数据边界

媒体默认保留在原目录，整理是用户显式发起、可预览可回滚的操作；馆藏、身份、观看记录和人工决定保存在本机 SQLite ledger；外部元数据与 AI 结果先作为带来源和置信度的候选，凭据不进入 Git、日志或 API 返回。Peach 面向单人自托管，不提供公开站点或团队权限模型。

## 文档

使用：[Windows 测试版](docs/TESTING_DESKTOP.md) · [运行与配置](docs/OPERATIONS.md) · [来源采集](docs/SOURCING.md) · [项目状态](docs/STATUS.md) · [变更日志](CHANGELOG.md) · [安全政策](SECURITY.md)

开发：[开发约定](AGENTS.md) · [测试与依赖](docs/TESTING.md) · [前端开发](docs/FRONTEND.md) · [产品待办](docs/PRODUCT_BACKLOG.md) · [交接说明](docs/HANDOFF.md) · [复用清单](docs/REUSE.md) · [README 维护](docs/README_MAINTENANCE.md) · [架构决策](docs/adr/)

开发验证统一使用 Windows `& .\scripts\test.ps1` 或 macOS/Linux `./scripts/test.sh`。提交问题请附版本、操作步骤、预期与实际结果，不要附带真实账本、媒体、Cookie 或私钥；安全问题按[安全政策](SECURITY.md)报告。

## 许可证

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao。

固定的第三方前端文件保留上游许可证与来源记录，见 [web/vendor](web/vendor/)。
