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

import ujson
from loguru import logger

from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.connection import get_aio_redis
from hoopa.utils.helpers import get_timestamp, get_priority_list, get_mac_pid


class BaseQueue:
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
    def __init__(self, waiting, serialization_module, engine):
        # 下载队列，一个优先级队列
        self.waiting = waiting
        # 进行中的队列，key为Request，value取出的时间戳
        self.pending = {}
        # 失败次数记录，key为Request，value失败次数
        self.failure = {}
        self.serialization_module = serialization_module
        self.engine = engine

    @classmethod
    async def create(cls, engine):
        waiting = PriorityQueue()
        serialization_module = importlib.import_module(engine.setting["SERIALIZATION"])
        return cls(waiting, serialization_module, engine)

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
            return Request.unserialize(result[1], self.serialization_module)
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
            str_request = request.serialize(self.serialization_module)
            pended_time = self.pending.get(str_request, 0)
            if time.time() - pended_time < self.engine.setting["PENDING_THRESHOLD"]:
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
        str_request = request.serialize(self.serialization_module)

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
        if not self.pending and self.waiting.empty():
            spider_ins.run = False


class RedisQueue(BaseQueue):
    """
    Redis队列
    """
    def __init__(self, spider_name, serialization_module, engine):
        self._spider_name = spider_name
        self.serialization_module = serialization_module
        self.engine = engine
        
        self._failure_key = f"{spider_name}:failure"
        self._pending_key = f"{spider_name}:pending"
        self._waiting_key = f"{spider_name}:waiting"
        self._client_key = f"{spider_name}:client"
        
        self.pool = None
        self._last_check_pending_task_time = 0
        
        # 统计信息
        self.task_count = 0
        self.task_success = 0
        self.task_failure = 0

    @classmethod
    async def create(cls, engine):
        serialization_module = importlib.import_module(engine.setting["SERIALIZATION"])
        spider_name = engine.setting["NAME"]
        return cls(spider_name, serialization_module, engine)

    async def init(self):
        """
        初始化db
        """
        self.pool = await get_aio_redis(self.engine.setting["REDIS_SETTING"])
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(self.set_heart_beat(), loop=loop)

    async def set_heart_beat(self):
        start_time = int(time.time())
        last_time_requests_count = 0
        while True:

            now_time = int(time.time())
            run_time = int(now_time - start_time)
            if run_time:
                requests_count = self.engine.requests_count
                requests_per_second_all = round(requests_count / run_time, 1)
                requests_per_second_10s = round((requests_count - last_time_requests_count) / 10, 1)
                last_time_requests_count = requests_count
                with await self.pool as conn:
                    data = {
                        "总数": self.task_count,
                        "成功": self.task_success,
                        "失败": self.task_failure,
                        "请求": self.engine.requests_count,
                        "每秒请求(全部)": requests_per_second_all,
                        "每秒请求(10s)": requests_per_second_10s,
                        "上报时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_time)),
                    }
                    dumps_data = ujson.dumps(data, ensure_ascii=False)
                    logger.info(f"统计: {dumps_data}")
                    await conn.hset(self._client_key, get_mac_pid(), dumps_data)

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
                        return Request.unserialize(eval_result, self.serialization_module)
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

        str_requests = [_.serialize(self.serialization_module) for _ in requests]
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

        request_ser = request.serialize(self.serialization_module)
        with await self.pool as conn:
            if response.ok == 1:
                # 成功，删除pending队列
                await conn.hdel(self._pending_key, request_ser)
                self.task_success += 1
            else:
                # 失败, 从等待队列中删除，并放到失败队列
                pipe = conn.pipeline()
                pipe.hdel(self._pending_key, request_ser)
                pipe.hset(self._failure_key, request_ser, response.status)
                await pipe.execute()
                self.task_failure += 1

    async def check_status(self, spider_ins, run_forever=False):
        with await self.pool as conn:
            pending_len = await conn.hlen(self._pending_key)
            waiting_len = await conn.zcard(self._waiting_key)
            if not pending_len and not waiting_len:
                spider_ins.run = False

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
                    if now_time - int(v) > self.engine.setting["PENDING_THRESHOLD"]:
                        request = Request.unserialize(k, self.serialization_module)
                        to_waiting_list.extend([request.priority, k])
                        del_pending_list.append(k)

                if to_waiting_list:
                    pipe = conn.pipeline()
                    pipe.zadd(self._waiting_key, *to_waiting_list)
                    pipe.hdel(self._pending_key, *del_pending_list)
                    result = await pipe.execute()

                    logger.info(f"pendings: {len(pending_list)}, del_pending: {result[1]}, add_waitings: {result[0]}")

    async def failure_to_waiting(self, spider_ins):

        with await self.pool as conn:
            failure_list: dict = await conn.hgetall(self._failure_key)

        if failure_list:
            zadd_list = []
            hdel_list = []
            for key, value in failure_list.items():
                request = Request.unserialize(key)
                zadd_list.extend([request.priority, key])
                hdel_list.append(key)

            if zadd_list:
                with await self.pool as conn:
                    try:
                        pipe = conn.pipeline()
                        pipe.zadd(self._waiting_key, *zadd_list)
                        pipe.hdel(self._failure_key, *hdel_list)
                        await pipe.execute()
                    except:
                        logger.debug(traceback.format_exc())
                        logger.error("failure_to_waiting error")

                    logger.info(f"failure_to_waiting, result: {len(hdel_list)}")

    async def close(self):
        self.pool.close()
