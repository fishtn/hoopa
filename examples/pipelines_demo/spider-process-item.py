# encoding: utf-8

import hoopa
from hoopa.settings import const


class DownloaderDemoSpider(hoopa.Spider):
    name = "downloader_demo"
    start_urls = ["http://httpbin.org/json"]
    downloader_cls = const.RequestsDownloader
    log_level = "info"

    def parse(self, request, response):
        data = response.json()
        slides = data["slideshow"]["slides"]
        item_list = []
        for slide in slides:
            data_item = hoopa.Item()
            data_item.title = slide["title"]
            data_item.type = slide["type"]
            item_list.append(data_item)
            yield data_item
        yield item_list

    def process_item(self, items):
        print(items)


if __name__ == "__main__":
    DownloaderDemoSpider.start()
