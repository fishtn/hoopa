# encoding: utf-8
import hoopa


class FirstSpider(hoopa.Spider):
    name = "demo"
    start_urls = ["https://httpbin.org/get"]
    log_level = "debug"

    async def parse(self, request, response):
        print(response.text)


if __name__ == "__main__":
    FirstSpider.start()
