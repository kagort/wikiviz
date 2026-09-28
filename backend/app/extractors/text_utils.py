"""
Общие правила извлечения видимого текста из HTML Wikipedia.

Используются несколькими extractor'ами, чтобы одинаково отбрасывать
служебную разметку MediaWiki (en и ru размечают её одинаково).
"""


def _has_class(element, name: str) -> bool:
    classes = element.get("class", []) if hasattr(element, "get") else []
    return name in classes


def is_footnote_marker(node, container) -> bool:
    """
    Проверяет, лежит ли текстовый узел внутри маркера сноски
    (<sup class="reference">, например "[107]"), не поднимаясь выше
    container. Обычный <sup> (степень, порядковый номер) сноской не считается.
    """
    parent = node.parent
    while parent is not None and parent is not container:
        if parent.name == "sup" and _has_class(parent, "reference"):
            return True
        parent = parent.parent
    return False


def strings_without_footnotes(container):
    """Текстовые узлы container, кроме текста маркеров сносок."""
    return (
        string
        for string in container.strings
        if not is_footnote_marker(string, container)
    )
