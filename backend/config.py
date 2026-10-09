import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-default-key-change-in-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-default-key-change-in-prod")
    JWT_EXPIRES_IN = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", 24)))
    JWT_COOKIE_NAME = "access_token"
    JWT_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "t")
    JWT_COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")

    # PostgreSQL Database Configuration
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "auth_db")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) or None
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_URL = os.getenv("REDIS_URL")

    # OTP and Registration Parameters
    REGISTRATION_TTL = int(os.getenv("REGISTRATION_TTL", 300))  # 5 minutes
    OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 5))
    OTP_COOLDOWN_SECONDS = int(os.getenv("OTP_COOLDOWN_SECONDS", 60))  # 1 minute cooldown
    OTP_MAX_RESENDS = int(os.getenv("OTP_MAX_RESENDS", 3))

    # SMTP Email Configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "t")
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "t")
    SMTP_DEV_MODE = os.getenv("SMTP_DEV_MODE", "false").lower() in ("true", "1", "t")

    CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173").split(",") if origin.strip()]


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    REGISTRATION_TTL = 300
    OTP_COOLDOWN_SECONDS = 60
    OTP_MAX_ATTEMPTS = 5
    OTP_MAX_RESENDS = 3
    SMTP_DEV_MODE = True
