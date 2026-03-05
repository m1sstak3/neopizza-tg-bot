from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.order import Order, OrderItem
from src.infrastructure.repositories.base import BaseRepository
from sqlalchemy import select

class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def get_orders_by_user(self, user_id: int):
         result = await self._session.execute(
             select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
         )
         return result.scalars().all()
         
    async def get_active_orders_by_restaurant(self, restaurant_id: int):
         from src.domain.entities.order import OrderStatus
         
         result = await self._session.execute(
             select(Order).where(
                 Order.restaurant_id == restaurant_id,
                 Order.status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
             ).order_by(Order.created_at.asc())
         )
         return result.scalars().all()

    async def get_orders_by_status_with_items(self, status) -> list[Order]:
         from sqlalchemy.orm import selectinload
         result = await self._session.execute(
             select(Order).options(
                 selectinload(Order.items).selectinload(OrderItem.menu_item)
             ).where(Order.status == status).order_by(Order.created_at.asc())
         )
         return result.scalars().all()


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrderItem)
