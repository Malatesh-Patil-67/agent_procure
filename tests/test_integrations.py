import os

import pytest


@pytest.mark.skipif(os.getenv("RUN_INTEGRATION_TESTS") != "true", reason="requires local Docker and Ollama services")
def test_qdrant_retrieval_and_postgres_trace_persistence() -> None:
    from pathlib import Path

    from supplier_allocation.database import get_engine, load_agent_traces
    from supplier_allocation.retrieval import index_documents, search_evidence

    root = Path(__file__).resolve().parents[1]
    index_documents(root / "data" / "raw")
    assert any(item["supplier_id"] == "SUP-001" for item in search_evidence("SUP-001 capacity", limit=3))
    assert isinstance(load_agent_traces(get_engine(), "SUP-001"), list)
