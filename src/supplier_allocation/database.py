from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy import create_engine, text

from .models import SupplierCommitment, VerificationResult


def get_engine():
    url = os.getenv("DATABASE_URL", "postgresql+psycopg://procurement:procurement@localhost:5433/procurement")
    return create_engine(url)


def load_operating_data(engine, raw_directory) -> None:
    deliveries = pd.read_csv(raw_directory / "delivery_history.csv")
    defects = pd.read_csv(raw_directory / "defect_history.csv")
    with engine.begin() as connection:
        for _, row in deliveries.iterrows():
            connection.execute(text("""
                INSERT INTO delivery_events (po_id, supplier_id, order_date, promised_date, received_date, units)
                VALUES (:po_id, :supplier_id, :order_date, :promised_date, :received_date, :units)
                ON CONFLICT (po_id) DO UPDATE SET received_date = EXCLUDED.received_date, units = EXCLUDED.units
            """), row.to_dict())
        for _, row in defects.iterrows():
            connection.execute(text("""
                INSERT INTO quality_inspections (supplier_id, inspection_date, units_inspected, units_rejected)
                VALUES (:supplier_id, :inspection_date, :units_inspected, :units_rejected)
                ON CONFLICT (supplier_id, inspection_date) DO UPDATE SET units_inspected = EXCLUDED.units_inspected, units_rejected = EXCLUDED.units_rejected
            """), row.to_dict())


def persist_assessments(engine, commitments: list[SupplierCommitment], results: list[VerificationResult], scorecard: pd.DataFrame) -> None:
    commitment_by_id = {item.supplier_id: item for item in commitments}
    result_by_id = {item.supplier_id: item for item in results}
    with engine.begin() as connection:
        for supplier_id, commitment in commitment_by_id.items():
            connection.execute(text("""
                INSERT INTO suppliers (supplier_id, supplier_name, country)
                VALUES (:supplier_id, :supplier_name, :country)
                ON CONFLICT (supplier_id) DO UPDATE SET supplier_name = EXCLUDED.supplier_name, country = EXCLUDED.country
            """), {"supplier_id": supplier_id, "supplier_name": commitment.supplier_name, "country": commitment.country})
            result = result_by_id[supplier_id]
            score = float(scorecard.loc[scorecard.supplier_id == supplier_id, "supplier_score"].iloc[0])
            connection.execute(
                text("DELETE FROM supplier_assessments WHERE supplier_id = :supplier_id"),
                {"supplier_id": supplier_id},
            )
            connection.execute(text("""
                INSERT INTO supplier_assessments (assessment_id, supplier_id, status, score, findings)
                VALUES (:assessment_id, :supplier_id, :status, :score, CAST(:findings AS jsonb))
            """), {"assessment_id": str(uuid4()), "supplier_id": supplier_id, "status": result.status, "score": score, "findings": json.dumps(result.findings)})


