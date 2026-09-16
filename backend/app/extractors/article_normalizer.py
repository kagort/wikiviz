from app.extractors.section_extractor import extract_sections
from app.extractors.section_normalizer import build_section_tree
from app.models import Article, NormalizedArticleModel
from app.wikipedia.models import RawArticle


def normalize_article(raw: RawArticle) -> NormalizedArticleModel:
    """
    Строит канонический NormalizedArticleModel (§7 ТЗ) из RawArticle.

    На этом шаге (Phase 3) заполняются только article и sections.
    Остальные поля (infobox, tables, locations, events, numbers, images,
    people, organizations, works) остаются пустыми заглушками — их заполнение
    задача отдельных extractors (Phase 4 Roadmap).
    """
    article = Article(
        id=raw.page_id,
        title=raw.title,
        language=raw.language,
        url=raw.url,
        description=None,  # заполнится в Phase 4 (description extraction)
        summary=None,       # заполнится в Phase 4 (summary extraction)
    )

    article_sections = extract_sections(raw.html)
    section_tree = build_section_tree(article_sections)

    return NormalizedArticleModel(
        article=article,
        sections=section_tree,
    )