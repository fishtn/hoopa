# encoding: utf-8
"""
爬虫核心
"""
import asyncio
import inspect
import operator
import time
import traceback
import typing
from copy import deepcopy
from signal import SIGINT, SIGTERM
from types import AsyncGeneratorType, CoroutineType

from loguru import logger

from hoopa.core.downloadermiddleware import DownloaderMiddleware
from hoopa.pipelines import PipelineManager
from hoopa.core.spidermiddleware import SpiderMiddleware
from hoopa.utils.concurrency import run_function, run_function_no_concurrency, iterate_in_threadpool
from hoopa.utils.log import Logging
from hoopa.utils.asynciter import AsyncIter
from hoopa.utils.helpers import split_list, get_timestamp, load_object, create_instance_and_init
from hoopa.exceptions import InvalidCallbackResult, Error, InvalidCallback
from hoopa.item import Item
from hoopa.request import Request
from hoopa.response import Response
from hoopa.core.scheduler import Scheduler
from hoopa.utils.project import get_project_settings
from hoopa.utils import decorators

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class Engine:
    def __init__(self, spider, loop=None):
        self.loop = loop
        asyncio.set_event_loop(self.loop)

        self.spider = spider

        # 循环获取request，默认True
        self.spider.run = True

        self.request_queue: asyncio.Queue = asyncio.Queue()

        # 重试中的个数
        self.retrying = 0

        # 请求数统计
        self.requests_count = 0

        # 读取配置文件，如果config下面没有配置文件，那么返回默认配置
        setting = get_project_settings(spider.settings_path)
        # 加载爬虫里面的配置，覆盖配置文件的配置
        setting.init_settings(spider)

        self.setting = setting
        self.spider.setting = setting
        Logging(setting)

    async def _load(self):
        # 初始化 spider init
        await run_function(self.spider.open_spider)
        await run_function(self.spider.init)

        # 初始化 download
        downloader_cls = load_object(self.setting["DOWNLOADER_CLS"])
        self.downloader = await create_instance_and_init(downloader_cls, self)

        # 初始化 scheduler
        self.scheduler = await create_instance_and_init(Scheduler, self)

        # 初始化stats
        self.stats = self.scheduler.stats

        # 初始化下载中间件
        self.downloader_middleware = await DownloaderMiddleware.create(self)
        # 初始化爬虫中间件
        self.spider_middleware = await SpiderMiddleware.create(self)
        # 初始化管道
        self.pipeline_manager = await PipelineManager.create(self)

        # 打印配置日志
        self.setting.print_log(self)

        # failure_to_waiting
        if self.spider.failure_to_waiting:
            await self.scheduler.failure_to_waiting(self.spider)

        # 处理start_requests
        await self._handle_start_requests()

    async def _process_async_callback(self, request: Request, response: Response, callback_results: AsyncGeneratorType):
        if not callback_results or response.ok != 1:
            return

        request_list = []

        async for callback_result in callback_results:
            if isinstance(callback_result, Request):
                request_list.append(callback_result)
            # 如果是字典，也可以跟item一样处理
            elif isinstance(callback_result, dict):
                await self.pipeline_manager.process_pipelines(request, response, callback_result, self.spider)
            elif isinstance(callback_result, Item):
                await self.pipeline_manager.process_pipelines(request, response, callback_result, self.spider)
            elif isinstance(callback_result, list) and all(isinstance(item, Item) for item in callback_result):
                # 如果是item list，也进行处理
                await self.pipeline_manager.process_pipelines(request, response, callback_result, self.spider)
            else:
                callback_result_name = type(callback_result).__name__
                raise InvalidCallbackResult(f"<Parse invalid callback result type: {callback_result_name}>")

        # 处理新请求, 默认50个请求批量存储
        request_list_split = split_list(request_list, 50)
        for item_requests in request_list_split:
            count = await self.scheduler.add(item_requests)
            logger.debug(f"{request} push request {count}")

    async def _process_callback(self, request, response):
        # 如果response.ok != 1，请求失败，不进行回调
        if response.ok != 1:
            return

        # 响应码在处理列表内，处理响应
        try:
            process_func = getattr(self.spider, request.callback, None)
        except:
            raise InvalidCallback("解析函数错误")

        try:
            if process_func is not None:
                callback_results = await self.spider_middleware.scrape_response(process_func, request, response,
                                                                                self.spider)
                # 判断是否是异步生成器，生成器需要需要在线程池里运行，避免阻塞
                if callback_results and not inspect.isasyncgen(callback_results):
                    return iterate_in_threadpool(callback_results)
                else:
                    return callback_results
            else:
                raise Exception(f"<Parse invalid callback result type: {request.callback}>")
        except Exception as e:
            response.ok = 0
            response.error = Error(e, traceback.format_exc())
            logger.error(f"{request} {response} callback error \n{response.error.stack}")

    @decorators.handle_download_callback_retry()
    async def handle_download_callback(self, request: Request):
        """
        处理请求
        @param request: request对象
        """
        # 请求数+1
        self.requests_count += 1

        # 加载request中间件, 并调用下载器
        response = await self.downloader_middleware.download(self.downloader.fetch, request, self.spider)

        # 回调
        callback_result = await self._process_callback(request, response)

        # 处理异步返回的request和item
        await self._process_async_callback(request, response, callback_result)

        return response

    @decorators.timeout_it()
    async def _process_task(self, request: Request):
        """
        处理请求
        @param request: request对象
        """
        response = Response()
        task_request = deepcopy(request)
        try:
            # 处理请求和回调
            response = await self.handle_download_callback(task_request)
            # 处理请求结果
            await self.scheduler.set_result(request, response, task_request)
        except Exception as e:
            response.ok = -1
            response.error = Error(e, traceback.format_exc())
            logger.error(f"{request} {response} callback error \n{response.error.stack}")

        if response.ok != 1:
            await run_function(self.spider.process_failed, task_request, response)
        else:
            await run_function(self.spider.process_succeed, task_request, response)

    async def _handle_start_requests(self):
        """
        用于初始化url，默认读取start_urls, 可重写
        """
        callback_results = await run_function(self.spider.start_requests)

        if isinstance(callback_results, typing.Generator):
            callback_results = AsyncIter(callback_results)

        request_list = []

        if callback_results and not isinstance(callback_results, CoroutineType):
            async for callback_result in callback_results:
                if isinstance(callback_result, Request):
                    request_list.append(callback_result)

        # 处理新请求, 默认50个请求批量存储
        request_list_split = split_list(request_list, self.spider.push_number)
        for item_requests in request_list_split:
            count = await self.scheduler.add(item_requests)
            logger.debug(f"start_requests push request {count}")

    async def start_worker(self):
        """
        Start spider worker
        :return:
        """
        while True:
            request_item = await self.request_queue.get()
            asyncio.run_coroutine_threadsafe(self._process_task(request_item), loop=self.loop)
            self.request_queue.task_done()

    async def consumer(self):
        logger.debug(f"consumer started")
        last_time = time.time()
        empty_rounds = 0  # 连续空轮次计数
        max_empty_rounds = 10  # 最大空轮次，超过后退出
        
        while self.spider.run:
            qsize = self.request_queue.qsize()
            add_task_count = max(self.spider.worker_numbers - qsize - self.retrying, 0)
            # logger.error(f"add_task_count: {add_task_count} {qsize} {self.retrying}")
            add_task_count = min(add_task_count, self.spider.worker_numbers)
            
            added_requests = 0
            for _ in range(add_task_count):
                request_item = await self.scheduler.get(self.spider.priority)
                if request_item is None:
                    break
                self.request_queue.put_nowait(request_item)
                added_requests += 1

            # 如果没有添加任何请求，增加空轮次计数
            if added_requests == 0:
                empty_rounds += 1
                # 如果连续多轮都没有新请求，且队列为空，则退出
                if empty_rounds >= max_empty_rounds and qsize == 0:
                    logger.debug("No more requests available, consumer stopping")
                    break
            else:
                empty_rounds = 0  # 重置空轮次计数

            # 休眠
            sleep_second = max(self.spider.download_delay - (time.time() - last_time), 0.01)

            await asyncio.sleep(sleep_second)
            last_time = time.time()
            await self.scheduler.check_scheduler(self.spider)
            
        logger.debug("Consumer finished")

    async def _start_spider(self):
        """
        启动爬虫，不断从队列中获取请求任务
        """
        # 初始化
        await self._load()

        if self.spider.run:
            logger.info(f"Spider start")

        # 启动worker任务
        workers = [
            asyncio.ensure_future(self.start_worker())
            for _ in range(self.spider.worker_numbers * 3)
        ]

        logger.debug(f"Worker started: {len(workers)}")

        # 启动consumer任务
        consumer_task = asyncio.ensure_future(self.consumer())

        try:
            # 等待consumer完成（当没有更多请求时会自动退出）
            await consumer_task
            
            # 等待所有队列中的任务完成
            await self.request_queue.join()
            
        finally:
            # 取消所有worker任务
            for worker in workers:
                worker.cancel()
            
            # 等待所有worker任务完成取消
            await asyncio.gather(*workers, return_exceptions=True)

        await self.finish()

    async def _start(self, before_start=None, after_stop=None):
        # 添加信号
        # SIGINT：由Interrupt Key产生，通常是CTRL+C或者DELETE。发送给所有ForeGround Group的进程
        # SIGTERM：请求中止进程，kill命令缺省发送
        for signal in (SIGINT, SIGTERM):
            try:
                self.loop.add_signal_handler(signal, lambda: asyncio.ensure_future(self.cancel_all_tasks(signal)))
            except NotImplementedError:
                pass

        # 爬虫开始之前执行
        await self.spider.run_spider_hook(before_start)

        # 爬虫开始
        try:
            await self._start_spider()
        except KeyboardInterrupt:
            await self.cancel_all_tasks()
        finally:
            # 爬虫结束后执行
            await self.spider.run_spider_hook(after_stop)
            logger.info("Spider finished!")

    @classmethod
    async def async_start(cls, before_start=None, after_stop=None, loop=None):
        loop = loop or asyncio.get_event_loop()
        spider_ins = cls(loop=loop)
        await spider_ins._start(before_start, after_stop)
        return spider_ins

    @classmethod
    def start(cls, before_start=None, after_stop=None, loop=None):
        """
        爬虫入口, 非异步
        @rtype: object
        """
        loop = loop or asyncio.new_event_loop()
        spider_ins = cls(loop=loop)
        loop.run_until_complete(spider_ins._start(before_start, after_stop))
        spider_ins.loop.run_until_complete(spider_ins.loop.shutdown_asyncgens())
        spider_ins.loop.close()
        return spider_ins

    async def finish(self):
        start_time = await self.stats.get_value("start_time")
        finish_time = int(get_timestamp())
        await self.stats.max_value("finish_time", finish_time)
        await self.stats.set_value("total_time", finish_time - start_time)

        spider_stats = await self.stats.get_stats()
        spider_stats_sorted_keys = sorted(spider_stats.items(), key=operator.itemgetter(0))
        blank = " " * 4
        body = "\nstats\n"

        body += f"\n".join(f"{blank}{k:50s}: {v}" for k, v in spider_stats_sorted_keys)
        logger.info(body)

        await run_function(self.spider.close_spider, spider_stats)

        await self.close()

    async def close(self):
        await self.scheduler.close()
        await run_function_no_concurrency(self.downloader.close)
        await run_function_no_concurrency(self.downloader_middleware.close)
        await run_function_no_concurrency(self.spider_middleware.close)
        await run_function_no_concurrency(self.pipeline_manager.close)
        await self.cancel_all_tasks()

    async def cancel_all_tasks(self, _signal=None):
        logger.info(f"Stopping spider: {self.spider.name}")
        tasks = []
        for task in asyncio.all_tasks():
            if task is not asyncio.tasks.current_task():
                tasks.append(task)
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
