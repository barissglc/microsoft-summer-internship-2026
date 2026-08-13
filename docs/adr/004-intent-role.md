# ADR-004: The Role of the Intent Field

## Status
Accepted

## Context
The dataset's `intent` field is very clean: 46 fixed classes, each with
~1000 examples. This theoretically allows for bypassing retrieval by
first performing "intent classification" and then directly returning a
canonical answer for that intent (a more deterministic but less flexible
architecture). Alternatively, using intent only as a "confidence signal"
lets the system behave sensibly even on questions outside/unexpected by
the dataset.

## Decision
Intent will not be a mandatory intermediate step. Semantic search (top-k)
will always run; the `intent`/`category` fields in the payload of the
returned results will only be added to Gemini's context as an additional
signal (e.g., "the likely category of this question: ORDER/cancel_order").
No separate intent-classification step or canonical-answer shortcut will
be built.

## Consequences
- The architecture stays simple: a single retrieval step plus a single
  generation step.
- The system can produce reasonable answers even on questions not in the
  dataset or on mixed questions (it isn't locked into 46 classes).
- If analytics later reveal frequent errors on certain intents, a
  shortcut/rule specific to that intent can be added afterward — this ADR
  would then be revisited.

## Related
[[glossary]], ADR-003
