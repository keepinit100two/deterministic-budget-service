from typing import Any

from app.services.google_sheets_client import GoogleSheetsClient
from app.services.run_budget_cycle import run_budget_cycle


def run_budget_cycle_from_google_sheet(
    *,
    period_id: str,
    credentials_file: str | None = None,
    spreadsheet_id: str | None = None,
    sheet_client: Any | None = None,
) -> dict:
    """
    Live execution path:
    - Reads real Google Sheet tabs
    - Uses Run_Control as the workbook contract source
    - Runs full budget cycle
    """

    client = sheet_client or GoogleSheetsClient(
        credentials_file=credentials_file,
        spreadsheet_id=spreadsheet_id,
    )

    control_values = client.get_sheet("Run_Control")
    control_map = _control_values_to_map(control_values)

    template_sheet_name = control_map.get("template_tab_name", "Template")
    income_sheet_name = control_map.get("income_tab_name", "Income_Input")
    output_sheet_name = control_map.get("output_tab_name", "Weekly_Output")
    audit_sheet_name = control_map.get("audit_log_tab_name", "Audit_Log")

    template_values = client.get_sheet(template_sheet_name)
    income_values = client.get_sheet(income_sheet_name)
    weekly_output_values = client.get_sheet(output_sheet_name)

    return run_budget_cycle(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
        weekly_output_values=weekly_output_values,
        period_id=period_id,
        output_sheet_name=output_sheet_name,
        income_sheet_name=income_sheet_name,
        audit_sheet_name=audit_sheet_name,
        sheet_client=client,
    )


def _control_values_to_map(control_values: list[list[Any]]) -> dict[str, str]:
    if not control_values:
        return {}

    rows = control_values[1:] if control_values[0][:2] == ["key", "value"] else control_values

    control_map: dict[str, str] = {}

    for row in rows:
        if len(row) < 2:
            continue

        key = str(row[0]).strip()
        value = str(row[1]).strip()

        if key:
            control_map[key] = value

    return control_map