# ADR-002: Low Similarity Score Behavior

## Status
Accepted

## Context
Qdrant always returns the top-k results — even if a question is completely
unrelated to the intended topic, it will still return the "closest"
records. Setting a similarity threshold and automatically falling back to
a human handoff (fallback response) below that threshold would be the
safest way to prevent hallucination, but this requires predicting in
advance when the decision would fire correctly versus incorrectly, and
calls for a separate calibration effort on the dataset.

## Decision
A fixed numeric threshold will not be used. The top-k results from Qdrant
(along with their scores) will always be passed to Gemini as context; the
Gemini prompt will explicitly include the instruction "if the provided
examples aren't sufficiently relevant to the question, state that you're
unsure and direct the user to customer support." In other words, the
decision of "when to hand off to a human" is moved from the retrieval
layer to the LLM layer.

**Additional decision**: The raw similarity score (cosine score) returned
by Qdrant will also be included in the prompt alongside each retrieved
example (e.g., "[similarity: 0.82] Question: ... Answer: ..."). This way,
the decision moved to the LLM layer isn't entirely blind — if the scores
are low (e.g., all top-5 scores are around 0.4), Gemini can read this as a
signal that "none of these are actually relevant" and follow the
uncertainty instruction more reliably. This was added to reduce the risk
that, given the nature of the dataset (46 intents, each with ~1000 near
paraphrases), even an out-of-domain question could cause the top-5 to
return 5 answers that are "fluent but irrelevant."

## Consequences
- Simpler retrieval layer (no threshold calibration or A/B testing
  needed).
- The quality of the Gemini prompt becomes critical — the system's
  hallucination risk depends heavily on prompt design. The prompt must
  include instructions to: (a) not go beyond the provided examples, (b)
  say so when unsure, and (c) avoid fabricating answers on topics that
  require definitive policy, such as returns/payments.
- If hallucination cases are observed in the future, this ADR can be
  revised and a score-threshold layer added later (this ADR may then be
  superseded).

## Related
[[glossary]]
