# ProFlow
A Python-based static analysis tool using Abstract Syntax Trees (ASTs) to inspect source code, identify function definitions, function calls and track caller–callee relationships across a codebase.

## Setup
Python deps:
- `pip install graphviz`
- Optional (for drag-and-drop in the GUI): `pip install tkinterdnd2`

Graphviz (system install) is also required:
https://www.graphviz.org/download/

## Run
GUI (drag a `.py` file into the window or use the "Open Python File..." button):
- `python gui.py`

CLI:
- `python main.py path\to\file.py`
