"""Resumable, fixed-grid offline prompt evaluation."""

import hashlib
import json
import os
import time
from pathlib import Path

from .corpus import digest
from .generation import RUNTIME_MODEL, prompt_material
from .lexical import known_violations
from .prior import Prior
from .runtime import Runtime


def judge(runtime: Runtime, prompt: str, intent: str, result: dict) -> dict:
    response = runtime.model.client.post("chat/completions", json={
        "model": RUNTIME_MODEL, "temperature": 0, "seed": 1, "max_tokens": 128,
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps({
            "curated_material": prompt_material(result["material"]),
            "intent": intent, "utterance": result["utterance"]}, ensure_ascii=False)}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "evaluation", "strict": True,
            "schema": {"type": "object", "additionalProperties": False,
                       "required": ["intent", "fidelity", "jargon", "reason"],
                       "properties": {"intent": {"type": "boolean"}, "fidelity": {"type": "boolean"},
                                      "jargon": {"type": "array", "items": {"type": "string"}},
                                      "reason": {"type": "string"}}}}},
    })
    response.raise_for_status()
    value = json.loads(response.json()["choices"][0]["message"]["content"])
    if set(value) != {"intent", "fidelity", "jargon", "reason"} or not isinstance(value["intent"], bool) or not isinstance(value["fidelity"], bool) or not isinstance(value["jargon"], list):
        raise ValueError("Malformed offline judgment")
    return value


def evaluate(root: Path, *, generate_only: bool = False, reviewed: bool = False):
    runtime = Runtime(root, os.getenv("TUUS_MODEL_URL", "http://127.0.0.1:8081/v1"))
    cases = json.loads((root / "evals/cases.json").read_text())
    generation_hash = hashlib.sha256(runtime.model.prompt.encode()).hexdigest()
    judge_prompt = (root / "prompts/judge_v1.txt").read_text()
    judge_hash = hashlib.sha256(judge_prompt.encode()).hexdigest()
    case_hash = hashlib.sha256((root / "evals/cases.json").read_bytes()).hexdigest()
    fingerprint = {"generation_prompt": generation_hash, "judge_prompt": judge_hash,
                   "cases": case_hash, "corpus": digest(runtime.corpora)}
    checkpoint = root / "evals/generations.jsonl"
    existing = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    if any(row["fingerprint"] != fingerprint for row in existing):
        raise ValueError("Evaluation artifacts differ; archive the previous results before a new run")
    completed = {row["id"] for row in existing}
    rows = existing
    started = time.perf_counter()
    for prior in cases["priors"]:
        for intent in cases["intents"]:
            for seed in cases["seeds"]:
                identifier = f"{intent['id']}/{prior['id']}/{seed}"
                if identifier in completed:
                    continue
                row = {"id": identifier, "intent": intent["text"], "prior": prior, "seed": seed,
                       "fingerprint": fingerprint}
                try:
                    result = runtime.generate(intent["text"], Prior(components=prior["components"]), seed)
                    row.update(result=result)
                except Exception as error:
                    row.update(error=f"{type(error).__name__}: {error}", judgment={
                        "intent": False, "fidelity": False, "jargon": [], "reason": "Evaluation failed"})
                with checkpoint.open("a") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                rows.append(row)
                print(f"Synthesized {len(rows)}/288: {identifier}", flush=True)
    if generate_only:
        runtime.model.close()
        return
    reviews = {}
    if reviewed:
        for path in sorted((root / "evals/reviews").glob("*.jsonl")):
            for line in path.read_text().splitlines():
                review = json.loads(line)
                if review["id"] in reviews:
                    raise ValueError("Duplicate evaluation review")
                reviews[review["id"]] = review
    final_checkpoint = root / "evals/results.jsonl"
    final_rows = [json.loads(line) for line in final_checkpoint.read_text().splitlines()] if final_checkpoint.exists() else []
    if any(row["fingerprint"] != fingerprint for row in final_rows):
        raise ValueError("Final evaluation fingerprint differs")
    done = {row["id"] for row in final_rows}
    for row in rows:
        if row["id"] in done:
            continue
        if "error" not in row:
            if reviewed:
                review = reviews.get(row["id"])
                if not review:
                    raise ValueError(f"Missing independent review: {row['id']}")
                checksum = hashlib.sha256(row["result"]["utterance"].encode()).hexdigest()
                if review["utterance_sha256"] != checksum:
                    raise ValueError("Review refers to a different utterance")
                judgment = review["judgment"]
                row["reviewer"] = review["reviewer"]
            else:
                judgment = judge(runtime, judge_prompt, row["intent"], row["result"])
            judgment["jargon"] = sorted(set(judgment["jargon"]) | set(known_violations(
                row["result"]["utterance"], row["intent"], row["result"]["material"], runtime.retriever.entries)))
            row["judgment"] = judgment
        with final_checkpoint.open("a") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        final_rows.append(row)
        print(f"Scored {len(final_rows)}/288: {row['id']}", flush=True)
    rows = final_rows
    count = len(rows)
    scores = {"intent": sum(row["judgment"]["intent"] for row in rows) / count,
              "fidelity": sum(row["judgment"]["fidelity"] for row in rows) / count,
              "zero_jargon": sum(not row["judgment"]["jargon"] and "error" not in row for row in rows) / count}
    baseline = {"version": 1, "cases": count, "fingerprint": fingerprint, "scores": scores,
                "generation_model": RUNTIME_MODEL, "judge_model": "Independent research-agent review" if reviewed else RUNTIME_MODEL,
                "judge_limitation": "Model-assisted offline judgments are not independent human validation.",
                "errors": sum("error" in row for row in rows),
                "elapsed_this_run_seconds": time.perf_counter() - started,
                "acceptance_targets": {"intent": 0.95, "fidelity": 0.95, "zero_jargon": 1.0}}
    (root / "evals/baseline.json").write_text(json.dumps(baseline, indent=2) + "\n")
    print(json.dumps(baseline, indent=2), flush=True)
    runtime.model.close()
