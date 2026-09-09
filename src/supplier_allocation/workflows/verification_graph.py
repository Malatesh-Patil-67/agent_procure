from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph

from ..extraction import extract_all
from ..scoring import build_scorecard
from ..verification import verify_all


class VerificationState(TypedDict, total=False):
    raw_directory: str
    commitments: list
    verifications: list
    scorecard: object


def _extract(state: VerificationState) -> VerificationState:
    commitments = extract_all(Path(state["raw_directory"]) / "contracts")
    return {"commitments": commitments}


def _verify(state: VerificationState) -> VerificationState:
    raw_directory = Path(state["raw_directory"])
    return {"verifications": verify_all(raw_directory, state["commitments"])}


def _score(state: VerificationState) -> VerificationState:
    return {"scorecard": build_scorecard(state["commitments"], state["verifications"])}


def build_verification_graph():
    graph = StateGraph(VerificationState)
    graph.add_node("extract", RunnableLambda(_extract))
    graph.add_node("verify", RunnableLambda(_verify))
    graph.add_node("score", RunnableLambda(_score))
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "verify")
    graph.add_edge("verify", "score")
    graph.add_edge("score", END)
    return graph.compile()
