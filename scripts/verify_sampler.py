"""Reproducible numerical and empirical sampler evidence."""

import json
import random

import numpy as np

from tuus.corpus import ROOT, load_corpus
from tuus.prior import Component, Prior
from tuus.retrieval import Retriever, likelihood


def main():
    rng = random.Random(314159)
    retriever = Retriever(load_corpus(), np.load(ROOT / "artifacts/embeddings.npy"))
    query = np.ones(384, dtype=np.float32) / np.sqrt(384)
    results = []
    for year in (1976, 1982, 1996, 2007, 2012, 2021, 2026):
        prior = Prior(components=[Component(mean=year, sigma=0.5, weight=1)])
        selections = [retriever.select(prior.sample(rng)[0], query, rng) for _ in range(10000)]
        covers_sample = sum(all(likelihood(entry, selection.sampled_year) > 0 for entry in selection.entries)
                            for selection in selections) / len(selections)
        covers_center = sum(all(likelihood(entry, year) > 0 for entry in selection.entries)
                            for selection in selections) / len(selections)
        results.append({"year": year, "sample_coverage": covers_sample, "center_coverage": covers_center,
                        "fallback_fraction": sum(selection.fallback for selection in selections) / len(selections)})
        assert covers_center >= 0.95
    mixture = Prior(components=[Component(mean=1970, sigma=8, weight=1), Component(mean=2030, sigma=0.5, weight=3)])
    samples = [mixture.sample(rng) for _ in range(10000)]
    first = sum(component == 0 for _, component in samples) / len(samples)
    assert abs(first - 0.25) < 0.02
    years = np.linspace(1970, 2030, 12001)
    integral = float(np.trapezoid([mixture.density(float(year)) for year in years], years))
    assert abs(integral - 1) < 1e-6
    separated = Prior(components=[Component(mean=1976, sigma=0.5, weight=1),
                                  Component(mean=1996, sigma=0.5, weight=3)])
    era_samples = [retriever.select(separated.sample(rng)[0], query, rng) for _ in range(10000)]
    cb_fraction = sum(selection.kairolexicon == "era_1970_cb_craze" for selection in era_samples) / len(era_samples)
    assert abs(cb_fraction - 0.25) < 0.02
    missing = [retriever.select(year, query, rng) for year in np.linspace(1970, 2030, 1000)]
    assert all(selection.entries for selection in missing)
    report = {"seed": 314159, "draws_per_case": 10000, "tight_prior_results": results,
              "boundary_mixture": {"expected_first_fraction": 0.25, "observed_first_fraction": first,
                                   "tolerance": 0.02, "integral": integral},
              "retrieved_era_mixture": {"centers": [1976, 1996], "weights": [1, 3],
                                        "expected_cb_fraction": 0.25, "observed_cb_fraction": cb_fraction,
                                        "tolerance": 0.02},
              "axis_probe_count": len(missing), "empty_retrievals": 0,
              "sparse_population_checks": "Independent synthetic 1:100 and 1:10 fixtures in tests/test_retrieval.py"}
    (ROOT / "reports/sampling.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
