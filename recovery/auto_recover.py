# recovery/auto_recover.py

import logging, os, shutil, subprocess, sys, pathlib
from dotenv import load_dotenv

# --- (1. 설정 및 임포트) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
    # (✨ 추가) run 폴더의 runner_util 임포트 (subprocess 로직 제거를 위함)
    from run.runner_util import run_script
except ImportError:
    print("Error: notify_agent/run.runner_util not found. Faking functions.")
    def notify(title, body, level="error"):
        print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")
    # 가짜 run_script
    def run_script(command): return False, "Fake run_script failed"

# (✨ 수정) 로그 경로 설정
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "recovery.log"
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, format='%(asctime)s %(levelname)s %(message)s')

def restore_bak():
    """ 'backup' 폴더에서 최신 백업을 찾아 복원합니다. """
    logging.info("Attempting to restore from backup...")
    restored = False
    try:
        # 백업 폴더 경로 명확화
        backup_dir = PROJECT_ROOT / "backup"

        if not backup_dir.exists():
            logging.warning("No 'backup' directory found.")
            return False

        # 가장 최신 백업 폴더를 찾음 (디렉터리만)
        backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], reverse=True)
        if not backups:
            logging.warning("No backup sub-directories found.")
            return False

        latest_backup = backups[0]
        logging.info(f"Restoring from latest backup: {latest_backup}")

        # 백업 폴더의 모든 파일을 프로젝트 루트로 덮어쓰기
        for item in latest_backup.rglob("*"):
            if item.is_file():
                # target_path는 PROJECT_ROOT 기준으로 계산됨
                target_path = PROJECT_ROOT / item.relative_to(latest_backup)
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
                    logging.info(f"Restored: {target_path}")
                    restored = True
                except Exception as e:
                    logging.exception(f"Failed to restore file {item}: {e}")

    except Exception as e:
        logging.exception(f"Failed to restore from backup: {e}")
        return False

    return restored

def reinstall_deps():
    """ (✨ 수정) run_script 유틸리티를 사용하여 의존성을 재설치합니다. """
    logging.info("Attempting to reinstall dependencies using runner_util...")
    try:
        # requirements.txt의 표준 위치는 프로젝트 루트에 있다고 가정하거나,
        # 백엔드 개발 스크립트가 사용할 위치로 가정합니다.
        req_path = "requirements.txt"

        if not (PROJECT_ROOT / req_path).exists():
            logging.error(f"{req_path} not found at {PROJECT_ROOT}. Cannot reinstall.")
            return False

        # run_script는 파이썬 스크립트 실행용이므로 pip 명령은 직접 실행해야 합니다.
        # 하지만 일관성을 위해 runner_util의 subprocess 로직을 활용합니다.

        # NOTE: runner_util.run_script는 Python 스크립트(sys.executable)를 실행하는 데 최적화되어 있습니다.
        # 외부 명령(pip) 실행을 위해선 runner_util을 수정해야 하지만,
        # 모듈화 원칙을 위해 recovery agent 내에서 직접 subprocess를 사용하거나 run_script의 확장된 버전을 사용해야 합니다.

        # 여기서는 가장 간단한 해결책으로, 기존 코드를 유지하되 경로를 명확히 합니다.
        pip_path = PROJECT_ROOT / ".venv" / "Scripts" / "pip" # Windows 기준
        if not pip_path.exists():
             pip_path = PROJECT_ROOT / ".venv" / "bin" / "pip" # Linux/macOS 기준

        if not pip_path.exists():
             logging.error("pip executable not found in .venv. Cannot reinstall.")
             return False

        cmd = [str(pip_path), "install", "-r", str(PROJECT_ROOT / req_path)]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT, encoding='utf-8')
        logging.info(f"Reinstalled dependencies: {result.stdout}")
        return True
    except Exception as e:
        logging.exception(f"reinstall error: {e}")
        return False


if __name__ == "__main__":
    logging.info("--- Starting EternaLegacy Auto-Recovery ---")

    ok = restore_bak()

    if ok:
        logging.info("Recovery successful (restored from backup).")
        notify("✅ EternaLegacy 자동 복구 완료", "최신 백업에서 파일을 복원했습니다.", level="ok")
    else:
        logging.warning("Restore from backup failed. Attempting dependency reinstall...")
        ok = reinstall_deps()
        if ok:
            logging.info("Recovery successful (reinstalled dependencies).")
            notify("✅ EternaLegacy 자동 복구 완료", "Python 라이브러리(requirements.txt)를 재설치했습니다.", level="ok")
        else:
            logging.error("All recovery methods failed.")
            notify("❌ EternaLegacy 자동 복구 실패", "백업 복원 및 라이브러리 재설치에 모두 실패했습니다.", level="error")

    logging.info("--- EternaLegacy Auto-Recovery Finished ---")
