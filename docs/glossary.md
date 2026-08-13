# Glossary

Short definitions of terms used throughout this project. New terms/
decisions are added here as they come up.

> **Note:** Some entries below describe the project's initial design
> (e.g. Gemini for embeddings, 768 dimensions). The embedding provider
> was later switched to Voyage AI (`voyage-4-large`, 1024 dimensions) —
> see ADR-001 and ADR-006 for the final configuration.

## Vector Search Fundamentals

**Embedding**: The process of converting a piece of text (a question, a
sentence) into a fixed-length array of numbers (a vector). Texts that are
semantically close end up with vectors that are close to each other too.
In this project, a multilingual Gemini embedding model is used to embed
customer questions (see ADR-001).

**Vector**: The output of the embedding process; e.g., a list of 768
numbers.

**gemini-embedding-001**: The Gemini embedding model used in this
project. It supports 100+ languages, produces a 3072-dimensional vector
by default, and can be reduced via `output_dimensionality` (768 is
planned for this project).

**task_type (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)**: A parameter in the
Gemini embedding API that specifies the "role" of the text being
embedded. A different task_type is used when loading the dataset into
Qdrant (`RETRIEVAL_DOCUMENT`) versus when embedding the user's live
question (`RETRIEVAL_QUERY`) — both are called through the same
embed_content function, but this parameter directly affects search
quality.

**Qdrant**: An open-source vector database. It stores millions of
vectors and quickly finds the ones "closest" to a given query vector
(nearest neighbor search). In this project, it's used to store the
vectors of 44,884 customer questions and find the ones most similar to
a user's question.

**Collection**: A table-like structure in Qdrant where vectors are
stored. This project uses a single collection (e.g., `support_qa`).

**Point**: A single record in a Qdrant collection — consisting of a
vector, a payload, and an id. In this project, each point corresponds to
one question-answer row in the dataset.

**Payload**: Additional data (metadata) attached to a point that isn't
part of the search but is returned along with the result. In this
project, the `response`, `category`, and `intent` fields are stored in
the payload (see ADR-003).

**Distance metric / Cosine similarity**: A method for measuring how
"close" two vectors are. This is chosen when creating a collection in
Qdrant (Cosine is planned for this project — the standard choice for
text embeddings).

**Top-k**: The k results closest to a query. E.g., "top-5" = the 5 most
similar records.

**Semantic search**: Search based on meaning similarity rather than
keyword matching. The core capability Qdrant provides in this project.

## RAG / LLM Layer

**RAG (Retrieval-Augmented Generation)**: A method that first retrieves
relevant records from a knowledge source (Qdrant in this project), then
feeds those records as context to an LLM (Gemini in this project) to
produce the final answer. The project as a whole is essentially a RAG
system.

**Gemini**: Google's LLM family. In this project it can serve two
different roles: (1) generating embeddings, and (2) writing the final,
well-formed customer answer using the examples retrieved from Qdrant.

**Context**: The top-k question/answer examples from Qdrant, given to the
LLM within the prompt. Gemini generates its answer based on this context.

**Hallucination**: An LLM fabricating information not present in its
context. In this project, this carries particular risk on topics that
require policy, such as returns/payments (see ADR-002).

## Dataset Terms (Bitext Retail/E-commerce Dataset)

**instruction**: The customer question/request in the dataset (English).

**response**: The canned, example customer support answer in the
dataset.

**category**: 13 top-level topic groups (ORDER, ACCOUNT, DELIVERY,
etc.).

**intent**: 46 specific intent classes (e.g., `cancel_order`,
`recover_password`). Each category contains multiple intents. In this
project, this isn't used as a mandatory classification step but as an
additional signal (see ADR-004).

**tags**: Linguistic variation tags in the dataset (M, L, B, I, C, N, P,
Q, W, K, E, Z) — e.g., Z = variation containing a typo, W = variation
containing rude/slang language. Not used in this project; they merely
explain why the dataset looks so varied/repetitive.

## Backend Terms

**FastAPI**: A fast, modern, Python-based web API framework. This
project plans to build its backend (the service that takes the user's
question and routes it to Qdrant + Gemini) on top of it.

**Ingestion**: The process of processing (embedding) the 44,884-row
dataset once and loading it into Qdrant. This is not conceived as a
service, but as a one-time, rerunnable batch script.

## ADR (Architecture Decision Record)

Documents that record the architectural decisions made in this project,
along with their rationale. Kept in the `docs/adr/` folder, numbered
sequentially. Each ADR consists of the sections: Status, Context,
Decision, Consequences.
