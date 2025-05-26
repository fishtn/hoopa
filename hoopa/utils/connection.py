from urllib.parse import urlparse
from contextlib import asynccontextmanager

from redis import asyncio as aioredis


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
    encoding = kwargs.pop('encoding', "utf-8")

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
    if isinstance(redis_setting, dict):
        # 直接使用字典参数创建连接
        return aioredis.Redis(
            host=redis_setting.get("host", "localhost"),
            port=redis_setting.get("port", 6379),
            db=redis_setting.get("db", 0),
            password=redis_setting.get("password"),
            encoding=redis_setting.get("encoding", "utf-8"),
            decode_responses=True
        )
    else:
        # 使用 URI 创建连接
        return aioredis.from_url(redis_setting, decode_responses=True)


@asynccontextmanager
async def get_redis_connection(pool):
    """
    从连接池获取 Redis 连接的上下文管理器
    @param pool: Redis 连接池
    @return: Redis 连接
    """
    redis_client = aioredis.Redis(connection_pool=pool)
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


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
