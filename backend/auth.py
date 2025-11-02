# backend/auth.py
import datetime
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

# config에서 설정값 임포트
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """ JWT 액세스 토큰을 생성합니다. """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, default_key: str) -> dict:
    """ JWT 토큰을 검증하고 페이로드를 반환합니다. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, default_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception
