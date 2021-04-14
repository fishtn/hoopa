# encoding: utf-8
"""
爬虫队列
"""
import asyncio
import importlib
import time
import traceback
import typing
from asyncio import PriorityQueue
from urllib.parse import urlparse, quote_plus

import aiohttp
import ujson
from loguru import logger
from aio_pika import IncomingMessage

from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.connection import get_aio_redis
from hoopa.utils.helpers import get_timestamp, get_priority_list, get_mac_pid
from hoopa.utils.rabbitmq_pool import RabbitMqPool
from hoopa.utils.serialization import serialize_request_and_response


class BaseQueue:
    async def init(self, setting):
        """
        初始化队列
        """
        pass

    async def get(self, priority):
        """
        从队列中获取一个request
        @param priority: 权重，取出对应权重的request
        """
        pass

    async def add(self, requests: typing.Union[Request, typing.List[Request]]):
        """
        向队列添加多个request
        @param requests:
        """
        pass

    async def set_result(self, request: Request, response: Response, task_request: Request):
        """
        保存结果
        @param request:
        @param response:
        @param task_request:
        """
        pass

    async def clean_queue(self):
        """
        清空队列
        """
        pass

    async def check_status(self, spider_ins, run_forever):
        """
        检查状态，主要是判断爬虫是否爬取完毕，其他的具体根据队列自身实现需要的功能
        @return:
        """
        pass

    async def close(self):
        pass


class MemoryQueue(BaseQueue):
    def __init__(self, ):
        # 下载队列，一个优先级队列
        self.waiting = None
        # 进行中的队列，key为Request，value取出的时间戳
        self.pending = {}
        # 失败次数记录，key为Request，value失败次数
        self.failure = {}
        self.module = None
        self.setting = None

    async def init(self, setting):
        """
        初始化
        """
        self.setting = setting
        self.waiting = PriorityQueue()
        self.module = importlib.import_module(setting.SERIALIZATION)

    async def clean_scheduler(self, waiting=True, pending=True, failure=True, data=True):
        """
        清空队列
        """
        pass

    async def get(self, priority):
        """
        从队列中获取一个request
        """
        if not self.waiting.empty():
            result = await self.waiting.get()
            self.pending[result[1]] = get_timestamp()
            return Request.unserialize(result[1], self.module)
        return None

    async def add(self, requests: typing.Union[Request, typing.List[Request]]):
        """
        向队列添加多个request
        @param requests:
        """
        if isinstance(requests, Request):
            requests = [requests]

        count = 0
        # 判断是否在pending中，如果在，是否过了最大时间
        for request in requests:
            str_request = request.serialize(self.module)
            pended_time = self.pending.get(str_request, 0)
            if time.time() - pended_time < self.setting["PENDING_THRESHOLD"]:
                continue

            count += 1
            self.waiting.put_nowait((-request.priority, str_request))
            if pended_time:
                self.pending.pop(str_request)
        return count

    async def set_result(self, request: Request, response: Response, task_request: Request):
        """
        保存结果
        @param request:
        @param response:
        @param task_request:
        """
        # 如果失败，且失败次数未达到，返回waiting
        str_request = request.serialize(self.module)

        # 如果在进行队列中，删除
        if str_request in self.pending:
            self.pending.pop(str_request)

        # 如果成功
        if response.ok == 1:
            return True

        if response.ok == -1:
            self.failure[str_request] = response.status
            return False

        if str_request in self.failure:
            self.failure[str_request] += 1
            await self.add(request)
        else:
            self.failure[str_request] = 1
            await self.add(request)

    async def check_status(self, spider_ins, run_forever=False):
        if len(self.pending) == 0 and self.waiting.empty():
            spider_ins.run = False


