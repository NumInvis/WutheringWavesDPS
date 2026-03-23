# WutheringWavesDPS

<div align="center">

鸣潮拉表分享社区 - v1.03

<a href="https://www.arcanamorning.tech/WutheringWavesDPS/">在线访问</a> ｜
<a href="https://github.com/NumInvis/WutheringWavesDPS/issues">问题反馈</a> ｜
<a href="https://afdian.com/a/r0xy0">爱发电赞助</a>

</div>

WutheringWavesDPS 是一个专为《鸣潮》玩家打造的拉表分享社区平台。它提供了完整的在线 Excel 编辑体验，同时集成了数据观察、社区分享、用户管理、问卷系统等功能。无论你是想制作 DPS 计算表、角色数据表，还是分享游戏攻略，都可以在这里快速完成并分享给其他玩家。

## ✨ 核心特性

1. 💯 **完全免费开源** - 永久免费使用，代码完全开源
2. 📊 **在线 Excel 编辑** - 基于 Luckysheet，完美兼容 Excel 格式、公式、样式
3. 📈 **数据观察中心** - 贴吧数据统计、iOS 畅销榜、排名趋势等多维度数据监控
4. 🤖 **自动化爬虫** - 定时自动获取贴吧、App Store 等数据
5. 🌐 **社区分享** - 上传、分享、点赞，构建游戏数据社区
6. 📋 **问卷系统** - 创建、发布、统计问卷，收集玩家反馈
7. 💻 **WebUI 管理** - 完整的后台管理系统，支持日志、任务调度监控
8. 📱 **移动端适配** - 全面优化手机端浏览体验
9. 🛡️ **权限管理** - 管理员、普通用户分级权限控制

## 🚀 快速开始

访问官方网站：[https://www.arcanamorning.tech/WutheringWavesDPS/](https://www.arcanamorning.tech/WutheringWavesDPS/)

### 使用流程

1. **注册/登录** - 创建账号或使用已有账号登录
2. **创建拉表** - 点击新建，在线编辑 Excel 表格
3. **保存分享** - 编辑完成后保存，生成分享链接
4. **社区浏览** - 查看其他玩家分享的拉表，点赞收藏
5. **数据观察** - 查看贴吧热度、游戏排名等数据
6. **问卷系统** - 创建问卷，收集玩家反馈（管理员功能）

## 📋 功能详解

### 在线表格编辑
- 基于 Luckysheet 实现，完美兼容 Excel
- 保留数据、公式、格式不变
- 支持在线编辑和实时保存
- 支持导入/导出 Excel 文件

### 数据观察（v1.02 新增）
- **贴吧发帖量统计** - 多日数据对比，表格展示
- **每周热帖排行** - 按热度排序，快速了解热门话题
- **每日热帖** - 当日热门帖子一览
- **iOS 畅销榜排行** - 支持国服/日服/美服/韩服排序
- **当日活跃度排行** - 柱状图展示各贴吧活跃度
- **排名趋势** - 折线图展示游戏排名变化，支持时间筛选
- **全局设置** - 管理员可调整页面布局和显示参数
- **个人设置** - 自定义字体大小、图表高度等

### 问卷系统（v1.03 新增）
- **问卷管理** - 管理员可创建、编辑、发布问卷
- **问卷填写** - 玩家可在线填写问卷
- **数据统计** - 实时统计问卷数据，生成统计报告
- **账号限制** - 每个账号只能填写一次，确保数据真实性

### 后端监控（v1.02 新增）
- **贴吧爬虫调度器** - 定时自动爬取贴吧数据
- **iOS 畅销榜爬虫** - 自动获取 App Store 排名
- **系统日志管理** - 查看和管理系统运行日志
- **任务调度监控** - 监控爬虫任务执行状态

### 社区功能
- **社区分享** - 上传并分享你的拉表
- **点星功能** - 为喜欢的拉表点赞
- **搜索功能** - 按作者/编号搜索表格
- **用户系统** - 注册、登录、修改密码
- **管理员功能** - 置顶、删除、日志监控

## 🛠️ 技术栈

- **后端**：FastAPI + SQLite + SQLModel
- **前端**：Vue 3 + TypeScript + Element Plus + Vite
- **表格组件**：Luckysheet
- **图表库**：ECharts
- **爬虫**：aiohttp + asyncio

## 📦 部署指南

### 环境要求
- Python 3.9+
- Node.js 16+
- SQLite 3

### 后端部署
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端部署
```bash
cd frontend
npm install
npm run build
# 将 dist 目录部署到 Web 服务器
```

## 📝 更新日志

### v1.03 (2026-03-23)
- ✨ 新增问卷系统，支持创建、发布、统计问卷
- ✨ 新增问卷填写页面，支持玩家在线填写
- ✨ 新增问卷统计页面，实时数据统计
- ✨ 新增账号限制功能，每个账号只能填写一次
- 🎨 优化前端界面，提升用户体验
- 🐛 修复多个已知问题

### v1.02 (2025-03-18)
- ✨ 新增数据观察模块，全方位监控游戏数据
- ✨ 新增后端监控系统，自动化数据获取
- ✨ 新增 iOS 畅销榜排行功能
- ✨ 新增贴吧发帖量统计和热帖排行
- ✨ 新增排名趋势折线图
- ✨ 新增全局设置和个人设置
- 📱 全面优化移动端适配
- 🐛 修复多个已知问题

### Beta 1.0
- 🎉 项目首次发布
- ✨ 在线 Excel 编辑功能
- ✨ 社区分享功能
- ✨ 用户系统

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 💖 支持我们

如果这个项目对你有帮助，欢迎通过爱发电支持我们：

[![爱发电](https://img.shields.io/badge/爱发电-赞助-ff69b4?style=flat-square)](https://afdian.com/a/r0xy0)

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

## 🔗 友情链接

- [鸣潮动作数据汇总](https://www.kdocs.cn/l/chWXEqFmFGvu)
- [安可网](https://encore.moe/)
- [鬼神莫能窥的B站空间](https://space.bilibili.com/274736623)
- [鸣潮数据库 - nanoka.cc](https://ww.nanoka.cc/)

---

<div align="center">

Made with ❤️ by WutheringWavesDPS Team

</div>
