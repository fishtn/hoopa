# -*- coding: utf-8 -*-
"""
装饰器
"""

import asyncio
from functools import wraps

from loguru import logger

from .helpers import spider_sleep
from ..request import Request


def handle_download_callback_retry():
    def retry(func):
        @wraps(func)
        async def wrapper(self, request: Request):
            _retry = 0
            try:
                while True:
                    response = await func(self, request)

                    # 成功返回response
                    if response.ok == 1:
                        return response

                    # 重试次数大于等于最大重试次数
                    if request.retries >= request.retry_times:
                        logger.error(f"{request} too many error, try {request.retries} times")
                        response.ok = -1

                    # 当ok == -1的时候，直接返回
                    if response.ok == -1:
                        return response

                    # 重试次数加1
                    request.retries += 1

                    if request.retries == 1:
                        self.retrying += 1
                        _retry = 1

                    # 统计重试次数
                    stats_name = response.error.name if response.error else response.status
                    await self.stats.inc_value(f"requests/retries/{stats_name}", 1)

                    # 休眠
                    # logger.error(f"request.retry_delay {request.retry_delay}")
                    await asyncio.sleep(request.retry_delay)
            finally:
                self.retrying -= _retry

        return wrapper

    return retry


def timeout_it(timeout=600):
    def __timeout_it(func):
        @wraps(func)
        async def wrapper(self, request: Request):
            try:
                await asyncio.wait_for(func(self, request), timeout)
            except asyncio.TimeoutError:
                logger.error(f"task timeout: {request}")
            except Exception as e:
                logger.error(f"error {request}\n: {e}")

        return wrapper
    return __timeout_it
