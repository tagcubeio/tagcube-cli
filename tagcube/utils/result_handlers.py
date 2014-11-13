from tagcube.utils.resource import Resource
from tagcube.utils.exceptions import TagCubeClientException

ONE_RESULT = 1
LATEST_RESULT = 2
ALL_RESULTS = 3


def _get_objects_from_json(_json):
    """
    After enabling pagination in our API we receive results like this:
        {
            "meta": {
                "previous": null,
                "total_count": 1,
                "offset": 0,
                "limit": 20,
                "next": null
            },
            "objects": [
                {
                    "href": "/1.0/profiles/2",
                    "id": 2,
                    "name": "fast_scan"
                }
            ]
        }

    In the past we received:
        [
            {
                "href": "/1.0/profiles/2",
                "id": 2,
                "name": "fast_scan"
            }
        ]

    So this simple/trivial function translates those two things. Created it
    just to explain what's going on behind the scenes.
    """
    return _json['objects']


def get_one_resource_after_filter(resource_name, filter_dict, _json):
    _json = _get_objects_from_json(_json)

    if len(_json) == 0:
        return None

    if len(_json) == 1:
        return Resource(_json[0])

    else:
        msg = 'Filter %r on resource "%s" returned more than one result.'
        raise TagCubeClientException(msg % (filter_dict, resource_name))


def get_latest_resource_after_filter(resource_name, filter_dict, _json):
    _json = _get_objects_from_json(_json)

    if len(_json) == 0:
        return None

    return Resource(_json[-1])


def get_all_resources_after_filter(resource_name, filter_dict, _json):
    _json = _get_objects_from_json(_json)

    return [Resource(rjson) for rjson in _json]


RESULT_HANDLERS = {ONE_RESULT: get_one_resource_after_filter,
                   LATEST_RESULT: get_latest_resource_after_filter,
                   ALL_RESULTS: get_all_resources_after_filter}