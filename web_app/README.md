# 鸣潮动作数据汇总 - Web版

将《鸣潮动作数据汇总.xlsx》移植到网站的完整解决方案。

## 项目结构

```
web_app/
├── api.py                 # Flask后端API
├── models.py              # SQLAlchemy数据库模型
├── import_excel.py        # Excel数据导入脚本
├── wuwa_data.db           # SQLite数据库（自动生成）
├── start.bat              # Windows启动脚本
├── frontend/              # Vue.js前端项目
│   ├── package.json
│   ├── vue.config.js
│   ├── public/
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       ├── store/
│       └── views/
│           ├── Home.vue          # 首页
│           ├── Characters.vue    # 角色列表
│           ├── CharacterDetail.vue # 角色详情
│           ├── Actions.vue       # 动作查询
│           ├── Echoes.vue        # 声骸数据库
│           └── Calculator.vue    # 伤害计算器
```

## 功能特性

### 后端API
- **角色管理**: 47个角色的完整数据
- **动作查询**: 3,786个动作的详细帧数数据
- **声骸数据库**: 230个声骸的召唤动作数据
- **高级筛选**: 按帧数、削韧、协奏回收等多维度筛选
- **动作对比**: 支持多个动作并排对比

### 前端界面
- **首页**: 数据统计可视化（ECharts图表）
- **角色数据库**: 卡片式展示，支持性别/体型/属性筛选
- **角色详情**: 动作类型分布、表格/卡片双视图
- **动作查询**: 高级筛选器、批量选择对比
- **声骸数据库**: 声骸列表、详细信息弹窗
- **伤害计算器**: 面板配置、动作队列、实时DPS计算

## 快速启动

### 方式1: 使用启动脚本（推荐）

```bash
cd web_app
start.bat
```

### 方式2: 手动启动

**1. 安装依赖**
```bash
pip install flask flask-cors sqlalchemy pandas openpyxl
```

**2. 导入数据（首次运行）**
```bash
python import_excel.py
```

**3. 启动后端**
```bash
python api.py
```

**4. 启动前端（可选）**
```bash
cd frontend
npm install
npm run serve
```

## API文档

### 角色相关
- `GET /api/characters` - 获取角色列表
- `GET /api/characters/:id` - 获取角色详情
- `GET /api/characters/:id/actions` - 获取角色动作

### 动作查询
- `GET /api/actions` - 动作高级查询（支持筛选、分页）
- `GET /api/actions/:id` - 获取动作详情
- `POST /api/actions/compare` - 对比多个动作

### 声骸
- `GET /api/echoes` - 获取声骸列表
- `GET /api/echoes/:id` - 获取声骸详情

### 统计
- `GET /api/stats` - 获取统计数据
- `GET /api/filters` - 获取筛选选项

## 数据说明

数据来源于《鸣潮动作数据汇总.xlsx》，包含12个Sheet：
- 索引: 角色分类导航
- 角色-女: 女性角色动作数据（约2000+行）
- 角色-男: 男性角色动作数据（约1000+行）
- 声骸: 声骸召唤动作数据
- 伤害配置/伤害计算: 面板配置和计算

## 技术栈

**后端:**
- Python 3.8+
- Flask + Flask-CORS
- SQLAlchemy (ORM)
- SQLite (数据库)
- Pandas (数据处理)

**前端:**
- Vue.js 3
- Vue Router 4
- Vuex 4
- Element Plus (UI组件库)
- ECharts (图表)
- Axios (HTTP请求)

## 浏览器访问

- 后端API: http://localhost:12056
- 前端开发服务器: http://localhost:13078

## 更新数据

如需更新数据，修改Excel文件后重新运行：
```bash
python import_excel.py
```

## 许可证

本项目仅供学习和研究使用。
