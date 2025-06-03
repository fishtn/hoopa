# encoding: utf-8
import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hoopa import Spider


class FirstSpider(Spider):
    name = "first"
    start_urls = ["https://httpbin.org/get"]
    log_level = "DEBUG"

    def parse(self, request, response):
        print("parse")
        yield [{
            "name": "Jeff",
            "age": 18
        }]


    def process_item(self, items):

        for item in items:
            # 注意：这里 item 是字典，不是对象

            print(item.name)  # 使用字典访问方式
            
            print(item.age)


if __name__ == "__main__":
    FirstSpider.start()
