from src.bs4withAI import elicytacje_regex, stable_id_from_url, get_category_object
import re


def test_elicytacje_regex():
    body = "https://elicytacje.komornik.pl/items/50259"
    assert elicytacje_regex(body) == ["50259"]

def test_elicytacje_regex_multiple_links():
    body = "https://elicytacje.komornik.pl/items/50259, https://elicytacje.komornik.pl/items/50260, https://elicytacje.komornik.pl/items/50261"
    assert elicytacje_regex(body) == ["50259","50260","50261"]

def test_elicytacje_regex_multiple_links_with_duplicates():
    body = "https://elicytacje.komornik.pl/items/50259, https://elicytacje.komornik.pl/items/50260, https://elicytacje.komornik.pl/items/50261,https://elicytacje.komornik.pl/items/50261"
    assert elicytacje_regex(body) == ["50259","50260","50261"]

def test_elicytacje_regex_None_data():
    body = None
    assert elicytacje_regex(body) == []

def test_elicytacje_regex_empty_string():
    body = ""
    assert elicytacje_regex(body) == []

def test_elicytacje_regex_no_match():
    assert elicytacje_regex("brak linków") == []



def test_stable_id_from_url_same_url_returns_same_id():
    url = "https://licytacje.komornik.pl/Notice/Details/123456"
    assert stable_id_from_url(url) == stable_id_from_url(url)

def test_stable_id_from_url_different_urls_return_different_ids():
    url1 = "https://licytacje.komornik.pl/Notice/Details/123456"
    url2 = "https://licytacje.komornik.pl/Notice/Details/789012"
    assert stable_id_from_url(url1) != stable_id_from_url(url2)

def test_stable_id_from_url_returns_positive_int():
    url = "https://licytacje.komornik.pl/Notice/Details/123"
    result = stable_id_from_url(url)
    assert isinstance(result, int)
    assert result >= 0

def test_stable_id_from_url_within_bigint_range():
    url = "https://example.com/test"
    result = stable_id_from_url(url)
    assert result < 9223372036854775807  # max PostgreSQL BIGINT


# --- get_category_object ---

def test_get_category_object_finds_match():
    categories = [
        {"category": "REAL_ESTATE", "value": "mieszkania", "itemcategoryid": 1},
        {"category": "REAL_ESTATE", "value": "domy", "itemcategoryid": 2},
    ]
    result = get_category_object("REAL_ESTATE", "mieszkania", categories)
    assert result == 1

def test_get_category_object_case_insensitive():
    categories = [
        {"category": "REAL_ESTATE", "value": "mieszkania", "itemcategoryid": 1},
    ]
    result = get_category_object("real_estate", "MIESZKANIA", categories)
    assert result == 1

def test_get_category_object_no_match():
    categories = [
        {"category": "REAL_ESTATE", "value": "mieszkania", "itemcategoryid": 1},
    ]
    result = get_category_object("VEHICLES", "samochody", categories)
    assert result is None

def test_get_category_object_none_category_name():
    categories = [{"category": "REAL_ESTATE", "value": "mieszkania", "itemcategoryid": 1}]
    result = get_category_object(None, "mieszkania", categories)
    assert result is None

def test_get_category_object_empty_categories():
    result = get_category_object("REAL_ESTATE", "mieszkania", [])
    assert result is None