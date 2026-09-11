from data.board_data import VALID_CELLS


Cell = tuple[int, int]


def absolute_cells(
        local_cells,
        anchor: Cell
) -> set[Cell]:
    """
    将 Piece 的局部坐标转换成棋盘绝对坐标。
    """
    anchor_row, anchor_col = anchor

    return {
        (
            anchor_row + row,
            anchor_col + col
        )
        for row, col in local_cells
    }


def can_place(
        local_cells,
        anchor: Cell,
        blocked_cells: set[Cell],
        occupied_cells: set[Cell],
) -> bool:
    """
    判断 Piece 是否可以放置。

    条件：
    1. 所有格子必须位于合法棋盘区域
    2. 不可以覆盖当天保留格
    3. 不可以与已有 Piece 重叠
    """

    cells = absolute_cells(
        local_cells,
        anchor
    )

    # 超出棋盘
    if not cells.issubset(VALID_CELLS):
        return False

    # 覆盖日期/月/星期
    if cells & blocked_cells:
        return False

    # 与其它 Piece 重叠
    if cells & occupied_cells:
        return False

    return True