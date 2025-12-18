import ast
import os
import sys
from typing import Dict, List, Optional, Set, Tuple


FlowEdge = Tuple[str, str, str]  # (caller, callee, args_as_text)


class FlowAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.flow_data: List[FlowEdge] = []
        self.current_function = "Main Script"

    def visit_FunctionDef(self, node):
        previous_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = previous_function

    def visit_Call(self, node):
        callee_name = self._get_func_name(node)

        args_passed = []
        for arg in node.args:
            if isinstance(arg, ast.Name):
                args_passed.append(arg.id)
            elif isinstance(arg, ast.Constant):
                args_passed.append(str(arg.value))
            else:
                args_passed.append("expr")

        args_str = ", ".join(args_passed)

        if callee_name:
            self.flow_data.append((self.current_function, callee_name, args_str))

        self.generic_visit(node)

    def _get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


def analyze_flow(target_file: str) -> Optional[Dict[str, object]]:
    """Parse a Python file and return program flow data for GUI rendering.

    Returns a dict with:
      - nodes: set[str]
      - edges: list[(caller, callee, args_as_text)]
    or None on error.
    """

    if not os.path.exists(target_file):
        print(f"Error: Could not find file at: {os.path.abspath(target_file)}")
        return None

    try:
        with open(target_file, "r", encoding="utf-8") as source:
            tree = ast.parse(source.read())
    except Exception as e:
        print(f"Error: Failed to parse Python file: {e}")
        return None

    analyzer = FlowAnalyzer()
    analyzer.visit(tree)

    nodes: Set[str] = set(["Main Script"])
    for caller, callee, _ in analyzer.flow_data:
        nodes.add(caller)
        nodes.add(callee)

    return {"nodes": nodes, "edges": analyzer.flow_data}


def _run_cli() -> int:
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_python_file.py>")
        return 2

    target_path = sys.argv[1]
    data = analyze_flow(target_path)
    if not data:
        return 1

    edges = data["edges"]
    print("Edges:")
    for caller, callee, args in edges:  # type: ignore[misc]
        suffix = f" ({args})" if args else ""
        print(f"  {caller} -> {callee}{suffix}")

    return 0


# --- Usage ---
if __name__ == "__main__":
    # If a file is passed, run CLI mode. Otherwise, launch the GUI.
    if len(sys.argv) > 1:
        raise SystemExit(_run_cli())

    from gui import run_app

    run_app()
