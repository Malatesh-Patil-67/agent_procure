from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import EvidenceRef, SupplierCommitment, VerificationResult


def verify_supplier(
    commitment: SupplierCommitment, delivery_history: pd.DataFrame, defect_history: pd.DataFrame
) -> VerificationResult:
    deliveries = delivery_history.loc[delivery_history.supplier_id == commitment.supplier_id].copy()
    defects = defect_history.loc[defect_history.supplier_id == commitment.supplier_id].copy()
    deliveries["order_date"] = pd.to_datetime(deliveries["order_date"])
    deliveries["promised_date"] = pd.to_datetime(deliveries["promised_date"])
    deliveries["received_date"] = pd.to_datetime(deliveries["received_date"])
    deliveries["on_time"] = deliveries.received_date <= deliveries.promised_date
    deliveries["lead_days"] = (deliveries.received_date - deliveries.order_date).dt.days
    observed_otd = round(deliveries.on_time.mean() * 100, 1)
    observed_lead = round(deliveries.lead_days.median(), 1)
    observed_defects = round(defects.units_rejected.sum() / defects.units_inspected.sum() * 100, 2)
    annualised_capacity = int(round(deliveries.units.sum() * 52 / max(1, len(deliveries))))
    findings: list[str] = []
    if observed_otd < commitment.minimum_on_time_delivery_pct:
        findings.append(f"On-time delivery {observed_otd}% is below the contractual {commitment.minimum_on_time_delivery_pct}% threshold.")
    if observed_lead > commitment.contractual_lead_time_days:
        findings.append(f"Median lead time {observed_lead} days exceeds the contractual {commitment.contractual_lead_time_days} days.")
    if observed_defects > commitment.maximum_defect_rate_pct:
        findings.append(f"Defect rate {observed_defects}% exceeds the contractual {commitment.maximum_defect_rate_pct}% limit.")
    if commitment.certificate_valid_until < pd.Timestamp.today().date():
        findings.append("ISO 9001 certificate is expired.")
    status = "APPROVED" if not findings else "REVIEW"
    if commitment.certificate_valid_until < pd.Timestamp.today().date():
        status = "BLOCKED"
    evidence = [
        *commitment.evidence,
        EvidenceRef(document="delivery_history.csv", passage=f"{len(deliveries)} purchase-order receipts analysed for {commitment.supplier_id}."),
        EvidenceRef(document="defect_history.csv", passage=f"{len(defects)} monthly inspection records analysed for {commitment.supplier_id}."),
    ]
    return VerificationResult(
        supplier_id=commitment.supplier_id,
        observed_on_time_delivery_pct=observed_otd,
        observed_median_lead_time_days=observed_lead,
        observed_defect_rate_pct=observed_defects,
        observed_peak_annualised_capacity_units=annualised_capacity,
        delivery_drift_days=round(observed_lead - commitment.contractual_lead_time_days, 1),
        status=status,
        findings=findings or ["All evaluated commitments are currently met."],
        evidence=evidence,
    )


def verify_all(raw_directory: Path, commitments: list[SupplierCommitment]) -> list[VerificationResult]:
    deliveries = pd.read_csv(raw_directory / "delivery_history.csv")
    defects = pd.read_csv(raw_directory / "defect_history.csv")
    return [verify_supplier(commitment, deliveries, defects) for commitment in commitments]
