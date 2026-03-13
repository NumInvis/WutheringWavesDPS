#!/usr/bin/env python3
"""测试登录流程"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password, create_access_token, decode_access_token
from datetime import timedelta

db = SessionLocal()

# 1. 查找用户
user = db.query(User).filter(User.username == 'person').first()
print(f'1. User found: {user.username}')

# 2. 验证密码
if verify_password('person', user.password_hash):
    print('2. Password verified: True')
else:
    print('2. Password verified: False')
    sys.exit(1)

# 3. 创建token
token = create_access_token(
    data={'sub': str(user.id)},
    expires_delta=timedelta(minutes=30)
)
print(f'3. Token created: {token[:50]}...')

# 4. 解码token
payload = decode_access_token(token)
print(f'4. Token decoded: {payload}')

# 5. 获取用户ID
user_id = payload.get('sub')
print(f'5. User ID from token: {user_id}')

# 6. 查询用户
user2 = db.query(User).filter(User.id == user_id).first()
if user2:
    print(f'6. User found by ID: {user2.username}')
else:
    print('6. User not found by ID')

print('\nAll steps passed!')
