from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supplier_allocation.extraction import extract_all
from supplier_allocation.verification import verify_all


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LABELS = ROOT / "data" / "evaluation" / "expected_assessments.csv"


def main() -> None:
    with LABELS.open() as handle:
        expected = {row["supplier_id"]: row["expected_status"] for row in csv.DictReader(handle)}
    commitments = extract_all(RAW / "contracts")
    observed = {item.supplier_id: item.status for item in verify_all(RAW, commitments)}
    correct = sum(observed[supplier_id] == status for supplier_id, status in expected.items())
    accuracy = correct / len(expected)
    print(f"Verification status accuracy: {accuracy:.1%} ({correct}/{len(expected)})")
    for supplier_id, status in expected.items():
        if observed[supplier_id] != status:
            print(f"Mismatch: {supplier_id} expected {status}, observed {observed[supplier_id]}")


if __name__ == "__main__":
    main()
