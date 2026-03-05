from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.presentation.fsm.order import OrderFSM
from src.infrastructure.repositories.restaurant import RestaurantRepository

order_flow_router = Router(name="order_flow_router")

@order_flow_router.callback_query(F.data.in_(["mode_delivery", "mode_pickup"]))
async def select_delivery_mode(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    mode = callback.data.split("_")[1]
    
    # Store selected mode in FSM state
    await state.update_data(delivery_mode=mode)
    await state.set_state(OrderFSM.choosing_restaurant)
    
    # Fetch active restaurants
    repo = RestaurantRepository(db_session)
    restaurants = await repo.get_active_restaurants()
    
    if not restaurants:
        await callback.answer("К сожалению, сейчас нет доступных ресторанов.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb_builder = []
    for r in restaurants:
        kb_builder.append([InlineKeyboardButton(text=r.name, callback_data=f"rest_{r.id}")])
    kb_builder.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_builder)
    
    text = "🚚 Выберите ресторан для доставки:" if mode == "delivery" else "🚶‍♂️ Выберите ресторан для самовывоза:"
    await callback.message.edit_text(text, reply_markup=kb)

@order_flow_router.callback_query(F.data == "back_to_rest")
async def back_to_rest_handler(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    data = await state.get_data()
    mode = data.get("delivery_mode", "delivery")
    
    # Simulate a callback data to reuse the existing function
    from aiogram.types import CallbackQuery
    callback.data = f"mode_{mode}"
    await select_delivery_mode(callback, state, db_session)
