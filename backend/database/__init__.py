import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///backend/content.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for all models
Base = declarative_base()


async def init_db():
    """Initialize database tables"""
    # Import models to ensure they are registered with Base.metadata
    from database.models import (  # noqa: F811
        Session, Transcript, Speakers, Utterances, Guest, GeneratedContent,
        PromptTemplate, PromptUsage, TokenUsage, UsageSummary
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        yield session


async def close_db():
    """Close database connections"""
    await engine.dispose()


# Lazy imports to avoid circular dependency (models import Base from this module)
from database.models import (  # noqa: E402, F811
    Session, Transcript, Speakers, Utterances, Guest, GeneratedContent,
    PromptTemplate, PromptUsage, TokenUsage, UsageSummary
)
from database.repository import Repository  # noqa: E402

__all__ = [
    "Base", "engine", "AsyncSessionLocal", "init_db", "get_session", "close_db",
    "Session", "Transcript", "Speakers", "Utterances", "Guest", "GeneratedContent",
    "PromptTemplate", "PromptUsage", "TokenUsage", "UsageSummary",
    "Repository"
]
