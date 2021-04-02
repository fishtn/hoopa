import sys
from loguru import logger

from hoopa.exceptions import InvalidLogLevel


class Logging:
    def __init__(self, setting=None):
        """
        """
        spider_name = setting.get("NAME")
        log_write_file = setting.get_bool("LOG_WRITE_FILE")
        self.log_level = setting.get("LOG_LEVEL", "INFO").upper()

        if self.log_level not in ("TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"):
            raise InvalidLogLevel(self.log_level)

        if self.log_level == "DEBUG":
            logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        else:
            logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>"

        if log_write_file:
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


