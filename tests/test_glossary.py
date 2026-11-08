"""Education: glossary completeness, search, link labelling."""

from __future__ import annotations

from futurecoins.education import GLOSSARY, RESOURCES, categories, get, search, short


def test_glossary_has_enough_terms() -> None:
    assert len(GLOSSARY) >= 30


def test_terms_are_unique() -> None:
    terms = [entry.term.lower() for entry in GLOSSARY]
    assert len(terms) == len(set(terms))


def test_every_entry_has_all_four_surfaces() -> None:
    for entry in GLOSSARY:
        assert entry.term
        assert entry.short
        assert entry.explanation
        assert entry.in_game
        assert entry.real_world
        assert entry.category


def test_every_link_says_what_you_will_learn() -> None:
    for entry in GLOSSARY:
        if entry.link:
            assert entry.link.startswith("https://")
            assert entry.link_label


def test_lookup_is_case_insensitive() -> None:
    assert get("HALVING") is not None
    assert short("halving")


def test_search_finds_a_term_from_its_explanation() -> None:
    results = search("fees")
    assert results
    assert any(entry.term == "Fee" for entry in results)


def test_search_can_filter_by_category() -> None:
    results = search("", "Consensus")
    assert results
    assert all(entry.category == "Consensus" for entry in results)


def test_categories_are_stable_and_nonempty() -> None:
    found = categories()
    assert found[0] == "Foundations"
    assert "Meta" in found


def test_resources_are_labelled() -> None:
    assert len(RESOURCES) >= 5
    for resource in RESOURCES:
        assert resource.url.startswith("https://")
        assert resource.what_you_learn
        assert resource.topic
