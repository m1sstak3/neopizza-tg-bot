from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from src.domain.entities.user import RoleEnum

class RoleMiddleware(BaseMiddleware):
    def __init__(self, allowed_roles: List[RoleEnum]):
        super().__init__()
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        user = data.get("user")
        if not user:
            # Maybe fallback to normal handler or block entirely
            return
            
        if user.role not in self.allowed_roles and user.role != RoleEnum.SUPERADMIN:
            # Silently drop or send an alert if it's a message
            from aiogram.types import Message, CallbackQuery
            if isinstance(event, Message):
                await event.answer("🚫 У вас нет доступа к этому разделу.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Доступ запрещен.", show_alert=True)
            return

        return await handler(event, data)
