import random

import numpy as np
import pytest
from pydantic import ValidationError

from tuus.prior import Component, Prior


def test_normalization_arbitrary_and_boundaries():
    rng = random.Random(941)
    configurations = [[Component(mean=year, sigma=sigma, weight=1)]
                      for year in (1970, 2030) for sigma in (0.5, 8)]
    configurations += [[Component(mean=rng.uniform(1970, 2030), sigma=rng.uniform(0.5, 8),
                                  weight=rng.uniform(0.01, 1000)) for _ in range(rng.randint(1, 6))]
                       for _ in range(30)]
    years = np.linspace(1970, 2030, 12001)
    for components in configurations:
        prior = Prior(components=components)
        mass = np.trapezoid([prior.density(float(year)) for year in years], years)
        assert abs(mass - 1) < 1e-6


@pytest.mark.parametrize("means", [(1980, 2020), (1970, 2030)])
def test_relative_weights_are_actual_mass_even_at_boundaries(means):
    prior = Prior(components=[Component(mean=means[0], sigma=8, weight=1),
                              Component(mean=means[1], sigma=0.5, weight=3)])
    rng = random.Random(127)
    samples = [prior.sample(rng) for _ in range(10000)]
    first = sum(index == 0 for _, index in samples) / len(samples)
    assert abs(first - 0.25) < 0.02
    assert all(1970 <= year <= 2030 for year, _ in samples)


def test_tight_draws_and_nonzero_distant_tail():
    tight = Prior(components=[Component(mean=2012, sigma=0.5, weight=1)])
    broad = Prior(components=[Component(mean=2012, sigma=8, weight=1)])
    rng = random.Random(917)
    assert sum(abs(tight.sample(rng)[0] - 2012) < 1.5 for _ in range(10000)) > 9950
    assert broad.density(1995) > 0.001


def test_invalid_prior_cannot_reach_runtime():
    for mean, sigma, weight in [(1969, 2, 1), (2012, 0.1, 1), (2012, 9, 1), (2012, 2, 0), (float("nan"), 2, 1)]:
        with pytest.raises(ValidationError):
            Component(mean=mean, sigma=sigma, weight=weight)
    with pytest.raises(ValidationError):
        Prior(components=[])
