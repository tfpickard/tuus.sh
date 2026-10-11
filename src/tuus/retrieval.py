"""Temporal selection independent of lexical population size."""

import random
import re
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
        self.context_patterns = {}
        for entry in self.entries:
            patterns = []
            for terms in (entry.context_terms, entry.context_exclusions):
                pattern = r"(?<!\w)(?:" + "|".join(re.escape(term) for term in terms) + r")(?!\w)"
                patterns.append(re.compile(pattern, re.I) if terms else None)
            self.context_patterns[entry.id] = patterns

    def eligible(self, function: str | None, intent: str) -> list[Entry]:
        contextual = []
        for entry in self.entries:
            allowed, excluded = self.context_patterns[entry.id]
            if not intent or ((allowed is None or allowed.search(intent))
                              and (excluded is None or not excluded.search(intent))):
                contextual.append(entry)
        # A wholly unrepresented intent retains a nonempty last-resort pool.
        pool = contextual or self.entries
        matching = [entry for entry in pool if function in entry.functions]
        return matching or pool

    def scores(self, year: float, eligible: list[Entry]) -> list[float]:
        allowed = {entry.id for entry in eligible}
        return [max((likelihood(entry, year) for entry in self.members[group.id]
                     if entry.id in allowed), default=0.0) for group in self.corpora]

    def group_scores(self, year: float, function: str | None = None) -> list[float]:
        return self.scores(year, self.eligible(function, ""))

    def select(self, year: float, query: np.ndarray, rng: random.Random,
               function: str | None = None, count: int = 2, intent: str = "") -> Selection:
        resolved = year
        eligible = self.eligible(function, intent)
        scores = self.scores(resolved, eligible)
        fallback = not any(scores)
        if fallback:
            # Find the nearest closed support; step inward so boundary likelihood is positive.
            nearest = min(eligible, key=lambda entry: max(
                entry.signature.onset - year, year - entry.signature.fade, 0.0))
            resolved = min(nearest.signature.fade - 1e-6,
                           max(nearest.signature.onset + 1e-6, year))
            scores = self.scores(resolved, eligible)
        group = rng.choices(self.corpora, weights=scores)[0]
        candidates = [entry for entry in eligible if group.id in entry.kairolexica
                      and likelihood(entry, resolved) > 0]
        ranked = sorted(candidates, key=lambda entry: (
            float(self.vectors[self.index[entry.id]] @ query)
            + 0.15 * likelihood(entry, resolved)), reverse=True)
        return Selection(year, resolved, group.id, tuple(ranked[:count]), fallback)
