# encoding: utf-8
"""
response对象
"""
import codecs
from dataclasses import dataclass

import typing
from http.cookies import SimpleCookie

import cchardet
import ujson
from aiohttp import ClientSession, helpers
from httpx import Headers, Cookies
from multidict import CIMultiDictProxy
from parsel import Selector


@dataclass
class Response:
    url: str = None
    _body: bytes = b''
    status: int = -1
    headers: typing.Union[CIMultiDictProxy[str], Headers] = None
    cookies: typing.Union[SimpleCookie, Cookies] = None
    session: ClientSession = None  # session
    history: typing.Union[list, tuple] = None
    encoding: str = None

    ok: int = 1  # 请求状态： 1正常；0失败，会进行重试；-1失败，不进行失败，直接进入失败队列
    error_type: int = None  # 错误名称
    debug_msg: str = None  # 调试信息

    _text: str = ''  # 响应体decode
    _selector: Selector = None  # xpath的selector

    def json(self):
        return ujson.loads(self.text)

    @property
    def text(self, errors='ignore'):
        # 如果response设置coding, 返回重新编码的
        if not self._body:
            return None

        if not self.encoding:
            self.encoding = self.get_encoding()

        return self._body.decode(self.encoding, errors=errors)

    @property
    def body(self):
        return self._body

    @property
    def content(self):
        return self._body

    @property
    def selector(self):
        if not self._selector:
            self._selector = Selector(self.text)
        return self._selector

    def xpath(self, xpath_str):
        return self.selector.xpath(xpath_str)

    def re(self, re_str):
        return self.selector.re(re_str)

    def css(self, re_str):
        return self.selector.css(re_str)

    @property
    def response_url(self):
        if self.history:
            last_res_header = self.history[-1].headers
            last_res_url = last_res_header.get("Location", None)

            if not last_res_url:
                last_res_url = last_res_header.get("location", None)

            return last_res_url
        else:
            return self.url

    def serialize(self):
        request_dict = {}
        for item in ["response_url", "status", "body", 'text', 'encoding', "ok", "error_type", "debug_msg"]:
            request_dict.setdefault(item, getattr(self, item))
        return request_dict

    def get_encoding(self) -> str:
        c_type = self.headers.get("Content-Type", "").lower()
        mimetype = helpers.parse_mimetype(c_type)

        encoding = mimetype.parameters.get("charset")
        if encoding:
            try:
                codecs.lookup(encoding)
            except LookupError:
                encoding = None
        if not encoding:
            if mimetype.type == "application" and (
                    mimetype.subtype == "json" or mimetype.subtype == "rdap"
            ):
                # RFC 7159 states that the default encoding is UTF-8.
                # RFC 7483 defines application/rdap+json
                encoding = "utf-8"
            elif self._body is None:
                raise RuntimeError(
                    "Cannot guess the encoding of " "a not yet read body"
                )
            else:
                encoding = cchardet.detect(self._body)["encoding"]
        if not encoding:
            encoding = "utf-8"

        return encoding

    def __repr__(self):
        return f"<Response [{self.status}]>"
