from typing import Any
from fablab.builders import load
from fablab.savers import save
import json


def dumps(obj: Any) -> str:
    """Dumps and object to a JSON string.

    Args:
        obj (Any): The object to serialize to JSON.

    Returns:
        str: A JSON string of the serialized object.
    """
    config = save(obj)

    return json.dumps(config)


def loads(jstring: str) -> Any:
    """Builds an object from a JSON string.

    Args:
        config (str): A JSON string of a FabLab serialized object.

    Returns:
        Any: The constructed object.
    """
    config = json.loads(jstring)
    return load(config)


class Foo:
    def __init__(self, a, b=2):
        self.a = a
        self.b = b
