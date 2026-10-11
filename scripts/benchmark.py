"""Measure the actual local-model request path on stated hardware."""

import json
import hashlib
import os
import platform
import time
from pathlib import Path

import numpy as np

from tuus.corpus import ROOT
from tuus.corpus import digest
from tuus.prior import default_prior
from tuus.runtime import Runtime


def main():
    started = time.perf_counter()
    runtime = Runtime(ROOT, os.getenv("TUUS_MODEL_URL", "http://127.0.0.1:8081/v1"))
    cold_ms = (time.perf_counter() - started) * 1000
    results = []
    for seed in (11, 29, 47, 83, 101):
        attempt = time.perf_counter()
        try:
            row = runtime.generate("Ask Morgan to collect the printouts before 15:00.", default_prior(), seed)
        except Exception as error:
            row = {"error": f"{type(error).__name__}: {error}",
                   "timing_ms": {"total": (time.perf_counter() - attempt) * 1000}}
            if getattr(error, "diagnostics", None):
                row["diagnostics"] = error.diagnostics
        row["seed"] = seed
        results.append(row)
        print(f"Measured seed {seed}: {row['timing_ms']['total']:.1f} ms; success={'error' not in row}", flush=True)
    totals = [row["timing_ms"]["total"] for row in results]
    retrievals = [row["timing_ms"]["retrieval"] for row in results if "retrieval" in row["timing_ms"]]
    quotas = {}
    for name in ("cpu.max", "memory.max"):
        path = Path("/sys/fs/cgroup") / name
        quotas[name] = path.read_text().strip() if path.exists() else None
    report = {"hardware": {"logical_cpus": os.cpu_count(), "architecture": platform.machine(),
                           "processor": platform.processor(), "cgroup_limits": quotas, "memory_total_kib": next(
                               int(line.split()[1]) for line in open('/proc/meminfo') if line.startswith('MemTotal:'))},
              "runtime_model": runtime.model.model, "quantization": "Q4_K_M", "samples": len(results),
              "fingerprint": {"corpus": digest(runtime.corpora),
                              "prompt": hashlib.sha256(runtime.model.prompt.encode()).hexdigest(),
                              "implementation": hashlib.sha256(b"".join(
                                  (ROOT / "src/tuus" / name).read_bytes() for name in
                                  ("generation.py", "lexical.py", "runtime.py", "retrieval.py", "prior.py"))).hexdigest()},
              "runtime_load_ms": cold_ms, "retrieval_p50_ms": float(np.percentile(retrievals, 50)) if retrievals else None,
              "total_p50_ms": float(np.percentile(totals, 50)), "total_p95_ms": float(np.percentile(totals, 95)),
              "successful_requests": sum("error" not in row for row in results),
              "subsecond_target_met": max(totals) < 1000 and all("error" not in row for row in results),
              "concurrency": "One request at a time; no evaluation or browser synthesis workload.",
              "network": "Loopback model endpoint; no hosted-model network excluded.", "results": results}
    (ROOT / "reports/latency.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    runtime.model.close()


if __name__ == "__main__":
    main()
