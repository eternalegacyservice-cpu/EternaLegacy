# backend/main.py (최종 FastAPI 앱)

from fastapi import FastAPI, Depends, HTTPException, status, Body, Request
from typing import List, Optional, Dict, Any
import json, os, stripe

# 내부 모듈 임포트
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES # 설정
from .db import get_db # DB 컨텍스트 매니저
from .dependencies import User, LoginRequest, Token, Will, WillVersionRequest # 모델 및 의존성
from .database_agent import get_current_user_dependency, get_hashed_password, get_user_from_db # DB/Auth 로직
from .business_service import create_new_will, notarize_current_version # 비즈니스 로직
from .auth import create_access_token # JWT 생성
from .audit import audit # 감사 로깅

app = FastAPI(title="EternaLegacy API", version="v1.0.0")

# --- (1. 인증 라우터 - legacy.py 통합) ---

@app.post("/api/v1/auth/token", response_model=Token)
async def login_for_access_token(form_data: LoginRequest = Body(...)):
    """ 이메일/비밀번호로 로그인하여 JWT 토큰을 발급받습니다. """
    try:
        with get_db() as conn:
            cur = conn.cursor()
            user = get_user_from_db(conn, cur, form_data.email)
            hashed_password = get_hashed_password(conn, cur, form_data.email)
            cur.close()
    except Exception as e:
        audit(f"LOGIN_FAIL_DB: {form_data.email} - {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")

    if user is None or not bcrypt.checkpw(form_data.password.encode('utf-8'), hashed_password.encode('utf-8')):
        audit(f"LOGIN_FAIL_CREDENTIALS: {form_data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # auth.py의 create_access_token 사용
    access_token = create_access_token(data={"sub": user.email})
    audit(f"LOGIN_SUCCESS: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}

# --- (2. 유언장 라우터 - legacy.py 통합) ---

@app.get("/api/v1/wills/me", response_model=List[Will])
def list_my_wills(current_user: User = Depends(get_current_user_dependency)):
    """ 현재 사용자가 소유한 모든 유언장을 조회합니다. """
    # (로직 생략: database_agent 또는 business_service 호출)
    audit(f"WILL_LIST: {current_user.email}")
    return [] # 임시

@app.post("/api/v1/wills", status_code=status.HTTP_201_CREATED)
def create_will(policy: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user_dependency)):
    """ 새 유언장 객체를 생성합니다. """
    will_id = create_new_will(current_user, policy) # business_service 호출
    return {"id": will_id}

@app.post("/api/v1/wills/{will_id}/version")
def add_will_version(will_id: str, version_req: WillVersionRequest, current_user: User = Depends(get_current_user_dependency)):
    """ 유언장에 새 버전을 추가하고 서명합니다. """
    # (로직 생략)
    audit(f"WILL_VERSION_ADD: {will_id} by {current_user.email}")
    return {"status": "ok", "version": 1}

@app.post("/api/v1/wills/{will_id}/notarize")
def notarize_will(will_id: str, current_user: User = Depends(get_current_user_dependency)):
    """ 현재 버전을 블록체인에 공증합니다. """
    # (임시 버전 데이터)
    dummy_version_data = {"title": "V1", "content": "Test", "hash_of_content": "0x1234567890abcdef"}
    result = notarize_current_version(will_id, current_user, dummy_version_data) # business_service 호출
    audit(f"WILL_NOTARIZE_REQUEST: {will_id} by {current_user.email}")
    return result

# --- (3. 웹훅 라우터 - legacy.py 통합) ---
# NOTE: 환경 변수 STRIPE_WEBHOOK_SECRET는 config.py에서 관리됩니다.

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """ Stripe 결제/이벤트 웹훅 처리. """
    # (로직 생략: legacy.py의 웹훅 로직 그대로)
    print("Stripe webhook received.")
    return {"status": "success"}

# --- (4. 헬스 체크) ---

@app.get("/health")
def health_check():
    """ DB 연결 및 서비스 상태 확인. """
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        audit(f"HEALTH_CHECK_FAIL: {e}")
        return {"status": "error", "db": f"failed: {e}"}

# --- (앱 시작 시 설정 유효성 검사) ---
@app.on_event("startup")
async def startup_event():
    # config.py가 제공하는 설정으로 유효성 검사
    missing = []
    if os.environ.get('DB_MODE') == 'production' and not os.environ.get('DB_PASSWORD'):
        missing.append('DB_PASSWORD')
    if not os.environ.get('SECRET_KEY'):
        missing.append('SECRET_KEY')

    if missing:
        print(f"⚠️ WARNING: Missing critical environment variables: {', '.join(missing)}")
