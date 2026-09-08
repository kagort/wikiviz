import pytest

from app.wikipedia.client import parse_wikipedia_url
from app.wikipedia.errors import InvalidURLError, UnsupportedDomainError


def test_basic_url():
    lang, title = parse_wikipedia_url("https://en.wikipedia.org/wiki/Albert_Einstein")
    assert lang == "en"
    assert title == "Albert_Einstein"


def test_mobile_url():
    lang, title = parse_wikipedia_url("https://en.m.wikipedia.org/wiki/Albert_Einstein")
    assert lang == "en"
    assert title == "Albert_Einstein"


def test_anchor_is_ignored():
    lang, title = parse_wikipedia_url(
        "https://en.wikipedia.org/wiki/Albert_Einstein#Early_life"
    )
    assert title == "Albert_Einstein"


def test_russian_language():
    lang, title = parse_wikipedia_url("https://ru.wikipedia.org/wiki/Эйнштейн,_Альберт")
    assert lang == "ru"
    assert title == "Эйнштейн,_Альберт"


def test_unsupported_domain():
    with pytest.raises(UnsupportedDomainError):
        parse_wikipedia_url("https://example.com/wiki/Foo")


def test_invalid_url():
    with pytest.raises(InvalidURLError):
        parse_wikipedia_url("not a url at all")