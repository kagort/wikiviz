from app.extractors.coordinate_extractor import extract_coordinates
from app.extractors.date_extractor import extract_dates
from app.extractors.image_extractor import extract_images
from app.extractors.number_extractor import extract_numbers
from app.extractors.section_extractor import extract_sections
from app.extractors.section_normalizer import build_section_tree
from app.extractors.table_extractor import extract_tables
from app.extractors.text_date_extractor import extract_text_dates
from app.models import Article, NormalizedArticleModel
from app.wikipedia.models import RawArticle


def normalize_article(raw: RawArticle) -> NormalizedArticleModel:
    """
    Строит канонический NormalizedArticleModel (§7 ТЗ) из RawArticle,
    вызывая все extractors, реализованные к концу Phase 4.

    Заполняются реальными данными: article, sections, tables, locations,
    images, events (оба источника - infobox и обычный текст, объединены
    в один список), numbers.

    Остаются пустыми заглушками (ждут будущих фаз - Entity Layer,
    Phase 15+ актуального Roadmap): infobox, people, organizations,
    works, relations, links, metadata. description и summary также пока
    None - отдельные пункты Roadmap Phase 3, не реализованные вместе
    с sections сознательно (см. историю Phase 3).
    """
    article = Article(
        id=raw.page_id,
        title=raw.title,
        language=raw.language,
        url=raw.url,
        description=None,
        summary=None,
    )

    article_sections = extract_sections(raw.html)
    section_tree = build_section_tree(article_sections)

    tables = extract_tables(raw.html)
    locations = extract_coordinates(raw.html, article_title=raw.title)
    images = extract_images(raw.html)
    events = extract_dates(raw.html) + extract_text_dates(raw.html)
    numbers = extract_numbers(raw.html, language=raw.language)

    return NormalizedArticleModel(
        article=article,
        sections=section_tree,
        tables=tables,
        locations=locations,
        images=images,
        events=events,
        numbers=numbers,
    )
