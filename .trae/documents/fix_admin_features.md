# 修复管理后台功能问题

## 问题分析

### 1. 系统日志"暂无日志"
**原因**：日志系统使用内存列表存储，但各API操作中没有调用 `add_log()` 函数记录日志。

**解决方案**：
- 在关键操作中添加日志记录调用
- 需要记录的操作包括：
  - 用户登录/登出
  - 表格上传/下载/删除
  - 公告发布/激活/删除
  - 用户注册
  - 管理员操作

### 2. 访问趋势没有正常展示
**原因**：
- 前端只支持选择天数（7天或30天），没有24小时选项
- 后端API只返回按小时统计的数据，没有聚合功能

**解决方案**：
- 后端：添加新的统计API，支持不同时间粒度
  - 24小时：按小时统计
  - 7天：按6小时聚合
  - 30天：按天聚合
- 前端：添加时间范围选择器（24h / 7天 / 30天）

### 3. 数据库显示异常
**原因**：
- `engine.url.database` 可能返回 None 或路径不正确
- 需要更健壮的数据库路径获取方式

**解决方案**：
- 改进数据库检查函数，使用更可靠的方式获取数据库信息
- 添加数据库类型判断（SQLite/PostgreSQL等）
- 对于SQLite，直接从配置获取路径

## 实施步骤

### 步骤1：修复系统日志记录
1. 在 `backend/app/api/auth.py` 中添加登录/登出日志
2. 在 `backend/app/api/spreadsheets.py` 中添加表格操作日志
3. 在 `backend/app/api/announcements.py` 中添加公告操作日志
4. 在 `backend/app/main.py` 中添加请求日志中间件

### 步骤2：改进访问统计API
1. 修改 `backend/app/api/visit_stats.py`：
   - 添加 `interval` 参数支持不同统计粒度
   - 24h：返回24条记录（按小时）
   - 7d：返回28条记录（每6小时一条）
   - 30d：返回30条记录（按天）

### 步骤3：改进前端访问趋势展示
1. 修改 `frontend/src/views/AdminCenter.vue`：
   - 添加时间范围选择器（24h / 7天 / 30天）
   - 根据选择的时间范围调整图表显示

### 步骤4：修复数据库健康检查
1. 修改 `backend/app/api/health.py`：
   - 改进数据库路径获取方式
   - 添加数据库类型判断
   - 对于SQLite，从配置获取路径

### 步骤5：修复前端日志API路径
1. 修改 `frontend/src/views/AdminCenter.vue`：
   - 修复日志API路径（`/api/admin/logs` -> `/admin/logs`）

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `backend/app/api/auth.py` | 添加登录/登出日志记录 |
| `backend/app/api/spreadsheets.py` | 添加表格操作日志记录 |
| `backend/app/api/announcements.py` | 添加公告操作日志记录 |
| `backend/app/api/visit_stats.py` | 添加时间粒度支持 |
| `backend/app/api/health.py` | 修复数据库检查逻辑 |
| `backend/app/main.py` | 添加请求日志中间件 |
| `frontend/src/views/AdminCenter.vue` | 改进访问趋势展示、修复API路径 |
