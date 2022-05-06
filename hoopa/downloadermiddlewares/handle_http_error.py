from loguru import logger

from hoopa import Response


class HandleHttpErrorMiddleware:
    async def process_response(self, request, response, spider_ins):
        # if response.status != 200:
        #     response.ok = 0
        #     return response
        pass

    async def process_exception(self, request, error, spider_ins):
        logger.error(f"{request} fetch error \n {error.stack}")
        return Response(error=error, ok=0)
