from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from src.presentation.middlewares.role import RoleMiddleware
from src.domain.entities.user import RoleEnum
from src.infrastructure.repositories.order import OrderRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.order import OrderStatus, DeliveryType

courier_router = Router(name="courier_router")

courier_router.message.middleware(RoleMiddleware([RoleEnum.COURIER, RoleEnum.ADMIN]))
courier_router.callback_query.middleware(RoleMiddleware([RoleEnum.COURIER, RoleEnum.ADMIN]))

@courier_router.message(Command("courier"))
async def courier_panel(message: Message, db_session: AsyncSession):
    repo = OrderRepository(db_session)
    result = await db_session.execute(
        repo._model_class.__table__.select().where(
            repo._model_class.status == OrderStatus.READY,
            repo._model_class.delivery_type == DeliveryType.DELIVERY
            # AND courier_id == None
        )
    )
    ready_orders = result.fetchall()
    
    if not ready_orders:
        await message.answer("🛵 Панель Курьера.\n\nСейчас нет готовых заказов на доставку.")
        return
        
    for order in ready_orders:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏃 Взять заказ", callback_data=f"courier_take_{order.id}")]
        ])
        
        await message.answer(
            f"📍 <b>Доставка #{order.id}</b>\n"
            f"Куда: {order.delivery_address}\n"
            f"Сумма: {order.total_amount}₽",
            reply_markup=kb
        )

@courier_router.callback_query(F.data.startswith("courier_take_"))
async def take_order(callback: CallbackQuery, db_session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    repo = OrderRepository(db_session)
    order = await repo.get_by_id(order_id)
    
    # Needs locking mechanism ideally, checking if courier is null
    if order and order.status == OrderStatus.READY and not order.courier_id:
        order.courier_id = callback.from_user.id
        order.status = OrderStatus.DELIVERING
        await db_session.commit()
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ ДОСТАВЛЕН", callback_data=f"courier_done_{order.id}")]
        ])
        
        await callback.message.edit_text(f"🏃 Вы взяли заказ #{order.id} в работу.\nПо готовности нажмите 'Доставлен'.", reply_markup=kb)
    else:
        await callback.answer("Этот заказ уже забрал другой курьер.", show_alert=True)


@courier_router.callback_query(F.data.startswith("courier_done_"))
async def mark_delivered(callback: CallbackQuery, db_session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    repo = OrderRepository(db_session)
    order = await repo.get_by_id(order_id)
    
    if order and order.status == OrderStatus.DELIVERING and order.courier_id == callback.from_user.id:
        order.status = OrderStatus.DELIVERED
        await db_session.commit()
        await callback.message.edit_text(f"🏁 Заказ #{order.id} успешно доставлен!")
    else:
        await callback.answer("Ошибка статуса или не ваш заказ.", show_alert=True)
