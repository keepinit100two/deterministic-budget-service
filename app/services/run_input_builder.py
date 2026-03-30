from typing import Any, List

from app.domain.schemas import AllocationRunInput
from app.services.normalizer import assemble_allocation_run_input_from_bundle
from app.services.output_block_scanner import find_first_empty_output_block
from app.services.sheets_adapter import build_raw_sheet_bundle


def _require_int(control_value: Any, key_name: str) -> int:
    try:
        return int(control_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Run_Control value for {key_name} must be an integer") from exc


def build_allocation_run_input_from_sheet_values(
    *,
    template_values: List[List[Any]],
    income_values: List[List[Any]],
    control_values: List[List[Any]],
    weekly_output_values: List[List[Any]],
    period_id: str,
) -> AllocationRunInput:
    """
    Full Normalize-phase orchestrator:
    Sheet values -> RawSheetBundle -> normalized canonical AllocationRunInput
    """

    raw_bundle = build_raw_sheet_bundle(
        template_values=template_values,
        income_values=income_values,
        control_values=control_values,
    )

    control = raw_bundle.raw_control_rows

    start_row = _require_int(control.get("start_row"), "start_row")
    start_col = _require_int(control.get("start_col"), "start_col")
    block_height = _require_int(control.get("block_height"), "block_height")
    block_width = _require_int(control.get("block_width"), "block_width")
    block_spacing = _require_int(control.get("block_spacing"), "block_spacing")
    blocks_per_band = _require_int(control.get("blocks_per_band"), "blocks_per_band")

    # Convert sheet-style 1-based config into scanner-friendly 0-based indexes
    scanner_start_row = start_row - 1
    scanner_start_col = start_col - 1

    target_block = find_first_empty_output_block(
        sheet_values=weekly_output_values,
        start_row=scanner_start_row,
        start_col=scanner_start_col,
        block_height=block_height,
        block_width=block_width,
        block_spacing=block_spacing,
        blocks_per_band=blocks_per_band,
    )

    # Convert scanner output back to 1-based coordinates for canonical contract
    canonical_start_row = target_block.start_row + 1
    canonical_end_row = target_block.end_row + 1
    canonical_label_col = target_block.label_col + 1
    canonical_amount_col = target_block.amount_col + 1

    return assemble_allocation_run_input_from_bundle(
        raw_bundle=raw_bundle,
        period_id=period_id,
        block_id=target_block.block_id,
        band_index=target_block.band_index,
        block_index_within_band=target_block.block_index_within_band,
        start_row=canonical_start_row,
        end_row=canonical_end_row,
        label_col=canonical_label_col,
        amount_col=canonical_amount_col,
    )