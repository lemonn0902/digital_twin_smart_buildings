from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings


settings = get_settings()

engine = create_engine(settings.db_url, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
