#!/usr/bin/env python
import traceback
from copy import deepcopy

from hoopa.item import Item
from hoopa.exceptions import Error, InvalidOutput
from hoopa.middleware import MiddlewareManager
from hoopa.utils.concurrency import run_function


class PipelineManager(MiddlewareManager):
    """下载中间件"""

    @classmethod
    def _get_mw_list_from_engine(cls, engine):
        return engine.setting.get("PIPELINES") + engine.setting.get("PIPELINES_BASE")

    def _add_middleware(self, mw):
        super()._add_middleware(mw)

        if hasattr(mw, "process_item") and callable(getattr(mw, "process_item")):
            self.methods["process_item"].append(mw.process_item)
            self.names["process_item"].append(mw.__class__.__name__)

        if hasattr(mw, "process_exception") and callable(getattr(mw, "process_exception")):
            self.methods["process_exception"].append(mw.process_exception)
            self.names["process_exception"].append(mw.__class__.__name__)

    async def process_item(self, item, spider_ins):
        _item = deepcopy(item)

        methods = [spider_ins.process_item] + list(self.methods["process_item"])

        for method in methods:
            # 主要是为了处理spider里面的process_item参数的不同
            if method.__code__.co_argcount == 2:
                _item = await run_function(method, _item)
            else:
                _item = await run_function(method, _item, spider_ins)

            if not _item:
                break

            if isinstance(_item, dict):
                _item = Item(_item)

            if not isinstance(_item, Item) and (not (isinstance(_item, list) and all(isinstance(item, Item) for item in _item))):
                raise InvalidOutput(
                    f"Middleware {method.__self__.__class__.__name__}"
                    ".process_item must return None or "
                    f"Item or list[Item], got {type(_item)}"
                )

    async def process_exception(self, request, response, item, exception, spider_ins):
        for method in self.methods['process_exception']:
            middleware_response = await run_function(method, request, response, item, exception, spider_ins)
            if middleware_response is not None and not isinstance(middleware_response, bool):
                raise InvalidOutput(
                    f"Middleware {method.__self__.__class__.__name__}"
                    ".process_exception must return None or "
                    f"bool, got {type(middleware_response)}"
                )
            if middleware_response:
                return

    async def process_pipelines(self, request, response, item, spider_ins):
        # 执行完request_middleware，调用下载器
        try:
            await self.process_item(item, spider_ins)
        except InvalidOutput:
            raise
        except Exception as e:
            return await self.process_exception(request, response, item, Error(e, traceback.format_exc()), spider_ins)
