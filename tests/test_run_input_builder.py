from decimal import Decimal

import pytest

from app.services.run_input_builder import build_allocation_run_input_from_sheet_values


def _empty_sheet(rows=60, cols=20):
    return [["" for _ in range(cols)] for _ in range(rows)]


def test_build_allocation_run_input_from_sheet_values_happy_path() -> None:
    template_values = [
        ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
        ["rent", "Rent", "247.50", 1, True],
        ["wifi", "Wifi", "18.75", 2, True],
    ]

    income_values = [
        ["period_id", "income_amount", "status", "notes"],
        ["2026-W12", "1251.00", "pending", "weekly paycheck"],
    ]

    control_values = [
        ["key", "value"],
        ["layout_version", "v1"],
        ["template_tab_name", "Template"],
        ["income_tab_name", "Income_Input"],
        ["output_tab_name", "Weekly_Output"],
        ["audit_log_tab_name", "Audit_Log"],
        ["blocks_per_band", 4],
        ["block_height", 16],
        ["block_width", 2],
        ["block_spacing", 1],
        ["start_row", 1],
        ["start_col", 1],
    ]

    weekly_output_values = _empty_sheet()

    result = build_allocation_run_input_from_sheet_values(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
        weekly_output_values=weekly_output_values,
        period_id="2026-W12",
    )

    assert result.period_id == "2026-W12"
    assert result.income.income_amount == Decimal("1251.00")
    assert len(result.template_lines) == 2

    assert result.target_block.block_id == "band1_block1"
    assert result.target_block.start_row == 1
    assert result.target_block.end_row == 16
    assert result.target_block.label_col == 1
    assert result.target_block.amount_col == 2


def test_build_allocation_run_input_from_sheet_values_skips_filled_first_block() -> None:
    template_values = [
        ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
        ["rent", "Rent", "247.50", 1, True],
    ]

    income_values = [
        ["period_id", "income_amount", "status", "notes"],
        ["2026-W12", "1251.00", "pending", "weekly paycheck"],
    ]

    control_values = [
        ["key", "value"],
        ["layout_version", "v1"],
        ["template_tab_name", "Template"],
        ["income_tab_name", "Income_Input"],
        ["output_tab_name", "Weekly_Output"],
        ["audit_log_tab_name", "Audit_Log"],
        ["blocks_per_band", 4],
        ["block_height", 16],
        ["block_width", 2],
        ["block_spacing", 1],
        ["start_row", 1],
        ["start_col", 1],
    ]

    weekly_output_values = _empty_sheet()

    # Fill first block completely (0-based columns 0 and 1, rows 0..15)
    for r in range(16):
        weekly_output_values[r][0] = "filled"
        weekly_output_values[r][1] = "filled"

    result = build_allocation_run_input_from_sheet_values(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
        weekly_output_values=weekly_output_values,
        period_id="2026-W12",
    )

    assert result.target_block.block_id == "band1_block2"
    assert result.target_block.label_col == 4
    assert result.target_block.amount_col == 5


def test_build_allocation_run_input_from_sheet_values_rejects_partial_block() -> None:
    template_values = [
        ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
        ["rent", "Rent", "247.50", 1, True],
    ]

    income_values = [
        ["period_id", "income_amount", "status", "notes"],
        ["2026-W12", "1251.00", "pending", "weekly paycheck"],
    ]

    control_values = [
        ["key", "value"],
        ["layout_version", "v1"],
        ["template_tab_name", "Template"],
        ["income_tab_name", "Income_Input"],
        ["output_tab_name", "Weekly_Output"],
        ["audit_log_tab_name", "Audit_Log"],
        ["blocks_per_band", 4],
        ["block_height", 16],
        ["block_width", 2],
        ["block_spacing", 1],
        ["start_row", 1],
        ["start_col", 1],
    ]

    weekly_output_values = _empty_sheet()
    weekly_output_values[0][0] = "partial"

    with pytest.raises(ValueError, match="Partial block detected"):
        build_allocation_run_input_from_sheet_values(
            template_values=template_values,
            income_values=income_values,
            control_values=control_values,
            weekly_output_values=weekly_output_values,
            period_id="2026-W12",
        )