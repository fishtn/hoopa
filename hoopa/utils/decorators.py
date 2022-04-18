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

                # 重试次数减1
                request.retries += 1
                # 统计重试次数
                await self.stats.inc_value(f"requests/retries/{response.error.name}", 1)

                # 休眠
                if request.retry_delay:
                    await spider_sleep(request.retry_delay)
                else:
                    await spider_sleep(self.setting["DOWNLOAD_DELAY"])


        return wrapper

    return retry


def timeout_it(timeout=600):
    def __timeout_it(func):
        @wraps(func)
        async def wrapper(self, request: Request, task_id):
            try:
                await asyncio.wait_for(func(self, request, task_id), timeout)
            except asyncio.TimeoutError:
                logger.error(f"task timeout: {task_id} {self.task_dict[task_id]}")
            except Exception as e:
                logger.error(f"{task_id}: {e}")
            finally:
                self.task_dict.pop(task_id)
        return wrapper
    return __timeout_it
