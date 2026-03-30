from decimal import Decimal

from app.domain.schemas import (
    AllocationRunInput,
    OutputBlockRef,
    TemplateLine,
    WeeklyIncomeInput,
)
from app.services.action_planner import build_weekly_output_action_plan
from app.services.decision_engine import compute_weekly_allocation


def _make_run_input() -> AllocationRunInput:
    return AllocationRunInput(
        period_id="2026-W12",
        income=WeeklyIncomeInput(
            period_id="2026-W12",
            income_amount=Decimal("300.00"),
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


def test_build_weekly_output_action_plan_creates_expected_writes() -> None:
    run_input = _make_run_input()
    allocation_result = compute_weekly_allocation(run_input)

    plan = build_weekly_output_action_plan(
        run_id="run_2026W12_001",
        output_sheet_name="Weekly_Output",
        run_input=run_input,
        allocation_result=allocation_result,
    )

    assert plan.run_id == "run_2026W12_001"
    assert plan.period_id == "2026-W12"
    assert plan.target_block.block_id == "band1_block1"

    # 4 allocation lines (3 categories + leftover) => 8 writes
    # plus Total label + Total amount => 2 writes
    assert len(plan.write_actions) == 10

    assert plan.write_actions[0].cell_ref == "A1"
    assert plan.write_actions[0].value == "Rent"

    assert plan.write_actions[1].cell_ref == "B1"
    assert plan.write_actions[1].value == Decimal("247.50")

    assert plan.write_actions[2].cell_ref == "A2"
    assert plan.write_actions[2].value == "Cell Phone"

    assert plan.write_actions[3].cell_ref == "B2"
    assert plan.write_actions[3].value == Decimal("0.00")

    assert plan.write_actions[6].cell_ref == "A4"
    assert plan.write_actions[6].value == "weekly_leftover"

    assert plan.write_actions[7].cell_ref == "B4"
    assert plan.write_actions[7].value == Decimal("52.50")

    assert plan.write_actions[8].cell_ref == "A5"
    assert plan.write_actions[8].value == "Total"

    assert plan.write_actions[9].cell_ref == "B5"
    assert plan.write_actions[9].value == Decimal("300.00")