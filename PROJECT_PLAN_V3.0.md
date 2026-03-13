# 鸣潮排轴DPS计算器 - 大型开源项目规划 V3.0

## 📋 项目概述

### 1.1 项目愿景
将鸣潮排轴DPS计算器从单用户工具升级为**面向多用户的开源协作平台**，提供：
- 完整的Excel级表格功能
- 表格社区分享平台
- Star评分与评价系统
- 分类、搜索、排序机制
- 企业级安全与性能保障

### 1.2 核心价值主张
| 维度 | 说明 |
|------|------|
| 🎯 用户体验 | 真正的Excel级无缝体验 |
| 👥 社区协作 | 用户分享、评分、讨论 |
| 🔒 安全可靠 | 防SQL注入、XSS、CSRF |
| ⚡ 高性能 | 支持多用户并发访问 |
| 📦 开源可扩展 | 模块化架构，易于贡献 |

---

## 🏗️ 系统架构设计

### 2.1 技术栈选择

#### 前端技术栈
| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 核心框架 | Vue 3 + TypeScript | 类型安全，组件化开发 |
| UI框架 | Element Plus | 企业级UI组件库 |
| 表格引擎 | Luckysheet + Univer | 双引擎支持，灵活切换 |
| 状态管理 | Pinia | 轻量级状态管理 |
| 路由 | Vue Router 4 | SPA路由管理 |
| 样式 | Tailwind CSS | 原子化CSS框架 |
| 构建工具 | Vite | 极速开发体验 |
| 测试 | Vitest + Playwright | 单元测试 + E2E测试 |

#### 后端技术栈
| 层级 | 技术选型 | 说明 |
|------|----------|------|
| Web框架 | FastAPI | 高性能异步框架，自动文档 |
| 数据库 | PostgreSQL | 企业级关系型数据库 |
| 缓存 | Redis | 会话缓存、排行榜缓存 |
| ORM | SQLAlchemy 2.0 | 异步ORM支持 |
| 认证 | JWT + OAuth2 | 安全认证机制 |
| 文件存储 | MinIO / S3 | 对象存储服务 |
| 任务队列 | Celery + Redis | 异步任务处理 |
| API文档 | OpenAPI + Swagger | 自动生成API文档 |
| 测试 | pytest | Python测试框架 |

#### DevOps技术栈
| 工具 | 用途 |
|------|------|
| Docker + Docker Compose | 容器化部署 |
| Nginx | 反向代理、负载均衡 |
| GitHub Actions | CI/CD流水线 |
| Prometheus + Grafana | 监控与告警 |
| ELK Stack | 日志收集与分析 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Web浏览器      │  │   移动端PWA      │  │   桌面Electron   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓ HTTPS/WSS
┌─────────────────────────────────────────────────────────────────────────┐
│                            负载均衡层 (Nginx)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              应用服务层                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  FastAPI Worker  │  │  FastAPI Worker  │  │  FastAPI Worker  │  │
│  │   (实例1-多线程)  │  │   (实例2-多线程)  │  │   (实例3-多线程)  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              数据存储层                                   │
├──────────────────────────────┬──────────────────────────────────────────┤
│  ┌──────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │   PostgreSQL (主)    │  │  │          Redis Cluster            │  │
│  │   业务数据、用户表   │  │  │  会话缓存、排行榜、限流、队列     │  │
│  └──────────────────────┘  │  └──────────────────────────────────┘  │
├──────────────────────────────┼──────────────────────────────────────────┤
│  ┌──────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │   MinIO / S3        │  │  │      Elasticsearch (可选)        │  │
│  │   Excel文件、附件     │  │  │      全文搜索、日志分析          │  │
│  └──────────────────────┘  │  └──────────────────────────────────┘  │
└──────────────────────────────┴──────────────────────────────────────────┘
```

---

## 🗄️ 数据库设计

### 3.1 核心数据模型

#### 用户表 (users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### 表格表 (spreadsheets)
```sql
CREATE TABLE spreadsheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    tags TEXT[],
    is_public BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    star_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT,
    thumbnail_url VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_spreadsheets_user ON spreadsheets(user_id);
CREATE INDEX idx_spreadsheets_category ON spreadsheets(category);
CREATE INDEX idx_spreadsheets_is_public ON spreadsheets(is_public);
CREATE INDEX idx_spreadsheets_stars ON spreadsheets(star_count DESC);
CREATE INDEX idx_spreadsheets_created ON spreadsheets(created_at DESC);
CREATE INDEX idx_spreadsheets_tags ON spreadsheets USING GIN(tags);
```

#### Star/点赞表 (stars)
```sql
CREATE TABLE stars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    spreadsheet_id UUID REFERENCES spreadsheets(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, spreadsheet_id)
);

