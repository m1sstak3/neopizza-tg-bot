from src.presentation.handlers.client.start import client_router
from src.presentation.handlers.client.order_flow import order_flow_router

# The following modules attach their handlers to order_flow_router directly.
# We import them to trigger the decorator side-effects.
import src.presentation.handlers.client.menu_catalog
import src.presentation.handlers.client.cart_view
import src.presentation.handlers.client.checkout
import src.presentation.handlers.client.payments

from aiogram import Router

# Gather all client routers
client_main_router = Router()
client_main_router.include_router(client_router)
client_main_router.include_router(order_flow_router)

__all__ = ["client_main_router"]
