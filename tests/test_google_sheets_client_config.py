import os

import pytest

from app.services.google_sheets_client import GoogleSheetsClient


def test_google_sheets_client_requires_credentials_file(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_FILE", raising=False)
    monkeypatch.delenv("GOOGLE_SHEETS_SPREADSHEET_ID", raising=False)

    with pytest.raises(ValueError, match="GOOGLE_SHEETS_CREDENTIALS_FILE"):
        GoogleSheetsClient()


def test_google_sheets_client_requires_spreadsheet_id(monkeypatch, tmp_path) -> None:
    fake_credentials = tmp_path / "fake-service-account.json"
    fake_credentials.write_text("{}")

    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_FILE", str(fake_credentials))
    monkeypatch.delenv("GOOGLE_SHEETS_SPREADSHEET_ID", raising=False)

    with pytest.raises(ValueError, match="GOOGLE_SHEETS_SPREADSHEET_ID"):
        GoogleSheetsClient()