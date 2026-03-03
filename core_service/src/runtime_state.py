from redis.asyncio import Redis

SYSTEM_STATE_KEY = 'leadmon:system:running'


class RuntimeState:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def is_running(self) -> bool:
        value = await self.redis.get(SYSTEM_STATE_KEY)
        if value is None:
            return True
        return value == '1'
