import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get("SECRET_KEY") or "tu_clave_secreta_predeterminada"

    # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "postgresql://postgres:0001@localhost:5432/calculai_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Clave API de Claude
    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY") or "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"

    # Configuración de seguridad
    SESSION_COOKIE_SECURE = os.environ.get("PRODUCTION", "False").lower() == "true"
    REMEMBER_COOKIE_SECURE = os.environ.get("PRODUCTION", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Configuración de rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # Otras configuraciones
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max-limit

    # Configuración de depuración
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ["true", "1", "t"]

    # Configuración de correo electrónico (para futuras funcionalidades)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "False").lower() in ["true", "1", "t"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # Configuración de la aplicación
    APP_NAME = "CalculAI"
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or "admin@calculai.com"

    # Configuración de la base de datos para el asistente virtual
    DB_CONFIG = {
        'dbname': 'calculai_db',
        'user': 'postgres',
        'password': '0001',
        'host': 'localhost',
        'port': '5432'
    }

    @staticmethod
    def init_app(app):
        pass