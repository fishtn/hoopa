# encoding: utf-8
"""
爬虫核心
"""
import asyncio
import operator
import traceback
from abc import ABC
from asyncio import iscoroutinefunction
from functools import reduce
from inspect import isawaitable
import typing
from types import AsyncGeneratorType, CoroutineType

import ujson
from loguru import logger

from hoopa.middlewares.stats import downloader_stats
from hoopa.settings import const
from hoopa.utils.log import Logging
from hoopa.utils.asynciter import AsyncIter
from hoopa.utils.helpers import spider_sleep, get_md5, split_list, get_uuid, get_timestamp, get_cls
from hoopa.exceptions import InvalidCallbackResult
from hoopa.middleware import Middleware
from hoopa.item import Item
from hoopa.request import Request
from hoopa.response import Response
from hoopa.scheduler import Scheduler
from hoopa.utils.project import get_project_settings, Setting
from hoopa.utils import decorators

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.debug("use uvloop")
except ImportError:
    pass


class BaseSpider:
    """
    used for extend spider
    """

    async def init(self):
        """
        由于魔术方法__init__无法使用await，可以在爬虫重写这个方法，以达到初始化的目的
        """
        pass

    async def start_requests(self):
        """
        用于
        """
        pass

    async def process_response(self, request, response):
        """
        处理响应
        @param request:
        @param response:
        @return:
        """
        pass

    async def parse(self, request: Request, response: Response):
        raise NotImplementedError("<!!! parse function is expected !!!>")


