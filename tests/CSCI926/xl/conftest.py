from typing import MutableMapping
import pytest
import urllib.request
from urllib.error import URLError

import xl.common as common


class MockResponse:
    response_data = "This is totally fake data."

    def __init__(self, url, data=None, timeout=0) -> None:
        self.url = url
        if data is not None:
            self.data = data
        else:
            self.data = self.response_data
        self.timeout = timeout

    def read(self):
        return self.data

    def close(self):
        pass


class MockRequest:
    def __init__(
        self,
        url: str,
        data=None,
        headers: MutableMapping[str, str] = {},
    ) -> None:
        self.url = url
        self.headers = headers
        self.data = data

    def close(self):
        pass


class MockOpener:
    def __init__(self, url="", data=None, timeout=0) -> None:
        self.url = url
        self.data = data
        self.timeout = timeout

    def open(self, url, data=None, timeout=0):
        if data is not None:
            data = self.data
        print(data)
        return MockResponse(url, data, timeout)


class MockURLError(MockOpener):
    def open(self, url, data=None, timeout=0):
        raise URLError("Test Exception Handling")


@pytest.fixture(autouse=True)
def mock_response(monkeypatch):

    def mock_request(*args, **kwargs):
        return MockRequest(*args, **kwargs)

    def mock_opener(*args, **kwargs):
        return MockOpener()

    monkeypatch.setattr(urllib.request, "Request", mock_request)
    monkeypatch.setattr(urllib.request, "_opener", mock_opener())


@pytest.fixture()
def mock_urlerror(monkeypatch):

    def mock_request(*args, **kwargs):
        return MockRequest(*args, **kwargs)

    def mock_opener(*args, **kwargs):
        return MockURLError()

    monkeypatch.setattr(urllib.request, "Request", mock_request)
    monkeypatch.setattr(urllib.request, "_opener", mock_opener())


@pytest.fixture
def mock_user_agent(user_agent="Test-Agent"):
    return {"User-Agent": user_agent}


@pytest.fixture
def mock_request_check_headers(monkeypatch):
    global headers
    headers = None

    def mock_request(url, data, header, *args, **kwargs):
        global headers
        headers = header
        return MockRequest(url, data, header, *args, **kwargs)

    def mock_urlopen(req):
        print(req.headers)
        return MockResponse(req.url, req.headers)

    monkeypatch.setattr(urllib.request, "Request", mock_request)
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)


def mock_metadata(title, artist="test artist", songlength=300, **kwargs):
    return {"title": title, "artist": artist, "songlength": songlength} | kwargs


class MockSong:
    PROTECTED_KEYS = ["metadata"]

    def __init__(self, title, artist="test artist", songlength=300, **kwargs) -> None:
        for k, v in mock_metadata(title, artist, songlength, **kwargs).items():
            self.__dict__[k] = v

    @property
    def metadata(self):
        return self.__dict__

    def __eq__(self, other):
        if isinstance(other, MockSong):
            return self.metadata == other.metadata
        else:
            return NotImplemented

    def __str__(self) -> str:
        return f"{self.title} by {self.artist}"

    def __repr__(self) -> str:
        return f'MockSong("{self.title}")'

    def __setitem__(self, name, value) -> None:
        if name == "metadata":
            raise KeyError("Metadata in use.")
        self.__dict__[name] = value

    def __getitem__(self, name, value) -> None:
        if name == "metadata":
            raise KeyError("Metadata in use.")
        self.__dict__[name] = value


@pytest.fixture()
def mock_empty_song():
    empty_song = MockSong("Mock Song")
    empty_song.__dict__ = {}
    return empty_song


@pytest.fixture(autouse=True)
def mock_song():
    return MockSong("Mock Song", mock=True)


@pytest.fixture(autouse=True)
def mock_song_in_list(mock_song):
    return common.MetadataList([mock_song], [mock_song.metadata])


@pytest.fixture
def mock_songs_with_metadata():
    def gen_song_list(num_songs=10):
        song_list = [MockSong(f"Test {x}") for x in range(num_songs)]
        meta_list = [x.metadata for x in song_list]
        return (song_list, meta_list)

    return gen_song_list
