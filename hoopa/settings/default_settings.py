# encoding: utf-8
from hoopa import const
from hoopa.downloadermiddlewares.handle_http_error import HandleHttpErrorMiddleware
from hoopa.downloadermiddlewares.handle_http_success import HandleHttpSuccessMiddleware
from hoopa.downloadermiddlewares.stats import StatsMiddleware
from hoopa.pipelinemiddlewares.default_pipeline import DefaultPipeline
from hoopa.pipelinemiddlewares.handle_process_error import HandleProcessError
from hoopa.spidermiddlewares.handle_parse_error import HandleParseErrorMiddleware

NAME = "hoopa"

# 最大协程数
WORKER_NUMBERS = 1
# 请求间隔, 可以是两个int组成的list，间隔随机取两个数之间的随机浮点数
DOWNLOAD_DELAY = 3
# pending超时时间，超过这个时间，放回waiting
PENDING_THRESHOLD = 100
# 任务完成不停止
RUN_FOREVER = False
INTERRUPT_WITH_ERROR = False
# 失败队列重新爬取
FAILURE_TO_WAITING = False
PUSH_NUMBER = 100


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
# 执行顺序： DOWNLOADER_MIDDLEWARES
DOWNLOADER_MIDDLEWARES = [
]

DOWNLOADER_MIDDLEWARES_BASE = [
    StatsMiddleware,
    HandleHttpErrorMiddleware,
    HandleHttpSuccessMiddleware,
]


# 爬虫中间件
# 执行顺序： DOWNLOADER_MIDDLEWARES
SPIDER_MIDDLEWARES = [
]

SPIDER_MIDDLEWARES_BASE = [
    HandleParseErrorMiddleware
]

# pipelines
# 执行顺序：DOWNLOADER_MIDDLEWARES
PIPELINES = [
]

PIPELINES_BASE = [
    DefaultPipeline,
    HandleProcessError
]


# redis配置信息
# REDIS_SETTING = "redis://127.0.0.1:6379/0?encoding=utf-8"
REDIS_SETTING = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
    'password': ''
}

# 默认去重，不删除去重队列, 将根据queue的类型来决定
DUPEFILTER_CLS = const.MemoryDupeFilter
# 是否删除去重队列
CLEAN_DUPEFILTER = None
# 去重数据库连接配置
DUPEFILTER_SETTING = None

# 统计器, 默认内存
STATS_CLS = const.MemoryStatsCollector

# 其他配置
# 序列化: pickle, ujson, orjson
SERIALIZATION = "ujson"

# 日志配置
LOG_CONFIG = None        # 自定义logger.configure的参数，类型为字典
LOG_LEVEL = "DEBUG"
LOG_WRITE_FILE = False
