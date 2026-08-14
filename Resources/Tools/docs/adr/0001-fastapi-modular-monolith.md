# ADR-0001：FastAPI 化的模块化单体

- 状态：Accepted
- 日期：2026-08-14

## 背景

Peach 已有可运行的 `rm-web.py`，数据查询和写入函数大体独立于 HTTP Handler，但媒体 Range、缩略图、Cookie 与错误响应仍耦合在 `BaseHTTPRequestHandler`。直接重写会让现有播放闭环失去回退路径。

## 决策

- 后端渐进迁移到 FastAPI；前端与后端在代码职责上拆分，但继续单进程、单体部署。
- 第一阶段只提供 `/healthz` 与现有 `/api/*` JSON 兼容入口，旧 `rm-web.py` 继续作为生产入口。
- 不引入微服务、PostgreSQL、React 重写或完整账号系统。
- Uvicorn 只允许单 worker，直到进程内缓存、写锁和后台任务状态移出全局变量。
- schema 升级必须由显式迁移器完成；应用导入和健康检查不得自动改真实数据库。

## 被否决的方案

- 一次性把首页、JSON API、媒体串流和生成任务全部重写。
- 为了“前后端分离”拆成独立部署服务。
- 先换前端框架，再恢复现有功能。

## 后果

迁移期会同时存在 legacy adapter 与 FastAPI 入口，但每一步都可独立验证和回退。待 JSON、媒体 Range、页面与 mDNS 全部通过契约测试及双视口验收后，才切换生产入口。
