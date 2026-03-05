from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.presentation.handlers.client.order_flow import order_flow_router
from src.presentation.fsm.order import OrderFSM
from src.infrastructure.repositories.menu import CategoryRepository, MenuItemRepository
from src.infrastructure.cache.cart import CartSession
from redis.asyncio import Redis
from src.config import config

@order_flow_router.callback_query(F.data.startswith("rest_"))
async def select_restaurant(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    rest_id = int(callback.data.split("_")[1])
    await state.update_data(restaurant_id=rest_id)
    await state.set_state(OrderFSM.browsing_menu)
    
    # Show main categories
    repo = CategoryRepository(db_session)
    categories = await repo.get_active_categories()
    
    if not categories:
        await callback.answer("⏳ Меню пока пустое.", show_alert=True)
        return

    kb_builder = []
    for c in categories:
        kb_builder.append([InlineKeyboardButton(text=c.name, callback_data=f"cat_{c.id}")])
    
    kb_builder.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")])
    kb_builder.append([InlineKeyboardButton(text="🔙 К выбору заведения", callback_data="back_to_rest")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_builder)
    await callback.message.edit_text("📜 Меню категорий", reply_markup=kb)


@order_flow_router.callback_query(F.data.startswith("cat_"))
async def show_category_items(callback: CallbackQuery, state: FSMContext, db_session: AsyncSession):
    cat_id = int(callback.data.split("_")[1])
    repo = MenuItemRepository(db_session)
    items = await repo.get_items_by_category(cat_id)
    
    if not items:
        await callback.answer("В этой категории пока нет блюд.", show_alert=True)
        return
        
    for item in items:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"➕ В корзину ({item.price}₽)", callback_data=f"add_{item.id}_{item.price}")]
        ])
        
        text = f"<b>{item.name}</b>\n\n{item.description or ''}"
        
        if item.photo_url:
            await callback.message.answer_photo(photo=item.photo_url, caption=text, reply_markup=kb)
        else:
            await callback.message.answer(text=text, reply_markup=kb)
            
    # Send bottom nav panel
    nav_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")],
        [InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="rest_0")] # Handled specially to go back
    ])
    await callback.message.answer("Выберите блюда, чтобы добавить в корзину:", reply_markup=nav_kb)


@order_flow_router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, redis: Redis):
    parts = callback.data.split("_")
    item_id = int(parts[1])
    price = int(parts[2])
    
    # Needs redis conn. We instantiate it inside or pass through middleware
    cart = CartSession(redis, callback.from_user.id)
    
    await cart.add_item(menu_item_id=item_id, price=price, quantity=1)
    await callback.answer(f"🍕 Блюдо добавлено в корзину!")
