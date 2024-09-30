import os
import secrets
from dotenv import load_dotenv

load_dotenv()

def str_to_bool(s):
    return s.lower() in ('true', 't', 'yes', 'y', '1')

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "postgresql://postgres:0001@localhost:5432/calculai_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

    SESSION_COOKIE_SECURE = str_to_bool(os.environ.get("PRODUCTION", "False"))
    REMEMBER_COOKIE_SECURE = str_to_bool(os.environ.get("PRODUCTION", "False"))
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max-limit

    DEBUG = str_to_bool(os.environ.get("FLASK_DEBUG", "False"))

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = str_to_bool(os.environ.get("MAIL_USE_TLS", "False"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    APP_NAME = "CalculAI"
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or "admin@calculai.com"

    DB_CONFIG = {
        'dbname': 'calculai_db',
        'user': 'postgres',
        'password': '0001',
        'host': 'localhost',
        'port': '5432'
    }

    @classmethod
    def check_config(cls):
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL",
            "CLAUDE_API_KEY",
            # Añade otras variables críticas aquí
        ]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")

    @classmethod
    def init_app(cls, app):
        cls.check_config()
        # Aquí puedes añadir más lógica de inicialización si es necesario