CREATE INDEX idx_stars_user ON stars(user_id);
CREATE INDEX idx_stars_spreadsheet ON stars(spreadsheet_id);
```

#### 分类表 (categories)
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO categories (name, slug, description, icon, sort_order) VALUES
('角色计算', 'character', '单个角色伤害计算模板', '👤', 1),
('队伍排轴', 'team', '完整队伍DPS排轴', '👥', 2),
('声骸搭配', 'echo', '声骸选择与搭配方案', '🎭', 3),
('机制研究', 'mechanics', '游戏机制深度研究', '🔬', 4),
('教程模板', 'tutorial', '新手教程与示例', '📚', 5);
```

---

## 📅 项目实施计划

### 阶段一：项目重构与基础架构 (4-6周)

#### 里程碑 1.1：代码库清理与重构 (1周)
- [ ] **移除硬编码模板**
  - 删除前端"弗洛洛拉表"和"陆赫斯拉表"按钮
  - 移除相关的硬编码文件引用
  - 清理uploads目录中的示例文件（移至文档）
  - 更新文档，移除模板相关说明

- [ ] **代码库标准化**
  - 建立项目目录结构规范
  - 配置ESLint + Prettier
  - 配置Black + isort (Python)
  - 建立Git提交规范（Conventional Commits）
  - 添加.gitignore文件

- [ ] **创建项目基础结构**
  ```
  wuwa-calc/
  ├── frontend/                 # 前端Vue应用
  │   ├── src/
  │   │   ├── components/      # 可复用组件
  │   │   ├── views/          # 页面组件
  │   │   ├── stores/         # Pinia状态管理
  │   │   ├── api/            # API客户端
  │   │   ├── utils/          # 工具函数
  │   │   └── types/          # TypeScript类型定义
  │   ├── public/
  │   └── package.json
  ├── backend/                 # 后端FastAPI应用
  │   ├── app/
  │   │   ├── api/            # API路由
  │   │   ├── models/         # SQLAlchemy模型
  │   │   ├── schemas/        # Pydantic模式
  │   │   ├── core/           # 核心配置
  │   │   ├── services/       # 业务逻辑
  │   │   └── tests/          # 测试
  │   ├── alembic/            # 数据库迁移
  │   └── requirements.txt
  ├── docker/                  # Docker配置
  ├── docs/                    # 项目文档
  └── README.md
  ```

#### 里程碑 1.2：后端基础架构 (2周)
- [ ] **FastAPI项目初始化**
  - 配置项目结构
  - 设置数据库连接（PostgreSQL）
  - 配置Redis缓存
  - 设置CORS、安全头
  - 配置日志系统

- [ ] **用户认证系统**
  - 实现JWT认证
  - 用户注册/登录/登出
  - 密码重置功能
  - 邮箱验证
  - OAuth2集成（GitHub、Google）

- [ ] **核心API框架**
  - RESTful API设计规范
  - 统一响应格式
  - 错误处理中间件
  - 请求限流中间件
  - API版本管理

- [ ] **数据库设计与迁移**
  - 创建所有核心表
  - 编写Alembic迁移脚本
  - 种子数据初始化
  - 索引优化

#### 里程碑 1.3：前端基础架构 (2周)
- [ ] **Vue 3项目初始化**
  - Vite + Vue 3 + TypeScript
  - 配置Tailwind CSS
  - 配置Element Plus
  - 配置路由（Vue Router）
  - 配置状态管理（Pinia）

- [ ] **基础UI组件**
  - 导航栏组件
  - 页脚组件
  - 用户认证页面（登录/注册）
  - 响应式布局系统
  - 加载状态、错误提示组件

- [ ] **API客户端封装**
  - Axios实例配置
  - 请求/响应拦截器
  - 认证Token管理
  - 错误处理
  - TypeScript类型定义

### 阶段二：核心功能开发 (6-8周)

#### 里程碑 2.1：表格核心功能 (2周)
- [ ] **Luckysheet深度集成**
  - 封装Vue组件
  - 实现文件导入（.xlsx, .xls）
  - 实现文件导出（.xlsx）
  - 实现公式引擎
  - 百分比公式自动转换
  - 单元格格式保留

- [ ] **表格编辑功能**
  - 实时自动保存
  - 撤销/重做
  - 单元格合并
  - 条件格式
  - 数据验证

#### 里程碑 2.2：保存到服务器 (1周)
- [ ] **后端API实现**
  - 文件上传到MinIO/S3
  - 表格元数据保存
  - 版本控制（可选）
  - 访问权限控制

- [ ] **前端功能**
  - "保存到服务器"按钮
  - 保存状态反馈
  - 自动保存（5分钟间隔）
  - 保存历史记录

