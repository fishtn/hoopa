

class CommonMiddleware:
    def process_request(self, request, spider_ins):
        request.timeout = 10

    def process_response(self, request, response, spider_ins):
        pass
