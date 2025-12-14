import ast
import graphviz
import os

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

def generate_flow_diagram(target_file):
    # Check if file exists before processing
    if not os.path.exists(target_file):
        print(f"Error: Could not find file at: {os.path.abspath(target_file)}")
        print("Make sure 'test_script.py' is in the folder above this one!")
        return

    print(f"Analyzing: {os.path.abspath(target_file)}...")

    with open(target_file, "r") as source:
        tree = ast.parse(source.read())

    analyzer = FlowAnalyzer()
    analyzer.visit(tree)

    dot = graphviz.Digraph(comment='Program Flow', format='png')
    dot.attr(rankdir='LR') 
    dot.attr('node', shape='oval', style='filled', fillcolor='lightblue', fontname='Helvetica')
    
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

    output_name = "flow_diagram"
    dot.render(output_name, view=True)
    print(f"Success! Diagram generated: {output_name}.png")

# --- Usage ---
if __name__ == "__main__":
    # Get the parent directory path
    # '..' goes up one level from the current working directory
    target_path = os.path.join(os.path.pardir, "test_script.py")
    
    generate_flow_diagram(target_path)