
from hoopa.middleware import Middleware

downloader_stats = Middleware()


@downloader_stats.request
async def request_stats_middleware(spider_ins, request):
    await spider_ins.stats.inc_value('downloader/request_method_count/%s' % request.method)


@downloader_stats.response
async def response_stats_middleware(spider_ins, request, response):
    await spider_ins.stats.inc_value('downloader/response_status_count/%s' % response.status)




