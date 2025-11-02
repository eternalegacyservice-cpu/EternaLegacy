# run/run_daily_task.py (최종 수정 버전)
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
    print("Error: notify_agent.py not found. Faking notify function.")
    def notify(title, body, level="error"):
        print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")

# --- (✨ 새로 추가) runner_util에서 공통 함수 임포트 ---
from run.runner_util import run_script
# --- (여기까지 새로 추가) ---


# 로깅 설정 (로그 파일 경로를 project_root 기준으로 설정)
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "daily_task.log"
logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """1일 주기로 '보고서 생성' -> '자동 업데이트'를 순차 실행합니다."""

    logging.info("=== Starting EternaLegacy Daily Task Cycle ===")

    # 1. 보고서 생성 (reports/report_agent.py)
    script_name = 'reports/report_agent.py'
    success, output = run_script([script_name])

    if not success:
        # 실패 로깅 상세 처리
        logging.warning(f"{script_name} failed. Continuing daily cycle...")
        if hasattr(output, 'stdout') and hasattr(output, 'stderr'):
            logging.error(f"Return Code: {output.returncode}")
            logging.error(f"Stdout: {output.stdout}")
            logging.error(f"Stderr: {output.stderr}")
        else:
            logging.error(f"Critical error: {output}")

        # 보고서 실패는 치명적이지 않으므로 알림만 보내고 계속 진행
        notify("⚠️ EternaLegacy 일일 작업 경고",
               f"{script_name} (보고서 생성) 실행에 실패했습니다. logs/daily_task.log 파일을 확인하세요.",
               level="warn")
    else:
        logging.info(f"Output from {script_name}:\n{output}")
        logging.info(f"--- Finished: {script_name} ---")

    # 2. 자동 업데이트 확인 (updater/self_update.py)
    script_name = 'updater/self_update.py'
    success, output = run_script([script_name])

    if not success:
        # 실패 로깅 상세 처리
        logging.error(f"{script_name} failed. Daily cycle finished with errors.")
        if hasattr(output, 'stdout') and hasattr(output, 'stderr'):
            logging.error(f"Return Code: {output.returncode}")
            logging.error(f"Stdout: {output.stdout}")
            logging.error(f"Stderr: {output.stderr}")
        else:
            logging.error(f"Critical error: {output}")

        notify("❌ EternaLegacy 일일 작업 실패",
               f"{script_name} (자동 업데이트) 실행에 실패했습니다. logs/daily_task.log 파일을 확인하세요.",
               level="error")
        return # 2단계 실패
    else:
        logging.info(f"Output from {script_name}:\n{output}")
        logging.info(f"--- Finished: {script_name} ---")

    logging.info("=== EternaLegacy Daily Task Cycle Completed Successfully ===")

if __name__ == "__main__":
    main()
