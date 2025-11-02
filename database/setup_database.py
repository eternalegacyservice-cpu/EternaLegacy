import sqlite3
import pathlib
import sys
import os
from dotenv import load_dotenv
import psycopg2
import contextlib

# --- (✨ 새로 추가) .env 파일 로드 ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
# --- (여기까지 새로 추가) ---

# --- (✨ 새로 추가) .env에서 DB 설정 읽기 ---
DB_MODE = os.environ.get("DB_MODE", "local")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
SQLITE_DB_PATH = PROJECT_ROOT / "data" / "wills.db"
# --- (여기까지 새로 추가) ---


@contextlib.contextmanager
def get_db_connection():
    # ... (기존 get_db_connection 함수와 동일) ...
    conn = None
    try:
        if DB_MODE == "production":
            print(f"Connecting to PostgreSQL database at {DB_HOST}...")
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            print("PostgreSQL connection successful.")
        else:
            print(f"Connecting to SQLite database at {SQLITE_DB_PATH}...")
            SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(SQLITE_DB_PATH)
            print("SQLite connection successful.")

        yield conn

    except Exception as e:
        print(f"Error connecting to database ({DB_MODE} mode): {e}", file=sys.stderr)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


def create_tables(conn):
    """
    (✨ 업그레이드) DB_MODE에 맞는 SQL 문법으로 테이블을 생성합니다.
    """

    print("Applying database schema...")

    # (✨ 수정) PostgreSQL은 AUTOINCREMENT 대신 SERIAL PRIMARY KEY를 사용
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        created_at TEXT NOT NULL
    );
    """

    wills_table_sql = """
    CREATE TABLE IF NOT EXISTS wills (
        id TEXT PRIMARY KEY,
        owner_email TEXT NOT NULL,
        policy TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (owner_email) REFERENCES users (email) ON DELETE CASCADE
    );
    """

    versions_table_sql = """
    CREATE TABLE IF NOT EXISTS versions (
        id {autoincrement_pk},
        will_id TEXT NOT NULL,
        version INTEGER NOT NULL,
        title TEXT,
        content TEXT,
        created_at TEXT NOT NULL,
        signed BOOLEAN NOT NULL,
        encrypted BOOLEAN NOT NULL,
        signature_b64 TEXT,
        cipher TEXT,
        salt_b64 TEXT,
        iv_b64 TEXT,
        FOREIGN KEY (will_id) REFERENCES wills (id) ON DELETE CASCADE
    );
    """

    grants_table_sql = """
    CREATE TABLE IF NOT EXISTS grants (
        id {autoincrement_pk},
        will_id TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (will_id) REFERENCES wills (id) ON DELETE CASCADE
    );
    """

    # (✨ 새로 추가) notifications 테이블 SQL
    notifications_table_sql = """
    CREATE TABLE IF NOT EXISTS notifications (
        id {autoincrement_pk},
        timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
        level VARCHAR(10) NOT NULL,
        title TEXT NOT NULL,
        body TEXT,
        status VARCHAR(20)
    );
    """

    # DB_MODE에 따라 SQL 문법 변경
    if DB_MODE == "production":
        # PostgreSQL 문법
        autoincrement_key = "SERIAL PRIMARY KEY"
        timestamp_type = "TIMESTAMPTZ"
    else:
        # SQLite 문법
        autoincrement_key = "INTEGER PRIMARY KEY AUTOINCREMENT"
        timestamp_type = "TEXT" # SQLite는 TEXT로 UTC 시간 저장

    # 최종 SQL 완성
    versions_table_sql = versions_table_sql.format(autoincrement_pk=autoincrement_key)
    grants_table_sql = grants_table_sql.format(autoincrement_pk=autoincrement_key)
    notifications_table_sql = notifications_table_sql.format(autoincrement_pk=autoincrement_key, timestamp_type=timestamp_type)


    try:
        with conn.cursor() as c:
            print("Creating/Updating table: users...")
            c.execute(users_table_sql)
            print("Creating/Updating table: wills...")
            c.execute(wills_table_sql)
            print("Creating/Updating table: versions...")
            c.execute(versions_table_sql)
            print("Creating/Updating table: grants...")
            c.execute(grants_table_sql)

            # (✨ 새로 추가) notifications 테이블 생성
            print("Creating/Updating table: notifications...")
            c.execute(notifications_table_sql)

        conn.commit()
        print("Tables schema updated successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}", file=sys.stderr)
        conn.rollback()

def main():
    print(f"Starting database setup (Mode: {DB_MODE})...")

    with get_db_connection() as conn:
        if conn is not None:
            create_tables(conn)
            print("Database setup complete.")
        else:
            print("Error! cannot create the database connection.", file=sys.stderr)

if __name__ == '__main__':
    main()
