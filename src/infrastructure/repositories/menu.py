from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.menu import Category, MenuItem, RecipeIngredient
from src.infrastructure.repositories.base import BaseRepository
from sqlalchemy import select

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)
        
    async def get_active_categories(self):
         result = await self._session.execute(
             select(Category).where(Category.is_active == True).order_by(Category.sort_order)
         )
         return result.scalars().all()


class MenuItemRepository(BaseRepository[MenuItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MenuItem)
        
    async def get_items_by_category(self, category_id: int):
         result = await self._session.execute(
             select(MenuItem).where(
                 MenuItem.category_id == category_id,
                 MenuItem.is_available == True
             )
         )
         return result.scalars().all()


class RecipeIngredientRepository(BaseRepository[RecipeIngredient]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RecipeIngredient)
        
    async def get_ingredients_by_menu_item(self, menu_item_id: int):
         result = await self._session.execute(
             select(RecipeIngredient).where(RecipeIngredient.menu_item_id == menu_item_id)
         )
         return result.scalars().all()
