import sys
from main import body_regex

def test_body_regex_single_link():
    body = "Zobacz: https://licytacje.komornik.pl/Notice/Details/123456"
    result = body_regex(body)
    assert result == ["https://licytacje.komornik.pl/Notice/Details/123456"]


def test_body_regex_multiple_links():
    body = """
    https://licytacje.komornik.pl/Notice/Details/111
    https://licytacje.komornik.pl/Notice/Details/222
    """
    result = body_regex(body)
    assert len(result) == 2
    assert "https://licytacje.komornik.pl/Notice/Details/111" in result
    assert "https://licytacje.komornik.pl/Notice/Details/222" in result


def test_body_regex_duplicate_links():
    body = """
    https://licytacje.komornik.pl/Notice/Details/111
    https://licytacje.komornik.pl/Notice/Details/111
    """
    result = body_regex(body)
    assert len(result) == 1
    assert "https://licytacje.komornik.pl/Notice/Details/111" in result


def test_body_regex_none_input():
    body = []
    result = body_regex(body)
    assert result == []

def test_body_regex_empty_string():
    body = ""
    result = body_regex(body)
    assert result == []

def test_body_regex_no_valid_link():
    body = "https://google.com https://example.com/Notice/Details/123"
    result = body_regex(body)
    assert result == []

def test_body_regex_link_with_text_around():
    body = "Kliknij tutaj: https://licytacje.komornik.pl/Notice/Details/999 aby zobaczyć"
    result = body_regex(body)
    assert result == ["https://licytacje.komornik.pl/Notice/Details/999"]

