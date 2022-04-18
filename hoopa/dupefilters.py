# encoding: utf-8
"""
去重器
"""

from hoopa.utils.connection import get_aio_redis


class BaseDupeFilter:
    async def get(self, fp):
        pass

    async def add(self, fp):
        pass

    async def clean_queue(self):
        pass

    async def close(self):
        pass


class MemoryDupeFilter(BaseDupeFilter):
    """
    基于内存去重
    """
    def __init__(self, *args, **kwargs):
        self.pool = set()

    async def get(self, fp):
        result = fp in self.pool
        return result is False

    async def add(self, fp):
        self.pool.add(fp)


class RedisDupeFilter(BaseDupeFilter):
    """
    redis去重，pika，tendis等兼容redis的数据库
    """

    def __init__(self, dupefilter_setting, key, engine):
        self.pool = None
        self.dupefilter_setting = dupefilter_setting
        self.key = key
        self.engine = engine

    @classmethod
    async def create(cls, engine):
        dupefilter_setting = engine.setting["DUPEFILTER_SETTING"]
        key = f"{engine.setting['NAME']}:DupeFilter"
        return cls(dupefilter_setting, key, engine)

    async def init(self):
        self.pool = await get_aio_redis(self.dupefilter_setting)

    async def get(self, fp):
        with await self.pool as conn:
            is_member = await conn.sismember(self.key, fp)
            return is_member == 0

    async def add(self, fp):
        with await self.pool as conn:
            added = await conn.sadd(self.key, fp)
            return added == 0

    async def clean_queue(self):
        with await self.pool as conn:
            return await conn.delete(self.key)

    async def close(self):
        self.pool.close()
