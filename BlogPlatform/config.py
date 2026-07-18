"""
Application configuration.
Reads sensitive values from environment variables where possible,
falling back to sane defaults for local development.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key used for sessions / CSRF tokens. In production, set this
    # via the SECRET_KEY environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLite database stored alongside the application.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size

    # Pagination
    POSTS_PER_PAGE = 6

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
