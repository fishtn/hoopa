# encoding: utf-8
from hoopa import Spider


class FirstSpider(Spider):
    name = "first"
    start_urls = ["https://httpbin.org/get"]

    def parse(self, request, response):

        yield {
            "name": "Jeff",
            "age": 18
        }

    def process_item(self, item):
        print(item)


if __name__ == "__main__":
    FirstSpider.start()
