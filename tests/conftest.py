import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.infrastructure.db.models.base import Base

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://neopizza_user:neopizza_password@localhost:5432/neopizza_test")

@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture(scope="function")
async def db_session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
