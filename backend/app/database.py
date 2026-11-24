import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        url = get_settings().DATABASE_URL
        kwargs = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs = {"connect_args": {"check_same_thread": False}}
        _engine = create_engine(url, **kwargs)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def get_db():
    Session = get_session_local()
    db = Session()
    try:
        yield db
    finally:
        db.close()


def init_db(max_retries: int = 10, retry_delay: float = 2.0):
    """Initialize database tables with connection retries for Docker environments."""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Connecting to database (attempt %d/%d)...", attempt, max_retries)
            engine = _get_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully.")
            return
        except Exception as e:
            logger.warning("Database connection attempt %d failed: %s", attempt, e)
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error("Failed to connect to database after %d attempts.", max_retries)
                raise