class RedisQueue(BaseQueue):
    """
    Redis队列
    """
    def __init__(self):
        self.pool = None
        self._spider_name = None
        self._failure_key = None
        self._pending_key = None
        self._waiting_key = None
        self._last_check_pending_task_time = 0
        self.module = None
        self._setting = None

        # 统计信息
        self.task_count = 0
        self.task_success = 0
        self.task_failure = 0

    async def init(self, setting):
        """
        初始化db
        """
        self._setting = setting
        self._spider_name = setting.NAME
        self._failure_key = f"{self._spider_name}:failure"
        self._pending_key = f"{self._spider_name}:pending"
        self._waiting_key = f"{self._spider_name}:waiting"
        self._waiting_key = f"{self._spider_name}:waiting"
        mac_pid_key = f"{self._spider_name}:client:{get_mac_pid()}"

        self.module = importlib.import_module(setting.SERIALIZATION)

        self.pool = await get_aio_redis(setting["REDIS_SETTING"])
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(self.set_heart_beat(mac_pid_key), loop=loop)

    async def set_heart_beat(self, mac_pid_key):
        while True:
            with await self.pool as conn:
                data = {"T": self.task_count, "S": self.task_success, "F": self.task_failure}
                await conn.set(mac_pid_key, ujson.dumps(data), expire=10)
            await asyncio.sleep(10)

    async def clean_queue(self):
        """
        清空队列
        """
        with await self.pool as conn:
            # 要避免一次性删除过大的key，导致redis阻塞
            await conn.delete(self._failure_key)
            await conn.delete(self._pending_key)
            await conn.delete(self._waiting_key)

    async def get(self, priority: typing.Union[int, list]):
        """
        从redis中获取request
        @param priority: 为None的时候，获取所有权重，否则获取指定的权重，可以是int，也可以是int列表
        @return: request
        """
        priority_list = []
        if priority is None:
            priority_list.append(("-inf", "+inf"))
        elif isinstance(priority, int):
            priority_list.append((priority, priority))
        else:
            priority_list = get_priority_list(priority)

        try:
            lua = """
                redis.replicate_commands()
                local waiting_key = KEYS[1]
                local pending_key = KEYS[2]
                local min = KEYS[3]
                local max = KEYS[4]

                -- 取值
                local result = redis.call('zrevrangebyscore', waiting_key, max, min, 'LIMIT', 0, 1)

                if result and table.getn(result) > 0 then
                    redis.call('zrem', waiting_key, result[1])
                    redis.call('hset', pending_key, result[1], redis.call('TIME')[1])
                    return result[1]
                end
                return nil
            """
            with await self.pool as conn:
                for p_item in priority_list:
                    _min, _max  = p_item
                    eval_result = await conn.eval(lua, keys=[self._waiting_key, self._pending_key, _min, _max], args=[])
                    if eval_result:
                        self.task_count += 1
                        return Request.unserialize(eval_result, self.module)
        except Exception as e:
            logger.error(f"get request error \n{traceback.format_exc()}")

        return None

    async def add(self, requests):
        """
        向队列添加request
        @param requests: request列表
        @return:
        """
        if not isinstance(requests, list):
            requests = [requests]

        str_requests = [_.serialize(self.module) for _ in requests]
        priority_list = [_.priority for _ in requests]
        lua = """
            redis.replicate_commands()
            local priority_list = KEYS
            local requests = ARGV

            local spider = table.remove(priority_list, 1)

            local now = redis.call('TIME')[1]
            local waiting_key = spider..':waiting'
            local pending_key = spider..':pending'

            local add_counts = 0
            for i, v in ipairs(requests) do
                -- 判断在pending中的时间
                local score = redis.call('hget', pending_key, v)
                if (score and tonumber(now) - tonumber(score) >= 30) or (not score) then
                    local result = redis.call('zadd', waiting_key, priority_list[i], v)
                    add_counts = add_counts + result
                    redis.call('hdel', pending_key, v)
                end
            end

            return add_counts
        """
        with await self.pool as conn:
            add_counts = await conn.eval(lua, keys=[self._spider_name] + priority_list, args=str_requests)
        return add_counts

    async def set_result(self, request: Request, response: Response, task_request: Request):
        """
        保存结果，设置状态（成功或失败）
        @param request:
        @param response:
        @param task_request:
        @return:
        """

        request_ser = request.serialize(self.module)
        with await self.pool as conn:
            if response.ok == 1:
                # 成功，删除pending队列
                await conn.hdel(self._pending_key, request_ser)
                self.task_success += 1
            else:
                failure_response = serialize_request_and_response(task_request, response)
                # 失败, 从等待队列中删除，并放到失败队列
                pipe = conn.pipeline()
                pipe.hdel(self._pending_key, request_ser)
                pipe.hset(self._failure_key, request_ser, failure_response)
                await pipe.execute()
                self.task_failure += 1

    async def check_status(self, spider_ins, run_forever=False):
        with await self.pool as conn:
            pending_len = await conn.hlen(self._pending_key)
            waiting_len = await conn.zcard(self._waiting_key)
            if not pending_len and not waiting_len:
                spider_ins.run = False
                return

        await self.check_pending_task()

    async def check_pending_task(self):
        # 判断是否有超时的链接
        now_time = time.time()
        if now_time - self._last_check_pending_task_time > 10:
            self._last_check_pending_task_time = now_time
            now_time = time.time()

            with await self.pool as conn:
                pending_list = await conn.hgetall(self._pending_key)

                to_waiting_list = []
                del_pending_list = []
                for k, v in pending_list.items():
                    if now_time - int(v) > self._setting["PENDING_THRESHOLD"]:
                        request = Request.unserialize(k, self.module)
                        to_waiting_list.extend([request.priority, k])
                        del_pending_list.append(k)

                if to_waiting_list:
                    pipe = conn.pipeline()
                    pipe.zadd(self._waiting_key, *to_waiting_list)
                    pipe.hdel(self._pending_key, *del_pending_list)
                    result = await pipe.execute()

                    logger.info(f"pendings: {len(pending_list)}, del_pending: {result[1]}, add_waitings: {result[0]}")

    async def close(self):
        self.pool.close()


