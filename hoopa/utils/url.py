
def get_location_from_history(history, downloader="aiohttp"):
    headers = history[-1].headers
    if downloader == "aiohttp":
        return headers['Location']
    elif downloader == "httpx":
        return headers['location']
    else:
        return headers.get("Location", headers.get("location", None))