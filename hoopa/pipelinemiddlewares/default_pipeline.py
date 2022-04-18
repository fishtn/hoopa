from loguru import logger


class DefaultPipeline:
    async def process_item(self, item, spider_ins):
        logger.info(item)





