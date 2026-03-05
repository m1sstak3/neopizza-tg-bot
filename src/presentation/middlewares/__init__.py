from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from aiogram import Dispatcher
from src.presentation.middlewares.db import DbSessionMiddleware
from src.presentation.middlewares.privacy import PrivacyGateMiddleware

def setup_middlewares(dp: Dispatcher, session_pool: async_sessionmaker[AsyncSession]):
    """
    Register all middlewares for the bot dispatcher
    """
    
    # 1. Inject DB Session
    dp.update.middleware(DbSessionMiddleware(session_pool=session_pool))
    
    # 2. Privacy Gate (Check if user accepted terms)
    dp.update.middleware(PrivacyGateMiddleware())
    
    # TODO: Add RoleMiddleware 
