# Supplier Allocation Intelligence

An end-to-end, human-in-the-loop prototype for quarterly procurement allocation at XYZ Industrial Systems.

The system generates a synthetic supplier archive, extracts contractual commitments with evidence references, compares commitments against observed delivery and quality performance, detects drift, and proposes an allocation scenario. It never creates purchase orders: a procurement reviewer approves or adjusts the recommendation.

## Quick start

```bash
UV_PROJECT_ENVIRONMENT=.uv uv sync --all-groups
UV_PROJECT_ENVIRONMENT=.uv uv run python scripts/generate_demo_data.py
UV_PROJECT_ENVIRONMENT=.uv uv run python scripts/run_pipeline.py
UV_PROJECT_ENVIRONMENT=.uv uv run streamlit run app.py
```

## Prototype flow

1. Generate synthetic contracts, audits, certificates, ERP delivery data, and defect records.
2. Extract source-grounded supplier commitments.
3. Verify delivery, quality, capacity, certification, and country-risk signals.
4. Create a reviewable supplier scorecard and detect performance drift.
5. Optimise an allocation under demand, capacity, concentration, and country-exposure constraints.

## Full local stack

`docker compose up -d` starts PostgreSQL (`localhost:5432`), Qdrant (`localhost:6333`), and Prefect (`localhost:4200`). Then run:

```bash
UV_PROJECT_ENVIRONMENT=.uv uv run python scripts/run_prefect_flow.py
DBT_PROFILES_DIR=dbt UV_PROJECT_ENVIRONMENT=.uv uv run dbt --project-dir dbt run
```

The flow uses LangGraph to coordinate extraction, verification, and scoring; stages operational data in DuckDB; persists supplier facts, assessments, allocations, and approvals to PostgreSQL; and indexes PDF passages in Qdrant for evidence retrieval.

## Safety boundary

All datasets are synthetic. The allocation output is a recommendation for human approval, not an order-placement instruction.
