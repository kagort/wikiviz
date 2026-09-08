class WikipediaError(Exception):
    """Базовый класс для всех ошибок модуля wikipedia."""


class InvalidURLError(WikipediaError):
    """URL не является валидным адресом (в принципе не парсится)."""


class UnsupportedDomainError(WikipediaError):
    """URL валиден, но домен не относится к Wikipedia."""


class ArticleNotFoundError(WikipediaError):
    """Wikipedia ответила, но статьи с таким названием не существует."""


class WikipediaAPIError(WikipediaError):
    """Сетевая ошибка, таймаут, или Wikipedia API вернул код ошибки."""