# hoopa


## 简介

**hoopa** 是一个轻量、快速的异步分布式爬虫框架

- 支持基于内存、redis、rabbitmq的优先级队列
- 支持aiohttp、 httpx、requests等HTTP库
- 支持断点续传

> 项目还在开发测试中，请勿用于生产环境，若发现问题，欢迎提issue


文档地址：https://fishtn.github.io/hoopa/


## 环境要求：

- Python 3.7.0+
- Works on Linux, Windows, macOS

## 安装
``` shell
# For Linux & Mac
pip install -U hoopa[uvloop]

# For Windows
pip install -U hoopa
```

## 开始

创建爬虫

```shell
hoopa create -s first_spider
```

然后添加url：http://httpbin.org/get

```python

import hoopa


class FirstSpider(hoopa.Spider):
    name = "first"
    start_urls = ["http://httpbin.org/get"]

    def parse(self, request, response):
        print(response)


if __name__ == "__main__":
    FirstSpider.start()
        
```

## todo
- [ ] 监控平台
- [ ] 远程部署
- [ ] 任务调度


## 感谢

-   [Tinepeas](https://github.com/kingname/Tinepeas)
-   [ruia](https://github.com/howie6879/ruia)
-   [feapder](https://github.com/Boris-code/feapder)
-   [scrapy](https://github.com/scrapy/scrapy)
-   [starlette](https://github.com/encode/starlette)
