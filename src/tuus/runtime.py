"""Immutable runtime bundle, semantic queries and synthesis."""

import json
import hashlib
import random
import time
from pathlib import Path

import numpy as np

from .corpus import digest, entries_of, load_corpus
from .embedding import Encoder
from .generation import SmallModel, detect_function, material
from .generation import ModelUnavailable
from .lexical import address_recipient, detail_violations, known_violations, material_violations, used_markers
from .prior import Prior
from .retrieval import Retriever


class Runtime:
    def __init__(self, root: Path, model_url: str):
        self.corpora = load_corpus(root)
        manifest = json.loads((root / "artifacts/manifest.json").read_text())
        if manifest["corpus_sha256"] != digest(self.corpora):
            raise ValueError("Corpus changed; rebuild offline artifacts")
        entries = entries_of(self.corpora)
        if manifest["entry_ids"] != [entry.id for entry in entries]:
            raise ValueError("Embedding order differs from corpus")
        if manifest["embeddings_sha256"] != hashlib.sha256((root / "artifacts/embeddings.npy").read_bytes()).hexdigest():
            raise ValueError("Embedding checksum differs from manifest")
        for relative, artifact in manifest["encoder_artifacts"].items():
            if hashlib.sha256((root / relative).read_bytes()).hexdigest() != artifact["sha256"]:
                raise ValueError("Query encoder differs from offline artifact")
        self.retriever = Retriever(self.corpora, np.load(root / "artifacts/embeddings.npy"))
        self.encoder = Encoder(root / "models/e5-small-v2")
        self.model = SmallModel(model_url, root / "prompts/generation_v7.txt")

    def generate(self, intent: str, prior: Prior, seed: int) -> dict:
        start = time.perf_counter()
        rng = random.Random(seed)
        query = self.encoder.query(intent)
        function = detect_function(intent)
        anchors = [prior.sample(rng)[0] for _ in range(3)]
        selections = [self.retriever.select(year, query, rng, function, count=1, intent=intent)
                      for year in anchors]
        records = material(selections)
        retrieval_ms = (time.perf_counter() - start) * 1000
        output = address_recipient(self.model.synthesize(intent, records, seed), intent)
        violations = known_violations(output, intent, records, self.retriever.entries)
        corrections = detail_violations(output, intent, records) + material_violations(output, records)
        if not used_markers(output, records):
            corrections.append("Include at least one supplied dated expression in the utterance.")
        if violations or corrections or not used_markers(output, records):
            output = address_recipient(self.model.synthesize(intent, records, seed + 1,
                                       excluded=violations, corrections=corrections), intent)
            if (known_violations(output, intent, records, self.retriever.entries)
                    or detail_violations(output, intent, records) or material_violations(output, records)
                    or not used_markers(output, records)):
                raise ModelUnavailable("Synthesis exceeded curated lexical material", diagnostics={
                    "utterance": output, "material": records,
                    "detail_violations": detail_violations(output, intent, records),
                    "material_violations": material_violations(output, records),
                    "lexical_violations": known_violations(output, intent, records, self.retriever.entries),
                    "used_markers": used_markers(output, records)})
        return {"utterance": output, "material": records,
                "selections": [{"sampled_year": selection.sampled_year,
                                "resolved_year": selection.resolved_year,
                                "kairolexicon": selection.kairolexicon,
                                "fallback": selection.fallback} for selection in selections],
                "timing_ms": {"retrieval": retrieval_ms,
                              "total": (time.perf_counter() - start) * 1000}}
