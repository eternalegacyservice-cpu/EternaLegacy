# run/run_hourly_task.py (최종 버전)

import logging
import sys
import os
import pathlib
from dotenv import load_dotenv

# --- (1. 설정 및 임포트) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
except ImportError:
    # FAKE NOTIFY
    def notify(title, body, level="error"):
        print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")

from run.runner_util import run_script

# 로깅 설정
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "hourly_task.log"
logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def _log_failure(script_name, output):
    """실패 시 로그 상세 정보를 기록하는 헬퍼 함수"""
    logging.error(f"!!! FAILED: {script_name} !!!")
    if hasattr(output, 'stdout') and hasattr(output, 'stderr'):
        logging.error(f"Return Code: {output.returncode}")
        logging.error(f"Stdout: {output.stdout}")
        logging.error(f"Stderr: {output.stderr}")
    else:
        logging.error(f"Critical error: {output}")

def main():
    """
    1시간 주기로 'AI 진단' -> '업그레이드 승인' -> '릴리스 검사'를 순차 실행합니다.
    """

    logging.info("=== Starting EternaLegacy Hourly Task Cycle ===")

    # 1. AI 진단 (업그레이드 제안)
    script_ai = 'ai_connector/upgrade_advisor_agent.py'
    success, output = run_script([script_ai])
    if not success:
        _log_failure(script_ai, output)
        notify("❌ EternaLegacy 시간별 작업 실패", f"{script_ai} (AI 진단) 실행 실패", level="error")
    else:
        logging.info(f"--- Finished: {script_ai} ---")


    # 2. 업그레이드 승인 (AI 진단 결과 승인)
    script_approver = 'approvals/upgrade_policy_agent.py'
    success, output = run_script([script_approver, '--auto'])

    if not success:
        _log_failure(script_approver, output)
        notify("❌ EternaLegacy 시간별 작업 실패", f"{script_approver} (업그레이드 승인) 실행 실패", level="error")
    else:
        logging.info(f"--- Finished: {script_approver} ---")


    # 3. 릴리스 검사 (✨ 유언장 자동 릴리스 로직 추가)
    script_release = 'approvals/release_checker_agent.py'
    success, output = run_script([script_release])

    if not success:
        _log_failure(script_release, output)
        notify("❌ EternaLegacy 시간별 작업 실패", f"{script_release} (릴리스 검사) 실행 실패", level="error")
    else:
        logging.info(f"--- Finished: {script_release} ---")


    logging.info("=== EternaLegacy Hourly Task Cycle Completed Successfully ===")

if __name__ == "__main__":
    main()
