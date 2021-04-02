import pickle
from copy import deepcopy

import ujson


def dumps(data, module=None):
    if not module:
        module = ujson
    return module.dumps(data)


def loads(data, module=None):
    if not module:
        module = ujson
    return module.loads(data)


def serialize_request_and_response(request, response):
    request_kwargs = request.replace_to_kwargs

    for item in deepcopy(request_kwargs):
        if not isinstance(item, (int, bool, str, dict, list)):
            request_kwargs.pop(item)

    response_dict = response.serialize()
    response_dict.setdefault("request", request_kwargs)

    return pickle.dumps(response_dict)
