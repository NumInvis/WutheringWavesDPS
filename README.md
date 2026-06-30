<div align="center">

<!-- Hero Logo -->
<img src="frontend/public/picture.png" alt="WutheringWavesDPS" width="160" />

# WutheringWavesDPS

**鸣潮拉表分享社区 · 在线 Excel 计算与数据观察平台**

[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Vue 3](https://img.shields.io/badge/Vue%203-4FC08D?logo=vuedotjs&logoColor=white&style=for-the-badge)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=for-the-badge)](https://fastapi.tiangolo.com/)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-409EFF?logo=element&logoColor=white&style=for-the-badge)](https://element-plus.org/)

[![Live Demo](https://img.shields.io/badge/🌐%20在线体验-arcanamorning.tech-18181b?style=for-the-badge)](https://www.arcanamorning.tech/WutheringWavesDPS/)
[![Issues](https://img.shields.io/badge/🐛%20问题反馈-GitHub%20Issues-18181b?style=for-the-badge)](https://github.com/NumInvis/WutheringWavesDPS/issues)
[![Sponsor](https://img.shields.io/badge/💖%20爱发电赞助-ff69b4?style=for-the-badge)](https://afdian.com/a/r0xy0)

</div>

---

## 📖 项目简介

**WutheringWavesDPS** 是专为《鸣潮》玩家打造的**在线拉表分享社区**。平台在浏览器中提供接近原生 Excel 的编辑体验，支持公式、样式、数据完整保留，并围绕游戏数据构建了社区分享、数据观察、问卷系统等完整生态。

无论你是想制作 DPS 计算表、角色排轴表，还是分享游戏攻略与数据可视化结果，都可以通过 WutheringWavesDPS 快速完成并安全分享给其他玩家。

> 🎯 **设计目标**：让《鸣潮》玩家社区拥有真正属于玩家自己的、开源、免费、可协作的拉表与数据平台。

---

## ✨ 核心亮点

<table>
<tr>
<td width="50%">

### 📊 在线 Excel 编辑
- 基于 **Luckysheet**，浏览器内完整复刻 Excel 体验
- 导入/导出 `.xlsx`，**公式、样式、数据不变形**
- 支持在线保存、版本回退、社区分享

</td>
<td width="50%">

### 🏘️ 社区分享生态
- 上传拉表，生成唯一分享链接
- 点赞、收藏、搜索、按作者/编号筛选
- 管理员可置顶、审核、维护社区内容

</td>
</tr>
<tr>
<td width="50%">

### 📈 数据观察中心
- 贴吧发帖量、热帖排行、活跃度统计
- iOS 畅销榜多区服排行与趋势折线
- 自动化爬虫定时采集，数据可持续沉淀

</td>
<td width="50%">

### 📝 问卷系统
- 管理员创建问卷，玩家在线填写
- 实时统计与可视化报告
- 账号级限制，确保数据真实有效

</td>
</tr>
<tr>
<td width="50%">

### 🛡️ 安全与隐私
- JWT 认证 + 密码哈希
- 日志中 IP 自动脱敏
- 搜索参数校验、上传 MIME 白名单
- 运行时数据与代码分离，拒绝敏感信息入仓

</td>
<td width="50%">

### 💻 管理后台
- 用户管理、公告发布、系统日志
- 爬虫调度监控、任务执行状态
- 备份导出、数据观察全局配置

</td>
</tr>
</table>

---

## 🖼️ 功能预览

<div align="center">

| 首页与社区 | 在线拉表编辑 | 数据观察中心 |
|:---:|:---:|:---:|
| 展示公告、入口导航、历史动态 | 浏览器内编辑 Excel，保留公式与样式 | 贴吧数据、iOS 榜单、趋势图表 |

</div>

---

## 🚀 快速开始

### 在线体验

直接访问已部署站点：

```
https://www.arcanamorning.tech/WutheringWavesDPS/
```

### 本地开发

#### 1. 克隆仓库

```bash
git clone https://github.com/NumInvis/WutheringWavesDPS.git
cd WutheringWavesDPS
```

#### 2. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 配置 JWT 密钥、管理员密码等

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，API 默认在 `http://localhost:8000`。

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│              Vue 3 + TypeScript + Element Plus              │
│                     Luckysheet / ECharts                    │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / WSS
┌───────────────────────────▼─────────────────────────────────┐
│                         Nginx                                │
│              静态资源 / 反向代理 / SSL 终结                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  前端 dist    │   │  FastAPI 后端  │   │  SQLite 数据库 │
│  (Vite Build) │   │  业务 API      │   │  用户/表格数据 │
└───────────────┘   └───────────────┘   └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  定时爬虫任务  │
                    │  贴吧 / iOS   │
                    └───────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | [Vue 3](https://vuejs.org/) + [TypeScript](https://www.typescriptlang.org/) |
| UI 组件库 | [Element Plus](https://element-plus.org/) |
| 构建工具 | [Vite](https://vitejs.dev/) |
| 表格组件 | [Luckysheet](https://github.com/dream-num/Luckysheet) |
| 图表库 | [ECharts](https://echarts.apache.org/) |
| 状态管理 | [Pinia](https://pinia.vuejs.org/) |
| 后端框架 | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) |
| 数据库 | SQLite（生产可切换 PostgreSQL） |
| 认证 | JWT + bcrypt |
| 爬虫 | aiohttp + asyncio |

---

## 📂 项目结构

```
WutheringWavesDPS/
├── backend/
│   ├── app/
│   │   ├── api/              # RESTful API 路由
│   │   ├── core/             # 配置、安全、日志、脱敏工具
│   │   ├── models/           # SQLAlchemy 数据模型
│   │   ├── schemas/          # Pydantic 数据校验
│   │   ├── services/         # 业务逻辑
│   │   ├── data/             # 贴吧/iOS 等采集数据
│   │   └── main.py           # FastAPI 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/            # 页面视图
│   │   ├── components/       # 公共组件
│   │   ├── styles/           # 主题与样式
│   │   ├── api/              # 接口封装
│   │   └── stores/           # Pinia 状态
│   ├── public/               # 静态资源
│   └── package.json
├── deploy/                   # Nginx / Supervisor / systemd 配置
├── DEPLOYMENT.md             # 生产部署指南
├── LICENSE
└── README.md
```

---

## 📦 生产部署

详细的部署步骤请参考 [`DEPLOYMENT.md`](DEPLOYMENT.md)。

简要流程：

```bash
# 1. 安装依赖并构建前端
cd frontend && npm install && npm run build
cd ../backend && pip install -r requirements.txt

# 2. 配置 Nginx（参考 deploy/nginx.conf）
sudo cp deploy/nginx.conf /etc/nginx/sites-available/wuthering-waves-dps
sudo ln -s /etc/nginx/sites-available/wuthering-waves-dps /etc/nginx/sites-enabled/

# 3. 配置进程守护（Supervisor / systemd）
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/wuthering-waves-dps.conf
sudo supervisorctl reread && sudo supervisorctl update

# 4. 申请 SSL 证书
sudo certbot --nginx -d www.arcanamorning.tech
```

---

## 🛡️ 安全说明

- **密码安全**：用户密码使用 bcrypt 哈希存储，JWT 密钥需通过环境变量配置。
- **IP 脱敏**：所有日志与下载记录中的 IP 地址均经过脱敏处理，仅保留前两位。
- **输入校验**：搜索接口对关键词长度与特殊字符进行严格校验，防止注入。
- **上传限制**：仅允许 `.xlsx` / `.xls` 格式，禁止宏启用文件，降低恶意文件风险。
- **运行时隔离**：数据库、用户上传文件、备份数据均不进入代码仓库，通过 `.gitignore` 隔离。

---

## 📝 更新日志

### v1.03 · 2026-03-23
- ✨ 新增问卷系统：创建、发布、填写、统计全链路
- ✨ 新增账号级问卷限制，保证数据真实性
- 🎨 优化前端交互与移动端适配
- 🐛 修复多个已知问题

### v1.02 · 2025-03-18
- ✨ 新增数据观察中心：贴吧、iOS 畅销榜、排名趋势
- ✨ 新增后端监控与爬虫调度
- ✨ 新增全局/个人设置
- 📱 全面优化移动端体验

### Beta 1.0 · 2025
- 🎉 项目首次发布
- ✨ 在线 Excel 编辑与社区分享
- ✨ 用户系统与管理员后台

完整更新日志见 [GitHub Releases](https://github.com/NumInvis/WutheringWavesDPS/releases)。

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'feat: add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 打开 Pull Request

请确保代码通过前端 lint / 后端类型检查，并保持提交信息清晰。

---

## 💖 支持我们

如果这个项目对你有帮助，欢迎通过爱发电支持我们：

[![爱发电](https://img.shields.io/badge/爱发电-赞助-ff69b4?style=for-the-badge)](https://afdian.com/a/r0xy0)

---

## 🔗 友情链接

- [鸣潮动作数据汇总](https://www.kdocs.cn/l/chWXEqFmFGvu)
- [安可网](https://encore.moe/)
- [鬼神莫能窥的 B 站空间](https://space.bilibili.com/274736623)
- [鸣潮数据库 - nanoka.cc](https://ww.nanoka.cc/)

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

---

<div align="center">

**Made with ❤️ by WutheringWavesDPS Team**

</div>
