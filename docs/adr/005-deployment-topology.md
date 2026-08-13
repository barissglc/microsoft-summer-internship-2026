# ADR-005: Deployment Topology

## Status
Accepted

## Context
The system is small-scale (44,884 records, ~100-150MB of vector data). The
user has their own Ubuntu/Debian server and wants all components (Qdrant,
FastAPI backend, frontend) to run on that server.

**Important security note**: Server access credentials (SSH host/user/
password) were **not written** to this ADR or to any file in the repo.
This information was shared in plain text during the chat; recommendation:
rotate the password and, if possible, use SSH key auth instead of a
password. Server connection details must never be committed to git — they
should only be used manually during deployment or via a secrets
manager/CI secret store.

## Decision
A Docker-based multi-container topology on a single server:

- **Qdrant**: The official `qdrant/qdrant` Docker image, with a volume
  persisted to disk (`qdrant_storage/`).
- **FastAPI backend**: A separate container with its own Dockerfile;
  connects to Qdrant over the container network (e.g.,
  `http://qdrant:6333`). The Gemini API key is read from `.env` (not
  committed to git, see `.gitignore`).
- **Frontend**: A static build (or separate container) on the same
  server, connecting to the backend's API via reverse-proxy/CORS.

The steps for connecting to and setting up the server (the docker compose
file, how environment variables are passed) will be written as a separate
`docker-compose.yml` and deploy script during the implementation phase;
this ADR only fixes the architecture (which component runs where).

## Consequences
- A single server means a single point of failure, but at this scale
  (low traffic, 44,884 fixed records) this is an acceptable risk.
- If migrating to Qdrant Cloud becomes necessary, only the
  `QDRANT_URL`/`QDRANT_API_KEY` environment variables change — no other
  code changes are required.
- Secret information always stays in `.env` or a secrets mechanism on the
  server, and is never written into an ADR, the glossary, or the code.

## Related
[[glossary]], ADR-001
