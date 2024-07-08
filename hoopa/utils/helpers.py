# encoding: utf-8
import asyncio
import hashlib
import os
import random
import uuid
from asyncio import iscoroutinefunction
from importlib import import_module

import arrow

from hoopa.utils.concurrency import run_function_no_concurrency


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


async def create_instance(objcls, *args, **kwargs):
    if hasattr(objcls, 'create'):
        instance = await run_function_no_concurrency(objcls.create, *args, **kwargs)
    else:
        instance = objcls()
    return instance


async def create_instance_and_init(objcls, engine, *args, **kwargs):
    instance = await create_instance(objcls, engine, *args, **kwargs)
    if hasattr(instance, 'init'):
        if instance.init.__code__.co_argcount == 1:
            await run_function_no_concurrency(instance.init)
        else:
            await run_function_no_concurrency(instance.init, engine.spider)

    return instance


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
    if isinstance(download_delay, (list, tuple)):
        download_delay = random.uniform(download_delay[0], download_delay[1])
    else:
        download_delay = download_delay

    await asyncio.sleep(max(download_delay, 0.01))


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


def get_continue_list(p_list):
    # 去重排序
    seq = sorted(list(set(p_list)))
    result_seq = []
    tmp = None
    tmp_list = []
    for i in seq:
        if tmp is None:
            tmp_list.append(i)
        elif i - tmp == 1:
            tmp_list.append(i)
        else:
            result_seq.append(tmp_list)
            tmp_list = [i]

        tmp = i
    if tmp_list:
        result_seq.append(tmp_list)
    return result_seq


def get_priority_list(p_list):
    continue_list = get_continue_list(p_list)
    priority_list = []

    for item in continue_list:
        priority_list.append((item[0], item[-1]))

    return priority_list


def get_mac_address():
    node = uuid.getnode()
    mac = uuid.UUID(int=node).hex[-12:]
    return mac


def get_pid():
    return os.getpid()


def get_mac_pid():
    mac = get_mac_address()
    pid = get_pid()
    return f"{mac}#{pid}"
