import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.user import UserRepository
from src.domain.entities.user import RoleEnum

class PrivacyGateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        
        # We only care about Messages and CallbackQueries from actual users
        user = None
        inner_event = None
        
        if event.message:
            inner_event = event.message
            user = event.message.from_user
        elif event.callback_query:
            inner_event = event.callback_query
            user = event.callback_query.from_user
            
        if not user:
            return await handler(event, data)
            
        session: AsyncSession = data.get("db_session")
        if not session:
            # If DB session is not loaded yet, just pass (should be loaded by DbMiddleware before this)
            return await handler(event, data)
            
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_telegram_id(user.id)
        
        # 1. If user doesn't exist, create an inactive dummy or prompt them
        from src.config import config
        if not db_user:
            db_user = await user_repo.create(
                telegram_id=user.id,
                name=user.full_name,
                username=user.username,
                role=RoleEnum.SUPERADMIN if user.id == config.SUPERADMIN_ID else RoleEnum.CLIENT,
                is_active=False # Pending privacy acceptance
            )
            await session.commit()
            
        # Put the user in data so handlers can use it
        data["user"] = db_user
        
        # Auto-upgrade existing user to SuperAdmin if they match and aren't already
        if user.id == config.SUPERADMIN_ID and db_user.role != RoleEnum.SUPERADMIN:
            db_user.role = RoleEnum.SUPERADMIN
            await session.commit()
        
        # 2. Check if the user has accepted the privacy policy
        if not db_user.privacy_accepted_at:
            # If the event is exactly what accepts it, we let it pass to handler or process here
            # But normally we intercept and force them to click a button
            if isinstance(inner_event, CallbackQuery) and inner_event.data == "accept_privacy":
                try:
                    db_user.privacy_accepted_at = datetime.datetime.utcnow().isoformat()
                    db_user.is_active = True
                    await session.commit()
                    await inner_event.answer("Согласие принято!")
                    
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🛵 Заказать доставку", callback_data="mode_delivery")],
                        [InlineKeyboardButton(text="🚶‍♂️ Самовывоз", callback_data="mode_pickup")],
                        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")]
                    ])
                    await inner_event.message.edit_text(
                        f"✅ Согласие принято. Добро пожаловать, {user.first_name}!\n\nВыберите способ получения заказа:",
                        reply_markup=kb
                    )
                    return await handler(event, data)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    await inner_event.answer("Произошла ошибка!", show_alert=True)
                    return
            
            # User hasn't accepted, and didn't click accept -> BLOCK everything else
            if isinstance(inner_event, Message):
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Принимаю условия", callback_data="accept_privacy")
                ]])
                await inner_event.answer(
                    "⚠️ <b>Внимание:</b>\n\n"
                    "Для использования NeoPizza мы обязаны получить ваше согласие на обработку "
                    "персональных данных (ФЗ-152/GDPR). Мы используем их только для доставки еды.\n\n"
                    "Пожалуйста, подтвердите согласие кнопкой ниже.",
                    reply_markup=kb
                )
            elif isinstance(inner_event, CallbackQuery):
                await inner_event.answer("Сначала примите условия обработки данных!", show_alert=True)
                
            return # Stop propagation

        # IF ALREADY ACCEPTED but they clicked an old 'accept_privacy' button hanging in chat
        if isinstance(inner_event, CallbackQuery) and inner_event.data == "accept_privacy":
            await inner_event.answer("Вы уже приняли условия!")
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛵 Заказать доставку", callback_data="mode_delivery")],
                [InlineKeyboardButton(text="🚶‍♂️ Самовывоз", callback_data="mode_pickup")],
                [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")]
            ])
            await inner_event.message.edit_text(
                f"✅ Вы уже в системе, {user.first_name}!\n\nВыберите способ получения заказа:",
                reply_markup=kb
            )
            return await handler(event, data)
            
        # 3. If accepted, proceed to the normal handlers
        return await handler(event, data)
