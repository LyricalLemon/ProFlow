import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional, Set, Tuple

from main import FlowEdge, analyze_flow


# Theme
BG = "#4a4a4a"  # grey
PANEL_BG = "#3f3f3f"
NODE_BG = "#2f2f2f"
ORANGE = "#ff8c00"  # bright orange
ORANGE_SOFT = "#cc6f00"


def _is_python_file(path: str) -> bool:
    return isinstance(path, str) and path.lower().endswith(".py") and os.path.isfile(path)


def _clean_dnd_path(path: str) -> str:
    # On Windows tkinterdnd2 may wrap paths in braces if they contain spaces.
    return path.strip().strip("{}")


def _compute_layout(nodes: Set[str], edges: List[FlowEdge]) -> Dict[str, Tuple[int, int]]:
    # Simple left-to-right layered layout (good enough for v1).
    start = "Main Script"

    adj: Dict[str, Set[str]] = {n: set() for n in nodes}
    for caller, callee, _ in edges:
        adj.setdefault(caller, set()).add(callee)
        adj.setdefault(callee, set())

    # Level assignment via BFS from start.
    levels: Dict[str, int] = {start: 0}
    queue: List[str] = [start]
    while queue:
        u = queue.pop(0)
        for v in adj.get(u, set()):
            candidate = levels[u] + 1
            if v not in levels or candidate < levels[v]:
                levels[v] = candidate
                queue.append(v)

    # Any disconnected nodes go after the connected component.
    max_level = max(levels.values()) if levels else 0
    for n in sorted(nodes):
        if n not in levels:
            max_level += 1
            levels[n] = max_level

    buckets: Dict[int, List[str]] = {}
    for n, lvl in levels.items():
        buckets.setdefault(lvl, []).append(n)
    for lvl in buckets:
        buckets[lvl].sort()

    dx = 260
    dy = 120
    margin_x = 120
    margin_y = 120

    pos: Dict[str, Tuple[int, int]] = {}
    for lvl in sorted(buckets.keys()):
        for i, n in enumerate(buckets[lvl]):
            x = margin_x + lvl * dx
            y = margin_y + i * dy
            pos[n] = (x, y)

    return pos


