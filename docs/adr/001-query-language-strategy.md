# ADR-001: Query Language Strategy

## Status
Accepted

## Context
The Bitext e-commerce dataset (44,884 rows) is entirely in English. However,
the site's actual users will ask questions in Turkish (and possibly mixed
languages). Since there's no lexical overlap between the two languages,
simple keyword search won't work; embedding-based semantic search is
required, but the chosen embedding model must be able to capture
cross-lingual similarity — otherwise a Turkish question would return
meaningless/random results against the English dataset.

## Decision
A multilingual embedding model will be used. The user's Turkish question
will be embedded directly, without going through any translation step, and
compared against the English dataset records in the same vector space.

Selected model: `gemini-embedding-001` (Google GenAI SDK,
`client.models.embed_content`). It supports over 100 languages, with a
default output dimensionality of 3072; this can be reduced to a smaller
size (e.g., 768) via the `output_dimensionality` parameter (Matryoshka
representation — the vectors remain usable quality even after truncation).
There's also a `task_type` parameter: `RETRIEVAL_DOCUMENT` should be used
when indexing the dataset, and `RETRIEVAL_QUERY` when embedding the user's
query — if the same `task_type` isn't used consistently, similarity scores
degrade, so task_type consistency between ingestion and query time is
critical.

Qdrant collection vector size: to balance cost/storage against search
quality, `output_dimensionality=768` is recommended (44,884 × 768 instead
of 44,884 × 3072 — roughly 4x smaller storage, with practically negligible
quality loss).

## Consequences
- No extra translation LLM call → low latency, low cost.
- The Qdrant collection's vector size (`size`) will be fixed based on the
  chosen embedding model's output dimensionality.
- Cross-lingual retrieval quality may be somewhat lower than same-language
  retrieval; this risk is accepted (the alternative, a translation step,
  would have added extra cost/latency).
- TODO: Once the embedding model choice is finalized (dimensionality, max
  tokens, cost), this ADR will be updated or backed by a separate
  ADR-00X.

## UPDATE: Embedding provider moved to Voyage AI

A daily quota of 1000 requests was discovered on the free tier of the
Gemini embedding API (see ADR-006), which made a full ingestion of 44,884
rows impractical. The embedding provider was moved to **Voyage AI**
(`voyage-4-large`); generation (answer production) remains on Gemini.

What changed: `output_dimensionality=1024` (Voyage's default), and the
`input_type` parameter replaces Gemini's `task_type` (`document` /
`query`). The core decision of this ADR (multilingual embedding without a
translation step, compared in the same vector space) hasn't changed —
only the provider did. See ADR-006 for details.

## Related
[[glossary]], ADR-003 (embedding content), ADR-006 (ingestion strategy)
