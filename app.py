from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from supplier_allocation.allocation import optimise_allocation
from supplier_allocation.database import get_engine, persist_allocation_scenario, record_approval
from supplier_allocation.models import AllocationConstraint
from supplier_allocation.retrieval import search_evidence


ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"

st.set_page_config(page_title="Supplier Allocation Intelligence", layout="wide")
st.title("Supplier Allocation Intelligence")
st.caption("Synthetic Phase 1 prototype · human approval required before any purchasing decision")

if not (PROCESSED / "supplier_scorecard.csv").exists():
    st.error("Run `python scripts/generate_demo_data.py` and `python scripts/run_pipeline.py` first.")
    st.stop()

scorecard = pd.read_csv(PROCESSED / "supplier_scorecard.csv")
with st.sidebar:
    st.header("Sourcing constraints")
    demand = st.number_input("Quarterly demand (units)", min_value=100_000, max_value=600_000, value=400_000, step=10_000)
    max_share = st.slider("Maximum supplier share", 0.20, 0.50, 0.35, 0.01)
    max_china = st.slider("Maximum China exposure", 0.0, 0.50, 0.25, 0.01)

constraints = AllocationConstraint(
    quarterly_demand_units=int(demand), maximum_single_supplier_share=max_share, maximum_china_exposure=max_china
)
try:
    allocation = optimise_allocation(scorecard, constraints)
except ValueError as error:
    st.error(str(error))
    st.stop()

metrics = st.columns(4)
metrics[0].metric("Demand", f"{demand:,.0f} units")
metrics[1].metric("Proposed cost", f"€{allocation.estimated_cost_eur.sum():,.0f}")
metrics[2].metric("Suppliers used", int((allocation.proposed_units > 0).sum()))
metrics[3].metric("Review required", int((allocation.status == "REVIEW").sum()))

st.subheader("Proposed sourcing allocation")
st.dataframe(
    allocation[["supplier_name", "country", "proposed_units", "proposed_share_pct", "estimated_cost_eur", "status", "allocation_reason"]],
    hide_index=True,
    use_container_width=True,
)
st.bar_chart(allocation.set_index("supplier_name")["proposed_units"])

st.subheader("Supplier verification scorecard")
st.dataframe(
    scorecard[["supplier_name", "country", "status", "supplier_score", "observed_otd_pct", "observed_lead_time_days", "observed_defect_rate_pct", "delivery_drift_days", "findings"]],
    hide_index=True,
    use_container_width=True,
)

st.subheader("Evidence and human approval")
results = json.loads((PROCESSED / "verification_results.json").read_text())
selected_supplier = st.selectbox("Review supplier", scorecard.supplier_name)
selected_id = scorecard.loc[scorecard.supplier_name == selected_supplier, "supplier_id"].iloc[0]
result = next(item for item in results if item["supplier_id"] == selected_id)
st.write("**Findings:**", " ".join(result["findings"]))
st.dataframe(pd.DataFrame(result["evidence"]), hide_index=True, use_container_width=True)
if st.button("Search Qdrant evidence archive"):
    try:
        evidence = search_evidence(f"{selected_supplier} delivery quality capacity")
        st.dataframe(pd.DataFrame(evidence), hide_index=True, use_container_width=True)
    except Exception as error:
        st.warning(f"Evidence archive unavailable: {error}")
decision = st.radio("Procurement decision", ["Pending review", "Approve assessment", "Reject assessment"], horizontal=True)
comment = st.text_area("Committee comment")
if st.button("Record review decision"):
    try:
        scenario_id = persist_allocation_scenario(
            get_engine(),
            "Interactive sourcing scenario",
            constraints.model_dump(),
            allocation,
        )
        mapped_decision = {"Approve assessment": "APPROVED", "Reject assessment": "REJECTED", "Pending review": "CHANGES_REQUESTED"}[decision]
        record_approval(get_engine(), scenario_id, "Procurement committee", mapped_decision, comment)
        st.success(f"Decision recorded in audit trail for scenario {scenario_id}. No purchase order has been created.")
    except Exception as error:
        st.error(f"Unable to record the audit decision: {error}")
