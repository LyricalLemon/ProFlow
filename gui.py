import builtins
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional, Set, Tuple
from PIL import Image, ImageTk

from main import FlowEdge, analyze_flow

# Theme
BG = "#4a4a4a"  # grey
PANEL_BG = "#3f3f3f"
NODE_BG = "#2f2f2f"
ORANGE = "#ff8c00"  # bright orange

BUILTINS: Set[str] = set(dir(builtins))

def _is_python_file(path: str) -> bool:
    return isinstance(path, str) and path.lower().endswith(".py") and os.path.isfile(path)

def _clean_dnd_path(path: str) -> str:
    # On Windows tkinterdnd2 may wrap paths in braces if they contain spaces.
    return path.strip().strip("{}")

def _create_rounded_rect(
    canvas: tk.Canvas,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    radius: int,
    **kwargs,
):
    # Approximate a rounded rectangle using a smoothed polygon.
    r = max(0, min(radius, abs(x1 - x0) // 2, abs(y1 - y0) // 2))
    points = [
        x0 + r,
        y0,
        x1 - r,
        y0,
        x1,
        y0,
        x1,
        y0 + r,
        x1,
        y1 - r,
        x1,
        y1,
        x1 - r,
        y1,
        x0 + r,
        y1,
        x0,
        y1,
        x0,
        y1 - r,
        x0,
        y0 + r,
        x0,
        y0,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=16, **kwargs)

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

        self.hide_builtins_var = tk.BooleanVar(value=False)
        self._last_nodes: Set[str] = set()
        self._last_edges: List[FlowEdge] = []
        self._last_assigned_to_by_callee: Dict[str, Set[str]] = {}
        self._tooltip_items: List[int] = []
        self._node_meta: Dict[str, Dict[str, List[str]]] = {}

        self.root.title("ProFlow")
        self.root.geometry("980x620")
        self.root.minsize(820, 520)
        self.root.configure(bg=BG)

        logo_image = Image.open("assets/ProFlow_Logo.png").convert("RGBA")
        logo_image = logo_image.resize((45, 45), Image.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(logo_image)

        # Top controls
        self.controls = tk.Frame(self.root, bg=PANEL_BG)
        self.controls.pack(side="top", fill="x")

        # Logo label (replaces "ProFlow" text)
        self.logo_label = tk.Label(
            self.controls,
            image=self.logo_photo,
            bg=PANEL_BG
        )
        self.logo_label.pack(side="left", padx=14, pady=10)

        self.open_btn = tk.Button(
            self.controls,
            text="Open Python File",
            command=self.open_file_dialog,
            bg=BG,
            fg=ORANGE,
            font=("Helvetica", 12, "bold"),
            activebackground=BG,
            activeforeground=ORANGE,
            relief="raised",
            width=15,
        )
        self.open_btn.pack(side="right", padx=14, pady=10)

        self.clear_btn = tk.Button(
            self.controls,
            text="Clear Diagram",
            command=self.clear_diagram,
            bg=BG,
            fg=ORANGE,
            font=("Helvetica", 12, "bold"),
            activebackground=BG,
            activeforeground=ORANGE,
            relief="raised",
            width=12,
        )
        self.clear_btn.pack(side="right", padx=(0, 5), pady=10)

        self.hide_builtins_btn = tk.Checkbutton(
            self.controls,
            text="Hide Built-Ins",
            variable=self.hide_builtins_var,
            command=self._redraw_last,
            bg=BG,
            fg=ORANGE,
            font=("Helvetica", 12, "bold"),
            activebackground=PANEL_BG,
            activeforeground=ORANGE,
            selectcolor=BG,
            relief="raised",
        )
        self.hide_builtins_btn.pack(side="right", padx=(0, 10), pady=10)

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

        hint_text = "Drag-and-drop is enabled :)" if dnd_available else "Drag-and-drop not available :( -> (pip install tkinterdnd2)."
        self.hint_label = tk.Label(self.root, text=hint_text, bg=BG, fg=ORANGE, font=("Helvetica", 9))
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
            fill=ORANGE,
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
        self._hide_tooltip()

        # Re-show watermark
        self.canvas.itemconfigure(self.watermark_id, state="normal")
        self.canvas.configure(scrollregion=(0, 0, 0, 0))
        self.status_var.set("Drop a .py file into the window, or click 'Open Python File...'.")

        self._last_nodes = set()
        self._last_edges = []
        self._last_assigned_to_by_callee = {}
        self._node_meta = {}

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Select a Python file",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return
        self._handle_file(path)

    def _build_node_meta(self, nodes: Set[str], edges: List[FlowEdge], assigned_to_by_callee: Dict[str, Set[str]]):
        called_with: Dict[str, Set[str]] = {}
        for _caller, callee, args in edges:
            if args:
                called_with.setdefault(callee, set()).add(args)

        meta: Dict[str, Dict[str, List[str]]] = {}
        for n in nodes:
            meta[n] = {
                "called_with": sorted(called_with.get(n, set())),
                "assigned_to": sorted(assigned_to_by_callee.get(n, set())),
            }
        self._node_meta = meta

    def _filter_graph(self, nodes: Set[str], edges: List[FlowEdge]) -> Tuple[Set[str], List[FlowEdge]]:
        if not self.hide_builtins_var.get():
            return nodes, edges

        filtered_nodes = set(n for n in nodes if (n == "Main Script" or n not in BUILTINS))
        filtered_edges = [
            (caller, callee, args)
            for (caller, callee, args) in edges
            if caller in filtered_nodes and callee in filtered_nodes
        ]
        return filtered_nodes, filtered_edges

    def _hide_tooltip(self):
        for item in self._tooltip_items:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        self._tooltip_items = []

    def _show_tooltip(self, node: str, event):
        self._hide_tooltip()

        info = self._node_meta.get(node, {})
        called_with = info.get("called_with", [])
        assigned_to = info.get("assigned_to", [])

        lines: List[str] = []
        label = "Start" if node == "Main Script" else node
        lines.append(f"{label}")

        if called_with:
            lines.append("")
            lines.append("Parameters:")
            for s in called_with[:10]:
                lines.append(f"  ({s})")
            if len(called_with) > 10:
                lines.append(f"  +{len(called_with) - 10} more")

        if assigned_to:
            lines.append("")
            lines.append("Variable Assignment:")
            for s in assigned_to[:12]:
                lines.append(f"  {s}")
            if len(assigned_to) > 12:
                lines.append(f"  +{len(assigned_to) - 12} more")

        if len(lines) == 1:
            lines.append("")
            lines.append("No metadata")

        text = "\n".join(lines)

        cx = int(self.canvas.canvasx(event.x))
        cy = int(self.canvas.canvasy(event.y))

        pad = 10
        text_id = self.canvas.create_text(
            cx + 20,
            cy + 20,
            text=text,
            fill=ORANGE,
            font=("Helvetica", 9),
            anchor="nw",
            tags=("flow", "tooltip"),
        )
        bbox = self.canvas.bbox(text_id)
        if not bbox:
            return
        x0, y0, x1, y1 = bbox
        rect_id = _create_rounded_rect(
            self.canvas,
            x0 - pad,
            y0 - pad,
            x1 + pad,
            y1 + pad,
            radius=10,
            fill=PANEL_BG,
            outline=ORANGE,
            width=2,
            tags=("flow", "tooltip"),
        )
        self.canvas.tag_raise(text_id, rect_id)
        self._tooltip_items = [rect_id, text_id]

    def _draw_flow(self, nodes: Set[str], edges: List[FlowEdge], assigned_to_by_callee: Dict[str, Set[str]]):
        self.canvas.delete("flow")
        self._hide_tooltip()
        self.canvas.itemconfigure(self.watermark_id, state="hidden")

        nodes, edges = self._filter_graph(nodes, edges)
        self._build_node_meta(nodes, edges, assigned_to_by_callee)

        pos = _compute_layout(nodes, edges)

        # Node size heuristic
        def node_size(label: str) -> Tuple[int, int]:
            w = max(140, min(360, 11 * len(label)))
            h = 64
            return w, h

        bounds_min_x = 10**9
        bounds_min_y = 10**9
        bounds_max_x = -10**9
        bounds_max_y = -10**9

        # Draw edges first so nodes appear on top.
        for caller, callee, _args in edges:
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

        # Draw nodes
        for node in nodes:
            x, y = pos.get(node, (0, 0))
            label = "Start" if node == "Main Script" else node
            w, h = node_size(label)
            x0 = x - w // 2
            y0 = y - h // 2
            x1 = x + w // 2
            y1 = y + h // 2

            tag = f"node:{node}"
            _create_rounded_rect(
                self.canvas,
                x0,
                y0,
                x1,
                y1,
                radius=16,
                fill=NODE_BG,
                outline=ORANGE,
                width=2,
                tags=("flow", "node", tag),
            )
            self.canvas.create_text(
                x,
                y,
                text=label,
                fill=ORANGE,
                font=("Helvetica", 12, "bold"),
                tags=("flow", "node", tag),
            )

            # Hover tooltips (unbind first to avoid accumulating bindings across redraws)
            self.canvas.tag_unbind(tag, "<Enter>")
            self.canvas.tag_unbind(tag, "<Leave>")
            self.canvas.tag_bind(tag, "<Enter>", lambda e, n=node: self._show_tooltip(n, e))
            self.canvas.tag_bind(tag, "<Leave>", lambda _e: self._hide_tooltip())

            bounds_min_x = min(bounds_min_x, x0)
            bounds_min_y = min(bounds_min_y, y0)
            bounds_max_x = max(bounds_max_x, x1)
            bounds_max_y = max(bounds_max_y, y1)

        if bounds_max_x < bounds_min_x:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            return

        pad = 140
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
        assigned_to_by_callee = data.get("assigned_to_by_callee", {})

        self._last_nodes = nodes  # type: ignore[assignment]
        self._last_edges = edges  # type: ignore[assignment]
        self._last_assigned_to_by_callee = assigned_to_by_callee  # type: ignore[assignment]

        self._draw_flow(nodes, edges, assigned_to_by_callee)  # type: ignore[arg-type]
        self.status_var.set("Diagram rendered. (Tip: hover nodes for details, click + drag to pan)")

    def _redraw_last(self):
        if not self._last_nodes:
            return
        self._draw_flow(self._last_nodes, self._last_edges, self._last_assigned_to_by_callee)

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
