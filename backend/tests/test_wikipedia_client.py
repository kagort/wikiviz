from unittest.mock import Mock, patch

import httpx
import pytest

from app.wikipedia.client import WikipediaClient
from app.wikipedia.errors import (
    ArticleNotFoundError,
    WikipediaAPIError,
)


def make_response(data, status_code=200):
    response = Mock()
    response.status_code = status_code

    response.raise_for_status = Mock()

    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "HTTP error",
            request=Mock(),
            response=Mock(),
        )

    response.json.return_value = data

    return response


def test_fetch_article_success():
    response_data = {
        "parse": {
            "pageid": 23862,
            "title": "Python (programming language)",
            "revid": 1373615803,
            "text": "<p>Python is a programming language.</p>",
        }
    }

    with patch(
        "app.wikipedia.client.httpx.get",
        return_value=make_response(response_data),
    ) as mock_get:

        client = WikipediaClient()

        article = client.fetch_article(
            "https://en.wikipedia.org/wiki/Python_(programming_language)"
        )

    assert article.page_id == 23862
    assert article.title == "Python (programming language)"
    assert article.language == "en"
    assert article.html == "<p>Python is a programming language.</p>"
    assert article.revision_id == 1373615803

    mock_get.assert_called_once()

    _, kwargs = mock_get.call_args

    assert kwargs["params"] == {
        "action": "parse",
        "page": "Python_(programming_language)",
        "prop": "text|revid",
        "redirects": "1",
        "format": "json",
        "formatversion": "2",
    }

    assert kwargs["headers"]["User-Agent"] == client.user_agent
    assert kwargs["timeout"] == client.timeout
    assert kwargs["trust_env"] is False


def test_fetch_article_missing_title():
    response_data = {
        "error": {
            "code": "missingtitle",
            "info": "The page you specified doesn't exist.",
        }
    }

    with patch(
        "app.wikipedia.client.httpx.get",
        return_value=make_response(response_data),
    ):
        client = WikipediaClient()

        with pytest.raises(ArticleNotFoundError):
            client.fetch_article(
                "https://en.wikipedia.org/wiki/Definitely_Nonexistent_Page"
            )


def test_fetch_article_invalid_title():
    response_data = {
        "error": {
            "code": "invalidtitle",
            "info": "Bad title.",
        }
    }

    with patch(
        "app.wikipedia.client.httpx.get",
        return_value=make_response(response_data),
    ):
        client = WikipediaClient()

        with pytest.raises(ArticleNotFoundError):
            client.fetch_article(
                "https://en.wikipedia.org/wiki/Invalid_Page"
            )


def test_fetch_article_http_error():
    response = make_response({}, status_code=500)

    with patch(
        "app.wikipedia.client.httpx.get",
        return_value=response,
    ):
        client = WikipediaClient()

        with pytest.raises(WikipediaAPIError):
            client.fetch_article(
                "https://en.wikipedia.org/wiki/Python_(programming_language)"
            )


def test_fetch_article_invalid_json():
    response = Mock()
    response.raise_for_status = Mock()
    response.json.side_effect = ValueError("Invalid JSON")

    with patch(
        "app.wikipedia.client.httpx.get",
        return_value=response,
    ):
        client = WikipediaClient()

        with pytest.raises(WikipediaAPIError):
            client.fetch_article(
                "https://en.wikipedia.org/wiki/Python_(programming_language)"
            )


def test_fetch_article_unexpected_response():
    response_data = {
        "unexpected": {}
    }

    with patch(
        "app.wikipedia.client.httpx.get",
        return_value=make_response(response_data),
    ):
        client = WikipediaClient()

        with pytest.raises(WikipediaAPIError):
            client.fetch_article(
                "https://en.wikipedia.org/wiki/Python_(programming_language)"
            )