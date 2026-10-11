"""Measure the actual local-model request path on stated hardware."""

import json
import os
import platform
import time

import numpy as np

from tuus.corpus import ROOT
from tuus.prior import default_prior
from tuus.runtime import Runtime


def main():
    started = time.perf_counter()
    runtime = Runtime(ROOT, os.getenv("TUUS_MODEL_URL", "http://127.0.0.1:8081/v1"))
    cold_ms = (time.perf_counter() - started) * 1000
    results = [runtime.generate("Ask Morgan to collect the printouts before 15:00.", default_prior(), seed)
               for seed in (11, 29, 47, 83, 101)]
    totals = [row["timing_ms"]["total"] for row in results]
    retrievals = [row["timing_ms"]["retrieval"] for row in results]
    report = {"hardware": {"logical_cpus": os.cpu_count(), "architecture": platform.machine(),
                           "processor": platform.processor(), "memory_total_kib": next(
                               int(line.split()[1]) for line in open('/proc/meminfo') if line.startswith('MemTotal:'))},
              "runtime_model": runtime.model.model, "quantization": "Q4_K_M", "samples": len(results),
              "runtime_load_ms": cold_ms, "retrieval_p50_ms": float(np.percentile(retrievals, 50)),
              "total_p50_ms": float(np.percentile(totals, 50)), "total_p95_ms": float(np.percentile(totals, 95)),
              "subsecond_target_met": max(totals) < 1000,
              "network": "Loopback model endpoint; no hosted-model network excluded.", "results": results}
    (ROOT / "reports/latency.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    runtime.model.close()


if __name__ == "__main__":
    main()
