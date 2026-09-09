from __future__ import annotations

import pandas as pd

from .models import SupplierCommitment, VerificationResult


COUNTRY_RISK = {"China": 0.85, "Italy": 0.25, "Poland": 0.15, "Germany": 0.10, "France": 0.10, "Sweden": 0.05}


def build_scorecard(commitments: list[SupplierCommitment], verifications: list[VerificationResult]) -> pd.DataFrame:
    verification_by_id = {item.supplier_id: item for item in verifications}
    rows = []
    for commitment in commitments:
        verification = verification_by_id[commitment.supplier_id]
        delivery_gap = max(0, commitment.minimum_on_time_delivery_pct - verification.observed_on_time_delivery_pct) / 100
        quality_gap = max(0, verification.observed_defect_rate_pct - commitment.maximum_defect_rate_pct) / 100
        lead_gap = max(0, verification.delivery_drift_days) / max(1, commitment.contractual_lead_time_days)
        risk_score = min(1.0, 0.45 * delivery_gap + 0.25 * quality_gap + 0.20 * lead_gap + 0.10 * COUNTRY_RISK[commitment.country])
        score = round(100 * (1 - risk_score), 1)
        rows.append({
            "supplier_id": commitment.supplier_id,
            "supplier_name": commitment.supplier_name,
            "country": commitment.country,
            "quoted_price_eur": commitment.quoted_price_eur,
            "quarterly_capacity_units": commitment.annual_capacity_units // 4,
            "status": verification.status,
            "supplier_score": score,
            "risk_score": round(risk_score, 3),
            "observed_otd_pct": verification.observed_on_time_delivery_pct,
            "observed_lead_time_days": verification.observed_median_lead_time_days,
            "observed_defect_rate_pct": verification.observed_defect_rate_pct,
            "delivery_drift_days": verification.delivery_drift_days,
            "findings": " ".join(verification.findings),
        })
    return pd.DataFrame(rows).sort_values(["risk_score", "quoted_price_eur"])
