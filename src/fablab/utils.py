import pickle
from typing import Any


def binary_equals(object_a: Any, object_b: Any) -> bool:
    pickle_a = pickle.dumps(object_a)
    pickle_b = pickle.dumps(object_b)
    return pickle_a == pickle_b
