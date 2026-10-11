import ast
import re
import tokenize
from pathlib import Path

from tuus.corpus import ROOT


def tracked_candidates():
    ignored = {".git", ".venv", "node_modules", "models", "dist", "__pycache__", ".pytest_cache", "test-results", "playwright-report"}
    for path in ROOT.rglob("*"):
        if path.is_file() and not set(path.relative_to(ROOT).parts) & ignored:
            yield path


def test_taxonomy_and_codepoints():
    terms = ["chi" + "ro", "corpu" + "ses", "cor" + "pi"]
    for path in tracked_candidates():
        assert chr(956) not in str(path.relative_to(ROOT))
        assert chr(181) not in str(path.relative_to(ROOT))
        if path.name in {"AGENTS.md", "CLAUDE.md"}:
            continue
        try: text = path.read_text()
        except UnicodeDecodeError: continue
        assert chr(181) not in text, path
        for term in terms:
            assert not re.search(term, text, re.I), (path, term)
        if path.suffix == ".py":
            with path.open("rb") as handle:
                for token in tokenize.tokenize(handle.readline):
                    if token.type == tokenize.NAME:
                        assert chr(956) not in token.string, (path, token.string)


def test_locked_description_and_inherited_rules():
    description = "Telechronistic micro-utterance synthesis from user-defined temporal priors over curated kairolexica."
    assert description in (ROOT / "pyproject.toml").read_text()
    for name in ("AGENTS.md", "CLAUDE.md"):
        text = (ROOT / name).read_text()
        assert "U+03BC" in text and "U+00B5" in text
        assert "deadpan" in text and "kairolexica" in text
    assert "pronoun" + "ciation" not in (ROOT / "README.md").read_text().lower()
