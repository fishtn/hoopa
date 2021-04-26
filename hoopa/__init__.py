import os, sys
import re


sys.path.insert(0, re.sub(r"([\\/]items)|([\\/]spiders)", "", os.getcwd()))

__all__ = [
    "Spider",
    "Item",
    "Middleware",
    "Request",
    "Response",
    "helpers",
    "const",
    "Logging",
    "Setting",
    "AiohttpDownloader",
    "HttpxDownloader",
    "AiohttpRequest",
    "AiohttpClient",
    "HttpxRequest",
    "HttpxClient",
]

from hoopa.spider import Spider
from hoopa.item import Item
from hoopa.middleware import Middleware
from hoopa.request import Request
from hoopa.response import Response
from hoopa.utils import helpers
from hoopa.settings import const
from hoopa.utils.http_params import AiohttpRequest, AiohttpClient, HttpxRequest, HttpxClient
from hoopa.utils.log import Logging
from hoopa.utils.project import Setting
from hoopa.downloader import AiohttpDownloader, HttpxDownloader

__version__ = "0.0.8"