class Spider(BaseSpider, ABC):
    """MyClass docstring block.

    Public attributes:
    - name: 爬虫名称.
    - worker_numbers: 最大协程数.
    - download_delay: 爬虫请求间隔.
    - pending_threshold: pending超时时间.
    - run_forever: 任务完成不停止, 默认False.
    - queue_cls: 任务队列路径，默认：const.MemoryQueue(hoopa.queues.MemoryQueue).
    - clean_queue: 清空任务队列，默认False.
    - priority: 指定队列优先级，redis优先队列有效.
    - downloader_cls: 下载器路径，默认：const.AiohttpDownloader(hoopa.downloader.AiohttpDownloader).
    - downloader_global_session: 下载器是否使用全局session，默认True.
    - middlewares: 下载中间件.
    - dupefilter_cls: 去重器路径，不配置的话根据queue_cls来决定, MemoryQueue和RabbitMQQueue使用MemoryDupeFilter，RedisQueue使用RedisDupeFilter
    - clean_dupefilter: 清空去重器，默认等于clean_queue
    - dupefilter_setting: 去重器设置，默认等于redis_setting
    - redis_setting: redis连接配置，可以是字典，也可以是uri
    - mq_uri: mq uri链接
    - mq_maxsize: mq连接池大小
    - mq_api_port: mq web api端口
    - serialization: 序列化模块，默认ujson，可选pickle
    - log_level： 日志级别，默认INFO
    - log_write_file： 日志是否写入文件，默认否
    - settings_path： 默认配置文件位置
    - start_urls： 起始url列表
    """
    name: str = "hoopa"
    worker_numbers: int = None
    download_delay: int = None
    pending_threshold: int = None
    run_forever: bool = None
    queue_cls: str = None
    clean_queue: bool = None
    priority: int = None
    downloader_cls: str = None
    downloader_global_session: bool = None
    http_client_kwargs: bool = None
    middlewares: list = None
    dupefilter_cls: bool = None
    clean_dupefilter: bool = None
    dupefilter_setting: dict = None
    redis_setting: typing.Union[dict, str] = None
    mq_uri: str = None
    mq_api_port: int = None
    mq_maxsize: int = None
    log_level: str = None
    log_write_file: bool = None
    serialization: bool = None
    settings_path: str = "config.settings"
    start_urls: list = []

    def __init__(self, middleware: typing.Union[typing.Iterable, Middleware] = None, loop=None):
        self.loop = loop
        asyncio.set_event_loop(self.loop)

        # 初始化调度器
        self.scheduler = Scheduler()
        # 循环获取request，默认True
        self.run = True
        # 协程任务list
        self.task_dict = {}

        # 读取配置文件，如果config下面没有配置文件，那么返回默认配置
        self.setting: Setting = get_project_settings(self.settings_path)
        # 加载爬虫里面的配置，覆盖配置文件的配置
        self.setting.init_settings(self)
        self.logging = Logging(self.setting)
        self.setting.print_log(self)

        # 加载middleware
        middleware_list = [downloader_stats]
        if middleware and isinstance(middleware, list):
            middleware_list.extend(middleware)

        # 加载配置里面的中间件
        if self.setting["MIDDLEWARES"] and isinstance(self.setting["MIDDLEWARES"], list):
            middleware_list.extend(self.setting["MIDDLEWARES"])

        self.middleware = reduce(lambda x, y: x + y, middleware_list)

    async def _load(self):
        # 初始化 spider init
        await self.init()

        # 初始化 download
        self.downloader = await get_cls(self.setting["DOWNLOADER_CLS"], self.setting)

        # 初始化 scheduler
        await self.scheduler.init(self.setting)

        # 初始化stats
        self.stats = self.scheduler.stats

        # 初始化开始的urls
        await self._process_start_urls()
        # 处理start_requests
        await self._handle_start_requests()

    async def _handle_start_requests(self):
        process_func = getattr(self, "start_requests", None)

        if iscoroutinefunction(process_func):
            process_result = await process_func()
            callback_results = process_result
        else:
            callback_results = process_func()

        if callback_results and not isinstance(callback_results, CoroutineType):
            async for callback_result in callback_results:
                if isinstance(callback_result, Request):
                    count = await self.scheduler.add(callback_result)
                    logger.debug(f"start_requests push request {count}")

    async def _process_start_urls(self):
        """
        初始化start_urls, 添加到队列中去
        """
        try:
            request_list = [Request(url=url, callback=self.parse, dont_filter=True) for url in self.start_urls]
            counts = 0
            if request_list:
                counts = await self.scheduler.add(request_list)
            logger.info(f"init start urls end, set {counts}")
        except Exception as e:
            # 初始化start_urls失败
            debug_msg = traceback.format_exc(self.logging.get_tb_limit())
            logger.error(f"init start urls error \n{debug_msg}")

    async def process_item(self, item_list: list):
        """
        处理item，RedisQueue的时候默认保存到redis。其他情况需要重写此方法
        @rtype: bool
        @param item_list:
        """
        if self.setting['SCHEDULER_QUEUE'] == const.RedisQueue:
            for item in item_list:
                item_str_json = ujson.dumps(item.__dict__)
                item_md5 = get_md5(item_str_json)

                with await self.scheduler.scheduler_queue.pool as conn:
                    result = await conn.hmset(f"{self.name}:{item.class_name}", item_md5, item_str_json)

                if result:
                    logger.info(f"{item.__dict__}")
            return result
        else:
            for item in item_list:
                logger.info(f"{item.__dict__}")
            return True

    async def _process_async_callback(self, request: Request, response: Response, callback_results: AsyncGeneratorType):
        # if not callback_results or isinstance(callback_results, CoroutineType):
        if not callback_results or response.ok != 1:
            return

        request_list = []
        item_list = []

        item_stats = {}
        request_stats = {}

        async for callback_result in callback_results:
            if isinstance(callback_result, Request):
                key = callback_result.priority
                item_stats[key] += item_stats.get(key, 1) + 1
                request_list.append(callback_result)
            elif isinstance(callback_result, Item):
                key = callback_result.class_name
                item_stats[key] += item_stats.get(key, 1) + 1
                item_list.append(callback_result)
            else:
                callback_result_name = type(callback_result).__name__
                raise InvalidCallbackResult(f"<Parse invalid callback result type: {callback_result_name}>")

        try:
            # 处理新请求, 默认100个请求批量存储
            request_list_split = split_list(request_list, 100)
            for request_item in request_list_split:
                count = await self.scheduler.add(request_item)
                logger.debug(f"{request} push request {count}")

            # 处理item
            await self.process_item(item_list)

            # 统计item
            for k, v in item_stats.items():
                self.stats.inc_value(f"item/{k}_count", v)
            # 统计request
            for k, v in request_stats.items():
                self.stats.inc_value(f"request/priority_count/{k}", v)
        except Exception as e:
            response.ok = 0
            response.error_type = e.__class__.__name__
            response.debug_msg = traceback.format_exc(self.logging.get_tb_limit())
            logger.error(f"{request} {response} process item or request \n{response.debug_msg}")

    async def _process_callback(self, request, response):

        # 如果response.ok != 1，请求失败，不进行回调
        if response.ok != 1:
            return

        # 响应码在处理列表内，处理响应
        process_func = getattr(self, request.callback, None)

        try:
            if process_func is not None:
                if iscoroutinefunction(process_func):
                    process_result = await process_func(request, response)
                    return process_result
                else:
                    return process_func(request, response)
            else:
                raise Exception(f"<Parse invalid callback result type: {request.callback}>")
        except Exception as e:
            response.ok = 0
            response.error_type = e.__class__.__name__
            response.debug_msg = traceback.format_exc(self.logging.get_tb_limit())
            logger.error(f"{request} {response} callback error \n{response.debug_msg}")

    async def _run_request_middleware(self, request: Request):
        if self.middleware.request_middleware:
            for middleware in self.middleware.request_middleware:
                if callable(middleware):
                    try:
                        aws_middleware_func = middleware(self, request)
                        if isawaitable(aws_middleware_func):
                            response = await aws_middleware_func
                            if response is not None and not isinstance(response, (Response, Request)):
                                raise Exception(f"<Middleware {middleware.__name__}: must return None, Response or Request")
                            if response:
                                return response
                        else:
                            logger.error(f"<Middleware {middleware.__name__}: must be a coroutine function")
                    except Exception as e:
                        logger.error(f"<Middleware {middleware.__name__}: {e}")

        # 执行完request_middleware，调用下载器
        return await self.downloader.request(request, self.setting["DOWNLOADER_GLOBAL_SESSION"])

    async def _run_response_middleware(self, request: Request, response: Response):
        # 如果response是request，返回异步生成器
        if isinstance(response, Request):
            return AsyncIter([response])

        # 没有response中间件，返回
        if not self.middleware.response_middleware:
            return

        for middleware in self.middleware.response_middleware:
            if callable(middleware):
                try:
                    aws_middleware_func = middleware(self, request, response)
                    if isawaitable(aws_middleware_func):
                        middleware_response = await aws_middleware_func
                        if middleware_response is not None and not isinstance(middleware_response, (Response, Request)):
                            raise Exception(f"<Middleware {middleware.__name__}: must return None, Response or Request")

                        if isinstance(middleware_response, Request):
                            return AsyncIter([middleware_response])

                        if isinstance(middleware_response, Response):
                            response = middleware_response
                            break
                    else:
                        logger.error(f"<Middleware {middleware.__name__}: must be a coroutine function")
                except Exception as e:
                    logger.error(f"<Middleware {middleware.__name__}: {e}")

        return await self._process_callback(request, response)

    @decorators.handle_request_retry()
    async def handle_request(self, request: Request):
        """
        处理请求
        @param request: request对象
        """
        # 加载request中间件, 并调用下载器
        response = await self._run_request_middleware(request)
        # 加载response中间件
        callback_result = await self._run_response_middleware(request, response)
        # 处理异步返回的request和item
        await self._process_async_callback(request, response, callback_result)

        return response

    @decorators.timeout_it()
    async def _process_task(self, request: Request, task_id):
        """
        处理请求
        @param task_id:
        @param request: request对象
        """
        try:
            task_request = request.replace()
            # 处理请求和回调
            response = await self.handle_request(task_request)
            # 处理请求响应
            await self.process_response(request, response)
            # 处理请求结果
            await self.scheduler.set_result(request, response, task_request)
        except Exception as e:
            debug_msg = traceback.format_exc(self.logging.get_tb_limit())
            logger.error(f"{request} callback error \n{debug_msg}")

    async def _start_spider(self):
        """
        启动爬虫，不断从队列中获取请求任务
        """
        # 初始化，加载
        await self._load()

        if self.run:
            logger.info(f"Spider start")

        while self.run:
            # 新增的协程数 = 最大协程数 - 当前协程数
            add_task_count = self.worker_numbers - len(self.task_dict)

            for _ in range(add_task_count):
                request = await self.scheduler.get(self.setting["PRIORITY"])
                if request is None:
                    break

                new_task_id = get_uuid()
                asyncio.run_coroutine_threadsafe(self._process_task(request, new_task_id), loop=self.loop)
                self.task_dict.setdefault(new_task_id, get_timestamp())

            # 休眠
            await spider_sleep(self.setting["DOWNLOAD_DELAY"])

            # 检查爬虫状态
            await self.scheduler.check_scheduler(self)

        await self.stop()

    @classmethod
    async def async_start(cls, middleware: typing.Union[typing.Iterable, Middleware] = None, loop=None):
        loop = loop or asyncio.get_event_loop()
        spider_ins = cls(middleware=middleware, loop=loop)
        await spider_ins._start_spider()
        return spider_ins

    @classmethod
    def start(cls, middleware: typing.Union[typing.Iterable, Middleware] = None, loop=None):
        """
        爬虫入口, 非异步
        @rtype: object
        """
        loop = loop or asyncio.get_event_loop()
        spider_ins = cls(middleware=middleware, loop=loop)
        loop.run_until_complete(spider_ins._start_spider())
        spider_ins.loop.run_until_complete(spider_ins.loop.shutdown_asyncgens())
        spider_ins.loop.close()
        return spider_ins

    async def stop(self):
        await self.scheduler.stats.max_value("finish_time", get_timestamp())
        spider_stats = await self.stats.get_stats()
        await self.scheduler.close()
        await self.downloader.close()
        spider_stats_sorted_keys = sorted(spider_stats.items(), key=operator.itemgetter(0))
        body = "stats\n"
        body += "\n".join(f"{k:50s}: {v}" for k, v in spider_stats_sorted_keys)
        logger.info(body)
        await self.cancel_all_tasks()

    async def cancel_all_tasks(self):
        logger.info(f"Stopping spider: {self.name}")
        tasks = []
        for task in asyncio.Task.all_tasks():
            if task is not asyncio.tasks.Task.current_task():
                tasks.append(task)
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


