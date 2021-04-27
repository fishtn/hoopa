# -*- coding: utf-8 -*-
"""
装饰器
"""

import asyncio
from asyncio import iscoroutinefunction
from functools import wraps

from loguru import logger
import traceback

from .concurrency import run_function
from .helpers import spider_sleep
from .url import get_location_from_history
from ..request import Request
from ..response import Response


def http_decorator(func):
    @wraps(func)
    async def log(http_ins, request: Request):
        response: Response = Response()
        try:
            if iscoroutinefunction(func):
                response = await func(http_ins, request)
            else:
                response = func(http_ins, request)
            return response
        except Exception as e:
            response.ok = 0
            response.error_type = e.__class__.__name__
            response.debug_msg = traceback.format_exc()
            logger.error(f"{request} fetch error \n {response.debug_msg}")

        if response.ok == 1:
            if response.history:
                last_url = get_location_from_history(response.history)
                logger.debug(f"{request} redirect <{last_url}> success")
            else:
                logger.debug(f"{request} fetch {response}")

        return response

    return log


def handle_download_callback_retry():
    def retry(func):
        @wraps(func)
        async def wrapper(self, request: Request):
            while True:
                response = await func(self, request)

                # 成功返回response
                if response.ok == 1:
                    return response

                # 重试次数等于0
                if request.retry_times == 0:
                    logger.error(f"{request} too many error, try {request.retry_times} times")
                    response.ok = -1

                # 调用retry_func方法
                retry_func = request.request_config.get("RETRY_FUNC")
                if retry_func and iscoroutinefunction(retry_func):
                    await run_function(retry_func, request, response)

                # 当ok == -1的时候，直接返回
                if response.ok == -1:
                    return response

                # 重试次数减1
                request.retry_times -= 1
                # 统计重试次数
                await self.stats.inc_value(f"requests/retry_times/{response.error_type}", 1)

                # 休眠
                if request.request_config.get("RETRY_DELAY", 0) > 0:
                    await spider_sleep(request.request_config["RETRY_DELAY"])

        return wrapper

    return retry


def timeout_it(timeout=600):
    def __timeout_it(func):
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
