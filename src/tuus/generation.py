"""Small-model synthesis; no corpus encoding or offline judging here."""

import json
import re
from pathlib import Path

import httpx

from .retrieval import Selection
from .lexical import protected_actions, protected_details

RUNTIME_MODEL = "Qwen3-4B-Instruct-2507"


def detect_function(intent: str) -> str | None:
    lowered = intent.lower()
    rules = {
        "thanking": r"\b(thank|thanks|grateful)\b",
        "apologizing": r"\b(apologize|apologise|sorry|apology)\b",
        "declining": r"\b(decline|refuse|turn down)\b",
        "deferring": r"\b(defer|postpone|later)\b",
        "scheduling": r"\b(schedule|arrange|appointment)\b|\b(?:to|we|you|us)\s+meet\b",
        "praising": r"\b(praise|congratulate|compliment)\b",
        "hyping": r"\b(hype|promote|announce|excited)\b",
        "requesting": r"\b(ask|request|please|could|would|help)\b",
        "greeting": r"\b(greet|hello|welcome)\b",
        "informing": r"\b(tell|inform|notify|report)\b",
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
                            "usage_role": entry.usage_role,
                            "examples": [example.text for example in sorted(entry.examples,
                                key=lambda example: (example.kind != "attested", len(example.text)))]})
    return records


def prompt_material(records: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(record["kairolexicon"], []).append({
            "id": record["id"], "marker": record["surface"], "meaning": record["meaning"],
            "usage_role": record.get("usage_role", "phrase"), "examples": record["examples"][:1],
        })
    return [{"kairolexicon": name, "entries": entries} for name, entries in groups.items()]


class ModelUnavailable(RuntimeError):
    def __init__(self, message: str, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics


class SmallModel:
    def __init__(self, base_url: str, prompt: Path, model: str = RUNTIME_MODEL):
        if model != RUNTIME_MODEL:
            raise ValueError("Request-path model must be the approved small model")
        self.model = model
        self.prompt = prompt.read_text()
        self.client = httpx.Client(base_url=base_url.rstrip("/") + "/", timeout=90,
                                   trust_env=False)

    def synthesize(self, intent: str, records: list[dict], seed: int,
                   excluded: list[str] | None = None, corrections: list[str] | None = None) -> str:
        context = json.dumps(prompt_material(records), ensure_ascii=False)
        details = json.dumps(protected_details(intent) + protected_actions(intent), ensure_ascii=False)
        correction_text = json.dumps(corrections or [], ensure_ascii=False)
        exclusions = json.dumps(excluded or [], ensure_ascii=False)
        request = (f"Curated dated expressions and illustrative quotations:\n{context}\n\n"
                   f"Corrections: {correction_text}\nExcluded expressions: {exclusions}\n"
                   f"Protected details: {details}\n\nCommunication intention: {intent}\n\n"
                   "Write a complete direct performance of the intention first. Add at least one "
                   "dated expression from EACH supplied kairolexicon without altering that performance. "
                   "Return utterance and the IDs of the expressions actually used.")
        marker_items = {"type": "string"}
        if records:
            marker_items["enum"] = [record["id"] for record in records]
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.prompt},
                         {"role": "user", "content": request}],
            "temperature": 0.35,
            "seed": seed,
            "max_tokens": 320,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "synthesis", "strict": True,
                "schema": {"type": "object", "additionalProperties": False,
                           "required": ["utterance", "markers"],
                           "properties": {"utterance": {"type": "string"},
                                          "markers": {"type": "array", "items": marker_items,
                                                      "minItems": 1 if records else 0}}}}},
        }
        try:
            response = self.client.post("chat/completions", json=payload)
            response.raise_for_status()
            value = json.loads(response.json()["choices"][0]["message"]["content"])
            if (not isinstance(value, dict) or set(value) != {"utterance", "markers"}
                    or not isinstance(value["utterance"], str) or not isinstance(value["markers"], list)
                    or any(marker not in [record["id"] for record in records] for marker in value["markers"])):
                raise ValueError("Synthesis response violated its output contract")
            output = value["utterance"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            raise ModelUnavailable("Synthesis service unavailable") from error
        if not output or len(output.split()) > 90:
            raise ModelUnavailable("Synthesis did not produce a bounded utterance")
        return output

    def close(self):
        self.client.close()
