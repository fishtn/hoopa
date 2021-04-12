# encoding: utf-8
"""
request对象
"""

from collections.abc import Coroutine

from w3lib.url import add_or_replace_parameters, canonicalize_url

from dataclasses import dataclass

from hoopa.utils import helpers
from hoopa.utils.serialization import loads, dumps


not_serialize_params = ["session", "message", "request_config", "retry_times", '_http_kwargs']
serialize_params = ['url', 'headers', 'method', 'params', 'data', 'json', 'meta', 'dont_filter', 'priority',
                    'callback', 'client_kwargs', 'http_kwargs']
not_kwargs_list = ["session", "message", "callback", "dont_filter", "meta", "priority", "retry_times",
                   "request_config", "client_kwargs", "_http_kwargs"]


@dataclass
class Request:
    # Default config
    REQUEST_CONFIG = {
        "RETRIES": 3,  # 重试次数
        "RETRY_DELAY": 0,  # 重试间隔
        "HTTP_LOG": True,  # 请求的日志是否打印
        "RETRY_FUNC": Coroutine,  # 重试之前的函数调用
    }

    def __init__(self, url, callback=None, method='get', headers=None, params=None,
                 data=None, json=None, meta=None, dont_filter=False, priority=0,
                 request_config=None, session=None, client_kwargs=None, **_http_kwargs):
        self.url = url
        self.headers = headers
        self.method = method
        self.params = params
        self.data = data
        self.json = json
        self.meta = meta

        # 不去重，默认为False，去重
        self.dont_filter = dont_filter
        # 优先级，越大优先级越大
        self.priority = priority
        # callback支持两种方式传入，可是函数名，也可以是函数，最终存储的是函数名字符串

        if not callback or isinstance(callback, str):
            self.callback = callback
        else:
            self.callback = callback.__name__

        self.client_kwargs = client_kwargs if client_kwargs else {}
        # 其他参数
        self._http_kwargs = _http_kwargs

        # session参数， http请求的session
        self.session = session

        self.request_config = (self.REQUEST_CONFIG if request_config is None else request_config)
        self.retry_times = self.request_config.get("RETRIES", 3)

        # rabbitmq的message
        self.message = None

    def __getitem__(self, item):
        return getattr(self, item)

    def set(self, name, value):
        """
        可用于设置属性
        """
        setattr(self, name, value)

    @staticmethod
    def unserialize(data_str, module=None):
        data = loads(data_str, module)
        url = data.pop("url")
        _request = Request(url)
        for k, v in data.items():
            setattr(_request, k, v)
        return _request

    def serialize(self, module=None):
        request_dict = {}
        _http_kwargs = self._http_kwargs
        for name, value in vars(self).items():
            if name not in not_serialize_params:
                # 不在request参数里面的参数都设置到http_kwargs
                if name in serialize_params:
                    request_dict.setdefault(name, value)
                else:
                    _http_kwargs[name] = value
        request_dict["http_kwargs"] = _http_kwargs
        return dumps(request_dict, module)

    def replace(self, *args, **kwargs):
        for x in ['url', 'method', 'params', 'data', 'json', 'meta', 'callback', 'dont_filter', 'priority']:
            kwargs.setdefault(x, getattr(self, x))
        cls = kwargs.pop('cls', self.__class__)
        return cls(*args, **kwargs)

    @property
    def replace_to_kwargs(self):
        """
        生成请求包需要的参数
        @return:
        """
        # http参数需要去除的字段
        http_kwargs = self._http_kwargs
        _kwargs = {}
        for name, value in vars(self).items():
            if value is not None and name not in not_kwargs_list:
                # 不在request参数里面的参数都设置到http_kwargs
                if name in serialize_params:
                    _kwargs.setdefault(name, value)
                else:
                    http_kwargs[name] = value

        # 将http_kwargs里面的参数都设置为http请求的参数
        _kwargs = {**_kwargs, **http_kwargs}
        # 把params字典的值统一转为str类型
        _params = _kwargs.get("params", {})
        _new_params = {}
        for k, v in _params.items():
            _new_params[k] = str(v)
        _kwargs["params"] = _new_params

        return _kwargs

    @property
    def http_kwargs(self):
        _http_kwargs = self._http_kwargs
        for name, value in vars(self).items():
            if name not in serialize_params and name not in not_kwargs_list:
                # 不在request参数里面的参数都设置到http_kwargs
                _http_kwargs[name] = value
        return _http_kwargs

    @property
    def fp(self):
        return helpers.request_fingerprint(self)

    @property
    def request_url(self):
        _url = self.url
        if self.params:
            _url = add_or_replace_parameters(self.url, self.params)

        return canonicalize_url(_url)

    def __repr__(self):
        return f"<{self.method} {self.request_url}>"


