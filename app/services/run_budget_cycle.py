from datetime import datetime
import uuid
from typing import Any, List

from app.domain.schemas import ActionPlan, AllocationRunInput, WeeklyAllocationResult
from app.services.action_planner import build_weekly_output_action_plan
from app.services.decision_engine import compute_weekly_allocation
from app.services.run_input_builder import build_allocation_run_input_from_sheet_values
from app.services.sheets_executor import SheetsExecutor


def run_budget_cycle(
    *,
    template_values: List[List[Any]],
    income_values: List[List[Any]],
    control_values: List[List[Any]],
    weekly_output_values: List[List[Any]],
    period_id: str,
    output_sheet_name: str,
    income_sheet_name: str,
    audit_sheet_name: str,
    sheet_client: Any,
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Full internal budget workflow orchestrator.

    Flow:
    1. Normalize workbook values into AllocationRunInput
    2. Compute deterministic allocation result
    3. Build deterministic sheet write plan
    4. Execute Weekly_Output write plan
    5. Mark Income_Input row as processed
    6. Append Audit_Log row

    Returns a structured result bundle for inspection and future persistence.
    """

    effective_run_id = run_id or f"run_{uuid.uuid4().hex}"

    run_input: AllocationRunInput = build_allocation_run_input_from_sheet_values(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
        weekly_output_values=weekly_output_values,
        period_id=period_id,
    )

    allocation_result: WeeklyAllocationResult = compute_weekly_allocation(run_input)

    action_plan: ActionPlan = build_weekly_output_action_plan(
        run_id=effective_run_id,
        output_sheet_name=output_sheet_name,
        run_input=run_input,
        allocation_result=allocation_result,
    )

    executor = SheetsExecutor(sheet_client)

    # 1. Execute Weekly_Output writes
    executor.execute(action_plan)

    # 2. Update Income_Input status -> processed
    _mark_income_row_processed(
        executor,
        income_values,
        income_sheet_name,
        period_id,
    )

    # 3. Append Audit_Log row
    _append_audit_log_row(
        executor,
        audit_sheet_name,
        effective_run_id,
        allocation_result,
        run_input,
    )

    return {
        "run_id": effective_run_id,
        "run_input": run_input,
        "allocation_result": allocation_result,
        "action_plan": action_plan,
    }


def _mark_income_row_processed(
    executor: SheetsExecutor,
    income_values: List[List[Any]],
    income_sheet_name: str,
    period_id: str,
) -> None:
    if not income_values:
        raise ValueError("Income_Input sheet is empty")

    header = income_values[0]

    try:
        period_col = header.index("period_id")
        status_col = header.index("status")
    except ValueError as exc:
        raise ValueError("Income_Input headers must include period_id and status") from exc

    for i, row in enumerate(income_values[1:], start=2):  # sheet rows are 1-based
        if period_col < len(row) and str(row[period_col]).strip() == period_id:
            cell_ref = f"{_col_to_a1(status_col + 1)}{i}"
            executor.sheet_client.write_cell(
                income_sheet_name,
                cell_ref,
                "processed",
            )
            return

    raise ValueError(f"Could not find income row for period_id={period_id}")


def _append_audit_log_row(
    executor: SheetsExecutor,
    audit_sheet_name: str,
    run_id: str,
    allocation_result: WeeklyAllocationResult,
    run_input: AllocationRunInput,
) -> None:
    # Append at next empty row. If the sheet client returns existing sheet rows
    # including the header row, then len(sheet) + 1 is the next row number.
    sheet = executor.sheet_client.get_sheet(audit_sheet_name)
    next_row = len(sheet) + 1

    values = [
        run_id,
        run_input.period_id,
        str(run_input.income.income_amount),
        str(allocation_result.total_allocated_to_categories),
        str(allocation_result.weekly_leftover_amount),
        run_input.target_block.block_id,
        "success",
        datetime.utcnow().isoformat(),
    ]

    for col_index, value in enumerate(values, start=1):
        cell_ref = f"{_col_to_a1(col_index)}{next_row}"
        executor.sheet_client.write_cell(
            audit_sheet_name,
            cell_ref,
            value,
        )


def _col_to_a1(col_number: int) -> str:
    if col_number < 1:
        raise ValueError("Column number must be >= 1")

    result = ""
    n = col_number

    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result

    return result