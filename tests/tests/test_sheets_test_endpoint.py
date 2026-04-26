from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_sheets_test_endpoint_returns_mocked_sheet_data(monkeypatch) -> None:
    class MockGoogleSheetsClient:
        def get_sheet(self, sheet_name):
            assert sheet_name == "Template"
            return [
                ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
                ["rent", "Rent", "247.50", 1, True],
                ["cell_phone", "Cell Phone", "55.00", 2, True],
            ]

    monkeypatch.setattr("app.main.GoogleSheetsClient", MockGoogleSheetsClient)

    response = client.get("/sheets/test")

    assert response.status_code == 200
    assert response.json() == {
        "status": "connected",
        "rows_returned": 3,
        "sample": [
            ["category_id", "display_name", "target_amount", "allocation_order", "is_active"],
            ["rent", "Rent", "247.50", 1, True],
            ["cell_phone", "Cell Phone", "55.00", 2, True],
        ],
    }