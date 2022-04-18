import platform
import sys
from loguru import logger

from hoopa.exceptions import InvalidLogLevelError


class Logging:
    """
    日志模块, 使用loguru作为日志模块，弊端就是全局只能存在一个logger，如果想自定义，通过LOG_CONFIG设置
    """

    def __init__(self, setting=None):

        # 自定义logger的配置
        configure = setting.get("LOG_CONFIG", None)
        if configure:
            logger.configure(**configure)
            return

        log_write_file = setting.get_bool("LOG_WRITE_FILE")
        self.log_level = setting.get("LOG_LEVEL", "INFO").upper()

        if self.log_level not in ("TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"):
            raise InvalidLogLevelError(self.log_level)

        if self.log_level == "DEBUG":
            logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{name}" \
                            "</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        else:
            logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <level>" \
                            "{message}</level>"

        if log_write_file:
            spider_name = setting.get("NAME")
            handler = {
                    "sink": "logs/%s.log" % spider_name,
                    "rotation": "00:00",
                    "level": self.log_level,
                    "enqueue": True,
                    "colorize": True,
                    "backtrace": False, "diagnose": False,
                    "format": logger_format,
                }
        else:
            handler = {
                "sink": sys.stderr,
                "level": self.log_level,
                "enqueue": True,
                "colorize": True,
                "format": logger_format,
                "backtrace": False, "diagnose": False,
            }

        config = {
            "handlers": [handler]
        }
        logger.configure(**config)

    def get_tb_limit(self):
        if self.log_level == "DEBUG":
            return None
        else:
            return -1


def ignore_windows_close_loop_error():
    """
    忽视windows下关闭事件循环的错误
    @return:
    """
    from functools import wraps
    from asyncio.proactor_events import _ProactorBasePipeTransport

    def silence_event_loop_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise

        return wrapper

    if platform.system() == 'Windows':
        _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)


ignore_windows_close_loop_error()