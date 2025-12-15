import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

from main import generate_flow_diagram


def _is_python_file(path: str) -> bool:
    return isinstance(path, str) and path.lower().endswith(".py") and os.path.isfile(path)


def _open_file_in_explorer(path: str) -> None:
    # Windows: open file with default associated app
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception:
        # Fallback: open containing folder
        try:
            os.startfile(os.path.dirname(path))  # type: ignore[attr-defined]
        except Exception:
            pass


class ProFlowGUI:
    def __init__(self, root: tk.Tk, dnd_available: bool):
        self.root = root
        self.dnd_available = dnd_available
        self.selected_file: Optional[str] = None
        self.last_png: Optional[str] = None

        self.root.title("ProFlow")
        self.root.geometry("720x420")
        self.root.minsize(640, 360)

        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Watermark / instruction text (background)
        self.watermark_id = self.canvas.create_text(
            0,
            0,
            fill="#e6e6e6",
            font=("Helvetica", 44, "bold"),
            anchor="center",
        )

        # Foreground UI
        self.frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window_id = self.canvas.create_window(0, 0, window=self.frame, anchor="center")

        self.title_label = tk.Label(
            self.frame,
            text="ProFlow",
            bg="white",
            fg="#222222",
            font=("Helvetica", 18, "bold"),
        )
        self.title_label.pack(pady=(0, 6))

        self.status_var = tk.StringVar(value="Drop a .py file here or use the button below.")
        self.status_label = tk.Label(
            self.frame,
            textvariable=self.status_var,
            bg="white",
            fg="#333333",
            font=("Helvetica", 11),
            wraplength=560,
            justify="center",
        )
        self.status_label.pack(pady=(0, 14))

        self.open_btn = tk.Button(self.frame, text="Open Python File...", command=self.open_file_dialog, width=22)
        self.open_btn.pack(pady=(0, 10))

        self.open_diagram_btn = tk.Button(
            self.frame,
            text="Open Last Diagram",
            command=self.open_last_diagram,
            width=22,
            state="disabled",
        )
        self.open_diagram_btn.pack()

        self.hint_var = tk.StringVar(
            value=(
                "Drag-and-drop is enabled." if dnd_available else "Drag-and-drop not available (install tkinterdnd2)."
            )
        )
        self.hint_label = tk.Label(self.frame, textvariable=self.hint_var, bg="white", fg="#777777")
        self.hint_label.pack(pady=(14, 0))

        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, _event=None):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        self.canvas.coords(self.watermark_id, w // 2, h // 2)
        self.canvas.coords(self.canvas_window_id, w // 2, h // 2)

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Select a Python file",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return
        self._handle_file(path)

    def open_last_diagram(self):
        if self.last_png and os.path.exists(self.last_png):
            _open_file_in_explorer(self.last_png)
        else:
            messagebox.showwarning("ProFlow", "No diagram found to open yet.")

    def _handle_file(self, path: str):
        path = path.strip().strip("{}")
        if not _is_python_file(path):
            messagebox.showerror("ProFlow", "Please select a valid .py file.")
            return

        self.selected_file = path
        self.status_var.set(f"Generating diagram for: {path}")
        self.root.update_idletasks()

        # Keep output name consistent with the existing CLI behavior.
        png_path = generate_flow_diagram(path, output_name="flow_diagram", view=True)
        if not png_path:
            self.status_var.set("Failed to generate diagram. See terminal output for details.")
            return

        self.last_png = png_path
        self.open_diagram_btn.config(state="normal")
        self.status_var.set(f"Success! Diagram generated: {png_path}")


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
        # Register the canvas as the drop target so users can drop anywhere in the window.
        def _on_drop(event):
            # event.data may contain multiple files; take the first
            paths = root.tk.splitlist(event.data)
            if not paths:
                return
            app._handle_file(paths[0])

        app.canvas.drop_target_register(DND_FILES)
        app.canvas.dnd_bind("<<Drop>>", _on_drop)

    root.mainloop()


if __name__ == "__main__":
    run_app()
