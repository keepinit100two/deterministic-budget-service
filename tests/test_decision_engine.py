from decimal import Decimal

from app.domain.schemas import (
    AllocationRunInput,
    OutputBlockRef,
    TemplateLine,
    WeeklyIncomeInput,
)
from app.services.decision_engine import compute_weekly_allocation


def _make_run_input(income_amount: str) -> AllocationRunInput:
    return AllocationRunInput(
        period_id="2026-W12",
        income=WeeklyIncomeInput(
            period_id="2026-W12",
            income_amount=Decimal(income_amount),
            status="pending",
            notes="weekly paycheck",
        ),
        template_lines=[
            TemplateLine(
                category_id="rent",
                display_name="Rent",
                target_amount=Decimal("247.50"),
                allocation_order=1,
                is_active=True,
            ),
            TemplateLine(
                category_id="cell_phone",
                display_name="Cell Phone",
                target_amount=Decimal("55.00"),
                allocation_order=2,
                is_active=True,
            ),
            TemplateLine(
                category_id="electric",
                display_name="Electric",
                target_amount=Decimal("50.00"),
                allocation_order=3,
                is_active=True,
            ),
        ],
        target_block=OutputBlockRef(
            block_id="band1_block1",
            band_index=1,
            block_index_within_band=1,
            start_row=1,
            end_row=16,
            label_col=1,
            amount_col=2,
        ),
    )


def test_compute_weekly_allocation_fully_funds_all_categories_when_income_is_sufficient() -> None:
    run_input = _make_run_input("500.00")

    result = compute_weekly_allocation(run_input)

    assert result.period_id == "2026-W12"
    assert result.starting_income == Decimal("500.00")
    assert result.total_allocated_to_categories == Decimal("352.50")
    assert result.weekly_leftover_amount == Decimal("147.50")
    assert result.grand_total_written == Decimal("500.00")
    assert result.decision_status == "success"

    assert len(result.lines) == 4
    assert result.lines[0].category_id == "rent"
    assert result.lines[0].allocated_amount == Decimal("247.50")
    assert result.lines[0].status == "fully_allocated"

    assert result.lines[1].category_id == "cell_phone"
    assert result.lines[1].allocated_amount == Decimal("55.00")
    assert result.lines[1].status == "fully_allocated"

    assert result.lines[2].category_id == "electric"
    assert result.lines[2].allocated_amount == Decimal("50.00")
    assert result.lines[2].status == "fully_allocated"

    assert result.lines[3].category_id == "weekly_leftover"
    assert result.lines[3].allocated_amount == Decimal("147.50")
    assert result.lines[3].status == "leftover_bucket"


def test_compute_weekly_allocation_stops_funding_after_first_unaffordable_category() -> None:
    run_input = _make_run_input("300.00")

    result = compute_weekly_allocation(run_input)

    assert result.total_allocated_to_categories == Decimal("247.50")
    assert result.weekly_leftover_amount == Decimal("52.50")
    assert result.grand_total_written == Decimal("300.00")

    assert result.lines[0].category_id == "rent"
    assert result.lines[0].allocated_amount == Decimal("247.50")
    assert result.lines[0].status == "fully_allocated"

    assert result.lines[1].category_id == "cell_phone"
    assert result.lines[1].allocated_amount == Decimal("0.00")
    assert result.lines[1].status == "not_funded"

    assert result.lines[2].category_id == "electric"
    assert result.lines[2].allocated_amount == Decimal("0.00")
    assert result.lines[2].status == "not_funded"

    assert result.lines[3].category_id == "weekly_leftover"
    assert result.lines[3].allocated_amount == Decimal("52.50")
    assert result.lines[3].status == "leftover_bucket"


def test_compute_weekly_allocation_handles_zero_income() -> None:
    run_input = _make_run_input("0.00")

    result = compute_weekly_allocation(run_input)

    assert result.total_allocated_to_categories == Decimal("0.00")
    assert result.weekly_leftover_amount == Decimal("0.00")
    assert result.grand_total_written == Decimal("0.00")

    assert result.lines[0].allocated_amount == Decimal("0.00")
    assert result.lines[0].status == "not_funded"
    assert result.lines[1].allocated_amount == Decimal("0.00")
    assert result.lines[1].status == "not_funded"
    assert result.lines[2].allocated_amount == Decimal("0.00")
    assert result.lines[2].status == "not_funded"
    assert result.lines[3].category_id == "weekly_leftover"
    assert result.lines[3].allocated_amount == Decimal("0.00")