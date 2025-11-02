import json, pathlib, smtplib, ssl, requests, datetime, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from dotenv import load_dotenv
import sys

# --- (1. 설정 및 환경 로드) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

LOGS_DIR = PROJECT_ROOT / "logs"; LOGS_DIR.mkdir(parents=True, exist_ok=True)

# --- (2. DB 연결 모듈 임포트 및 설정) ---
# EternaLegacy 프로젝트의 backend/database_agent.py에서 get_db를 가져옵니다.
sys.path.append(str(PROJECT_ROOT))
try:
    # 모듈화된 backend 패키지에서 DB 연결 함수 임포트
    from backend.database_agent import get_db
except ImportError:
    print("Warning: Could not import get_db from backend. Database logging will be disabled.")
    # DB 로깅을 비활성화하는 더미 함수
    def get_db():
        class DummyConn:
            def __enter__(self): return None, None
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return DummyConn()

DB_MODE = os.environ.get("DB_MODE", "local")
# --- (여기까지 DB 설정) ---


LEVEL_ICON = {
    "ok": "✅",
    "update": "🔄",
    "warn": "⚠️",
    "error": "❌",
    "info": "ℹ️"
}

# --- (3. 로깅 및 DB 로깅 함수) ---

def log(msg: str):
    """(파일 로깅) 로그 파일에 메시지를 기록합니다."""
    p = LOGS_DIR / "notify.log"
    ts = datetime.datetime.utcnow().isoformat()+"Z"
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{ts} {msg}\n")

def _initialize_db_table(conn, cur):
    """ 알림 테이블이 없으면 생성합니다. """
    try:
        if DB_MODE == "production":
            # PostgreSQL
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    level VARCHAR(10) NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT,
                    status VARCHAR(20)
                );
            """)
        else:
            # SQLite
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT,
                    status TEXT
                );
            """)
        conn.commit()
    except Exception as e:
        log(f"[db_init] Error creating notifications table: {e}")

def _log_to_db(level: str, title: str, body: str, status: str):
    """ DB에 알림 이력을 기록합니다. """
    try:
        with get_db() as (conn, cur):
            if conn is None: return

            _initialize_db_table(conn, cur)

            placeholder = "%s" if DB_MODE == "production" else "?"
            cur.execute(
                f"""
                INSERT INTO notifications (level, title, body, status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (level, title, body[:4000], status) # 본문은 4000자로 제한
            )
            conn.commit()
            log(f"[db_log] Logged notification: {title} ({status})")
    except Exception as e:
        log(f"[db_log] CRITICAL DB LOGGING ERROR: {e}")


# --- (4. 알림 전송 함수) ---

def _send_email(subject, body):
    # ... (기존 _send_email 로직 유지) ...
    try:
        host = os.environ.get("SMTP_HOST")
        port = int(os.environ.get("SMTP_PORT", 587))
        user = os.environ.get("SMTP_USER")
        password = os.environ.get("SMTP_PASSWORD")
        to = os.environ.get("SMTP_TO")

        if not (host and user and password and to):
            log("[email] missing smtp config in .env file"); return False

        context = ssl.create_default_context()
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.sendmail(user, [to], msg.as_string())

        log("[email] sent"); return True
    except Exception as e:
        log(f"[email] error: {e}"); return False

def _send_telegram(text):
    # ... (기존 _send_telegram 로직 유지) ...
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not (token and chat_id):
            log("[telegram] missing config in .env file"); return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        if len(text) > 4096:
            text = text[:4090] + "\n...(truncated)"

        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=15)

        r.raise_for_status()
        log("[telegram] sent"); return True
    except Exception as e:
        log(f"[telegram] error: {e}"); return False

def format_block(title: str, lines: list[str] | None = None) -> str:
    # ... (기존 format_block 로직 유지) ...
    title = title.replace("<", "&lt;").replace(">", "&gt;")
    s = f"<b>{title}</b>"
    if lines:
        for ln in lines:
            ln = ln.replace("<", "&lt;").replace(">", "&gt;")
            s += f"\n• {ln}"
    return s

def notify(title: str, body: str, level: str = "info"):
    """
    주요 알림 함수. 이메일/텔레그램으로 전송하고, DB에 기록합니다.
    """
    icon = LEVEL_ICON.get(level, LEVEL_ICON["info"])

    email_subject = f"{icon} {title}"
    telegram_text = f"{icon} {format_block(title)}\n{body}"
    email_body = f"{title}\n\n{body}"

    # 1. 전송 시도
    ok1 = _send_email(email_subject, email_body)
    ok2 = _send_telegram(telegram_text)

    # 2. 전송 상태 결정 및 파일 로깅
    status_str = "SUCCESS"
    if ok1 and ok2: status_str = "SUCCESS_BOTH"
    elif ok1: status_str = "SUCCESS_EMAIL"
    elif ok2: status_str = "SUCCESS_TELEGRAM"
    else: status_str = "FAILED_ALL"

    log(f"[notify] {status_str} level={level} title={title}")

    # 3. DB 로깅 (가장 중요한 업그레이드 부분)
    _log_to_db(level, title, body, status_str)

    return ok1 or ok2

def notify_status(status: str, details: list[str] | None = None):
    # ... (기존 notify_status 로직 유지) ...
    level = "ok" if status=="ok" else ("warn" if status=="warn" else ("error" if status=="error" else "info"))
    title = "EternaLegacy system " + status.upper()

    body_details = "\n".join(f"- {d}" for d in (details or []))

    return notify(title, body_details, level=level)

if __name__ == "__main__":
    # 이 스크립트를 직접 실행하면 테스트 메시지를 보냅니다.
    print("Sending EternaLegacy test notifications...")

    if not (os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("SMTP_USER")):
        print("!!! ERROR: .env file not loaded or keys are missing.")
        log("[notify_test] .env file not loaded or keys are missing.")
    else:
        # DB 로깅 테스트
        notify("EternaLegacy Test (DB Log)", "This tests database logging.", level="info")
        notify_status("ok", ["health: ok", "version: v4.x.x", "DB logging: active"])
        notify_status("error", ["example failure detail"])

        print("Test notifications sent. Check your email/telegram, logs/notify.log, and the 'notifications' DB table.")
        log("[notify_test] Test messages sent.")
