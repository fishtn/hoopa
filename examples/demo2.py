# encoding: utf-8

import hoopa
from hoopa.settings import const


class DataItem(hoopa.Item):
    title: str
    type: str


class DemoSpider(hoopa.Spider):
    name = "demo"
    start_urls = ["http://httpbin.org/json"]
    downloader_cls = const.AiohttpDownloader

    async def parse(self, request, response):
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
    DemoSpider.start()
