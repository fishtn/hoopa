from loguru import logger

from hoopa import Response


class HandleParseErrorMiddleware:
    async def process_exception(self, request, response, error, spider_ins):
        logger.error(f"{request.callback} 解析出现错误:\n{request}\n{response}\n {error.stack}")
        return Response(error=error, ok=0)




