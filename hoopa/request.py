# encoding: utf-8
"""
request对象
"""

from types import SimpleNamespace
from typing import (Any, Iterable, Mapping, Optional, Union, Callable)

from aiohttp import ClientTimeout
from aiohttp.helpers import (BasicAuth, sentinel)
from aiohttp.client_reqrep import Fingerprint
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders

from httpx._types import (AuthTypes, CookieTypes, HeaderTypes, QueryParamTypes, RequestContent, RequestData,
                          RequestFiles, TimeoutTypes, URLTypes,)
from httpx._config import (UNSET, UnsetType)
from loguru import logger

from w3lib.url import add_or_replace_parameters, canonicalize_url

try:
    from ssl import SSLContext
except ImportError:  # pragma: no cover
    SSLContext = object  # type: ignore

from hoopa.utils import helpers
from hoopa.utils.serialization import loads, dumps


not_serialize_params = ["session", "message", 'http_kwargs', "retries"]

serialize_params = ['url', 'headers', 'method', 'params', 'data', 'json', 'meta', 'dont_filter', 'priority',
                    'callback', 'client_kwargs', 'http_kwargs']

not_kwargs_list = ["session", "message", "callback", "dont_filter", "meta", "priority",
                   "client_kwargs", "http_kwargs", "retries", "retry_times", "retry_delay"]


class AiohttpParams:
    method: str = None
    url: StrOrURL = None
    params: Optional[Mapping[str, str]] = None
    data: Any = None
    json: Any = None
    cookies: Optional[LooseCookies] = None
    headers: Optional[LooseHeaders] = None
    skip_auto_headers: Optional[Iterable[str]] = None
    auth: Optional[BasicAuth] = None
    allow_redirects: bool = True
    max_redirects: int = 10
    compress: Optional[str] = None
    chunked: Optional[bool] = None
    expect100: bool = False
    raise_for_status: Optional[bool] = None
    read_until_eof: bool = True
    proxy: Optional[StrOrURL] = None
    proxy_auth: Optional[BasicAuth] = None
    timeout: Union[ClientTimeout, object] = sentinel
    verify_ssl: Optional[bool] = None
    fingerprint: Optional[bytes] = None
    ssl_context: Optional[SSLContext] = None
    ssl: Optional[Union[SSLContext, bool, Fingerprint]] = None
    proxy_headers: Optional[LooseHeaders] = None
    trace_request_ctx: Optional[SimpleNamespace] = None
    read_bufsize: Optional[int] = None


class HttpxParams:
    method: str = None
    url: URLTypes = None
    content: RequestContent = None
    data: RequestData = None
    files: RequestFiles = None
    json: Any = None
    params: QueryParamTypes = None
    headers: HeaderTypes = None
    cookies: CookieTypes = None
    auth: Union[AuthTypes, UnsetType] = UNSET
    allow_redirects: bool = True
    timeout: Union[TimeoutTypes, UnsetType] = UNSET


class RequestParams:
    method = None
    url = None
    params = None
    data = None
    headers = None
    cookies = None
    files = None
    auth = None
    timeout = None
    allow_redirects = True
    proxies = None
    hooks = None
    stream = None
    verify = None
    cert = None
    json = None


class OtherParams:
    # rabbitmq的message
    message = None
    # session参数， http请求的session
    session = None
    # 重试次数
    retry_times = 3
    # 重试时的间隔
    retry_delay = 0

    http_kwargs = None


class Request(AiohttpParams, HttpxParams, RequestParams, OtherParams):
    def __init__(
            self,
            url,
            method='get',
            headers=None,
            params=None,
            data=None,
            json=None,
            cookies=None,
            timeout=10,
            allow_redirects=True,
            callback=None,
            meta=None,
            dont_filter=False,
            priority=0,
            retry_times=3,
            retry_delay=1,
            client_kwargs=None,
            **_http_kwargs
    ):
        self.url = url
        self.headers = headers
        self.method = method
        self.params = params
        self.data = data
        self.json = json
        self.allow_redirects = allow_redirects
        self.cookies = cookies
        self.timeout = timeout

        # 其他参数
        for key, value in _http_kwargs.items():
            self.set(key, value)

        self.meta = meta

        # 默认为False，去重
        self.dont_filter = dont_filter

        # 优先级，越大优先级越大
        self.priority = priority

        # callback支持两种方式传入，可是函数名，也可以是函数，最终存储的是函数名字符串
        self.callback = callback if not callback or isinstance(callback, str) else callback.__name__

        self.client_kwargs = client_kwargs if client_kwargs else {}

        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.retries = 0

    def __getitem__(self, item):
        return getattr(self, item)

    def set(self, name, value):
        setattr(self, name, value)

    @staticmethod
    def unserialize(data_str, module=None):
        data = loads(data_str, module)
        http_kwargs = data.pop("http_kwargs")
        _request = Request(**data)
        for k, v in http_kwargs.items():
            _request.set(k, v)
        return _request

    def serialize(self, module=None):
        request_dict = {}
        _http_kwargs = {}
        for name, value in vars(self).items():
            if name not in not_serialize_params:
                # 不在request参数里面的参数都设置到http_kwargs
                if name in serialize_params:
                    request_dict.setdefault(name, value)
                else:
                    _http_kwargs[name] = value
        request_dict["http_kwargs"] = _http_kwargs
        return dumps(request_dict, module)

    def copy(self):
        kwargs = vars(self)
        cls = kwargs.pop('cls', self.__class__)
        return cls(**kwargs)

    @property
    def replace_to_kwargs(self):
        """
        生成请求参数
        @return:
        """
        _kwargs = {}
        for name, value in vars(self).items():
            if value is not None and name not in not_kwargs_list:
                # 不在not_kwargs_list里面的参数都设置到http_kwargs
                _kwargs.setdefault(name, value)

        # 把params字典的值统一转为str类型
        _params = _kwargs.get("params", None)
        if _params:
            _new_params = {}
            for k, v in _params.items():
                _new_params[k] = str(v)
            _kwargs["params"] = _new_params
        return _kwargs

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
        return f"<Request p{self.priority} {self.method} {self.request_url}>"
