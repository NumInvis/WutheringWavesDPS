# 鸣潮排轴DPS计算器 - 后端

## 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL 15+ (或使用SQLite进行开发)
- Redis 7+

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/
│   ├── api/           # API路由
│   ├── models/        # 数据库模型
│   ├── schemas/       # Pydantic模式
│   ├── core/          # 核心配置
│   ├── services/      # 业务逻辑
│   ├── tests/         # 测试
│   └── main.py        # 应用入口
├── alembic/           # 数据库迁移
├── requirements.txt   # 依赖
└── .env.example       # 环境变量示例
```

## 技术栈

- **Web框架**: FastAPI
- **数据库**: PostgreSQL + SQLAlchemy 2.0
- **缓存**: Redis
- **认证**: JWT + Passlib
- **测试**: pytest
