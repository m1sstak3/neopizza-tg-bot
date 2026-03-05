from aiogram import F, Bot
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from src.presentation.handlers.client.checkout import order_flow_router
from src.domain.entities.order import PaymentMethod
from src.presentation.fsm.order import OrderFSM
from aiogram.fsm.context import FSMContext
from src.config import config
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.cache.cart import CartSession
from redis.asyncio import Redis

@order_flow_router.message(OrderFSM.choosing_pickup_time)
async def process_pickup_time(message: Message, state: FSMContext, bot: Bot, db_session: AsyncSession, redis: Redis):
    # Simply save time and proceed to process
    await state.update_data(pickup_time=message.text)
    
    data = await state.get_data()
    payment_method = data.get("payment_method")
    
    if payment_method == "pay_online":
        await send_invoice(message.from_user.id, message.chat.id, bot, state, redis)
    else:
        from src.presentation.handlers.client.checkout import process_order_creation
        from aiogram.types import ReplyKeyboardRemove
        await message.answer("Способ оплаты: Наличными/Картой при получении. Оформляем заказ...", reply_markup=ReplyKeyboardRemove())
        await process_order_creation(message, state, message.from_user.id, db_session, redis)


async def send_invoice(user_id: int, chat_id: int, bot: Bot, state: FSMContext, redis: Redis):
    if not config.PAYMENT_PROVIDER_TOKEN or config.PAYMENT_PROVIDER_TOKEN == "PROVIDER_TOKEN":
        await bot.send_message(chat_id, "⚠️ Оплата онлайн временно недоступна (не настроен токен банка). Пожалуйста, оформите заказ заново с оплатой при получении.")
        # Optionally clear state or revert
        return
        
    cart_session = CartSession(redis, user_id)
    cart = await cart_session.get_cart()
    total = await cart_session.get_total_amount()
    
    # Telegram Payments expects prices in minimal units (e.g. kopecks for RUB)
    prices = [LabeledPrice(label="Заказ NeoPizza", amount=total * 100)]
    
    await bot.send_invoice(
        chat_id=chat_id,
        title="Оплата заказа NeoPizza",
        description=f"Оплата заказа на сумму {total}₽",
        payload="neopizza_order_payload",
        provider_token=config.PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        need_name=True,
        need_phone_number=True,
    )

@order_flow_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@order_flow_router.message(F.successful_payment)
async def successful_payment_handler(message: Message, state: FSMContext, db_session: AsyncSession, redis: Redis):
    payment_info = message.successful_payment
    
    # Mark state/payment_method explicitly online, then create order
    await state.update_data(payment_method="pay_online")
    
    from src.presentation.handlers.client.checkout import process_order_creation
    await message.answer(f"✅ Оплата прошла успешно! Провайдер: {payment_info.provider_payment_charge_id}")
    await process_order_creation(message, state, message.from_user.id, db_session, redis)
