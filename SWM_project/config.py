"""
EcoLoop Configuration
=====================
Reads settings from environment variables (via .env file).
Never put real secrets in this file.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask core ──────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    # ── Database ─────────────────────────────────────────────────────────────
    _custom_db_url = os.environ.get("DATABASE_URL")
    if _custom_db_url:
        SQLALCHEMY_DATABASE_URI = _custom_db_url
    elif IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/ecoloop.db"
    else:
        _db_user = os.environ.get("DB_USER", "root")
        _db_pw   = os.environ.get("DB_PASSWORD", "")
        _db_host = os.environ.get("DB_HOST", "localhost")
        _db_port = os.environ.get("DB_PORT", "3306")
        _db_name = os.environ.get("DB_NAME", "ecoloop")
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{_db_user}:{_db_pw}@{_db_host}:{_db_port}/{_db_name}"
            "?charset=utf8mb4"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # ── Uploads ──────────────────────────────────────────────────────────────
    if IS_VERCEL:
        UPLOAD_FOLDER = "/tmp/uploads"
    else:
        UPLOAD_FOLDER = os.path.abspath(
            os.environ.get("UPLOAD_FOLDER", "instance/uploads")
        )
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 10)) * 1024 * 1024

    # ── AI Classifier ────────────────────────────────────────────────────────
    if IS_VERCEL:
        MODEL_PATH = "/tmp/models/ecoloop_classifier.h5"
    else:
        MODEL_PATH = os.path.abspath(
            os.environ.get("MODEL_PATH", "instance/models/ecoloop_classifier.h5")
        )
    MODEL_VERSION = os.environ.get("MODEL_VERSION", "1.0.0")
    CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.60))

    # ── Recovery engine ──────────────────────────────────────────────────────
    # Repair is economic when cost < this fraction of resale value
    REPAIR_COST_RATIO_THRESHOLD = float(
        os.environ.get("REPAIR_COST_RATIO_THRESHOLD", 0.60)
    )

    # ── WTF / CSRF ───────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    UPLOAD_FOLDER = "/tmp/ecoloop_test_uploads"


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
