from typing import Any
import pytest
from tests.CSCI926.xl.conftest import MockSong
from xl.common import (
    MetadataList,
    TimeSpan,
    VersionError,
    clamp,
    enum,
    sanitize_url,
    get_url_contents,
    classproperty,
)
import math as m
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
        ("https://www.example.com", "https://www.example.com"),
        ("https://www.example.com/search", "https://www.example.com/search"),
        (
            "https://www.example.com/search?q=test",
            "https://www.example.com/search?q=test",
        ),
        ("https://www.example.com", "https://www.example.com"),
        ("https://www.example.com:3000", "https://www.example.com:3000"),
        ("https://www.example.com:3000/", "https://www.example.com:3000/"),
        ("https://www.example.com:3000/search", "https://www.example.com:3000/search"),
        (
            "https://www.example.com:3000/search?q=test",
            "https://www.example.com:3000/search?q=test",
        ),
        (
            "https://www.example.com:3000/search?q=test#test",
            "https://www.example.com:3000/search?q=test#test",
        ),
        ("https://user:password@www.example.com", "https://user:*****@www.example.com"),
        (
            "https://user:password@www.example.com:3000",
            "https://user:*****@www.example.com:3000",
        ),
        (
            "https://user:password@www.example.com:3000/",
            "https://user:*****@www.example.com:3000/",
        ),
        (
            "https://user:password@www.example.com:3000/search?q=test",
            "https://user:*****@www.example.com:3000/search?q=test",
        ),
        (
            "https://user:password@www.example.com:3000/search?q=test#test",
            "https://user:*****@www.example.com:3000/search?q=test#test",
        ),
        ("http://www.example.com", "http://www.example.com"),
        ("http://www.example.com/search", "http://www.example.com/search"),
        (
            "http://www.example.com/search?q=test",
            "http://www.example.com/search?q=test",
        ),
        ("http://www.example.com", "http://www.example.com"),
        ("http://www.example.com:3000", "http://www.example.com:3000"),
        ("http://www.example.com:3000/", "http://www.example.com:3000/"),
        ("http://www.example.com:3000/search", "http://www.example.com:3000/search"),
        (
            "http://www.example.com:3000/search?q=test",
            "http://www.example.com:3000/search?q=test",
        ),
        (
            "http://www.example.com:3000/search?q=test#test",
            "http://www.example.com:3000/search?q=test#test",
        ),
        ("http://user:password@www.example.com", "http://user:*****@www.example.com"),
        (
            "http://user:password@www.example.com:3000",
            "http://user:*****@www.example.com:3000",
        ),
        (
            "http://user:password@www.example.com:3000/",
            "http://user:*****@www.example.com:3000/",
        ),
        (
            "http://user:password@www.example.com:3000/search?q=test",
            "http://user:*****@www.example.com:3000/search?q=test",
        ),
        (
            "http://user:password@www.example.com:3000/search?q=test#test",
            "http://user:*****@www.example.com:3000/search?q=test#test",
        ),
        ("tcp://www.example.com", "tcp://www.example.com"),
        ("tcp://www.example.com/search", "tcp://www.example.com/search"),
        ("tcp://www.example.com/search?q=test", "tcp://www.example.com/search?q=test"),
        ("tcp://www.example.com", "tcp://www.example.com"),
        ("tcp://www.example.com:3000", "tcp://www.example.com:3000"),
        ("tcp://www.example.com:3000/", "tcp://www.example.com:3000/"),
        ("tcp://www.example.com:3000/search", "tcp://www.example.com:3000/search"),
        (
            "tcp://www.example.com:3000/search?q=test",
            "tcp://www.example.com:3000/search?q=test",
        ),
        (
            "tcp://www.example.com:3000/search?q=test#test",
            "tcp://www.example.com:3000/search?q=test#test",
        ),
        ("tcp://user:password@www.example.com", "tcp://user:*****@www.example.com"),
        (
            "tcp://user:password@www.example.com:3000",
            "tcp://user:*****@www.example.com:3000",
        ),
        (
            "tcp://user:password@www.example.com:3000/",
            "tcp://user:*****@www.example.com:3000/",
        ),
        (
            "tcp://user:password@www.example.com:3000/search?q=test",
            "tcp://user:*****@www.example.com:3000/search?q=test",
        ),
        (
            "tcp://user:password@www.example.com:3000/search?q=test#test",
            "tcp://user:*****@www.example.com:3000/search?q=test#test",
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


# @pytest.mark.xfail  # Work out how to raise
def test_get_url_contents_raises(mock_urlerror, mock_user_agent):
    with pytest.raises(urllib.error.URLError):
        get_url_contents("http://example.com", mock_user_agent["User-Agent"])


@pytest.mark.parametrize(
    "value",
    [
        5,
        [1, 2, 3],
        {"test": 1},
        {"a", "b"},
        None,
        TypeError,
        "Value",
        type("Enum", (), {"One": 1, "Two": 2}),
        True,
        lambda: "test",
    ],
)
def test_classproperty(value):
    """
    Example Uses from codebase:
    - menu_title = classproperty(lambda c: c.display)
    - formatter = classproperty(lambda c: TrackFormatter('$%s' % c.name))
    """

    class ClassWithProperties:
        display = value
        test = classproperty(lambda c: c.display)

    assert ClassWithProperties().test == value


def test_versionerror_raises():
    with pytest.raises(VersionError) as exp:
        raise VersionError("Test")


def test_versionerror_message():
    with pytest.raises(VersionError) as exp:
        raise VersionError("Test")
    assert "Test" in str(exp.value)


@pytest.mark.parametrize(
    "days, hours, minutes, seconds",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (1, 1, 1, 0),
        (1, 1, 1, 1),
        (4, 0, 0, 59),
        (4, 0, 59, 0),
        (4, 23, 0, 0),
        (4, 23, 59, 59),
        (1_000_000_000, 23, 59, 59),
    ],
)
def test_timespan_days(days, hours, minutes, seconds):
    test_span = seconds + minutes * 60 + hours * 3600 + days * 3600 * 24
    assert TimeSpan(test_span).days == days


