import json

import pytest

from tuus.corpus import ROOT, entries_of, load_corpus, semantic_text


def test_entire_corpus_validates():
    corpora = load_corpus()
    assert len(corpora) >= 10
    assert len(entries_of(corpora)) >= 80


@pytest.mark.parametrize("mutation", ["membership", "source", "duplicate", "unreviewed", "example"])
def test_validation_rejects_corrupt_corpus(tmp_path, make_entry, make_group, mutation):
    group = make_group("small", [make_entry()]).model_dump()
    if mutation == "membership": group["entries"][0]["kairolexica"] = ["missing"]
    if mutation == "source": group["entries"][0]["source_ids"] = ["missing"]
    if mutation == "duplicate": group["entries"].append(group["entries"][0].copy())
    if mutation == "unreviewed": group["entries"][0]["review_status"] = "candidate"
    if mutation == "example": group["entries"][0]["examples"][0]["text"] = "An unrelated quotation."
    directory = tmp_path / "corpus/kairolexica"
    directory.mkdir(parents=True)
    (directory / "small.json").write_text(json.dumps(group))
    errors = {"membership": "undeclared", "source": "unknown source", "duplicate": "Duplicate entry",
              "unreviewed": "unaccepted", "example": "example omits"}
    with pytest.raises(ValueError, match=errors[mutation]):
        load_corpus(tmp_path)


def test_embeddings_exclude_temporal_metadata(make_entry):
    entry = make_entry()
    text = semantic_text(entry)
    assert "2012" not in text
    assert "2009" not in text
    assert "estimated" not in text


def test_project_copy_is_present_and_undocumented():
    group = next(group for group in load_corpus() if group.id == "tuus_2026")
    surfaces = {entry.surface for entry in group.entries}
    assert "T" + chr(956) + "US" in surfaces
    assert "telechronistic" in surfaces
    assert "temporal prior" in surfaces
    assert "kairolexica" in surfaces
    description = "Telechronistic micro-utterance synthesis from user-defined temporal priors over curated kairolexica."
    assert description in surfaces
    assert any(entry.surface in (ROOT / "README.md").read_text() for entry in group.entries if entry.id == "tuus_opening")
    readme = (ROOT / "README.md").read_text().lower()
    assert "recursive" not in readme
    assert "tuus_2026" not in readme
