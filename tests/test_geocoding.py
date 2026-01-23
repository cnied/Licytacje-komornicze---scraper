import pytest
import requests


class MockResponse:
    def __init__(self, json_data=None, raise_error=False):
        self._json_data = json_data
        self._raise_error = raise_error

    def json(self):
        if self._raise_error:
            raise ValueError("Invalid JSON")
        return self._json_data


@pytest.fixture
def mock_successful_response():
    return MockResponse(json_data={
        "features": [
            {"geometry": {"coordinates": [21.0122, 52.2297]}}
        ]
    })


@pytest.fixture
def mock_empty_features_response():
    return MockResponse(json_data={"features": []})


@pytest.fixture
def mock_invalid_json_response():
    return MockResponse(raise_error=True)


# --- geocoding_function ---

def test_geocoding_function_returns_none_for_none_address():
    from src.geocoding import geocoding_function
    assert geocoding_function(None) is None


def test_geocoding_function_returns_none_for_empty_address():
    from src.geocoding import geocoding_function
    assert geocoding_function("") is None


def test_geocoding_function_success(monkeypatch, mock_successful_response):
    def mock_get(url, headers, timeout):
        return mock_successful_response

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    result = geocoding_function("Warszawa, ul. Marszałkowska 1")

    assert result == (21.0122, 52.2297)


def test_geocoding_function_returns_none_on_api_error(monkeypatch):
    def mock_get(url, headers, timeout):
        raise Exception("Connection timeout")

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    result = geocoding_function("Warszawa")

    assert result is None


def test_geocoding_function_returns_none_on_empty_features(monkeypatch, mock_empty_features_response):
    def mock_get(url, headers, timeout):
        return mock_empty_features_response

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    result = geocoding_function("nieistniejący adres xyz123")

    assert result is None


def test_geocoding_function_encodes_special_characters(monkeypatch, mock_successful_response):
    captured_url = None

    def mock_get(url, headers, timeout):
        nonlocal captured_url
        captured_url = url
        return mock_successful_response

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    geocoding_function("Kraków, ul. Świętego Jana")

    assert "Krak%C3%B3w" in captured_url


def test_geocoding_function_returns_tuple(monkeypatch, mock_successful_response):
    def mock_get(url, headers, timeout):
        return mock_successful_response

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    result = geocoding_function("Test address")

    assert isinstance(result, tuple)
    assert len(result) == 2


def test_geocoding_function_timeout(monkeypatch):
    def mock_get(url, headers, timeout):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    result = geocoding_function("Warszawa")

    assert result is None


def test_geocoding_function_invalid_json_response(monkeypatch, mock_invalid_json_response):
    def mock_get(url, headers, timeout):
        return mock_invalid_json_response

    monkeypatch.setattr("src.geocoding.requests.get", mock_get)

    from src.geocoding import geocoding_function
    result = geocoding_function("Warszawa")

    assert result is None
