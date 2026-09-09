# Supplier Allocation Intelligence

An end-to-end, human-in-the-loop prototype for quarterly procurement allocation at Example Manufacturing SE, a fictional company.

The system generates a synthetic supplier archive, extracts contractual commitments with evidence references, compares commitments against observed delivery and quality performance, detects drift, and proposes an allocation scenario. It never creates purchase orders: a procurement reviewer approves or adjusts the recommendation.

## Quick start

Install uv once if it is not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installation, then run:

```bash
uv sync --all-groups
uv run python scripts/generate_demo_data.py
uv run python scripts/run_pipeline.py
uv run streamlit run app.py
```

## Prototype flow

1. Generate synthetic contracts, audits, certificates, ERP delivery data, and defect records.
2. Extract source-grounded supplier commitments.
3. Verify delivery, quality, capacity, certification, and country-risk signals.
4. Create a reviewable supplier scorecard and detect performance drift.
5. Optimise an allocation under demand, capacity, concentration, and country-exposure constraints.

## Architecture

```mermaid
flowchart TD
    documents["Synthetic supplier archive\nContracts · audits · certificates"]
    operations["Operational data\nDelivery history · defects · demand"]

    subgraph ingest["Ingestion and evidence"]
        document_reader["unstructured + pdfplumber\nDocument text and page evidence"]
        duckdb["DuckDB\nOperational staging"]
        extractor["Pydantic extraction agent\nSupplier commitments"]
    end

    subgraph workflow["Prefect + LangGraph workflow"]
        verification["Verification agents\nDelivery · quality · capacity"]
        drift["Performance-drift assessment"]
        scorecard["Supplier scorecard\nDeterministic control result"]
        ollama["Optional local Ollama agent\nEvidence-grounded narrative"]
    end

    subgraph decision["Human-in-the-loop decision"]
        optimiser["CVXPY allocation engine\nCost, capacity, concentration, country risk"]
        streamlit["Streamlit review dashboard"]
        approval["Procurement committee\nApprove, reject, or adjust"]
    end

    postgres[("PostgreSQL\nFacts · assessments · allocations · approvals")]
    qdrant[("Qdrant\nDocument evidence retrieval")]
    dbt["dbt\nSupplier-delivery analytics view"]

    documents --> document_reader --> extractor
    operations --> duckdb --> verification
    extractor --> verification --> drift --> scorecard
    extractor --> postgres
    scorecard --> postgres
    document_reader --> qdrant
    scorecard --> ollama --> streamlit
    scorecard --> optimiser --> streamlit --> approval --> postgres
    postgres --> dbt
    qdrant --> streamlit
```

`Prefect` schedules the end-to-end flow, while `LangGraph` defines the extraction, verification, scoring, and optional local-LLM agent sequence. Deterministic verification remains authoritative; the local Ollama agent only adds a grounded explanation for human review.

## Full local stack

`docker compose up -d` starts PostgreSQL (`localhost:5433`), Qdrant (`localhost:6333`), and Prefect (`localhost:4200`). Then run:

```bash
uv run python scripts/run_prefect_flow.py
uv run dbt run --project-dir dbt --profiles-dir dbt
```

The flow uses LangGraph to coordinate extraction, verification, and scoring; stages operational data in DuckDB; persists supplier facts, assessments, allocations, and approvals to PostgreSQL; and indexes PDF passages in Qdrant for evidence retrieval.

## Local LLM agents

The deterministic checks remain the control result. Ollama adds evidence-grounded procurement narratives without sending supplier evidence to a cloud model.

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
cp .env.example .env
# Set OLLAMA_ENABLED=true in .env
uv run python scripts/run_prefect_flow.py
```

The default is `qwen2.5:3b`, a smaller model suitable for local development. Change `OLLAMA_MODEL` in `.env` to use another locally installed Ollama model.

## Safety boundary

All datasets are synthetic. The allocation output is a recommendation for human approval, not an order-placement instruction.
