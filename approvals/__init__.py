# approvals/__init__.py
# 모든 에이전트와 I/O 함수를 노출합니다.

from .data_io import read_latest_request, mark_as_approved
from .upgrade_policy_agent import main as run_upgrade_policy_agent # AI 진단 승인 로직
from .release_checker_agent import check_and_release_wills as run_release_checker_agent # 유언장 릴리스 로직
