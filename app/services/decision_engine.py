from decimal import Decimal
from typing import List

from app.domain.schemas import (
    AllocationRunInput,
    WeeklyAllocationLine,
    WeeklyAllocationResult,
)


def compute_weekly_allocation(
    run_input: AllocationRunInput,
) -> WeeklyAllocationResult:
    """
    Deterministic budget allocation engine.

    Policy:
    - Walk active template lines in allocation_order.
    - Fully fund a category only if the full target amount is available.
    - On the first unaffordable category, fund it with 0.00 and
      fund all remaining categories with 0.00.
    - Place all remaining money into weekly_leftover.
    """

    remaining_income = run_input.income.income_amount
    allocation_lines: List[WeeklyAllocationLine] = []

    funding_stopped = False

    for template_line in run_input.template_lines:
        if funding_stopped:
            allocated_amount = Decimal("0.00")
            status = "not_funded"
        elif remaining_income >= template_line.target_amount:
            allocated_amount = template_line.target_amount
            remaining_income -= allocated_amount
            status = "fully_allocated"
        else:
            allocated_amount = Decimal("0.00")
            status = "not_funded"
            funding_stopped = True

        allocation_lines.append(
            WeeklyAllocationLine(
                period_id=run_input.period_id,
                category_id=template_line.category_id,
                display_name=template_line.display_name,
                target_amount=template_line.target_amount,
                allocated_amount=allocated_amount,
                allocation_order=template_line.allocation_order,
                status=status,
            )
        )

    weekly_leftover_amount = remaining_income

    allocation_lines.append(
        WeeklyAllocationLine(
            period_id=run_input.period_id,
            category_id="weekly_leftover",
            display_name="weekly_leftover",
            target_amount=Decimal("0.00"),
            allocated_amount=weekly_leftover_amount,
            allocation_order=len(run_input.template_lines) + 1,
            status="leftover_bucket",
        )
    )

    total_allocated_to_categories = sum(
        line.allocated_amount
        for line in allocation_lines
        if line.category_id != "weekly_leftover"
    )

    grand_total_written = total_allocated_to_categories + weekly_leftover_amount

    if grand_total_written != run_input.income.income_amount:
        raise ValueError(
            "Allocation invariant violated: grand_total_written must equal starting income"
        )

    return WeeklyAllocationResult(
        period_id=run_input.period_id,
        starting_income=run_input.income.income_amount,
        lines=allocation_lines,
        total_allocated_to_categories=total_allocated_to_categories,
        weekly_leftover_amount=weekly_leftover_amount,
        grand_total_written=grand_total_written,
        decision_status="success",
    )