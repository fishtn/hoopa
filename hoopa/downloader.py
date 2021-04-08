# encoding: utf-8
"""
下载器
"""

import aiohttp
import httpx
from aiohttp import TCPConnector

from hoopa.utils.decorators import http_decorator
from hoopa.request import Request
from hoopa.response import Response


class Downloader:
    async def init(self, setting):
        pass

    async def close(self):
        pass

    async def download(self, request: Request) -> Response:
        pass

    async def fetch(self, request: Request) -> Response:
        pass

    async def request(self, request: Request, global_session=False) -> Response:
        if global_session:
            # 全局session
            response = await self.fetch(request)
        else:
            # 一个请求一个session
            response = await self.download(request)
        return response


class AiohttpDownloader(Downloader):
    """
    Aiohttp下载器
    """
    def __init__(self):
        self.tc = None
        self.session = None
        self.session_flag = False

    async def init(self, setting):
        if setting["HTTP_CLIENT_KWARGS"]:
            self.session = aiohttp.ClientSession(**setting["HTTP_CLIENT_KWARGS"])
        else:
            jar = aiohttp.DummyCookieJar()
            self.tc = TCPConnector(limit=500, force_close=True, enable_cleanup_closed=True, verify_ssl=False)
            self.session = aiohttp.ClientSession(connector=self.tc, cookie_jar=jar)

        return self.session

    async def close(self):
        if self.tc:
            await self.tc.close()
        if self.session:
            await self.session.close()

    @http_decorator
    async def download(self, request: Request) -> Response:
        _kwargs = request.replace_to_kwargs
        client_kwargs = _kwargs.pop("client_kwargs", {})
        async with aiohttp.ClientSession(**client_kwargs) as client:
            resp = await client.request(**_kwargs)
            try:
                resp_text = await resp.text()
            except UnicodeDecodeError:
                resp_text = None

        response = Response(
            url=str(resp.url),
            _body=await resp.read(),
            _text=resp_text,
            status=resp.status,
            cookies=resp.cookies,
            headers=resp.headers,
            history=resp.history,
        )

        return response

    @http_decorator
    async def fetch(self, request: Request) -> Response:
        _kwargs = request.replace_to_kwargs
        async with self.session.request(**_kwargs) as resp:
            try:
                resp_text = await resp.text()
            except UnicodeDecodeError:
                resp_text = None

        response = Response(
            url=str(resp.url),
            _body=await resp.read(),
            _text=resp_text,
            status=resp.status,
            cookies=resp.cookies,
            headers=resp.headers,
            history=resp.history,
        )

        return response


class HttpxDownloader(Downloader):
    """
    Httpx下载器
    """
    def __init__(self):
        self.session = None

    async def init(self, setting):

        if setting["HTTP_CLIENT_KWARGS"]:
            self.session = httpx.AsyncClient(**setting["HTTP_CLIENT_KWARGS"])
        else:
            self.session = httpx.AsyncClient(http2=True, verify=False)
        return self.session

    async def close(self):
        pass

    @http_decorator
    async def download(self, request: Request) -> Response:
        _kwargs = request.replace_to_kwargs
        client_kwargs = _kwargs.pop("client_kwargs", {})
        async with httpx.AsyncClient(**client_kwargs) as client:
            resp = await client.request(**_kwargs)

            try:
                resp_text = resp.text
            except UnicodeDecodeError:
                resp_text = None

        response = Response(
            url=str(resp.url),
            _body=resp.content,
            _text=resp_text,
            status=resp.status_code,
            cookies=resp.cookies,
            headers=resp.headers,
            history=resp.history,
        )

        return response

    @http_decorator
    async def fetch(self, request: Request) -> Response:
        _kwargs = request.replace_to_kwargs
        resp = await self.session.request(**_kwargs)

        try:
            resp_text = resp.text
        except UnicodeDecodeError:
            resp_text = None

        response = Response(
            url=str(resp.url),
            _body=resp.content,
            _text=resp_text,
            status=resp.status_code,
            cookies=resp.cookies,
            headers=resp.headers,
            history=resp.history,
        )

        return response
