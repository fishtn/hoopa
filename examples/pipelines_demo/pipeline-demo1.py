# encoding: utf-8

import hoopa
from hoopa.settings import const


class DemoPipeline:
    def process_item(self, item, spider_ins):
        print(item)


class DownloaderDemoSpider(hoopa.Spider):
    name = "downloader_demo"
    start_urls = ["http://httpbin.org/json"]
    downloader_cls = const.RequestsDownloader
    log_level = "info"
    pipelines = [DemoPipeline]

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


if __name__ == "__main__":
    DownloaderDemoSpider.start()
