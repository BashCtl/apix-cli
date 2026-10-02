import json


def is_json(data):
    try:
        json.loads(data)
    except ValueError:
        return False
    return True

