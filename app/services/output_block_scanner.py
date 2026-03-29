from typing import Any, List

from app.domain.schemas import OutputBlockRef


def _is_cell_empty(value: Any) -> bool:
    return str(value).strip() == ""


def _is_block_empty(
    sheet_values: List[List[Any]],
    start_row: int,
    start_col: int,
    block_height: int,
    block_width: int,
) -> bool:
    for r in range(start_row, start_row + block_height):
        for c in range(start_col, start_col + block_width):
            if r < len(sheet_values) and c < len(sheet_values[r]):
                if not _is_cell_empty(sheet_values[r][c]):
                    return False
    return True


def _is_block_partially_filled(
    sheet_values: List[List[Any]],
    start_row: int,
    start_col: int,
    block_height: int,
    block_width: int,
) -> bool:
    has_data = False
    has_empty = False

    for r in range(start_row, start_row + block_height):
        for c in range(start_col, start_col + block_width):
            if r < len(sheet_values) and c < len(sheet_values[r]):
                if _is_cell_empty(sheet_values[r][c]):
                    has_empty = True
                else:
                    has_data = True
            else:
                has_empty = True

    return has_data and has_empty


def find_first_empty_output_block(
    *,
    sheet_values: List[List[Any]],
    start_row: int,
    start_col: int,
    block_height: int,
    block_width: int,
    block_spacing: int,
    blocks_per_band: int,
) -> OutputBlockRef:
    """
    Scan the Weekly_Output sheet and return the first valid empty block.
    """

    band_index = 1
    current_row = start_row

    while True:
        for block_idx in range(blocks_per_band):
            current_col = start_col + block_idx * (block_width + block_spacing)

            if _is_block_partially_filled(
                sheet_values,
                current_row,
                current_col,
                block_height,
                block_width,
            ):
                raise ValueError(
                    f"Partial block detected at band={band_index}, block={block_idx + 1}"
                )

            if _is_block_empty(
                sheet_values,
                current_row,
                current_col,
                block_height,
                block_width,
            ):
                return OutputBlockRef(
                    block_id=f"band{band_index}_block{block_idx + 1}",
                    band_index=band_index,
                    block_index_within_band=block_idx + 1,
                    start_row=current_row,
                    end_row=current_row + block_height - 1,
                    label_col=current_col,
                    amount_col=current_col + 1,
                )

        # Move to next band
        band_index += 1
        current_row += block_height