class RabbitMQQueue(BaseQueue):
    def __init__(self):
        self.spider_name = None
        self.mq_uri = None
        self.mq_maxsize = None
        self.pool = None
        self.queue_name = f"{self.spider_name}_queue"
        self._last_check_task_status_time = time.time()

        # 从uri提取，用于web api
        self.mq_user = None
        self.mq_pwd = None
        self.mq_api_url = None
        self.module = None

    async def init(self, setting):
        self.spider_name = setting.NAME
        self.mq_uri = setting["MQ_URI"]
        self.mq_maxsize = setting["MQ_MAXSIZE"]
        mq_api_port = setting["MQ_API_PORT"]
        self.pool = RabbitMqPool(self.spider_name)
        await self.pool.init(self.mq_uri, self.mq_maxsize)

        self.module = importlib.import_module(setting.SERIALIZATION)

        result = urlparse(self.mq_uri).netloc
        split_list = result.split("@")
        user_pwd = split_list[0].split(":")
        self.mq_user = user_pwd[0]
        self.mq_pwd = user_pwd[1]

        queue_name = f"spider_queue_{self.spider_name}"
        host = split_list[1].split(":")[0]
        self.mq_api_url = f"http://{host}:{mq_api_port}/api/queues/{quote_plus('/')}/{queue_name}"

    async def clean_scheduler(self):
        """
        清空队列
        """
        async with self.pool.channel_pool.acquire() as channel:
            await channel.queue_delete(queue_name=self.queue_name)

    async def get(self, priority):
        """
        从队列中获取一个request
        """

        message = await self.pool.subscribe(2)

        if message:
            request = Request.unserialize(message.body.decode(), self.module)
            request.message = message
        else:
            request = None
        return request

    async def add(self, requests: typing.Union[Request, typing.List[Request]]):
        """
        向队列添加多个request
        @param requests:
        """
        if isinstance(requests, Request):
            requests = [requests]

        for request in requests:
            request_ser = request.serialize(self.module)
            await self.pool.publish(request_ser, request.priority)

        return len(requests)

    async def set_result(self, request: Request, response: Response, task_request: Request):
        """
        保存结果
        @param request:
        @param response:
        @param task_request:
        """
        message: IncomingMessage = request.message

        if response.ok == 1:
            await message.ack()
        else:
            await message.nack(requeue=False)

    async def check_status(self, spider_ins, run_forever=False):
        # mq要看total队列是否为空，但是aio_pika并不能获取这个值，只能通过web api来获取
        try:
            async with aiohttp.ClientSession() as client:
                auth = aiohttp.BasicAuth(self.mq_user, self.mq_pwd)
                async with client.request(method='GET', url=self.mq_api_url, auth=auth) as req:
                    data = await req.json()
                    total = int(data["messages"])

            if total == 0:
                spider_ins.run = False
        except:
            logger.error("获取mq队列消息数量失败")

    async def close(self):
        await self.pool.close()