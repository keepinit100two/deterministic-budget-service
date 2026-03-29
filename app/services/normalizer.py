from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from app.domain.schemas import (
    AllocationRunInput,
    OutputBlockRef,
    RawSheetBundle,
    TemplateLine,
    WeeklyIncomeInput,
)


def normalize_template_rows(raw_rows: List[Dict[str, Any]]) -> List[TemplateLine]:
    """
    Convert raw template rows into canonical TemplateLine objects.

    Rules enforced here:
    - inactive rows are ignored
    - target_amount must parse as Decimal
    - rows are sorted by allocation_order ascending
    """
    normalized: List[TemplateLine] = []

    for row in raw_rows:
        is_active = bool(row.get("is_active", False))
        if not is_active:
            continue

        try:
            target_amount = Decimal(str(row["target_amount"]))
        except (KeyError, InvalidOperation) as exc:
            raise ValueError(f"Invalid target_amount in template row: {row}") from exc

        try:
            allocation_order = int(row["allocation_order"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid allocation_order in template row: {row}") from exc

        category_id = str(row.get("category_id", "")).strip()
        display_name = str(row.get("display_name", "")).strip()

        if not category_id:
            raise ValueError(f"Missing category_id in template row: {row}")
        if not display_name:
            raise ValueError(f"Missing display_name in template row: {row}")
        if target_amount < Decimal("0"):
            raise ValueError(f"Negative target_amount is not allowed: {row}")
        if category_id == "weekly_leftover":
            raise ValueError("weekly_leftover must not appear as a template category")

        normalized.append(
            TemplateLine(
                category_id=category_id,
                display_name=display_name,
                target_amount=target_amount,
                allocation_order=allocation_order,
                is_active=True,
            )
        )

    normalized.sort(key=lambda line: line.allocation_order)

    _validate_template_lines(normalized)

    return normalized


def _validate_template_lines(lines: List[TemplateLine]) -> None:
    if not lines:
        raise ValueError("No active template lines found")

    seen_category_ids = set()
    seen_orders = set()

    for line in lines:
        if line.category_id in seen_category_ids:
            raise ValueError(f"Duplicate category_id found: {line.category_id}")
        if line.allocation_order in seen_orders:
            raise ValueError(
                f"Duplicate allocation_order found: {line.allocation_order}"
            )

        seen_category_ids.add(line.category_id)
        seen_orders.add(line.allocation_order)


def normalize_income_row(raw_row: Dict[str, Any]) -> WeeklyIncomeInput:
    """
    Convert one raw income row into canonical WeeklyIncomeInput.
    """
    period_id = str(raw_row.get("period_id", "")).strip()
    status = str(raw_row.get("status", "")).strip()
    notes = raw_row.get("notes")

    if not period_id:
        raise ValueError(f"Missing period_id in income row: {raw_row}")
    if not status:
        raise ValueError(f"Missing status in income row: {raw_row}")

    try:
        income_amount = Decimal(str(raw_row["income_amount"]))
    except (KeyError, InvalidOperation) as exc:
        raise ValueError(f"Invalid income_amount in income row: {raw_row}") from exc

    if income_amount < Decimal("0"):
        raise ValueError(f"Negative income_amount is not allowed: {raw_row}")

    return WeeklyIncomeInput(
        period_id=period_id,
        income_amount=income_amount,
        status=status,
        notes=notes,
    )


def build_output_block_ref(
    *,
    block_id: str,
    band_index: int,
    block_index_within_band: int,
    start_row: int,
    end_row: int,
    label_col: int,
    amount_col: int,
) -> OutputBlockRef:
    """
    Build a canonical OutputBlockRef from already-determined layout coordinates.
    """
    if not block_id.strip():
        raise ValueError("block_id is required")
    if band_index < 1:
        raise ValueError("band_index must be >= 1")
    if block_index_within_band < 1:
        raise ValueError("block_index_within_band must be >= 1")
    if end_row < start_row:
        raise ValueError("end_row must be >= start_row")
    if label_col < 1 or amount_col < 1:
        raise ValueError("label_col and amount_col must be >= 1")

    return OutputBlockRef(
        block_id=block_id,
        band_index=band_index,
        block_index_within_band=block_index_within_band,
        start_row=start_row,
        end_row=end_row,
        label_col=label_col,
        amount_col=amount_col,
    )


def build_allocation_run_input(
    *,
    income: WeeklyIncomeInput,
    template_lines: List[TemplateLine],
    target_block: OutputBlockRef,
) -> AllocationRunInput:
    """
    Assemble the final canonical input object for the decision stage.
    """
    if not template_lines:
        raise ValueError("template_lines must not be empty")

    return AllocationRunInput(
        period_id=income.period_id,
        income=income,
        template_lines=template_lines,
        target_block=target_block,
    )


def select_income_row_for_period(
    raw_income_rows: List[Dict[str, Any]],
    period_id: str,
) -> Dict[str, Any]:
    """
    Select exactly one pending income row for the requested period.
    """
    matches = [
        row
        for row in raw_income_rows
        if str(row.get("period_id", "")).strip() == period_id
        and str(row.get("status", "")).strip() == "pending"
    ]

    if not matches:
        raise ValueError(f"No pending income row found for period_id={period_id}")

    if len(matches) > 1:
        raise ValueError(f"Multiple pending income rows found for period_id={period_id}")

    return matches[0]


def assemble_allocation_run_input_from_bundle(
    *,
    raw_bundle: RawSheetBundle,
    period_id: str,
    block_id: str,
    band_index: int,
    block_index_within_band: int,
    start_row: int,
    end_row: int,
    label_col: int,
    amount_col: int,
) -> AllocationRunInput:
    """
    Assemble a canonical AllocationRunInput from a raw sheet bundle
    and explicit output block coordinates.
    """
    template_lines = normalize_template_rows(raw_bundle.raw_template_rows)

    selected_income_row = select_income_row_for_period(
        raw_bundle.raw_income_rows,
        period_id,
    )
    income = normalize_income_row(selected_income_row)

    target_block = build_output_block_ref(
        block_id=block_id,
        band_index=band_index,
        block_index_within_band=block_index_within_band,
        start_row=start_row,
        end_row=end_row,
        label_col=label_col,
        amount_col=amount_col,
    )

    return build_allocation_run_input(
        income=income,
        template_lines=template_lines,
        target_block=target_block,
    )