# encoding: utf-8
"""
下载器
"""

import aiohttp
import httpx
import requests
from aiohttp import TCPConnector

from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils.concurrency import run_function


class Downloader:
    """
    下载器基础类，子类需要实现：init, close, get_session, fetch
    同步调用：fetch
    """
    session = None

    def __init__(self, http_client_kwargs, engine):
        self.http_client_kwargs = http_client_kwargs
        self.engine = engine

    @classmethod
    async def create(cls, engine):
        http_client_kwargs = engine.setting["HTTP_CLIENT_KWARGS"]
        return cls(http_client_kwargs, engine)

    async def close(self):
        pass

    async def get_session(self, request):
        """
        1. 优先使用request参数的session
        2. client_kwargs参数不为空，新建一个session
        3. 全局session不为空，使用全局session
        4. 新建一个session，提供给单次下载
        """
        pass

    def fetch(self, request: Request) -> Response:
        """
        同步请求
        @param request:
        @return: Response
        """
        pass


class AiohttpDownloader(Downloader):
    """
    Aiohttp下载器
    """
    tc = None

    async def init(self):
        if self.http_client_kwargs:
            self.session = aiohttp.ClientSession(**self.http_client_kwargs)
        else:
            jar = aiohttp.DummyCookieJar()
            self.tc = TCPConnector(limit=100, force_close=True, enable_cleanup_closed=True, verify_ssl=False)
            self.session = aiohttp.ClientSession(connector=self.tc, cookie_jar=jar)

    async def close(self):
        if self.tc:
            await self.tc.close()
        if self.session:
            await self.session.close()

    async def get_session(self, request):
        """
        1. 优先使用request参数的session
        2. client_kwargs参数不为空，新建一个session
        3. 使用全局session
        """
        is_close = False
        if request.session:
            session = request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            is_close = True
            session = aiohttp.ClientSession(**request.client_kwargs)
        else:
            session = self.session
        return session, is_close

    async def fetch(self, request: Request) -> Response:
        session, is_close = await self.get_session(request)
        _kwargs = request.replace_to_kwargs
        try:
            async with session.request(**_kwargs) as resp:
                response = Response(
                    url=str(resp.url),
                    body=await resp.read(),
                    status=resp.status,
                    cookies=resp.cookies,
                    headers=resp.headers,
                    history=resp.history,
                )
                return response
        finally:
            if is_close:
                await session.close()


class HttpxDownloader(Downloader):
    """
    Httpx下载器
    """

    async def init(self):
        if self.http_client_kwargs:
            self.session = httpx.AsyncClient(**self.http_client_kwargs)
        else:
            self.session = httpx.AsyncClient(http2=True, verify=False)

    async def close(self):
        await self.session.aclose()

    async def fetch(self, request: Request) -> Response:
        session, is_close = await self.get_session(request)
        _kwargs = request.replace_to_kwargs
        _kwargs.pop('allow_redirects')
        try:
            resp = await self.session.request(**_kwargs)
            response = Response(
                url=str(resp.url),
                body=resp.content,
                status=resp.status_code,
                cookies=resp.cookies,
                headers=resp.headers,
                history=resp.history,
            )
            return response
        finally:
            if is_close:
                await session.aclose()

    async def get_session(self, request):
        is_close = False
        if request.session:
            session = request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            is_close = True
            session = httpx.AsyncClient(**request.client_kwargs)
        else:
            session = self.session

        return session, is_close


class RequestsDownloader(Downloader):
    """
    Requests下载器
    """

    def init(self):
        session = requests.Session()
        if self.http_client_kwargs:
            self.session = self.set_session(session, **self.http_client_kwargs)
        else:
            self.session = self.set_session(session)

    def close(self):
        self.session.close()

    async def fetch(self, request: Request) -> Response:
        return await run_function(self.sync_fetch, request)

    def sync_fetch(self, request: Request) -> Response:
        session, is_close = self.get_session(request)
        _kwargs = request.replace_to_kwargs

        try:
            resp = self.session.request(**_kwargs)
            response = Response(
                url=str(resp.url),
                body=resp.content,
                status=resp.status_code,
                cookies=resp.cookies,
                headers=resp.headers,
                history=resp.history
            )
            return response
        finally:
            if is_close:
                session.close()

    def get_session(self, request):
        is_close = False
        if request.session:
            session = request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            session = requests.Session()
            session = self.set_session(session, **request.client_kwargs)
        else:
            session = requests.Session()
        return session, is_close

    @staticmethod
    def set_session(session, **kwargs):
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        return session
