# db/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Create engine with proper pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_session():
    """
    Dependency for FastAPI endpoints
    Ensures proper session cleanup
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_session_direct():
    """
    Get session directly (not for FastAPI dependencies)
    Used in TwitterOAuth and other non-endpoint code
    IMPORTANT: Caller must close session manually
    """
    return SessionLocal()

def init_db():
    """Initialize database tables"""
    from db.models import User, UserProfile, Analysis, PeerMatch, OAuthState, TweetsCache, PeerPool
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


def test_connection():
    """Test database connection"""
    try:
        session = get_session()
        session.execute(text("SELECT 1"))  # ← Fixed: wrapped in text()
        session.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False