from typing import Any, Dict, List

from app.domain.schemas import RawSheetBundle


def _require_header_row(
    values: List[List[Any]],
    expected_headers: List[str],
    tab_name: str,
) -> List[str]:
    if not values:
        raise ValueError(f"{tab_name} tab is empty")

    header_row = [str(cell).strip() for cell in values[0]]

    if header_row != expected_headers:
        raise ValueError(
            f"{tab_name} headers mismatch. "
            f"Expected {expected_headers}, got {header_row}"
        )

    return header_row


def _rows_to_dicts(
    values: List[List[Any]],
    expected_headers: List[str],
    tab_name: str,
) -> List[Dict[str, Any]]:
    _require_header_row(values, expected_headers, tab_name)

    records: List[Dict[str, Any]] = []

    for row in values[1:]:
        # Skip completely blank rows
        if not any(str(cell).strip() for cell in row):
            continue

        padded_row = list(row) + [""] * (len(expected_headers) - len(row))
        trimmed_row = padded_row[: len(expected_headers)]

        record = {
            expected_headers[idx]: trimmed_row[idx]
            for idx in range(len(expected_headers))
        }
        records.append(record)

    return records


def _control_values_to_dict(
    values: List[List[Any]],
    tab_name: str = "Run_Control",
) -> Dict[str, Any]:
    expected_headers = ["key", "value"]
    _require_header_row(values, expected_headers, tab_name)

    control_map: Dict[str, Any] = {}

    for row in values[1:]:
        if not any(str(cell).strip() for cell in row):
            continue

        padded_row = list(row) + ["", ""]
        key = str(padded_row[0]).strip()
        value = padded_row[1]

        if not key:
            raise ValueError(f"{tab_name} contains a row with blank key")

        if key in control_map:
            raise ValueError(f"{tab_name} contains duplicate key: {key}")

        control_map[key] = value

    return control_map


def build_raw_sheet_bundle(
    *,
    template_values: List[List[Any]],
    income_values: List[List[Any]],
    control_values: List[List[Any]],
) -> RawSheetBundle:
    template_headers = [
        "category_id",
        "display_name",
        "target_amount",
        "allocation_order",
        "is_active",
    ]
    income_headers = [
        "period_id",
        "income_amount",
        "status",
        "notes",
    ]

    raw_template_rows = _rows_to_dicts(
        template_values,
        template_headers,
        "Template",
    )
    raw_income_rows = _rows_to_dicts(
        income_values,
        income_headers,
        "Income_Input",
    )
    raw_control_rows = _control_values_to_dict(
        control_values,
        "Run_Control",
    )

    return RawSheetBundle(
        raw_template_rows=raw_template_rows,
        raw_income_rows=raw_income_rows,
        raw_control_rows=raw_control_rows,
    )