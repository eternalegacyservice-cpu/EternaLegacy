# ai_connector/data_io.py
import os, json, pathlib, datetime

# PROJECT_ROOT는 ai_connector 폴더의 상위 폴더인 EternaLegacy를 가리킵니다.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
OUTBOX_DIR = PROJECT_ROOT / "outbox"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

def read_system_logs(n_lines=2000):
    """
    여러 로그 파일에서 최근 n줄의 로그를 읽어 병합합니다.
    """
    merged_logs = []
    log_files = [
        "runtime.log", "update_audit.log", "recovery.log",
        "hourly_task.log", "daily_task.log", "notify.log"
    ]
    for name in log_files:
        p = LOGS_DIR / name
        if p.exists():
            try:
                merged_logs += p.read_text(encoding="utf-8", errors="ignore").splitlines()[-n_lines:]
            except Exception as e:
                print(f"Error reading log file {p}: {e}")
    return "\n".join(merged_logs) if merged_logs else "(no logs yet)"

def write_request_payload(payload):
    """
    AI 분석 결과를 JSON 파일로 outbox 폴더에 저장합니다.
    """
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = OUTBOX_DIR / f"upgrade_request_{ts}.json"
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
    except Exception as e:
        print(f"Error writing request payload to {path}: {e}")
        return None
