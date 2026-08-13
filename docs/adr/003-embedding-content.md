# ADR-003: What Gets Embedded

## Status
Accepted

## Context
Each row of the dataset has `instruction` (customer question), `response`
(canned answer), `category`, and `intent` fields. Since the user's live
question will always come in the form of a "question," retrieval's core
job is to find question↔question similarity. Including the `response`
text in the vector as well risks "polluting" the vector space with answer
vocabulary and degrading the actual question-to-question similarity.

## Decision
Only the `instruction` field will be embedded into Qdrant. The `response`,
`category`, `intent`, and `tags` fields will not go into the vector;
instead they'll be stored in the Qdrant point's **payload**. After
retrieval, these payloads (particularly `response` and `category`) will be
passed to Gemini as context; `category`/`intent` can also be used for
filtering later on (e.g., restricting to a specific category).

## Consequences
- Vector quality stays focused on pure question-to-question similarity.
- Since the response is stored in the payload, no separate lookup is
  needed to provide context to Gemini — Qdrant returns both similar
  questions and their answers in a single query.
- Because `intent`/`category` live in the payload, the "use as a signal"
  approach in ADR-004 is directly possible.

## Related
[[glossary]], ADR-001, ADR-004
