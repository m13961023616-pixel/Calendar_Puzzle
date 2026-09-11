from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.piece import (
    rotate_cells_left,
    rotate_cells_right,
    flip_cells_horizontal,
)
from data.piece_data import PIECES
from ui.piece_widget import PieceWidget


class PieceLibrary(QWidget):

    selection_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected_piece_id = None

        self.current_cells = {
            piece.id: piece.cells
            for piece in PIECES
        }

        self.widgets = {}

        self.build_ui()

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0, 0, 0, 0
        )

        layout.setSpacing(10)

        title = QLabel(
            "选择一块拼图片"
        )

        title.setObjectName(
            "pieceHint"
        )

        layout.addWidget(title)

        grid = QGridLayout()

        grid.setSpacing(8)

        for index, piece in enumerate(
            PIECES
        ):

            widget = PieceWidget(
                piece.id,
                piece.cells,
            )

            widget.clicked.connect(
                self.select_piece
            )

            self.widgets[
                piece.id
            ] = widget

            row = index // 2
            col = index % 2

            grid.addWidget(
                widget,
                row,
                col,
            )

        layout.addLayout(grid)
        layout.addStretch()

    def select_piece(
            self,
            piece_id
    ):

        widget = self.widgets[
            piece_id
        ]

        if not widget.available:
            return

        self.selected_piece_id = (
            piece_id
        )

        for (
            pid,
            piece_widget
        ) in self.widgets.items():

            piece_widget.set_selected(
                pid == piece_id
            )

        self.selection_changed.emit(
            piece_id
        )

    def rotate_selected_left(self):

        if self.selected_piece_id is None:
            return

        widget = self.widgets[
            self.selected_piece_id
        ]

        if not widget.available:
            return

        piece_id = (
            self.selected_piece_id
        )

        cells = self.current_cells[
            piece_id
        ]

        cells = rotate_cells_left(
            cells
        )

        self.current_cells[
            piece_id
        ] = cells

        self.widgets[
            piece_id
        ].set_cells(cells)

    def rotate_selected_right(self):

        if self.selected_piece_id is None:
            return

        widget = self.widgets[
            self.selected_piece_id
        ]

        if not widget.available:
            return

        piece_id = (
            self.selected_piece_id
        )

        cells = self.current_cells[
            piece_id
        ]

        cells = rotate_cells_right(
            cells
        )

        self.current_cells[
            piece_id
        ] = cells

        self.widgets[
            piece_id
        ].set_cells(cells)

    def flip_selected_horizontal(self):
        """
        将当前选中的 Piece 左右镜像。

        翻转基于 Piece 当前状态，
        因此如果已经旋转过，
        会直接翻转当前旋转后的形状。
        """

        if self.selected_piece_id is None:
            return

        widget = self.widgets[
            self.selected_piece_id
        ]

        # 已经放到 Board 上的 Piece
        # 在 Library 中不可操作
        if not widget.available:
            return

        piece_id = (
            self.selected_piece_id
        )

        cells = self.current_cells[
            piece_id
        ]

        cells = flip_cells_horizontal(
            cells
        )

        self.current_cells[
            piece_id
        ] = cells

        self.widgets[
            piece_id
        ].set_cells(cells)

    def mark_piece_placed(
            self,
            piece_id
    ):

        if piece_id not in self.widgets:
            return

        self.widgets[
            piece_id
        ].set_available(False)

        self.widgets[
            piece_id
        ].set_selected(False)

        if (
            self.selected_piece_id
            == piece_id
        ):
            self.selected_piece_id = None

    def reset_all(self):

        self.selected_piece_id = None

        self.current_cells = {
            piece.id: piece.cells
            for piece in PIECES
        }

        for piece in PIECES:

            widget = self.widgets[
                piece.id
            ]

            widget.set_cells(
                piece.cells
            )

            widget.set_selected(
                False
            )

            widget.set_available(
                True
            )

    def return_piece(self, piece_id):
        """
        将已放置的 Piece 恢复为 Library 中可用状态。
        保留它当前的旋转方向。
        """

        if piece_id not in self.widgets:
            return

        widget = self.widgets[piece_id]

        widget.set_available(True)
        widget.set_selected(False)

        self.selected_piece_id = None