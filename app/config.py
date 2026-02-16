from __future__ import annotations

import os

DEFAULT_DB_URL = "sqlite:///consumption_viewer.db"
SCHEMA_VERSION = "v1"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DB_URL)
