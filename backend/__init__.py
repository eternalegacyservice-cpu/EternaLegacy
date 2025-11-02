# backend/__init__.py

# 백엔드 모듈 내의 주요 Pydantic 모델과 함수를 쉽게 임포트할 수 있도록 노출합니다.

# --- (✨ 수정) ---
# 1. 'db.py'에서 'get_db'를 가져옵니다.
# 2. 'database_agent.py'에서 'get_current_user_dependency'를 가져옵니다.
# 3. 'dependencies.py'에 존재하지 않는 'UserCreate', 'ReleasePolicy' 임포트를 제거합니다.

from .dependencies import User, Token, Will
from .db import get_db
from .database_agent import get_current_user_dependency

# (참고) 아래 임포트는 business_service.py에 해당 함수가 정의되어 있어야 합니다.
# from .business_service import check_will_ownership_dependency, check_will_read_access_dependency
