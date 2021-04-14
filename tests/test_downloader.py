import asyncio
import hoopa


async def downloader_demo():
    downloader = hoopa.AiohttpDownloader()
    response = await downloader.fetch(hoopa.Request(url="https://httpbin.org/get"))
    print(response)


asyncio.run(downloader_demo())