class ProFlowGUI:
    def __init__(self, root: tk.Tk, dnd_available: bool):
        self.root = root
        self.dnd_available = dnd_available
        self.selected_file: Optional[str] = None

        self.root.title("ProFlow")
        self.root.geometry("980x620")
        self.root.minsize(820, 520)
        self.root.configure(bg=BG)

        # Top controls
        self.controls = tk.Frame(self.root, bg=PANEL_BG)
        self.controls.pack(side="top", fill="x")

        self.title_label = tk.Label(
            self.controls,
            text="ProFlow",
            bg=PANEL_BG,
            fg=ORANGE,
            font=("Helvetica", 18, "bold"),
        )
        self.title_label.pack(side="left", padx=14, pady=10)

        self.open_btn = tk.Button(
            self.controls,
            text="Open Python File...",
            command=self.open_file_dialog,
            bg=BG,
            fg=ORANGE,
            activebackground=BG,
            activeforeground=ORANGE,
            relief="flat",
            width=18,
        )
        self.open_btn.pack(side="right", padx=14, pady=10)

        self.clear_btn = tk.Button(
            self.controls,
            text="Clear",
            command=self.clear_diagram,
            bg=BG,
            fg=ORANGE,
            activebackground=BG,
            activeforeground=ORANGE,
            relief="flat",
            width=10,
        )
        self.clear_btn.pack(side="right", padx=(0, 10), pady=10)

        self.status_var = tk.StringVar(value="Drop a .py file into the window, or click 'Open Python File...'.")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=BG,
            fg=ORANGE,
            font=("Helvetica", 11),
            wraplength=900,
            justify="center",
        )
        self.status_label.pack(side="top", fill="x", padx=10, pady=(6, 0))

        hint_text = "Drag-and-drop is enabled." if dnd_available else "Drag-and-drop not available (pip install tkinterdnd2)."
        self.hint_label = tk.Label(self.root, text=hint_text, bg=BG, fg=ORANGE_SOFT, font=("Helvetica", 9))
        self.hint_label.pack(side="top", fill="x", padx=10, pady=(2, 8))

        # Diagram canvas + scrollbars
        self.diagram_frame = tk.Frame(self.root, bg=BG)
        self.diagram_frame.pack(side="top", fill="both", expand=True)

        self.x_scroll = tk.Scrollbar(self.diagram_frame, orient="horizontal")
        self.y_scroll = tk.Scrollbar(self.diagram_frame, orient="vertical")

        self.canvas = tk.Canvas(
            self.diagram_frame,
            bg=BG,
            highlightthickness=0,
            xscrollcommand=self.x_scroll.set,
            yscrollcommand=self.y_scroll.set,
        )

        self.x_scroll.config(command=self.canvas.xview)
        self.y_scroll.config(command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.x_scroll.grid(row=1, column=0, sticky="ew")

        self.diagram_frame.rowconfigure(0, weight=1)
        self.diagram_frame.columnconfigure(0, weight=1)

        # Watermark / instruction text
        self.watermark_id = self.canvas.create_text(
            0,
            0,
            text="Drag Python Files ;)",
            fill=ORANGE_SOFT,
            font=("Helvetica", 52, "bold"),
            anchor="center",
        )
        self._center_watermark()

        # Built-in canvas panning (click + drag)
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.root.bind("<Configure>", lambda _e: self._center_watermark())

    def _center_watermark(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            self.canvas.coords(self.watermark_id, w // 2, h // 2)

    def clear_diagram(self):
        self.canvas.delete("flow")
        # Re-show watermark
        self.canvas.itemconfigure(self.watermark_id, state="normal")
        self.canvas.configure(scrollregion=(0, 0, 0, 0))
        self.status_var.set("Drop a .py file into the window, or click 'Open Python File...'.")

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Select a Python file",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return
        self._handle_file(path)

    def _draw_flow(self, nodes: Set[str], edges: List[FlowEdge]):
        self.canvas.delete("flow")
        self.canvas.itemconfigure(self.watermark_id, state="hidden")

        pos = _compute_layout(nodes, edges)

        # Node size heuristic
        def node_size(label: str) -> Tuple[int, int]:
            w = max(130, min(320, 10 * len(label)))
            h = 62
            return w, h

        bounds_min_x = 10**9
        bounds_min_y = 10**9
        bounds_max_x = -10**9
        bounds_max_y = -10**9

        # Draw edges first so nodes appear on top.
        for caller, callee, args in edges:
            if caller not in pos or callee not in pos:
                continue
            x0, y0 = pos[caller]
            x1, y1 = pos[callee]
            self.canvas.create_line(
                x0,
                y0,
                x1,
                y1,
                fill=ORANGE,
                width=2,
                arrow=tk.LAST,
                arrowshape=(12, 14, 6),
                tags=("flow",),
            )
            if args:
                mx = (x0 + x1) // 2
                my = (y0 + y1) // 2
                self.canvas.create_text(
                    mx,
                    my - 14,
                    text=f"({args})",
                    fill=ORANGE_SOFT,
                    font=("Helvetica", 9),
                    tags=("flow",),
                )

        # Draw nodes
        for node in nodes:
            x, y = pos.get(node, (0, 0))
            label = "Start" if node == "Main Script" else node
            w, h = node_size(label)
            x0 = x - w // 2
            y0 = y - h // 2
            x1 = x + w // 2
            y1 = y + h // 2

            self.canvas.create_oval(
                x0,
                y0,
                x1,
                y1,
                fill=NODE_BG,
                outline=ORANGE,
                width=2,
                tags=("flow",),
            )
            self.canvas.create_text(
                x,
                y,
                text=label,
                fill=ORANGE,
                font=("Helvetica", 12, "bold"),
                tags=("flow",),
            )

            bounds_min_x = min(bounds_min_x, x0)
            bounds_min_y = min(bounds_min_y, y0)
            bounds_max_x = max(bounds_max_x, x1)
            bounds_max_y = max(bounds_max_y, y1)

        if bounds_max_x < bounds_min_x:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            return

        pad = 120
        self.canvas.configure(scrollregion=(bounds_min_x - pad, bounds_min_y - pad, bounds_max_x + pad, bounds_max_y + pad))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def _handle_file(self, path: str):
        path = _clean_dnd_path(path)
        if not _is_python_file(path):
            messagebox.showerror("ProFlow", "Please select a valid .py file.")
            return

        self.selected_file = path
        self.status_var.set(f"Analyzing: {path}")
        self.root.update_idletasks()

        data = analyze_flow(path)
        if not data:
            self.status_var.set("Failed to analyze file. See terminal output for details.")
            return

        nodes = data["nodes"]
        edges = data["edges"]
        self._draw_flow(nodes, edges)  # type: ignore[arg-type]
        self.status_var.set("Diagram rendered. (Tip: click + drag to pan)")


def run_app() -> None:
    dnd_available = False

    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore

        class _Root(TkinterDnD.Tk):
            pass

        root: tk.Tk = _Root()
        dnd_available = True
    except Exception:
        root = tk.Tk()
        DND_FILES = None  # type: ignore

    app = ProFlowGUI(root, dnd_available=dnd_available)

    if dnd_available:
        def _on_drop(event):
            paths = root.tk.splitlist(event.data)
            if not paths:
                return
            app._handle_file(paths[0])

        # Drop anywhere on the diagram canvas.
        app.canvas.drop_target_register(DND_FILES)
        app.canvas.dnd_bind("<<Drop>>", _on_drop)

    root.mainloop()


if __name__ == "__main__":
    run_app()
