from src.presentation.handlers.staff.cashier import cashier_router
from src.presentation.handlers.staff.chef import chef_router
from src.presentation.handlers.staff.courier import courier_router
from src.presentation.handlers.staff.admin import admin_router
from src.presentation.handlers.staff.superadmin import superadmin_router
from aiogram import Router

staff_main_router = Router()
staff_main_router.include_router(cashier_router)
staff_main_router.include_router(chef_router)
staff_main_router.include_router(courier_router)
staff_main_router.include_router(admin_router)
staff_main_router.include_router(superadmin_router)

__all__ = ["staff_main_router"]
