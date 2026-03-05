from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from src.presentation.middlewares.role import RoleMiddleware
from src.domain.entities.user import RoleEnum
from src.infrastructure.repositories.order import OrderRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.order import OrderStatus

chef_router = Router(name="chef_router")

# Require Chef, Admin or Superadmin role
chef_router.message.middleware(RoleMiddleware([RoleEnum.CHEF, RoleEnum.ADMIN]))
chef_router.callback_query.middleware(RoleMiddleware([RoleEnum.CHEF, RoleEnum.ADMIN]))

@chef_router.message(Command("chef", "kitchen"))
async def chef_panel(message: Message, db_session: AsyncSession):
    repo = OrderRepository(db_session)
    cooking_orders = await repo.get_orders_by_status_with_items(OrderStatus.COOKING)
    
    if not cooking_orders:
        await message.answer("👨‍🍳 Панель Повара.\n\nСейчас нет заказов в готовке.")
        return
        
    for order in cooking_orders:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍳 ГОТОВО (На сборку)", callback_data=f"chef_ready_{order.id}")]
        ])
        
        items_text = "\n".join([f"• {item.menu_item.name if item.menu_item else 'Блюдо удалено'} x{item.quantity}" for item in order.items])
        
        await message.answer(
            f"🍳 <b>Готовим заказ #{order.id}</b>\n\n"
            f"<b>Состав заказа:</b>\n{items_text}\n\n"
            f"Адрес/Тип: {'Самовывоз' if order.delivery_type == 'pickup' else 'Доставка'}",
            reply_markup=kb
        )

@chef_router.callback_query(F.data.startswith("chef_ready_"))
async def order_ready(callback: CallbackQuery, db_session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    repo = OrderRepository(db_session)
    order = await repo.get_by_id(order_id)
    
    if order and order.status == OrderStatus.COOKING:
        order.status = OrderStatus.READY
        await db_session.commit()
        
        await callback.message.edit_text(f"✅ Заказ #{order.id} помечен как 'Готово'.")
        # Notify Couriers / Add to available queue / Notify client self-pickup
        # (Using Celery tasks or direct broadcast logic here)
    else:
        await callback.answer("Заказ уже отдан или не найден.", show_alert=True)
