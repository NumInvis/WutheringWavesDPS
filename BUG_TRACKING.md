# Bug Tracking Report - WutheringWavesDPS

**生成日期**: 2026-03-14
**版本**: Beta 1.0

---

## 一、已发现Bug清单

### 🔴 Critical (严重)

#### Bug #1: Excel完全无法加载
**状态**: 🔧 修复中
**优先级**: P0

**表现**:
- 工作区页面无法显示Excel表格
- 导入Excel文件后无响应
- 控制台无 `[Excel Load]` 日志输出

**复现步骤**:
1. 访问 http://localhost:14880/calculator
2. 点击"导入Excel"
3. 选择任意.xlsx文件
4. 观察：表格区域空白，无错误提示

**错误信息**:
- 浏览器控制台无任何 `[Excel Load]` 相关日志
- test-excel.html 可以正常运行，说明Luckysheet本身没问题

**初步分析**:
- Vue组件中的脚本加载逻辑可能有问题
- CDN加载可能失败但没有正确报错
- `loadAllScripts()` 函数中的Promise可能没有正确resolve

**根因假设**:
1. 脚本加载顺序问题
2. `waitForLuckysheet()` 超时或失败
3. `initEmptySheet()` 在DOM未准备好时执行

---

#### Bug #2: AdminLogs页面ElTag type="" 错误
**状态**: 🔧 修复中
**优先级**: P0

**表现**:
- 访问日志页面时控制台报错
- 错误信息：`Invalid prop: custom validator check failed for prop "type"`
- 导致页面渲染异常

**复现步骤**:
1. 管理员登录
2. 点击"日志"导航
3. 观察控制台错误

**错误信息**:
```
[Vue warn]: Invalid prop: custom validator check failed for prop "type". 
Expected one of ["primary", "success", "info", "warning", "danger"], got value "".
at <ElTag type="" size="small" >
```

**初步分析**:
- `getLogType()` 函数返回空字符串
- 某些日志的 `level` 字段不在预期范围内
- 可能是 `undefined` 或 `null` 导致的

**已尝试修复**:
- 修改 `getLogType()` 添加默认值
- 强制转换 `level` 为字符串
- 但问题仍然存在，可能有其他调用点

---

### 🟠 High (高)

#### Bug #3: 递归更新警告
**状态**: 🔧 修复中
**优先级**: P1

**表现**:
- 访问日志页面时出现Vue警告
- 可能导致性能问题或无限循环

**错误信息**:
```
[Vue warn]: Maximum recursive updates exceeded in component <ElCard>.
This means you have a reactive effect that is mutating its own dependencies...
```

**初步分析**:
- `addRealtimeLog()` 函数直接修改 `logs.value`
- 可能触发Vue的响应式无限循环
- 日志订阅机制可能有问题

---

### 🟡 Medium (中)

#### Bug #4: 数据库事务不完整
**状态**: 📋 待修复
**优先级**: P2

**表现**:
- 删除表格时先删除stars再删除spreadsheet
- 如果中间失败，数据可能不一致

**代码位置**:
```python
# backend/app/api/spreadsheets.py:366-372
db.query(Star).filter(...).delete()  # 第一步
db.delete(spreadsheet)               # 第二步
db.commit()                          # 提交
```

**修复方案**:
- 使用事务包装确保原子性

---

#### Bug #5: N+1查询问题
**状态**: 📋 待修复
**优先级**: P2

**表现**:
- 表格列表查询时循环查询关联数据
- 性能随数据量增长而下降

**代码位置**:
```python
# backend/app/api/spreadsheets.py:202-204
for item in items:
    _hydrate_spreadsheet(item, current_user_id, db)
```

**修复方案**:
- 使用 `joinedload` 或批量查询优化

---

## 二、修复记录

### 已修复

| Bug | 修复时间 | 修复方案 | 验证状态 |
|-----|---------|---------|---------|
| 硬编码密码哈希 | 2026-03-14 | 改为环境变量读取 | ✅ |
| JWT密钥硬编码 | 2026-03-14 | 改为环境变量读取 | ✅ |
| 文件上传DoS漏洞 | 2026-03-14 | 流式读取 | ✅ |
| 前端XSS风险 | 2026-03-14 | 移除alert重写 | ✅ |

### 修复中

| Bug | 当前状态 | 下一步行动 |
|-----|---------|-----------|
| Excel加载失败 | 分析中 | 检查脚本加载逻辑 |
| ElTag type错误 | 分析中 | 检查所有调用点 |
| 递归更新警告 | 分析中 | 重构日志更新机制 |

---

## 三、测试计划

### 单元测试
- [ ] Excel解析功能测试
- [ ] 用户认证流程测试
- [ ] 表格CRUD操作测试

### 集成测试
- [ ] 端到端Excel导入导出
- [ ] 管理员功能完整流程
- [ ] 并发操作测试

### 性能测试
- [ ] 大数据量表格查询
- [ ] 文件上传性能
- [ ] 前端渲染性能

---

## 四、文档更新

### 需要更新的文档
- [ ] README.md - 添加已知问题
- [ ] API文档 - 补充错误码
- [ ] 部署文档 - 环境变量配置

---

*最后更新: 2026-03-14*
