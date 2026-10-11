"""Known-marker guard, with intent text exemptions."""

import re

from .schema import Entry


def used_markers(output: str, records: list[dict]) -> list[str]:
    return [record["id"] for record in records if any(contains(output, form)
            for form in [record["surface"], *record["variants"]])]


def contains(text: str, form: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(form) + r"(?!\w)", text, re.I))


def known_violations(output: str, intent: str, records: list[dict], entries: list[Entry]) -> list[str]:
    allowed = {record["id"] for record in records}
    violations = []
    for entry in entries:
        if entry.id in allowed:
            continue
        for form in [entry.surface, *entry.variants]:
            if contains(output, form) and not contains(intent, form):
                # A larger supplied phrase may legitimately contain a shorter corpus form.
                supplied = [record["surface"] for record in records] + [variant for record in records for variant in record["variants"]]
                if not any(contains(phrase, form) and contains(output, phrase) for phrase in supplied):
                    violations.append(form)
    return sorted(set(violations))
