# encoding: utf-8
"""
去重器
"""

import aioredis

from hoopa.utils.connection import get_aio_redis


class BaseDupeFilter:
    async def init(self, setting):
        pass

    async def get(self, fp):
        pass

    async def add(self, fp):
        pass

    async def clean_queue(self):
        pass

    async def close(self):
        pass


class RedisDupeFilter(BaseDupeFilter):
    """
    redis去重，pika，tendis等兼容redis的数据库
    """
    def __init__(self):
        self.pool = None
        self.key = None

    async def init(self, setting):
        dupefilter_setting = setting["DUPEFILTER_SETTING"]
        self.key = f"{setting['NAME']}:DupeFilter"
        self.pool = await get_aio_redis(dupefilter_setting)

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


class MemoryDupeFilter(BaseDupeFilter):
    """
    基于内存去重
    """
    def __init__(self):
        self.pool = set()

    async def init(self, setting):
        pass

    async def get(self, request):
        result = request in self.pool
        return result is False

    async def add(self, request):
        self.pool.add(request)

    async def clean_queue(self):
        pass



