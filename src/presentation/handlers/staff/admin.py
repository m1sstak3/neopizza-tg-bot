from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from src.presentation.middlewares.role import RoleMiddleware
from src.domain.entities.user import RoleEnum
from src.infrastructure.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

admin_router = Router(name="admin_router")
admin_router.message.middleware(RoleMiddleware([RoleEnum.ADMIN, RoleEnum.SUPERADMIN]))
admin_router.callback_query.middleware(RoleMiddleware([RoleEnum.ADMIN, RoleEnum.SUPERADMIN]))

@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Отчет для Бухгалтера", callback_data="admin_report")],
        [InlineKeyboardButton(text="👥 Управление персоналом", callback_data="admin_staff")],
    ])
    await message.answer("👑 Панель Администратора", reply_markup=kb)

@admin_router.callback_query(F.data == "admin_report")
async def generate_report(callback: CallbackQuery):
    # Mocking a CSV generation process
    await callback.message.answer("📊 Генерирую отчет по ингредиентам и продажами за смену...\n(Здесь отправляется CSV/Excel файл)")
    await callback.answer()

@admin_router.callback_query(F.data == "admin_staff")
async def manage_staff(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назначить роль", callback_data="staff_manage_assign")],
        [InlineKeyboardButton(text="Снять роль", callback_data="staff_manage_remove")],
        [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text("📝 Управление персоналом. Выберите действие:", reply_markup=kb)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

class StaffManageFSM(StatesGroup):
    waiting_for_user_id = State()

@admin_router.callback_query(F.data == "staff_manage_assign")
async def assign_role_start(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Кассир", callback_data="staff_role_CASHIER")],
        [InlineKeyboardButton(text="👨‍🍳 Шеф", callback_data="staff_role_CHEF")],
        [InlineKeyboardButton(text="🛵 Курьер", callback_data="staff_role_COURIER")],
        [InlineKeyboardButton(text="👑 Админ", callback_data="staff_role_ADMIN")],
        [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text("Выберите роль для назначения (или снятия):", reply_markup=kb)

@admin_router.callback_query(F.data == "staff_manage_remove")
async def remove_role_start(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить роль (Сделать клиентом)", callback_data="staff_role_CLIENT")],
        [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text("Выберите действие:", reply_markup=kb)

@admin_router.callback_query(F.data == "back_to_admin")
async def back_to_admin_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Отчет для Бухгалтера", callback_data="admin_report")],
        [InlineKeyboardButton(text="👥 Управление персоналом", callback_data="admin_staff")],
    ])
    await callback.message.edit_text("👑 Панель Администратора", reply_markup=kb)

@admin_router.callback_query(F.data.startswith("staff_role_"))
async def assign_role_select(callback: CallbackQuery, state: FSMContext):
    role = callback.data.replace("staff_role_", "")
    await state.update_data(target_role=role)
    await state.set_state(StaffManageFSM.waiting_for_user_id)
    
    await callback.message.edit_text(
        f"Выбрана роль: <b>{role}</b>\n\n"
        "Отправьте мне <b>ID</b> пользователя или его <b>@username</b>."
    )

@admin_router.message(StaffManageFSM.waiting_for_user_id)
async def assign_role_finish(message: Message, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    target_role_str = data.get("target_role")
    target_str = message.text.strip()
    
    await state.clear()
    
    repo = UserRepository(db_session)
    user = None
    
    if target_str.startswith("@"):
        user = await repo.get_by_username(target_str)
    elif target_str.isdigit():
        user = await repo.get_by_telegram_id(int(target_str))
        
    if not user:
        await message.answer(f"❌ Пользователь `{target_str}` не найден в базе данных. Он должен хотя бы раз нажать /start.")
        return
        
    user.role = RoleEnum(target_role_str.lower())
    await db_session.commit()
    
    await message.answer(f"✅ Роль пользователя <b>{user.name or user.username or user.telegram_id}</b> успешно изменена на <b>{target_role_str}</b>")
