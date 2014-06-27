from tagcube.utils.resource import Resource
from tagcube.utils.exceptions import TagCubeClientException

ONE_RESULT = 1
LATEST_RESULT = 2
ALL_RESULTS = 3


def get_one_resource_after_filter(resource_name, filter_dict, _json):
    if len(_json) == 0:
        return None

    if len(_json) == 1:
        return Resource(_json[0])

    else:
        msg = 'Filter %r on resource "%s" returned more than one result.'
        raise TagCubeClientException(msg % (filter_dict, resource_name))


def get_latest_resource_after_filter(resource_name, filter_dict, _json):
    if len(_json) == 0:
        return None

    return Resource(_json[-1])


def get_all_resources_after_filter(resource_name, filter_dict, _json):
    return [Resource(rjson) for rjson in _json]


RESULT_HANDLERS = {ONE_RESULT: get_one_resource_after_filter,
                   LATEST_RESULT: get_latest_resource_after_filter,
                   ALL_RESULTS: get_all_resources_after_filter}