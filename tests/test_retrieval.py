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
