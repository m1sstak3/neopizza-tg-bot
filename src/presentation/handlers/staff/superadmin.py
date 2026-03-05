from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from src.presentation.middlewares.role import RoleMiddleware
from src.domain.entities.user import RoleEnum
from src.infrastructure.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

superadmin_router = Router(name="superadmin_router")

# Require Superadmin role
superadmin_router.message.middleware(RoleMiddleware([RoleEnum.SUPERADMIN]))
superadmin_router.callback_query.middleware(RoleMiddleware([RoleEnum.SUPERADMIN]))



@superadmin_router.message(Command("superadmin", "super"))
async def superadmin_panel(message: Message, db_session: AsyncSession):
    # Calculate some basic mock stats
    user_repo = UserRepository(db_session)
    result = await db_session.execute(select(func.count(user_repo._model_class.telegram_id)))
    users_count = result.scalar() or 0
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Все точки (Аналитика)", callback_data="super_analytics")],
        [InlineKeyboardButton(text="👥 Управление Админами", callback_data="super_manage_admins")],
        [InlineKeyboardButton(text="🔒 Заблокированные", callback_data="super_bans")]
    ])
    
    await message.answer(
        f"👑 <b>SuperAdmin Panel</b>\n\n"
        f"Всего пользователей в базе: {users_count}\n\n"
        f"<i>Для управления ролями перейдите в панель /admin</i>",
        reply_markup=kb
    )

@superadmin_router.callback_query(F.data == "super_analytics")
async def super_analytics(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_superadmin")]
    ])
    await callback.message.edit_text("📈 Аналитика по всем точкам (Mock): Выручка за сегодня: 154,300 ₽ | Заказов: 84", reply_markup=kb)

@superadmin_router.callback_query(F.data == "super_manage_admins")
async def super_manage_admins(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_superadmin")]
    ])
    await callback.message.edit_text(
        "👥 Для назначения или снятия любых ролей, включая Админов,\n"
        "перейдите в стандартную панель управления персоналом: /admin", reply_markup=kb
    )

@superadmin_router.callback_query(F.data == "super_bans")
async def super_bans(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_superadmin")]
    ])
    await callback.message.edit_text("🔒 Управление блокировками в разработке. Для ручного снятия бана обращайтесь в БД.", reply_markup=kb)
    
@superadmin_router.callback_query(F.data == "back_to_superadmin")
async def back_to_superadmin_handler(callback: CallbackQuery, db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    result = await db_session.execute(select(func.count(user_repo._model_class.telegram_id)))
    users_count = result.scalar() or 0
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Все точки (Аналитика)", callback_data="super_analytics")],
        [InlineKeyboardButton(text="👥 Управление Админами", callback_data="super_manage_admins")],
        [InlineKeyboardButton(text="🔒 Заблокированные", callback_data="super_bans")]
    ])
    await callback.message.edit_text(
        f"👑 <b>SuperAdmin Panel</b>\n\n"
        f"Всего пользователей в базе: {users_count}\n\n"
        f"<i>Для управления ролями перейдите в панель /admin</i>", reply_markup=kb
    )
