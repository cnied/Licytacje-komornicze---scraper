from src.bs4withAI import elicytacje_regex
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




# def elicytacje_regex(body):
#     return list(dict.fromkeys(re.findall(regex, body or "")))