#### 里程碑 2.3：表格社区功能 (3周)
- [ ] **表格展示页面**
  - 表格卡片列表
  - 网格/列表视图切换
  - 表格详情页
  - 在线预览功能
  - 下载功能

- [ ] **Star评分系统**
  - 点赞/取消点赞
  - 1-5星评分
  - 评分评论
  - 评分统计展示

- [ ] **分类与标签系统**
  - 分类浏览
  - 标签管理
  - 分类筛选
  - 热门标签云

- [ ] **搜索与排序**
  - 全文搜索（Elasticsearch）
  - 关键词高亮
  - 多维度排序（最新、最热、评分）
  - 高级筛选

#### 里程碑 2.4：用户个人中心 (1周)
- [ ] **个人资料页**
  - 头像、昵称、简介编辑
  - 密码修改
  - 账号设置

- [ ] **我的表格**
  - 已发布表格管理
  - 草稿箱
  - 表格统计

- [ ] **收藏与历史**
  - Starred表格列表
  - 浏览历史
  - 下载历史

### 阶段三：社区与交互 (4-6周)

#### 里程碑 3.1：评论与讨论 (2周)
- [ ] **评论系统**
  - 表格评论区
  - 回复功能
  - 评论点赞
  - 举报功能

- [ ] **通知系统**
  - 站内消息
  - 邮件通知
  - 实时通知（WebSocket）

#### 里程碑 3.2：排行榜与推荐 (2周)
- [ ] **排行榜**
  - 每日/每周/每月热门
  - 新星表格
  - 优质作者榜
  - Redis缓存优化

- [ ] **推荐系统**
  - 相关表格推荐
  - 基于用户兴趣
  - 基于内容相似度

#### 里程碑 3.3：社交功能 (1-2周)
- [ ] **关注系统**
  - 关注用户
  - 粉丝列表
  - 动态推送

- [ ] **分享功能**
  - 社交平台分享
  - 嵌入代码生成
  - 短链接生成

### 阶段四：优化与完善 (4-6周)

#### 里程碑 4.1：性能优化 (2周)
- [ ] **前端性能**
  - 代码分割与懒加载
  - 虚拟列表（大数据量）
  - 图片懒加载
  - 缓存策略

- [ ] **后端性能**
  - 数据库查询优化
  - Redis缓存策略
  - API响应压缩
  - CDN集成

- [ ] **性能测试**
  - 负载测试（Locust）
  - 压力测试
  - 性能基准建立

#### 里程碑 4.2：安全加固 (2周)
- [ ] **安全审计**
  - SQL注入防护
  - XSS攻击防护
  - CSRF防护
  - 文件上传安全

- [ ] **安全功能**
  - 二步验证（2FA）
  - 登录IP限制
  - 异常行为检测
  - 数据加密

#### 里程碑 4.3：测试与质量 (1-2周)
- [ ] **单元测试**
  - 前端测试覆盖率 > 80%
  - 后端测试覆盖率 > 85%
  - CI自动运行测试

- [ ] **E2E测试**
  - 核心用户流程
  - 跨浏览器测试
  - 移动端测试

- [ ] **代码质量**
  - SonarQube代码扫描
  - 安全漏洞扫描
  - 代码审查流程

### 阶段五：部署与上线 (2-3周)

#### 里程碑 5.1：容器化部署 (1周)
- [ ] **Docker配置**
  - 多阶段构建
  - Docker Compose开发环境
  - 生产环境配置

- [ ] **CI/CD流水线**
  - GitHub Actions配置
  - 自动测试
  - 自动部署

#### 里程碑 5.2：监控与运维 (1周)
- [ ] **监控系统**
  - Prometheus指标采集
  - Grafana仪表板
  - 告警规则配置

- [ ] **日志系统**
  - ELK Stack配置
  - 日志聚合
  - 日志分析

#### 里程碑 5.3：正式上线 (1周)
- [ ] **域名与SSL**
  - 域名配置
  - SSL证书（Let's Encrypt）
  - HTTPS强制跳转

- [ ] **上线检查清单**
  - [ ] 数据库备份策略
  - [ ] 灾难恢复方案
  - [ ] 服务级别协议（SLA）
  - [ ] 用户文档
  - [ ] 管理员手册

---

## 🔒 安全保障措施

### 5.1 常见安全漏洞防护

| 漏洞类型 | 防护措施 |
|---------|---------|
| **SQL注入** | 使用ORM参数化查询，禁止原生SQL拼接 |
| **XSS攻击** | 内容安全策略(CSP)，输出编码，DOMPurify |
| **CSRF攻击** | SameSite cookies，CSRF token |
| **文件上传** | 文件类型验证，大小限制，随机文件名，病毒扫描 |
| **暴力破解** | 登录限流，验证码，账户锁定 |
| **会话劫持** | HttpOnly cookies，Secure标志，会话过期 |
| **敏感数据泄露** | 密码bcrypt哈希，敏感数据加密 |

