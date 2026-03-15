"""
Application configuration.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import AliasChoices, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
PROJECT_ROOT = BASE_DIR.parent                 # wuwa_calc_final/
DATA_ROOT = PROJECT_ROOT.parent                # D:\素材\


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "WutheringWavesDPS"
    app_env: str = "development"
    app_debug: bool = True
    app_version: str = "Beta1.0"
    app_port: int = 14876

    # Database
    database_url: str = Field(
        default=f"sqlite:///{(BASE_DIR / 'wuwa_calc.db').as_posix()}"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT - 必须从环境变量读取，没有默认值
    jwt_secret_key: str = Field(
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY")
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Admin account - 密码必须从环境变量读取，不再强制重置密码
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_email: Optional[str] = Field(default=None, validation_alias="ADMIN_EMAIL")
    admin_password: Optional[str] = Field(default=None, validation_alias="ADMIN_PASSWORD")
    admin_password_hash: Optional[str] = Field(default=None, validation_alias="ADMIN_PASSWORD_HASH")
    admin_singleton: bool = True
    admin_force_password: bool = False  # 默认不强制重置密码

    # File storage
    storage_type: str = "local"
    upload_dir: str = str(BASE_DIR / "uploads")
    max_upload_size: int = 50 * 1024 * 1024
    minio_endpoint: str = Field(default="localhost:9000", validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="", validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="", validation_alias="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field(default="wuwa-calc-files", validation_alias="MINIO_BUCKET_NAME")
    minio_secure: bool = Field(default=False, validation_alias="MINIO_SECURE")

    # CORS
    cors_origins: List[str] = [
        "http://localhost:14876", 
        "http://127.0.0.1:14876",
        "http://localhost:14877", 
        "http://127.0.0.1:14877",
        "http://localhost:14878", 
        "http://127.0.0.1:14878",
        "http://localhost:14879", 
        "http://127.0.0.1:14879",
        "http://localhost:5173", 
        "http://localhost:3000",
        "http://www.arcanamorning.tech:14876",
        "https://www.arcanamorning.tech:14876",
        "http://www.arcanamorning.tech",
        "https://www.arcanamorning.tech"
    ]


@lru_cache()
def get_settings():
    """Get settings singleton."""
    settings = Settings()
    
    # 验证关键配置
    if not settings.jwt_secret_key or settings.jwt_secret_key == "your-super-secret-key-change-in-production":
        raise ValueError(
            "JWT_SECRET_KEY must be set in environment variables! "
            "Please set a secure random string."
        )
    
    return settings
