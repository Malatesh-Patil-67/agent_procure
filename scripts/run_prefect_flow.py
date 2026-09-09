from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supplier_allocation.workflows.prefect_flow import quarterly_supplier_allocation


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = quarterly_supplier_allocation(str(root / "data" / "raw"))
    print(f"Persisted {result['supplier_count']} supplier assessments and indexed {result['indexed_documents']} documents.")
