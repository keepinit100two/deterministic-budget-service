import json
import os
from typing import Any, List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class GoogleSheetsClient:
    """
    Real Google Sheets client.

    Preferred Cloud Run configuration:
    - GOOGLE_SHEETS_CREDENTIALS_JSON
    - GOOGLE_SHEETS_SPREADSHEET_ID

    Local fallback configuration:
    - GOOGLE_SHEETS_CREDENTIALS_FILE
    - GOOGLE_SHEETS_SPREADSHEET_ID
    """

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(
        self,
        credentials_file: str | None = None,
        spreadsheet_id: str | None = None,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")

        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is not configured")

        credentials_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")

        if credentials_json:
            creds_dict = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=self.SCOPES,
            )
        else:
            resolved_credentials_file = credentials_file or os.getenv(
                "GOOGLE_SHEETS_CREDENTIALS_FILE"
            )

            if not resolved_credentials_file:
                raise ValueError(
                    "GOOGLE_SHEETS_CREDENTIALS_JSON or GOOGLE_SHEETS_CREDENTIALS_FILE is required"
                )

            creds = Credentials.from_service_account_file(
                resolved_credentials_file,
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