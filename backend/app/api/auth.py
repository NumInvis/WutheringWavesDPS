"""
认证相关 API。
"""
import re
import uuid
from datetime import timedelta, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenData,
    PasswordChange
)

router = APIRouter(prefix="/api/auth", tags=["认证"])
settings = get_settings()

# Allow optional auth for public endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _safe_email_local_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._+-]", "-", value or "")
    return cleaned or f"user-{uuid.uuid4().hex[:8]}"


def _make_placeholder_email(username: str) -> str:
    local_part = _safe_email_local_part(username)
    return f"{local_part}@wuwa.invalid"


def init_admin_user(db: Session):
    """初始化管理员账号（唯一管理员）。"""
    admin_username = settings.admin_username
    if not admin_username:
        return

    admin_email = settings.admin_email or _make_placeholder_email(admin_username)

    password_hash = settings.admin_password_hash
    if settings.admin_password:
        password_hash = get_password_hash(settings.admin_password)

    if not password_hash:
        return

    admin_user = db.query(User).filter(User.username == admin_username).first()
    if admin_user:
        admin_user.email = admin_email
        admin_user.is_admin = True
        admin_user.is_verified = True
        admin_user.is_active = True
        admin_user.role = "admin"
        if settings.admin_force_password:
            admin_user.password_hash = password_hash
    else:
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=password_hash,
            display_name=admin_username,
            is_admin=True,
            is_verified=True,
            is_active=True,
            role="admin"
        )
        db.add(admin_user)

    if settings.admin_singleton:
        db.query(User).filter(
            User.username != admin_username,
            User.is_admin == True
        ).update(
            {"is_admin": False, "role": "user"},
            synchronize_session=False
        )

    test_user = db.query(User).filter(User.username == "person").first()
    if not test_user:
        test_user = User(
            username="person",
            email="person@wuwa.invalid",
            password_hash=get_password_hash("person"),
            display_name="person",
            is_admin=False,
            is_verified=True,
            is_active=True,
            role="user"
        )
        db.add(test_user)

    db.commit()
    db.refresh(admin_user)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户（必须登录）。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（允许匿名）。"""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id: str = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户。"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户。"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册。"""
    import re
    username = user_data.username.strip()
    
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名只能包含英文和数字"
        )
    
    if not re.match(r'^[a-zA-Z0-9]+$', user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码只能包含英文和数字"
        )
    
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )

    # 邮箱可选：未提供则使用占位邮箱（需合法格式，避免响应序列化失败）
    email = (user_data.email or "").strip() or None
    if email:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    else:
        email = _make_placeholder_email(username)

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        display_name=user_data.display_name or username,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio
    )

    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="注册失败：用户名或邮箱已存在"
        )
    db.refresh(db_user)

    return db_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新当前用户信息。"""
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录。"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在，请先注册",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息。"""
    return current_user


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改当前用户密码。"""
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码已修改"}
