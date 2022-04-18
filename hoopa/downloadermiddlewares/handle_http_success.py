from loguru import logger

from hoopa.utils.url import get_location_from_history


class HandleHttpSuccessMiddleware:
    async def process_response(self, request, response, spider_ins):
        if response.ok == 1:
            if response.history:
                last_url = get_location_from_history(response.history)
                logger.debug(f"{request} redirect <{last_url}> success")
            else:
                logger.debug(f"{request} fetch {response}")




