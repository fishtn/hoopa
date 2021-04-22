# encoding: utf-8

import hoopa
from hoopa.settings import const


class DataItem(hoopa.Item):
    title: str
    type: str


class DownloaderDemoSpider(hoopa.Spider):
    name = "downloader_demo"
    start_urls = ["http://httpbin.org/json"]
    # 默认为aiohttp，可修改为httpx
    # downloader_cls = const.AiohttpDownloader
    downloader_cls = const.HttpxDownloader

    def parse(self, request, response):
        data = response.json()
        slides = data["slideshow"]["slides"]
        for slide in slides:
            data_item = DataItem()
            data_item.title = slide["title"]
            data_item.type = slide["type"]
            yield data_item

    async def process_item(self, item_list: list):
        for item in item_list:
            print(item)


if __name__ == "__main__":
    DownloaderDemoSpider.start()
