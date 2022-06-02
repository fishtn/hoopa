#!/usr/bin/env python
from collections import deque, defaultdict

from hoopa.utils.concurrency import run_function
from hoopa.utils.helpers import create_instance_and_init


class MiddlewareManager:
    """中间件管理类"""

    def __init__(self,  middlewares, engine=None):
        self.engine = engine

        # 存放中间件队列的字典
        self.methods = defaultdict(deque)
        # 存放中间件名称队列的字典
        self.names = defaultdict(deque)

        for mw in middlewares:
            self._add_middleware(mw)

    @classmethod
    async def create(cls, engine):
        mw_list = cls._get_mw_list_from_engine(engine)

        middlewares = []
        for mw_cls in mw_list:
            mw = await create_instance_and_init(mw_cls, engine)
            middlewares.append(mw)

        return cls(middlewares, engine)

    @classmethod
    def _get_mw_list_from_engine(cls, setting):
        raise NotImplementedError

    def _add_middleware(self, mw):
        """
        add init and close
        @param mw: middleware
        @return:
        """
        if hasattr(mw, "init") and callable(getattr(mw, "init")):
            self.methods["init"].appendleft(mw.init)

        if hasattr(mw, "close") and callable(getattr(mw, "close")):
            self.methods["close"].appendleft(mw.close)

    async def _process_chain(self, method_name, obj, *args):
        for method in self.methods[method_name]:
            await run_function(method, obj, *args)

    async def init(self):
        await self._process_chain("init", self.engine.spider)

    async def close(self):
        await self._process_chain("close", self.engine.spider)
