from decimal import Decimal

from fastapi.testclient import TestClient

from app.domain.schemas import (
    AllocationRunInput,
    OutputBlockRef,
    WeeklyIncomeInput,
    WeeklyAllocationResult,
)
from app.main import app


client = TestClient(app)


def test_budget_run_live_endpoint_returns_budget_response(monkeypatch) -> None:
    def fake_run_budget_cycle_from_google_sheet(*, period_id: str):
        assert period_id == "2026-W12"

        return {
            "run_id": "run_live_test_001",
            "run_input": AllocationRunInput(
                period_id="2026-W12",
                income=WeeklyIncomeInput(
                    period_id="2026-W12",
                    income_amount=Decimal("300.00"),
                    status="pending",
                    notes="weekly paycheck",
                ),
                template_lines=[],
                target_block=OutputBlockRef(
                    block_id="band1_block1",
                    band_index=1,
                    block_index_within_band=1,
                    start_row=1,
                    end_row=16,
                    label_col=1,
                    amount_col=2,
                ),
            ),
            "allocation_result": WeeklyAllocationResult(
                period_id="2026-W12",
                starting_income=Decimal("300.00"),
                lines=[],
                total_allocated_to_categories=Decimal("247.50"),
                weekly_leftover_amount=Decimal("52.50"),
                grand_total_written=Decimal("300.00"),
                decision_status="success",
            ),
        }

    monkeypatch.setattr(
        "app.main.run_budget_cycle_from_google_sheet",
        fake_run_budget_cycle_from_google_sheet,
    )

    response = client.post(
        "/budget/run-live",
        json={"period_id": "2026-W12"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "run_live_test_001",
        "period_id": "2026-W12",
        "decision_status": "success",
        "total_allocated_to_categories": "247.50",
        "weekly_leftover_amount": "52.50",
        "grand_total_written": "300.00",
        "target_block_id": "band1_block1",
    }