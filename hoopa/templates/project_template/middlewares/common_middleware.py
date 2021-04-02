from hoopa import Middleware

common_middleware = Middleware()


@common_middleware.request
async def set_request_middleware(spider_ins, request):
    request.timeout = 10


@common_middleware.response
async def set_response_middleware(spider_ins, request, response):
    pass
