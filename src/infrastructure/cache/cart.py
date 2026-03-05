import json
from typing import Dict, Any
from redis.asyncio import Redis

class CartSession:
    """
    Manages the user's shopping cart in Redis.
    Structure: cart:{telegram_id} -> hash map 
               field: item_id, value: {quantity, price, note}
    """
    def __init__(self, redis: Redis, telegram_id: int):
        self.redis = redis
        self.cart_key = f"cart:{telegram_id}"
        
    async def add_item(self, menu_item_id: int, price: int, quantity: int = 1, note: str = ""):
        # Check if already exists to increment quantity
        existing = await self.redis.hget(self.cart_key, str(menu_item_id))
        if existing:
            data = json.loads(existing)
            data["quantity"] += quantity
            if note:
                data["note"] = data.get("note", "") + " | " + note
            await self.redis.hset(self.cart_key, str(menu_item_id), json.dumps(data))
        else:
            data = {
                "quantity": quantity,
                "price": price,
                "note": note
            }
            await self.redis.hset(self.cart_key, str(menu_item_id), json.dumps(data))
            
        # Expire cart after 24 hours of inactivity
        await self.redis.expire(self.cart_key, 86400)

    async def remove_item(self, menu_item_id: int):
        await self.redis.hdel(self.cart_key, str(menu_item_id))
        
    async def decrement_item(self, menu_item_id: int):
        existing = await self.redis.hget(self.cart_key, str(menu_item_id))
        if existing:
            data = json.loads(existing)
            if data["quantity"] > 1:
                data["quantity"] -= 1
                await self.redis.hset(self.cart_key, str(menu_item_id), json.dumps(data))
            else:
                await self.remove_item(menu_item_id)

    async def get_cart(self) -> Dict[str, dict]:
        raw = await self.redis.hgetall(self.cart_key)
        # raw is {b'1': b'{"quantity": 1, ...}'} depending on decode_responses
        return {k: json.loads(v) for k, v in raw.items()}

    async def clear_cart(self):
        await self.redis.delete(self.cart_key)
        
    async def get_total_amount(self) -> int:
        cart = await self.get_cart()
        return sum(item["price"] * item["quantity"] for item in cart.values())
