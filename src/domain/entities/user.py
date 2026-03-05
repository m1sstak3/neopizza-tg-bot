from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM
from src.domain.entities.base import Base, TimestampMixin

class RoleEnum(str, Enum):
    CLIENT = "client"
    CASHIER = "cashier"
    CHEF = "chef"
    COURIER = "courier"
    ACCOUNTANT = "accountant"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    role: Mapped[RoleEnum] = mapped_column(
        ENUM(RoleEnum, name="role_enum", create_type=False),
        nullable=False,
        default=RoleEnum.CLIENT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    violations_count: Mapped[int] = mapped_column(default=0)
    
    # Store privacy policy acceptance timestamp
    privacy_accepted_at: Mapped[str] = mapped_column(String, nullable=True)
