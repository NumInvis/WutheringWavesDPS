# 鸣潮排轴DPS计算器

一个面向多用户的开源协作平台，提供完整的Excel级表格功能、社区分享和评分系统。

## 📋 项目概述

本项目将鸣潮排轴DPS计算器从单用户工具升级为面向多用户的开源协作平台，提供：
- ✨ 完整的Excel级表格功能（Luckysheet）
- 📤 表格保存到服务器
- 👥 社区分享平台
- ⭐ Star评分与评价系统
- 🏷️ 分类、搜索、排序机制
- 🔒 企业级安全与性能保障

## 🏗️ 项目架构

```
wuwa-calc-final/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── api/         # API路由 (auth, spreadsheets, stars, categories)
│   │   ├── models/      # 数据库模型 (User, Spreadsheet, Star, Category)
│   │   ├── schemas/     # Pydantic模式
│   │   ├── core/        # 核心配置 (config, database, security)
│   │   └── main.py      # 应用入口
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # Vue 3前端
│   ├── src/
│   │   ├── views/       # 页面组件 (Home, Calculator, Community, Login, Register)
│   │   ├── stores/      # Pinia状态管理 (user store)
│   │   ├── api/         # API客户端
│   │   ├── router/      # 路由配置
│   │   ├── components/  # 可复用组件 (CyberCard, CyberButton, CharacterTag, UploadDialog)
│   │   ├── styles/      # 全局主题样式
│   │   ├── data/        # 鸣潮角色数据
│   │   ├── App.vue
│   │   └── main.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml    # Docker Compose配置
├── PROJECT_PLAN_V3.0.md  # 完整项目规划
└── README.md            # 本文件
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd wuwa-calc-final

# 启动所有服务
docker-compose up -d

# 访问服务
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 方式二：本地开发

#### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库连接等
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

#### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问前端：http://localhost:5173

## 📚 文档

- [完整项目规划](./PROJECT_PLAN_V3.0.md) - 16周全周期开发计划
- [后端文档](./backend/README.md)
- [前端文档](./frontend/README.md)

## 🛠️ 技术栈

### 后端
- **Web框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15+ / SQLite (开发)
- **ORM**: SQLAlchemy 2.0
- **缓存**: Redis 7+
- **认证**: JWT + Passlib (bcrypt)
- **容器化**: Docker + Docker Compose

### 前端
- **核心框架**: Vue 3.4+ + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite
- **表格引擎**: Luckysheet + LuckyExcel
- **HTTP客户端**: Axios
- **主题**: 赛博朋克科技感设计

## 📋 核心功能

### ✅ 已完成

#### 后端功能
- [x] 用户认证系统（注册/登录/JWT令牌）
- [x] 管理员账户初始化（ROXY/moningbot1，bcrypt哈希）
- [x] 首次登录即注册功能
- [x] 完整的表格CRUD API
- [x] 区域分类（拉表区/其他区）
- [x] 角色标签系统
- [x] 表格状态管理（草稿/发布/下架/精华）
- [x] Star评分系统（创建/更新/删除）
- [x] 分类管理API
- [x] 搜索、筛选、排序、分页
- [x] 权限控制（用户只能操作自己的表格，管理员可下架/精华）
- [x] 自动初始化默认分类
- [x] CORS配置
- [x] Docker容器化

#### 前端功能
- [x] 项目初始化（Vue 3 + TypeScript + Element Plus）
- [x] 用户认证页面（登录/注册）
- [x] 赛博朋克科技感登录界面（粒子动画、扫描线、故障效果）
- [x] 导航栏和用户菜单
- [x] API客户端封装（Axios + 拦截器）
- [x] 状态管理（Pinia User Store）
- [x] 路由守卫
- [x] 全局主题系统（赛博朋克配色）
- [x] 可复用组件（CyberCard, CyberButton, CharacterTag）
- [x] 文件上传对话框（区域选择、角色标签、草稿/发布）
- [x] Calculator页面集成
- [x] Community页面完善（区域筛选、角色标签筛选、精华筛选）
- [x] Home页面完全重设计（Hero区域、功能卡片、CTA区域）
- [x] App.vue完全重设计（粒子动画、科技感导航）
- [x] Docker容器化 + Nginx配置

### 🚧 进行中
- [ ] Luckysheet深度集成
- [ ] 表格在线预览

### 📋 待开始
- [ ] 评论系统
- [ ] 排行榜
- [ ] 关注系统
- [ ] 性能优化
- [ ] 安全审计
- [ ] 单元测试和E2E测试

## 🔒 安全特性

- 密码bcrypt哈希（管理员密码安全存储）
- JWT令牌认证
- SQL注入防护（ORM参数化查询）
- XSS防护（内容安全策略）
- CSRF防护（SameSite cookies）
- 文件上传验证
- 权限控制（拥有者/管理员/普通用户）
- .gitignore保护敏感文件

## 👥 管理员账户

- **用户名**: ROXY
- **密码**: moningbot1

> 注意：密码使用bcrypt哈希存储，不会明文出现在代码中。

## 🏷️ 区域分类

- **拉表区**: 需要打上角色标签的表格
- **其他区**: 普通表格，不需要角色标签

## 🎮 鸣潮角色

支持20+鸣潮角色，包括：
- 弗洛洛、陆赫斯、爱弥斯、希维尔、蕾娜、娜米、菲尔、黛安娜等

## 👥 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

项目地址: https://github.com/NumInvis/WutheringWavesHelp

---

**项目版本**: 1.0.0-beta1  
**最后更新**: 2026-03-13  
**开发进度**: Beta版本发布
