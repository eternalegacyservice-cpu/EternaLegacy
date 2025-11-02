# ai_connector/upgrade_advisor_agent.py

import os, json, pathlib, datetime, sys
from dotenv import load_dotenv

# --- (SDK 및 내부 모듈 임포트) ---
from google import genai
from google.genai import types

# I/O 로직 임포트 (내부 모듈)
from ai_connector import data_io

# --- (1. 초기 설정 및 환경 로드) ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# 'notify' 폴더를 파이썬 경로에 추가
sys.path.append(str(PROJECT_ROOT))
try:
    from notify.notify_agent import notify
except ImportError:
    print("Error: notify_agent.py not found. Faking notify function.")
    def notify(title, body, level="error"):
        print(f"[FAKE NOTIFY - {level.upper()}] {title}: {body}")
# --- (여기까지 설정) ---


# --- (2. 핵심 비즈니스 로직) ---

# 시스템 프롬프트 (EternaLegacy 프로젝트 명 사용)
SYSTEM_PROMPT = (
"You are an assistant for EternaLegacy (digital will service). "
"Your task is to analyze the log excerpt and determine if a system upgrade or intervention is needed. "
"Return a compact JSON object only: {need_upgrade:bool, reasons:list, new_features:list, priority:'low|normal|high', questions?:list}. "
"If you detect missing configuration (API keys, notify, policy), add a 'questions' array in Korean with concise actionable items."
)

def _heuristic_check():
    """ Gemini API 호출 실패 시 사용되는 휴리스틱 분석 로직. """
    logs = data_io.read_system_logs() # data_io 모듈 사용

    need = bool(logs and (("ERROR" in logs) or ("failed" in logs.lower())))
    questions = []

    # .env에서 GEMINI API 키 확인
    if not os.environ.get("GEMINI_API_KEY"):
        questions.append("Gemini API 키(GEMINI_API_KEY)가 .env에 등록이 필요합니다.")

    # .env에서 알림 설정 확인
    tg_ok = bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
    mail_ok = bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASSWORD"))
    if not (tg_ok or mail_ok):
        questions.append("알림 채널(텔레그램 또는 이메일)이 .env에 설정이 필요합니다.")

    return {
        "need_upgrade": bool(need),
        "reasons": ["local heuristic trigger" if need else "no critical error"],
        "new_features": [],
        "priority": "normal" if need else "low",
        "questions": questions,
        "source": "local-heuristic",
        "generated_at": datetime.datetime.utcnow().isoformat()+"Z"
    }

def get_upgrade_suggestion():
    """ 시스템 로그를 분석하고 Gemini API를 호출하여 업그레이드 제안을 받습니다. """

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        print("GEMINI_API_KEY not found in .env. Falling back to heuristic mode.")
        return _heuristic_check()

    try:
        client = genai.Client()
    except Exception as e:
        print(f"Gemini Client initialization failed: {e}. Falling back to heuristic mode.")
        payload = _heuristic_check()
        payload["reasons"] = [f"gemini client error: {e}"]
        payload["source"] = "gemini-error"
        return payload

    # I/O 모듈을 통해 로그를 읽어옵니다.
    logs_excerpt = data_io.read_system_logs()

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(f"Logs excerpt:\n```\n{logs_excerpt}\n```")]
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.1,
        max_output_tokens=700,
        response_mime_type="application/json"
    )

    try:
        print(f"Calling Gemini API (model: {model})...")
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        txt = response.text.strip()

        try:
            payload = json.loads(txt)
            payload["source"] = "google-gemini"
            print("Successfully received payload from Gemini.")
        except Exception:
            print("Model returned non-JSON. Falling back to heuristic mode.")
            payload = _heuristic_check()
            payload["reasons"] = [f"model returned non-JSON; fallback heuristic", txt[:400]]
            payload["source"] = "gemini-fallback"

        return payload

    except Exception as e:
        print(f"Gemini call failed: {e}. Falling back to heuristic mode.")
        payload = _heuristic_check()
        payload["reasons"] = [f"gemini error: {e}"]
        payload["source"] = "gemini-error"
        return payload

# --- (3. 메인 실행 함수) ---
if __name__ == "__main__":

    print("Running EternaLegacy AI Upgrade Advisor Agent...")

    req = get_upgrade_suggestion()
    path = data_io.write_request_payload(req) # data_io 모듈 사용

    print(f"Request payload written to: {path}")

    # 설정 필요 알림
    if req.get("questions"):
        print(f"Found questions: {req['questions']}")
        body = "\n".join(f"- {q}" for q in req["questions"][:10])
        notify("⚠️ EternaLegacy 설정 필요", body, level="warn")

    # 업그레이드 제안 알림
    if req.get("need_upgrade"):
        print("Upgrade suggestion detected.")
        notify("🔄 EternaLegacy 업그레이드 제안", json.dumps(req, ensure_ascii=False)[:3500], level="update")

    print("AI Connector finished.")
