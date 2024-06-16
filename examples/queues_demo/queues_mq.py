# encoding: utf-8

import hoopa
from hoopa.settings import const


class QueuesDemoSpider(hoopa.Spider):
    name = "queues_demo"
    start_urls = ["http://httpbin.org/json"]

    # mq
    queue_cls = const.RabbitMQQueue

    #  默认配置
    mq_maxsize = 10
    mq_uri = "amqp://guest:guest@127.0.0.1/"
    mq_api_port = 15672

    def parse(self, request, response):
        data = response.json()
        slides = data["slideshow"]["slides"]
        for slide in slides:
            data_item = hoopa.Item()
            data_item.title = slide["title"]
            data_item.type = slide["type"]
            yield data_item

    def process_item(self, item):
        print(item)


if __name__ == "__main__":
    QueuesDemoSpider.start()
