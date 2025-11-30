from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from config.settings import settings
from db.models import Base
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before using
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Get database session"""
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        session.close()
        raise


def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


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