from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("PREFECT_API_URL", "http://127.0.0.1:4200/api")

from supplier_allocation.workflows.prefect_flow import quarterly_supplier_allocation


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = quarterly_supplier_allocation(str(root / "data" / "raw"))
    print(f"Persisted {result['supplier_count']} supplier assessments and indexed {result['indexed_documents']} documents.")
    if result["llm_assessments"]:
        print(f"Generated {len(result['llm_assessments'])} local Ollama assessment narratives.")
