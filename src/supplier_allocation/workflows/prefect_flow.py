from __future__ import annotations

from pathlib import Path

from prefect import flow, task

from ..allocation import optimise_allocation
from ..database import get_engine, load_operating_data, persist_agent_traces, persist_assessments, persist_extracted_facts
from ..models import AllocationConstraint
from ..retrieval import index_documents
from .verification_graph import build_verification_graph


@task
def run_verification(raw_directory: str):
    return build_verification_graph().invoke({"raw_directory": raw_directory})


@task
def index_evidence(raw_directory: str) -> int:
    return index_documents(Path(raw_directory))


@flow(name="quarterly-supplier-allocation")
def quarterly_supplier_allocation(raw_directory: str) -> dict:
    state = run_verification(raw_directory)
    scorecard = state["scorecard"]
    allocation = optimise_allocation(scorecard, AllocationConstraint())
    engine = get_engine()
    persist_assessments(engine, state["commitments"], state["verifications"], scorecard)
    persist_agent_traces(engine, state["llm_assessments"])
    persist_extracted_facts(engine, state["commitments"], Path(raw_directory))
    load_operating_data(engine, Path(raw_directory))
    indexed_count = index_evidence(raw_directory)
    return {
        "supplier_count": len(scorecard),
        "indexed_documents": indexed_count,
        "allocation": allocation.to_dict(orient="records"),
        "llm_assessments": {
            supplier_id: assessment.model_dump() for supplier_id, assessment in state["llm_assessments"].items()
        },
    }
