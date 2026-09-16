from app.extractors.section_extractor import ArticleSection
from app.models import Section


def build_section_tree(article_sections: list[ArticleSection]) -> list[Section]:
    """
    Строит иерархическое дерево Section (§7 ТЗ) из плоского списка
    ArticleSection, извлечённого из HTML.

    Использует стек: каждый следующий раздел либо становится ребёнком
    последнего добавленного раздела (если его level больше), либо
    поднимаемся по стеку до подходящего уровня вложенности.
    """
    root: list[Section] = []
    # Стек хранит пары (level, Section) — открытые "ветки" дерева,
    # в которые ещё можно добавлять детей.
    stack: list[tuple[int, Section]] = []

    for index, raw_section in enumerate(article_sections):
        node = Section(
            id=f"section-{index}",
            title=raw_section.title,
            level=raw_section.level,
            children=[],
        )

        # Поднимаемся по стеку, пока не найдём раздел с уровнем МЕНЬШЕ текущего
        # (то есть настоящего родителя — h3 ищет ближайший h2 выше себя).
        while stack and stack[-1][0] >= node.level:
            stack.pop()

        if stack:
            stack[-1][1].children.append(node)
        else:
            root.append(node)

        stack.append((node.level, node))

    return root