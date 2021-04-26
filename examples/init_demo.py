# encoding: utf-8
import hoopa


class FirstSpider(hoopa.Spider):
    name = "first"
    start_urls = ["https://httpbin.org/get"]

    def init(self):
        print(1)

    def parse(self, request, response):
        print(response.text)


if __name__ == "__main__":
    FirstSpider.start()
