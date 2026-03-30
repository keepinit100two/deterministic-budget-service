import pytest

from app.services.google_sheet_runner import run_budget_cycle_from_google_sheet


class MockGoogleSheetsClient:
    def __init__(self):
        self.calls = []
        self.data = {
            "Template": [
                ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
                ["rent", "Rent", "247.50", 1, True],
            ],
            "Income_Input": [
                ["period_id", "income_amount", "status", "notes"],
                ["2026-W12", "300.00", "pending", "weekly paycheck"],
            ],
            "Run_Control": [
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
            ],
            "Weekly_Output": [["" for _ in range(10)] for _ in range(20)],
            "Audit_Log": [
                ["run_id", "period_id", "income_amount", "total_allocated",
                 "weekly_leftover", "target_block_id", "status", "timestamp"]
            ],
        }

    def get_sheet(self, name):
        return self.data[name]

    def write_cell(self, sheet_name, cell_ref, value):
        self.calls.append((sheet_name, cell_ref, value))


def test_google_sheet_runner_executes_with_mock(monkeypatch):
    mock_client = MockGoogleSheetsClient()

    def fake_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(
        "app.services.google_sheet_runner.GoogleSheetsClient",
        fake_client,
    )

    result = run_budget_cycle_from_google_sheet(period_id="2026-W12")

    assert result["run_input"].period_id == "2026-W12"
    assert result["allocation_result"].decision_status == "success"

    assert len(mock_client.calls) > 0
    assert any(call[0] == "Weekly_Output" for call in mock_client.calls)
    assert any(call[0] == "Income_Input" for call in mock_client.calls)
    assert any(call[0] == "Audit_Log" for call in mock_client.calls)