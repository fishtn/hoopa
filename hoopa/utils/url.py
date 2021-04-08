
def get_location_from_history(history):
    headers = history[-1].headers
    return headers.get("Location", headers.get("location", None))
