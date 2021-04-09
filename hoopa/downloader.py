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
    downloader_global_session = None
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

    async def init(self, setting):
        self.downloader_global_session = setting["DOWNLOADER_GLOBAL_SESSION"]
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

    async def get_session(self, request):
        """
        优先使用request参数的session
        client_kwargs不为空时，自己生成
        默认使用全局session
        """
        if request.session:
            return request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            self.close_session = True
            return aiohttp.ClientSession(**request.client_kwargs)
        else:
            return self.session

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
    async def init(self, setting):
        if setting["HTTP_CLIENT_KWARGS"]:
            self.session = httpx.AsyncClient(**setting["HTTP_CLIENT_KWARGS"])
        else:
            self.session = httpx.AsyncClient(http2=True, verify=False)
        return self.session

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
        优先使用request参数的session
        client_kwargs不为空时，自己生成
        默认使用全局session
        """
        if request.session:
            return request.session
        elif request.client_kwargs:
            # 单个请求创建的会话需要使用后关闭
            self.close_session = True
            return httpx.AsyncClient(**request.client_kwargs)
        else:
            return self.session


