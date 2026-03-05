from aiogram.fsm.state import StatesGroup, State

class OrderFSM(StatesGroup):
    choosing_delivery_mode = State()
    choosing_restaurant = State()
    browsing_menu = State()
    in_cart = State()
    entering_address = State() # Only for delivery
    choosing_pickup_time = State() # Only for pickup
    checkout = State()
    waiting_for_payment = State()
