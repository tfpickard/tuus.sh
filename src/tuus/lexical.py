"""Known-marker guard, with intent text exemptions."""

import re
import unicodedata

from .schema import Entry


LEADING_ACTIONS = {
    "ask", "thank", "thanks", "praise", "congratulate", "tell", "inform",
    "notify", "request", "please", "welcome", "greet", "apologize", "apologise",
    "decline", "defer", "postpone", "schedule", "arrange", "announce", "promote",
    "hype", "write", "say", "express", "help", "could", "would", "can",
}


def protected_details(intent: str) -> list[str]:
    """Conservative literal checks for explicit names and numeric constraints.

    These checks supplement offline semantic review; they cannot establish that
    the speech act or every constraint was preserved.
    """
    words = list(re.finditer(r"\b[A-Z][a-zA-Z]*\b", intent))
    names = [match.group() for match in words if match.group() != "I"
             and match.group().lower() not in LEADING_ACTIONS
             and (match.start() > 0 or intent[match.end():].startswith(","))]
    numbers = re.findall(r"(?<!\w)\d+(?::\d+)?(?:\.\d+)?(?!\w)", intent)
    # Retain the stated reason, allowing ordinary leading-verb inflections.
    reason = re.search(r"^(?:thank|praise|congratulate|apologi[sz]e)\b.*?\bfor\s+(.+)", intent, re.I)
    reasons = [reason.group(1).rstrip(".!? ")] if reason else []
    return list(dict.fromkeys(names + numbers + reasons))


def protected_actions(intent: str) -> list[str]:
    action = re.search(r"^ask\b.*?\bto\s+(?:not\s+)?(\w+)", intent, re.I)
    actions = [action.group(1)] if action else []
    invitation = re.search(r"^(?:politely\s+)?decline\b.*?\binvitation\b.*?\bto\s+(\w+)", intent, re.I)
    if invitation:
        actions.append(invitation.group(1))
    if re.search(r"\bnot\b", intent, re.I):
        actions.append("not")
    return actions


def address_recipient(output: str, intent: str) -> str:
    """Restore an omitted explicit recipient as neutral direct address.

    This does not repair actor inversions or substitute for semantic evaluation.
    A name already present is left in place for the role guard to inspect.
    """
    match = re.search(r"^(?i:ask|thank|praise|congratulate|welcome|greet|apologi[sz]e\s+to)\s+([A-Z][a-zA-Z]*)\b", intent)
    if match and not contains(output, match.group(1)):
        return f"{match.group(1)}, {output}"
    return output


def detail_present(output: str, detail: str) -> bool:
    if contains(output, detail):
        return True
    reason = re.fullmatch(r"([a-z]+ing)(\s+.+)", detail, re.I)
    if not reason:
        return False
    stem = reason.group(1)[:-3]
    forms = {stem, stem + "s", stem + "ed", stem + "e"}
    return any(contains(output, form + reason.group(2)) for form in forms)


