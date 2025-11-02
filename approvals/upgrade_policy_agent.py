# approvals/upgrade_policy_agent.py (구 approver.py)

import argparse, json, pathlib, sys, os
from dotenv import load_dotenv

# --- (1. 설정 및 임포트) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
except ImportError:
    print("Error: notify_agent.py not found. Faking notify function.")
    def notify(title, body, level="error"):
        print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")

# --- (✨ 새로 추가) I/O 로직 임포트 ---
from approvals.data_io import read_latest_request, mark_as_approved
# --- (여기까지 새로 추가) ---

# .env에서 정책 읽기
AUTO_APPLY = os.environ.get("AUTO_APPLY_MINOR", "false").lower() == "true"

def main(auto=False):
    """
    AI 진단 결과를 기반으로 업그레이드 자동/수동 승인 여부를 결정하고 처리합니다.
    """
    req_path, data = read_latest_request()

    if not req_path:
        print("[approver] No unapproved request found in outbox.")
        return 0

    # 파일 읽기 성공 시, 데이터 분석
    need = data.get("need_upgrade", False)
    priority = data.get("priority","normal")

    if not need:
        print("[approver] No upgrade needed according to latest request.")
        return 0

    # --- 자동 승인 로직 ---
    # 조건: 1. '--auto' 플래그 ON, 2. .env 정책 ON, 3. 우선순위 'low' or 'normal'
    if auto and AUTO_APPLY and priority in ("low","normal"):
        notify("✅ EternaLegacy 자동 승인",
               f"AI가 제안한 {priority} 등급 업그레이드를 자동 승인했습니다.",
               level="ok")

        # (중요) 승인 후 파일 이름 변경
        if mark_as_approved(req_path):
            print(f"[approver] Auto-approved and marked file (priority={priority}).")
            return 0 # 자동 승인 성공
        else:
            # 파일 이름 변경 실패 시 비정상 종료 (중복 실행 방지 실패)
            print(f"[approver] CRITICAL: Auto-approved but failed to mark file.")
            notify("❌ EternaLegacy Approver 실패", "자동 승인했지만 파일 이름 변경 실패!", level="error")
            return 1

    # --- 수동 승인 로직 ---
    if need:
        notify("⚠️ EternaLegacy 수동 승인 필요",
               f"AI가 {priority} 등급 업그레이드를 제안했습니다. (자동 승인 비활성화됨)",
               level="warn")
        print(f"[approver] Manual approval required (priority={priority}). Notification sent.")

    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true", help="Run in automated mode (used by hourly scheduler)")
    args = ap.parse_args()

    try:
        sys.exit(main(auto=args.auto))
    except Exception as e:
        print(f"Approver failed with unexpected error: {e}")
        notify("❌ EternaLegacy Approver 실패", f"Approver 에이전트 실행 중 치명적 오류 발생: {e}", level="error")
        sys.exit(1)
