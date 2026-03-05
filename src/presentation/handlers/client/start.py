from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# This router handles client interactions
client_router = Router(name="client_router")

@client_router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Entry point for clients. PrivacyGateMiddleware has already ensured they agreed to TOS.
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛵 Заказать доставку", callback_data="mode_delivery")],
        [InlineKeyboardButton(text="🚶‍♂️ Самовывоз", callback_data="mode_pickup")],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")]
    ])
    
    await message.answer(
        f"🍕 Привет, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в NeoPizza. "
        "Самая быстрая пицца формата Dark Kitchen.\n\n"
        "Выберите способ получения заказа:",
        reply_markup=kb
    )

@client_router.callback_query(F.data == "back_to_start")
async def back_to_start_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛵 Заказать доставку", callback_data="mode_delivery")],
        [InlineKeyboardButton(text="🚶‍♂️ Самовывоз", callback_data="mode_pickup")],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders")]
    ])
    await callback.message.edit_text(
        f"🍕 Привет, {callback.from_user.first_name}!\n\n"
        "Добро пожаловать в NeoPizza. Самая быстрая пицца формата Dark Kitchen.\n\n"
        "Выберите способ получения заказа:",
        reply_markup=kb
    )
