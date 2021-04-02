from urllib.parse import urlparse

import aioredis


def get_redis_uri_from_dict(**kwargs):
    """
    将redis连接字典转成uri
    @param kwargs: 参数字典，仅含host, port, db, password, encoding
    @return:
    """
    host = kwargs.pop('host', None)
    port = kwargs.pop('port', None)
    db = kwargs.pop('db', None)
    password = kwargs.pop('password', None)
    encoding = kwargs.pop('encoding', None)

    if password:
        uri = f"redis://:{password}@{host}:{port}/{db}?encoding={encoding}"
    else:
        uri = f"redis://{host}:{port}/{db}?encoding={encoding}"

    return uri


async def get_aio_redis(redis_setting):
    """
    创建aioredis连接池
    @param redis_setting: redis配置dict或者uri
    @return:
    """
    uri = redis_setting
    if isinstance(redis_setting, dict):
        uri = get_redis_uri_from_dict(**redis_setting)
    return await aioredis.create_redis_pool(uri)


def get_host(redis_setting):
    """
    从redis配置字典和uri获取host
    @param redis_setting:
    @return:
    """
    if isinstance(redis_setting, dict):
        return redis_setting["host"]
    else:
        return urlparse(redis_setting).hostname
