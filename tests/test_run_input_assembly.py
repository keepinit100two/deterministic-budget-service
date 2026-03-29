from decimal import Decimal

import pytest

from app.domain.schemas import RawSheetBundle
from app.services.normalizer import (
    assemble_allocation_run_input_from_bundle,
    select_income_row_for_period,
)


def _make_raw_bundle() -> RawSheetBundle:
    return RawSheetBundle(
        raw_template_rows=[
            {
                "category_id": "rent",
                "display_name": "Rent",
                "target_amount": "247.50",
                "allocation_order": 1,
                "is_active": True,
            },
            {
                "category_id": "wifi",
                "display_name": "Wifi",
                "target_amount": "18.75",
                "allocation_order": 2,
                "is_active": True,
            },
        ],
        raw_income_rows=[
            {
                "period_id": "2026-W12",
                "income_amount": "1251.00",
                "status": "pending",
                "notes": "weekly paycheck",
            },
            {
                "period_id": "2026-W11",
                "income_amount": "1180.00",
                "status": "processed",
                "notes": "already completed",
            },
        ],
        raw_control_rows={
            "layout_version": "v1",
            "template_tab_name": "Template",
            "income_tab_name": "Income_Input",
            "output_tab_name": "Weekly_Output",
            "audit_log_tab_name": "Audit_Log",
            "blocks_per_band": 4,
            "block_height": 16,
            "block_width": 2,
            "block_spacing": 1,
            "start_row": 1,
            "start_col": 1,
        },
    )


def test_select_income_row_for_period_returns_single_pending_match() -> None:
    raw_bundle = _make_raw_bundle()

    result = select_income_row_for_period(raw_bundle.raw_income_rows, "2026-W12")

    assert result["period_id"] == "2026-W12"
    assert result["status"] == "pending"
    assert result["income_amount"] == "1251.00"


def test_select_income_row_for_period_rejects_missing_pending_match() -> None:
    raw_bundle = _make_raw_bundle()

    with pytest.raises(ValueError, match="No pending income row found"):
        select_income_row_for_period(raw_bundle.raw_income_rows, "2026-W99")


def test_select_income_row_for_period_rejects_multiple_pending_matches() -> None:
    raw_bundle = RawSheetBundle(
        raw_template_rows=[],
        raw_income_rows=[
            {
                "period_id": "2026-W12",
                "income_amount": "1251.00",
                "status": "pending",
                "notes": "",
            },
            {
                "period_id": "2026-W12",
                "income_amount": "1300.00",
                "status": "pending",
                "notes": "",
            },
        ],
        raw_control_rows={},
    )

    with pytest.raises(ValueError, match="Multiple pending income rows found"):
        select_income_row_for_period(raw_bundle.raw_income_rows, "2026-W12")


def test_assemble_allocation_run_input_from_bundle_builds_canonical_object() -> None:
    raw_bundle = _make_raw_bundle()

    result = assemble_allocation_run_input_from_bundle(
        raw_bundle=raw_bundle,
        period_id="2026-W12",
        block_id="band1_block3",
        band_index=1,
        block_index_within_band=3,
        start_row=17,
        end_row=32,
        label_col=8,
        amount_col=9,
    )

    assert result.period_id == "2026-W12"
    assert result.income.period_id == "2026-W12"
    assert result.income.income_amount == Decimal("1251.00")

    assert len(result.template_lines) == 2
    assert result.template_lines[0].category_id == "rent"
    assert result.template_lines[1].category_id == "wifi"

    assert result.target_block.block_id == "band1_block3"
    assert result.target_block.band_index == 1
    assert result.target_block.block_index_within_band == 3
    assert result.target_block.start_row == 17
    assert result.target_block.end_row == 32
    assert result.target_block.label_col == 8
    assert result.target_block.amount_col == 9