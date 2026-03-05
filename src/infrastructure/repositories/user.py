from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User
from src.infrastructure.repositories.base import BaseRepository
from sqlalchemy import select

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
        
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        clean_username = username.lstrip('@')
        result = await self._session.execute(
            select(User).where(User.username == clean_username)
        )
        return result.scalar_one_or_none()
