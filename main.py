import ast
import os
import sys
from typing import Optional

import graphviz


class FlowAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.flow_data = []
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


def generate_flow_diagram(target_file: str, output_name: str = "flow_diagram", view: bool = True) -> Optional[str]:
    """Generate a program flow PNG diagram for a Python file.

    Returns the full path to the generated PNG, or None on error.
    """

    if not os.path.exists(target_file):
        print(f"Error: Could not find file at: {os.path.abspath(target_file)}")
        return None

    print(f"Analyzing: {os.path.abspath(target_file)}...")

    try:
        with open(target_file, "r", encoding="utf-8") as source:
            tree = ast.parse(source.read())
    except Exception as e:
        print(f"Error: Failed to parse Python file: {e}")
        return None

    analyzer = FlowAnalyzer()
    analyzer.visit(tree)

    dot = graphviz.Digraph(comment="Program Flow", format="png")
    dot.attr(rankdir="LR")
    dot.attr("node", shape="oval", style="filled", fillcolor="lightblue", fontname="Helvetica")

    functions = set()
    for caller, callee, _ in analyzer.flow_data:
        functions.add(caller)
        functions.add(callee)

    for func in functions:
        label = "Start" if func == "Main Script" else func
        dot.node(func, label=label)

    for caller, callee, args in analyzer.flow_data:
        label = f"({args})" if args else ""
        dot.edge(caller, callee, label=label, fontsize="10", fontcolor="red")

    try:
        # graphviz.render returns the path to the rendered file
        rendered_path = dot.render(output_name, view=view)
    except Exception as e:
        print(f"Error: Failed to render diagram (is Graphviz installed?): {e}")
        return None

    # rendered_path should already be a .png file, but normalize just in case
    png_path = rendered_path if rendered_path.lower().endswith(".png") else f"{rendered_path}.png"
    print(f"Success! Diagram generated: {png_path}")
    return os.path.abspath(png_path)


def _run_cli() -> int:
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_python_file.py>")
        return 2

    target_path = sys.argv[1]
    out = generate_flow_diagram(target_path, view=True)
    return 0 if out else 1


# --- Usage ---
if __name__ == "__main__":
    # If a file is passed, run CLI mode. Otherwise, launch the GUI.
    if len(sys.argv) > 1:
        raise SystemExit(_run_cli())

    from gui import run_app

    run_app()
