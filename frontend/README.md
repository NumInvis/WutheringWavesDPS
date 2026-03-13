# 鸣潮排轴DPS计算器 - 前端

## 快速开始

### 环境要求

- Node.js 18+
- npm 或 pnpm

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── components/    # 可复用组件
│   ├── views/         # 页面组件
│   ├── stores/        # Pinia状态管理
│   ├── api/           # API客户端
│   ├── utils/         # 工具函数
│   ├── types/         # TypeScript类型定义
│   ├── router/        # 路由配置
│   ├── App.vue        # 根组件
│   └── main.ts        # 入口文件
├── public/            # 静态资源
├── index.html         # HTML模板
├── package.json       # 依赖配置
├── vite.config.ts     # Vite配置
└── tsconfig.json      # TypeScript配置
```

## 技术栈

- **核心框架**: Vue 3 + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite
- **测试**: Vitest
- **表格引擎**: Luckysheet + LuckyExcel
