"""
collecting spider stats
"""

from hoopa.utils.connection import get_aio_redis


class StatsCollector:

    def __init__(self):
        self._stats = {}

    async def get_value(self, key, default=None, spider=None):
        return self._stats.get(key, default)

    async def get_stats(self, spider=None):
        return self._stats

    async def set_value(self, key, value, spider=None):
        self._stats[key] = value

    async def set_stats(self, stats, spider=None):
        self._stats = stats

    async def inc_value(self, key, count=1, start=0, spider=None):
        d = self._stats
        d[key] = d.setdefault(key, start) + count

    async def max_value(self, key, value, spider=None):
        self._stats[key] = max(self._stats.setdefault(key, value), value)

    async def min_value(self, key, value, spider=None):
        self._stats[key] = min(self._stats.setdefault(key, value), value)

    async def close(self):
        pass


class MemoryStatsCollector(StatsCollector):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.spider_stats = {}


class DummyStatsCollector(StatsCollector):

    def get_value(self, key, default=None, spider=None):
        return default

    def set_value(self, key, value, spider=None):
        pass

    def set_stats(self, stats, spider=None):
        pass

    def inc_value(self, key, count=1, start=0, spider=None):
        pass

    def max_value(self, key, value, spider=None):
        pass

    def min_value(self, key, value, spider=None):
        pass


class RedisStatsCollector(StatsCollector):
    """
    Stats Collector based on Redis
    """
    pool = None
    stats_key = None

    def __init__(self, redis_setting, stats_key, engine):
        super().__init__()
        self.redis_setting = redis_setting
        self.stats_key = stats_key
        self.engine = engine

    @classmethod
    async def create(cls, engine):
        redis_setting = engine.setting["REDIS_SETTING"]
        stats_key = f"{engine.setting['NAME']}:Stats"

        return cls(redis_setting, stats_key, engine)

    async def init(self):
        self.pool = await get_aio_redis(self.redis_setting)

    async def get_value(self, key, default=None, spider=None):
        """Return the value of hash stats"""
        with await self.pool as conn:
            if await conn.hexists(self.stats_key, key):
                return int(await conn.hget(self.stats_key, key))
            else:
                return default

    async def get_stats(self, spider=None):
        """Return the all of the values of hash stats"""
        with await self.pool as conn:
            return await conn.hgetall(self.stats_key)

    async def set_value(self, key, value, spider=None):
        """Set the value according to hash key of stats"""
        with await self.pool as conn:
            return await conn.hset(self.stats_key, key, value)

    async def set_stats(self, stats, spider=None):
        """Set all the hash stats"""
        with await self.pool as conn:
            await conn.hmset(self.stats_key, stats)

    async def inc_value(self, key, count=1, start=0, spider=None):
        """Set increment of value according to key"""
        with await self.pool as conn:
            if not await conn.hexists(self.stats_key, key):
                await self.set_value(key, start)
            await conn.hincrby(self.stats_key, key, count)

    async def max_value(self, key, value, spider=None):
        """Set max value between current and new value"""
        await self.set_value(key, max(await self.get_value(key, value), value))

    async def min_value(self, key, value, spider=None):
        """Set min value between current and new value"""
        await self.set_value(key, min(await self.get_value(key, value), value))

    async def close(self):
        self.pool.close()
