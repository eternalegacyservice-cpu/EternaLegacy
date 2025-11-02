# updater/update_util.py
import requests, hashlib, os, shutil, subprocess, pathlib
from typing import Dict, Any

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

def fetch_manifest(url: str) -> Dict[str, Any]:
    """MANIFEST URL에서 JSON 데이터를 다운로드하고 파싱합니다."""
    import json
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    m_bytes = r.content
    return json.loads(m_bytes)

def sha256_bytes(b: bytes) -> str:
    """바이트 데이터의 SHA256 해시를 계산합니다."""
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def execute_post_hook(hook_command: str, base_dir: pathlib.Path):
    """
    업데이트 후처리 명령어(예: pip install)를 실행합니다.
    """
    import logging # 로깅은 update_util 내부에서 처리
    logging.info(f"Running post-hook: {hook_command}")

    # .venv의 pip 실행 파일을 찾습니다.
    pip_path = base_dir / ".venv" / "Scripts" / "pip" # Windows
    if not pip_path.exists():
        pip_path = base_dir / ".venv" / "bin" / "pip" # Linux/macOS

    # 명령어 문자열에서 'pip' 부분을 .venv 경로로 치환합니다.
    full_hook = hook_command.replace("pip", str(pip_path))

    # shell=True를 사용하거나, 명령어를 리스트로 분리하여 실행합니다.
    # 안전을 위해 shell=True를 제거하고 리스트로 실행하는 것이 좋지만,
    # 원본 파일과의 호환성을 위해 여기서는 `shell=True`와 치환을 유지합니다.
    subprocess.run(full_hook, shell=True, check=True, cwd=base_dir)

def apply_files_with_backup(manifest: Dict[str, Any], base_dir: pathlib.Path):
    """
    매니페스트에 따라 파일을 백업하고 적용합니다.
    """
    import logging # 로깅은 update_util 내부에서 처리
    import datetime

    # 1. 백업 생성
    backup_dir = base_dir / "backup" / f"backup_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for f in manifest.get("files", []):
        path = base_dir / f["path"]
        if path.exists():
            try:
                backup_target = backup_dir / f["path"]
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_target)
            except Exception as e:
                logging.warning(f"Failed to backup {f['path']}: {e}")

    # 2. 파일 적용
    logging.info(f"Applying {len(manifest.get('files', []))} files...")
    for f in manifest.get("files", []):
        try:
            data = requests.get(f["url"]).content
            if sha256_bytes(data) != f["sha256"]:
                raise RuntimeError(f"SHA mismatch for {f['path']}")

            path = base_dir / f["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            logging.info(f"Updated: {path}")
        except Exception as e:
            logging.error(f"Failed to apply file {f['path']}: {e}")
            raise RuntimeError(f"Failed to apply update: {f['path']}")

    # 3. 후속 작업 (post-hooks) 실행
    for hook in manifest.get("post_hooks", []):
        execute_post_hook(hook, base_dir)
