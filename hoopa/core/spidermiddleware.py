#!/usr/bin/env python
import traceback

from hoopa.item import Item
from hoopa.exceptions import Error, InvalidOutput
from hoopa.middleware import MiddlewareManager
from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.concurrency import run_function


class SpiderMiddleware(MiddlewareManager):
    """爬虫中间件"""

    @classmethod
    def _get_mw_list_from_engine(cls, engine):
        return engine.setting.get("SPIDER_MIDDLEWARES") + engine.setting.get("SPIDER_MIDDLEWARES_BASE")

    def _add_middleware(self, mw):
        super()._add_middleware(mw)
        if hasattr(mw, "process_request") and callable(getattr(mw, "process_request")):
            self.methods["process_request"].append(mw.process_request)
            self.names["process_request"].append(mw.__class__.__name__)

        if hasattr(mw, "process_response") and callable(getattr(mw, "process_response")):
            self.methods["process_response"].appendleft(mw.process_response)
            self.names["process_response"].appendleft(mw.__class__.__name__)

        if hasattr(mw, "process_exception") and callable(getattr(mw, "process_exception")):
            self.methods["process_exception"].appendleft(mw.process_exception)
            self.names["process_exception"].appendleft(mw.__class__.__name__)

    async def process_input(self, request: Request, response: Response, spider_ins):
        for method in self.methods["process_request"]:
            middleware_response = await run_function(method, request, response, spider_ins)
            if response is not None and not isinstance(middleware_response, bool):
                raise Exception(f"<Middleware {method.__name__}: must return None, got {type(response)}")

            if middleware_response:
                return

    async def process_output(self, request: Request, response: Response, result, spider_ins):
        for method in self.methods["process_response"]:
            middleware_response = await run_function(method, request, response, result, spider_ins)
            if middleware_response is not None and not isinstance(middleware_response, (Response, Request)):
                raise InvalidOutput(f"<Middleware {method.__name__}: must return None, Request or Item, "
                                    f"got {type(response)}")

            if isinstance(middleware_response, (Request, Item)):
                return middleware_response

        return result

    async def process_exception(self, request, response, error, spider_ins):
        for method in self.methods['process_exception']:
            middleware_response = await run_function(method, request, response, error, spider_ins)
            if middleware_response is not None and not isinstance(middleware_response, bool):
                raise InvalidOutput(
                    f"Middleware {method.__self__.__class__.__name__}"
                    ".process_exception must return None or "
                    f"bool, got {type(middleware_response)}"
                )
            if middleware_response:
                return
        raise error.exception

    async def scrape_response(self, parse_func, request, response, spider_ins):
        # 调用中间件
        await self.process_input(request, response, spider_ins)

        try:
            results = await run_function(parse_func, request, response)

            if results:
                # 加载response中间件
                process_response_results = []
                for result in results:
                    process_response_result = await self.process_output(request, response, result, spider_ins)
                    process_response_results.append(process_response_result)

                return iter(process_response_results)

        except Exception as e:
            await self.process_exception(request, response, Error(e, traceback.format_exc()), spider_ins)

