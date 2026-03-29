import pytest

from app.services.sheets_adapter import (
    build_raw_sheet_bundle,
)


def test_build_raw_sheet_bundle_parses_template_income_and_control() -> None:
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

    result = build_raw_sheet_bundle(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
    )

    assert len(result.raw_template_rows) == 2
    assert result.raw_template_rows[0]["category_id"] == "rent"
    assert result.raw_template_rows[1]["display_name"] == "Wifi"

    assert len(result.raw_income_rows) == 1
    assert result.raw_income_rows[0]["period_id"] == "2026-W12"
    assert result.raw_income_rows[0]["income_amount"] == "1251.00"

    assert result.raw_control_rows["layout_version"] == "v1"
    assert result.raw_control_rows["blocks_per_band"] == 4
    assert result.raw_control_rows["start_col"] == 1


def test_build_raw_sheet_bundle_rejects_bad_template_headers() -> None:
    template_values = [
        ["category", "display_name", "target_amount", "allocation_order", "is_active"],
        ["rent", "Rent", "247.50", 1, True],
    ]

    income_values = [
        ["period_id", "income_amount", "status", "notes"],
        ["2026-W12", "1251.00", "pending", "weekly paycheck"],
    ]

    control_values = [
        ["key", "value"],
        ["layout_version", "v1"],
    ]

    with pytest.raises(ValueError, match="Template headers mismatch"):
        build_raw_sheet_bundle(
            template_values=template_values,
            income_values=income_values,
            control_values=control_values,
        )


def test_build_raw_sheet_bundle_rejects_duplicate_control_key() -> None:
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
        ["layout_version", "v2"],
    ]

    with pytest.raises(ValueError, match="duplicate key"):
        build_raw_sheet_bundle(
            template_values=template_values,
            income_values=income_values,
            control_values=control_values,
        )