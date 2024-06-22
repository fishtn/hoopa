# encoding: utf-8

import hoopa
from hoopa import Item
from hoopa.settings import const




class DemoSpider(hoopa.Spider):
    name = "downloader_demo"
    start_urls = ["http://httpbin.org/json"]
    # 默认为aiohttp，可修改为httpx, requests
    downloader_cls = const.RequestsDownloader
    # downloader_cls = const.HttpxDownloader
    # downloader_cls = const.AiohttpDownloader
    log_level = "info"

    def parse(self, request, response):
        data = response.json()
        slides = data["slideshow"]["slides"]
        for slide in slides:
            data_item = Item("DemoItem")
            data_item.title = slide["title"]
            data_item.type = slide["type"]
            yield data_item

    def process_item(self, item):
        print(item)


if __name__ == "__main__":
    DemoSpider.start()
