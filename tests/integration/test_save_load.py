from fablab import save, load
from dataclasses import dataclass


@dataclass
class MyClass:
    a: float
    b: int
    c: str
    d: list
    e: dict


def test_save_load_float():
    my_value = 1.234

    saved = save(my_value)

    loaded = load(saved)

    assert my_value == loaded


def test_save_load_list():
    my_list = [1, 2.3, 2.3, 1]

    saved = save(my_list)

    loaded = load(saved)

    assert loaded is not my_list
    assert loaded == my_list


def test_save_load_dict():
    my_dict = {"a": 1, "b": 2, "c": 1.1, "d": 1.1}

    saved = save(my_dict)

    loaded = load(saved)

    assert loaded is not my_dict
    assert loaded == my_dict


def test_save_load_tuple():
    my_tuple = (1, 2, 3.3, 4)

    saved = save(my_tuple)

    loaded = load(saved)

    assert loaded is not my_tuple
    assert loaded == my_tuple


def test_save_load_nested_tuple():
    nested_tuple = (1, 2, 3)
    main_tuple = (3, 4, nested_tuple)

    saved = save(main_tuple)

    loaded = load(saved)

    assert loaded is not main_tuple
    assert loaded == main_tuple


def test_save_load_recursive_tuples():
    inner_list = [1, 2]
    my_tuple = (1, 2, inner_list, 3, 4)
    inner_list.append(my_tuple)

    saved = save(my_tuple)

    loaded = load(saved)

    assert loaded is not my_tuple

    # Check simple values manually
    assert loaded[0] == my_tuple[0]
    assert loaded[1] == my_tuple[1]
    assert loaded[3] == my_tuple[3]
    assert loaded[4] == my_tuple[4]

    # Check recursive values
    assert loaded[2][0] == 1
    assert loaded[2][1] == 2
    assert loaded[2][2] is loaded


def test_save_load_class():
    my_class = MyClass(1.5, 3, "hello!", ["world", "!"], {"one": 1})

    saved = save(my_class)
    loaded = load(saved)
