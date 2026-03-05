import asyncio
import os
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from redis.asyncio import Redis

from src.config import config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.presentation.middlewares import setup_middlewares

logger = structlog.get_logger(__name__)

async def setup_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Try using Redis storage if accessible, otherwise fallback to memory.
    try:
        redis_conn = Redis.from_url(config.REDIS_URL, decode_responses=True)
        # Simply verifying the connection details internally
        storage = RedisStorage(redis=redis_conn)
        logger.info("Using Redis state storage")
    except Exception as e:
        logger.warning("Redis not available, falling back to MemoryStorage", error=str(e))
        storage = MemoryStorage()
        redis_conn = None

    dp = Dispatcher(storage=storage)
    dp["redis"] = redis_conn
    
    # Setup DB Pool
    engine = create_async_engine(config.DATABASE_URL, echo=False)
    session_pool = async_sessionmaker(engine, expire_on_commit=False)
    
    # Setup Middlewares
    setup_middlewares(dp, session_pool)
    
    from src.presentation.handlers.client import client_main_router
    from src.presentation.handlers.staff import staff_main_router
    
    dp.include_router(client_main_router)
    dp.include_router(staff_main_router)
    
    return bot, dp

async def main():
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    logger.info("Starting NeoPizza Bot Initialization...", bot="running")
    
    bot, dp = await setup_bot()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        if dp["redis"]:
            await dp["redis"].aclose()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot successfully stopped.")
