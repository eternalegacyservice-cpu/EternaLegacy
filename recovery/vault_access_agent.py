# recovery/vault_access_agent.py
import os, sys, pathlib
import json
import base64
from dotenv import load_dotenv

# --- 설정 및 임포트 ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
except ImportError:
    def notify(title, body, level="error"): print(f"[FAKE NOTIFY] {title}: {body}")

def load_secret(key_name: str, fallback_value: str = "") -> str:
    """
    (임시 볼트 에이전트) 환경 변수에서 민감 정보를 로드하는 볼트 역할을 시뮬레이션합니다.
    실제 프로덕션에서는 HashiCorp Vault 또는 AWS KMS를 호출해야 합니다.
    """
    secret = os.environ.get(key_name, fallback_value)
    if not secret:
        notify("⚠️ 볼트 경고", f"핵심 비밀 키 '{key_name}'가 .env에 없습니다.", level="warn")
    return secret

def get_critical_secrets():
    """
    블록체인 및 Stripe와 관련된 핵심 비밀 정보를 가져옵니다.
    """
    secrets = {
        "ETHEREUM_PRIVATE_KEY": load_secret("ETHEREUM_PRIVATE_KEY"),
        "STRIPE_SECRET_KEY": load_secret("STRIPE_SECRET_KEY"),
        "DB_PASSWORD": load_secret("DB_PASSWORD"),
        "SECRET_KEY": load_secret("SECRET_KEY"), # JWT 서명 키
    }

    # 누락된 키가 있는지 확인
    missing = [k for k, v in secrets.items() if not v]
    if missing:
        print(f"[VAULT] WARNING: Missing secrets: {', '.join(missing)}")

    return secrets

if __name__ == "__main__":
    print("Running Vault Access Check...")
    secrets = get_critical_secrets()
    print(f"Loaded {len(secrets)} secrets (Check logs for warnings on missing keys).")
