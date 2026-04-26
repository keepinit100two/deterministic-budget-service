import pytest

from app.services.google_sheets_client import GoogleSheetsClient


def test_google_sheets_client_requires_spreadsheet_id(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_FILE", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_SPREADSHEET_ID", raising=False)

    with pytest.raises(ValueError, match="GOOGLE_SHEETS_SPREADSHEET_ID"):
        GoogleSheetsClient()


def test_google_sheets_client_requires_credentials(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_FILE", raising=False)
    monkeypatch.setenv("GOOGLE_SHEETS_SPREADSHEET_ID", "fake-sheet-id")

    with pytest.raises(
        ValueError,
        match="GOOGLE_SHEETS_CREDENTIALS_JSON or GOOGLE_SHEETS_CREDENTIALS_FILE",
    ):
        GoogleSheetsClient()