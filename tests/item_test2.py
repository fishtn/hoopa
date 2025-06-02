# encoding: utf-8
from hoopa import Spider


class FirstSpider(Spider):
    name = "first"
    start_urls = ["https://httpbin.org/get"]

    def parse(self, request, response):

        yield [{
            "name": "Jeff",
            "age": 18
        }]

    def process_items(self, items):
        print(items)


if __name__ == "__main__":
    FirstSpider.start()
