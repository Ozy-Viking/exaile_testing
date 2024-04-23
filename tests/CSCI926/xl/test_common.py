import pytest
from xl.common import clamp, enum, sanitize_url, get_url_contents

import urllib


@pytest.fixture
def enum_input():
    return {"ON": 1, "OFF": 0}


@pytest.fixture
def enum_1():
    return enum(ON=1, OFF=0)


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
    assert getattr(enum_1, name) == value


def test_enum_values_by_name_ON(enum_input):
    e1 = enum(**enum_input)
    assert e1.ON == 1


def test_enum_values_by_name_OFF(enum_input):
    e1 = enum(**enum_input)
    assert e1.OFF == 0


@pytest.mark.parametrize(
    "input, error",
    [
        (0, TypeError),
        (None, TypeError),
        ([], TypeError),
        ([1, 2], TypeError),
        ({}, TypeError),
        ({1, 2}, TypeError),
    ],
)
def test_enum_raises(input, error):
    with pytest.raises(error):
        enum(input)


@pytest.mark.parametrize(
    "input_url, expected_url",
    [
        ("https://www.google.com", "https://www.google.com"),
        ("https://www.google.com/search", "https://www.google.com/search"),
        (
            "https://www.google.com/search?q=test",
            "https://www.google.com/search?q=test",
        ),
        ("https://www.google.com", "https://www.google.com"),
        ("https://www.google.com:3000", "https://www.google.com:3000"),
        ("https://www.google.com:3000/", "https://www.google.com:3000/"),
        ("https://www.google.com:3000/search", "https://www.google.com:3000/search"),
        (
            "https://www.google.com:3000/search?q=test",
            "https://www.google.com:3000/search?q=test",
        ),
        (
            "https://www.google.com:3000/search?q=test#test",
            "https://www.google.com:3000/search?q=test#test",
        ),
        ("https://user:password@www.google.com", "https://user:*****@www.google.com"),
        (
            "https://user:password@www.google.com:3000",
            "https://user:*****@www.google.com:3000",
        ),
        (
            "https://user:password@www.google.com:3000/",
            "https://user:*****@www.google.com:3000/",
        ),
        (
            "https://user:password@www.google.com:3000/search?q=test",
            "https://user:*****@www.google.com:3000/search?q=test",
        ),
        (
            "https://user:password@www.google.com:3000/search?q=test#test",
            "https://user:*****@www.google.com:3000/search?q=test#test",
        ),
        ("http://www.google.com", "http://www.google.com"),
        ("http://www.google.com/search", "http://www.google.com/search"),
        ("http://www.google.com/search?q=test", "http://www.google.com/search?q=test"),
        ("http://www.google.com", "http://www.google.com"),
        ("http://www.google.com:3000", "http://www.google.com:3000"),
        ("http://www.google.com:3000/", "http://www.google.com:3000/"),
        ("http://www.google.com:3000/search", "http://www.google.com:3000/search"),
        (
            "http://www.google.com:3000/search?q=test",
            "http://www.google.com:3000/search?q=test",
        ),
        (
            "http://www.google.com:3000/search?q=test#test",
            "http://www.google.com:3000/search?q=test#test",
        ),
        ("http://user:password@www.google.com", "http://user:*****@www.google.com"),
        (
            "http://user:password@www.google.com:3000",
            "http://user:*****@www.google.com:3000",
        ),
        (
            "http://user:password@www.google.com:3000/",
            "http://user:*****@www.google.com:3000/",
        ),
        (
            "http://user:password@www.google.com:3000/search?q=test",
            "http://user:*****@www.google.com:3000/search?q=test",
        ),
        (
            "http://user:password@www.google.com:3000/search?q=test#test",
            "http://user:*****@www.google.com:3000/search?q=test#test",
        ),
        ("tcp://www.google.com", "tcp://www.google.com"),
        ("tcp://www.google.com/search", "tcp://www.google.com/search"),
        ("tcp://www.google.com/search?q=test", "tcp://www.google.com/search?q=test"),
        ("tcp://www.google.com", "tcp://www.google.com"),
        ("tcp://www.google.com:3000", "tcp://www.google.com:3000"),
        ("tcp://www.google.com:3000/", "tcp://www.google.com:3000/"),
        ("tcp://www.google.com:3000/search", "tcp://www.google.com:3000/search"),
        (
            "tcp://www.google.com:3000/search?q=test",
            "tcp://www.google.com:3000/search?q=test",
        ),
        (
            "tcp://www.google.com:3000/search?q=test#test",
            "tcp://www.google.com:3000/search?q=test#test",
        ),
        ("tcp://user:password@www.google.com", "tcp://user:*****@www.google.com"),
        (
            "tcp://user:password@www.google.com:3000",
            "tcp://user:*****@www.google.com:3000",
        ),
        (
            "tcp://user:password@www.google.com:3000/",
            "tcp://user:*****@www.google.com:3000/",
        ),
        (
            "tcp://user:password@www.google.com:3000/search?q=test",
            "tcp://user:*****@www.google.com:3000/search?q=test",
        ),
        (
            "tcp://user:password@www.google.com:3000/search?q=test#test",
            "tcp://user:*****@www.google.com:3000/search?q=test#test",
        ),
    ],
)
def test_sanitize_url(input_url, expected_url):
    assert sanitize_url(input_url) == expected_url


@pytest.mark.parametrize(
    "input_url, expected_url",
    [
        ("jnafjilagfbuylaerwfbhjlar", "jnafjilagfbuylaerwfbhjlar"),
        ("test@user", "test@user"),
        ("user:test@test", "user:test@test"),
        ("//user:password@test.com", "//user:*****@test.com"),
    ],
)
def test_sanitize_url_with_junk_input(input_url, expected_url):
    assert sanitize_url(input_url) == expected_url


@pytest.mark.parametrize(
    "input, error",
    [
        (0, TypeError),
        (None, TypeError),
        ([], TypeError),
        ({}, TypeError),
    ],
)
def test_sanitize_url_errors(input, error):
    with pytest.raises(error):
        sanitize_url(input)


def test_get_url_contents(mock_response):
    assert (
        get_url_contents("http://example.com", "Test-Agent")
        == "This is totally fake data."
    )


def test_get_url_headers(mock_request_check_headers, mock_user_agent):
    assert get_url_contents("http://example.com", "Test-Agent") == mock_user_agent


@pytest.mark.xfail  # Work out how to raise
def test_get_url_contents_raises(mock_user_agent):
    with pytest.raises(urllib.error.URLError):
        get_url_contents("http://example.com", mock_user_agent["User-Agent"])
