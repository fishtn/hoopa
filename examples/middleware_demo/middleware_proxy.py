# encoding: utf-8

import hoopa
from hoopa.settings import const


class ProxyMiddleware:
    def process_request(self, request, spider_ins):
        # 判断下载器
        if spider_ins.downloader_cls == const.AiohttpDownloader:
            request.proxy = "http://127.0.0.1:7890"
        else:
            request.proxies = {'https': "http://127.0.0.1:7890", 'http': "http://127.0.0.1:7890"}


class MiddlewareDemoSpider(hoopa.Spider):
    name = "middleware_demo"
    start_urls = ["http://httpbin.org/ip"]
    middlewares = [ProxyMiddleware]

    def parse(self, request, response):
        print(response.text)


if __name__ == "__main__":
    MiddlewareDemoSpider.start()
