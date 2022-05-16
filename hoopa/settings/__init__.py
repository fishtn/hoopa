from importlib import import_module
from typing import Dict, Any

from loguru import logger

from hoopa.settings import const
from hoopa.settings.const import const_map

SETTINGS_PRIORITIES = {
    'default': 0,
    'project': 1,
    'spider': 2,
}

spider_attr_list = [
    'name',
    'worker_numbers',
    'download_delay',
    'pending_threshold',
    'run_forever',
    'queue_cls',
    'clean_queue',
    'priority',
    'downloader_cls',
    'http_client_kwargs',
    'dupefilter_cls',
    'clean_dupefilter',
    'dupefilter_setting',
    'redis_setting',
    'stats_cls',
    'downloader_middlewares',
    'spider_middlewares',
    'pipelines',
    'log_config',
    'log_level',
    'log_write_file',
    'serialization',
    'interrupt_with_error',
    'push_number',
    'failure_to_waiting'
]


class SettingItem:
    default: Any = None
    project: Any = None
    spider: Any = None

    @property
    def max_priority(self):
        if self.spider:
            return 2
        elif self.project:
            return 1
        else:
            return 0

    def get(self, priority):
        return getattr(self, priority)

    def set(self, priority, value):
        return setattr(self, priority, value)


class Setting:
    priority_map: Dict[str, SettingItem] = {}
    project_setting: bool = True

    # __getitem__和__setitem__，让对象可以像字典一样调用
    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, name, default=None, priority=None):
        if not priority:
            return getattr(self, name, default)

        return getattr(self.priority_map[name], priority, default)

    def set(self, name, value, priority="project"):
        setting_item = self.priority_map.get(name, SettingItem())
        if getattr(setting_item, priority, None) is not None:
            if SETTINGS_PRIORITIES[priority] >= self.priority_map[name].max_priority:
                setattr(self, name, value)
                setattr(self.priority_map[name], priority, value)
        else:
            setattr(self, name, value)
            setting_item.set(priority, value)
            self.priority_map[name] = setting_item

    def set_module(self, module, priority="project"):
        if isinstance(module, str):
            module = import_module(module)
        for key in dir(module):
            if key.isupper():
                self.set(key, getattr(module, key), priority)

    def get_bool(self, name, default=False):
        got = self.get(name, default)
        try:
            return bool(int(got))
        except ValueError:
            if got in ("True", "true"):
                return True
            if got in ("False", "false"):
                return False
            raise ValueError("Supported values for boolean settings "
                             "are 0/1, True/False, '0'/'1', "
                             "'True'/'False' and 'true'/'false'")

    def init_settings(self, spider_ins):
        """
        设置spider的配置
        """

        for name in spider_attr_list:
            if getattr(spider_ins, name) is not None:
                self.set(name.upper(), getattr(spider_ins, name), "spider")

        for name in spider_attr_list:
            setattr(spider_ins, name, self.get(name.upper()))

    def print_log(self, spider_ins):
        setting_level = "project"
        if not self.project_setting:
            setting_level = "spider"

        common_list = ['name', 'worker_numbers', 'download_delay', 'run_forever',
                       'http_client_kwargs', 'log_level', 'log_write_file', 'serialization']

        body = f"\nsetting max level: {setting_level}"

        # blank
        blank = " " * 4
        for item in common_list:
            body += f"\n{blank}{item:25s}: {self.get(item.upper())}"

        queue_cls = self.get("QUEUE_CLS")
        queue_cls_str = const_map.get(queue_cls, queue_cls)
        body += f"\n{blank}{'queue_cls':25s}: {queue_cls_str}"
        if queue_cls == const.RedisQueue:
            body += f"\n{blank}{'clean_queue':25s}: {self.get('CLEAN_QUEUE')}"
            body += f"\n{blank}{'priority':25s}: {self.get('PRIORITY')}"
        elif queue_cls == const.RabbitMQQueue:
            body += f"\n{blank}{'clean_queue':25s}: {self.get('CLEAN_QUEUE')}"

        dupefilter_cls = self.get("DUPEFILTER_CLS")
        dupefilter_cls_str = const_map.get(dupefilter_cls, dupefilter_cls)
        body += f"\n{blank}{'dupefilter_cls':25s}: {dupefilter_cls_str}"
        if dupefilter_cls == const.RedisDupeFilter:
            body += f"\n{blank}{'clean_dupefilter':25s}: {self.get('CLEAN_DUPEFILTER')}"

        stats_cls = self.get("STATS_CLS")
        stats_cls_str = const_map.get(stats_cls, stats_cls)
        body += f"\n{blank}{'stats_cls':25s}: {stats_cls_str}"

        downloader_cls = self.get("DOWNLOADER_CLS")
        downloader_cls_str = const_map.get(downloader_cls, downloader_cls)
        body += f"\n{blank}{'downloader_cls':25s}: {downloader_cls_str}"

        if getattr(spider_ins, "middleware", None):
            request_middleware = []
            for item in spider_ins.middleware.request_middleware_cls:
                request_middleware.append(item)

            response_middleware = []
            for item in spider_ins.middleware.response_middleware_cls:
                response_middleware.append(item)

            body += f"\n{blank}{'request_middleware':25s}: {request_middleware}"
            body += f"\n{blank}{'response_middleware':25s}: {response_middleware}"

        logger.info(body)
