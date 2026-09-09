from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    document: str
    page: int = 1
    passage: str


class SupplierCommitment(BaseModel):
    supplier_id: str
    supplier_name: str
    country: str
    quoted_price_eur: float
    annual_capacity_units: int
    contractual_lead_time_days: float
    minimum_on_time_delivery_pct: float
    maximum_defect_rate_pct: float
    certificate_valid_until: date
    evidence: list[EvidenceRef] = Field(default_factory=list)


class VerificationResult(BaseModel):
    supplier_id: str
    observed_on_time_delivery_pct: float
    observed_median_lead_time_days: float
    observed_defect_rate_pct: float
    observed_peak_annualised_capacity_units: int
    delivery_drift_days: float
    status: Literal["APPROVED", "REVIEW", "BLOCKED"]
    findings: list[str]
    evidence: list[EvidenceRef]


class AllocationConstraint(BaseModel):
    quarterly_demand_units: int = 400_000
    maximum_single_supplier_share: float = 0.35
    maximum_china_exposure: float = 0.25
    minimum_active_suppliers: int = 2
