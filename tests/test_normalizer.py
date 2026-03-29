from decimal import Decimal

import pytest

from app.services.normalizer import (
    build_allocation_run_input,
    build_output_block_ref,
    normalize_income_row,
    normalize_template_rows,
)


def test_normalize_template_rows_sorts_and_filters_inactive() -> None:
    raw_rows = [
        {
            "category_id": "wifi",
            "display_name": "Wifi",
            "target_amount": "18.75",
            "allocation_order": 3,
            "is_active": True,
        },
        {
            "category_id": "rent",
            "display_name": "Rent",
            "target_amount": "247.50",
            "allocation_order": 1,
            "is_active": True,
        },
        {
            "category_id": "old_category",
            "display_name": "Old Category",
            "target_amount": "10.00",
            "allocation_order": 2,
            "is_active": False,
        },
    ]

    result = normalize_template_rows(raw_rows)

    assert len(result) == 2
    assert result[0].category_id == "rent"
    assert result[1].category_id == "wifi"
    assert result[0].target_amount == Decimal("247.50")
    assert result[1].target_amount == Decimal("18.75")


def test_normalize_template_rows_rejects_duplicate_category_id() -> None:
    raw_rows = [
        {
            "category_id": "rent",
            "display_name": "Rent",
            "target_amount": "247.50",
            "allocation_order": 1,
            "is_active": True,
        },
        {
            "category_id": "rent",
            "display_name": "Rent Duplicate",
            "target_amount": "100.00",
            "allocation_order": 2,
            "is_active": True,
        },
    ]

    with pytest.raises(ValueError, match="Duplicate category_id"):
        normalize_template_rows(raw_rows)


def test_normalize_template_rows_rejects_weekly_leftover_in_template() -> None:
    raw_rows = [
        {
            "category_id": "weekly_leftover",
            "display_name": "weekly_leftover",
            "target_amount": "10.00",
            "allocation_order": 1,
            "is_active": True,
        }
    ]

    with pytest.raises(ValueError, match="weekly_leftover"):
        normalize_template_rows(raw_rows)


def test_normalize_income_row_parses_decimal() -> None:
    raw_row = {
        "period_id": "2026-W12",
        "income_amount": "1251.00",
        "status": "pending",
        "notes": "weekly paycheck",
    }

    result = normalize_income_row(raw_row)

    assert result.period_id == "2026-W12"
    assert result.income_amount == Decimal("1251.00")
    assert result.status == "pending"
    assert result.notes == "weekly paycheck"


def test_build_output_block_ref_creates_canonical_block() -> None:
    result = build_output_block_ref(
        block_id="band1_block3",
        band_index=1,
        block_index_within_band=3,
        start_row=17,
        end_row=32,
        label_col=8,
        amount_col=9,
    )

    assert result.block_id == "band1_block3"
    assert result.band_index == 1
    assert result.block_index_within_band == 3
    assert result.start_row == 17
    assert result.end_row == 32
    assert result.label_col == 8
    assert result.amount_col == 9


def test_build_allocation_run_input_assembles_canonical_input() -> None:
    income = normalize_income_row(
        {
            "period_id": "2026-W12",
            "income_amount": "1251.00",
            "status": "pending",
            "notes": "weekly paycheck",
        }
    )

    template_lines = normalize_template_rows(
        [
            {
                "category_id": "rent",
                "display_name": "Rent",
                "target_amount": "247.50",
                "allocation_order": 1,
                "is_active": True,
            }
        ]
    )

    target_block = build_output_block_ref(
        block_id="band1_block1",
        band_index=1,
        block_index_within_band=1,
        start_row=1,
        end_row=16,
        label_col=1,
        amount_col=2,
    )

    result = build_allocation_run_input(
        income=income,
        template_lines=template_lines,
        target_block=target_block,
    )

    assert result.period_id == "2026-W12"
    assert result.income.period_id == "2026-W12"
    assert len(result.template_lines) == 1
    assert result.target_block.block_id == "band1_block1"