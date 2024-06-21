# encoding: utf-8
import hoopa


class FirstSpider(hoopa.Spider):
    name = "first"
    start_urls = ["https://httpbin.org/get"]

    async def open_spider(self):
        print('open spider')

    def parse(self, request, response):
        print(response.text)

    async def close_spider(self, spider_stats):
        print('close spider')
        print(spider_stats)


if __name__ == "__main__":
    FirstSpider.start()
