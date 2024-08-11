# encoding: utf-8
import requests
from hoopa.utils.concurrency import run_function

from hoopa import Request, Response
from hoopa.downloader import Downloader

import hoopa
import cloudscraper


class CloudScraperDownloader(Downloader):
    scraper = None

    def init(self):
        self.scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance

    async def fetch(self, request: Request) -> Response:
        return await run_function(self.sync_fetch, request)

    def sync_fetch(self, request: Request) -> Response:
        _kwargs = request.replace_to_kwargs

        resp = self.scraper.request(**_kwargs)
        response = Response(
            url=str(resp.url),
            body=resp.content,
            status=resp.status_code,
            cookies=resp.cookies,
            headers=resp.headers,
            history=resp.history
        )
        return response


class DownloaderDemoSpider(hoopa.Spider):
    name = "downloader_demo"
    start_urls = ["http://httpbin.org/json"]
    downloader_cls = "downloader_demo3.CloudScraperDownloader"
    log_level = "debug"

    def parse(self, request, response):
        res = requests.get("http://httpbin.org/ip")
        print(res.text)


if __name__ == "__main__":
    DownloaderDemoSpider.start()
