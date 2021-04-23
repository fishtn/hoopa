
class StatsMiddleware:
    async def process_request(self, request, spider_ins):
        await spider_ins.stats.inc_value('downloader/request_method_count/%s' % request.method)

    async def process_response(self, request, response, spider_ins):
        await spider_ins.stats.inc_value('downloader/response_status_count/%s' % response.status)




