import pytest
from xl.common import clamp, enum


@pytest.fixture
def enum_input():
    return {"ON": 1, "OFF": 0}


@pytest.fixture
def enum_1():
    return {"ON": 1, "OFF": 0}


@pytest.mark.parametrize(
    "value, minimum, maximum, expected",
    [
        (1, 1, 1, 1),
        (1, 0, 2, 1),
        (-1, 0, 5, 0),
        (-10, -20, -5, -10),
        (1_000_000, 1_000_000_000, 10_000_000_000, 1_000_000_000),
        (1.1, 0.0, 2.5, 1.1),
        ("String", "String", "String", "String"),
        ("String", "Str", "Strings", "String"),
        ("String", "Str", "Stri", "Stri"),
    ],
)
def test_clamp(value, minimum, maximum, expected):
    assert clamp(value, minimum, maximum) == expected


@pytest.mark.parametrize(
    "value, minimum, maximum, error",
    [(None, None, None, TypeError), (None, 0, 10, TypeError)],
)
def test_clamp_error_on_TypeError(value, minimum, maximum, error):
    with pytest.raises(error):
        clamp(value, minimum, maximum)


def test_enum_type(enum_input):
    assert enum(**enum_input).__name__ == "Enum"


@pytest.mark.parametrize(
    "name, value",
    [
        ("ON", 1),
        ("OFF", 0),
    ],
)
def test_enum_values_by_key(name, value, enum_1):
    assert enum_1[name] == value
