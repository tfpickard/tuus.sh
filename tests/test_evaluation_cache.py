import hashlib
import json

import pytest

from tuus import evaluation
from tuus.corpus import digest


@pytest.mark.parametrize("reviewed", [False, True])
def test_changed_judging_mode_cannot_relabel_or_overwrite_cached_evidence(tmp_path, monkeypatch, reviewed):
    for directory in ("evals", "prompts", "artifacts", "src/tuus"):
        (tmp_path / directory).mkdir(parents=True)
    cases = {"priors": [{"id": "prior"}], "intents": [{"id": "intent", "text": "Welcome."}], "seeds": [1]}
    (tmp_path / "evals/cases.json").write_text(json.dumps(cases))
    (tmp_path / "prompts/judge_v1.txt").write_text("Judge.")
    (tmp_path / "artifacts/models.json").write_text("{}")
    names = ("generation.py", "lexical.py", "runtime.py", "retrieval.py", "prior.py")
    for name in names:
        (tmp_path / "src/tuus" / name).write_text(name)
    fingerprint = {
        "generation_prompt": hashlib.sha256(b"Generate.").hexdigest(),
        "judge_prompt": hashlib.sha256(b"Judge.").hexdigest(),
        "cases": hashlib.sha256((tmp_path / "evals/cases.json").read_bytes()).hexdigest(),
        "corpus": digest([]),
        "implementation": hashlib.sha256("".join(names).encode()).hexdigest(),
        "model_artifacts": hashlib.sha256(b"{}").hexdigest(),
    }
    row = {"id": "intent/prior/1", "fingerprint": fingerprint,
           "judgment": {"intent": True, "fidelity": True, "jargon": [], "reason": "Prior evidence."}}
    (tmp_path / "evals/generations.jsonl").write_text(json.dumps(row) + "\n")
    if not reviewed:
        row["reviewer"] = "Independent review"
    evidence = json.dumps(row) + "\n"
    (tmp_path / "evals/results.jsonl").write_text(evidence)
    (tmp_path / "evals/baseline.json").write_text("Preserved baseline.\n")
    model = type("Model", (), {"prompt": "Generate."})()
    runtime = type("Runtime", (), {"corpora": [], "model": model})()
    monkeypatch.setattr(evaluation, "Runtime", lambda root, url: runtime)

    with pytest.raises(ValueError, match="different review mode"):
        evaluation.evaluate(tmp_path, reviewed=reviewed)

    assert (tmp_path / "evals/results.jsonl").read_text() == evidence
    assert (tmp_path / "evals/baseline.json").read_text() == "Preserved baseline.\n"
