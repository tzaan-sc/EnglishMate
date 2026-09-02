import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SQLITE_FALLBACK_URI = f"sqlite:///{BASE_DIR / 'instance' / 'englishmate.db'}"


def _resolve_db_uri() -> str:
    """Trả về PostgreSQL URI nếu kết nối thành công, ngược lại fallback về SQLite."""
    pg_url = os.getenv("DATABASE_URL", "")
    if pg_url and pg_url.startswith("postgresql"):
        try:
            import psycopg2
            from urllib.parse import urlparse
            p = urlparse(pg_url)
            conn = psycopg2.connect(
                dbname=p.path.lstrip("/"),
                user=p.username,
                password=p.password,
                host=p.hostname,
                port=p.port or 5432,
                connect_timeout=3,
            )
            conn.close()
            return pg_url  # PostgreSQL kết nối thành công
        except Exception as e:
            print(f"\n[⚠️  DB FALLBACK] Không kết nối được PostgreSQL: {e}")
            print(f"[⚠️  DB FALLBACK] Tự động chuyển sang SQLite: {SQLITE_FALLBACK_URI}\n")
    return SQLITE_FALLBACK_URI


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = _resolve_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # OAuth Credentials
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
    FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")

    # SMTP Email Credentials
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "t")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
