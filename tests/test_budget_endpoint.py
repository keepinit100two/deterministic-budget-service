from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _empty_sheet(rows=60, cols=20):
    return [["" for _ in range(cols)] for _ in range(rows)]


def test_budget_run_endpoint_executes_workflow() -> None:
    payload = {
        "period_id": "2026-W12",
        "template_values": [
            ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
            ["rent", "Rent", "247.50", 1, True],
            ["cell_phone", "Cell Phone", "55.00", 2, True],
            ["electric", "Electric", "50.00", 3, True],
        ],
        "income_values": [
            ["period_id", "income_amount", "status", "notes"],
            ["2026-W12", "300.00", "pending", "weekly paycheck"],
        ],
        "control_values": [
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
        "weekly_output_values": _empty_sheet(),
        "output_sheet_name": "Weekly_Output",
        "income_sheet_name": "Income_Input",
        "audit_sheet_name": "Audit_Log",
    }

    response = client.post("/budget/run", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert "run_id" in body
    assert body["period_id"] == "2026-W12"
    assert body["decision_status"] == "success"
    assert body["total_allocated_to_categories"] == "247.50"
    assert body["weekly_leftover_amount"] == "52.50"
    assert body["grand_total_written"] == "300.00"
    assert body["target_block_id"] == "band1_block1"