from dataclasses import dataclass


Cell = tuple[int, int]


@dataclass(frozen=True)
class PieceDefinition:
    id: str
    cells: frozenset[Cell]


def normalize_cells(cells) -> frozenset[Cell]:
    """
    将一组格子坐标平移到左上角。
    保证最小 row = 0，最小 col = 0。
    """
    cells = list(cells)

    if not cells:
        return frozenset()

    min_row = min(row for row, col in cells)
    min_col = min(col for row, col in cells)

    return frozenset(
        (row - min_row, col - min_col)
        for row, col in cells
    )


def rotate_cells_right(cells) -> frozenset[Cell]:
    """
    顺时针旋转90°。

    (row, col)
        ->
    (col, -row)

    旋转后再 normalize。
    """
    rotated = [
        (col, -row)
        for row, col in cells
    ]

    return normalize_cells(rotated)


def rotate_cells_left(cells) -> frozenset[Cell]:
    """
    逆时针旋转90°。
    """
    rotated = [
        (-col, row)
        for row, col in cells
    ]

    return normalize_cells(rotated)

def flip_cells_horizontal(cells) -> frozenset[Cell]:
    """
    左右镜像翻转 Piece。

    保持当前旋转状态，只沿竖直轴做镜像：

        (row, col)
            ->
        (row, -col)

    翻转后再 normalize，
    让最小 row / col 回到 0。
    """

    flipped = [
        (row, -col)
        for row, col in cells
    ]

    return normalize_cells(flipped)

def get_unique_rotations(cells) -> list[frozenset[Cell]]:
    """
    返回一块拼图片所有不重复的旋转状态。
    最多4种。
    """
    rotations = []

    current = normalize_cells(cells)

    for _ in range(4):
        if current not in rotations:
            rotations.append(current)

        current = rotate_cells_right(current)

    return rotations