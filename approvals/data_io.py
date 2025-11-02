# approvals/data_io.py
import pathlib
import json

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTBOX = PROJECT_ROOT / "outbox"

def read_latest_request():
    """outbox에서 가장 최신의 'upgrade_request_...json' 파일 경로와 내용을 반환합니다."""
    try:
        # 확장자가 .json으로 끝나고 .APPROVED가 아닌 파일만 선택
        reqs = sorted([p for p in OUTBOX.glob("upgrade_request_*.json") if ".APPROVED" not in p.suffixes])

        if not reqs:
            return None, None

        req_path = reqs[-1]
        data = json.loads(req_path.read_text(encoding="utf-8"))
        return req_path, data

    except Exception as e:
        print(f"Error reading latest request from outbox: {e}")
        return None, None

def mark_as_approved(req_path: pathlib.Path):
    """승인된 요청 파일의 이름을 변경하여 중복 처리를 방지합니다."""
    try:
        new_path = req_path.with_suffix(req_path.suffix + ".APPROVED")
        req_path.rename(new_path)
        print(f"[approver] Marked as approved: {new_path}")
        return True
    except Exception as e:
        print(f"Error renaming approved file {req_path}: {e}")
        return False
