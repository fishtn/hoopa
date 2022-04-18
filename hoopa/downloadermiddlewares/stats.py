
class StatsMiddleware:

    def __init__(self, stats):
        self.stats = stats

    @classmethod
    async def create(cls, engine):
        return cls(engine.stats)

    async def process_request(self, request, spider_ins):
        await self.stats.inc_value('downloader/request_method_count/%s' % request.method)

    async def process_response(self, request, response, spider_ins):
        await self.stats.inc_value('downloader/response_status_count/%s' % response.status)




