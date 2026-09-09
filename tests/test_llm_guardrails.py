from supplier_allocation.llm_agents import AssessmentNarrative, guard_assessment
from supplier_allocation.models import EvidenceRef, VerificationResult


def test_guard_assessment_removes_unsupported_citations_and_preserves_review() -> None:
    verification = VerificationResult(
        supplier_id="SUP-001", observed_on_time_delivery_pct=90, observed_median_lead_time_days=25,
        observed_defect_rate_pct=1.0, observed_peak_annualised_capacity_units=100_000,
        delivery_drift_days=4, status="REVIEW", findings=["Delivery drift"],
        evidence=[EvidenceRef(document="contract.pdf", passage="Lead time")],
    )
    narrative = AssessmentNarrative(summary="", key_risks=[], recommended_status="APPROVED", evidence_documents=["invented.pdf"])
    guarded = guard_assessment(narrative, verification)
    assert guarded.recommended_status == "REVIEW"
    assert guarded.evidence_documents == ["contract.pdf"]
