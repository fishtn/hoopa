# encoding: utf-8
"""
response对象
"""
import codecs
from dataclasses import dataclass

import cchardet
import ujson
from aiohttp import helpers
from parsel import Selector

from hoopa.utils.url import get_location_from_history


@dataclass
class Response:
    def __init__(
        self,
        url: str = "",
        *,
        encoding: str = "",
        cookies=None,
        history=None,
        headers=None,
        status: int = -1,
        body: bytes = b'',
        text: str = "",
    ):
        self._url = url
        self._encoding = encoding
        self._headers = headers
        self._cookies = cookies
        self._history = history
        self._status = status

        self._body = body
        self._text = text

        self._error_type: str = ""  # 错误名称
        self._debug_msg: str = ""  # 调试信息

        self._ok: int = 1  # 请求状态： 1成功；0失败，会进行重试；-1失败，不进行失败，直接进入失败队列

    @property
    def url(self):
        return self._url

    @property
    def encoding(self):
        return self._encoding

    @property
    def content(self):
        return self._body

    @property
    def text(self, errors='ignore'):
        if self._text:
            return self._text

        if not self._body:
            return None

        if not self._encoding:
            self._encoding = self.get_encoding()

        return self._body.decode(self._encoding, errors=errors)

    @text.setter
    def text(self, value: str):
        self._text = value

    def json(self):
        return ujson.loads(self.text)

    @property
    def ok(self):
        return self._ok

    @ok.setter
    def ok(self, value: int):
        self._ok = value

    @property
    def error_type(self):
        return self._error_type

    @error_type.setter
    def error_type(self, value: str):
        self._error_type = value

    @property
    def debug_msg(self):
        return self._debug_msg

    @debug_msg.setter
    def debug_msg(self, value: str):
        self._debug_msg = value

    @property
    def headers(self):
        return self._headers

    @property
    def cookies(self):
        return self._cookies

    @property
    def history(self):
        return self._history

    @property
    def status(self):
        return self._status

    @property
    def selector(self):
        return Selector(self.text)

    def xpath(self, xpath_str):
        return self.selector.xpath(xpath_str)

    def re(self, re_str):
        return self.selector.re(re_str)

    def css(self, re_str):
        return self.selector.css(re_str)

    def serialize(self):
        request_dict = {}
        for item in ["url", "status", "body", 'text', 'encoding', "ok", "error_type", "debug_msg"]:
            request_dict.setdefault(item, getattr(self, item))
        return request_dict

    def get_encoding(self) -> str:
        c_type = self._headers.get("Content-Type", "").lower()
        mimetype = helpers.parse_mimetype(c_type)

        encoding = mimetype.parameters.get("charset")
        if encoding:
            try:
                codecs.lookup(encoding)
            except LookupError:
                encoding = None
        if not encoding:
            if mimetype.type == "application" and (mimetype.subtype == "json" or mimetype.subtype == "rdap"):
                encoding = "utf-8"
            elif self._body is None:
                raise RuntimeError("Cannot guess the encoding of " "a not yet read body")
            else:
                encoding = cchardet.detect(self._body)["encoding"]
        if not encoding:
            encoding = "utf-8"

        return encoding

    @property
    def response_url(self):
        if self._history:
            last_res_url = get_location_from_history(self._history)
            return last_res_url
        else:
            return self.url

    def __repr__(self):
        return f"<Response [{self._status}]>"
