import os
from typing import Any, List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class GoogleSheetsClient:
    """
    Real Google Sheets client using a service account.

    Required environment variables:
    - GOOGLE_SHEETS_CREDENTIALS_FILE
    - GOOGLE_SHEETS_SPREADSHEET_ID
    """

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(
        self,
        credentials_file: str | None = None,
        spreadsheet_id: str | None = None,
    ) -> None:
        self.credentials_file = credentials_file or os.getenv(
            "GOOGLE_SHEETS_CREDENTIALS_FILE"
        )
        self.spreadsheet_id = spreadsheet_id or os.getenv(
            "GOOGLE_SHEETS_SPREADSHEET_ID"
        )

        if not self.credentials_file:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS_FILE is not configured")

        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is not configured")

        creds = Credentials.from_service_account_file(
            self.credentials_file,
            scopes=self.SCOPES,
        )

        self.service = build("sheets", "v4", credentials=creds)
        self.spreadsheets = self.service.spreadsheets()

    def read_range(self, sheet_name: str, range_a1: str) -> List[List[Any]]:
        full_range = f"{sheet_name}!{range_a1}"
        result = (
            self.spreadsheets.values()
            .get(spreadsheetId=self.spreadsheet_id, range=full_range)
            .execute()
        )
        return result.get("values", [])

    def get_sheet(self, sheet_name: str) -> List[List[Any]]:
        result = (
            self.spreadsheets.values()
            .get(spreadsheetId=self.spreadsheet_id, range=sheet_name)
            .execute()
        )
        return result.get("values", [])

    def write_cell(self, sheet_name: str, cell_ref: str, value: Any) -> None:
        full_range = f"{sheet_name}!{cell_ref}"
        body = {"values": [[value]]}

        (
            self.spreadsheets.values()
            .update(
                spreadsheetId=self.spreadsheet_id,
                range=full_range,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )