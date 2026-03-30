from app.services.google_sheets_client import GoogleSheetsClient
from app.services.run_budget_cycle import run_budget_cycle


def run_budget_cycle_from_google_sheet(
    *,
    period_id: str,
    credentials_file: str | None = None,
    spreadsheet_id: str | None = None,
) -> dict:
    """
    Live execution path:
    - Reads real Google Sheet tabs
    - Runs full budget cycle
    """

    client = GoogleSheetsClient(
        credentials_file=credentials_file,
        spreadsheet_id=spreadsheet_id,
    )

    template_values = client.get_sheet("Template")
    income_values = client.get_sheet("Income_Input")
    control_values = client.get_sheet("Run_Control")
    weekly_output_values = client.get_sheet("Weekly_Output")

    return run_budget_cycle(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
        weekly_output_values=weekly_output_values,
        period_id=period_id,
        output_sheet_name="Weekly_Output",
        income_sheet_name="Income_Input",
        audit_sheet_name="Audit_Log",
        sheet_client=client,
    )