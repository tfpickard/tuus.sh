# Verification record

The implementation was evaluated on 11 October 2026. Structural and browser
checks pass; generation-quality acceptance has not been achieved. The work
remains a draft implementation rather than a production release.

## Corpus and immutable artifacts

`tuus validate` accepts 113 entries in 18 kairolexica without errors. The separate
candidate set contains 11 entries in five groups and validates through
`tuus validate --candidates`; candidates are excluded from runtime retrieval and
the container bundle. Source-attested and constructed examples remain distinct.
Temporal parameters record their confidence and estimated fade status.

`tuus coverage` produces `coverage.html`, `coverage.json` and `coverage.csv`.
These contain annual signature density, per-kairolexicon and communicative-function
support, semantic neighbors and cosine-graph clusters. Zero-density integer years
are 1970–1973, 2004 and 2028–2030. Thin years are explicitly reported. These are
curation observations; the embedding clusters are not measures of corpus quality.
Context-specific communicative coverage can be thinner than aggregate coverage.

## Numerical and request-path verification

The seeded sampler report uses 10,000 draws per case. Tight-prior center coverage
exceeds 95% at each tested center. A boundary-truncated 1:3 mixture produces
25.40% first-component samples against 25%, within the stated two-percentage-point
tolerance, and integrates to 1.0000000000000002. Actual retrieved era proportions
are 24.45% against 25%. One thousand axis probes produce no empty retrievals.
Synthetic 1:100 sparse-neighbor and 1:10 overlapping-population tests verify that
kairolexicon size does not determine selection probability.

The Python suite passes 39 tests. Request-path instrumentation raises if corpus
encoding is attempted, and the runtime rejects every model identifier except the
approved small model. Schema, duplicate, example, function/context eligibility,
negation, quantity, recipient-role, grammatical-role, malformed-review, cached judging
mode and URL-prefix
regressions are included. Runtime lexical guards supplement semantic evaluation;
they do not prove that arbitrary coined jargon or every actor-role error is absent.

## Browser and deployment verification

All eight Playwright tests pass with no skipped or flaky cases. They exercise
component addition, removal, displacement, width and relative-weight changes,
keyboard operation, mobile layout, error states, copying, re-sampling and actual
model generation at root and `/tuus/`. The displayed composite matches the
normalized prior within the browser test's numerical tolerance. Screenshots are
committed in this directory, including all three specified prior configurations.

The packaged service runs as UID 10001. Its root and `/tuus/` instances return
identical HTML and load the same relative assets. Both health endpoints return
HTTP 200. Actual synthesis at both mounts returns the same correctly scoped
request: "Morgan, got your ears on? Collect the printouts before 15:00."
The packaged requests take 20.55 and 17.99 seconds respectively, with a tight 1976
prior. Image identity, asset identity, responses and measurements are recorded
in `deployment.json`.
Public deployment has not been performed: VPS and DNS access are not configured.

## Evaluation and performance

The final fixed grid contains 288 cases: 12 intents, eight priors and three seeds.
Independent model-assisted reviews bind to exact utterance checksums and inspect
intent performance, supplied-marker fidelity and unlicensed jargon separately.
Generation errors count as failures. Acceptance targets remain 95% intent,
95% fidelity and 100% absence of unlicensed jargon. Reviews are not independent
human certification.

| Criterion | Final score | Target | Result |
| --- | --- | --- | --- |
| Intent | 75.00% (216/288) | 95% | Below target |
| Lexical fidelity | 81.25% (234/288) | 95% | Below target |
| Jargon-free successful generation | 92.36% (266/288) | 100% | Below target |

All three criteria pass jointly in 187/288 cases. There are 21 generation errors
and one successful output with identified unlicensed slang. Errors remain in the
denominator for every criterion. The absence of an identified violation in a
review is not an exhaustive lexical-safety proof.

| Prior | Cases | Intent passes | Fidelity passes | Jargon-clear successful cases | Errors |
| --- | --- | --- | --- | --- | --- |
| CB, 1976 | 36 | 30 | 33 | 33 | 3 |
| Valley, 1982 | 36 | 27 | 33 | 33 | 3 |
| Internet, 1996 | 36 | 27 | 31 | 32 | 4 |
| Tight, 2012 | 36 | 25 | 14 | 27 | 8 |
| Broad, 2012 | 36 | 22 | 25 | 34 | 2 |
| Two-component mixture | 36 | 25 | 32 | 35 | 1 |
| Recent, 2026 | 36 | 30 | 33 | 36 | 0 |
| Uncovered, 2030 | 36 | 30 | 33 | 36 | 0 |

Remaining failures include indirect apologies that change the recipient's role,
copied example tasks or deadlines, and markers used without their required
meaning or grammatical relation. Ambiguous clipped expressions and conventional
self-appraisal remain visible in review reasons for human calibration. Compatible
communicative coverage and small-model assembly require further work. Evaluation
cache checks prevent switching judging modes from relabeling or overwriting the
independently reviewed evidence.

An earlier fully reviewed baseline is preserved under
`evals/archive/generation_v5_evaluated/`, with its corpus, prompt and implementation
snapshot: 53.82% intent, 70.14% fidelity, 97.22% absence of unlicensed jargon,
and six generation errors. The archived implementation, prompt and corpus
checksums match their baseline fingerprints. The corpus checksum is reproduced
with its archived schema, which predates the additional grammatical-role fields.

`latency.json` records five sequential default-prior requests without evaluation
or browser synthesis traffic. All five complete successfully through the runtime
guards; this small benchmark does not replace independent semantic evaluation.
Median retrieval time is 9.02 milliseconds, median end-to-end time is 15.52 seconds,
and p95 end-to-end time is 21.86 seconds. Runtime bundle loading takes 240
milliseconds. The model is Qwen3-4B-Instruct-2507, Q4_K_M, on x86-64 with a
two-core CPU quota and an 8 GiB memory quota. The model endpoint is loopback;
no hosted-model network latency has been excluded. The sub-second target is not
met. Corpus, prompt and implementation fingerprints match the evaluated baseline.
The baseline's aggregation elapsed time excludes checkpointed generation;
actual request timings are recorded separately.

## Repository metadata

The original Mozilla Public License 2.0 is retained. `AGENTS.md` and `CLAUDE.md`
record the locked taxonomy, codepoint, identifier and register requirements.
The repository-description update was rejected by the connected GitHub
integration with HTTP 403, `Resource not accessible by integration`. The owner
must set the exact required description through repository settings.
