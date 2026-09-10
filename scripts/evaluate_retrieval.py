from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from supplier_allocation.retrieval import index_documents, search_evidence


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    index_documents(ROOT / "data" / "raw")
    hits = 0
    for supplier_number in range(1, 36):
        supplier_id = f"SUP-{supplier_number:03}"
        results = search_evidence(f"{supplier_id} contractual capacity and lead time", limit=3)
        hits += int(any(result["supplier_id"] == supplier_id for result in results))
    print(f"Retrieval recall@3: {hits / 35:.1%} ({hits}/35)")


if __name__ == "__main__":
    main()
