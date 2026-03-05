import asyncio
import structlog
from src.application.tasks.celery_app import celery_app
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import config
from src.infrastructure.repositories.order import OrderRepository
from src.domain.entities.order import OrderStatus

logger = structlog.get_logger(__name__)

# Engine used by Celery tasks
engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

def run_async(coro):
    """Helper to run async code inside Celery sync worker."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@celery_app.task(name="calculate_dynamic_eta")
def calculate_dynamic_eta(order_id: int):
    """
    Calculates ETA based on current load and distance.
    This is called when Order is created.
    """
    async def _calc():
        async with AsyncSessionLocal() as session:
            repo = OrderRepository(session)
            order = await repo.get_by_id(order_id)
            if not order:
                return
                
            # Dummy logic: 15 mins base + 5 mins per active order in DB
            result = await session.execute(
                repo._model_class.__table__.select().where(
                    repo._model_class.status.in_([OrderStatus.PENDING, OrderStatus.COOKING])
                )
            )
            active_count = len(result.fetchall())
            
            eta_minutes = 15 + (active_count * 5)
            logger.info("ETA Calculated", order_id=order_id, eta_minutes=eta_minutes)
            # You could update the order or notify user here
            
    run_async(_calc())
    return True


@celery_app.task(name="auto_assign_courier")
def auto_assign_courier(order_id: int):
    """
    Called periodically or delayed. Auto assigns free couriers if manual pickup delays.
    """
    async def _assign():
        async with AsyncSessionLocal() as session:
            repo = OrderRepository(session)
            order = await repo.get_by_id(order_id)
            if order and order.status == OrderStatus.READY and not order.courier_id:
                logger.info("Auto assigning courier to order", order_id=order_id)
                # Fetch free couriers, assign, notify
    run_async(_assign())
    return True
