# WutheringWavesDPS

鸣潮拉表开源社区

## 功能特性

- Excel 在线编辑器（基于 Luckysheet）
- 社区分享表格
- 管理员置顶/删除功能
- 表格唯一编号
- 作者可编辑自己的表格
- 用户修改密码功能
- 按作者/编号搜索表格
- 实时日志监控系统
- 工作区状态保持（keep-alive）

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 默认账号

- 管理员: admin / admin124
- 测试用户：person / person

**注意**: 首次登录后请立即修改密码！

## 技术栈

- 后端: FastAPI + SQLite
- 前端: Vue 3 + Element Plus + Luckysheet

## License

MIT
