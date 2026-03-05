from aiogram import F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.presentation.handlers.client.cart_view import order_flow_router
from src.presentation.fsm.order import OrderFSM
from src.infrastructure.repositories.order import OrderRepository
from src.domain.entities.order import DeliveryType, PaymentMethod
from src.infrastructure.cache.cart import CartSession
from redis.asyncio import Redis
from src.config import config


@order_flow_router.callback_query(F.data == "checkout_start")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mode = data.get("delivery_mode", "delivery")
    
    # Let's ask for the payment method first
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Карта (Telegram Payments)", callback_data="pay_online")],
        [InlineKeyboardButton(text="💵 Наличными курьеру", callback_data="pay_cash")]
    ])
    
    await state.set_state(OrderFSM.waiting_for_payment)
    await callback.message.edit_text("Выберите способ оплаты:", reply_markup=kb)

@order_flow_router.callback_query(F.data.in_(["pay_online", "pay_cash"]))
async def select_payment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(payment_method=callback.data)
    data = await state.get_data()
    mode = data.get("delivery_mode", "delivery")
    
    if mode == "delivery":
        await state.set_state(OrderFSM.entering_address)
        
        # Request location or text address
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📍 Отправить геопозицию", request_location=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
        
        await callback.message.delete()
        await callback.message.answer(
            "📍 Пожалуйста, введите ваш адрес доставки (Улица, Дом, Квартира, Подъезд) или отправьте геопозицию:",
            reply_markup=kb
        )
    else:
        await state.set_state(OrderFSM.choosing_pickup_time)
        
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Как можно скорее")],
            [KeyboardButton(text="Через 15 минут"), KeyboardButton(text="Через 30 минут")],
            [KeyboardButton(text="Через 45 минут"), KeyboardButton(text="Через 1 час")]
        ], resize_keyboard=True, one_time_keyboard=True)
        
        await callback.message.delete()
        await callback.message.answer("Когда планируете забрать? Выберите или напишите время:", reply_markup=kb)
        # Skipping directly to process order for simplicity without DB injection complex mapping
        # await process_order_creation(callback.message, state, callback.from_user.id, db_session=None)

@order_flow_router.message(OrderFSM.entering_address, F.text | F.location)
async def process_address(message: Message, state: FSMContext, db_session: AsyncSession, redis: Redis):
    addr = message.text
    coords = None
    if message.location:
        addr = f"Lat: {message.location.latitude}, Lon: {message.location.longitude}"
        coords = {"lat": message.location.latitude, "lon": message.location.longitude}
        
    await state.update_data(address=addr, coordinates=coords)
    
    data = await state.get_data()
    payment_method = data.get("payment_method")
    
    # Normally we do geocoding and intersection with polygons here.
    # For now, MVP assumes it's accepted.
    
    if payment_method == "pay_online":
        from src.presentation.handlers.client.payments import send_invoice
        await message.answer("Адрес принят. Формируем счет на оплату...", reply_markup=ReplyKeyboardRemove())
        await send_invoice(message.from_user.id, message.chat.id, message.bot, state, redis)
    else:
        await message.answer("Адрес принят. Оформляем заказ (оплата при получении)...", reply_markup=ReplyKeyboardRemove())
        await process_order_creation(message, state, message.from_user.id, db_session, redis)


async def process_order_creation(message: Message, state: FSMContext, user_id: int, db_session: AsyncSession, redis: Redis):
    data = await state.get_data()
    mode = data.get("delivery_mode", "delivery")
    address = data.get("address")
    coords = data.get("coordinates")
    rest_id = data.get("restaurant_id")
    if rest_id == 0 or not rest_id:
        rest_id = None
    
    cart_session = CartSession(redis, user_id)
    cart = await cart_session.get_cart()
    total_amount = await cart_session.get_total_amount()
    
    if not cart:
         await message.answer("Корзина пуста.")
         return
         
    delivery_type = DeliveryType.DELIVERY if mode == "delivery" else DeliveryType.PICKUP
    
    order_repo = OrderRepository(db_session)
    order = await order_repo.create(
        user_id=user_id,
        restaurant_id=rest_id,
        delivery_type=delivery_type,
        payment_method=PaymentMethod.CASH, # Defaulting for now
        total_amount=total_amount,
        delivery_address=address,
        coordinates=coords
    )
    
    # Note: realistically we should insert OrderItems here as well. Let's do a basic one.
    from src.domain.entities.order import OrderItem
    from src.infrastructure.repositories.order import OrderItemRepository
    
    item_repo = OrderItemRepository(db_session)
    for item_id_str, item_data in cart.items():
        await item_repo.create(
            order_id=order.id,
            menu_item_id=int(item_id_str),
            quantity=item_data["quantity"],
            unit_price=item_data["price"]
        )
        
    await db_session.commit()
    
    # Clear cart
    await cart_session.clear_cart()
    
    await state.clear()
    await message.answer(f"🎉 Ваш заказ #{order.id} успешно оформлен!\nОжидайте подтверждения.")
    # Here we should notify the Cashier channel/group
