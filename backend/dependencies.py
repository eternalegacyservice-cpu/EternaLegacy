# backend/dependencies.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from fastapi.security import OAuth2PasswordBearer
import datetime

# --- Pydantic Models (from legacy.py) ---
class User(BaseModel):
    email: str
    full_name: Optional[str] = None
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

class WillVersionRequest(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)

class WillVersion(WillVersionRequest):
    will_id: str
    version: int
    created_at: str
    # 서명 및 암호화 관련 필드
    signed: bool
    encrypted: bool
    signature_b64: Optional[str] = None
    cipher: Optional[str] = None
    salt_b64: Optional[str] = None
    iv_b64: Optional[str] = None

class Will(BaseModel):
    id: str
    owner_email: str
    policy: Dict[str, Any] # time_lock, deadman 등 정책 JSON
    versions: List[WillVersion] = []
    created_at: str
    updated_at: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Grant(BaseModel):
    will_id: str
    email: str
    role: str # 'viewer', 'approver'
    created_at: str

class HeartbeatRequest(BaseModel):
    last_heartbeat_utc: str

# --- FastAPI Dependencies ---
# legacy.py에 정의된 OAuth2 스키마
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")
