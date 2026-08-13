# ADR-006: Full Data Ingestion Strategy

## Status
Accepted

## Context
During pilot testing (a 100-row trial with `scripts/pilot_verify.py`, and a
stratified 90-row trial in the actual run), it was observed that the
Gemini embedding API's free tier
`EmbedContentRequestsPerMinutePerUserPerProjectPerModel-FreeTier` quota is
in practice limited to roughly 100 embedded texts per minute (a single
batch call of 100 consumes the entire quota). Instead of enabling billing
or shrinking the dataset, the user preferred a throttled background job
running on the free quota. For 44,884 rows, this means a job lasting
roughly 7-9 hours at a rate of ~90 rows/minute.

## Decision
The `scripts/ingest.py` script works as follows:

- **Deterministic point ID**: Each Qdrant point's id is the row index from
  the CSV (0-indexed). This way, if the script is interrupted and rerun,
  re-upserting the same row doesn't create a new record but overwrites the
  existing one (idempotent).
- **Checkpoint file**: `ingestion_checkpoint.json` holds the index of the
  last successfully processed row. On startup, the script reads this file
  and resumes from where it left off.
- **Throttling**: After each batch (≤90 rows), a wait of roughly 61
  seconds is applied (minus the batch's own duration) so the next batch
  doesn't land in the same per-minute quota window. If a 429 error still
  occurs, an additional fixed 60s retry (exponential-ish) is applied.
- **task_type consistency**: `RETRIEVAL_DOCUMENT` is used during
  ingestion, and `RETRIEVAL_QUERY` at query time (ADR-001).
- **Normalization**: Truncated embeddings from
  `output_dimensionality=768` are L2-normalized within the script so that
  Qdrant's Cosine distance works correctly (vectors are not guaranteed to
  remain normalized after Matryoshka/MRL truncation).
- **Persistent Qdrant**: A real Qdrant Docker container (persisting to the
  `qdrant_storage/` volume) is used instead of `:memory:`, so data isn't
  lost if the script is interrupted.

## Consequences
- The first full ingestion will take ~7-9 hours; during this time, since
  the same Gemini API key's embedding quota will be fully used, the
  backend's live query-time embedding calls may share the same quota
  during this window and get delayed. Development/testing should be
  scheduled outside this window, or a separate API key should be used.
- If billing is enabled later, the only change needed is to lower
  `BATCH_SIZE`/wait time — the script's logic stays the same.
- If the script is interrupted (computer shutdown, network error, etc.),
  the checkpoint file lets it resume from where it left off.

## UPDATE (same day): Daily quota discovered — plan invalidated

At row 630, ingestion stopped with `429 RESOURCE_EXHAUSTED`. The error
message revealed a separate **daily** quota in addition to the per-minute
one: `EmbedContentRequestsPerDayPerProjectPerModel-FreeTier`,
`quotaValue: 1000`. That is, the free tier allows a total of ~1000
embedded texts per day for `gemini-embedding-001` (this limit is shared
across local pilot trials, server-side ingestion, and chat testing, all
under the same API key).

This invalidates ADR-006's original "~7-9 hours" assumption: at a rate of
1000/day, 44,884 rows would take **~45 days** — the throttled background
job approach is impractical under this quota.

Conclusion: enabling billing (pay-as-you-go) is no longer optional but
**required** in order to index all 44,884 rows in a reasonable amount of
time. The user was asked again with this new information (see chat log);
this ADR will be updated based on the decision made after billing is
enabled.

## CONCLUSION: Embedding provider switched to Voyage AI

Even after enabling billing on Gemini, a separate project/billing issue
(`403 PERMISSION_DENIED`) occurred. As a result, the embedding provider
was moved to **Voyage AI** (`voyage-4-large` model):

- The **first 200M tokens per account are free** — the 44,884-row dataset
  (~4-5M tokens) is well under this limit, so it remained entirely free.
- No daily request quota (Gemini's 1000/day limit doesn't apply here);
  only the initial trial, before a payment method was added, had a low
  rate limit (3 requests/min) — once a card was added, it went up to
  standard speed (~300 rows/sec ingestion throughput).
- Because of this, `scripts/ingest.py` removed the throttling logic:
  instead of a fixed `MIN_SECONDS_BETWEEN_BATCHES` wait, there's now only
  a short retry on 429/503 errors.
- Answer generation is still on Gemini (`gemini-flash-lite-latest`, free
  tier) — only the embedding provider changed.

The full 44,884-row ingestion completed successfully with this
configuration. See ADR-001 (update note).

## Related
[[glossary]], ADR-001, ADR-003
