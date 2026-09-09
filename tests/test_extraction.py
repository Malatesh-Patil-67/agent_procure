from pathlib import Path

from supplier_allocation.extraction import extract_all


def test_extracts_all_synthetic_contracts() -> None:
    root = Path(__file__).resolve().parents[1]
    commitments = extract_all(root / "data" / "raw" / "contracts")
    assert len(commitments) == 35
    alpha = next(item for item in commitments if item.supplier_id == "SUP-001")
    assert alpha.quoted_price_eur == 14.20
    assert alpha.annual_capacity_units == 600_000
    assert alpha.evidence
