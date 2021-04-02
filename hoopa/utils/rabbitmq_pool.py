# encoding: utf-8
import asyncio
from dataclasses import dataclass

from aio_pika import connect_robust, Channel, pool, Message, DeliveryMode


@dataclass
class RabbitMqPool:
    _url: str = None
    _max_size: int = None
    _connection_pool: pool.Pool = None
    _channel_pool: pool.Pool = None

    async def close(self):
        await self._connection_pool.close()
        await self._channel_pool.close()

    def __init__(self, spider_name):
        self.spider_name = spider_name
        self.queue = None
        self.exchange = None
        self.routing_key = None

        self.exchange_name = "spider_exchange"
        self.queue_name = f"spider_queue_{self.spider_name}"
        self.routing_key = f"spider_rk_{self.spider_name}"
        self.dlx_exchange_name = "spider_exchange_dlx"
        self.dlx_queue_name = f"spider_queue_{self.spider_name}_dlx"
        self.dlx_routing_key = f"spider_rk_{self.spider_name}_dlx"

    async def init(self, url, max_size: int):
        self._url = url
        self._connection_pool = pool.Pool(self._get_connection, max_size=max_size)
        self._channel_pool = pool.Pool(self._get_channel, max_size=max_size)
        await self.declare_delay_queue()
        await self.declare_queue()

    @property
    def channel_pool(self):
        return self._channel_pool

    async def _get_connection(self):
        return await connect_robust(self._url)

    async def _get_channel(self) -> Channel:
        async with self._connection_pool.acquire() as connection:
            return await connection.channel()

    async def declare_delay_queue(self):
        async with self._channel_pool.acquire() as channel:
            dlx_exchange = await channel.declare_exchange(name=self.dlx_exchange_name, type='direct', durable=True)
            dlx_queue = await channel.declare_queue(name=self.dlx_queue_name, auto_delete=False, durable=True)
            await dlx_queue.bind(self.dlx_exchange_name, self.dlx_routing_key)

    async def declare_queue(self):

        self.routing_key = self.routing_key
        async with self._channel_pool.acquire() as channel:
            self.exchange = await channel.declare_exchange(name=self.exchange_name, type='topic', durable=True, arguments={"x-max-priority": 20})
            arguments = {
                # 'x-dead-letter-exchange': self.dlx_exchange_name,
                # 'x-dead-letter-routing-key': self.dlx_routing_key,
                "x-max-priority": 20,
            }
            self.queue = await channel.declare_queue(name=self.queue_name, durable=True, auto_delete=False, arguments={"x-max-priority": 20})
            await self.queue.bind(self.exchange_name, self.routing_key)

    async def subscribe(self, timeout: int) -> None:
        declaration_result = await self.queue.declare()
        print(declaration_result.message_count)
        if declaration_result.message_count > 0:
            message = await self.queue.get(timeout=timeout)
            return message
        else:
            return None

    async def publish(self, msg: str, priority: int = 0) -> None:
        await self.exchange.publish(
            Message(
                msg.encode(),
                priority=priority,
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=self.routing_key
        )
