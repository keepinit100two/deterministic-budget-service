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
    Scan the Weekly_Output sheet and return the first fully empty block.

    Design decision:
    - A block with any data is considered occupied and skipped.
    - A fully empty block is safe to write.
    - We do not treat partially filled blocks as fatal here because real budget
      output blocks may use fewer rows than the configured block height.
    """

    band_index = 1
    current_row = start_row

    while True:
        for block_idx in range(blocks_per_band):
            current_col = start_col + block_idx * (block_width + block_spacing)

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

        band_index += 1
        current_row += block_height