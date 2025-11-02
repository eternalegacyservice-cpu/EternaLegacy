# updater/self_update_agent.py

import json, os, logging, pathlib, sys
from dotenv import load_dotenv

# --- (1. 설정 및 임포트) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
    # (✨ 추가) update_util 임포트
    from updater.update_util import fetch_manifest, apply_files_with_backup
except ImportError:
    print("Error: notify_agent/updater.update_util not found. Faking functions.")
    def notify(title, body, level="error"): print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")
    def fetch_manifest(url): return {"version": None}
    def apply_files_with_backup(m, d): pass

# 로그 경로 설정
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "update_audit.log"
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, format='%(asctime)s %(levelname)s %(message)s')


def check_for_updates():
    """
    업데이트를 확인하고, 새로운 버전이 있으면 다운로드 및 적용합니다.
    """
    logging.info("Checking for updates...")
    try:
        url = os.environ.get("MANIFEST_URL", "").strip()
        if not url:
            logging.info("MANIFEST_URL is not configured in .env. Skipping update check.")
            return

        last_ver_file = LOGS_DIR / "last_update_version.txt"
        last_ver = None
        if last_ver_file.exists():
            last_ver = last_ver_file.read_text(encoding="utf-8").strip()

        m = fetch_manifest(url) # 헬퍼 함수 사용
        ver = m.get("version")

        if ver and ver != last_ver:
            logging.info(f"New version detected: {ver} (previous: {last_ver})")
            notify("🔄 EternaLegacy 새 버전 감지", f"버전: {ver}\n변경 사항: {json.dumps(m.get('changelog', 'N/A'), ensure_ascii=False)}", level="update")

            # (✨ 업그레이드) 파일 적용 로직을 헬퍼 함수에 위임
            apply_files_with_backup(m, PROJECT_ROOT)

            last_ver_file.write_text(ver, encoding="utf-8")

            logging.info(f"Update to {ver} applied successfully.")
            notify("✅ EternaLegacy 업데이트 완료", f"v{ver}으로 성공적으로 업데이트되었습니다.", level="ok")
        else:
            logging.info(f"Already up-to-date (version: {last_ver}).")

    except Exception as e:
        logging.exception(f"Update check failed: {e}")
        notify("❌ EternaLegacy 업데이트 확인 실패", str(e)[:1500], level="error")

if __name__ == "__main__":
    check_for_updates()
