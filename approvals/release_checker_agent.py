# approvals/release_checker_agent.py
import datetime
import json
import sys
import os
import pathlib
from dotenv import load_dotenv

# --- (1. 설정 및 모듈 임포트) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
    # (✨ 추가) backend 모듈 임포트
    from backend.database_agent import get_db
    from backend.dependencies import Will # Will Pydantic 모델 사용
except ImportError:
    print("Error: notify_agent/backend modules not found. Faking functions.")
    def notify(title, body, level="error"): print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")
    def get_db():
        class DummyConn:
            def __enter__(self): return None, None
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return DummyConn()
    class DummyWill: pass
    Will = DummyWill


def check_and_release_wills():
    """
    모든 유언장을 순회하며 릴리스 정책이 충족되었는지 확인합니다.
    """
    current_time_str = datetime.datetime.utcnow().isoformat() + "Z"
    current_time_dt = datetime.datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
    release_count = 0

    print(f"Starting EternaLegacy release check at {current_time_str}...")

    try:
        with get_db() as (conn, cur):
            if conn is None:
                notify("❌ 릴리스 체크 실패", "데이터베이스 연결에 실패했습니다.", level="error")
                return 0

            # 1. 'manual'이 아닌 유언장만 조회
            placeholder = "%s" if os.environ.get("DB_MODE") == "production" else "?"
            # 정책(policy) 필드를 조회합니다.
            cur.execute(f"SELECT id, owner_email, policy FROM wills WHERE policy NOT LIKE {placeholder}",
                        ('%"type": "manual"%'))
            wills_to_check = cur.fetchall()

            for w_row in wills_to_check:
                will_id = w_row["id"]
                owner_email = w_row["owner_email"]
                pol = json.loads(w_row["policy"])
                t = pol.get("type", "manual")

                can_release_result = {"release": False, "reason": "none"}

                if t == "time_lock":
                    ts = pol.get("release_after_utc")
                    if ts:
                        release_time_dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if current_time_dt >= release_time_dt:
                            can_release_result = {"release": True, "reason": "time_lock_expired"}

                elif t == "deadman":
                    hb = pol.get("last_heartbeat_utc"); days_str = pol.get("heartbeat_interval_days", 30)
                    try: days = int(days_str)
                    except (ValueError, TypeError): days = 30
                    if hb:
                        last_hb_dt = datetime.datetime.fromisoformat(hb.replace("Z", "+00:00"))
                        timeout_delta = datetime.timedelta(days=days)
                        if current_time_dt - last_hb_dt > timeout_delta:
                            can_release_result = {"release": True, "reason": "deadman_heartbeat_timeout"}

                # 2. 릴리스 조건이 충족되면 정책 업데이트
                if can_release_result["release"]:
                    print(f"Will {will_id} condition met: {can_release_result['reason']}")

                    # 정책을 "released" 상태로 변경 (또는 별도 필드를 사용)
                    # 여기서는 정책 타입에 "released"를 추가하여 릴리스됨을 표시
                    pol["type"] = "released"
                    pol["release_reason"] = can_release_result["reason"]
                    new_policy_json = json.dumps(pol)

                    # DB 업데이트: policy 필드 변경
                    cur.execute(
                        f"UPDATE wills SET policy = {placeholder}, updated_at = {placeholder} WHERE id = {placeholder}",
                        (new_policy_json, current_time_str, will_id)
                    )
                    conn.commit()
                    release_count += 1

                    # 3. 알림 전송
                    notify(f"🔥 EternaLegacy 유언장 릴리스",
                           f"유언장 ID: {will_id}\n소유자: {owner_email}\n자동 릴리스 조건 충족: **{can_release_result['reason']}**",
                           level="warn") # 'warn' 레벨로 긴급 알림

            print(f"Completed check. {release_count} wills released.")
            return release_count

    except Exception as e:
        print(f"Critical error during release check: {e}")
        notify("❌ 릴리스 체크 실패", f"유언장 릴리스 에이전트 실행 중 오류: {e}", level="error")
        return 0


if __name__ == "__main__":
    check_and_release_wills()

    # run_hourly_task.py에서 호출되도록, 실행 후에는 정상 종료 코드 반환
    sys.exit(0)
