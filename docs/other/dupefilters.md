# Dupefilters
去重，默认是内存去重，去重指纹是md5

可以根据需要修改redis去重（兼容redis hash的也可以，例如tendis）
```python
dupefilter_cls = const.RedisDupeFilter
dupefilter_setting = "redis://127.0.0.1:6379/0?encoding=utf-8"
```

默认去重没有实现布隆去重，可以进行拓展