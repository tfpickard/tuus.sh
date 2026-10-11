"""Corpus preparation and curation reports, outside the request path."""

import csv
import html
import hashlib
import json
from pathlib import Path

import numpy as np

from .corpus import digest, entries_of, load_corpus, semantic_text
from .embedding import Encoder
from .retrieval import likelihood
from .schema import Kairolexicon


def build(root: Path):
    corpora = load_corpus(root)
    entries = entries_of(corpora)
    encoder = Encoder(root / "models/e5-small-v2")
    vectors = np.concatenate([encoder.corpus([semantic_text(entry) for entry in entries[index:index + 16]])
                              for index in range(0, len(entries), 16)])
    directory = root / "artifacts"
    directory.mkdir(exist_ok=True)
    np.save(directory / "embeddings.npy", vectors)
    models = json.loads((directory / "models.json").read_text())
    manifest = {"schema_version": 1, "corpus_sha256": digest(corpora),
                "embeddings_sha256": hashlib.sha256((directory / "embeddings.npy").read_bytes()).hexdigest(),
                "entry_ids": [entry.id for entry in entries],
                "encoder": "intfloat/e5-small-v2", "dimensions": 384,
                "encoder_artifacts": {key: value for key, value in models.items() if "e5-small-v2" in key},
                "temporal_metadata_in_embeddings": False}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (root / "schemas/kairolexicon.json").write_text(
        json.dumps(Kairolexicon.model_json_schema(), indent=2) + "\n")
    return len(entries)


def coverage(root: Path):
    corpora = load_corpus(root)
    entries = entries_of(corpora)
    vectors = np.load(root / "artifacts/embeddings.npy")
    years = list(range(1970, 2031))
    yearly = []
    for year in years:
        active = [entry for entry in entries if likelihood(entry, year) > 0]
        yearly.append({"year": year, "active_entries": len(active),
                       "likelihood_mass": sum(likelihood(entry, year) for entry in entries),
                       "active_kairolexica": len({membership for entry in active for membership in entry.kairolexica}),
                       "functions": sorted({function for entry in active for function in entry.functions})})
    similarities = vectors @ vectors.T
    np.fill_diagonal(similarities, -1)
    pairs = sorted(((float(similarities[i, j]), entries[i].id, entries[j].id)
                    for i in range(len(entries)) for j in range(i + 1, len(entries))), reverse=True)[:30]
    centered = vectors - vectors.mean(axis=0)
    left, singular, _ = np.linalg.svd(centered, full_matrices=False)
    coordinates = left[:, :2] * singular[:2]
    report = {"corpus_sha256": digest(corpora), "entry_count": len(entries),
              "kairolexicon_count": len(corpora), "years": yearly,
              "gaps": [row["year"] for row in yearly if row["active_entries"] == 0],
              "thin_years": [row["year"] for row in yearly if row["active_entries"] < 5],
              "kairolexica": [{"id": group.id, "name": group.name, "entries": len(group.entries),
                               "density": [sum(likelihood(entry, year) for entry in group.entries) for year in years]}
                              for group in corpora],
              "nearest_pairs": [{"similarity": score, "entries": [first, second]} for score, first, second in pairs],
              "semantic_coordinates": [{"entry": entry.id, "x": float(position[0]), "y": float(position[1])}
                                       for entry, position in zip(entries, coordinates)]}
    directory = root / "reports"
    directory.mkdir(exist_ok=True)
    (directory / "coverage.json").write_text(json.dumps(report, indent=2) + "\n")
    with (directory / "coverage.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "active_entries", "likelihood_mass", "active_kairolexica", "functions"])
        writer.writeheader()
        writer.writerows({**row, "functions": ";".join(row["functions"])} for row in yearly)
    rows = "".join(f"<tr class={'gap' if not row['active_entries'] else 'covered'}><th>{row['year']}</th>"
                   f"<td>{row['active_entries']}</td><td>{row['active_kairolexica']}</td>"
                   f"<td>{row['likelihood_mass']:.2f}</td><td>{html.escape(', '.join(row['functions']))}</td></tr>" for row in yearly)
    group_rows = "".join("<tr><th>" + html.escape(group["name"]) + "</th>" + "".join(
        f"<td title='{year}: {density:.2f}' style='background:rgba(79,99,74,{min(1, density / 10):.2f})'>{density:.1f}</td>"
        for year, density in zip(years, group["density"])) + "</tr>" for group in report["kairolexica"])
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>TμUS coverage</title>
<style>body{{font:15px system-ui;margin:32px;color:#25352a;background:#f8f7f0}}table{{border-collapse:collapse}}th,td{{padding:6px;border:1px solid #ccc}}.gap{{background:#f3d9cf}}.scroll{{overflow:auto}}h1,h2{{font-family:Georgia}}</style>
<h1>Temporal coverage and semantic proximity</h1><p>{len(entries)} entries in {len(corpora)} kairolexica. Zero-support years are shaded.</p>
<h2>Per-kairolexicon density</h2><div class="scroll"><table><tr><th>Kairolexicon</th>{''.join(f'<th>{year}</th>' for year in years)}</tr>{group_rows}</table></div>
<h2>Per-year support</h2><table><tr><th>Year</th><th>Entries</th><th>Kairolexica</th><th>Likelihood mass</th><th>Functions</th></tr>{rows}</table>
<h2>Semantic neighbors</h2><p>Cosine similarity identifies near-duplicate and concentrated semantic material. Coordinates and full detail accompany this report in JSON.</p><ol>
{''.join(f'<li>{html.escape(a)} — {html.escape(b)}: {score:.3f}</li>' for score, a, b in pairs)}</ol></html>"""
    (directory / "coverage.html").write_text(page)
    return report
