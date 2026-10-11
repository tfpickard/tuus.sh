# Offline evaluation review protocol

The fixed grid is 12 intents crossed with eight priors and three seeds. Generation
records are append-only and carry corpus, prompt and case fingerprints. Reviews
must cite an utterance checksum, so a judgment cannot be reused for changed output.

Review the actual utterance, intent and retrieved material. Evaluate three criteria
independently:

- Intent: the speech act is actually performed; material names, actor roles,
  quantities, deadlines and negation are preserved; no extra required tasks are added.
- Fidelity: at least one supplied marker is used in its intended sense and grammatical
  role; the sampled mix is represented when multiple usable kairolexica are available.
  Unsupported grammatical repurposing fails this criterion.
- Jargon: list dated or specialized expressions not licensed by retrieved material.
  Neutral connective language and the user's own expressions are exempt. A list with
  no entries records that no violation was identified, not a proof of exhaustive safety.

Research agents review era-specific slices independently of the generating model.
They must inspect all assigned records, never automatically approve them based on
marker presence. Record concise evidence for each decision. Review artifacts are
model-assisted judgments, not human certification. Ambiguous judgments remain
visible for subsequent human calibration.

The evaluated runtime includes neutral recipient restoration: when a direct
speech act names one recipient and synthesis omits that name, it prefixes a
salutation using the exact input name. Existing names and actor inversions are
not rewritten. This repair adds no tasks, facts or dated vocabulary. Semantic
review still evaluates the final utterance in full.

Each JSONL review contains `id`, `utterance_sha256`, `reviewer`, and `judgment`.
The judgment has boolean `intent`, boolean `fidelity`, list-of-string `jargon`, and
string `reason`. Generation failures receive failed scores during aggregation.
