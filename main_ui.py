import io
import os
import tempfile
import threading
import tkinter as tk
from functools import lru_cache
from tkinter import filedialog, messagebox, ttk

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "baby-plonk-mpl"))

import matplotlib.pyplot as plt
from PIL import Image, ImageTk

from compiler.program import Program


plt.rcParams["text.usetex"] = True
os.environ["PATH"] += ":/Library/TeX/texbin"


class PlonKApp:
    SAMPLE_CONSTRAINTS = "1 1 0 0 1\n0 0 1 1 1\n[1,0,0,-1,0]"

    def __init__(self, root):
        self.root = root
        self.root.title("Baby PlonK Studio")
        self.root.geometry("1280x860")
        self.root.minsize(1080, 760)
        self.root.configure(bg="#f4efe7")

        self.latex_refs = []
        self.is_running = False
        self.selector_columns = ("constraint", "q_L", "q_R", "q_M", "q_C", "q_O")

        self._build_styles()
        self._build_layout()
        self._bind_shortcuts()
        self._set_status("Ready. Enter constraints and generate selectors.")
        self._update_validation_state()

    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        palette = {
            "bg": "#f4efe7",
            "panel": "#fffaf2",
            "panel_alt": "#f8f2e8",
            "text": "#2b2118",
            "muted": "#6f6256",
            "accent": "#b85c38",
            "accent_dark": "#8f4324",
            "border": "#dfd1c4",
            "ok": "#2f7d4a",
            "warn": "#d97a20",
            "error": "#bf3c32",
        }
        self.colors = palette

        style.configure("App.TFrame", background=palette["bg"])
        style.configure("Panel.TFrame", background=palette["panel"], relief="flat")
        style.configure("AltPanel.TFrame", background=palette["panel_alt"], relief="flat")
        style.configure(
            "Title.TLabel",
            background=palette["bg"],
            foreground=palette["text"],
            font=("Avenir Next", 26, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=palette["bg"],
            foreground=palette["muted"],
            font=("Avenir Next", 11),
        )
        style.configure(
            "Section.TLabel",
            background=palette["panel"],
            foreground=palette["text"],
            font=("Avenir Next", 14, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=palette["panel"],
            foreground=palette["muted"],
            font=("Avenir Next", 11),
        )
        style.configure(
            "Hint.TLabel",
            background=palette["panel_alt"],
            foreground=palette["muted"],
            font=("Avenir Next", 10),
        )
        style.configure(
            "Metric.TLabel",
            background=palette["panel_alt"],
            foreground=palette["text"],
            font=("Avenir Next", 18, "bold"),
        )
        style.configure(
            "MetricCaption.TLabel",
            background=palette["panel_alt"],
            foreground=palette["muted"],
            font=("Avenir Next", 10),
        )
        style.configure(
            "Status.TLabel",
            background=palette["bg"],
            foreground=palette["muted"],
            font=("Avenir Next", 10),
        )
        style.configure(
            "TButton",
            background=palette["accent"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
            font=("Avenir Next", 11, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", palette["accent_dark"]), ("disabled", "#ccb9ae")],
            foreground=[("disabled", "#fff8f2")],
        )
        style.configure(
            "Secondary.TButton",
            background=palette["panel_alt"],
            foreground=palette["text"],
            borderwidth=1,
            relief="solid",
            padding=(12, 10),
            font=("Avenir Next", 10, "bold"),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#efe2d1"), ("disabled", "#ede0d7")],
            foreground=[("disabled", "#a89a8e")],
        )
        style.configure(
            "TEntry",
            fieldbackground="white",
            foreground=palette["text"],
            bordercolor=palette["border"],
            lightcolor=palette["border"],
            darkcolor=palette["border"],
            padding=8,
        )
        style.configure("TNotebook", background=palette["panel"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=palette["panel_alt"],
            foreground=palette["text"],
            padding=(14, 8),
            font=("Avenir Next", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", palette["panel"]), ("active", "#efe2d1")],
        )
        style.configure(
            "Treeview",
            background="#fffdf8",
            foreground=palette["text"],
            fieldbackground="#fffdf8",
            bordercolor=palette["border"],
            rowheight=30,
            font=("SF Mono", 11),
        )
        style.configure(
            "Treeview.Heading",
            background=palette["panel_alt"],
            foreground=palette["text"],
            font=("Avenir Next", 10, "bold"),
            relief="flat",
        )

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = ttk.Frame(self.root, style="App.TFrame", padding=24)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Baby PlonK Studio", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="A friendlier workspace for experimenting with constraints, selectors, and generated equations.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        splitter = ttk.Panedwindow(outer, orient="horizontal")
        splitter.grid(row=1, column=0, columnspan=2, sticky="nsew")

        left = ttk.Frame(splitter, style="Panel.TFrame", padding=20)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(4, weight=1)

        right = ttk.Frame(splitter, style="Panel.TFrame", padding=20)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)

        splitter.add(left, weight=5)
        splitter.add(right, weight=6)

        self._build_input_panel(left)
        self._build_result_panel(right)

        footer = ttk.Frame(outer, style="App.TFrame")
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        footer.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(footer, text="", style="Status.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")

    def _build_input_panel(self, parent):
        ttk.Label(parent, text="Input", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            parent,
            text="Use one row per constraint. Space-separated and list syntax are both supported.",
            style="Body.TLabel",
            wraplength=520,
        ).grid(row=1, column=0, sticky="w", pady=(6, 14))

        self.validation_var = tk.StringVar(value="Waiting for input")
        self.validation_label = ttk.Label(parent, textvariable=self.validation_var, style="Body.TLabel")
        self.validation_label.grid(row=2, column=0, sticky="w", pady=(0, 10))

        hint_panel = ttk.Frame(parent, style="AltPanel.TFrame", padding=12)
        hint_panel.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        hint_panel.columnconfigure(0, weight=1)
        ttk.Label(
            hint_panel,
            text="Quick format guide",
            style="MetricCaption.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            hint_panel,
            text="Space format: 1 1 0 0 1    List format: [1, 0, 0, -1, 0]",
            style="Hint.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(
            hint_panel,
            text="Shortcut: Ctrl/Cmd+Enter to generate",
            style="Hint.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        text_shell = tk.Frame(
            parent,
            bg=self.colors["border"],
            highlightthickness=0,
            bd=0,
            padx=1,
            pady=1,
        )
        text_shell.grid(row=4, column=0, sticky="nsew")
        text_shell.grid_rowconfigure(0, weight=1)
        text_shell.grid_columnconfigure(0, weight=1)

        self.constraints_text = tk.Text(
            text_shell,
            height=16,
            wrap="word",
            relief="flat",
            bg="white",
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            selectbackground="#e7c8b7",
            font=("SF Mono", 13),
            padx=14,
            pady=14,
        )
        self.constraints_text.grid(row=0, column=0, sticky="nsew")

        text_scroll = ttk.Scrollbar(text_shell, orient="vertical", command=self.constraints_text.yview)
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.constraints_text.configure(yscrollcommand=text_scroll.set)
        self.constraints_text.bind("<KeyRelease>", self._on_constraints_change)

        controls = ttk.Frame(parent, style="Panel.TFrame")
        controls.grid(row=5, column=0, sticky="ew", pady=(16, 16))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Group order", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.group_order_entry = ttk.Entry(controls, width=14)
        self.group_order_entry.grid(row=0, column=1, sticky="w")
        self.group_order_entry.bind("<KeyRelease>", self._on_constraints_change)
        ttk.Label(
            controls,
            text="Leave blank to use the number of constraints.",
            style="Body.TLabel",
        ).grid(row=0, column=2, sticky="w", padx=(12, 0))

        stats = ttk.Frame(parent, style="AltPanel.TFrame", padding=12)
        stats.grid(row=6, column=0, sticky="ew", pady=(0, 16))
        for index in range(3):
            stats.columnconfigure(index, weight=1)

        self.input_rows_var = tk.StringVar(value="0")
        self.input_width_var = tk.StringVar(value="0")
        self.suggested_order_var = tk.StringVar(value="0")
        self._metric_card(stats, 0, "Rows", self.input_rows_var)
        self._metric_card(stats, 1, "Width", self.input_width_var)
        self._metric_card(stats, 2, "Suggested Order", self.suggested_order_var)

        actions = ttk.Frame(parent, style="Panel.TFrame")
        actions.grid(row=7, column=0, sticky="new")
        actions.columnconfigure(3, weight=1)

        self.generate_button = ttk.Button(actions, text="Generate Selectors", command=self.run_program_async)
        self.generate_button.grid(row=0, column=0, sticky="w")

        ttk.Button(actions, text="Load Sample", style="Secondary.TButton", command=self.load_sample).grid(
            row=0, column=1, sticky="w", padx=(10, 0)
        )
        ttk.Button(actions, text="Clear", style="Secondary.TButton", command=self.clear_inputs).grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        ttk.Button(actions, text="Export Results", style="Secondary.TButton", command=self.export_results).grid(
            row=0, column=4, sticky="e"
        )
        ttk.Button(actions, text="Copy Results", style="Secondary.TButton", command=self.copy_results).grid(
            row=0, column=5, sticky="e", padx=(10, 0)
        )

    def _build_result_panel(self, parent):
        ttk.Label(parent, text="Results", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            parent,
            text="Selectors, summaries, and rendered equations appear here after generation.",
            style="Body.TLabel",
            wraplength=460,
        ).grid(row=1, column=0, sticky="w", pady=(6, 14))

        metrics = ttk.Frame(parent, style="AltPanel.TFrame", padding=14)
        metrics.grid(row=2, column=0, sticky="ew")
        for index in range(3):
            metrics.columnconfigure(index, weight=1)

        self.constraint_count_var = tk.StringVar(value="0")
        self.group_order_var = tk.StringVar(value="0")
        self.status_metric_var = tk.StringVar(value="Idle")

        self._metric_card(metrics, 0, "Constraints", self.constraint_count_var)
        self._metric_card(metrics, 1, "Group Order", self.group_order_var)
        self._metric_card(metrics, 2, "Run State", self.status_metric_var)

        notebook = ttk.Notebook(parent)
        notebook.grid(row=3, column=0, sticky="nsew", pady=(16, 0))
        parent.rowconfigure(3, weight=1)

        overview_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=10)
        details_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=10)
        notebook.add(overview_tab, text="Selector Table")
        notebook.add(details_tab, text="Detailed Output")

        overview_tab.columnconfigure(0, weight=1)
        overview_tab.rowconfigure(0, weight=1)
        details_tab.columnconfigure(0, weight=1)
        details_tab.rowconfigure(0, weight=1)

        table_shell = tk.Frame(
            overview_tab,
            bg=self.colors["border"],
            highlightthickness=0,
            bd=0,
            padx=1,
            pady=1,
        )
        table_shell.grid(row=0, column=0, sticky="nsew")
        table_shell.grid_rowconfigure(0, weight=1)
        table_shell.grid_columnconfigure(0, weight=1)

        self.selector_table = ttk.Treeview(
            table_shell,
            columns=self.selector_columns,
            show="headings",
        )
        headings = {
            "constraint": "#",
            "q_L": "q_L",
            "q_R": "q_R",
            "q_M": "q_M",
            "q_C": "q_C",
            "q_O": "q_O",
        }
        widths = {
            "constraint": 70,
            "q_L": 80,
            "q_R": 80,
            "q_M": 80,
            "q_C": 80,
            "q_O": 80,
        }
        for column in self.selector_columns:
            self.selector_table.heading(column, text=headings[column])
            self.selector_table.column(column, width=widths[column], anchor="center", stretch=column == "constraint")
        self.selector_table.grid(row=0, column=0, sticky="nsew")

        table_scroll = ttk.Scrollbar(table_shell, orient="vertical", command=self.selector_table.yview)
        table_scroll.grid(row=0, column=1, sticky="ns")
        self.selector_table.configure(yscrollcommand=table_scroll.set)

        result_shell = tk.Frame(
            details_tab,
            bg=self.colors["border"],
            highlightthickness=0,
            bd=0,
            padx=1,
            pady=1,
        )
        result_shell.grid(row=0, column=0, sticky="nsew")
        result_shell.grid_rowconfigure(0, weight=1)
        result_shell.grid_columnconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_shell,
            height=28,
            wrap="word",
            relief="flat",
            bg="#fffdf8",
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            selectbackground="#e7c8b7",
            font=("Avenir Next", 12),
            padx=16,
            pady=16,
            state="disabled",
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        result_scroll = ttk.Scrollbar(result_shell, orient="vertical", command=self.result_text.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=result_scroll.set)

    def _metric_card(self, parent, column, caption, variable):
        card = ttk.Frame(parent, style="AltPanel.TFrame", padding=10)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))
        card.columnconfigure(0, weight=1)
        ttk.Label(card, textvariable=variable, style="Metric.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, text=caption, style="MetricCaption.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _on_constraints_change(self, _event=None):
        self._update_validation_state()

    def _bind_shortcuts(self):
        self.root.bind_all("<Control-Return>", lambda _event: self.run_program_async())
        self.root.bind_all("<Command-Return>", lambda _event: self.run_program_async())
        self.root.bind_all("<Control-l>", lambda _event: self.load_sample())
        self.root.bind_all("<Command-l>", lambda _event: self.load_sample())

    def _update_validation_state(self):
        input_text = self.constraints_text.get("1.0", tk.END).strip()
        if not input_text:
            self._set_text_border(self.constraints_text, self.colors["border"])
            self.validation_var.set("Waiting for input")
            self.input_rows_var.set("0")
            self.input_width_var.set("0")
            self.suggested_order_var.set("0")
            return

        try:
            constraints = self.parse_constraints(input_text)
            width = len(constraints[0]) if constraints else 0
            if any(len(row) != width for row in constraints):
                raise ValueError("Every row must have the same number of values.")
            suggested_order = len(constraints)
            group_order_input = self.group_order_entry.get().strip()
            if group_order_input:
                suggested_order = max(suggested_order, int(group_order_input))
            self._set_text_border(self.constraints_text, "#c7d9cb")
            self.validation_var.set(f"Input looks valid: {len(constraints)} row(s), {width} value(s) each.")
            self.input_rows_var.set(str(len(constraints)))
            self.input_width_var.set(str(width))
            self.suggested_order_var.set(str(suggested_order))
        except ValueError as exc:
            self._set_text_border(self.constraints_text, "#d9a09c")
            self.validation_var.set(f"Input issue: {exc}")
            self.input_rows_var.set("!")
            self.input_width_var.set("!")
            self.suggested_order_var.set("!")

    def _set_text_border(self, widget, color):
        widget.master.configure(bg=color)

    def _set_status(self, message):
        self.status_label.config(text=message)

    def _set_running_state(self, running):
        self.is_running = running
        self.generate_button.config(state="disabled" if running else "normal")
        self.status_metric_var.set("Running" if running else "Idle")

    def _write_results(self, lines, latex_images):
        self.latex_refs = []
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        for line in lines:
            self.result_text.insert(tk.END, line)
        for image in latex_images:
            photo = ImageTk.PhotoImage(image)
            label = tk.Label(self.result_text, image=photo, bg="#fffdf8")
            label.image = photo
            self.latex_refs.append(photo)
            self.result_text.window_create(tk.END, window=label)
            self.result_text.insert(tk.END, "\n\n")
        self.result_text.see("1.0")
        self.result_text.config(state="disabled")

    def _populate_selector_table(self, rows):
        for item in self.selector_table.get_children():
            self.selector_table.delete(item)
        for row in rows:
            self.selector_table.insert("", "end", values=row)

    def run_program_async(self):
        if self.is_running:
            return
        payload = {
            "constraints_input": self.constraints_text.get("1.0", tk.END).strip(),
            "group_order_input": self.group_order_entry.get().strip(),
        }
        self._set_running_state(True)
        self._set_status("Generating selectors and rendering equations...")
        worker = threading.Thread(target=self.run_program, args=(payload,), daemon=True)
        worker.start()

    def run_program(self, payload):
        try:
            constraints_input = payload["constraints_input"]
            constraints = self.parse_constraints(constraints_input)
            if not constraints:
                raise ValueError("Please enter at least one constraint.")

            width = len(constraints[0])
            if any(len(row) != width for row in constraints):
                raise ValueError("Every constraint row must have the same length.")

            default_group_order = len(constraints)
            group_order_input = payload["group_order_input"]
            group_order = int(group_order_input) if group_order_input else default_group_order

            if group_order < len(constraints):
                raise ValueError(f"Group order must be >= {len(constraints)}.")

            program = Program(constraints, group_order)
            coeff_sets = program.coeffs()

            lines = [
                "Generation summary\n",
                "==================\n",
                f"Constraints: {len(program.constraints)}\n",
                f"Group order: {group_order}\n",
                f"Row width: {width}\n\n",
            ]
            latex_images = []
            selector_rows = []

            for index, coeffs in enumerate(coeff_sets, start=1):
                for key, value in coeffs.items():
                    if value not in {0, 1, -1}:
                        raise ValueError(
                        f"Invalid coefficient {value} for {key} in constraint {index}. Only 0, 1, -1 are allowed."
                        )

                selector_rows.append(
                    (
                        index,
                        coeffs["q_L"],
                        coeffs["q_R"],
                        coeffs["q_M"],
                        coeffs["q_C"],
                        coeffs["q_O"],
                    )
                )
                lines.extend(
                    [
                        f"Constraint {index}\n",
                        f"q_L: {coeffs['q_L']}\n",
                        f"q_R: {coeffs['q_R']}\n",
                        f"q_M: {coeffs['q_M']}\n",
                        f"q_C: {coeffs['q_C']}\n",
                        f"q_O: {coeffs['q_O']}\n",
                        "Equation:\n",
                    ]
                )

                latex_eq = (
                    f"$${coeffs['q_L']} \\cdot w_a + {coeffs['q_R']} \\cdot w_b + "
                    f"{coeffs['q_M']} \\cdot (w_a \\cdot w_b) + {coeffs['q_C']} - "
                    f"{coeffs['q_O']} \\cdot w_c \\overset{{?}}{{=}} 0$$"
                )
                latex_images.append(self.render_latex(latex_eq))
                lines.append("\n")

            self.root.after(
                0,
                    lambda: self._handle_success(
                        lines=lines,
                        latex_images=latex_images,
                        selector_rows=selector_rows,
                        constraint_count=len(program.constraints),
                        group_order=group_order,
                    ),
                )
        except Exception as exc:
            self.root.after(0, lambda: self._handle_error(str(exc)))

    def _handle_success(self, lines, latex_images, selector_rows, constraint_count, group_order):
        self.constraint_count_var.set(str(constraint_count))
        self.group_order_var.set(str(group_order))
        self._populate_selector_table(selector_rows)
        self._write_results(lines, latex_images)
        self._set_running_state(False)
        self.status_metric_var.set("Ready")
        self._set_status(f"Generated {constraint_count} constraint selector set(s).")

    def _handle_error(self, message):
        self._set_running_state(False)
        self.status_metric_var.set("Needs attention")
        self._set_status("Generation stopped because the input needs attention.")
        messagebox.showerror("Generation Error", message)

    def load_sample(self):
        self.constraints_text.delete("1.0", tk.END)
        self.constraints_text.insert("1.0", self.SAMPLE_CONSTRAINTS)
        self.group_order_entry.delete(0, tk.END)
        self._update_validation_state()
        self._set_status("Loaded a sample constraint set.")

    def clear_inputs(self):
        self.constraints_text.delete("1.0", tk.END)
        self.group_order_entry.delete(0, tk.END)
        self.constraint_count_var.set("0")
        self.group_order_var.set("0")
        self.status_metric_var.set("Idle")
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state="disabled")
        self._populate_selector_table([])
        self.latex_refs = []
        self._update_validation_state()
        self._set_status("Cleared the current input and results.")

    def export_results(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Nothing to export", "Generate results before exporting.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        self._set_status(f"Exported results to {file_path}.")

    def copy_results(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Nothing to copy", "Generate results before copying.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self._set_status("Copied current results to the clipboard.")

    @staticmethod
    def parse_constraints(input_text):
        constraints = []
        for line_number, row in enumerate(input_text.splitlines(), start=1):
            row = row.strip()
            if not row:
                continue

            if row.startswith("[") and row.endswith("]"):
                raw_values = [value.strip() for value in row[1:-1].split(",") if value.strip()]
            else:
                raw_values = row.split()

            if not raw_values:
                raise ValueError(f"Line {line_number} is empty.")

            try:
                constraints.append([int(value) for value in raw_values])
            except ValueError as exc:
                raise ValueError(f"Line {line_number} contains a non-integer value.") from exc
        return constraints

    @lru_cache(maxsize=128)
    def render_latex(self, latex_str):
        fig, ax = plt.subplots(figsize=(6.6, 1.1))
        ax.axis("off")
        plt.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"

        try:
            ax.text(0, 0.76, latex_str, fontsize=11, ha="left", va="top", usetex=True)
            return self._figure_to_image(fig)
        except Exception:
            plt.close(fig)
            fallback_fig, fallback_ax = plt.subplots(figsize=(6.6, 1.1))
            fallback_ax.axis("off")
            fallback_ax.text(
                0,
                0.72,
                latex_str.replace("$$", ""),
                fontsize=10,
                ha="left",
                va="top",
                wrap=True,
            )
            return self._figure_to_image(fallback_fig)

    @staticmethod
    def _figure_to_image(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.12, dpi=220)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)


if __name__ == "__main__":
    root = tk.Tk()
    app = PlonKApp(root)
    root.mainloop()
