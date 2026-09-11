# Calendar Puzzle

A small Windows desktop calendar puzzle game built with **Python** and **PySide6**.

The puzzle board contains:

- 12 month cells
- 31 day cells
- 7 weekday cells

For a selected date, the corresponding **month**, **day**, and **weekday** remain uncovered. The player uses the available puzzle pieces to fill all remaining cells.

## Features

- Automatically uses the current date on startup
- Calendar date selector
- Highlights the target month, day, and weekday
- 10 puzzle pieces
- Rotate pieces left or right
- Flip pieces horizontally
- Drag pieces from the library onto the board
- Grid snapping
- Grab and drag a piece from the exact cell clicked
- Valid / invalid placement preview
- Collision detection
- Move already placed pieces
- Drag a placed piece outside the board to return it to the library
- Reset the puzzle

## Controls

1. Select a puzzle piece from the piece library.
2. Use **Rotate Left**, **Rotate Right**, or **Flip Horizontally** if needed.
3. Click and hold any cell of the piece.
4. Drag it onto the board.
5. Green preview means the placement is valid.
6. Red preview means the placement is invalid.
7. A placed piece can be dragged again to reposition it.
8. Drag a placed piece outside the board to return it to the library.

## Project Structure

```text
CalendarPuzzle/
├─ main.py
├─ core/
│  ├─ date_mapper.py
│  ├─ piece.py
│  └─ placement.py
├─ data/
│  ├─ board_data.py
│  └─ piece_data.py
├─ ui/
│  ├─ board_widget.py
│  ├─ piece_library.py
│  └─ piece_widget.py
├─ solver/
└─ tests/
```

## Requirements

- Python 3.12
- PySide6

For development and packaging:

- pytest
- PyInstaller

Install dependencies:

```bash
pip install PySide6 pytest pyinstaller
```

## Run from Source

```bash
python main.py
```

## Build Windows Executable

A simple one-file Windows build can be created with PyInstaller:

```bash
pyinstaller --noconfirm --clean --onefile --windowed --name CalendarPuzzle main.py
```

The executable will be generated at:

```text
dist/CalendarPuzzle.exe
```

For debugging packaging issues, an `onedir` build is useful:

```bash
pyinstaller --noconfirm --clean --onedir --windowed --name CalendarPuzzle main.py
```

## Version

### v1.0 — Manual Edition

The first complete manual-play version includes piece rotation, horizontal flipping, drag-and-drop placement, collision checking, repositioning, and returning pieces to the library.

Solver-based features such as **Hint** and **Auto Solve** are intentionally not included in the v1.0 interface.

## AI Assistance

This project was developed with the assistance of **OpenAI ChatGPT**.

AI assistance was used for:

- project architecture and planning
- PySide6 UI implementation
- drag-and-drop interaction design
- piece transformation logic
- collision and placement logic
- debugging and iterative code refinement
- documentation

The project was iteratively tested and refined through manual interaction and user feedback.

## Future Work

Possible future additions include:

- automatic puzzle solver
- hint system
- solution animation
- saved solutions / daily challenge history

## License

No license has been selected yet.
