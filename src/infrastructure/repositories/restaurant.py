from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.restaurant import Restaurant, DeliveryZoneTier
from src.infrastructure.repositories.base import BaseRepository
from sqlalchemy import select

class RestaurantRepository(BaseRepository[Restaurant]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Restaurant)

    async def get_active_restaurants(self):
        result = await self._session.execute(
            select(Restaurant).where(Restaurant.is_active == True)
        )
        return result.scalars().all()


class DeliveryZoneTierRepository(BaseRepository[DeliveryZoneTier]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DeliveryZoneTier)
