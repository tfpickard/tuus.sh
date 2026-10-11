# TμUS

TμUS synthesizes telechronistic micro-utterances calibrated to user-defined temporal priors over attested kairolexica.

The Telechronistic μ-Utterance Synthesizer couples semantic retrieval with explicit
temporal likelihoods. A present communicative intent is realized using curated
kairolectic markers selected from a normalized temporal prior over 1970–2030.

Enter an intent, adjust the temporal prior, and select **Synthesize**. Each
Gaussian component has a temporal center, width, and relative weight. Drag its
center horizontally, adjust the lateral width handle, or move the apex vertically
to alter its weight. Select an empty region to add a component. Select a component
and press Delete, or use its removal control, to remove it. At least one component
is retained. Re-sampling and copying operate on the resulting μ-utterance.

## Local operation

Python 3.11 or later and Node.js 20 or later are required. Model artifacts are
retrieved separately and checked against pinned revisions and checksums.

```sh
uv sync --extra dev
uv run python scripts/fetch_models.py
uv run tuus validate
uv run tuus build
uv run tuus coverage
npm --prefix web ci
npm --prefix web run build
```

Start a `llama.cpp` server with the approved small model:

```sh
llama-server -m models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf \
  --alias Qwen3-4B-Instruct-2507 --port 8081 -c 4096 -t 3
```

In a second terminal:

```sh
TUUS_MODEL_URL=http://127.0.0.1:8081/v1 \
  uv run uvicorn tuus.api:app_factory --factory --host 127.0.0.1 --port 8000
```

The application is served at `http://127.0.0.1:8000/`. To serve the same build at
a subpath, set `TUUS_BASE_PATH=/tuus` and use `http://127.0.0.1:8000/tuus/`.
The internal synthesis endpoint is same-origin and is not a public API contract.

## Corpus and evaluation

Kairolexica are curated project data. Entries retain canonical forms, variants,
communicative functions, temporal signatures, examples, and dating rationale.
Constructed examples are distinguished from source-attested usages. Estimated
temporal parameters are qualified in the underlying records.

```sh
uv run tuus validate
uv run tuus coverage
uv run tuus evaluate
uv run pytest
npm --prefix web test
```

The coverage report records temporal density, distinct kairolexicon support,
communicative-function coverage, and semantic proximity. Uncovered temporal
regions resolve to the nearest supported material. Generation prompts and
evaluation cases are versioned independently of the runtime artifacts.

Deployment configuration is supplied in `deploy/`. The runtime uses ordinary
HTTP and immutable local artifacts; serving is independent of the hosting provider.
No account or persistent input history is maintained.

The repository is licensed under the Mozilla Public License 2.0.

Telechronistic micro-utterance synthesis from user-defined temporal priors over curated kairolexica.
