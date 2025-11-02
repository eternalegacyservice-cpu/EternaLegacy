# backend/database_agent.py
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from jose import jwt
import bcrypt, datetime, os

# 내부 모듈 통합
from .config import SECRET_KEY, ALGORITHM, DB_MODE
from .db import get_db
from .auth import verify_access_token
# (✨ 수정) 'dependencies.py'에서 'oauth2_scheme'를 임포트합니다.
from .dependencies import User, TokenData, Will, oauth2_scheme
from .audit import audit # 감사 로깅 모듈

# --- (1. 인증 관련 DB 헬퍼) ---

def get_user_from_db(conn, cur, email: str) -> Optional[User]:
    """ 이메일을 사용하여 DB에서 User 객체를 가져옵니다. """
    placeholder = "%s" if DB_MODE == "production" else "?"
    # conn.row_factory 설정에 따라 dict 또는 Row 객체를 반환한다고 가정
    cur.execute(f"SELECT email, full_name, created_at FROM users WHERE email = {placeholder}", (email,))
    user_row = cur.fetchone()
    if user_row:
        return User.model_validate(dict(user_row))
    return None

def get_hashed_password(conn, cur, email: str) -> Optional[str]:
    """ 이메일을 사용하여 DB에서 해시된 비밀번호를 가져옵니다. """
    placeholder = "%s" if DB_MODE == "production" else "?"
    cur.execute(f"SELECT hashed_password FROM users WHERE email = {placeholder}", (email,))
    password_row = cur.fetchone()
    if password_row:
        # SQLite는 튜플, PostgreSQL은 DictRow를 반환할 수 있음
        return password_row["hashed_password"] if isinstance(password_row, dict) else password_row[0]
    return None

# --- (2. FastAPI 의존성) ---

def get_current_user_dependency(token: str = Depends(oauth2_scheme)) -> User:
    """ JWT 토큰을 검증하고 현재 사용자 객체를 반환하는 FastAPI 의존성 함수. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # auth.py의 로직 사용
        payload = verify_access_token(token, default_key=SECRET_KEY)
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
        token_data = TokenData(email=email)
    except Exception: # JWTError 등
        raise credentials_exception

    # DB 연결 및 사용자 조회 (db.py의 get_db 사용)
    try:
        with get_db() as (conn, cur):
            # PostgreSQL은 cursor_factory를 사용해 DictRow를 반환하도록 설정되었다고 가정
            cur = conn.cursor()
            user = get_user_from_db(conn, cur, email=token_data.email)
            cur.close()
    except Exception as e:
        audit(f"DB_ERROR: get_current_user: {e}")
        raise HTTPException(status_code=503, detail="DB service unavailable")

    if user is None: raise credentials_exception

    # 감사 로깅
    audit(f"USER_ACCESS: {user.email}")
    return user
