# encoding: utf-8

import hoopa
from hoopa import Request
from hoopa.settings import const


class ProxyMiddleware:
    def process_request(self, request: Request, spider_ins):
        # 判断下载器
        if spider_ins.downloader_cls == const.AiohttpDownloader:
            request.proxy = "http://127.0.0.1:7890"
        elif spider_ins.downloader_cls == const.HttpxDownloader:
            # 这里httpx请求都是先创建会话来请求的，httpx会话代理只能设置会话的配置
            request.client_kwargs["proxies"] = {'https': "http://127.0.0.1:7890", 'http': "http://127.0.0.1:7890"}
        elif spider_ins.downloader_cls == const.RequestsDownloader:
            request.proxies = {'https': "http://127.0.0.1:7890", 'http': "http://127.0.0.1:7890"}


class MiddlewareDemoSpider(hoopa.Spider):
    name = "middleware_demo"
    start_urls = ["http://httpbin.org/ip"]
    middlewares = [ProxyMiddleware]

    def parse(self, request, response):
        print(response.text)


if __name__ == "__main__":
    MiddlewareDemoSpider.start()
