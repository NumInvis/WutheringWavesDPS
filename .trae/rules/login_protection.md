# 登录相关代码保护规则

## 禁止修改的文件

以下文件是登录功能的核心代码，**严禁修改**：

### 前端
- `frontend/src/api/index.ts` - API客户端，登录请求逻辑
- `frontend/src/stores/user.ts` - 用户状态管理
- `frontend/src/views/Login.vue` - 登录页面

### 后端
- `backend/app/api/auth.py` - 认证API
- `backend/app/core/security.py` - 密码哈希和JWT
- `backend/app/core/rate_limit.py` - 登录速率限制
- `backend/app/models/user.py` - 用户模型

## 登录流程说明

### 前端登录请求
```typescript
// 正确的请求方式
const response = await this.client.post('auth/login', params, {
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
})
```

**注意**：
- 路径是 `auth/login`，不是 `/auth/login`（不带前导斜杠）
- Content-Type 是 `application/x-www-form-urlencoded`
- 使用 `URLSearchParams` 构建请求体

### 后端登录验证
```python
# OAuth2PasswordRequestForm 需要 form-data 格式
form_data: OAuth2PasswordRequestForm = Depends()
# 验证密码
verify_password(form_data.password, user.password_hash)
```

### 密码哈希
```python
# bcrypt 哈希，密码限制72字节
password = password[:72]
bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
```

## 常见错误

1. **请求路径错误**：`/auth/login` 会忽略 baseURL
2. **Content-Type错误**：不能用 `multipart/form-data`
3. **数据库重建**：会丢失用户数据
4. **模型导入错误**：确保 User 模型正确导入

## 添加新功能时的注意事项

1. 不要修改 `Base.metadata.create_all()` 的位置
2. 不要修改用户模型的字段
3. 不要修改登录相关的中间件逻辑
4. 新增模型时，确保正确导入 Base
5. 不要在 `.env` 中硬编码密码
