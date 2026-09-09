# Use local semantic evidence retrieval

The evidence archive uses a local embedding model with Qdrant rather than deterministic hash vectors or a hosted embedding API. This preserves local processing of supplier evidence while enabling meaningful semantic retrieval; every result must retain its document, page, and passage for procurement review.

## Considered Options

- Deterministic hash vectors: easy to run but provide no semantic relevance.
- Hosted embeddings: stronger managed option but move supplier evidence outside the local environment.
- Local embedding model: adds model management but supports private, meaningful retrieval.
