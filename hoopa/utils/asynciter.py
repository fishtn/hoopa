"""
将list转成异步迭代器
"""


class AsyncIter:
    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for item in self.items:
            yield item

    async def fun(self):
        for item in self.items:
            yield item
