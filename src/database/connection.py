"""Database connection and session management"""

import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration"""

    def __init__(self):
        self.server = os.getenv("DB_SERVER", "")
        self.database = os.getenv("DB_NAME", "")
        self.username = os.getenv("DB_USERNAME", "")
        self.password = os.getenv("DB_PASSWORD", "")
        self.driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    def get_connection_string(self) -> str:
        """Build Azure SQL connection string"""
        if not all([self.server, self.database, self.username, self.password]):
            # Return SQLite for development if Azure SQL not configured
            return "sqlite:///consumption_viewer.db"

        params = quote_plus(
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"


# Create database engine
config = DatabaseConfig()
engine = create_engine(
    config.get_connection_string(),
    echo=os.getenv("APP_ENV") == "development",
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """Initialize database schema"""
    from src.models.database import Base

    Base.metadata.create_all(bind=engine)
