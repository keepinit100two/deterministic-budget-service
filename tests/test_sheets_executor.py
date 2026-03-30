from app.services.sheets_executor import SheetsExecutor
from app.domain.schemas import ActionPlan, SheetWriteAction, OutputBlockRef


class MockSheetClient:
    def __init__(self):
        self.calls = []

    def write_cell(self, sheet_name, cell_ref, value):
        self.calls.append((sheet_name, cell_ref, value))


def test_execute_applies_all_actions_in_order():
    mock_client = MockSheetClient()
    executor = SheetsExecutor(mock_client)

    plan = ActionPlan(
        run_id="run_1",
        period_id="2026-W12",
        target_block=OutputBlockRef(
            block_id="band1_block1",
            band_index=1,
            block_index_within_band=1,
            start_row=1,
            end_row=16,
            label_col=1,
            amount_col=2,
        ),
        write_actions=[
            SheetWriteAction(
                action_id="1",
                sheet_name="Weekly_Output",
                cell_ref="A1",
                value="Rent",
                action_type="write_cell",
                reason="label",
            ),
            SheetWriteAction(
                action_id="2",
                sheet_name="Weekly_Output",
                cell_ref="B1",
                value=247.50,
                action_type="write_cell",
                reason="value",
            ),
        ],
    )

    executor.execute(plan)

    assert len(mock_client.calls) == 2
    assert mock_client.calls[0] == ("Weekly_Output", "A1", "Rent")
    assert mock_client.calls[1] == ("Weekly_Output", "B1", 247.50)