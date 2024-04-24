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

