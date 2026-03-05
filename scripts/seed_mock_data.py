import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import config
from src.infrastructure.db.models.restaurant import Restaurant, DeliveryZoneTier
from src.infrastructure.db.models.menu import Category, MenuItem
from sqlalchemy import select

engine = create_async_engine(config.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if restaurant exists
        result = await session.execute(select(Restaurant).limit(1))
        existing_rest = result.scalars().first()
        
        if existing_rest:
            print("Data already seeded.")
            return

        # 1. Create a Restaurant
        rest = Restaurant(
            name="NeoPizza Центральная",
            address="ул. Тверская, 1",
            coordinates={"lat": 55.7570, "lon": 37.6150},
            working_hours={"open": "10:00", "close": "23:00"},
            delivery_zone_polygon={"type": "Polygon", "coordinates": [[[37.6, 55.7], [37.7, 55.7], [37.7, 55.8], [37.6, 55.8], [37.6, 55.7]]]},
            is_active=True
        )
        session.add(rest)
        await session.flush()

        # 2. Add Delivery Tiers (no restaurant_id in your current model, but we should link it ideally.
        # However, for now, we'll just instantiate what the model accepts.)
        tier1 = DeliveryZoneTier(min_km=0.0, max_km=2.0, price=99, estimated_minutes=15)
        tier2 = DeliveryZoneTier(min_km=2.0, max_km=5.0, price=179, estimated_minutes=30)
        session.add_all([tier1, tier2])

        # 3. Create Categories
        cat_pizza = Category(name="🍕 Пицца", sort_order=1)
        cat_drinks = Category(name="🥤 Напитки", sort_order=2)
        session.add_all([cat_pizza, cat_drinks])
        await session.flush()

        # 4. Create Menu Items
        item1 = MenuItem(
            name="Пицца Пепперони",
            description="Острая пепперони, моцарелла, томатный соус (30см)",
            photo_url="https://images.unsplash.com/photo-1628840042765-356cda07504e?q=80&w=800",
            price=550.0,
            category_id=cat_pizza.id
        )
        item2 = MenuItem(
            name="Пицца Маргарита",
            description="Моцарелла, томаты, базилик (30см)",
            photo_url="https://images.unsplash.com/photo-1574071318508-1cdbab80d002?q=80&w=800",
            price=450.0,
            category_id=cat_pizza.id
        )
        item3 = MenuItem(
            name="Кола 0.5",
            description="Охлажденная газировка",
            photo_url="https://images.unsplash.com/photo-1622483767028-3f66f32aef97?q=80&w=800",
            price=120.0,
            category_id=cat_drinks.id
        )
        
        session.add_all([item1, item2, item3])
        
        await session.commit()
        print("Mock data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
