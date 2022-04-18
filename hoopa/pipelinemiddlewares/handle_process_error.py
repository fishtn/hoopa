from loguru import logger


class HandleProcessError:
    async def process_exception(self, request, response, item, error, spider_ins):
        logger.error(f"{item} 入库失败")
        response.ok = 0
        response.error = error
        logger.error(error.stack)


