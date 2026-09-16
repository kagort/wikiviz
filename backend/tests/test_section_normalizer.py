from app.extractors.section_extractor import ArticleSection
from app.extractors.section_normalizer import build_section_tree


def test_flat_sections_stay_flat():
    sections = [
        ArticleSection(level=2, title="History", html="..."),
        ArticleSection(level=2, title="Design", html="..."),
    ]

    tree = build_section_tree(sections)

    assert len(tree) == 2
    assert tree[0].title == "History"
    assert tree[0].children == []
    assert tree[1].title == "Design"
    assert tree[1].children == []


def test_h3_nests_under_preceding_h2():
    sections = [
        ArticleSection(level=2, title="Design", html="..."),
        ArticleSection(level=3, title="Syntax", html="..."),
        ArticleSection(level=3, title="Indentation", html="..."),
        ArticleSection(level=2, title="Features", html="..."),
    ]

    tree = build_section_tree(sections)

    assert len(tree) == 2
    assert tree[0].title == "Design"
    assert len(tree[0].children) == 2
    assert tree[0].children[0].title == "Syntax"
    assert tree[0].children[1].title == "Indentation"

    assert tree[1].title == "Features"
    assert tree[1].children == []


def test_deep_nesting_h2_h3_h4():
    sections = [
        ArticleSection(level=2, title="A", html="..."),
        ArticleSection(level=3, title="B", html="..."),
        ArticleSection(level=4, title="C", html="..."),
        ArticleSection(level=2, title="D", html="..."),
    ]

    tree = build_section_tree(sections)

    assert len(tree) == 2
    assert tree[0].title == "A"
    assert tree[0].children[0].title == "B"
    assert tree[0].children[0].children[0].title == "C"
    assert tree[1].title == "D"


def test_empty_list_returns_empty_tree():
    assert build_section_tree([]) == []


def test_section_ids_are_unique():
    sections = [
        ArticleSection(level=2, title="A", html="..."),
        ArticleSection(level=3, title="B", html="..."),
    ]

    tree = build_section_tree(sections)

    all_ids = [tree[0].id, tree[0].children[0].id]
    assert len(all_ids) == len(set(all_ids))