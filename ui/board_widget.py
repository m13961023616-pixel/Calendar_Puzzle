import json
from datetime import date

from PySide6.QtCore import (
    Qt,
    QRectF,
    QPoint,
    QMimeData,
    Signal,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QDrag,
    QPixmap,
    QCursor,
)

from PySide6.QtWidgets import (
    QWidget,
    QApplication,
)

from core.date_mapper import (
    get_target_positions,
)

from core.placement import (
    absolute_cells,
    can_place,
)

from data.board_data import (
    BOARD_COLS,
    BOARD_ROWS,
    CELL_LABELS,
    VALID_CELLS,
)

from ui.piece_widget import (
    PIECE_MIME_TYPE,
)


class BoardWidget(QWidget):

    piece_placed = Signal(str)
    piece_returned = Signal(str)

    def __init__(
            self,
            parent=None
    ):
        super().__init__(parent)

        self.selected_date = date.today()

        self.target_positions = (
            get_target_positions(
                self.selected_date
            )
        )

        # =================================================
        # 已经正式放置的 Piece
        #
        # {
        #     "A": {
        #         "cells": frozenset(...),
        #         "anchor": (row, col)
        #     }
        # }
        # =================================================

        self.placed_pieces = {}

        # =================================================
        # Drag Preview
        # =================================================

        self.preview_piece_id = None
        self.preview_cells = None
        self.preview_anchor = None
        self.preview_valid = False

        # =================================================
        # 棋盘内部拖拽
        #
        # 这里记录：
        #
        # 1. 用户最开始按中了哪个 Piece
        # 2. 按中了这个 Piece 的哪一个小格
        # 3. 鼠标从哪里开始按下
        # =================================================

        self.board_drag_piece_id = None
        self.board_drag_grabbed_cell = None
        self.board_drag_start_position = QPoint()

        # 当前真正正在拖动的 Piece
        #
        # 非 None 时：
        # - 原位置暂时不绘制
        # - 碰撞检测忽略它自己
        self.dragging_piece_id = None

        self.setMinimumSize(
            620,
            620
        )

        self.setAcceptDrops(True)
        self.setMouseTracking(True)

    # =====================================================
    # Date
    # =====================================================

    def set_date(
            self,
            selected_date: date
    ):
        self.selected_date = (
            selected_date
        )

        self.target_positions = (
            get_target_positions(
                selected_date
            )
        )

        self.reset_board()

        self.update()

    # =====================================================
    # Board Geometry
    # =====================================================

    def get_board_geometry(self):

        margin = 18
        spacing = 6

        available_width = (
            self.width()
            - margin * 2
        )

        available_height = (
            self.height()
            - margin * 2
        )

        cell_size = min(

            (
                available_width
                - spacing
                * (BOARD_COLS - 1)
            )
            / BOARD_COLS,

            (
                available_height
                - spacing
                * (BOARD_ROWS - 1)
            )
            / BOARD_ROWS,
        )

        total_width = (
            BOARD_COLS
            * cell_size
            + (
                BOARD_COLS - 1
            )
            * spacing
        )

        total_height = (
            BOARD_ROWS
            * cell_size
            + (
                BOARD_ROWS - 1
            )
            * spacing
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

    # =====================================================
    # 鼠标位置 -> 最近的 Board Cell
    #
    # 用于 Drag 吸附
    # =====================================================

    def board_cell_from_position(
            self,
            position
    ):
        """
        根据鼠标位置找到最近的棋盘格中心。

        鼠标跨过相邻两个 Cell 中心之间的中线，
        Piece 才会跳到下一格。
        """

        (
            cell_size,
            spacing,
            offset_x,
            offset_y,
        ) = self.get_board_geometry()

        step = (
            cell_size
            + spacing
        )

        first_center_x = (
            offset_x
            + cell_size / 2
        )

        first_center_y = (
            offset_y
            + cell_size / 2
        )

        col = round(
            (
                position.x()
                - first_center_x
            )
            / step
        )

        row = round(
            (
                position.y()
                - first_center_y
            )
            / step
        )

        if (
            row < 0
            or row >= BOARD_ROWS
            or col < 0
            or col >= BOARD_COLS
        ):
            return None

        return (
            row,
            col
        )

    # =====================================================
    # 鼠标真正点击到了哪个 Board Cell
    #
    # 与上面不同：
    # 这里不使用“最近格子”，而要求鼠标真的在格子矩形内部。
    #
    # 这样点击格子之间的缝隙不会误抓 Piece。
    # =====================================================

    def board_cell_at_position(
            self,
            position
    ):

        (
            cell_size,
            spacing,
            offset_x,
            offset_y,
        ) = self.get_board_geometry()

        for (
            row,
            col
        ) in VALID_CELLS:

            x = (
                offset_x
                + col
                * (
                    cell_size
                    + spacing
                )
            )

            y = (
                offset_y
                + row
                * (
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
    # Grabbed Cell -> Piece Anchor
    # =====================================================

    def anchor_from_position(
            self,
            position,
            grabbed_cell
    ):

        board_cell = (
            self.board_cell_from_position(
                position
            )
        )

        if board_cell is None:
            return None

        (
            board_row,
            board_col
        ) = board_cell

        (
            grabbed_row,
            grabbed_col
        ) = grabbed_cell

        return (
            board_row
            - grabbed_row,

            board_col
            - grabbed_col,
        )

    # =====================================================
    # 找到某个棋盘格属于哪个 Piece
    # =====================================================

    def find_piece_at_cell(
            self,
            board_cell
    ):
        """
        返回：

            (
                piece_id,
                info
            )

        如果这个格子没有 Piece：
            None
        """

        for (
            piece_id,
            info
        ) in self.placed_pieces.items():

            cells = absolute_cells(
                info["cells"],
                info["anchor"]
            )

            if board_cell in cells:

                return (
                    piece_id,
                    info
                )

        return None

    # =====================================================
    # Occupied Cells
    # =====================================================

    def get_occupied_cells(
            self,
            exclude_piece_id=None
    ):
        """
        获取已经占用的 Board Cell。

        exclude_piece_id：
            在移动某块 Piece 时，
            碰撞检测需要忽略它自己的旧位置。
        """

        occupied = set()

        for (
            piece_id,
            info
        ) in self.placed_pieces.items():

            if (
                piece_id
                == exclude_piece_id
            ):
                continue

            occupied |= absolute_cells(
                info["cells"],
                info["anchor"]
            )

        return occupied

    # =====================================================
    # Board Mouse Press
    # =====================================================

    def mousePressEvent(
            self,
            event
    ):

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            super().mousePressEvent(
                event
            )
            return

        # 用户到底点到了哪个真实格子
        board_cell = (
            self.board_cell_at_position(
                event.position()
            )
        )

        if board_cell is None:

            self.clear_board_drag_candidate()

            super().mousePressEvent(
                event
            )
            return

        result = (
            self.find_piece_at_cell(
                board_cell
            )
        )

        # 点的是普通空格 / 日期目标格
        if result is None:

            self.clear_board_drag_candidate()

            super().mousePressEvent(
                event
            )
            return

        (
            piece_id,
            info
        ) = result

        (
            anchor_row,
            anchor_col
        ) = info["anchor"]

        (
            board_row,
            board_col
        ) = board_cell

        # =================================================
        # 算出：
        # 用户按中了 Piece 自身的哪个 Local Cell
        # =================================================

        grabbed_cell = (
            board_row
            - anchor_row,

            board_col
            - anchor_col,
        )

        self.board_drag_piece_id = (
            piece_id
        )

        self.board_drag_grabbed_cell = (
            grabbed_cell
        )

        self.board_drag_start_position = (
            event.position().toPoint()
        )

        event.accept()

    # =====================================================
    # Board Mouse Move
    # =====================================================

    def mouseMoveEvent(self, event):

        # =====================================================
        # 情况 1：
        # 当前正准备拖动 Board 上的 Piece
        # =====================================================

        if (
                self.board_drag_piece_id
                is not None
        ):

            if (
                    self.board_drag_grabbed_cell
                    is None
            ):
                return

            if (
                    event.buttons()
                    & Qt.MouseButton.LeftButton
            ):

                distance = (
                        event.position().toPoint()
                        - self.board_drag_start_position
                ).manhattanLength()

                if (
                        distance
                        >= QApplication.startDragDistance()
                ):
                    self.start_board_drag()

                    self.clear_board_drag_candidate()

                return

        # =====================================================
        # 情况 2：
        # 没有按鼠标，只是在 Board 上移动
        #
        # 判断是不是悬停在已放置 Piece 上。
        # =====================================================

        if (
                event.buttons()
                == Qt.MouseButton.NoButton
        ):

            board_cell = (
                self.board_cell_at_position(
                    event.position()
                )
            )

            if board_cell is not None:

                result = (
                    self.find_piece_at_cell(
                        board_cell
                    )
                )

                if result is not None:
                    self.setCursor(
                        Qt.CursorShape.PointingHandCursor
                    )

                    event.accept()
                    return

            # 没有悬停在 Piece 上
            self.unsetCursor()

        super().mouseMoveEvent(
            event
        )

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    # =====================================================
    # Board Mouse Release
    # =====================================================

    def mouseReleaseEvent(
            self,
            event
    ):

        self.clear_board_drag_candidate()

        super().mouseReleaseEvent(
            event
        )

    # =====================================================
    # 清理“准备拖动”的临时状态
    # =====================================================

    def clear_board_drag_candidate(self):

        self.board_drag_piece_id = None

        self.board_drag_grabbed_cell = None

        self.board_drag_start_position = (
            QPoint()
        )

    # =====================================================
    # 开始拖动已经放好的 Piece
    # =====================================================

    def start_board_drag(self):

        piece_id = (
            self.board_drag_piece_id
        )

        grabbed_cell = (
            self.board_drag_grabbed_cell
        )

        if (
            piece_id is None
            or grabbed_cell is None
        ):
            return

        if (
            piece_id
            not in self.placed_pieces
        ):
            return

        info = self.placed_pieces[
            piece_id
        ]

        cells = info["cells"]

        # =================================================
        # 标记这块正在移动
        #
        # 注意：
        # 我们没有真的把它从 placed_pieces 删除。
        #
        # 好处：
        # 如果用户取消 Drag，
        # 原来的 Piece 自动恢复。
        # =================================================

        self.dragging_piece_id = (
            piece_id
        )

        self.update()

        drag = QDrag(self)

        mime = QMimeData()

        (
            grabbed_row,
            grabbed_col
        ) = grabbed_cell

        data = {
            # 明确告诉 Board：
            # 这是从 Board 自己拿起来的，
            # 不是从右侧 PieceLibrary 拿来的。
            "source": "board",

            "piece_id": piece_id,

            "cells": [
                [row, col]
                for row, col in cells
            ],

            "grabbed_row":
                grabbed_row,

            "grabbed_col":
                grabbed_col,
        }

        mime.setData(
            PIECE_MIME_TYPE,
            json.dumps(
                data
            ).encode("utf-8")
        )

        drag.setMimeData(
            mime
        )

        # =================================================
        # 和你现在右侧 Piece 拖动保持一致：
        #
        # 不显示系统拖拽截图/箭头。
        #
        # 你之前说拖动时鼠标消失也可以接受，
        # 所以这里沿用同样效果。
        # =================================================

        transparent_pixmap = (
            QPixmap(1, 1)
        )

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

        result = Qt.DropAction.IgnoreAction

        try:

            result = drag.exec(
                Qt.DropAction.MoveAction
            )

        finally:

            # =====================================================
            # 如果最终没有合法 Drop，
            # 需要判断到底是：
            #
            # 1. 拖到 Board 外 -> 收回 Library
            # 2. Board 内非法位置 -> 回原位置
            # =====================================================

            if (
                    result
                    == Qt.DropAction.IgnoreAction
            ):

                global_pos = (
                    QCursor.pos()
                )

                local_pos = (
                    self.mapFromGlobal(
                        global_pos
                    )
                )

                inside_board_widget = (
                    self.rect().contains(
                        local_pos
                    )
                )

                # ---------------------------------------------
                # 鼠标已经在 Board Widget 外
                # -> 收回 Piece Library
                # ---------------------------------------------

                if not inside_board_widget:

                    if (
                            piece_id
                            in self.placed_pieces
                    ):
                        del self.placed_pieces[
                            piece_id
                        ]

                        self.piece_returned.emit(
                            piece_id
                        )

            self.dragging_piece_id = None

            self.clear_preview()

            self.update()

    # =====================================================
    # MIME
    # =====================================================

    def read_piece_data(
            self,
            event
    ):

        mime = event.mimeData()

        if not mime.hasFormat(
            PIECE_MIME_TYPE
        ):
            return None

        try:

            raw_data = bytes(
                mime.data(
                    PIECE_MIME_TYPE
                )
            ).decode("utf-8")

            data = json.loads(
                raw_data
            )

            # 旧版 PieceWidget 没有 source 时，
            # 默认认为来自右侧 Library。
            source = data.get(
                "source",
                "library"
            )

            piece_id = (
                data["piece_id"]
            )

            cells = frozenset(
                (
                    int(row),
                    int(col)
                )
                for row, col
                in data["cells"]
            )

            grabbed_cell = (
                int(
                    data["grabbed_row"]
                ),
                int(
                    data["grabbed_col"]
                ),
            )

            return (
                source,
                piece_id,
                cells,
                grabbed_cell,
            )

        except (
            KeyError,
            ValueError,
            TypeError,
            json.JSONDecodeError
        ):
            return None

    # =====================================================
    # Drag Enter
    # =====================================================

    def dragEnterEvent(
            self,
            event
    ):

        data = (
            self.read_piece_data(
                event
            )
        )

        if data is None:

            event.ignore()
            return

        (
            source,
            piece_id,
            cells,
            grabbed_cell
        ) = data

        # =================================================
        # 从 Library 来：
        # 同一块不能重复放置
        # =================================================

        if source == "library":

            if (
                piece_id
                in self.placed_pieces
            ):
                event.ignore()
                return

        # =================================================
        # 从 Board 来：
        # 必须确实已经存在
        # =================================================

        elif source == "board":

            if (
                piece_id
                not in self.placed_pieces
            ):
                event.ignore()
                return

        else:

            event.ignore()
            return

        event.acceptProposedAction()

    # =====================================================
    # Drag Move
    # =====================================================

    def dragMoveEvent(
            self,
            event
    ):

        data = (
            self.read_piece_data(
                event
            )
        )

        if data is None:

            self.clear_preview()

            event.ignore()
            return

        (
            source,
            piece_id,
            cells,
            grabbed_cell
        ) = data

        anchor = (
            self.anchor_from_position(
                event.position(),
                grabbed_cell,
            )
        )

        if anchor is None:

            self.clear_preview()

            event.ignore()
            return

        # =================================================
        # 如果是在移动棋盘上的 Piece，
        # occupied 必须忽略它自己的原位置。
        # =================================================

        exclude_piece_id = None

        if source == "board":
            exclude_piece_id = (
                piece_id
            )

        occupied = (
            self.get_occupied_cells(
                exclude_piece_id
            )
        )

        valid = can_place(
            cells,
            anchor,
            self.target_positions,
            occupied,
        )

        self.preview_piece_id = (
            piece_id
        )

        self.preview_cells = (
            cells
        )

        self.preview_anchor = (
            anchor
        )

        self.preview_valid = (
            valid
        )

        self.update()

        event.acceptProposedAction()

    # =====================================================
    # Drag Leave
    # =====================================================

    def dragLeaveEvent(
            self,
            event
    ):

        self.clear_preview()

        event.accept()

    # =====================================================
    # Drop
    # =====================================================

    def dropEvent(
            self,
            event
    ):

        data = (
            self.read_piece_data(
                event
            )
        )

        if data is None:

            event.ignore()
            return

        (
            source,
            piece_id,
            cells,
            grabbed_cell
        ) = data

        anchor = (
            self.anchor_from_position(
                event.position(),
                grabbed_cell,
            )
        )

        if anchor is None:

            self.clear_preview()

            event.ignore()
            return

        exclude_piece_id = None

        if source == "board":
            exclude_piece_id = (
                piece_id
            )

        occupied = (
            self.get_occupied_cells(
                exclude_piece_id
            )
        )

        valid = can_place(
            cells,
            anchor,
            self.target_positions,
            occupied,
        )

        if not valid:

            self.clear_preview()

            event.ignore()
            return

        # =================================================
        # 情况 1：
        # 从右侧 Library 第一次放入
        # =================================================

        if source == "library":

            self.placed_pieces[
                piece_id
            ] = {
                "cells": cells,
                "anchor": anchor,
            }

            # 通知 PieceLibrary：
            # 这块已经使用，变灰
            self.piece_placed.emit(
                piece_id
            )

        # =================================================
        # 情况 2：
        # 已经在 Board 上，
        # 这里只更新位置。
        # =================================================

        elif source == "board":

            self.placed_pieces[
                piece_id
            ] = {
                "cells": cells,
                "anchor": anchor,
            }

        self.clear_preview()

        self.update()

        event.acceptProposedAction()

    # =====================================================
    # Preview
    # =====================================================

    def clear_preview(self):

        self.preview_piece_id = None
        self.preview_cells = None
        self.preview_anchor = None
        self.preview_valid = False

        self.update()

    # =====================================================
    # Reset
    # =====================================================

    def reset_board(self):

        self.placed_pieces.clear()

        self.dragging_piece_id = None

        self.clear_board_drag_candidate()

        self.clear_preview()

        self.update()

    # =====================================================
    # Drawing Helper
    # =====================================================

    def draw_cell(
            self,
            painter,
            row,
            col,
            cell_size,
            spacing,
            offset_x,
            offset_y,
            fill_color,
            border_color,
            text=None,
            text_color=None,
    ):

        x = (
            offset_x
            + col
            * (
                cell_size
                + spacing
            )
        )

        y = (
            offset_y
            + row
            * (
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
                1.5
            )
        )

        painter.drawRoundedRect(
            rect,
            10,
            10
        )

        if text is None:
            return

        font = QFont(
            "Microsoft YaHei"
        )

        if "星期" in text:

            font.setPointSize(10)
            font.setBold(True)

        elif len(text) >= 3:

            font.setPointSize(12)
            font.setBold(True)

        else:

            font.setPointSize(13)
            font.setBold(True)

        painter.setFont(
            font
        )

        painter.setPen(
            text_color
            or QColor("#333333")
        )

        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

    # =====================================================
    # Paint
    # =====================================================

    def paintEvent(
            self,
            event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#FFFFFF")
        )

        (
            cell_size,
            spacing,
            offset_x,
            offset_y,
        ) = self.get_board_geometry()

        # =================================================
        # 正在移动的 Piece 暂时不算 occupied。
        #
        # 这样：
        # - 原位置下面的日期文字重新出现
        # - Piece 看起来真的被“拿起来了”
        # =================================================

        occupied = (
            self.get_occupied_cells(
                self.dragging_piece_id
            )
        )

        # =================================================
        # 1. Board
        # =================================================

        for (
            row,
            col
        ) in VALID_CELLS:

            pos = (
                row,
                col
            )

            label = (
                CELL_LABELS[pos]
            )

            if pos in occupied:
                continue

            if (
                pos
                in self.target_positions
            ):

                fill = QColor(
                    "#F6D9A7"
                )

                border = QColor(
                    "#D4A04D"
                )

                text_color = QColor(
                    "#5C420E"
                )

            else:

                fill = QColor(
                    "#F8F5EF"
                )

                border = QColor(
                    "#D8D2C8"
                )

                text_color = QColor(
                    "#3A332B"
                )

            self.draw_cell(
                painter,
                row,
                col,
                cell_size,
                spacing,
                offset_x,
                offset_y,
                fill,
                border,
                label,
                text_color,
            )

        # =================================================
        # 2. 已经放置的 Pieces
        # =================================================

        for (
            piece_id,
            info
        ) in self.placed_pieces.items():

            # 当前正在拖动的 Piece
            # 不在旧位置绘制
            if (
                piece_id
                == self.dragging_piece_id
            ):
                continue

            cells = (
                absolute_cells(
                    info["cells"],
                    info["anchor"]
                )
            )

            for (
                row,
                col
            ) in cells:

                self.draw_cell(
                    painter,
                    row,
                    col,
                    cell_size,
                    spacing,
                    offset_x,
                    offset_y,

                    QColor(
                        "#D7DED8"
                    ),

                    QColor(
                        "#87978A"
                    ),
                )

        # =================================================
        # 3. Drag Preview
        # =================================================

        if (
            self.preview_cells
            is not None
            and self.preview_anchor
            is not None
        ):

            cells = (
                absolute_cells(
                    self.preview_cells,
                    self.preview_anchor,
                )
            )

            if self.preview_valid:

                fill = QColor(
                    182,
                    218,
                    187,
                    170,
                )

                border = QColor(
                    "#65A76D"
                )

            else:

                fill = QColor(
                    235,
                    169,
                    169,
                    165,
                )

                border = QColor(
                    "#C85C5C"
                )

            for (
                row,
                col
            ) in cells:

                if (
                    row < 0
                    or row >= BOARD_ROWS
                    or col < 0
                    or col >= BOARD_COLS
                ):
                    continue

                self.draw_cell(
                    painter,
                    row,
                    col,
                    cell_size,
                    spacing,
                    offset_x,
                    offset_y,
                    fill,
                    border,
                )