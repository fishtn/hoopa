# encoding: utf-8

import hoopa
from hoopa.settings import const


class DataItem(hoopa.Item):
    title: str
    type: str


class RedisDemoSpider(hoopa.Spider):
    name = "redis_demo"
    start_urls = ["http://httpbin.org/json"]

    # 设置队列为redis
    queue_cls = const.RedisQueue
    redis_setting = "redis://127.0.0.1:6379/0?encoding=utf-8"

    async def parse(self, request, response):
        data = response.json()
        slides = data["slideshow"]["slides"]
        for slide in slides:
            data_item = DataItem()
            data_item.title = slide["title"]
            data_item.type = slide["type"]
            yield data_item


if __name__ == "__main__":
    RedisDemoSpider.start()