def detail_violations(output: str, intent: str, records: list[dict]) -> list[str]:
    missing = [detail for detail in protected_details(intent) if not detail_present(output, detail)]
    for action in protected_actions(intent):
        # A supplied marker may explicitly express the action (e.g. "eyeball"
        # means "meet"). This is a lexical check, not a semantic certification.
        expressed = action != "not" and any(
            contains(record["meaning"], action) and used_markers(output, [record])
            for record in records)
        inflections = {action, action + "s", action + "ed", action + "ing"}
        if action.endswith("e"):
            inflections.update({action + "d", action[:-1] + "ing"})
        if action == "not":
            present = bool(re.search(r"\bnot\b|n['’]t\b", output, re.I))
        else:
            present = any(contains(output, form) for form in inflections)
        if not present and not expressed:
            missing.append(action)
    allowed_text = intent + " " + " ".join(form for record in records
                                            for form in [record["surface"], *record["variants"]])
    added = [number for number in re.findall(r"(?<!\w)\d+(?::\d+)?(?:\.\d+)?(?!\w)", output)
             if not contains(allowed_text, number)]
    corrections = [f"Restore the explicit detail: {detail}" for detail in missing] + [
        f"Remove the unsupported numeric detail: {number}" for number in dict.fromkeys(added)]
    complement = re.search(r"^ask\b.*?\bto\s+(?:not\s+)?\w+\s+(.+)", intent, re.I)
    if complement:
        object_phrase = re.split(r"\b(?:before|after|until|at|on|by|without|unless)\b", complement.group(1), maxsplit=1)[0]
        ignored = {"the", "a", "an", "some", "my", "our", "your", "of", "for", "to"}
        terms = [term for term in re.findall(r"\b[\w'-]+\b", object_phrase) if term.lower() not in ignored]
        corrections += [f"Retain the requested object or quantity: {term}" for term in terms if not contains(output, term)]
    if re.search(r"^ask\b.*?\bto\s+not\b", intent, re.I) or re.search(r"^ask\b.*?\bnot\s+to\b", intent, re.I):
        if re.search(r"(?:[—:;,]|^)\s*not to\b", output, re.I):
            corrections.append("State a complete direct prohibition, such as 'do not', rather than a dangling 'not to' phrase.")
    if re.search(r"^apologi[sz]e\b", intent, re.I) and re.search(r"\bI\s+can(?:not|['’]t)\s+(?:even\s+)?apologi[sz]e\b", output, re.I):
        corrections.append("Actually apologize; do not say that you cannot apologize.")
    temporal_terms = ("today", "tomorrow", "yesterday", "next meeting", "next week", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    corrections += [f"Remove the unsupported temporal detail: {term}" for term in temporal_terms
                    if contains(output, term) and not contains(allowed_text, term)]
    recipient = re.search(r"^(?i:ask)\s+([A-Z][a-zA-Z]*)\b", intent)
    if recipient and re.search(r"\b(?:from|meet|meeting|tell|ask)\s+" + re.escape(recipient.group(1)) + r"\b", output, re.I):
        corrections.append(f"Address {recipient.group(1)} directly; do not describe them as a third-person object.")
    return corrections


def used_markers(output: str, records: list[dict]) -> list[str]:
    return [record["id"] for record in records if any(marker_present(output, form, record.get("usage_role", "phrase"))
            for form in [record["surface"], *record["variants"]])]


def marker_present(output: str, form: str, role: str) -> bool:
    if not contains(output, form):
        return False
    marker = re.escape(normalized(form).strip().strip(".,!?;:'\""))
    if role == "fragment":
        return bool(re.search(r"(?<!\w)" + marker + r"\s*(?:[.!?;,]|$)", normalized(output), re.I))
    if role == "closing":
        return bool(re.search(r"(?<!\w)" + marker + r"['\"]?\s*(?:,\s*[A-Z][a-zA-Z]*)?\s*(?:[.!?;]|$)", normalized(output), re.I))
    return True


def material_violations(output: str, records: list[dict]) -> list[str]:
    used = set(used_markers(output, records))
    groups = {record["kairolexicon"] for record in records}
    represented = {record["kairolexicon"] for record in records if record["id"] in used}
    corrections = []
    for group in sorted(groups - represented):
        expressions = "; ".join(f"{record['surface']} ({record.get('usage_role', 'phrase')})"
                                for record in records if record["kairolexicon"] == group)
        corrections.append(f"Include an exact supplied expression from {group}: {expressions}. Do not substitute a definition or synonym.")
    for record in records:
        if record["id"] not in used and any(contains(output, form) for form in [record["surface"], *record["variants"]]):
            corrections.append(f"Use {record['surface']} as a {record.get('usage_role', 'phrase')}, not as part of another clause.")
    return corrections


def normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).translate(str.maketrans({
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"}))


def contains(text: str, form: str) -> bool:

    # Terminal punctuation belongs to the sentence, not the lexical marker.
    marker = normalized(form).strip().strip(".,!?;:'\"")
    return bool(marker and re.search(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", normalized(text), re.I))


def known_violations(output: str, intent: str, records: list[dict], entries: list[Entry]) -> list[str]:
    allowed = {record["id"] for record in records}
    violations = []
    for entry in entries:
        if entry.id in allowed:
            continue
        for form in [entry.surface, *entry.variants]:
            # This record denotes a fragmented reaction, not ordinary English
            # modal clauses such as "I can't attend". The latter are connective
            # language; a standalone reaction remains a dated marker.
            if entry.id == "tumblr_cant_even":
                if not re.search(re.escape(normalized(form)) + r"\s*(?:[.!?;,]|$|with\b)", normalized(output), re.I):
                    continue
            if entry.id == "as_if_formula" and not re.search(r"\bas if\s*(?:[.!?;,]|$)", output, re.I):
                continue
            if entry.id == "cb_break" and not re.search(r"(?:^|[.!?;,])\s*break\s*(?:[:!?;,]|$)", output, re.I):
                continue
            if contains(output, form) and not contains(intent, form):
                # A larger supplied phrase may legitimately contain a shorter corpus form.
                supplied = [record["surface"] for record in records] + [variant for record in records for variant in record["variants"]]
                if not any(contains(phrase, form) and contains(output, phrase) for phrase in supplied):
                    violations.append(form)
    return sorted(set(violations))
