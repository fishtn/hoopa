# encoding: utf-8
"""
爬虫核心
"""
import weakref
from abc import ABC
from inspect import isawaitable
import typing
import asyncio

import ujson
from loguru import logger

from hoopa.core.engine import Engine
from hoopa.settings import const, Setting
from hoopa.utils.connection import get_aio_redis
from hoopa.utils.helpers import get_md5
from hoopa.exceptions import SpiderHookError
from hoopa.request import Request
from hoopa.response import Response
from hoopa.item import Item


try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class BaseSpider:
    """
    used for extend spider

    Public attributes:
    - name: 爬虫名称.
    - worker_numbers: worker_numbers任务数，每download_delay秒worker_numbers个， 默认每1秒1个
    - download_delay: 爬虫请求间隔，每download_delay秒worker_numbers个， 默认每1秒1个
    - pending_threshold: pending超时时间.
    - run_forever: 任务完成不停止, 默认False.
    - queue_cls: 任务队列路径，默认：const.MemoryQueue(hoopa.queues.MemoryQueue).
    - clean_queue: 清空任务队列，默认False.
    - priority: 指定队列优先级，redis优先队列有效.
    - downloader_cls: 下载器路径，默认：const.AiohttpDownloader(hoopa.downloader.AiohttpDownloader).
    - downloader_middlewares: 下载中间件
    - spider_middlewares: 爬虫中间件
    - pipelines: 管道
    - dupefilter_cls: 去重器路径，默认MemoryDupeFilter，另外有RedisDupeFilter
    - clean_dupefilter: 清空去重器，默认等于clean_queue
    - dupefilter_setting: 去重器设置，默认等于redis_setting
    - redis_setting: redis连接配置，可以是字典，也可以是uri 例如："redis://127.0.0.1:6379/0?encoding=utf-8"
    - serialization: 序列化模块，默认ujson，可选pickle
    - log_config： 自定义logger.configure的参数，类型为字典
    - log_level： 日志级别，默认INFO
    - log_write_file： 日志是否写入文件，默认否
    - settings_path： 默认配置文件位置
    - start_urls： 起始url列表
    - interrupt_with_error： 出现错误时推出，默认False
    - failure_to_waiting：  将错误队列放入等待队列，默认False
    - push_number：  请求推送到redis单次最大数量
    - run:  控制爬虫停止，默认为True运行，设置为False停止
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
    http_client_kwargs: bool = None
    downloader_middlewares: list = None
    spider_middlewares: list = None
    pipelines: list = None
    dupefilter_cls: bool = None
    clean_dupefilter: bool = None
    stats_cls: str = None
    dupefilter_setting: typing.Union[dict, str] = None
    redis_setting: typing.Union[dict, str] = None
    log_config: dict = None
    log_level: str = None
    log_write_file: bool = None
    serialization: bool = None
    settings_path: str = "config.settings"
    start_urls: list = []
    interrupt_with_error: bool = None
    setting: Setting = None
    push_number: int = None
    failure_to_waiting: bool = None
    run: bool = None

    async def run_spider_hook(self, hook_func):
        """
        Run hook before/after spider start crawling
        :param hook_func: aws function
        :return:
        """
        if callable(hook_func):
            try:
                aws_hook_func = hook_func(weakref.proxy(self))
                if isawaitable(aws_hook_func):
                    await aws_hook_func
            except Exception as e:
                raise SpiderHookError(f"<Hook {hook_func.__name__}: {e}")

    async def open_spider(self):
        pass

    async def close_spider(self, spider_stats):
        pass

    async def init(self):
        """
        由于魔术方法__init__无法使用await，可以在爬虫重写这个方法，以达到初始化的目的
        """
        pass

    async def start_requests(self):
        """
        用于初始化url，默认读取start_urls, 可重写
        """
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse)

    async def process_item(self, item: Item):
        return item

    async def process_request(self, request: Request):
        return request

    async def parse(self, request: Request, response: Response):
        raise NotImplementedError("<!!! parse function is expected !!!>")

    async def process_failed(self, request: Request, response: Response):
        """
        处理错误的任务
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_succeed(self, request: Request, response: Response):
        """
        处理成功的任务
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    @classmethod
    async def async_start(cls, before_start=None, after_stop=None, loop=None):
        loop = loop or asyncio.get_event_loop()
        spider_ins = cls()
        engine = Engine(spider_ins, loop=loop)
        await engine._start(before_start, after_stop)
        return engine

    @classmethod
    def start(cls, before_start=None, after_stop=None, loop=None):
        """
        爬虫入口, 非异步
        @rtype: object
        """
        loop = loop or asyncio.new_event_loop()
        spider_ins = cls()
        engine = Engine(spider_ins, loop=loop)
        loop.run_until_complete(engine._start(before_start, after_stop))
        engine.loop.run_until_complete(engine.loop.shutdown_asyncgens())
        engine.loop.close()
        return engine


class Spider(BaseSpider, ABC):

    async def process_failed(self, request: Request, response: Response):
        """
        处理错误的任务
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_succeed(self, request: Request, response: Response):
        """
        处理成功的任务
        :param request: Request
        :param response: Response
        :return:
        """
        pass

    async def process_item(self, item: typing.Union[Item, list[Item]]):
        """
        处理item，爬虫里面的process_item，可以直接调用
        @param item:
        """
        return item

    async def process_request(self, request):
        """
        爬虫里面的载中间件，处理下载前的request
        @param request:
        """
        pass


class RedisSpider(BaseSpider, ABC):
    redis_pool = None
    queue_cls = const.RedisQueue

    async def open_spider(self):
        self.redis_pool = await get_aio_redis(self.setting["REDIS_SETTING"])
        self.setting.set("DUPEFILTER_CLS", const.RedisDupeFilter, "default")
        self.setting.set("STATS_CLS", const.RedisStatsCollector, "default")
        self.setting.set("DUPEFILTER_SETTING", self.setting.get("REDIS_SETTING"), "default")
        self.setting.set("CLEAN_DUPEFILTER", self.setting.get("CLEAN_QUEUE"), "default")

    async def process_item(self, item: Item):
        """
        处理item，RedisQueue的时候默认保存到redis。其他情况需要重写此方法
        @rtype: bool
        @param item:
        """
        item_str_json = ujson.dumps(item.values)
        item_md5 = get_md5(item_str_json)

        with await self.redis_pool as conn:
            result = await conn.hmset(f"{self.name}:{item.item_name}", item_md5, item_str_json)
        if result:
            logger.info(f"{item.values}")


