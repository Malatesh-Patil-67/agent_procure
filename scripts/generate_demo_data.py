"""Create reproducible, fully synthetic supplier documents and operating data."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

SUPPLIERS = [
    ("SUP-001", "Alpha Components GmbH", "Germany", 14.20, 600_000, 21, 97.0, 1.0, 96.0, 24.2, 0.61),
    ("SUP-002", "Beta Precision Ltd", "Poland", 13.80, 400_000, 14, 96.0, 1.2, 91.7, 25.1, 0.95),
    ("SUP-003", "Gamma Manufacturing SA", "France", 14.05, 520_000, 18, 97.0, 0.9, 97.8, 18.6, 0.52),
    ("SUP-004", "Delta Industrial SpA", "Italy", 13.30, 440_000, 20, 95.0, 1.1, 95.2, 20.8, 1.08),
    ("SUP-005", "Epsilon Metals Co", "China", 12.95, 380_000, 28, 94.0, 1.5, 94.1, 29.3, 1.41),
    ("SUP-006", "Zeta Engineering AB", "Sweden", 15.10, 320_000, 16, 98.0, 0.8, 98.5, 15.9, 0.43),
]


def write_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    y_position = 800
    for line in text.splitlines():
        pdf.drawString(50, y_position, line)
        y_position -= 20
    pdf.save()


def write_documents() -> None:
    for supplier_id, name, country, price, capacity, lead_time, otd, defects, *_ in SUPPLIERS:
        contract = f"""XYZ INDUSTRIAL SYSTEMS — SUPPLY AGREEMENT\n\nSupplier: {name} ({supplier_id})\nCountry of manufacture: {country}\n\nCommercial terms\nQuoted unit price: EUR {price:.2f}\nCertified annual capacity: {capacity:,} units\nContractual lead time: {lead_time} calendar days\nMinimum on-time delivery: {otd:.1f}%\nMaximum defect rate: {defects:.1f}%\nMinimum annual volume: 40,000 units\nTermination notice: 90 days\n"""
        audit = f"""SUPPLIER AUDIT REPORT — {name}\n\nAudit scope: manufacturing quality system and capacity controls.\nConclusion: production controls are suitable for the declared {capacity:,} unit annual capacity.\nCapacity statement: output above the declared limit requires a documented capacity review.\n"""
        certificate = f"""ISO 9001 CERTIFICATE\n\nOrganisation: {name}\nCertificate status: VALID\nValid until: 2027-06-30\nScope: precision-component manufacture\n"""
        write_pdf(RAW / "contracts" / f"{supplier_id}_contract.pdf", contract)
        write_pdf(RAW / "audits" / f"{supplier_id}_audit.pdf", audit)
        write_pdf(RAW / "certificates" / f"{supplier_id}_iso9001.pdf", certificate)


def write_operating_data() -> None:
    random.seed(42)
    start = date(2025, 10, 1)
    with (RAW / "delivery_history.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["supplier_id", "po_id", "order_date", "promised_date", "received_date", "units"])
        writer.writeheader()
        for supplier_id, _, _, _, _, lead_time, _, _, observed_otd, observed_lead, _ in SUPPLIERS:
            for index in range(48):
                promised = start + timedelta(days=index * 7)
                late = random.random() > observed_otd / 100
                deviation = max(0, int(round(observed_lead - lead_time))) if late else 0
                received = promised + timedelta(days=deviation)
                order_date = received - timedelta(days=round(observed_lead))
                writer.writerow({"supplier_id": supplier_id, "po_id": f"PO-{supplier_id[-3:]}-{index:03}", "order_date": order_date, "promised_date": promised, "received_date": received, "units": random.randint(900, 2600)})
    with (RAW / "defect_history.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["supplier_id", "inspection_date", "units_inspected", "units_rejected"])
        writer.writeheader()
        for supplier_id, *_, defect_rate in SUPPLIERS:
            for index in range(12):
                inspected = random.randint(6000, 11000)
                writer.writerow({"supplier_id": supplier_id, "inspection_date": start + timedelta(days=index * 30), "units_inspected": inspected, "units_rejected": round(inspected * defect_rate / 100)})
    with (RAW / "demand_forecast.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["quarter", "component", "demand_units"])
        writer.writeheader()
        writer.writerow({"quarter": "2026-Q4", "component": "Precision Component A", "demand_units": 400000})


if __name__ == "__main__":
    write_documents()
    write_operating_data()
    print(f"Synthetic source archive created in {RAW}")
