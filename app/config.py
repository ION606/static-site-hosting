import os
from secrets import token_hex


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or token_hex(64)
    SQLALCHEMY_DATABASE_URI = "sqlite:////app/instance/db.sqlite"
    UPLOAD_FOLDER = "sites"
    SERVER_NAME = "tinysite.cloud"
    SESSION_COOKIE_DOMAIN = ".tinysite.cloud"
    SESSION_COOKIE_NAME = "tinysite_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    PORT = 5121
