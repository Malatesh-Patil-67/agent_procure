from __future__ import annotations

import cvxpy as cp
import pandas as pd

from .models import AllocationConstraint


def optimise_allocation(scorecard: pd.DataFrame, constraints: AllocationConstraint) -> pd.DataFrame:
    eligible = scorecard.loc[scorecard.status != "BLOCKED"].copy().reset_index(drop=True)
    if eligible.empty:
        raise ValueError("No eligible suppliers are available for allocation.")
    allocations = cp.Variable(len(eligible), nonneg=True)
    demand = constraints.quarterly_demand_units
    capacity = eligible.quarterly_capacity_units.to_numpy()
    price = eligible.quoted_price_eur.to_numpy()
    risk = eligible.risk_score.to_numpy()
    china = (eligible.country == "China").astype(float).to_numpy()
    risk_penalty_eur = 4.0
    objective = cp.Minimize(cp.sum(cp.multiply(price + risk * risk_penalty_eur, allocations)))
    allocation_constraints = [
        cp.sum(allocations) == demand,
        allocations <= capacity,
        allocations <= demand * constraints.maximum_single_supplier_share,
        china @ allocations <= demand * constraints.maximum_china_exposure,
    ]
    problem = cp.Problem(objective, allocation_constraints)
    problem.solve(solver=cp.CLARABEL)
    if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
        raise ValueError(f"Allocation problem is infeasible: {problem.status}")
    eligible["proposed_units"] = allocations.value.round().astype(int)
    eligible["proposed_share_pct"] = (eligible.proposed_units / demand * 100).round(1)
    eligible["estimated_cost_eur"] = (eligible.proposed_units * eligible.quoted_price_eur).round(0).astype(int)
    eligible["allocation_reason"] = eligible.apply(_reason, axis=1)
    return eligible.sort_values("proposed_units", ascending=False)


def _reason(row: pd.Series) -> str:
    if row.proposed_units == 0:
        return "Not selected by the current cost-risk scenario."
    if row.status == "REVIEW":
        return "Cost-effective but requires procurement review of verification findings."
    if row.supplier_score >= 95:
        return "Strong verified performance and low risk."
    return "Balanced contribution to cost, capacity, and diversification."
