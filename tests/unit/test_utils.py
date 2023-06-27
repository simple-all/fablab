from fablab import utils
from dataclasses import dataclass


@dataclass
class DummyData:
    a: float
    b: int
    c: list


def test_binary_equals():
    object_a = DummyData(1.0, 4, [6, 7, 8])
    object_b = DummyData(1.0, 4, [6, 7, 8])
    object_c = DummyData(1.0, 5, [7, 8, 9])

    assert utils.binary_equals(object_a, object_b)
    assert not utils.binary_equals(object_a, object_c)
