# WutheringWavesDPS 后端

WutheringWavesDPS 后端服务，基于 **FastAPI** 构建，提供用户认证、在线表格、社区分享、数据观察、问卷系统、爬虫调度等核心能力的 RESTful API。

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) |
| 数据库 | SQLite（默认）/ PostgreSQL（生产可选） |
| 认证 | JWT + bcrypt |
| 配置管理 | Pydantic Settings + `.env` |
| 任务调度 | asyncio + 后台任务 |
| 爬虫 | aiohttp |

---

## 📋 环境要求

- Python 3.10+
- 建议使用虚拟环境
- 生产环境可选 Redis / PostgreSQL

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少配置以下关键项：

```env
JWT_SECRET_KEY=your-secure-random-key
ADMIN_PASSWORD=your-secure-admin-password
```

### 3. 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📂 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── auth.py       # 认证相关
│   │   ├── spreadsheets.py # 表格管理
│   │   ├── uploads.py    # 文件上传
│   │   ├── tieba.py      # 贴吧数据
│   │   ├── survey.py     # 问卷系统
│   │   └── admin.py      # 管理员接口
│   ├── core/             # 核心模块
│   │   ├── config.py     # 应用配置
│   │   ├── security.py   # 密码与 JWT
│   │   ├── ip_utils.py   # IP 脱敏
│   │   └── logger.py     # 日志管理
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic 校验模型
│   ├── services/         # 业务逻辑
│   ├── data/             # 运行时采集数据
│   └── main.py           # FastAPI 入口
├── requirements.txt
└── .env.example
```

---

## 🔐 安全说明

- **JWT 密钥**：必须通过 `JWT_SECRET_KEY` 环境变量配置，禁止使用默认密钥。
- **管理员密码**：首次启动时通过 `ADMIN_PASSWORD` 初始化，生产环境务必使用强密码。
- **IP 脱敏**：`app/core/ip_utils.py` 统一处理 IP 脱敏，日志中不记录完整 IP。
- **上传安全**：仅允许 `.xlsx` / `.xls` 格式，校验 MIME 类型与文件签名。
- **输入校验**：关键接口对搜索参数等用户输入进行白名单校验。

---

## 🧪 开发命令

```bash
# 启动热重载开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式启动
uvicorn app.main:app --host 127.0.0.1 --port 14876 --workers 2
```

---

## 📡 API 概览

主要 API 分组：

| 路由前缀 | 说明 |
|----------|------|
| `/api/auth` | 注册、登录、密码修改 |
| `/api/spreadsheets` | 表格创建、编辑、分享、搜索 |
| `/api/uploads` | Excel 文件上传与下载 |
| `/api/tieba` | 贴吧数据统计与热帖 |
| `/api/app-ranking` | iOS 畅销榜数据 |
| `/api/survey` | 问卷创建、填写、统计 |
| `/api/admin` | 用户管理、日志、备份、设置 |

完整 API 文档请在服务启动后访问 `/docs`。

---

## 📝 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | 必填 |
| `JWT_ALGORITHM` | JWT 算法 | HS256 |
| `ADMIN_USERNAME` | 管理员用户名 | admin |
| `ADMIN_PASSWORD` | 管理员初始密码 | 必填 |
| `DATABASE_URL` | 数据库连接 | SQLite |
| `MAX_UPLOAD_SIZE` | 最大上传大小 | 52428800 |

更多配置详见 `.env.example`。
