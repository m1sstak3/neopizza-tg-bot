from enum import Enum
from datetime import datetime
from sqlalchemy import BigInteger, String, ForeignKey, Integer, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM
from src.domain.entities.base import Base, TimestampMixin

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COOKING = "cooking"
    READY = "ready"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    ONLINE = "online"
    CASH = "cash"
    CARD_COURIER = "card_courier"

class DeliveryType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="SET NULL"), nullable=True)
    courier_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True, index=True)
    
    status: Mapped[OrderStatus] = mapped_column(
        ENUM(OrderStatus, name="order_status_enum", create_type=False),
        nullable=False,
        default=OrderStatus.PENDING
    )
    
    delivery_type: Mapped[DeliveryType] = mapped_column(
        ENUM(DeliveryType, name="delivery_type_enum", create_type=False),
        nullable=False,
        default=DeliveryType.DELIVERY
    )
    
    payment_method: Mapped[PaymentMethod] = mapped_column(
        ENUM(PaymentMethod, name="payment_method_enum", create_type=False),
        nullable=False
    )
    payment_status: Mapped[bool] = mapped_column(default=False)
    
    total_amount: Mapped[int] = mapped_column(nullable=False, comment="Total cost including delivery")
    delivery_cost: Mapped[int] = mapped_column(default=0)
    
    delivery_address: Mapped[str] = mapped_column(String(255), nullable=True)
    coordinates: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # True if the user ordered for a specific future time.
    is_preorder: Mapped[bool] = mapped_column(default=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Store relation to items
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True)
    
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[int] = mapped_column(nullable=False, comment="Price at the time of order")
    note: Mapped[str] = mapped_column(Text, nullable=True)
    
    order: Mapped["Order"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship()
