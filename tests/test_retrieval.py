import random

import numpy as np

from tuus.prior import Component, Prior
from tuus.retrieval import Retriever, likelihood


def vectors(count):
    return np.ones((count, 384), dtype=np.float32) / np.sqrt(384)


def test_sparse_era_wins_when_temporally_distinct(make_entry, make_group):
    small = [make_entry("small_marker", "small", 2010, 2012, 2014)]
    large = [make_entry(f"large_marker_{index}", "large", 2014, 2016, 2018) for index in range(100)]
    retriever = Retriever([make_group("small", small), make_group("large", large)], vectors(101))
    prior = Prior(components=[Component(mean=2012, sigma=0.5, weight=1)])
    rng = random.Random(63)
    results = [retriever.select(prior.sample(rng)[0], vectors(1)[0], rng) for _ in range(10000)]
    assert sum(result.kairolexicon == "small" for result in results) / len(results) >= 0.95
    assert sum(all(likelihood(entry, result.sampled_year) > 0 for entry in result.entries)
               for result in results) / len(results) >= 0.95


def test_overlap_not_biased_by_population(make_entry, make_group):
    small = [make_entry("small_marker", "small")]
    large = [make_entry(f"large_marker_{index}", "large") for index in range(10)]
    retriever = Retriever([make_group("small", small), make_group("large", large)], vectors(11))
    rng = random.Random(83)
    selected = [retriever.select(2012, vectors(1)[0], rng).kairolexicon for _ in range(10000)]
    assert abs(selected.count("small") / len(selected) - 0.5) < 0.02


def test_no_coverage_never_empty_and_resolves_nearest_support(make_entry, make_group):
    entries = [make_entry()]
    retriever = Retriever([make_group("small", entries)], vectors(1))
    rng = random.Random(317)
    for year in np.linspace(1970, 2030, 1000):
        result = retriever.select(float(year), vectors(1)[0], rng)
        assert result.entries
        assert likelihood(result.entries[0], result.resolved_year) > 0
        if year < 2009:
            assert 2009 < result.resolved_year < 2009.001
        if year > 2015:
            assert 2014.999 < result.resolved_year < 2015


def test_function_compatibility_does_not_depend_on_population(make_entry, make_group):
    compatible = make_entry("compatible_marker", "small")
    compatible.functions = ["requesting"]
    incompatible = [make_entry(f"label_{index}", "large") for index in range(100)]
    for entry in incompatible:
        entry.functions = ["hyping"]
    retriever = Retriever([make_group("small", [compatible]), make_group("large", incompatible)], vectors(101))
    rng = random.Random(217)
    for _ in range(100):
        assert retriever.select(2012, vectors(1)[0], rng, "requesting").kairolexicon == "small"
    # If neither group supports the function, temporal material remains available.
    assert retriever.select(2012, vectors(1)[0], rng, "apologizing").entries


def test_conditional_senses_require_relevant_context_without_emptying_sparse_eras(make_entry, make_group):
    specific = make_entry("inspect_marker")
    specific.context_terms = ["inspect", "review"]
    general = make_entry("floor_request")
    retriever = Retriever([make_group("small", [specific, general])], vectors(2))
    rng = random.Random(12)
    selected = retriever.select(2012, vectors(1)[0], rng, "requesting", count=1,
                                intent="Ask a colleague to collect printouts")
    assert selected.entries == (general,)
    sparse = Retriever([make_group("small", [specific])], vectors(1))
    assert sparse.select(2012, vectors(1)[0], rng, "requesting", intent="Collect printouts").entries


def test_context_gap_resolves_to_compatible_material_before_broadening(make_entry, make_group):
    technical = make_entry("technical", "technical", 2009, 2012, 2015)
    technical.context_terms = ["investment"]
    greeting = make_entry("opening", "nearby", 2015, 2016, 2018)
    retriever = Retriever([make_group("technical", [technical]), make_group("nearby", [greeting])], vectors(2))
    result = retriever.select(2012, vectors(1)[0], random.Random(12), "requesting",
                              intent="Ask a colleague to collect printouts")
    assert result.entries == (greeting,)
    assert result.fallback and 2015 < result.resolved_year < 2015.001
    matched = retriever.select(2012, vectors(1)[0], random.Random(12), "requesting",
                               intent="Ask about the investment")
    assert matched.entries == (technical,) and not matched.fallback


def test_explicit_politeness_excludes_incompatible_dismissal(make_entry, make_group):
    hostile = make_entry("hostile", "same")
    hostile.functions = ["declining"]
    hostile.context_exclusions = ["politely"]
    closing = make_entry("closing", "same")
    closing.functions = ["declining"]
    retriever = Retriever([make_group("same", [hostile, closing])], vectors(2))
    result = retriever.select(2012, vectors(1)[0], random.Random(12), "declining",
                               intent="Politely decline the invitation to speak")
    assert result.entries == (closing,)
