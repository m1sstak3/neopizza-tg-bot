from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from src.presentation.middlewares.role import RoleMiddleware
from src.domain.entities.user import RoleEnum
from src.infrastructure.repositories.order import OrderRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.order import OrderStatus

cashier_router = Router(name="cashier_router")

# Require Cashier, Admin or Superadmin role
cashier_router.message.middleware(RoleMiddleware([RoleEnum.CASHIER, RoleEnum.ADMIN]))
cashier_router.callback_query.middleware(RoleMiddleware([RoleEnum.CASHIER, RoleEnum.ADMIN]))

@cashier_router.message(Command("cashier"))
async def cashier_panel(message: Message, db_session: AsyncSession):
    repo = OrderRepository(db_session)
    # Ideally link cashier to a specific restaurant. For MVP let's assume global or hardcoded
    # We'll fetch all PENDING orders globally.
    
    pending_orders = await repo.get_orders_by_status_with_items(OrderStatus.PENDING)
    
    if not pending_orders:
        await message.answer("💼 Панель Кассира.\n\nСейчас нет новых заказов.")
        return
        
    for order in pending_orders:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять (в готовку)", callback_data=f"cashier_accept_{order.id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cashier_cancel_{order.id}")]
        ])
        
        items_text = "\n".join([f"• {item.menu_item.name if item.menu_item else 'Блюдо удалено'} x{item.quantity}" for item in order.items])
        
        await message.answer(
            f"📦 <b>Новый заказ #{order.id}</b>\n\n"
            f"<b>Состав заказа:</b>\n{items_text}\n\n"
            f"Сумма: {order.total_amount}₽\n"
            f"Тип: {'Доставка' if order.delivery_type == 'delivery' else 'Самовывоз'}",
            reply_markup=kb
        )

@cashier_router.callback_query(F.data.startswith("cashier_accept_"))
async def accept_order(callback: CallbackQuery, db_session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    repo = OrderRepository(db_session)
    order = await repo.get_by_id(order_id)
    
    if order and order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CONFIRMED
        # Instantly to COOKING if POS manual API integration is assumed later
        order.status = OrderStatus.COOKING 
        await db_session.commit()
        
        await callback.message.edit_text(f"✅ Заказ #{order.id} передан на кухню.")
        # Notify Chef here
    else:
        await callback.answer("Заказ уже обработан или не найден.", show_alert=True)
