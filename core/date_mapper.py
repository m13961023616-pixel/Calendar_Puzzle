from datetime import date

from data.board_data import CELL_LABELS

WEEKDAY_LABELS = {
    0: "星期一",
    1: "星期二",
    2: "星期三",
    3: "星期四",
    4: "星期五",
    5: "星期六",
    6: "星期日",
}


def get_target_labels(selected_date: date) -> set[str]:
    """根据一个真实日期，返回应当高亮的三个标签：月 / 日 / 星期"""
    month_label = f"{selected_date.month}月"
    day_label = f"{selected_date.day}日"
    weekday_label = WEEKDAY_LABELS[selected_date.weekday()]

    return {month_label, day_label, weekday_label}


def get_target_positions(selected_date: date) -> set[tuple[int, int]]:
    """根据一个真实日期，返回棋盘上应高亮的坐标集合"""
    target_labels = get_target_labels(selected_date)

    positions = set()
    for pos, label in CELL_LABELS.items():
        if label in target_labels:
            positions.add(pos)

    return positions


def get_weekday_text(selected_date: date) -> str:
    return WEEKDAY_LABELS[selected_date.weekday()]