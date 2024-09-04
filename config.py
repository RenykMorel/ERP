class Config:
    # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        "mysql+mysqlconnector://root:@localhost/calculai_db?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"charset": "utf8mb4", "collation": "utf8mb4_unicode_ci"},
    }

    # Clave API de Claude
    CLAUDE_API_KEY = "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"
