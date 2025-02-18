import os
from secrets import token_hex


def get_secret_key():
    try:
        with open("/app/instance/secret.key", "rb") as f:
            return bytes.hex(f.readline())
    except FileNotFoundError as e:
        if not os.path.exists("/app/instance"):
            os.mkdir("/app/instance")

        with open("/app/instance/secret.key", "wb") as f:
            newKey = token_hex(64)
            f.write(bytearray.fromhex(newKey))
            return newKey


class Config:
    SECRET_KEY = get_secret_key()
    SQLALCHEMY_DATABASE_URI = "sqlite:////app/instance/db.sqlite"
    UPLOAD_FOLDER = "/app/sites"
    SERVER_NAME = "tinysite.cloud"
    SESSION_COOKIE_DOMAIN = ".tinysite.cloud"
    SESSION_COOKIE_NAME = "tinysite_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    PORT = 5121
    RESERVED_SUBDOMAINS = {
        "",
        "www",
        "api",
        "admin",
        "support",
        "docs",
        "blog",
        "cdn",
        "test",
        "dev",
        "staging",
        "secure",
        "mail",
        "status",
        "gateway",
    }