def persist_extracted_facts(engine, commitments: list[SupplierCommitment], raw_directory: Path) -> None:
    fact_fields = {
        "quoted_price_eur": "quoted_price_eur",
        "annual_capacity_units": "annual_capacity_units",
        "contractual_lead_time_days": "contractual_lead_time_days",
        "minimum_on_time_delivery_pct": "minimum_on_time_delivery_pct",
        "maximum_defect_rate_pct": "maximum_defect_rate_pct",
    }
    with engine.begin() as connection:
        for commitment in commitments:
            contract_name = f"{commitment.supplier_id}_contract.pdf"
            contract_path = raw_directory / "contracts" / contract_name
            content_hash = __import__("hashlib").sha256(contract_path.read_bytes()).hexdigest()
            document_id = connection.execute(text("""
                INSERT INTO documents (document_id, supplier_id, document_type, file_name, content_hash)
                VALUES (:document_id, :supplier_id, 'contract', :file_name, :content_hash)
                ON CONFLICT (file_name, content_hash) DO UPDATE SET supplier_id = EXCLUDED.supplier_id
                RETURNING document_id
            """), {"document_id": str(uuid4()), "supplier_id": commitment.supplier_id, "file_name": contract_name, "content_hash": content_hash}).scalar_one()
            connection.execute(
                text("DELETE FROM extracted_facts WHERE document_id = :document_id"),
                {"document_id": document_id},
            )
            for field_name, attribute in fact_fields.items():
                evidence = next(item for item in commitment.evidence if field_name.replace("_", " ").split()[0].lower() in item.passage.lower() or field_name.split("_")[0] in item.passage.lower())
                connection.execute(text("""
                    INSERT INTO extracted_facts (fact_id, supplier_id, document_id, fact_name, fact_value, page_number, source_passage)
                    VALUES (:fact_id, :supplier_id, :document_id, :fact_name, CAST(:fact_value AS jsonb), :page_number, :source_passage)
                """), {"fact_id": str(uuid4()), "supplier_id": commitment.supplier_id, "document_id": document_id, "fact_name": field_name, "fact_value": json.dumps(getattr(commitment, attribute)), "page_number": evidence.page, "source_passage": evidence.passage})


def persist_agent_traces(engine, assessments: dict) -> None:
    """Persist each local-agent assessment and its bounded evidence-tool trace."""
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_tool_traces (
                trace_id UUID PRIMARY KEY,
                supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
                tool_trace JSONB NOT NULL,
                evidence_documents JSONB NOT NULL,
                narrative JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        for supplier_id, assessment in assessments.items():
            connection.execute(text("DELETE FROM agent_tool_traces WHERE supplier_id = :supplier_id"), {"supplier_id": supplier_id})
            connection.execute(text("""
                INSERT INTO agent_tool_traces (trace_id, supplier_id, tool_trace, evidence_documents, narrative)
                VALUES (:trace_id, :supplier_id, CAST(:tool_trace AS jsonb), CAST(:evidence_documents AS jsonb), CAST(:narrative AS jsonb))
            """), {
                "trace_id": str(uuid4()),
                "supplier_id": supplier_id,
                "tool_trace": json.dumps(assessment.tool_trace),
                "evidence_documents": json.dumps(assessment.evidence_documents),
                "narrative": assessment.model_dump_json(),
            })


def persist_allocation_scenario(engine, name: str, constraints: dict, allocation: pd.DataFrame) -> str:
    scenario_id = str(uuid4())
    total_cost = float(allocation.estimated_cost_eur.sum())
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO allocation_scenarios (scenario_id, scenario_name, constraints, total_cost_eur)
            VALUES (:scenario_id, :name, CAST(:constraints AS jsonb), :total_cost)
        """), {"scenario_id": scenario_id, "name": name, "constraints": json.dumps(constraints), "total_cost": total_cost})
        for _, row in allocation.iterrows():
            connection.execute(text("""
                INSERT INTO allocation_lines (scenario_id, supplier_id, proposed_units, proposed_share_pct, estimated_cost_eur, rationale)
                VALUES (:scenario_id, :supplier_id, :proposed_units, :proposed_share_pct, :estimated_cost_eur, :rationale)
            """), {"scenario_id": scenario_id, "supplier_id": row.supplier_id, "proposed_units": int(row.proposed_units), "proposed_share_pct": float(row.proposed_share_pct), "estimated_cost_eur": float(row.estimated_cost_eur), "rationale": row.allocation_reason})
    return scenario_id


def record_approval(engine, scenario_id: str, reviewer_name: str, decision: str, comment: str) -> None:
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO approval_decisions (decision_id, scenario_id, reviewer_name, decision, comment)
            VALUES (:decision_id, :scenario_id, :reviewer_name, :decision, :comment)
        """), {"decision_id": str(uuid4()), "scenario_id": scenario_id, "reviewer_name": reviewer_name, "decision": decision, "comment": comment})
