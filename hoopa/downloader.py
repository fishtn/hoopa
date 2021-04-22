# encoding: utf-8
"""
下载器
"""

import aiohttp
import httpx
import requests
from aiohttp import TCPConnector

from hoopa.utils.decorators import http_decorator
from hoopa.request import Request
from hoopa.response import Response


class Downloader:
    session = None
    close_session = None

    async def init(self, setting):
        pass

    async def close(self):
        pass

    async def fetch(self, request: Request) -> Response:
        pass

    async def get_session(self, request):
        pass


class AiohttpDownloader(Downloader):
    """
    Aiohttp下载器
    """
    def __init__(self):
        self.tc = None

    async def init(self, http_client_kwargs=None):
        if http_client_kwargs:
            self.session = aiohttp.ClientSession(**http_client_kwargs)
        else:
            jar = aiohttp.DummyCookieJar()
            self.tc = TCPConnector(limit=100, force_close=True, enable_cleanup_closed=True, verify_ssl=False)
            self.session = aiohttp.ClientSession(connector=self.tc, cookie_jar=jar)

        return self

    async def close(self):
        if self.tc:
            await self.tc.close()
        if self.session:
            await self.session.close()

    async def get_session(self, request):
        """
        1. 优先使用request参数的session
        2. client_kwargs参数不为空，新建一个session
        3. 全局session不为空，使用全局session
        4. 新建一个session
        """
        if request.session:
            return request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            self.close_session = True
            return aiohttp.ClientSession(**request.client_kwargs)
        elif self.session:
            return self.session
        else:
            self.close_session = True
            return aiohttp.ClientSession()

    @http_decorator
    async def fetch(self, request: Request) -> Response:
        session = await self.get_session(request)
        _kwargs = request.replace_to_kwargs
        try:
            async with session.request(**_kwargs) as resp:
                response = Response(
                    url=str(resp.url),
                    _body=await resp.read(),
                    status=resp.status,
                    cookies=resp.cookies,
                    headers=resp.headers,
                    history=resp.history,
                )
                return response
        finally:
            if self.close_session:
                await session.close()


class HttpxDownloader(Downloader):
    """
    Httpx下载器
    """
    async def init(self, http_client_kwargs=None):
        if http_client_kwargs:
            self.session = httpx.AsyncClient(**http_client_kwargs)
        else:
            self.session = httpx.AsyncClient(http2=True, verify=False)
        return self

    async def close(self):
        await self.session.aclose()

    @http_decorator
    async def fetch(self, request: Request) -> Response:
        session = await self.get_session(request)
        _kwargs = request.replace_to_kwargs

        try:
            resp = await self.session.request(**_kwargs)
            response = Response(
                url=str(resp.url),
                _body=resp.content,
                status=resp.status_code,
                cookies=resp.cookies,
                headers=resp.headers,
                history=resp.history,
            )
            return response
        finally:
            if self.close_session:
                await session.aclose()

    async def get_session(self, request):
        """
        1. 优先使用request参数的session
        2. client_kwargs参数不为空，新建一个session
        3. 全局session不为空，使用全局session
        4. 新建一个session
        """
        if request.session:
            return request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            self.close_session = True
            return httpx.AsyncClient(**request.client_kwargs)
        elif self.session:
            return self.session
        else:
            self.close_session = True
            return httpx.AsyncClient()


class RequestsDownloader(Downloader):
    """
    Requests下载器
    """
    def init(self, http_client_kwargs):
        if http_client_kwargs:
            self.session = self.create_session(self.session, **http_client_kwargs)
        else:
            self.session = self.create_session()
        return self

    def close(self):
        self.session.close()

    @http_decorator
    def fetch(self, request: Request) -> Response:
        session = self.get_session(request)
        _kwargs = request.replace_to_kwargs

        try:
            resp = self.session.request(**_kwargs)
            response = Response(
                url=str(resp.url),
                _body=resp.content,
                status=resp.status_code,
                cookies=resp.cookies,
                headers=resp.headers,
                history=resp.history
            )
            return response
        finally:
            if self.close_session:
                session.close()

    def get_session(self, request):
        """
        1. 优先使用request参数的session
        2. client_kwargs参数不为空，新建一个session
        3. 全局session不为空，使用全局session
        4. 新建一个session
        """
        if request.session:
            return request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            self.close_session = True
            session = self.create_session(**request.client_kwargs)
            return session
        elif self.session:
            return self.session
        else:
            return self.create_session()

    def create_session(self, session=None, **kwargs):
        if session is None:
            session = requests.Session()
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        return session
