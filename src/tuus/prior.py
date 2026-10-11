"""Analytic, axis-truncated Gaussian mixtures."""

import math
import random
from statistics import NormalDist

from pydantic import Field

from .schema import Record

AXIS_START = 1970.0
AXIS_END = 2030.0
STANDARD = NormalDist()


class Component(Record):
    mean: float = Field(ge=AXIS_START, le=AXIS_END, allow_inf_nan=False)
    sigma: float = Field(ge=0.5, le=8, allow_inf_nan=False)
    weight: float = Field(gt=0, le=1000, allow_inf_nan=False)


class Prior(Record):
    components: list[Component] = Field(min_length=1, max_length=6)

    def density(self, year: float) -> float:
        if not AXIS_START <= year <= AXIS_END:
            return 0.0
        total = sum(component.weight for component in self.components)
        density = 0.0
        for component in self.components:
            low, high = bounds(component)
            z = (year - component.mean) / component.sigma
            gaussian = math.exp(-0.5 * z * z) / (component.sigma * math.sqrt(2 * math.pi))
            density += component.weight / total * gaussian / (high - low)
        return density

    def sample(self, rng: random.Random) -> tuple[float, int]:
        index = rng.choices(range(len(self.components)),
                            weights=[component.weight for component in self.components])[0]
        component = self.components[index]
        low, high = bounds(component)
        probability = low + rng.random() * (high - low)
        probability = min(1 - 1e-15, max(1e-15, probability))
        year = component.mean + component.sigma * STANDARD.inv_cdf(probability)
        return min(AXIS_END, max(AXIS_START, year)), index


def bounds(component: Component) -> tuple[float, float]:
    return (STANDARD.cdf((AXIS_START - component.mean) / component.sigma),
            STANDARD.cdf((AXIS_END - component.mean) / component.sigma))


def default_prior() -> Prior:
    return Prior(components=[Component(mean=year, sigma=8, weight=1)
                             for year in (1976, 1992, 2008, 2024)])
