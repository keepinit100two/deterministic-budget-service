from decimal import Decimal

from app.services.run_budget_cycle import run_budget_cycle


class MockSheetClient:
    def __init__(self):
        self.calls = []
        self.sheets = {
            "Audit_Log": [["run_id", "period_id", "income_amount", "total_allocated",
                           "weekly_leftover", "target_block_id", "status", "timestamp"]]
        }

    def write_cell(self, sheet_name, cell_ref, value):
        self.calls.append((sheet_name, cell_ref, value))

    def get_sheet(self, sheet_name):
        return self.sheets.get(sheet_name, [])


def _empty_sheet(rows=60, cols=20):
    return [["" for _ in range(cols)] for _ in range(rows)]


def test_run_budget_cycle_executes_end_to_end() -> None:
    template_values = [
        ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
        ["rent", "Rent", "247.50", 1, True],
        ["cell_phone", "Cell Phone", "55.00", 2, True],
        ["electric", "Electric", "50.00", 3, True],
    ]

    income_values = [
        ["period_id", "income_amount", "status", "notes"],
        ["2026-W12", "300.00", "pending", "weekly paycheck"],
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
    mock_client = MockSheetClient()

    result = run_budget_cycle(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
        weekly_output_values=weekly_output_values,
        period_id="2026-W12",
        output_sheet_name="Weekly_Output",
        income_sheet_name="Income_Input",
        audit_sheet_name="Audit_Log",
        sheet_client=mock_client,
        run_id="run_test_001",
    )

    assert result["run_id"] == "run_test_001"

    run_input = result["run_input"]
    allocation_result = result["allocation_result"]
    action_plan = result["action_plan"]

    assert run_input.period_id == "2026-W12"
    assert run_input.target_block.block_id == "band1_block1"

    assert allocation_result.total_allocated_to_categories == Decimal("247.50")
    assert allocation_result.weekly_leftover_amount == Decimal("52.50")
    assert allocation_result.grand_total_written == Decimal("300.00")

    assert action_plan.run_id == "run_test_001"
    assert action_plan.period_id == "2026-W12"

    # 3 categories + leftover = 4 lines => 8 writes
    # plus Total label + Total amount => 2 writes
    assert len(action_plan.write_actions) == 10

    # 10 Weekly_Output writes
    # 1 Income_Input status update
    # 8 Audit_Log writes
    assert len(mock_client.calls) == 19

    # Weekly_Output writes
    assert mock_client.calls[0] == ("Weekly_Output", "A1", "Rent")
    assert mock_client.calls[1] == ("Weekly_Output", "B1", Decimal("247.50"))
    assert mock_client.calls[2] == ("Weekly_Output", "A2", "Cell Phone")
    assert mock_client.calls[3] == ("Weekly_Output", "B2", Decimal("0.00"))
    assert mock_client.calls[6] == ("Weekly_Output", "A4", "weekly_leftover")
    assert mock_client.calls[7] == ("Weekly_Output", "B4", Decimal("52.50"))
    assert mock_client.calls[8] == ("Weekly_Output", "A5", "Total")
    assert mock_client.calls[9] == ("Weekly_Output", "B5", Decimal("300.00"))

    # Income_Input status update
    assert mock_client.calls[10] == ("Income_Input", "C2", "processed")

    # Audit_Log writes start after the status update
    assert mock_client.calls[11][0] == "Audit_Log"
    assert mock_client.calls[11][1] == "A2"
    assert mock_client.calls[11][2] == "run_test_001"

    assert mock_client.calls[12] == ("Audit_Log", "B2", "2026-W12")
    assert mock_client.calls[13] == ("Audit_Log", "C2", "300.00")
    assert mock_client.calls[14] == ("Audit_Log", "D2", "247.50")
    assert mock_client.calls[15] == ("Audit_Log", "E2", "52.50")
    assert mock_client.calls[16] == ("Audit_Log", "F2", "band1_block1")
    assert mock_client.calls[17] == ("Audit_Log", "G2", "success")
    assert mock_client.calls[18][0] == "Audit_Log"
    assert mock_client.calls[18][1] == "H2"
    assert isinstance(mock_client.calls[18][2], str)

    # Higher-level sanity checks
    assert any(call[0] == "Income_Input" and call[2] == "processed" for call in mock_client.calls)
    assert any(call[0] == "Audit_Log" for call in mock_client.calls)