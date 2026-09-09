from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .extraction import _read_document
from .models import SupplierCommitment, VerificationResult

load_dotenv()


class AssessmentNarrative(BaseModel):
    summary: str = Field(description="A concise procurement assessment grounded only in provided evidence.")
    key_risks: list[str] = Field(description="Material supplier risks, if any.")
    recommended_status: Literal["APPROVED", "REVIEW", "BLOCKED"] = Field(
        description="One of APPROVED, REVIEW, or BLOCKED."
    )
    evidence_documents: list[str] = Field(description="Names of documents or datasets that support the assessment.")


def ollama_enabled() -> bool:
    return os.getenv("OLLAMA_ENABLED", "false").lower() in {"1", "true", "yes"}


def build_local_model() -> ChatOllama:
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        temperature=0,
    )


def assess_supplier_with_llm(
    commitment: SupplierCommitment,
    verification: VerificationResult,
    contract_directory: Path,
) -> AssessmentNarrative:
    contract_text = _read_document(contract_directory / f"{commitment.supplier_id}_contract.pdf")
    prompt = f"""You are a procurement verification agent. Assess one supplier using only the evidence below.
Do not invent facts, thresholds, or evidence. The deterministic verification status is the control result;
recommend a stricter status only when the supplied evidence supports it.

Supplier: {commitment.supplier_name} ({commitment.supplier_id})
Country: {commitment.country}

Contract evidence:
{contract_text}

Observed verification:
- Status: {verification.status}
- On-time delivery: {verification.observed_on_time_delivery_pct}%
- Median lead time: {verification.observed_median_lead_time_days} days
- Defect rate: {verification.observed_defect_rate_pct}%
- Findings: {verification.findings}
- Available evidence documents: {[item.document for item in verification.evidence]}
"""
    structured_model = build_local_model().with_structured_output(AssessmentNarrative)
    return AssessmentNarrative.model_validate(structured_model.invoke(prompt))


def assess_all_suppliers(
    commitments: list[SupplierCommitment],
    verifications: list[VerificationResult],
    contract_directory: Path,
) -> dict[str, AssessmentNarrative]:
    verification_by_id = {item.supplier_id: item for item in verifications}
    return {
        commitment.supplier_id: assess_supplier_with_llm(commitment, verification_by_id[commitment.supplier_id], contract_directory)
        for commitment in commitments
    }
