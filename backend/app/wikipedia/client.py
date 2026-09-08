
import re
from urllib.parse import unquote, urlparse

import httpx

from app.wikipedia.errors import (
    ArticleNotFoundError,
    InvalidURLError,
    UnsupportedDomainError,
    WikipediaAPIError,
)
from app.wikipedia.models import RawArticle


_WIKIPEDIA_DOMAIN_RE = re.compile(
    r"^(?P<lang>[a-z]{2,3})(?:\.m)?\.wikipedia\.org$"
)


def parse_wikipedia_url(url: str) -> tuple[str, str]:
    """
    Разбирает URL статьи Wikipedia.

    Возвращает:
        (language, title)

    Бросает:
        InvalidURLError
        UnsupportedDomainError
    """
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise InvalidURLError(f"Cannot parse URL: {url}") from exc

    if not parsed.scheme or not parsed.netloc:
        raise InvalidURLError(
            f"Not a valid absolute URL: {url}"
        )

    domain_match = _WIKIPEDIA_DOMAIN_RE.match(parsed.netloc)

    if not domain_match:
        raise UnsupportedDomainError(
            f"Unsupported domain: {parsed.netloc}"
        )

    language = domain_match.group("lang")

    if not parsed.path.startswith("/wiki/"):
        raise InvalidURLError(
            f"URL does not point to an article: {url}"
        )

    title = parsed.path.removeprefix("/wiki/")
    title = unquote(title)

    if not title:
        raise InvalidURLError(
            f"URL does not contain an article title: {url}"
        )

    return language, title


class WikipediaClient:
    """Минимальный клиент для получения статьи через MediaWiki API."""

    def __init__(
        self,
        timeout: float = 10.0,
        user_agent: str = (
            "WikiViz/0.1 "
            "(contact: kagort@yandex.ru) "
            "httpx/0.28.1"
        ),
    ) -> None:
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch_article(self, url: str) -> RawArticle:
        """
        Получает статью Wikipedia через MediaWiki API.

        На вход принимает URL статьи.
        На выходе возвращает RawArticle.
        """

        language, requested_title = parse_wikipedia_url(url)

        api_url = f"https://{language}.wikipedia.org/w/api.php"

        params = {
            "action": "parse",
            "page": requested_title,
            "prop": "text|revid",
            "redirects": "1",
            "format": "json",
            "formatversion": "2",
        }

        headers = {
            "User-Agent": self.user_agent,
        }

        try:
            response = httpx.get(
                api_url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                trust_env=False,
            )
            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise WikipediaAPIError(
                f"Failed to request Wikipedia API: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise WikipediaAPIError(
                "Wikipedia API returned invalid JSON"
            ) from exc

        if "error" in data:
            error = data["error"]
            error_code = error.get("code")

            if error_code in {"missingtitle", "invalidtitle"}:
                raise ArticleNotFoundError(
                    f"Article not found: {requested_title}"
                )

            raise WikipediaAPIError(
                f"Wikipedia API error: {error}"
            )

        try:
            parsed = data["parse"]

            title = parsed["title"]
            page_id = parsed["pageid"]
            html = parsed["text"]
            revision_id = parsed.get("revid")

        except (KeyError, TypeError) as exc:
            raise WikipediaAPIError(
                "Unexpected response format from Wikipedia API"
            ) from exc

        article_url = (
            f"https://{language}.wikipedia.org/wiki/"
            f"{title.replace(' ', '_')}"
        )

        return RawArticle(
            page_id=page_id,
            title=title,
            language=language,
            url=article_url,
            html=html,
            revision_id=revision_id,
        )

