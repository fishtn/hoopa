# encoding: utf-8
"""
调度器
"""

import time
import typing

from loguru import logger
from w3lib.url import is_url

from hoopa.exceptions import InvalidUrl
from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.helpers import get_timestamp, get_cls


class Scheduler:
    """
    调度器
    """
    def __init__(self):
        self.setting = None

        self.scheduler_queue = None
        self.dupefilter = None
        self.stats = None

        self._last_check_status_time = time.time()

    async def init(self, setting):
        self.setting = setting
        # 初始化dupefilter
        self.dupefilter = await get_cls(setting["DUPEFILTER_CLS"], setting=setting)
        self.scheduler_queue = await get_cls(setting["QUEUE_CLS"], setting=setting)
        self.stats = await get_cls(self.setting["STATS_CLS"], setting=self.setting)

        # 删除队列
        if setting["CLEAN_QUEUE"]:
            # 获取相关的key
            await self.scheduler_queue.clean_queue()

        # 删除去重队列
        if setting["CLEAN_DUPEFILTER"]:
            # 获取相关的key
            await self.dupefilter.clean_queue()

        # 初始化爬虫开始时间
        await self.stats.min_value("start_time", int(get_timestamp()))

        return self

    async def get(self, priority=None):
        """
        从队列中获取一个 request
        @param priority: 权重，取出对应权重的request，当队列为redis时生效
        """
        if priority and not isinstance(priority, (int, list)):
            raise TypeError(f"queue_priority must be int or list, not {type(priority)}")

        request = await self.scheduler_queue.get(priority)

        if request:
            await self.stats.inc_value('queue/request_count', 1)
            logger.debug(f"get request {request}")
        return request

    async def add(self, requests: typing.Union[Request, typing.List[Request]]):
        """
        向队列添加多个request
        @param requests:
        """
        if not isinstance(requests, list):
            requests = [requests]

        # 判断url是否合法
        for item in requests:
            if item is None:
                raise InvalidUrl(f"Invalid url: {item} url is None ")
            if not is_url(item.url):
                raise InvalidUrl(f"Invalid url: {item.url} ")

        # 去重
        request_list = []
        for request in requests:
            if request.dont_filter or await self.dupefilter.get(request.fp):
                request_list.append(request)

        #  去重后为空
        if not request_list:
            return 0

        # 放进队列
        set_len = await self.scheduler_queue.add(request_list)

        # 把放进队列的request去重
        for request in requests:
            if not request.dont_filter:
                await self.dupefilter.add(request.fp)

        return set_len

    async def set_result(self, request: Request, response: Response, task_request: Request):
        """
        保存结果
        @param request:
        @param response:
        @param task_request: 爬虫请求过程中的request
        """
        await self.scheduler_queue.set_result(request, response, task_request)

        if response.ok == 1:
            logger.debug(f"{request} result: success, status: {response.status}")
        else:
            logger.error(f"{request} result: failure, status: {response.status}")

        # 统计信息
        await self.stats.inc_value(f"queue/response_count", 1)
        await self.stats.inc_value(f'queue/response_count/priority_{request.priority}/{response.ok}', 1)

    async def check_scheduler(self, spider_ins):
        await self.scheduler_queue.check_status(spider_ins, self.setting["RUN_FOREVER"])

    async def close(self):
        await self.dupefilter.close()
        await self.scheduler_queue.close()
        await self.stats.close()
