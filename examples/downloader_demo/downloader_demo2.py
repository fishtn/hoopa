# encoding: utf-8
import requests

import hoopa
from hoopa.settings import const


class DownloaderDemoSpider(hoopa.Spider):
    name = "downloader_demo"
    start_urls = ["http://httpbin.org/json"]
    downloader_cls = const.RequestsDownloader
    log_level = "debug"

    def parse(self, request, response):
        res = requests.get("http://httpbin.org/ip")
        print(res.text)


if __name__ == "__main__":
    DownloaderDemoSpider.start()
