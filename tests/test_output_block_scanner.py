from app.services.output_block_scanner import find_first_empty_output_block


def _empty_sheet(rows=50, cols=20):
    return [["" for _ in range(cols)] for _ in range(rows)]


def test_find_first_empty_block_returns_first_block():
    sheet = _empty_sheet()

    result = find_first_empty_output_block(
        sheet_values=sheet,
        start_row=0,
        start_col=0,
        block_height=16,
        block_width=2,
        block_spacing=1,
        blocks_per_band=4,
    )

    assert result.block_id == "band1_block1"
    assert result.start_row == 0
    assert result.label_col == 0


def test_find_second_block_when_first_is_filled():
    sheet = _empty_sheet()

    for r in range(16):
        sheet[r][0] = "data"
        sheet[r][1] = "data"

    result = find_first_empty_output_block(
        sheet_values=sheet,
        start_row=0,
        start_col=0,
        block_height=16,
        block_width=2,
        block_spacing=1,
        blocks_per_band=4,
    )

    assert result.block_id == "band1_block2"


def test_partially_used_block_is_treated_as_occupied_and_skipped():
    sheet = _empty_sheet()

    sheet[0][0] = "data"

    result = find_first_empty_output_block(
        sheet_values=sheet,
        start_row=0,
        start_col=0,
        block_height=16,
        block_width=2,
        block_spacing=1,
        blocks_per_band=4,
    )

    assert result.block_id == "band1_block2"