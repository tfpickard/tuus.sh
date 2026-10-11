"""Temporal selection independent of lexical population size."""

import random
from dataclasses import dataclass

import numpy as np

from .corpus import entries_of
from .schema import Entry, Kairolexicon


def likelihood(entry: Entry, year: float) -> float:
    signature = entry.signature
    if year <= signature.onset or year >= signature.fade:
        return 0.0
    if year <= signature.peak:
        return (year - signature.onset) / (signature.peak - signature.onset)
    return (signature.fade - year) / (signature.fade - signature.peak)


@dataclass(frozen=True)
class Selection:
    sampled_year: float
    resolved_year: float
    kairolexicon: str
    entries: tuple[Entry, ...]
    fallback: bool


class Retriever:
    def __init__(self, corpora: list[Kairolexicon], vectors: np.ndarray):
        self.corpora = corpora
        self.entries = entries_of(corpora)
        if vectors.shape != (len(self.entries), 384):
            raise ValueError("Embedding matrix does not match corpus")
        if not np.isfinite(vectors).all():
            raise ValueError("Non-finite embeddings")
        self.vectors = vectors
        self.index = {entry.id: index for index, entry in enumerate(self.entries)}
        self.members = {group.id: [entry for entry in self.entries if group.id in entry.kairolexica]
                        for group in corpora}

    def group_scores(self, year: float) -> list[float]:
        return [max(likelihood(entry, year) for entry in self.members[group.id])
                for group in self.corpora]

    def select(self, year: float, query: np.ndarray, rng: random.Random,
               function: str | None = None, count: int = 2) -> Selection:
        resolved = year
        scores = self.group_scores(resolved)
        fallback = not any(scores)
        if fallback:
            # Find the nearest closed support; step inward so boundary likelihood is positive.
            nearest = min(self.entries, key=lambda entry: max(
                entry.signature.onset - year, year - entry.signature.fade, 0.0))
            resolved = min(nearest.signature.fade - 1e-6,
                           max(nearest.signature.onset + 1e-6, year))
            scores = self.group_scores(resolved)
        group = rng.choices(self.corpora, weights=scores)[0]
        candidates = [entry for entry in self.members[group.id] if likelihood(entry, resolved) > 0]
        matching = [entry for entry in candidates if function in entry.functions]
        if matching:
            candidates = matching
        ranked = sorted(candidates, key=lambda entry: (
            float(self.vectors[self.index[entry.id]] @ query)
            + 0.15 * likelihood(entry, resolved)), reverse=True)
        return Selection(year, resolved, group.id, tuple(ranked[:count]), fallback)
