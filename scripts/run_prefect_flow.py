from __future__ import annotations

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("PREFECT_API_URL", "http://127.0.0.1:4200/api")

from supplier_allocation.workflows.prefect_flow import quarterly_supplier_allocation


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = quarterly_supplier_allocation(str(root / "data" / "raw"))
    narratives_path = root / "data" / "processed" / "llm_assessments.json"
    narratives_path.parent.mkdir(parents=True, exist_ok=True)
    narratives_path.write_text(json.dumps(result["llm_assessments"], indent=2))
    print(f"Persisted {result['supplier_count']} supplier assessments and indexed {result['indexed_documents']} documents.")
    if result["llm_assessments"]:
        print(f"Generated {len(result['llm_assessments'])} local Ollama assessment narratives at {narratives_path}.")
