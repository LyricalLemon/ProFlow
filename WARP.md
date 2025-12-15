# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project overview
ProFlow is a small Python static-analysis tool that parses a Python source file into an AST and produces a Graphviz call-flow diagram (caller → callee), including a best-effort label of arguments at each call site.

## Common commands (Windows / PowerShell)
### Setup
ProFlow depends on:
- The Python package `graphviz` (installed via pip)
- A local Graphviz installation so the `dot` binary is available (see `README.md`)

Create a virtual environment and install the Python dependency:
- `python -m venv .venv`
- `.\.venv\Scripts\Activate.ps1`
- `python -m pip install -U pip`
- `pip install graphviz`

### Run
The main entrypoint is `main.py`:
- `python .\main.py`

Note: `main.py` currently analyzes a hard-coded relative path (`..\test_script.py`) based on the *current working directory*. If you want to analyze the `test_script.py` that lives in this repo root, you can run:
- `python -c "import main; main.generate_flow_diagram(r'.\\test_script.py')"`

### “Tests”
There is no automated test harness in this repo yet. `test_script.py` is a small dummy input program used to demonstrate call-flow extraction.

## Architecture / code structure
### Call graph extraction (AST visitor)
`main.py` contains `FlowAnalyzer`, an `ast.NodeVisitor` that builds `flow_data` as a list of edges:
- Each edge is a tuple `(caller_function_name, callee_function_name, args_string)`.
- `current_function` tracks context while traversing:
  - Defaults to `"Main Script"` for top-level calls.
  - `visit_FunctionDef` updates `current_function` while visiting that function body.
- `visit_Call` records calls and tries to stringify positional args:
  - `ast.Name` → variable name
  - `ast.Constant` → literal value
  - otherwise `"expr"`
- `_get_func_name` extracts the callee name for `foo(...)` and `obj.foo(...)` (attribute calls only record the attribute name, not the object/type).

### Diagram generation
`generate_flow_diagram(target_file)` in `main.py`:
- Reads and parses the target file (`ast.parse`).
- Runs `FlowAnalyzer` to collect edges.
- Builds a `graphviz.Digraph`:
  - Adds nodes for any seen callers/callees.
  - Renames the `"Main Script"` node label to `"Start"`.
  - Adds directed edges with labels `(args)`.
- Renders output to `flow_diagram.png` in the working directory (and also creates a `flow_diagram` render artifact).

## Key files
- `main.py`: AST traversal + Graphviz rendering (primary implementation)
- `test_script.py`: sample program used as analysis input
- `flow_diagram.png`: example output artifact
- `CHANGE_LOG.md`: planned/desired features and release notes
