# EternaLegacy/Dockerfile

# --- 1단계: 빌더(Builder) ---
# 의존성을 설치하고 컴파일하는 환경
FROM python:3.11-slim-bookworm as builder

# 작업 디렉터리 설정
WORKDIR /app

# 가상 환경 생성
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# 필요한 라이브러리 설치 (소스 코드 복사 전에 설치하여 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- 2단계: 최종(Final) 이미지 ---
# 실제 애플리케이션을 실행할 깨끗하고 가벼운 환경
FROM python:3.11-slim-bookworm

WORKDIR /app

# 빌더에서 생성한 가상 환경 복사
COPY --from=builder /app/venv /app/venv

# backend 애플리케이션 코드 복사
# (주의: .dockerignore 파일이 있어야 .env 등이 복사되지 않습니다)
COPY ./backend ./backend

# 가상 환경 활성화
ENV PATH="/app/venv/bin:$PATH"

# 컨테이너가 8000번 포트를 외부에 노출
EXPOSE 8000

# 컨테이너 실행 명령:
# Gunicorn을 사용해 4개의 Uvicorn 워커로 backend/main.py 안의 'app' 실행
ENV PYTHONPATH="/app"
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app", "--bind", "0.0.0.0:8000"]
