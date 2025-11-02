# backend/config.py
import os
from dotenv import load_dotenv
import pathlib

# .env 파일의 위치를 프로젝트 루트로 설정
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- (1) DB 설정 ---
# 'production' (PostgreSQL) 또는 'development' (SQLite)
DB_MODE = os.environ.get("DB_MODE", "development")

# --- (2) JWT 및 보안 설정 ---
# (중요) .env 파일에 반드시 SECRET_KEY가 설정되어 있어야 합니다.
# 예: openssl rand -hex 32
SECRET_KEY = os.environ.get("SECRET_KEY", "default_very_weak_secret_key_12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1일

# --- (3) Stripe 설정 ---
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# --- (4) 블록체인 설정 ---
ETHEREUM_NODE_URL = os.environ.get("ETHEREUM_NODE_URL")
ETHEREUM_PRIVATE_KEY = os.environ.get("ETHEREUM_PRIVATE_KEY")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS")