@pytest.mark.parametrize(
    "days, hours, minutes, seconds",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (1, 1, 1, 0),
        (1, 1, 1, 1),
        (4, 0, 0, 59),
        (4, 0, 59, 0),
        (4, 23, 0, 0),
        (4, 23, 59, 59),
        (1_000_000_000, 23, 59, 59),
    ],
)
def test_timespan_hours(days, hours, minutes, seconds):
    test_span = seconds + minutes * 60 + hours * 3600 + days * 3600 * 24
    assert TimeSpan(test_span).hours == hours


@pytest.mark.parametrize(
    "days, hours, minutes, seconds",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (1, 1, 1, 0),
        (1, 1, 1, 1),
        (4, 0, 0, 59),
        (4, 0, 59, 0),
        (4, 23, 0, 0),
        (4, 23, 59, 59),
        (1_000_000_000, 23, 59, 59),
    ],
)
def test_timespan_minutes(days, hours, minutes, seconds):
    test_span = seconds + minutes * 60 + hours * 3600 + days * 3600 * 24
    assert TimeSpan(test_span).minutes == minutes


@pytest.mark.parametrize(
    "days, hours, minutes, seconds",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (1, 1, 1, 0),
        (1, 1, 1, 1),
        (4, 0, 0, 59),
        (4, 0, 59, 0),
        (4, 23, 0, 0),
        (4, 23, 59, 59),
        (1_000_000_000, 23, 59, 59),
    ],
)
def test_timespan_minutes(days, hours, minutes, seconds):
    test_span = seconds + minutes * 60 + hours * 3600 + days * 3600 * 24
    assert TimeSpan(test_span).seconds == seconds


