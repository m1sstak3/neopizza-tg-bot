from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.presentation.handlers.client.order_flow import order_flow_router
from src.presentation.fsm.order import OrderFSM
from src.infrastructure.repositories.menu import MenuItemRepository
from src.domain.entities.order import DeliveryType
from src.infrastructure.cache.cart import CartSession
from redis.asyncio import Redis
from src.config import config

@order_flow_router.callback_query(F.data == "view_cart")
async def view_cart(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession, redis: Redis):
    cart_session = CartSession(redis, callback.from_user.id)
    cart = await cart_session.get_cart()
    
    if not cart:
        await callback.answer("Ваша корзина пуста 🛒", show_alert=True)
        return
        
    repo = MenuItemRepository(db_session)
    
    text = "<b>🛒 Ваша Корзина:</b>\n\n"
    total = 0
    kb_builder = []
    
    for item_id, item_data in cart.items():
        # Fetch name using repo (cached ideally)
        db_item = await repo.get_by_id(int(item_id))
        
        name = db_item.name if db_item else "Удален из меню"
        qty = item_data["quantity"]
        price = item_data["price"] * qty
        total += price
        
        text += f"• {name} x{qty} — {price}₽\n"
        kb_builder.append([InlineKeyboardButton(text=f"➖ Убрать {name}", callback_data=f"remove_item_{item_id}")])
        
    text += f"\n<b>Итого: {total}₽</b>"
    
    # Validation logic inside state
    data = await state.get_data()
    mode = data.get("delivery_mode", "delivery")
    
    # 1200 MOV for delivery
    if mode == "delivery":
        if total < 1200:
            text += f"\n\n<i>⚠️ Минимальная сумма для доставки 1200₽. Не хватает {1200 - total}₽.</i>"
            kb_builder.append([InlineKeyboardButton(text="🛒 В меню за добавкой", callback_data="rest_0")]) # Mock back to categories
        else:
             kb_builder.append([InlineKeyboardButton(text="✅ Оформить (Доставка)", callback_data="checkout_start")])
    elif mode == "pickup":
        kb_builder.append([InlineKeyboardButton(text="✅ Оформить (Самовывоз)", callback_data="checkout_start")])
        
    kb_builder.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")])
    kb_builder.append([InlineKeyboardButton(text="🔙 В меню", callback_data="rest_0")])
        
    kb = InlineKeyboardMarkup(inline_keyboard=kb_builder)
    
    await state.set_state(OrderFSM.in_cart)
    await callback.message.edit_text(text, reply_markup=kb)


@order_flow_router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery, redis: Redis):
    cart_session = CartSession(redis, callback.from_user.id)
    await cart_session.clear_cart()
    await callback.answer("Корзина очищена 🗑", show_alert=True)
    
    # Redirect to start or menu wrapper
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 На главное меню", callback_data="back_to_start")]
    ])
    await callback.message.edit_text("Корзина пуста. Выберите что-нибудь из меню!", reply_markup=kb)


@order_flow_router.callback_query(F.data.startswith("remove_item_"))
async def remove_cart_item(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession, redis: Redis):
    item_id = int(callback.data.split("_")[2])
    
    cart_session = CartSession(redis, callback.from_user.id)
    await cart_session.decrement_item(item_id)
    
    # Re-render cart
    await view_cart(callback, state, db_session, redis)
