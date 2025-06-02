# hoopa

## 简介

**hoopa** 是一个轻量、快速的异步分布式爬虫框架

- 支持内存、redis 的优先级队列
- 支持 aiohttp、 httpx、requests 等 HTTP 库
- 支持断点续传

兼容同步和异步代码，不习惯异步的，可以使用同步写，但是要注意的是不能在异步方法里面进行阻塞的操作

> 自用框架，不保证稳定性，请勿用于生产环境

文档地址：https://fishtn.github.io/hoopa/

## 环境要求：

- Python 3.7.0+
- Works on Linux, Windows, macOS

## 安装

```shell
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

然后添加 url：http://httpbin.org/get

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

- [Tinepeas](https://github.com/kingname/Tinepeas)
- [ruia](https://github.com/howie6879/ruia)
- [feapder](https://github.com/Boris-code/feapder)
- [scrapy](https://github.com/scrapy/scrapy)
- [starlette](https://github.com/encode/starlette)
