"""
登录核心代码 - 严禁修改
此文件的任何修改都可能导致登录功能失效
"""
# 前端 API 客户端核心配置
API_BASE_URL = '/WutheringWavesDPS/api'

# 登录请求配置
LOGIN_CONFIG = {
    'endpoint': 'auth/login',  # 不带前导斜杠！
    'content_type': 'application/x-www-form-urlencoded',
    'timeout': 30000
}

# 后端认证配置
AUTH_CONFIG = {
    'token_url': '/WutheringWavesDPS/api/auth/login',
    'jwt_algorithm': 'HS256',
    'bcrypt_rounds': 12
}

# IP白名单
IP_WHITELIST = {
    '111.18.157.89',  # 管理员IP
    '127.0.0.1',
    '::1'
}