@pytest.mark.parametrize(
    "input, exp, raises",
    [
        (None, TypeError, False),
        ([], TypeError, False),
        ({}, TypeError, False),
        (set(), TypeError, False),
        (m.factorial(200), OverflowError, True),
    ],
)
def test_timespan_raises(input, exp, raises):
    if raises:
        with pytest.raises(exp):
            TimeSpan(input)
    else:
        ts = TimeSpan(input)
        assert ts.days == 0
        assert ts.hours == 0
        assert ts.minutes == 0
        assert ts.seconds == 0


@pytest.mark.parametrize(
    "days, hours, minutes, seconds",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (1, 1, 1, 0),
        (1, 1, 1, 1),
        (4, 0, 0, 59),
        (4, 0, 59, 0),
        (4, 23, 0, 0),
        (4, 23, 59, 59),
        (1_000_000_000, 23, 59, 59),
    ],
)
def test_timespan_str(days, hours, minutes, seconds):
    test_span = seconds + minutes * 60 + hours * 3600 + days * 3600 * 24
    assert str(TimeSpan(test_span)) == f"{days}d, {hours}h, {minutes}m, {seconds}s"


@pytest.mark.parametrize(
    "days, hours, minutes, seconds",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (1, 1, 1, 0),
        (1, 1, 1, 1),
        (4, 0, 0, 59),
        (4, 0, 59, 0),
        (4, 23, 0, 0),
        (4, 23, 59, 59),
        (1_000_000_000, 23, 59, 59),
    ],
)
def test_timespan_repr(days, hours, minutes, seconds):
    test_span = seconds + minutes * 60 + hours * 3600 + days * 3600 * 24
    assert repr(TimeSpan(test_span)) == f"TimeSpan({float(test_span)})"


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    assert isinstance(mdl, MetadataList)


