
# Downloader:
import json

AiohttpDownloader = "hoopa.downloader.AiohttpDownloader"
HttpxDownloader = "hoopa.downloader.HttpxDownloader"
RequestsDownloader = "hoopa.downloader.RequestsDownloader"

# SchedulerQueue:
RedisQueue = "hoopa.queues.RedisQueue"
MemoryQueue = "hoopa.queues.MemoryQueue"
RabbitMQQueue = "hoopa.queues.RabbitMQQueue"

# Dupefilter:
RedisDupeFilter = "hoopa.dupefilters.RedisDupeFilter"
MemoryDupeFilter = "hoopa.dupefilters.MemoryDupeFilter"

# StatsCollector
MemoryStatsCollector = "hoopa.statscollectors.MemoryStatsCollector"  # memory
DummyStatsCollector = "hoopa.statscollectors.DummyStatsCollector"  # 假的，不进行统计
RedisStatsCollector = "hoopa.statscollectors.RedisStatsCollector"  # redis


const_map = {
    "hoopa.downloader.AiohttpDownloader": "AiohttpDownloader",
    "hoopa.downloader.HttpxDownloader": "HttpxDownloader",
    "hoopa.queues.RedisQueue": "RedisQueue",
    "hoopa.queues.MemoryQueue": "MemoryQueue",
    "hoopa.queues.RabbitMQQueue": "RabbitMQQueue",
    "hoopa.dupefilters.RedisDupeFilter": "RedisDupeFilter",
    "hoopa.dupefilters.MemoryDupeFilter": "MemoryDupeFilter",
    "hoopa.statscollectors.MemoryStatsCollector": "MemoryStatsCollector",
    "hoopa.statscollectors.DummyStatsCollector": "DummyStatsCollector",
    "hoopa.statscollectors.RedisStatsCollector": "RedisStatsCollector"
}