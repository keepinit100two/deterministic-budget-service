from typing import Any

from app.domain.schemas import ActionPlan


class SheetsExecutor:
    """
    Applies an ActionPlan to a sheet-like interface.

    This is intentionally simple for v1:
    - sequential writes
    - no batching
    - no retries
    """

    def __init__(self, sheet_client: Any):
        """
        sheet_client must expose:

        write_cell(sheet_name: str, cell_ref: str, value: Any) -> None
        """
        self.sheet_client = sheet_client

    def execute(self, plan: ActionPlan) -> None:
        for action in plan.write_actions:
            if action.action_type != "write_cell":
                raise ValueError(f"Unsupported action type: {action.action_type}")

            self.sheet_client.write_cell(
                sheet_name=action.sheet_name,
                cell_ref=action.cell_ref,
                value=action.value,
            )