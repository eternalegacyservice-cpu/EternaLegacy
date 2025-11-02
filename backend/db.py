# backend/db.py
import os
import sqlite3
import psycopg2
import contextlib
from psycopg2.extras import DictCursor
from typing import ContextManager

# config에서 DB 모드 임포트
from .config import DB_MODE, PROJECT_ROOT

# --- (1) DB 연결 설정 ---

def get_sqlite_connection():
    """ SQLite DB 연결을 반환합니다. (개발용) """
    # DB 파일 경로를 프로젝트 루트의 'data' 폴더로 지정
    db_path = PROJECT_ROOT / "data" / "eterna_legacy.db"
    db_path.parent.mkdir(parents=True, exist_ok=True) # data 폴더 생성
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row # 결과를 dict처럼 접근
        return conn
    except Exception as e:
        print(f"[FATAL] SQLite connection failed: {e}")
        return None

def get_postgresql_connection():
    """ PostgreSQL DB 연결을 반환합니다. (프로덕션용) """
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT", 5432)
        )
        return conn
    except Exception as e:
        print(f"[FATAL] PostgreSQL connection failed: {e}")
        return None

# --- (2) DB 컨텍스트 매니저 (get_db) ---

@contextlib.contextmanager
def get_db() -> ContextManager[tuple[sqlite3.Connection | psycopg2.extensions.connection,
                                     sqlite3.Cursor | psycopg2.extensions.cursor]]:
    """
    FastAPI 의존성 및 스크립트에서 사용할 DB 연결 컨텍스트 매니저.
    DB_MODE에 따라 다른 DB에 연결합니다.
    """
    conn = None
    cur = None
    try:
        if DB_MODE == "production":
            conn = get_postgresql_connection()
            if conn:
                cur = conn.cursor(cursor_factory=DictCursor) # 결과를 dict처럼 접근
        else:
            # 기본값 (development)
            conn = get_sqlite_connection()
            if conn:
                cur = conn.cursor()

        if conn is None or cur is None:
            # 경고는 띄우되, 스크립트가 (notify용) 가짜 함수를 쓸 수 있도록
            # (None, None)을 반환하여 즉시 실패하지 않게 함.
            print("Warning: Could not establish DB connection. Returning (None, None).")
            yield (None, None)
        else:
            # 정상 연결
            yield (conn, cur)

            if conn: conn.commit() # 트랜잭션 완료

    except Exception as e:
        print(f"DB transaction error: {e}")
        if conn: conn.rollback()
        # 예외를 다시 발생시켜 호출자에게 알림
        raise e
    finally:
        if cur: cur.close()
        if conn: conn.close()
