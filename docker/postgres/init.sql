CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    supplier_id TEXT REFERENCES suppliers(supplier_id),
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (file_name, content_hash)
);

CREATE TABLE extracted_facts (
    fact_id UUID PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    document_id UUID NOT NULL REFERENCES documents(document_id),
    fact_name TEXT NOT NULL,
    fact_value JSONB NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    source_passage TEXT NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE delivery_events (
    po_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    order_date DATE NOT NULL,
    promised_date DATE NOT NULL,
    received_date DATE NOT NULL,
    units INTEGER NOT NULL CHECK (units > 0)
);

CREATE TABLE quality_inspections (
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    inspection_date DATE NOT NULL,
    units_inspected INTEGER NOT NULL CHECK (units_inspected > 0),
    units_rejected INTEGER NOT NULL CHECK (units_rejected >= 0),
    PRIMARY KEY (supplier_id, inspection_date)
);

CREATE TABLE supplier_assessments (
    assessment_id UUID PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    status TEXT NOT NULL CHECK (status IN ('APPROVED', 'REVIEW', 'BLOCKED')),
    score NUMERIC(5,2) NOT NULL,
    findings JSONB NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE allocation_scenarios (
    scenario_id UUID PRIMARY KEY,
    scenario_name TEXT NOT NULL,
    constraints JSONB NOT NULL,
    total_cost_eur NUMERIC(14,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE allocation_lines (
    scenario_id UUID NOT NULL REFERENCES allocation_scenarios(scenario_id),
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    proposed_units INTEGER NOT NULL CHECK (proposed_units >= 0),
    proposed_share_pct NUMERIC(5,2) NOT NULL,
    estimated_cost_eur NUMERIC(14,2) NOT NULL,
    rationale TEXT NOT NULL,
    PRIMARY KEY (scenario_id, supplier_id)
);

CREATE TABLE approval_decisions (
    decision_id UUID PRIMARY KEY,
    scenario_id UUID NOT NULL REFERENCES allocation_scenarios(scenario_id),
    reviewer_name TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED', 'CHANGES_REQUESTED')),
    comment TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
