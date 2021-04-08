# encoding: utf-8
import asyncio
import hashlib
import random
import uuid
from importlib import import_module

import arrow


def get_md5(data):
    return hashlib.md5(data.encode(encoding='UTF-8')).hexdigest()


def get_timestamp():
    return arrow.now().float_timestamp


def get_datetime(fmt="YYYY-MM-DD HH:MM:SS"):
    return arrow.now().format(fmt)


def split_list(seq, step):
    return [seq[i:i+step] for i in range(0, len(seq), step)]


def load_object(path):
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError("Error loading object '%s': not a full path" % path)

    module, name = path[:dot], path[dot + 1:]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError("Module '%s' doesn't define any object named '%s'" % (module, name))

    return obj


async def get_cls(path, setting):
    _cls = load_object(path)
    obj = _cls()
    await obj.init(setting)
    return obj


def request_fingerprint(request):
    fp = hashlib.md5()
    fp.update(to_bytes(request.method))
    fp.update(to_bytes(request.request_url))
    fp.update(to_bytes(str(request.data)) or b'')
    fp.update(to_bytes(str(request.json)) or b'')

    return fp.hexdigest()


async def spider_sleep(download_delay):
    """
    执行休眠
    @return:
    """
    # 休眠间隔, 加入随机值选项
    if isinstance(download_delay, list):
        download_delay = random.uniform(download_delay[0], download_delay[1])
    else:
        download_delay = download_delay

    await asyncio.sleep(download_delay)


def to_str(bytes_or_str, encoding="utf-8", errors='strict'):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode(encoding, errors)
    else:
        value = bytes_or_str
    return value


def to_bytes(bytes_or_str, encoding="utf-8", errors='strict'):
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode(encoding, errors)
    else:
        value = bytes_or_str
    return value


def get_uuid():
    return str(uuid.uuid4())

