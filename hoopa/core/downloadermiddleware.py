#!/usr/bin/env python
import traceback

from hoopa.exceptions import Error, InvalidOutput
from hoopa.middleware import MiddlewareManager
from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.asynciter import AsyncIter
from hoopa.utils.concurrency import run_function


class DownloaderMiddleware(MiddlewareManager):
    """下载中间件"""

    @classmethod
    def _get_mw_list_from_engine(cls, engine):
        return engine.setting.get("DOWNLOADER_MIDDLEWARES") + engine.setting.get("DOWNLOADER_MIDDLEWARES_BASE")

    def _add_middleware(self, mw):
        super()._add_middleware(mw)
        if hasattr(mw, "process_request") and callable(getattr(mw, "process_request")):
            self.methods["process_request"].append(mw.process_request)
            self.names["process_request"].append(mw.__class__.__name__)

        if hasattr(mw, "process_response") and callable(getattr(mw, "process_response")):
            self.methods["process_response"].append(mw.process_response)
            self.names["process_response"].append(mw.__class__.__name__)

        if hasattr(mw, "process_exception") and callable(getattr(mw, "process_exception")):
            self.methods["process_exception"].append(mw.process_exception)
            self.names["process_exception"].append(mw.__class__.__name__)

    async def process_request(self, request: Request, spider_ins):
        methods = [spider_ins.process_request] + list(self.methods["process_request"])
        for method in methods:
            # 主要是为了处理spider里面的process_item参数的不同
            if method.__code__.co_argcount == 2:
                response = await run_function(method, request)
            else:
                response = await run_function(method, request, spider_ins)

            if response is not None and not isinstance(response, (Response, Request)):
                raise InvalidOutput(f"<Middleware {method.__name__}: must return None, Response or Request")
            if response:
                return response

    async def process_response(self, request: Request, response: Response, spider_ins):
        # 如果response是request，返回异步生成器
        if isinstance(response, Request):
            return AsyncIter([response])

        for method in self.methods["process_response"]:
            middleware_response = await run_function(method, request, response, spider_ins)
            if middleware_response is not None and not isinstance(middleware_response, (Response, Request)):
                raise InvalidOutput(f"<Middleware {method.__name__}: must return None, Response or Request")
            if isinstance(middleware_response, Request):
                return AsyncIter([middleware_response])
            if isinstance(middleware_response, Response):
                response = middleware_response
                break

        return response

    async def process_exception(self, request, exception, spider_ins):
        for method in self.methods['process_exception']:
            middleware_response = await run_function(method, request, exception, spider_ins)
            if middleware_response is not None and not isinstance(middleware_response, (Response, Request)):
                raise InvalidOutput(
                    f"Middleware {method.__self__.__class__.__name__}"
                    ".process_exception must return None, Response or "
                    f"Request, got {type(middleware_response)}"
                )
            if middleware_response:
                return middleware_response
        raise exception

    async def download(self, download_func, request, spider_ins):
        # 加载request中间件, 并调用下载器
        response = await self.process_request(request, spider_ins)

        # 没有response，调用下载器
        if not response:
            # 执行完request_middleware，调用下载器
            try:
                response = await run_function(download_func, request)
            except Exception as e:
                return await self.process_exception(request, Error(e, traceback.format_exc()), spider_ins)

        if response:
            # 加载response中间件
            process_response_result = await self.process_response(request, response, spider_ins)

            if process_response_result:
                return process_response_result

        return response
