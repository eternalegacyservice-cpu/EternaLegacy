# run/runner_util.py
import subprocess
import logging
import sys
import pathlib
import os

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

def run_script(command: list) -> tuple[bool, object]:
    """
    (공통 함수) 외부 스크립트(예: 에이전트)를 서브 프로세스로 실행하고
    성공 여부 및 출력을 반환합니다.
    """
    script_name = command[0]

    try:
        script_full_path = PROJECT_ROOT / script_name
        # (중요) sys.executable을 사용해야 현재 가상 환경의 파이썬으로 실행됨
        full_command = [sys.executable, str(script_full_path)] + command[1:]

        result = subprocess.run(
            full_command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=PROJECT_ROOT  # 실행 위치를 프로젝트 루트로 고정
        )
        # 성공 시: True와 표준 출력(stdout) 반환
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        # 스크립트 실행 중 오류 발생 시: False와 오류 객체 반환
        return False, e
    except Exception as e:
        # 치명적인 오류(파일 없음 등): False와 오류 객체 반환
        return False, e
