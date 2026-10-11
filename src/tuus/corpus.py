"""Validated corpus loading and immutable artifact construction."""

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

from .schema import Entry, Kairolexicon
from .lexical import contains

ROOT = Path(os.getenv("TUUS_ROOT", str(Path(__file__).resolve().parents[2])))


def canonical(text: str) -> str:
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def load_corpus(root: Path = ROOT, *, candidates: bool = False) -> list[Kairolexicon]:
    directory = "candidates" if candidates else "kairolexica"
    paths = sorted((root / "corpus" / directory).glob("*.json"))
    if not paths:
        raise ValueError("No kairolexica found")
    corpora = [Kairolexicon.model_validate_json(path.read_text()) for path in paths]
    groups = {group.id for group in corpora}
    if len(groups) != len(corpora):
        raise ValueError("Duplicate kairolexicon identifier")
    entry_ids: set[str] = set()
    forms: dict[str, str] = {}
    for group in corpora:
        source_ids = {source.id for source in group.sources}
        if len(source_ids) != len(group.sources):
            raise ValueError(f"{group.id}: duplicate source identifier")
        for entry in group.entries:
            if entry.id in entry_ids:
                raise ValueError(f"Duplicate entry identifier: {entry.id}")
            entry_ids.add(entry.id)
            if len(set(entry.kairolexica)) != len(entry.kairolexica):
                raise ValueError(f"{entry.id}: duplicate membership")
            if group.id not in entry.kairolexica or not set(entry.kairolexica) <= groups:
                raise ValueError(f"{entry.id}: undeclared kairolexicon membership")
            references = set(entry.source_ids) | {
                example.source_id for example in entry.examples if example.source_id
            }
            if not references <= source_ids:
                raise ValueError(f"{entry.id}: unknown source reference")
            if not candidates and entry.review_status != "accepted":
                raise ValueError(f"{entry.id}: unaccepted entry in corpus")
            for example in entry.examples:
                if not any(contains(example.text, form) for form in [entry.surface, *entry.variants]):
                    raise ValueError(f"{entry.id}: example omits all declared lexical forms")
            for form in [entry.surface, *entry.variants]:
                key = canonical(form)
                if not key:
                    raise ValueError(f"{entry.id}: empty lexical form")
                if key in forms and forms[key] != entry.id:
                    raise ValueError(f"Duplicate lexical form: {form} ({forms[key]}, {entry.id})")
                forms[key] = entry.id
    return corpora


def entries_of(corpora: list[Kairolexicon]) -> list[Entry]:
    return [entry for group in corpora for entry in group.entries]


def digest(corpora: list[Kairolexicon]) -> str:
    payload = json.dumps([group.model_dump() for group in corpora], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def semantic_text(entry: Entry) -> str:
    text = f"{entry.surface}. {entry.gloss} Functions: {', '.join(entry.functions)}. "
    text += " ".join(example.text for example in entry.examples)
    # Dates and provenance are not semantic inputs, including incidental year mentions.
    return re.sub(r"\b(?:19|20)\d{2}s?\b", "", text)
