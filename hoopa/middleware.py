#!/usr/bin/env python
import traceback
from collections import deque

from loguru import logger

from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.asynciter import AsyncIter
from hoopa.utils.concurrency import run_function, run_function_no_concurrency


class Middleware:
    """中间件管理类"""

    def __init__(self):
        # request middleware
        self.request_middleware = deque()
        # response middleware
        self.response_middleware = deque()
        # close method
        self.close_method = deque()

        # 存放中间件类
        self.request_middleware_cls = deque()
        self.response_middleware_cls = deque()

    async def init(self, setting):
        middleware_cls_list = []
        # 先加载project级别的中间件，如果不存在就加载默认的
        project_middlewares = setting.get("MIDDLEWARES", "project")
        if project_middlewares and isinstance(project_middlewares, list):
            middleware_cls_list.extend(project_middlewares)
        else:
            default_middlewares = setting.get("MIDDLEWARES", "default")
            middleware_cls_list.extend(default_middlewares)

        # 加载spider里面的中间件
        spider_middlewares = setting["MIDDLEWARES"],
        if spider_middlewares and isinstance(spider_middlewares, list):
            middleware_cls_list.extend(spider_middlewares)

        middlewares = []

        for mw_cls in middleware_cls_list:
            mw = mw_cls()
            if hasattr(mw, "init") and callable(getattr(mw, "init")):
                await run_function_no_concurrency(mw.init)
            middlewares.append(mw)

        self._load_middleware(middlewares)

        return self

    def _load_middleware(self, middlewares):
        for mw in middlewares:
            if hasattr(mw, "process_request") and callable(getattr(mw, "process_request")):
                self.request_middleware.append(mw.process_request)
                self.request_middleware_cls.append(mw.__class__.__name__)

            if hasattr(mw, "process_response") and callable(getattr(mw, "process_response")):
                self.response_middleware.appendleft(mw.process_response)
                self.response_middleware_cls.appendleft(mw.__class__.__name__)

            if hasattr(mw, "close") and callable(getattr(mw, "close")):
                self.close_method.appendleft(mw.close)

    async def download(self, download_func, request, spider_ins):
        # 加载request中间件, 并调用下载器
        response = await self.process_request(download_func, request, spider_ins)

        # 加载response中间件
        process_response_result = await self.process_response(request, response, spider_ins)

        if process_response_result:
            return process_response_result

        return response

    async def process_request(self, download_func, request: Request, spider_ins):
        for middleware in self.request_middleware:
            try:
                response = await run_function(middleware, request, spider_ins)
                if response is not None and not isinstance(response, (Response, Request)):
                    raise Exception(f"<Middleware {middleware.__name__}: must return None, Response or Request")
                if response:
                    return AsyncIter([response])
            except Exception as e:
                logger.error(f"<Middleware {middleware.__name__}: {e} \n{traceback.format_exc()}>")

        # 执行完request_middleware，调用下载器
        return await run_function(download_func, request)

    async def process_response(self, request: Request, response: Response, spider_ins):
        # 如果response是request，返回异步生成器
        if isinstance(response, Request):
            return AsyncIter([response])

        for middleware in self.response_middleware:
            try:
                middleware_response = await run_function(middleware, request, response, spider_ins)
                if middleware_response is not None and not isinstance(middleware_response, (Response, Request)):
                    raise Exception(f"<Middleware {middleware.__name__}: must return None, Response or Request")
                if isinstance(middleware_response, Request):
                    return AsyncIter([middleware_response])
                if isinstance(middleware_response, Response):
                    response = middleware_response
                    break
            except Exception as e:
                logger.error(f"<Middleware {middleware.__name__}: {e} \n{traceback.format_exc()}>")

        return response

    async def close(self):
        for func in self.close_method:
            await run_function_no_concurrency(func)
