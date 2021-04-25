# Stats

统计，默认是使用内存的，如果使用默认的redis队列，默认使用redis

根据需求修改


```python
stats_cls = const.RedisStatsCollector
```
配置为redis_setting