from redis.asyncio import Redis

SYSTEM_STATE_KEY = 'leadmon:system:running'


class SystemStateStore:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def set_running(self, running: bool) -> None:
        await self.redis.set(SYSTEM_STATE_KEY, '1' if running else '0')

    async def is_running(self) -> bool:
        value = await self.redis.get(SYSTEM_STATE_KEY)
        if value is None:
            return True
        return value == '1'
