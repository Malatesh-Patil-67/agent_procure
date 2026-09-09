from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph

from ..extraction import extract_all
from ..llm_agents import assess_all_suppliers, ollama_enabled
from ..scoring import build_scorecard
from ..verification import verify_all


class VerificationState(TypedDict, total=False):
    raw_directory: str
    commitments: list
    verifications: list
    scorecard: object
    llm_assessments: dict


def _extract(state: VerificationState) -> VerificationState:
    commitments = extract_all(Path(state["raw_directory"]) / "contracts")
    return {"commitments": commitments}


def _verify(state: VerificationState) -> VerificationState:
    raw_directory = Path(state["raw_directory"])
    return {"verifications": verify_all(raw_directory, state["commitments"])}


def _score(state: VerificationState) -> VerificationState:
    return {"scorecard": build_scorecard(state["commitments"], state["verifications"])}


def _reason(state: VerificationState) -> VerificationState:
    if not ollama_enabled():
        return {"llm_assessments": {}}
    raw_directory = Path(state["raw_directory"])
    assessments = assess_all_suppliers(state["commitments"], state["verifications"], raw_directory / "contracts")
    scorecard = state["scorecard"].copy()
    scorecard["llm_assessment"] = scorecard.supplier_id.map({key: value.summary for key, value in assessments.items()})
    scorecard["llm_recommended_status"] = scorecard.supplier_id.map({key: value.recommended_status for key, value in assessments.items()})
    return {"scorecard": scorecard, "llm_assessments": assessments}


def build_verification_graph():
    graph = StateGraph(VerificationState)
    graph.add_node("extract", RunnableLambda(_extract))
    graph.add_node("verify", RunnableLambda(_verify))
    graph.add_node("score", RunnableLambda(_score))
    graph.add_node("reason", RunnableLambda(_reason))
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "verify")
    graph.add_edge("verify", "score")
    graph.add_edge("score", "reason")
    graph.add_edge("reason", END)
    return graph.compile()
