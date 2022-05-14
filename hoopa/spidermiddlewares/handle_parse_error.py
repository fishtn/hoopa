from loguru import logger

from hoopa.request import Request


class HandleParseErrorMiddleware:
    async def process_exception(self, request: Request, response, error, spider_ins):
        response.ok = 0
        response.error = error
        logger.error(f"{request.callback} 解析出现错误:\nrequest: {request.serialize()}\n{response}\n {error.stack}")
        return True


