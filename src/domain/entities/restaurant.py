from sqlalchemy import String, Boolean, JSON, Time
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.base import Base, TimestampMixin

class Restaurant(Base, TimestampMixin):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Store lat, lon as JSON or separate floats. Using JSON for flexibility (e.g., {"lat": 55.75, "lon": 37.61})
    coordinates: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Working hours (e.g., {"open": "10:00", "close": "22:00"})
    working_hours: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Polygon data (GeoJSON format) to define delivery boundaries
    delivery_zone_polygon: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DeliveryZoneTier(Base, TimestampMixin):
    __tablename__ = "delivery_zone_tiers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Simple radius based tiers. Example: min_km=0, max_km=2
    min_km: Mapped[float] = mapped_column(nullable=False)
    max_km: Mapped[float] = mapped_column(nullable=False)
    
    price: Mapped[int] = mapped_column(nullable=False, comment="Price in RUB")
    estimated_minutes: Mapped[int] = mapped_column(nullable=False, comment="Additional time for this zone")