@pytest.mark.parametrize(
    "item_count",
    list(range(10, 1_011, 50)),
)
def test_MetadataList_Metadata_shorter_raises_ValueError(
    item_count, mock_songs_with_metadata
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    with pytest.raises(ValueError):
        mdl = MetadataList(song_list, meta_list[:-1])


@pytest.mark.parametrize(
    "item_count",
    list(range(10, 1_011, 50)),
)
def test_MetadataList_metadata_longer_raises_ValueError(
    item_count, mock_songs_with_metadata
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    with pytest.raises(ValueError):
        mdl = MetadataList(song_list[:-1], meta_list)


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList_len(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    assert len(mdl) == item_count


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList_repr(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    assert repr(mdl) == f"MetadataList({song_list})"


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList_iter(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    for idx, song in enumerate(mdl):
        assert song == song_list[idx]


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList_add(
    item_count, mock_songs_with_metadata, mock_song, mock_song_in_list
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    mdl = mdl + mock_song_in_list
    assert len(mdl) == item_count + 1
    assert mdl[-1] == mock_song


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList_iadd(
    item_count, mock_songs_with_metadata, mock_song, mock_song_in_list
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    mdl += mock_song_in_list
    assert len(mdl) == item_count + 1
    assert mdl[-1] == mock_song


@pytest.mark.parametrize(
    "item_count",
    list(range(0, 1_001, 50)),
)
def test_MetadataList_eq(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl1 = MetadataList(song_list, meta_list)
    mdl2 = MetadataList(song_list, meta_list)
    assert mdl1 == mdl2


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_getitem_no_slice(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    assert mdl[item_count // 2] == song_list[item_count // 2]


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_getitem_slice(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    s = slice(item_count // 2)

    mdl = MetadataList(song_list, meta_list)
    mdl2 = MetadataList(song_list[s], meta_list[s])
    assert mdl[s] == mdl2


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_setitem_without_metadata_not_MetadataList(
    item_count, mock_songs_with_metadata, mock_song
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)

    song_list[0] = [mock_song]
    meta_list[0] = None
    mdlv2 = MetadataList(song_list, meta_list)

    mdl[0] = [mock_song]
    assert mdl == mdlv2


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_setitem_MetadataList(
    item_count, mock_songs_with_metadata, mock_song_in_list
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)

    song_list[0] = mock_song_in_list
    meta_list[0] = list(mock_song_in_list.metadata)
    mdlv2 = MetadataList(song_list, meta_list)

    mdl[0] = mock_song_in_list
    assert mdl == mdlv2


@pytest.mark.parametrize(
    "item_count",
    list(range(2, 1003, 50)),
)
def test_MetadataList_delitem(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)

    del_song = song_list[0]
    del_metadata = meta_list[0]

    del mdl[0]

    assert len(mdl) == item_count - 1
    assert mdl[0] != del_song
    assert mdl.metadata[0] != del_metadata


@pytest.mark.parametrize(
    "item_count",
    list(range(2, 1003, 50)),
)
def test_MetadataList_append(item_count, mock_songs_with_metadata, mock_song):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    song_list_v2, meta_list_v2 = mock_songs_with_metadata(item_count)
    song_list_v2.append(mock_song)
    meta_list_v2.append(mock_song.metadata)
    mdl.append(mock_song, mock_song.metadata)
    mdl_v2 = MetadataList(song_list_v2, meta_list_v2)
    assert mdl == mdl_v2
    assert mdl.metadata == meta_list_v2


@pytest.mark.parametrize(
    "item_count",
    list(range(2, 1003, 50)),
)
def test_MetadataList_extend(
    item_count,
    mock_songs_with_metadata,
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)

    song_list_v2, _ = mock_songs_with_metadata(item_count)
    meta_list_v2 = [None for _ in range(len(song_list_v2))]
    mdl.extend(song_list_v2)

    song_list_v3 = song_list + song_list_v2
    meta_list_v3 = meta_list + meta_list_v2
    mdl_v2 = MetadataList(song_list_v3, meta_list_v3)

    assert mdl == mdl_v2
    assert mdl.metadata == mdl_v2.metadata


# TODO: Found Bug
@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_insert_middle(item_count, mock_songs_with_metadata, mock_song):
    insert_loc = int(item_count // 2)
    insert_song = mock_song
    insert_meta = mock_song.metadata
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    mdl.insert(insert_loc, insert_song, insert_meta)
    song_list_v2, meta_list_v2 = mock_songs_with_metadata(item_count)
    song_list_v2.insert(insert_loc, insert_song)
    meta_list_v2.insert(insert_loc, insert_meta)
    mdl_v2 = MetadataList(song_list_v2, meta_list_v2)
    assert mdl == mdl_v2
    assert mdl.metadata[insert_loc] == insert_meta
    assert mdl.metadata is not mdl_v2.metadata
    assert len(mdl.metadata) == len(mdl_v2.metadata)
    assert mdl.metadata == mdl_v2.metadata
    assert mdl[insert_loc] == insert_song


def test_MetadataList_insert_zero_length(mock_songs_with_metadata, mock_song):
    insert_loc = 0
    insert_song = mock_song
    insert_meta = mock_song.metadata
    song_list, meta_list = mock_songs_with_metadata(0)
    mdl = MetadataList(song_list, meta_list)
    mdl.insert(insert_loc, insert_song, insert_meta)
    song_list_v2, meta_list_v2 = mock_songs_with_metadata(0)
    song_list_v2.insert(insert_loc, insert_song)
    meta_list_v2.insert(insert_loc, insert_meta)
    mdl_v2 = MetadataList(song_list_v2, meta_list_v2)
    assert mdl == mdl_v2
    assert mdl.metadata[insert_loc] == insert_meta
    assert mdl.metadata is not mdl_v2.metadata
    assert len(mdl.metadata) == len(mdl_v2.metadata)
    assert mdl.metadata == mdl_v2.metadata
    assert mdl[insert_loc] == insert_song


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_insert_beginning(item_count, mock_songs_with_metadata, mock_song):
    insert_loc = 0
    insert_song = mock_song
    insert_meta = mock_song.metadata
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    mdl.insert(insert_loc, insert_song, insert_meta)
    song_list_v2, meta_list_v2 = mock_songs_with_metadata(item_count)
    song_list_v2.insert(insert_loc, insert_song)
    meta_list_v2.insert(insert_loc, insert_meta)
    mdl_v2 = MetadataList(song_list_v2, meta_list_v2)
    assert mdl == mdl_v2
    assert mdl.metadata[insert_loc] == insert_meta
    assert mdl.metadata is not mdl_v2.metadata
    assert len(mdl.metadata) == len(mdl_v2.metadata)
    assert mdl.metadata == mdl_v2.metadata
    assert mdl[insert_loc] == insert_song


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_insert_end(item_count, mock_songs_with_metadata, mock_song):
    insert_loc = item_count
    insert_song = mock_song
    insert_meta = mock_song.metadata
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    mdl.insert(insert_loc, insert_song, insert_meta)
    song_list_v2, meta_list_v2 = mock_songs_with_metadata(item_count)
    song_list_v2.insert(insert_loc, insert_song)
    meta_list_v2.insert(insert_loc, insert_meta)
    mdl_v2 = MetadataList(song_list_v2, meta_list_v2)
    assert mdl == mdl_v2
    assert mdl.metadata[insert_loc] == insert_meta
    assert mdl.metadata is not mdl_v2.metadata
    assert len(mdl.metadata) == len(mdl_v2.metadata)
    assert mdl.metadata == mdl_v2.metadata
    assert mdl[insert_loc] == insert_song


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_pop_removes_one(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    expected_length = item_count - 1
    mdl.pop()
    assert len(mdl) == expected_length
    assert len(mdl.metadata) == expected_length


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_pop_returns_last_item(item_count, mock_songs_with_metadata):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    last_song = song_list[-1]
    pop_item = mdl.pop()
    assert pop_item == last_song


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_pop_returns_inputed_index(item_count, mock_songs_with_metadata):
    pop_loc = int(item_count // 2)
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    expected_length = item_count - 1
    pop_song = song_list[pop_loc]
    pop_item = mdl.pop(pop_loc)
    assert pop_item == pop_song
    assert len(mdl) == expected_length


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_remove(item_count, mock_songs_with_metadata):
    remove_loc = int(item_count // 2)
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    expected_length = item_count - 1
    remove_song = song_list[remove_loc]
    assert remove_song in mdl
    mdl.remove(remove_song)
    assert remove_song not in mdl
    assert len(mdl) == expected_length
    assert len(mdl.metadata) == expected_length


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_remove_item_not_in_list(
    item_count, mock_songs_with_metadata, mock_song
):
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    expected_length = item_count
    assert mock_song not in mdl
    with pytest.raises(ValueError):
        mdl.remove(mock_song)
    assert len(mdl) == expected_length
    assert len(mdl.metadata) == expected_length


@pytest.mark.parametrize(
    "item_count",
    list(range(1, 1_002, 50)),
)
def test_MetadataList_reverse(item_count, mock_songs_with_metadata):
    reverse_slice = slice(None, None, -1)
    song_list, meta_list = mock_songs_with_metadata(item_count)
    mdl = MetadataList(song_list, meta_list)
    mdl.reverse()
    song_list_v2, meta_list_v2 = mock_songs_with_metadata(item_count)
    song_list_v3 = song_list_v2[reverse_slice]
    meta_list_v3 = meta_list_v2[reverse_slice]
    mdl_v2 = MetadataList(song_list_v3, meta_list_v3)

    assert mdl == mdl_v2
    assert mdl.metadata == mdl_v2.metadata
    assert mdl[0] == mdl_v2[0]
