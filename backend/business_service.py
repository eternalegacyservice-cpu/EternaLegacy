# backend/business_service.py
from typing import Dict, Any, List
import base64, os, datetime, json
from fastapi import HTTPException
from .config import DB_MODE, SECRET_KEY
from .db import get_db
# 순수 로직 모듈 임포트
from .crypto import aes_encrypt_gcm, aes_decrypt_gcm
from .versioning import sign_version, verify_signature
from .blockchain import notarize_hash
from .audit import audit
from .dependencies import WillVersionRequest, User


# NOTE: 이 파일에는 DB 트랜잭션과 순수 로직의 조합이 들어갑니다.

def create_new_will(user: User, policy: Dict[str, Any]) -> str:
    """ 새 유언장을 생성하고 DB에 저장합니다. """
    # (로직 생략: DB 트랜잭션, UUID 생성 등)
    audit(f"CREATE_WILL: {user.email}")
    # ...
    return "will-uuid-1234"

def notarize_current_version(will_id: str, user: User, version_data: Dict[str, Any]):
    """ 현재 유언장 버전을 블록체인에 공증합니다. """

    # 1. 서명 검증 (Version Service 활용)
    # NOTE: signer_secret은 SECRET_KEY를 base64 디코딩하여 사용한다고 가정
    signer_secret = base64.b64decode(SECRET_KEY.encode('utf-8')) # 단순화된 예시

    signature = sign_version(version_data['title'], version_data['content'], signer_secret)
    # ...

    # 2. 해시 생성 및 공증 (Blockchain Service 활용)
    will_hash = version_data.get("hash_of_content") # 이미 DB에 저장된 해시
    if not will_hash:
         raise HTTPException(status_code=500, detail="Will content hash not found")

    try:
        tx_hash = notarize_hash(will_hash, will_id) # blockchain.py 호출
        audit(f"NOTARIZE_SUCCESS: {will_id} by {user.email} -> {tx_hash}")
        return {"tx_hash": tx_hash}
    except Exception as e:
        audit(f"NOTARIZE_FAIL: {will_id} by {user.email} -> {e}")
        raise HTTPException(status_code=500, detail=f"Blockchain notarization failed: {e}")

# ... 기타 비즈니스 로직 (버전 조회, 권한 부여 등) ...
