from typing import Any, Generic, Type, TypeVar, Optional, Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model_class: Type[ModelType]):
        self._session = session
        self._model_class = model_class

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        result = await self._session.execute(
            select(self._model_class).where(self._model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self._session.execute(
            select(self._model_class).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelType:
        obj = self._model_class(**kwargs)
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def update(self, id: Any, **kwargs: Any) -> Optional[ModelType]:
        result = await self._session.execute(
            update(self._model_class)
            .where(self._model_class.id == id)
            .values(**kwargs)
            .returning(self._model_class)
        )
        await self._session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: Any) -> bool:
        result = await self._session.execute(
            delete(self._model_class).where(self._model_class.id == id)
        )
        await self._session.flush()
        return result.rowcount > 0
