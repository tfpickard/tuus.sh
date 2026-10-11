"""Small-model synthesis; no corpus encoding or offline judging here."""

import json
import re
from pathlib import Path

import httpx

from .retrieval import Selection

RUNTIME_MODEL = "Qwen3-4B-Instruct-2507"


def detect_function(intent: str) -> str | None:
    lowered = intent.lower()
    rules = {
        "thanking": r"\b(thank|thanks|grateful)\b",
        "apologizing": r"\b(apologize|apologise|sorry|apology)\b",
        "declining": r"\b(decline|refuse|turn down)\b",
        "deferring": r"\b(defer|postpone|later)\b",
        "scheduling": r"\b(schedule|arrange|appointment|meeting)\b",
        "praising": r"\b(praise|congratulate|compliment)\b",
        "hyping": r"\b(hype|promote|announce|excited)\b",
        "requesting": r"\b(ask|request|please|could|would|help)\b",
        "greeting": r"\b(greet|hello|welcome)\b",
    }
    return next((function for function, pattern in rules.items()
                 if re.search(pattern, lowered)), None)


def material(selections: list[Selection]) -> list[dict]:
    seen = set()
    records = []
    for selection in selections:
        for entry in selection.entries:
            if entry.id in seen:
                continue
            seen.add(entry.id)
            records.append({"id": entry.id, "surface": entry.surface,
                            "variants": entry.variants,
                            "kairolexicon": selection.kairolexicon,
                            "meaning": entry.gloss,
                            "examples": [example.text for example in entry.examples]})
    return records


def prompt_material(records: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(record["kairolexicon"], []).append({
            "marker": record["surface"], "meaning": record["meaning"],
            "example": record["examples"][0],
        })
    return [{"kairolexicon": name, "entries": entries} for name, entries in groups.items()]


class ModelUnavailable(RuntimeError):
    pass


class SmallModel:
    def __init__(self, base_url: str, prompt: Path, model: str = RUNTIME_MODEL):
        if model != RUNTIME_MODEL:
            raise ValueError("Request-path model must be the approved small model")
        self.model = model
        self.prompt = prompt.read_text()
        self.client = httpx.Client(base_url=base_url.rstrip("/") + "/", timeout=90,
                                   trust_env=False)

    def synthesize(self, intent: str, records: list[dict], seed: int, excluded: list[str] | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.prompt},
                         {"role": "user", "content": json.dumps({
                             "curated_material": prompt_material(records), "intent": intent,
                             "excluded_expressions": excluded or []}, ensure_ascii=False)}],
            "temperature": 0.65,
            "seed": seed,
            "max_tokens": 160,
        }
        try:
            response = self.client.post("chat/completions", json=payload)
            response.raise_for_status()
            output = response.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            raise ModelUnavailable("Synthesis service unavailable") from error
        if not output or len(output.split()) > 90:
            raise ModelUnavailable("Synthesis did not produce a bounded utterance")
        return output

    def close(self):
        self.client.close()
