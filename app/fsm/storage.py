"""
FSM storage — Redis recommended for production; MemoryStorage for dev.
"""

from aiogram.fsm.storage.memory import MemoryStorage

# For production with multiple instances, use RedisStorage:
# from aiogram.fsm.storage.redis import RedisStorage
# redis = redis.asyncio.from_url("redis://localhost")
# storage = RedisStorage(redis=redis)

storage = MemoryStorage()
