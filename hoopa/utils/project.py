# encoding: utf-8
import importlib.util
import os

from hoopa.settings import Setting


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
