# encoding: utf-8
import importlib.util
import os
from importlib import import_module

from loguru import logger

from hoopa.settings import const
from hoopa.settings.const import const_map

SETTINGS_PRIORITIES = {
    'default': 0,
    'project': 1,
    'spider': 2,
}


spider_attr_list = ['name', 'worker_numbers', 'download_delay', 'run_forever', 'queue_cls',
                    'clean_queue', 'priority', 'downloader_cls', 'http_client_kwargs',
                    'middlewares', 'dupefilter_cls', 'clean_dupefilter', 'dupefilter_setting', 'redis_setting',
                    'mq_uri', 'mq_api_port', 'mq_maxsize', 'log_level', 'log_write_file', 'serialization']


class Setting:
    priority_map: dict = {}
    project_setting: bool = True

    # __getitem__和__setitem__，让对象可以像字典一样调用
    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, name, default=None):
        return getattr(self, name, default)

    def set(self, name, value, priority="project"):
        if self.priority_map.get(name, None):
            if SETTINGS_PRIORITIES[priority] > self.priority_map[name]:
                setattr(self, name, value)
                self.priority_map[name] = SETTINGS_PRIORITIES[priority]
        else:
            setattr(self, name, value)
            self.priority_map[name] = SETTINGS_PRIORITIES[priority]

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

        # 去重default配置
        if self.get("QUEUE_CLS") == const.RedisQueue:
            self.set("DUPEFILTER_CLS", const.RedisDupeFilter, "default")
        else:
            self.set("DUPEFILTER_CLS", const.MemoryDupeFilter, "default")

        self.set("DUPEFILTER_SETTING", self.get("REDIS_SETTING"), "default")
        self.set("CLEAN_DUPEFILTER", self.get("CLEAN_QUEUE"), "default")

        for name in spider_attr_list:
            setattr(spider_ins, name, self.get(name.upper()))

    def print_log(self, spider_ins):
        setting_level = "project"
        if not self.project_setting:
            logger.debug(f"读取配置文件失败, 如果有配置文件，请检查是否配置正确")
            setting_level = "spider"

        common_list = ['name', 'worker_numbers', 'download_delay', 'run_forever',
                       'http_client_kwargs', 'log_level', 'log_write_file', 'serialization']

        body = f"setting  max_level--{setting_level}"
        
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
            for item in spider_ins.middleware.request_middleware:
                request_middleware.append(item.__name__)

            response_middleware = []
            for item in spider_ins.middleware.response_middleware:
                response_middleware.append(item.__name__)

            body += f"\n{blank}{'request_middleware':25s}: {request_middleware}"
            body += f"\n{blank}{'response_middleware':25s}: {response_middleware}"

        logger.info(body)


def get_project_settings(settings_path="config.settings"):
    """
    读取配置文件，先从默认配置读取，然后读取自定义配置
    @param settings_path: 配置文件可以填写相对路径，例如config.settings。也可以填写绝对路径：D:/setting.py
    @return: Setting对象
    """

    setting = Setting()
    setting.set_module("hoopa.settings.default_settings", priority="default")
    try:
        if os.path.isfile(settings_path):
            module_spec = importlib.util.spec_from_file_location(os.path.basename(settings_path), settings_path)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            setting.set_module(module, priority="project")
        else:
            setting.set_module(settings_path)
    except Exception as e:
        setting.project_setting = False

    return setting
