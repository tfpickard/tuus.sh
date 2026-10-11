# Implementation architecture

The offline layer validates accepted kairolexica, embeds semantic descriptions,
and produces immutable vectors, a checksum manifest, a JSON schema and coverage
reports. Candidates validate separately and remain outside the runtime bundle.
Prompts and fixed evaluation cases are independently versioned. Evaluations
fingerprint the corpus, prompt, implementation and model artifacts; reviewed
scores bind to each exact utterance by checksum.

The Python service loads and verifies the bundle at startup. Each request embeds
only its short intent, samples three temporal positions, and retrieves compatible
material. Context and communicative-function eligibility precede temporal
selection; positive contexts and incompatible contexts are compiled at startup.
Each kairolexicon receives its maximum entry likelihood rather than a
sum proportional to its population. An intent-specific coverage gap resolves to
the nearest compatible support. Cosine similarity ranks eligible entries within
the selected kairolexicon. Dates and provenance do not enter embedding text.

A single approved 4B model assembles one utterance through ordinary HTTP. Known
lexical violations, omitted explicit details, and actor inversions permit one
corrective attempt before an unavailable response. Ordinary action inflections
and supplied action-equivalent markers are recognized. Grammatical-role checks
distinguish fragments and closings from completed clauses, and require representation
of each retrieved kairolexicon. The model returns an internal expression-ID list
alongside the utterance; only the utterance reaches the browser. An omitted explicitly
named recipient can be restored as neutral direct address; other semantic
properties require offline review. Runtime guards do not prove the absence of
arbitrary newly coined jargon. Independent offline review supplies that evidence.

The browser has one intent input and one temporal-prior editor. Its Gaussian
components are independently truncated to 1970–2030 before relative weights are
normalized. The composite curve displays the resulting density. The same static
build resolves assets and synthesis relative to its document location and can
be mounted at root or a configured prefix. A Python service, a private inference
service and an ordinary reverse proxy form the portable deployment. Containers
package these processes without changing their interfaces.

## Dependency rationale

| Dependency | Purpose |
| --- | --- |
| FastAPI | Portable HTTP request routing and validation integration. |
| Pydantic | Directly used shared corpus and prior schemas with rejected extra fields. |
| Uvicorn | ASGI serving independent of the hosting provider. |
| NumPy | Fixed semantic-vector operations and offline numerical reports. |
| HTTPX | Small-model HTTP transport, with explicit timeouts and proxy behavior. |
| ONNX Runtime | Quantized local query encoding and offline corpus encoding. |
| Tokenizers | The pinned embedding model tokenizer. |
| TypeScript | Static verification of the prior editor and browser integration. |
| Vite | Build-time relative asset bundling; absent from the runtime service. |
| pytest | Numerical, schema, retrieval and request-path verification. |
| Playwright | Real-browser interaction, clipboard, responsive and subpath verification. |
| Hatchling | Standard Python package build backend; absent from application request handling. |

No application database, account service, vector database or client framework is
required. The corpus is curated project data, rather than a request-time service.

## V1 decisions

| Question | Implemented default and rationale |
| --- | --- |
| Stack | Python service and offline CLI; TypeScript/SVG browser editor. Each layer uses its ordinary numerical or browser interfaces. |
| Hosting | Portable Linux service deployment with optional containers and Caddy. The provider remains unselected; deployment requires VPS and DNS access. |
| Runtime model | Local Qwen3-4B-Instruct-2507, Q4_K_M, through a private HTTP endpoint. There is no per-request provider charge; hardware capacity and hosting carry fixed costs. |
| Embeddings | Pinned quantized e5-small-v2 ONNX encoder, 384 dimensions. Corpus vectors are offline artifacts; only the short intent is encoded per request. |
| Width bounds | Sigma 0.5–8 years: a precise annual target remains possible while the widest component retains a localized peak. |
| Component cap | Six: the editor retains legible individual handles and a bounded payload. |
| Initial prior | Four equally weighted components at 1976, 1992, 2008 and 2024, each with sigma 8. Untouched synthesis samples broadly across the axis. |
| Output count | One utterance; re-sampling supplies another without a selection panel. |
| Touch | Native pointer handling plus responsive layout; mouse remains primary. Keyboard adjustments supplement direct manipulation. |
| Corpus target | Quality-gated acceptance rather than uniform quotas. The current accepted set has 113 entries in 18 kairolexica; thin decades and gaps remain visible in the coverage report. |
| Provenance display | Omitted from the v1 output surface. Selection records remain available in offline evaluation evidence. |
| API | UI only as a supported product surface; the same-origin synthesis endpoint is an internal implementation interface. |

The sub-second end-to-end target remains a measured target rather than a claim.
Local CPU inference and semantic generation acceptance require evidence in the
verification reports before a production release is represented as ready.
