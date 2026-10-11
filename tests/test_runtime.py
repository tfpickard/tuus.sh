import random

import numpy as np
import pytest
from fastapi.testclient import TestClient

from tuus.api import create_app
from tuus.embedding import Encoder
from tuus.generation import RUNTIME_MODEL, SmallModel
from tuus.prior import default_prior
from tuus.runtime import Runtime


class FixedModel:
    def synthesize(self, intent, records, seed):
        assert records
        return f"Please collect the printouts, {records[0]['surface']}."


def test_request_path_never_encodes_corpus_or_calls_other_model(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Corpus encoding occurred on request path")
    monkeypatch.setattr(Encoder, "corpus", forbidden)
    runtime = Runtime.__new__(Runtime)
    from tuus.corpus import load_corpus, entries_of
    from tuus.retrieval import Retriever
    runtime.corpora = load_corpus()
    runtime.retriever = Retriever(runtime.corpora, np.load("artifacts/embeddings.npy"))
    runtime.encoder = type("QueryOnly", (), {"query": lambda self, text: np.ones(384, dtype=np.float32) / np.sqrt(384)})()
    runtime.model = FixedModel()
    result = runtime.generate("Ask a colleague to collect printouts", default_prior(), 93)
    assert result["utterance"].startswith("Please collect")
    with pytest.raises(ValueError):
        SmallModel("http://localhost:8081/v1", __import__('pathlib').Path("prompts/generation_v1.txt"), model="unapproved-large-model")


def test_root_and_subpath_identical_build_and_generation(tmp_path):
    directory = tmp_path / "web/dist"
    (directory / "assets").mkdir(parents=True)
    (directory / "index.html").write_text('<script src="./assets/app.js"></script>')
    (directory / "assets/app.js").write_text('console.log("tuus")')
    runtime = type("Stub", (), {"generate": lambda self, intent, prior, seed: {"utterance": "Please collect the printouts."}})()
    with TestClient(create_app(tmp_path, runtime=runtime, mounts=("", "/tuus"))) as client:
        assert client.get("/").content == client.get("/tuus/").content
        assert client.get("/assets/app.js").content == client.get("/tuus/assets/app.js").content
        for prefix in ("", "/tuus"):
            response = client.post(prefix + "/api/synthesize", json={"intent": "collect printouts", "prior": default_prior().model_dump()})
            assert response.status_code == 200
            assert response.json()["utterance"].startswith("Please")
            assert client.post(prefix + "/api/synthesize", json={"intent": " ", "prior": default_prior().model_dump()}).status_code == 422
