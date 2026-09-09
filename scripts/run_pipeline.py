from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supplier_allocation.allocation import optimise_allocation
from supplier_allocation.extraction import extract_all
from supplier_allocation.models import AllocationConstraint
from supplier_allocation.scoring import build_scorecard
from supplier_allocation.staging import stage_operating_data
from supplier_allocation.verification import verify_all


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    stage_operating_data(RAW, PROCESSED / "procurement_staging.duckdb")
    commitments = extract_all(RAW / "contracts")
    verifications = verify_all(RAW, commitments)
    scorecard = build_scorecard(commitments, verifications)
    allocation = optimise_allocation(scorecard, AllocationConstraint())
    scorecard.to_csv(PROCESSED / "supplier_scorecard.csv", index=False)
    allocation.to_csv(PROCESSED / "proposed_allocation.csv", index=False)
    (PROCESSED / "verification_results.json").write_text(
        json.dumps([result.model_dump(mode="json") for result in verifications], indent=2)
    )
    print("Pipeline complete")
    print(scorecard[["supplier_name", "status", "supplier_score", "findings"]].to_string(index=False))
    print("\nProposed allocation")
    print(allocation[["supplier_name", "proposed_share_pct", "estimated_cost_eur", "allocation_reason"]].to_string(index=False))


if __name__ == "__main__":
    main()
