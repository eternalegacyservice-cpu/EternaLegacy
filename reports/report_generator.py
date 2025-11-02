# reports/report_generator.py
import pathlib, datetime, json, sys, os

# --- (1. 설정 및 모듈 임포트) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
    # (✨ 추가) backend의 DB 연결 함수 임포트
    from backend.database_agent import get_db
    # (✨ 추가) report_data_io 임포트
    from reports.report_data_io import write_report_data
except ImportError:
    print("Error: necessary modules not found. Faking functions.")
    def notify(title, body, level="error"): print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")
    # 가짜 DB 연결 함수
    def get_db():
        class DummyConn:
            def __enter__(self): return None, None
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return DummyConn()
    def write_report_data(data): return pathlib.Path("/tmp/fake_report.json")

def grab_log_tail(path_name, n_chars=5000):
    """로그 파일의 마지막 N 글자를 가져옵니다."""
    p = LOGS_DIR / path_name
    if p.exists():
        try:
            full_text = p.read_text(encoding="utf-8", errors="ignore")
            return full_text[-n_chars:]
        except Exception as e:
            return f"Error reading {path_name}: {e}"
    return "(log not found)"

def check_db_health():
    """ (✨ 업그레이드) 실제 DB 연결 상태를 확인합니다. """
    try:
        with get_db() as (conn, cur):
            if conn is None:
                return "error (connection failed/misconfigured)"
            # 간단한 쿼리로 연결 유효성 검사
            cur.execute("SELECT 1")
            return "ok (connection successful)"
    except Exception as e:
        return f"error: {e}"

def main():
    print("Generating daily report for EternaLegacy...")
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")

    # (✨ 업그레이드) 실제 DB 헬스 체크
    db_status = check_db_health()

    data = {
        "report_generated_at": ts,
        "database_health": db_status,
        "logs": {
            "hourly_task": grab_log_tail("hourly_task.log"),
            "notify": grab_log_tail("notify.log"),
            "audit_will": grab_log_tail("audit_will.log"),
            "daily_task": grab_log_tail("daily_task.log"),
            "update_audit": grab_log_tail("update_audit.log"),
            "recovery": grab_log_tail("recovery.log")
        }
    }

    try:
        out_path = write_report_data(data) # I/O 모듈 사용
        print(f"[OK] Report written to: {out_path}")
        if "error" in db_status:
             notify("⚠️ EternaLegacy DB 경고", f"일일 보고서 생성 완료. DB 상태에 오류가 있습니다: {db_status}", level="warn")
    except Exception as e:
        print(f"[ERROR] Failed to write report: {e}")
        notify("❌ EternaLegacy 일일 보고서 실패", f"보고서 파일 생성 중 오류 발생: {e}", level="error")

if __name__ == "__main__":
    main()
