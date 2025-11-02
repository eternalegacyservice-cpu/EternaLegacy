# backend/upgrade_advisor.py
import os
import datetime
import json
import pathlib
from dotenv import load_dotenv
# --- (✨ Gemini SDK 임포트) ---
from google import genai
from google.genai import types
# --- (여기까지 변경) ---

# --- (내부 I/O 에이전트 임포트) ---
from backend import data_access_agent

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# (✨ 변경) 시스템 프롬프트 내부 이름 변경
SYSTEM_PROMPT = (
"You are an assistant for **EternaLegacy** (digital will service). "
"Your task is to analyze the log excerpt and determine if a system upgrade or intervention is needed. "
"Return a compact JSON object only: {need_upgrade:bool, reasons:list, new_features:list, priority:'low|normal|high', questions?:list}. "
"If you detect missing configuration (API keys, notify, policy), add a 'questions' array in Korean with concise actionable items."
)

def _heuristic_check():
    """
    Gemini API 호출이 불가능하거나 실패했을 때 사용되는 휴리스틱 분석 로직.
    """
    logs = data_access_agent.read_system_logs()

    # ... (휴리스틱 로직은 이름에 영향을 받지 않음) ...
    need = bool(logs and (("ERROR" in logs) or ("failed" in logs.lower())))
    questions = []

    if not os.environ.get("GEMINI_API_KEY"):
        questions.append("Gemini API 키(GEMINI_API_KEY)가 .env에 등록이 필요합니다.")

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
    """
    시스템 로그를 분석하고 Gemini API를 호출하여 업그레이드 제안을 받습니다.
    Gemini API 호출에 문제가 발생하면 휴리스틱 체크로 폴백(fallback)합니다.
    """
    # 1. .env에서 키와 모델 설정 읽기
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    # 2. 키가 없으면 AI 호출 없이 휴리스틱(Heuristic) 모드로 즉시 전환
    if not api_key:
        print("GEMINI_API_KEY not found in .env. Falling back to heuristic mode.")
        return _heuristic_check()

    # Gemini 클라이언트 초기화
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Gemini Client initialization failed: {e}. Falling back to heuristic mode.")
        payload = _heuristic_check()
        payload["reasons"] = [f"gemini client error: {e}"]
        payload["source"] = "gemini-error"
        return payload

    # 요청 내용 구성
    logs_excerpt = data_access_agent.read_system_logs()
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(f"Logs excerpt:\n```\n{logs_excerpt}\n```")]
        )
    ]

    # 설정 구성
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT, # <- EternaLegacy 이름 포함
        temperature=0.1,
        max_output_tokens=700,
        response_mime_type="application/json"
    )

    try:
        # 3. Gemini API 호출
        print(f"Calling Gemini API (model: {model})...")
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # 4. AI가 JSON을 잘 반환했는지 파싱
        txt = response.text.strip()

        try:
            payload = json.loads(txt)
            payload["source"] = "google-gemini"
            print("Successfully received payload from Gemini.")
        except Exception:
            # 5. AI가 JSON이 아닌 엉뚱한 텍스트를 반환한 경우
            print("Model returned non-JSON. Falling back to heuristic mode.")
            payload = _heuristic_check()
            payload["reasons"] = [f"model returned non-JSON; fallback heuristic", txt[:400]]
            payload["source"] = "gemini-fallback"

        return payload

    except Exception as e:
        # 6. Gemini API 호출 자체가 실패한 경우 (네트워크 오류, 인증 오류 등)
        print(f"Gemini call failed: {e}. Falling back to heuristic mode.")
        payload = _heuristic_check()
        payload["reasons"] = [f"gemini error: {e}"]
        payload["source"] = "gemini-error"
        return payload
