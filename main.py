import sys
from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.date_mapper import get_weekday_text
from ui.board_widget import BoardWidget
from ui.piece_library import PieceLibrary


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calendar Puzzle")
        self.resize(1250, 850)

        self.current_date = date.today()

        self.board_widget = None
        self.date_edit = None
        self.weekday_label = None

        self.build_ui()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 20, 24, 24)
        root_layout.setSpacing(16)

        # ---------- 顶部 ----------
        header = QHBoxLayout()

        title = QLabel("日历拼图")
        title.setObjectName("titleLabel")

        date_panel = QHBoxLayout()
        date_panel.setSpacing(10)

        date_text = QLabel("选择日期")
        date_text.setObjectName("smallLabel")

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.date_edit.setDisplayFormat("yyyy年M月d日")
        self.date_edit.setDate(QDate(
            self.current_date.year,
            self.current_date.month,
            self.current_date.day
        ))
        self.date_edit.dateChanged.connect(self.on_date_changed)

        self.weekday_label = QLabel(get_weekday_text(self.current_date))
        self.weekday_label.setObjectName("weekdayLabel")

        date_panel.addWidget(date_text)
        date_panel.addWidget(self.date_edit)
        date_panel.addWidget(self.weekday_label)

        header.addWidget(title)
        header.addStretch()
        header.addLayout(date_panel)

        root_layout.addLayout(header)

        # ---------- 主体 ----------
        content = QHBoxLayout()
        content.setSpacing(18)

        # 左侧棋盘区
        board_panel = QFrame()
        board_panel.setObjectName("panel")

        board_layout = QVBoxLayout(board_panel)
        board_layout.setContentsMargins(20, 20, 20, 20)
        board_layout.setSpacing(12)

        board_title = QLabel("拼图棋盘")
        board_title.setObjectName("sectionTitle")

        self.board_widget = BoardWidget()
        self.board_widget.set_date(self.current_date)

        board_layout.addWidget(board_title)
        board_layout.addWidget(self.board_widget, 1)

        content.addWidget(board_panel, 3)

        # 右侧拼图片区
        piece_panel = QFrame()
        piece_panel.setObjectName("panel")

        piece_layout = QVBoxLayout(piece_panel)
        piece_layout.setContentsMargins(20, 20, 20, 20)
        piece_layout.setSpacing(12)

        piece_title = QLabel("拼图片")
        piece_title.setObjectName("sectionTitle")

        piece_layout.addWidget(piece_title)
        piece_layout.addSpacing(6)

        self.piece_library = PieceLibrary()

        self.board_widget.piece_placed.connect(
            self.piece_library.mark_piece_placed
        )

        self.board_widget.piece_returned.connect(
            self.piece_library.return_piece
        )

        piece_layout.addWidget(
            self.piece_library,
            1
        )

        rotate_left = QPushButton("↶  向左旋转")
        rotate_right = QPushButton("↷  向右旋转")
        flip_horizontal = QPushButton("⇆  左右翻转")

        rotate_left.clicked.connect(
            self.piece_library.rotate_selected_left
        )

        rotate_right.clicked.connect(
            self.piece_library.rotate_selected_right
        )

        flip_horizontal.clicked.connect(
            self.piece_library.flip_selected_horizontal
        )

        reset_button = QPushButton("重置")

        reset_button.clicked.connect(
            self.reset_game
        )

        hint_button = QPushButton("提示")
        solve_button = QPushButton("自动求解")
        hint_button.setVisible(False)
        solve_button.setVisible(False)

        piece_layout.addWidget(rotate_left)
        piece_layout.addWidget(rotate_right)
        piece_layout.addWidget(flip_horizontal)
        piece_layout.addSpacing(10)
        piece_layout.addWidget(reset_button)
        piece_layout.addWidget(hint_button)
        piece_layout.addWidget(solve_button)

        content.addWidget(piece_panel, 1)

        root_layout.addLayout(content, 1)

        self.apply_style()

    def on_date_changed(self, qdate: QDate):
        self.current_date = date(qdate.year(), qdate.month(), qdate.day())

        self.weekday_label.setText(get_weekday_text(self.current_date))
        self.board_widget.set_date(self.current_date)

        self.piece_library.reset_all()

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F2EE;
            }

            QLabel {
                color: #333333;
                font-family: "Microsoft YaHei";
            }

            #titleLabel {
                font-size: 26px;
                font-weight: 700;
            }

            #sectionTitle {
                font-size: 18px;
                font-weight: 600;
            }

            #smallLabel {
                font-size: 14px;
                color: #666666;
            }

            #weekdayLabel {
                font-size: 16px;
                font-weight: 600;
                color: #6A5531;
                background-color: #EEE6D8;
                border: 1px solid #D7CCB9;
                border-radius: 8px;
                padding: 6px 12px;
            }

            #panel {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD7;
                border-radius: 14px;
            }

            QPushButton, QDateEdit {
                background-color: #EEEAE3;
                border: 1px solid #D8D2C8;
                border-radius: 9px;
                padding: 9px 12px;
                font-size: 14px;
                color: #333333;
                font-family: "Microsoft YaHei";
            }

            QPushButton:hover, QDateEdit:hover {
                background-color: #E6E0D7;
            }

            QPushButton:pressed {
                background-color: #DAD3C8;
            }
        """)

    def reset_game(self):
        self.board_widget.reset_board()

        self.piece_library.reset_all()


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()