# recovery/integrity_checker.py
import logging, sys, os, pathlib
from dotenv import load_dotenv

# --- 설정 및 임포트 ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
sys.path.append(str(PROJECT_ROOT))

# (✨ 수정) 'notify'와 'get_db' 임포트를 분리합니다.

# 1. notify 임포트 시도
try:
    from notify.notify_agent import notify
except ImportError:
    print("Warning: notify_agent not found. Using FAKE notify.")
    def notify(title, body, level="error"):
        print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")

# 2. get_db 임포트 시도
try:
    from backend.db import get_db
except ImportError as e:
    print(f"FATAL: Could not import get_db from backend.db. Error: {e}")
    # get_db 임포트 실패 시 사용할 가짜 함수
    def get_db():
        class DummyConn:
            def __enter__(self):
                return None, None
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return DummyConn()

# --- (이하 동일) ---

LOG_FILE = PROJECT_ROOT / "logs" / "recovery.log"
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, format='%(asctime)s %(levelname)s %(message)s')

REQUIRED_FILES = [".env", "backend/main.py", "backend/dependencies.py", "requirements.txt"]

def check_db_integrity():
    """DB 스키마 및 기본 연결 무결성 검사."""
    try:
        with get_db() as (conn, cur):
            if conn is None or cur is None:
                return False, "DB Connection Failed (Import Error or Config Error)"

            cur.execute("SELECT 1 FROM users LIMIT 1")
            cur.execute("SELECT 1 FROM wills LIMIT 1")
        return True, "DB health check OK."
    except Exception as e:
        # 'no such table: users' 등이 여기에 해당
        return False, f"DB integrity check FAILED: {e}"

def check_file_integrity():
    """필수 파일 존재 여부 검사."""
    missing = []
    for f in REQUIRED_FILES:
        if not (PROJECT_ROOT / f).exists():
            missing.append(f)
    if missing:
        return False, f"Missing critical files: {', '.join(missing)}"
    return True, "Critical files present."

def main():
    """시스템 무결성을 검사하고 실패 시 오류를 반환합니다."""

    file_ok, file_msg = check_file_integrity()
    db_ok, db_msg = check_db_integrity()

    if file_ok and db_ok:
        logging.info("System integrity check PASSED.")
        print("System integrity check PASSED.")
        return 0
    else:
        details = [file_msg, db_msg]
        logging.error(f"System integrity check FAILED. Details: {details}")
        notify("🚨 EternaLegacy 무결성 경고", f"시스템 무결성 검사 실패. 자세한 내용은 recovery.log를 확인하세요.\n파일: {file_msg}\nDB: {db_msg}", level="error")

        print(f"System integrity check FAILED.\nFile: {file_msg}\nDB: {db_msg}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
