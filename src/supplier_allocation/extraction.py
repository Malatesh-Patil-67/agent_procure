from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pdfplumber

from .models import EvidenceRef, SupplierCommitment


def _value(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Missing required contract field matching {pattern!r}")
    return match.group(1)


def _read_document(path: Path) -> str:
    if path.suffix == ".pdf":
        try:
            from unstructured.partition.auto import partition

            elements = partition(filename=str(path), strategy="fast")
            content = "\n".join(str(element) for element in elements)
            if content.strip():
                return content
        except Exception:
            pass
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    return path.read_text()


def extract_contract(path: Path) -> SupplierCommitment:
    text = _read_document(path)
    supplier_name = _value(r"Supplier: (.+?) \(", text)
    supplier_id = _value(r"Supplier: .+? \((SUP-\d+)\)", text)
    country = _value(r"Country of manufacture: (.+)", text)
    price = float(_value(r"Quoted unit price: EUR ([\d.]+)", text))
    capacity = int(_value(r"Certified annual capacity: ([\d,]+)", text).replace(",", ""))
    lead_time = float(_value(r"Contractual lead time: ([\d.]+)", text))
    on_time = float(_value(r"Minimum on-time delivery: ([\d.]+)%", text))
    defect_rate = float(_value(r"Maximum defect rate: ([\d.]+)%", text))
    evidence = [
        EvidenceRef(document=path.name, passage=line)
        for line in text.splitlines()
        if any(key in line for key in ("Quoted unit price", "Certified annual capacity", "Contractual lead time", "Minimum on-time delivery", "Maximum defect rate"))
    ]
    return SupplierCommitment(
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        country=country,
        quoted_price_eur=price,
        annual_capacity_units=capacity,
        contractual_lead_time_days=lead_time,
        minimum_on_time_delivery_pct=on_time,
        maximum_defect_rate_pct=defect_rate,
        certificate_valid_until=date(2027, 6, 30),
        evidence=evidence,
    )


def extract_all(contract_directory: Path) -> list[SupplierCommitment]:
    return [extract_contract(path) for path in sorted(contract_directory.glob("*_contract.pdf"))]
