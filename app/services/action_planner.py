import uuid
from decimal import Decimal
from typing import List

from app.domain.schemas import (
    ActionPlan,
    AllocationRunInput,
    SheetWriteAction,
    WeeklyAllocationResult,
)


def _col_to_a1(col_number: int) -> str:
    """
    Convert 1-based column number to Excel/Sheets column letters.
    Example: 1 -> A, 2 -> B, 27 -> AA
    """
    if col_number < 1:
        raise ValueError("Column number must be >= 1")

    result = ""
    n = col_number

    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result

    return result


def _cell_ref(row: int, col: int) -> str:
    if row < 1 or col < 1:
        raise ValueError("Row and column numbers must be >= 1")
    return f"{_col_to_a1(col)}{row}"


def build_weekly_output_action_plan(
    *,
    run_id: str,
    output_sheet_name: str,
    run_input: AllocationRunInput,
    allocation_result: WeeklyAllocationResult,
) -> ActionPlan:
    """
    Convert decision output into deterministic Weekly_Output sheet write actions.
    """
    write_actions: List[SheetWriteAction] = []

    current_row = run_input.target_block.start_row
    label_col = run_input.target_block.label_col
    amount_col = run_input.target_block.amount_col

    for line in allocation_result.lines:
        write_actions.append(
            SheetWriteAction(
                action_id=str(uuid.uuid4()),
                sheet_name=output_sheet_name,
                cell_ref=_cell_ref(current_row, label_col),
                value=line.display_name,
                action_type="write_cell",
                reason=f"Write label for {line.category_id}",
            )
        )

        write_actions.append(
            SheetWriteAction(
                action_id=str(uuid.uuid4()),
                sheet_name=output_sheet_name,
                cell_ref=_cell_ref(current_row, amount_col),
                value=line.allocated_amount,
                action_type="write_cell",
                reason=f"Write amount for {line.category_id}",
            )
        )

        current_row += 1

    write_actions.append(
        SheetWriteAction(
            action_id=str(uuid.uuid4()),
            sheet_name=output_sheet_name,
            cell_ref=_cell_ref(current_row, label_col),
            value="Total",
            action_type="write_cell",
            reason="Write total label",
        )
    )

    write_actions.append(
        SheetWriteAction(
            action_id=str(uuid.uuid4()),
            sheet_name=output_sheet_name,
            cell_ref=_cell_ref(current_row, amount_col),
            value=allocation_result.grand_total_written,
            action_type="write_cell",
            reason="Write grand total amount",
        )
    )

    return ActionPlan(
        run_id=run_id,
        period_id=run_input.period_id,
        target_block=run_input.target_block,
        write_actions=write_actions,
    )