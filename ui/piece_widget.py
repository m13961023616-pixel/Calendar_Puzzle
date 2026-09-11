import json

from PySide6.QtCore import (
    Qt,
    QRectF,
    QPoint,
    QMimeData,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QDrag,
    QPixmap,
)
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
)


PIECE_MIME_TYPE = "application/x-calendar-puzzle-piece"


class PieceWidget(QWidget):

    clicked = Signal(str)

    # =====================================================
    # 统一的 Piece 显示参数
    # =====================================================

    CELL_SIZE = 18
    CELL_SPACING = 3
    CORNER_RADIUS = 3
    BORDER_WIDTH = 1.3

    def __init__(
            self,
            piece_id,
            cells,
            parent=None
    ):
        super().__init__(parent)

        self.piece_id = piece_id
        self.cells = cells

        self.selected = False
        self.available = True

        # 鼠标按下的位置
        self.drag_start_position = QPoint()

        # 用户真正抓住了 Piece 的哪一个格子
        # 例如 (1, 0)
        self.grabbed_cell = None

        self.setMinimumHeight(96)

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

    # =====================================================
    # Piece 状态
    # =====================================================

    def set_cells(self, cells):
        self.cells = cells
        self.update()

    def set_selected(self, selected: bool):
        self.selected = selected
        self.update()

    def set_available(self, available: bool):
        self.available = available

        if available:
            self.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
        else:
            self.setCursor(
                Qt.CursorShape.ForbiddenCursor
            )

        self.update()

    # =====================================================
    # Piece geometry
    # =====================================================

    def get_piece_geometry(self):
        """
        返回 Piece 在这个 Widget 中的绘制参数。

        这里和 paintEvent 使用完全相同的算法，
        因此可以准确判断用户点中了哪个小格。
        """

        if not self.cells:
            return None

        rows = [
            row
            for row, col in self.cells
        ]

        cols = [
            col
            for row, col in self.cells
        ]

        piece_rows = max(rows) + 1
        piece_cols = max(cols) + 1

        cell_size = self.CELL_SIZE
        spacing = self.CELL_SPACING

        total_width = (
            piece_cols * cell_size
            + (piece_cols - 1) * spacing
        )

        total_height = (
            piece_rows * cell_size
            + (piece_rows - 1) * spacing
        )

        offset_x = (
            self.width()
            - total_width
        ) / 2

        offset_y = (
            self.height()
            - total_height
        ) / 2

        return (
            cell_size,
            spacing,
            offset_x,
            offset_y,
        )

    def cell_from_position(self, position):
        """
        判断鼠标在 Piece 上点击了哪个真实小格。

        返回：
            (row, col)

        如果点在 Piece 外面的空白区域：
            None
        """

        geometry = self.get_piece_geometry()

        if geometry is None:
            return None

        (
            cell_size,
            spacing,
            offset_x,
            offset_y,
        ) = geometry

        for row, col in self.cells:

            x = (
                offset_x
                + col * (
                    cell_size
                    + spacing
                )
            )

            y = (
                offset_y
                + row * (
                    cell_size
                    + spacing
                )
            )

            rect = QRectF(
                x,
                y,
                cell_size,
                cell_size,
            )

            if rect.contains(position):
                return (
                    row,
                    col
                )

        return None

    # =====================================================
    # Mouse
    # =====================================================

    def mousePressEvent(self, event):

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            super().mousePressEvent(event)
            return

        if not self.available:
            return

        mouse_position = (
            event.position()
        )

        # ---------------------------------------------
        # 关键：
        # 判断用户真正按住的是 Piece 哪一个小格
        # ---------------------------------------------

        grabbed_cell = (
            self.cell_from_position(
                mouse_position
            )
        )

        # 点在 Piece 周围空白区域
        # 不开始拖动
        if grabbed_cell is None:
            return

        self.grabbed_cell = (
            grabbed_cell
        )

        self.drag_start_position = (
            mouse_position.toPoint()
        )

        self.clicked.emit(
            self.piece_id
        )

        event.accept()

    def mouseMoveEvent(self, event):

        if not self.available:
            return

        if self.grabbed_cell is None:
            return

        if not (
            event.buttons()
            & Qt.MouseButton.LeftButton
        ):
            return

        distance = (
            event.position().toPoint()
            - self.drag_start_position
        ).manhattanLength()

        if (
            distance
            < QApplication.startDragDistance()
        ):
            return

        self.start_drag()

        # drag.exec() 返回以后，
        # 本次拖动已经结束
        self.grabbed_cell = None

    def mouseReleaseEvent(self, event):

        # 如果只是点击，没有形成 Drag，
        # 松开后清理 grabbed_cell
        self.grabbed_cell = None

        super().mouseReleaseEvent(event)

    # =====================================================
    # Drag
    # =====================================================

    def start_drag(self):
        """
        开始 Drag & Drop。

        特点：
        1. 不显示 PieceWidget 截图
        2. 鼠标保持食指手型
        3. 尽量移除系统默认的 MoveAction 小箭头
        """

        if self.grabbed_cell is None:
            return

        drag = QDrag(self)

        mime = QMimeData()

        grabbed_row, grabbed_col = (
            self.grabbed_cell
        )

        data = {
            "piece_id": self.piece_id,

            "cells": [
                [row, col]
                for row, col in self.cells
            ],

            "grabbed_row": grabbed_row,
            "grabbed_col": grabbed_col,
        }

        mime.setData(
            PIECE_MIME_TYPE,
            json.dumps(
                data
            ).encode("utf-8")
        )

        drag.setMimeData(mime)

        # =====================================================
        # 不再显示 Piece 的 Widget 截图
        # =====================================================

        # 创建一个完全透明的小 Pixmap，
        # 用来替换 Qt / Windows 默认的拖拽动作图标。
        transparent_pixmap = QPixmap(1, 1)
        transparent_pixmap.fill(
            Qt.GlobalColor.transparent
        )

        drag.setDragCursor(
            transparent_pixmap,
            Qt.DropAction.MoveAction
        )

        drag.setDragCursor(
            transparent_pixmap,
            Qt.DropAction.CopyAction
        )

        drag.setDragCursor(
            transparent_pixmap,
            Qt.DropAction.IgnoreAction
        )

        # =====================================================
        # 拖动期间使用食指手型
        # =====================================================

        QApplication.setOverrideCursor(
            Qt.CursorShape.PointingHandCursor
        )

        try:
            drag.exec(
                Qt.DropAction.MoveAction
            )

        finally:
            # 无论 Drag 正常结束、取消还是发生异常，
            # 都恢复鼠标状态。
            QApplication.restoreOverrideCursor()

    # =====================================================
    # Paint
    # =====================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        if not self.cells:
            return

        geometry = (
            self.get_piece_geometry()
        )

        if geometry is None:
            return

        (
            cell_size,
            spacing,
            offset_x,
            offset_y,
        ) = geometry

        # ---------------------------------------------
        # 颜色
        # ---------------------------------------------

        if not self.available:

            fill_color = QColor(
                "#E5E3DF"
            )

            border_color = QColor(
                "#D8D5CF"
            )

        elif self.selected:

            fill_color = QColor(
                "#E9C98F"
            )

            border_color = QColor(
                "#C38B32"
            )

        else:

            fill_color = QColor(
                "#EDE7DD"
            )

            border_color = QColor(
                "#CFC6B8"
            )

        # ---------------------------------------------
        # 绘制每个 Piece Cell
        # ---------------------------------------------

        for row, col in self.cells:

            x = (
                offset_x
                + col * (
                    cell_size
                    + spacing
                )
            )

            y = (
                offset_y
                + row * (
                    cell_size
                    + spacing
                )
            )

            rect = QRectF(
                x,
                y,
                cell_size,
                cell_size,
            )

            painter.setBrush(
                fill_color
            )

            painter.setPen(
                QPen(
                    border_color,
                    self.BORDER_WIDTH
                )
            )

            painter.drawRoundedRect(
                rect,
                self.CORNER_RADIUS,
                self.CORNER_RADIUS,
            )