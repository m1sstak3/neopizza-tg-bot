import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db.models.user import User, RoleEnum
from src.infrastructure.repositories.user import UserRepository
import logging

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.create(
        telegram_id=123456789,
        name="Test User",
        phone="+79991112233"
    )
    
    assert user.telegram_id == 123456789
    assert user.name == "Test User"
    assert user.role == RoleEnum.CLIENT

@pytest.mark.asyncio
async def test_get_user_by_telegram_id(db_session: AsyncSession):
    repo = UserRepository(db_session)
    await repo.create(
        telegram_id=987654321,
        name="Get User"
    )
    
    fetched = await repo.get_by_telegram_id(987654321)
    
    assert fetched is not None
    assert fetched.name == "Get User"

@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.create(
        telegram_id=111222333,
        name="Old Name"
    )
    
    updated = await repo.update(user.telegram_id, name="New Name", role=RoleEnum.CASHIER)
    
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.role == RoleEnum.CASHIER
