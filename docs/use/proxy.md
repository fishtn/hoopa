# 代理ip

代理ip是在中间件设置的，因为有不同的HTTP库，所以设置代理的时候要根据自己使用的下载器来设置

```python
class ProxyMiddleware:
    def process_request(self, request, spider_ins):
        # 判断下载器
        if spider_ins.downloader_cls == const.AiohttpDownloader:
            request.proxy = "http://127.0.0.1:7890"
        else:
            request.proxies = {'https': "http://127.0.0.1:7890", 'http': "http://127.0.0.1:7890"}
```

如果ip是通过接口获取，可以在这里直接使用http请求获取。

```python
class ProxyMiddleware:
    def process_request(self, request, spider_ins):
        # 判断下载器
        if spider_ins.downloader_cls == const.AiohttpDownloader:
            request.proxy = "http://127.0.0.1:7890"
        else:
            request.proxies = {'https': "http://127.0.0.1:7890", 'http': "http://127.0.0.1:7890"}
```