### 5.2 安全审查流程
1. **代码审查**：每PR必须经过至少1人审查
2. **自动化扫描**：CI/CD中集成安全扫描工具
3. **定期审计**：每季度进行一次完整安全审计
4. **漏洞奖励**：建立漏洞赏金计划

---

## 📊 质量保障计划

### 6.1 测试策略

| 测试类型 | 工具 | 覆盖率目标 | 执行频率 |
|---------|------|-----------|---------|
| 单元测试 | Vitest / pytest | 前端80%，后端85% | 每次提交 |
| 集成测试 | Playwright / pytest | 核心流程100% | 每日 |
| E2E测试 | Playwright / Cypress | 关键用户路径 | 每周 |
| 性能测试 | Locust / k6 | - | 里程碑结束 |
| 安全测试 | OWASP ZAP | - | 每月 |
| 兼容性测试 | BrowserStack | 主流浏览器 | 发布前 |

### 6.2 性能指标

| 指标 | 目标值 |
|------|--------|
| 页面加载时间 | < 2秒 (95分位) |
| API响应时间 | < 200ms (95分位) |
| 并发用户支持 | ≥ 1000 |
| 数据库查询 | < 50ms (95分位) |
| 可用性 | 99.9% |

---

## 👥 团队与协作

### 7.1 团队角色

| 角色 | 职责 | 人数建议 |
|------|------|---------|
| **技术负责人** | 架构设计、技术决策、代码审查 | 1 |
| **前端开发** | Vue组件、用户界面、交互体验 | 2-3 |
| **后端开发** | API设计、数据库、业务逻辑 | 2 |
| **全栈开发** | 前后端衔接、DevOps | 1 |
| **UI/UX设计** | 界面设计、用户体验优化 | 1 |
| **测试工程师** | 测试策略、质量保障 | 1 |
| **社区运营** | 文档、社区管理、用户支持 | 1 |

### 7.2 开发流程

1. **需求分析** → 2. **技术设计** → 3. **开发实现** → 4. **代码审查** → 5. **测试验证** → 6. **部署上线**

### 7.3 版本控制策略

| 分支 | 用途 |
|------|------|
| `main` | 生产环境，稳定版本 |
| `develop` | 开发分支，集成测试 |
| `feature/*` | 功能开发分支 |
| `hotfix/*` | 紧急修复分支 |
| `release/*` | 发布准备分支 |

---

## 📈 项目里程碑时间线

```
第1-2周  ──────────────────  阶段一：项目重构与基础架构
   ↓
第3-6周  ──────────────────  阶段二：核心功能开发
   ↓
第7-10周 ──────────────────  阶段三：社区与交互
   ↓
第11-14周──────────────────  阶段四：优化与完善
   ↓
第15-16周──────────────────  阶段五：部署与上线
   ↓
     🎉 正式发布
```

---

## 📚 文档计划

| 文档类型 | 内容 | 负责人 |
|---------|------|--------|
| **README** | 项目介绍、快速开始、功能特性 | 技术负责人 |
| **架构文档** | 系统设计、技术选型、API文档 | 技术负责人 |
| **用户手册** | 使用指南、教程视频、FAQ | 社区运营 |
| **开发者文档** | 贡献指南、开发环境搭建 | 全栈开发 |
| **部署文档** | 生产部署、运维指南 | DevOps |
| **API文档** | OpenAPI/Swagger自动生成 | 后端开发 |

---

## 🎯 成功标准

### 功能完整性
- [ ] 完整的Excel级表格编辑功能
- [ ] 表格保存到服务器
- [ ] 社区分享平台
- [ ] Star评分系统
- [ ] 搜索、分类、排序

### 技术质量
- [ ] 测试覆盖率达标（前端80%，后端85%）
- [ ] 性能指标达成
- [ ] 通过安全审计
- [ ] 代码审查流程建立

### 社区指标（上线后3个月）
- [ ] 注册用户 ≥ 1000
- [ ] 分享表格 ≥ 500
- [ ] 日活用户 ≥ 100
- [ ] Star总数 ≥ 5000
- [ ] GitHub Stars ≥ 200

---

## 🚀 下一步行动

1. **立即开始**：成立核心团队，确定技术负责人
2. **第一周**：完成代码库清理，建立项目结构
3. **第二周**：初始化前后端项目，配置CI/CD
4. **持续进行**：每周同步进度，月度里程碑评审

---

**文档版本**: V3.0  
**最后更新**: 2026-03-13  
**维护者**: 项目核心团队
