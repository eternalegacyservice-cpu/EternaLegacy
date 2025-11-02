# reports/report_data_io.py
import pathlib
import json
import datetime

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def write_report_data(data: dict):
    """보고서 데이터를 JSON 파일로 저장합니다."""
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")
    out_name = f"report_{ts.replace(':','').replace(' ','_').replace('-','')}.json"
    out_path = REPORTS_DIR / out_name

    try:
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path
    except Exception as e:
        raise RuntimeError(f"Failed to write report: {e}")
