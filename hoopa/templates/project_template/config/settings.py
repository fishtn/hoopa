# encoding: utf-8
from hoopa import const
from hoopa.downloadermiddlewares.stats import StatsMiddleware
from .middlewares.common_middleware import CommonMiddleware

NAME = "hoopa"

# 最大协程数
WORKER_NUMBERS = 1
# 请求间隔, 可以是两个int组成的list，间隔随机取两个数之间的随机浮点数
DOWNLOAD_DELAY = 3
# pending超时时间，超过这个时间，放回waiting
PENDING_THRESHOLD = 100
# 任务完成不停止
RUN_FOREVER = False

# 队列
# 调度器队列，默认redis, memory, mq
QUEUE_CLS = const.MemoryQueue
# 删除队列（包括数据集，去重队列）
CLEAN_QUEUE = False
# 指定优先级，仅当队列为redis有用
PRIORITY = None

# 下载器aiohttp httpx
DOWNLOADER_CLS = const.AiohttpDownloader
HTTP_CLIENT_KWARGS = None

# 下载中间件
MIDDLEWARES = [
    CommonMiddleware,
    StatsMiddleware
]

# 默认去重，不删除去重队列, 将根据queue的类型来决定
DUPEFILTER_CLS = None
# 是否删除去重队列
CLEAN_DUPEFILTER = None
# 去重数据库连接配置
DUPEFILTER_SETTING = None

# 统计器
STATS_CLS = const.MemoryStatsCollector

# redis配置信息
# REDIS_SETTING = "redis://127.0.0.1:6379/0?encoding=utf-8"
REDIS_SETTING = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
    'password': ''
}

# MQ
MQ_MAXSIZE = 10
MQ_URI = "amqp://guest:guest@127.0.0.1/"
MQ_API_PORT = 15672


# 其他配置
# 序列化: pickle, ujson, orjson
SERIALIZATION = "ujson"

# 日志配置
LOG_LEVEL = "INFO"
LOG_WRITE_FILE = False
