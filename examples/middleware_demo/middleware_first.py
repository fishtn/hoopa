# encoding: utf-8

import hoopa
from hoopa.settings import const


class DemoMiddleware:
    def process_request(self, request, spider_ins):
        print(f"{request} 中间件")

    def process_response(self, request, response, spider_ins):
        print(f"{response} 中间件")


class MiddlewareDemoSpider(hoopa.Spider):
    name = "middleware_demo"
    start_urls = ["http://httpbin.org/json"]
    downloader_middlewares = [DemoMiddleware]
    log_level = 'error'

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
    MiddlewareDemoSpider.start()
