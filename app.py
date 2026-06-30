from __future__ import annotations

import os
import math
import sys
from pathlib import Path


def _configure_tcl_paths() -> None:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    candidates = [
        base / "runtime_tcl",
        base / "tcl",
        Path(__file__).resolve().parent / "runtime_tcl",
    ]
    for candidate in candidates:
        if (candidate / "tcl8.6" / "init.tcl").exists() and (candidate / "tk8.6" / "tk.tcl").exists():
            os.environ.setdefault("TCL_LIBRARY", str(candidate / "tcl8.6"))
            os.environ.setdefault("TK_LIBRARY", str(candidate / "tk8.6"))
            return


_configure_tcl_paths()

import tkinter as tk
from tkinter import BOTH, END, LEFT, RIGHT, VERTICAL, X, Y, filedialog, messagebox, ttk

from anchor_calculator import (
    AUTO_FACTOR_KEYS,
    DEFAULT_VALUES,
    INPUT_SPECS,
    SHEAR_CASE_LABELS,
    AnchorInputs,
    AnchorResults,
    CalculationError,
    calculate_anchor,
    inputs_from_mapping,
)
from report_writer import write_calculation_report


APP_TITLE = "光伏跟踪支架地脚螺栓计算程序"
APP_VERSION = "1.0.0"
APP_ICON = Path("assets") / "anchor_plate.ico"
BG = "#F4F7FA"
PANEL = "#FFFFFF"
TEXT = "#111827"
MUTED = "#64748B"
ACCENT = "#1F4E79"
OK = "#15803D"
WARN = "#B45309"
NG = "#B91C1C"


FACTOR_SOURCES = {
    "phi_tension_steel": "ACI 318-19 Table 17.5.3；φ 作用于 Nsa，设计强度为 φ·Nsa。",
    "psi_ec_n": "ACI 318-19 17.6.2.3；抗拉混凝土锥体破坏偏心修正。",
    "psi_c_n": "ACI 318-19 17.6.2.5；抗拉混凝土锥体破坏开裂修正。",
    "psi_cp_n": "ACI 318-19 17.6.2.6；抗拉劈裂修正。",
    "phi_tension_concrete": "ACI 318-19 Table 17.5.3；φ 作用于 Ncbg，设计强度为 φ·Ncbg。",
    "psi_c_p": "ACI 318-19 17.6.3.2；拔出强度开裂修正。",
    "phi_pullout": "ACI 318-19 Table 17.5.3；φ 作用于 Npn，设计强度为 φ·Npn。",
    "phi_shear_steel": "ACI 318-19 Table 17.5.3；φ 作用于 Vsa，设计强度为 φ·Vsa。",
    "psi_ec_v": "ACI 318-19 17.7.2.3；抗剪混凝土边缘破坏偏心修正。",
    "psi_c_v": "ACI 318-19 17.7.2.5；抗剪混凝土边缘破坏开裂修正。",
    "psi_h_v": "ACI 318-19 17.7.2.6；构件厚度修正，程序按当前 ha 与 ca1 自动计算。",
    "phi_shear_concrete": "ACI 318-19 Table 17.5.3；φ 作用于 Vcbg，设计强度为 φ·Vcbg。",
    "kcp": "ACI 318-19 17.7.3.1；混凝土撬出系数，程序按 hef 自动计算。",
    "phi_pryout": "ACI 318-19 Table 17.5.3；φ 作用于 Vcpg，设计强度为 φ·Vcpg。",
}


TOOLTIP_PURPOSES = {
    "plate_l": "底板沿弯矩方向的长度。",
    "plate_b": "底板垂直于弯矩方向的宽度。",
    "da": "锚栓公称直径；ACI 17.3.2 的混凝土破坏计算适用范围为 da <= 4 in.。",
    "ase": "锚栓有效钢材截面积，用于抗拉和抗剪钢材强度。",
    "hef": "从混凝土表面至锚固有效端的有效埋深。",
    "s1": "沿弯矩方向两排锚栓的中心间距。",
    "s2": "垂直于弯矩方向两列锚栓的中心间距。",
    "pedestal_l": "基础墩沿弯矩方向的平面尺寸。",
    "pedestal_b": "基础墩垂直于弯矩方向的平面尺寸。",
    "ha": "基础墩高度或混凝土构件厚度。",
    "eh": "J- or L-bolt 弯钩内侧至外端的距离，用于拔出强度公式。",
    "built_up_grout_pad": "是否采用 built-up grout pad；有灌浆垫层时，ACI 17.7.1.2.1 要对 Vsa 乘以 0.80。",
    "futa": "锚栓钢材规定抗拉强度；ACI 17.6.1.2/17.7.1.2 要求用于计算的 futa 不超过 1.9fya 或 125 ksi。程序会校核 125 ksi 上限；由于不单独输入 fya，仍需用户确认 futa <= 1.9fya。",
    "lambda_a": "混凝土轻骨料修正系数。",
    "fc_prime": "ACI 318 锚栓计算采用的 specified compressive strength, f'c，属于美标混凝土强度定义；用于混凝土锥体破坏、拔出、抗剪边缘破坏等 ACI 公式。ACI 17.3.1 对 cast-in anchors 的计算值限制为 f'c <= 10000 psi。",
    "fc_design": "按项目需要直接输入的底板局部承压设计值；本程序用于 sigma_max <= fc 的简化复核，可按中国规范或项目要求确定。",
    "ec_modulus": "混凝土弹性模量，输入值单位为 10^4 N/mm2；用于《钢结构节点设计手册》（第四版）表 8-3 中的弹性模量比 n = Es/Ec。",
    "es_modulus": "钢材弹性模量，输入值单位为 10^5 N/mm2；用于《钢结构节点设计手册》（第四版）表 8-3 中的弹性模量比 n = Es/Ec。",
    "fy_tension_rebar": "用于简化估算抗拉锚固配筋面积的设计强度；程序按 As,N = Nua,g / fy,N 计算，不再额外乘 φ。该值可按中国规范或项目要求确定。",
    "fy_shear_rebar": "用于简化估算抗剪锚固配筋面积的设计强度；程序按 As,V = Vua,g / fy,V 计算，不再额外乘 φ。该值可按中国规范或项目要求确定。",
    "tension_rebar_factor": "用于把程序计算的抗拉所需配筋面积换算为实配参与面积：As,N,prov = k_As,N × As,N,req。",
    "shear_rebar_factor": "用于把程序计算的抗剪所需配筋面积换算为实配参与面积：As,V,prov = k_As,V × As,V,req。",
    "n": "轴力设计值；正值表示对底板向下的压力。",
    "m": "弯矩设计值；正方向见图示中的 M。",
    "v": "剪力设计值；正方向见图示中的 V。",
    "mu": "底板与混凝土界面的摩擦系数，用于 Vfb = μ(Ta + N)。",
    "phi_tension_steel": "钢材抗拉强度折减系数。",
    "psi_ec_n": "抗拉混凝土锥体破坏偏心修正系数。",
    "psi_c_n": "抗拉混凝土锥体破坏开裂修正系数。",
    "psi_cp_n": "抗拉劈裂修正系数。",
    "phi_tension_concrete": "混凝土抗拉锥体破坏强度折减系数。",
    "psi_c_p": "拔出强度开裂修正系数。",
    "phi_pullout": "拔出强度折减系数。",
    "phi_shear_steel": "钢材抗剪强度折减系数。",
    "psi_ec_v": "抗剪混凝土边缘破坏偏心修正系数。",
    "psi_c_v": "抗剪混凝土边缘破坏开裂修正系数。",
    "psi_h_v": "抗剪混凝土边缘破坏厚度修正系数。",
    "phi_shear_concrete": "混凝土抗剪边缘破坏强度折减系数。",
    "kcp": "混凝土撬出强度系数。",
    "phi_pryout": "混凝土撬出强度折减系数。",
}


RESULT_GROUPS = (
    ("demand", "需求与混凝土局部承压 / Demand and Local Bearing", "混凝土局部承压及单根锚栓设计需求。Nua 为单根锚栓抗拉需求，Vua 为扣除界面摩擦后的单根锚栓抗剪需求。"),
    ("geometry", "构造与几何要求 / Geometry Requirements", "锚栓间距等构造和几何限制。eh 为拔出公式适用条件，已在输入框提示中说明。"),
    ("tension", "抗拉验算 / Tension Checks", "钢材抗拉、混凝土抗拉锥体破坏、拔出破坏等抗拉承载力验算。"),
    ("shear", "抗剪验算 / Shear Checks", "先判断界面摩擦是否已经足够抵抗剪力；只有扣除摩擦后 Vua > 0 时才进行锚栓抗剪承载力验算。"),
    ("interaction", "拉剪相互作用 / Tension-Shear Interaction", "仅当同一锚栓或同一锚栓组同时承受拉力和扣除界面摩擦后的锚栓剪力时，才按 ACI 318-19 17.8 验算；若不需锚栓抗剪，或 Case 1 中抗拉与抗剪由不同侧锚栓承担，则本项不适用。"),
)


CHECK_DISPLAY_NAMES = {
    "Minimum spacing s1": "最小锚栓间距 s1 / Minimum spacing s1",
    "Minimum spacing s2": "最小锚栓间距 s2 / Minimum spacing s2",
    "Minimum member thickness ha": "最小构件厚度 ha / Minimum member thickness ha",
    "Concrete local bearing": "混凝土局部承压 / Concrete local bearing",
    "Steel strength in tension": "钢材抗拉强度 / Steel strength in tension",
    "Concrete breakout strength in tension": "混凝土抗拉锥体破坏 / Concrete breakout strength in tension",
    "Pullout strength in tension": "抗拉拔出强度 / Pullout strength in tension",
    "Anchor shear demand after friction": "是否需要锚栓抗剪 / Anchor shear demand after friction",
    "Steel strength in shear": "钢材抗剪强度 / Steel strength in shear",
    "Concrete breakout strength in shear": "混凝土抗剪边缘破坏 / Concrete breakout strength in shear",
    "Concrete pryout strength in shear": "混凝土撬出破坏 / Concrete pryout strength in shear",
    "Tension-shear interaction": "拉剪相互作用 / Tension and shear interaction",
}


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None) -> None:
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 24
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=self.text,
            justify="left",
            bg="#111827",
            fg="#FFFFFF",
            padx=10,
            pady=7,
            wraplength=380,
            font=("Microsoft YaHei UI", 9),
        )
        label.pack()

    def hide(self, _event=None) -> None:
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=PANEL)
        self.content = ttk.Frame(canvas, style="Panel.TFrame")
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        window = canvas.create_window((0, 0), window=self.content, anchor="nw")

        def _configure_content(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _configure_canvas(event) -> None:
            canvas.itemconfigure(window, width=event.width)

        self.content.bind("<Configure>", _configure_content)
        canvas.bind("<Configure>", _configure_canvas)

        def _wheel(event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(_event=None) -> None:
            canvas.bind_all("<MouseWheel>", _wheel)

        def _unbind_wheel(_event=None) -> None:
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)
        self.content.bind("<Enter>", _bind_wheel)
        self.content.bind("<Leave>", _unbind_wheel)


class AnchorBoltApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self._apply_window_icon()
        self.geometry("1280x820")
        self.minsize(1120, 720)
        self.configure(bg=BG)
        self.vars: dict[str, tk.StringVar] = {}
        self.project_var = tk.StringVar(value="Photovoltaic Tracker Support")
        self.prepared_by_var = tk.StringVar(value="Engineer")
        self.shear_case_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="请先计算。")
        self.detail_var = tk.StringVar(value="选择结果表中的项目可查看公式与代入。")
        self.demand_var = tk.StringVar(value="")
        self.check_lookup: dict[str, object] = {}
        self.last_results: AnchorResults | None = None
        self._auto_update_job: str | None = None

        self._configure_style()
        self._build_layout()
        self._load_defaults()
        self.calculate()

    def _apply_window_icon(self) -> None:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        icon_path = base / APP_ICON
        if not icon_path.exists():
            return
        try:
            self.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

    def _configure_style(self) -> None:
        self.option_add("*Font", ("Microsoft YaHei UI", 9))
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 9))
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Section.TLabel", background=PANEL, foreground=ACCENT, font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Status.TLabel", background=PANEL, foreground=TEXT, font=("Microsoft YaHei UI", 13, "bold"))
        style.configure("TButton", padding=(12, 7), borderwidth=1)
        style.configure("Accent.TButton", padding=(14, 8), background=ACCENT, foreground="#FFFFFF", bordercolor=ACCENT)
        style.map("Accent.TButton", background=[("active", "#173B5C")], foreground=[("disabled", "#E5E7EB")])
        style.configure("TEntry", padding=(8, 4), fieldbackground="#FFFFFF")
        style.configure("TCombobox", padding=(8, 4), fieldbackground="#FFFFFF")
        style.configure("Treeview", rowheight=28, fieldbackground="#FFFFFF", background="#FFFFFF")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"), background="#E2E8F0", foreground=TEXT)
        style.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", TEXT)])

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill=BOTH, expand=True)

        title_row = ttk.Frame(root)
        title_row.pack(fill=X, pady=(0, 12))
        title = ttk.Label(title_row, text=f"{APP_TITLE} v{APP_VERSION}", font=("Microsoft YaHei UI", 16, "bold"), foreground=ACCENT)
        title.pack(side=LEFT)
        subtitle = ttk.Label(title_row, text="ACI 318-19 Chapter 17 | 独立计算 | Word 计算书", style="Muted.TLabel")
        subtitle.pack(side=LEFT, padx=(18, 0))

        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=BOTH, expand=True)

        left = ttk.Frame(paned, style="Panel.TFrame", width=420)
        right = ttk.Frame(paned, style="Panel.TFrame")
        paned.add(left, weight=0)
        paned.add(right, weight=1)

        self._build_input_panel(left)
        self._build_output_panel(right)

    def _build_input_panel(self, parent: ttk.Frame) -> None:
        wrapper = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        wrapper.pack(fill=BOTH, expand=True)

        input_tabs = ttk.Notebook(wrapper)
        input_tabs.pack(fill=BOTH, expand=True)

        project_tab = ttk.Frame(input_tabs, style="Panel.TFrame", padding=10)
        input_tabs.add(project_tab, text="项目")
        ttk.Label(project_tab, text="项目信息", style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        self._entry_row(project_tab, "项目名称", self.project_var, "用于英文 Word calculation report 封面。")
        self._entry_row(project_tab, "编制人", self.prepared_by_var, "用于英文 Word calculation report 封面。")

        for group, label in (
            ("Geometry", "几何"),
            ("Materials", "材料"),
            ("Loads", "荷载"),
            ("Factors", "规范系数"),
        ):
            tab = ttk.Frame(input_tabs, style="Panel.TFrame", padding=8)
            input_tabs.add(tab, text=label)
            scroll = ScrollableFrame(tab)
            scroll.pack(fill=BOTH, expand=True)
            content = scroll.content
            ttk.Label(content, text=f"{label}参数" if group != "Factors" else label, style="Section.TLabel").pack(anchor="w", pady=(0, 8))
            if group == "Factors":
                ttk.Separator(content, orient="horizontal").pack(fill=X, pady=(0, 10))
                ttk.Label(content, text="用户输入系数", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
                for spec in INPUT_SPECS:
                    if spec.group != group or spec.key in AUTO_FACTOR_KEYS:
                        continue
                    var = tk.StringVar()
                    self.vars[spec.key] = var
                    self._entry_row(content, self._format_input_label(spec), var, self._format_tooltip(spec))
                ttk.Separator(content, orient="horizontal").pack(fill=X, pady=(12, 10))
                ttk.Label(content, text="自动计算系数", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
                for spec in INPUT_SPECS:
                    if spec.group != group or spec.key not in AUTO_FACTOR_KEYS:
                        continue
                    var = tk.StringVar()
                    self.vars[spec.key] = var
                    self._readonly_entry_row(content, self._format_input_label(spec), var, self._format_tooltip(spec))
            else:
                for spec in INPUT_SPECS:
                    if spec.group != group:
                        continue
                    var = tk.StringVar()
                    self.vars[spec.key] = var
                    if spec.key == "built_up_grout_pad":
                        self._yes_no_row(content, spec, var)
                    elif spec.key in AUTO_FACTOR_KEYS:
                        self._readonly_entry_row(content, self._format_input_label(spec), var, self._format_tooltip(spec))
                    else:
                        self._entry_row(
                            content,
                            self._format_input_label(spec),
                            var,
                            self._format_tooltip(spec),
                        )
            if group == "Loads":
                self._case_row(content)

        button_bar = ttk.Frame(wrapper, style="Panel.TFrame")
        button_bar.pack(fill=X, pady=(12, 0))
        ttk.Button(button_bar, text="计算", style="Accent.TButton", command=self.calculate).pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        ttk.Button(button_bar, text="恢复样例", command=self.reset_defaults).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(wrapper, text="导出英文计算书 (Word)", command=self.export_word).pack(fill=X, pady=(10, 0))

    def _entry_row(self, parent: ttk.Frame, label: str, var: tk.StringVar, tip: str) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill=X, pady=3)
        lbl = ttk.Label(row, text=label, style="Panel.TLabel", width=31)
        lbl.pack(side=LEFT)
        entry = ttk.Entry(row, textvariable=var, width=11)
        entry.pack(side=RIGHT)
        entry.bind("<FocusOut>", lambda _event: self._schedule_auto_update())
        entry.bind("<Return>", lambda _event: self.calculate(silent=True))
        ToolTip(lbl, tip)
        ToolTip(entry, tip)

    def _readonly_entry_row(self, parent: ttk.Frame, label: str, var: tk.StringVar, tip: str) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill=X, pady=3)
        lbl = ttk.Label(row, text=label, style="Panel.TLabel", width=31)
        lbl.pack(side=LEFT)
        entry = ttk.Entry(row, textvariable=var, width=11, state="readonly")
        entry.pack(side=RIGHT)
        ToolTip(lbl, tip)
        ToolTip(entry, tip)

    def _yes_no_row(self, parent: ttk.Frame, spec, var: tk.StringVar) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill=X, pady=3)
        lbl = ttk.Label(row, text=self._format_input_label(spec), style="Panel.TLabel", width=31)
        lbl.pack(side=LEFT)
        combo = ttk.Combobox(row, textvariable=var, state="readonly", values=("有 / Yes", "无 / No"), width=9)
        combo.pack(side=RIGHT)
        tip = self._format_tooltip(spec)
        ToolTip(lbl, tip)
        ToolTip(combo, tip)
        combo.bind("<<ComboboxSelected>>", lambda _event: self.calculate(silent=True))

    def _case_row(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill=X, pady=3)
        lbl = ttk.Label(row, text="剪力控制工况 Case", style="Panel.TLabel", width=31)
        lbl.pack(side=LEFT)
        combo = ttk.Combobox(row, textvariable=self.shear_case_var, state="readonly", values=("1", "2"), width=9)
        combo.pack(side=RIGHT)
        case_tip = (
            "Case 1：靠近受剪边的两根锚栓通过圆孔承压承担 Vua，受剪边距采用 ca1。\n"
            "Case 2：远离受剪边的两根锚栓承担 Vua，受剪边距采用 ca1 + s1；近边两颗需要设置顺剪力方向的长圆孔释放剪力。"
        )
        ToolTip(lbl, case_tip)
        ToolTip(combo, case_tip)
        combo.bind("<<ComboboxSelected>>", lambda _event: self.calculate(silent=True))
        note = ttk.Label(
            parent,
            text="Case 1：近边两颗圆孔承压。\nCase 2：远边两颗承压，近边两颗需长圆孔释放剪力。",
            style="Panel.TLabel",
            foreground=MUTED,
            wraplength=360,
            justify="left",
        )
        note.pack(fill=X, pady=(0, 6))

    def _build_output_panel(self, parent: ttk.Frame) -> None:
        wrapper = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        wrapper.pack(fill=BOTH, expand=True)

        top = ttk.Frame(wrapper, style="Panel.TFrame")
        top.pack(fill=X)
        self.status_label = ttk.Label(top, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side=LEFT)

        notebook = ttk.Notebook(wrapper)
        notebook.pack(fill=BOTH, expand=True, pady=(12, 0))
        result_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=8)
        diagram_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=8)
        notebook.add(diagram_tab, text="图示")
        notebook.add(result_tab, text="结果")

        columns = ("ratio", "status")
        result_paned = tk.PanedWindow(
            result_tab,
            orient=tk.VERTICAL,
            sashrelief=tk.RAISED,
            sashwidth=7,
            bg="#CBD5E1",
            bd=0,
            showhandle=True,
        )
        result_paned.pack(fill=BOTH, expand=True)

        force_frame = ttk.Frame(result_paned, style="Panel.TFrame", padding=(8, 6))
        result_table_frame = ttk.Frame(result_paned, style="Panel.TFrame")
        result_detail_frame = ttk.Frame(result_paned, style="Panel.TFrame")
        result_paned.add(force_frame, minsize=128)
        result_paned.add(result_table_frame, minsize=180)
        result_paned.add(result_detail_frame, minsize=150)

        ttk.Label(force_frame, text="内力计算结果 / Force Result", style="Panel.TLabel", font=("Microsoft YaHei UI", 10, "bold")).pack(fill=X)
        force_table_frame = ttk.Frame(force_frame, style="Panel.TFrame")
        force_table_frame.pack(fill=BOTH, expand=True, pady=(6, 0))
        self.force_tree = ttk.Treeview(force_table_frame, columns=("item", "value"), show="headings", height=5)
        self.force_tree.heading("item", text="计算项目")
        self.force_tree.heading("value", text="计算结果")
        self.force_tree.column("item", width=360, anchor="w")
        self.force_tree.column("value", width=520, anchor="w")
        force_scroll = ttk.Scrollbar(force_table_frame, orient=VERTICAL, command=self.force_tree.yview)
        self.force_tree.configure(yscrollcommand=force_scroll.set)
        self.force_tree.pack(side=LEFT, fill=BOTH, expand=True)
        force_scroll.pack(side=RIGHT, fill=Y)
        self.force_tree.bind("<MouseWheel>", self._scroll_force_tree)

        ttk.Label(result_table_frame, text="验算结论 / Check Summary", style="Panel.TLabel", font=("Microsoft YaHei UI", 10, "bold")).pack(fill=X, pady=(0, 6))
        self.tree = ttk.Treeview(result_table_frame, columns=columns, show="tree headings", height=12)
        self.tree.heading("#0", text="类别 / 验算项目")
        self.tree.heading("ratio", text="校核值/需求")
        self.tree.heading("status", text="结论")
        self.tree.column("#0", width=540, anchor="w")
        self.tree.column("ratio", width=120, anchor="center")
        self.tree.column("status", width=240, anchor="center")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.tag_configure("ok", foreground=OK)
        self.tree.tag_configure("warn", foreground=WARN)
        self.tree.tag_configure("ng", foreground=NG)
        self.tree.tag_configure("na", foreground=MUTED)
        self.tree.tag_configure("info", foreground=ACCENT)
        self.tree.bind("<<TreeviewSelect>>", self._show_selected_detail)

        ttk.Label(result_detail_frame, text="验算详情 / Check Detail", style="Panel.TLabel", font=("Microsoft YaHei UI", 10, "bold")).pack(fill=X)
        detail = ttk.Label(result_detail_frame, textvariable=self.detail_var, style="Panel.TLabel", wraplength=720, justify="left")
        detail.pack(fill=X, pady=(6, 0))
        self.detail_canvas = tk.Canvas(result_detail_frame, height=190, bg="#F8FAFC", highlightthickness=1, highlightbackground="#CBD5E1")
        self.detail_canvas.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.detail_canvas.bind("<Configure>", self._redraw_detail_canvas)

        self.canvas = tk.Canvas(diagram_tab, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1")
        self.canvas.pack(fill=BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.draw_diagram())

    def _load_defaults(self) -> None:
        for key, value in DEFAULT_VALUES.items():
            if key == "shear_case":
                self.shear_case_var.set(str(int(value)))
            elif key in self.vars:
                if key == "built_up_grout_pad":
                    self.vars[key].set("有 / Yes" if value >= 0.5 else "无 / No")
                    continue
                spec = next((s for s in INPUT_SPECS if s.key == key), None)
                decimals = spec.decimals if spec else 3
                self.vars[key].set(_fmt(value, decimals))

    def reset_defaults(self) -> None:
        self._load_defaults()
        self.calculate()

    def _format_input_label(self, spec) -> str:
        if spec.unit == "-":
            return f"{spec.label_cn}  {spec.symbol}"
        return f"{spec.label_cn}  {spec.symbol} ({spec.unit})"

    def _format_tooltip(self, spec) -> str:
        purpose = TOOLTIP_PURPOSES.get(spec.key, spec.tooltip)
        if spec.group == "Factors" or spec.key in {"fc_prime", "fc_design"}:
            lines = [
                spec.tooltip,
                f"用途：{purpose}",
            ]
        else:
            lines = [
                f"用途：{purpose}",
            ]
        if spec.key == "eh":
            lines.append("适用条件：ACI 318-19 17.6.3.2.2(b) 的 J- or L-bolt 拔出公式要求 3da ≤ eh ≤ 4.5da。")
        if spec.key in AUTO_FACTOR_KEYS:
            lines.append("自动计算：程序按当前输入自动确定，计算后回填显示。")
        if spec.group == "Factors" and spec.key not in AUTO_FACTOR_KEYS:
            lines.append(f"默认值：{_fmt(spec.default, spec.decimals)}")
            source = FACTOR_SOURCES.get(spec.key)
            if source:
                lines.append(f"规范来源：{source}")
        elif spec.group == "Factors":
            source = FACTOR_SOURCES.get(spec.key)
            if source:
                lines.append(f"规范来源：{source}")
        return "\n".join(lines)

    def _schedule_auto_update(self) -> None:
        if self._auto_update_job:
            self.after_cancel(self._auto_update_job)
        self._auto_update_job = self.after(250, lambda: self.calculate(silent=True))

    def _collect_inputs(self) -> AnchorInputs:
        data = {key: var.get() for key, var in self.vars.items()}
        if data.get("built_up_grout_pad") == "有 / Yes":
            data["built_up_grout_pad"] = "1"
        elif data.get("built_up_grout_pad") == "无 / No":
            data["built_up_grout_pad"] = "0"
        data["shear_case"] = self.shear_case_var.get()
        return inputs_from_mapping(data)

    def calculate(self, silent: bool = False) -> None:
        self._auto_update_job = None
        try:
            inputs = self._collect_inputs()
            results = calculate_anchor(inputs)
        except CalculationError as exc:
            if silent:
                self.status_label.configure(foreground=NG)
                self.status_var.set(f"输入待修正: {exc}")
            else:
                messagebox.showerror("计算失败", str(exc))
            return
        except Exception as exc:
            if silent:
                self.status_label.configure(foreground=NG)
                self.status_var.set(f"输入待修正: {exc}")
            else:
                messagebox.showerror("计算失败", f"未知错误: {exc}")
            return
        self.last_results = results
        self._refresh_results()
        self.draw_diagram()

    def _refresh_results(self) -> None:
        assert self.last_results is not None
        results = self.last_results
        self._sync_auto_inputs(results)
        color = {"OK": OK, "Rebar Required": WARN, "NG": NG}.get(results.overall_status, TEXT)
        self.status_label.configure(foreground=color)
        self.status_var.set(f"总体验算结论: {results.overall_status}")

        self._refresh_force_table(results)

        self.tree.delete(*self.tree.get_children())
        self.check_lookup = {}
        checks = results.checks + [results.interaction_5_3]
        groups = {
            "demand": ["Concrete local bearing"],
            "geometry": ["Minimum spacing s1", "Minimum spacing s2", "Minimum member thickness ha"],
            "tension": [
                "Steel strength in tension",
                "Concrete breakout strength in tension",
                "Pullout strength in tension",
            ],
            "shear": [
                "Anchor shear demand after friction",
                "Steel strength in shear",
                "Concrete breakout strength in shear",
                "Concrete pryout strength in shear",
            ],
            "interaction": ["Tension-shear interaction"],
        }
        for group_key, group_title, group_detail in RESULT_GROUPS:
            child_names = groups[group_key]
            child_checks = [check for name in child_names for check in checks if check.name == name]
            group_status = self._aggregate_status(child_checks)
            group_tag = self._status_tag(group_status)
            group_iid = f"group:{group_key}"
            if group_key in {"tension", "shear", "interaction"}:
                self.tree.insert("", END, iid=group_iid, text=group_title, values=("", ""), open=True)
            else:
                self.tree.insert("", END, iid=group_iid, text=group_title, values=("", self._display_status(group_status)), tags=(group_tag,), open=True)
            self.check_lookup[group_iid] = group_detail
            for check_index, check in enumerate(child_checks):
                ratio = self._display_ratio(check)
                tag = self._status_tag(check.status)
                iid = f"check:{group_key}:{check_index}"
                self.tree.insert(group_iid, END, iid=iid, text=self._display_check_name(check.name), values=(ratio, self._display_status(check.status, check)), tags=(tag,))
                self.check_lookup[iid] = check
        self.detail_var.set(
            "结果已按需求与混凝土局部承压、构造与几何要求、抗拉验算、抗剪验算和拉剪相互作用分组；抗剪项会先说明是否需要锚栓承担剪力。"
        )
        self._draw_detail_diagram(None)

    def _refresh_force_table(self, results: AnchorResults) -> None:
        self.force_tree.delete(*self.force_tree.get_children())
        rows = (
            ("柱脚受力工况 / Force case", f"{results.values['force_case']} - {results.values['force_case_label']}"),
            ("偏心距 / Eccentricity e", f"{results.values['eccentricity']:.1f} mm"),
            ("受拉侧锚栓至底板边距离 / l1", f"{results.values['l1']:.1f} mm"),
            ("弹性模量比 / Modular ratio n = Es/Ec", f"{results.values['modular_ratio']:.3f}"),
            ("混凝土受压高度 / Compression depth x", f"{results.values['compression_x']:.1f} mm"),
            ("受拉侧锚栓总拉力 / Total tension Ta", f"{results.values['total_anchor_tension']:.3f} kN"),
            ("界面摩擦力 / Interface friction Vfb", f"{results.values['friction_force']:.3f} kN"),
            ("单根锚栓抗拉需求 / Single anchor Nua", f"{results.values['nua']:.3f} kN"),
            ("受拉锚栓组总拉力 / Anchor group Nua,g", f"{results.values['nuag']:.3f} kN"),
            ("单根锚栓抗剪需求 / Single anchor Vua", f"{results.values['vua']:.3f} kN"),
            ("承剪锚栓组总剪力 / Anchor group Vua,g", f"{results.values['vuag']:.3f} kN"),
        )
        for row in rows:
            self.force_tree.insert("", END, values=row)

    def _scroll_force_tree(self, event) -> str:
        self.force_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _show_selected_detail(self, _event=None) -> None:
        if not self.last_results:
            return
        selected = self.tree.selection()
        if not selected:
            return
        item = self.check_lookup.get(selected[0])
        if isinstance(item, str):
            self.detail_var.set(item)
            self._draw_detail_diagram(None)
            return
        check = item
        if check is None:
            return
        detail = f"{self._display_check_name(check.name)}\n{check.section}\n公式: {check.formula}\n代入: {check.substitution}"
        if check.note:
            detail += f"\n说明: {check.note}"
        if check.status == "Rebar Required" and check.ratio is not None:
            detail += f"\n未配置锚固钢筋时的混凝土破坏比值: {check.ratio:.3f}"
            if check.name == "Concrete breakout strength in tension":
                factor = self.last_results.inputs.tension_rebar_factor
                provided = self.last_results.values["tension_rebar_provided_area"]
                detail += f"\n实配抗拉锚固钢筋: As,N,prov = {self.last_results.tension_rebar_area:.2f} x {factor:.2f} = {provided:.2f} mm2"
            elif check.name == "Concrete breakout strength in shear":
                factor = self.last_results.inputs.shear_rebar_factor
                provided = self.last_results.values["shear_rebar_provided_area"]
                detail += f"\n实配抗剪锚固钢筋: As,V,prov = {self.last_results.shear_rebar_area:.2f} x {factor:.2f} = {provided:.2f} mm2"
        self.detail_var.set(detail)
        self._draw_detail_diagram(check.name)

    def _redraw_detail_canvas(self, _event=None) -> None:
        if not self.last_results:
            return
        selected = self.tree.selection()
        if not selected:
            self._draw_detail_diagram(None)
            return
        item = self.check_lookup.get(selected[0])
        if isinstance(item, str) or item is None:
            self._draw_detail_diagram(None)
            return
        self._draw_detail_diagram(item.name)

    def _display_check_name(self, name: str) -> str:
        return CHECK_DISPLAY_NAMES.get(name, name)

    def _display_ratio(self, check) -> str:
        if check.name == "Tension-shear interaction" and self.last_results:
            eta_n = self.last_results.governing_tension_ratio
            eta_v = self.last_results.governing_shear_ratio
            if check.status == "Not Applicable":
                return "-"
            if check.section == "ACI 318-19 17.8.2":
                return f"min(eta_N,eta_V)={min(eta_n, eta_v):.3f} ≤ 0.2"
            interaction_sum = self.last_results.values.get("interaction_sum")
            if interaction_sum is not None:
                op = "≤" if interaction_sum <= 1.2 else ">"
                return f"eta_N+eta_V={interaction_sum:.3f} {op} 1.2"
        if check.ratio is None:
            return "-"
        if check.status == "Rebar Required" and self.last_results:
            if check.name == "Concrete breakout strength in tension":
                return f"As,N,req={self.last_results.tension_rebar_area:.2f} mm2"
            if check.name == "Concrete breakout strength in shear":
                return f"As,V,req={self.last_results.shear_rebar_area:.2f} mm2"
        if check.name in {"Minimum spacing s1", "Minimum spacing s2"}:
            symbol = "s1" if check.name.endswith("s1") else "s2"
            op = ">=" if check.status == "OK" else "<"
            return f"{symbol}={check.demand:.0f} {op} 4da={check.capacity:.0f}"
        if check.name == "Minimum member thickness ha":
            op = "≥" if check.status == "OK" else "<"
            return f"ha={check.demand:.0f} {op} hef={check.capacity:.0f}"
        if check.name == "Anchor shear demand after friction":
            if self.last_results and self.last_results.values["vua"] > 1.0e-9:
                return f"Vua={self.last_results.values['vua']:.3f} kN > 0"
            return "Vua=0.000 kN = 0"
        op = "≤" if check.ratio <= 1.0 else ">"
        return f"{check.ratio:.3f} {op} 1.0"

    def _display_status(self, status: str, check=None) -> str:
        if status == "OK":
            return "满足 / OK"
        if status == "NG":
            return "不满足 / NG"
        if status == "Not Applicable":
            return "不适用 / N/A"
        if status == "Required":
            return "需要 / Required"
        if status == "Not Required":
            return "不需要 / Not Required"
        if status == "Rebar Required":
            if check and "tension" in check.name.lower():
                return f"需要配筋 / Rebar Required, As,N,req = {self.last_results.tension_rebar_area:.2f} mm2"
            if check and "shear" in check.name.lower():
                return f"需要配筋 / Rebar Required, As,V,req = {self.last_results.shear_rebar_area:.2f} mm2"
            return "需要配筋 / Rebar Required"
        return status

    def _aggregate_status(self, checks) -> str:
        statuses = [check.status for check in checks]
        if not statuses:
            return "Not Applicable"
        if any(status == "NG" for status in statuses):
            return "NG"
        if any(status == "Rebar Required" for status in statuses):
            return "Rebar Required"
        if all(status == "Not Required" for status in statuses):
            return "Not Required"
        if all(status == "Not Applicable" for status in statuses):
            return "Not Applicable"
        return "OK"

    def _sync_auto_inputs(self, results: AnchorResults) -> None:
        for key in AUTO_FACTOR_KEYS:
            if key in self.vars and key in results.values:
                spec = next((s for s in INPUT_SPECS if s.key == key), None)
                decimals = spec.decimals if spec else 3
                self.vars[key].set(_fmt(results.values[key], decimals))
        if "built_up_grout_pad" in self.vars:
            self.vars["built_up_grout_pad"].set("有 / Yes" if results.inputs.built_up_grout_pad >= 0.5 else "无 / No")

    def _status_tag(self, status: str) -> str:
        if status == "NG":
            return "ng"
        if status == "Rebar Required":
            return "warn"
        if status == "Not Applicable":
            return "na"
        if status in {"Required", "Not Required"}:
            return "info"
        return "ok"

    def _set_detail_canvas_visible(self, visible: bool) -> None:
        canvas = getattr(self, "detail_canvas", None)
        if canvas is None:
            return
        if visible:
            if not canvas.winfo_ismapped():
                canvas.pack(fill=BOTH, expand=True, pady=(8, 0))
        elif canvas.winfo_ismapped():
            canvas.pack_forget()

    def _draw_detail_diagram(self, check_name: str | None) -> None:
        canvas = getattr(self, "detail_canvas", None)
        if canvas is None:
            return
        no_diagram_items = {"Minimum spacing s1", "Minimum spacing s2", "Minimum member thickness ha"}
        if not check_name or check_name in no_diagram_items:
            self._set_detail_canvas_visible(False)
            canvas.delete("all")
            return
        self._set_detail_canvas_visible(True)
        canvas.delete("all")
        w = max(canvas.winfo_width(), 760)
        h = max(canvas.winfo_height(), 180)
        blue = "#2563EB"
        green = "#16A34A"
        orange = "#F97316"
        black = "#111827"
        concrete = "#D1D5DB"
        plate = "#94A3B8"
        crack = "#FFFFFF"
        grey = "#64748B"
        red = "#DC2626"

        canvas.create_rectangle(0, 0, w, h, fill="#F8FAFC", outline="")

        title = self._display_check_name(check_name)
        canvas.create_text(18, 14, text=title, anchor="nw", fill=black, font=("Microsoft YaHei UI", 10, "bold"))

        if check_name == "Concrete local bearing":
            self._draw_local_bearing(canvas, 54, 58, 260, 92)
        elif check_name == "Steel strength in tension":
            self._draw_anchor_section(canvas, 72, 62, 170, 112, mode="steel_tension")
        elif check_name == "Concrete breakout strength in tension":
            self._draw_anchor_section(canvas, 54, 70, 245, 108, mode="tension_breakout")
            if self.last_results and self.last_results.tension_rebar_area > 0:
                self._draw_tension_rebar(canvas, 330, 64, 250, 126)
        elif check_name == "Pullout strength in tension":
            self._draw_anchor_section(canvas, 72, 68, 190, 108, mode="pullout")
        elif check_name == "Anchor shear demand after friction":
            self._draw_friction_shear(canvas, 62, 78, 310, 90)
        elif check_name == "Steel strength in shear":
            self._draw_anchor_section(canvas, 72, 50, 190, 120, mode="steel_shear")
        elif check_name == "Concrete breakout strength in shear":
            self._draw_anchor_section(canvas, 62, 48, 250, 125, mode="shear_breakout")
            if self.last_results and self.last_results.shear_rebar_area > 0:
                self._draw_shear_rebar(canvas, 360, 42, 285, 132)
        elif check_name == "Concrete pryout strength in shear":
            self._draw_anchor_section(canvas, 72, 50, 240, 120, mode="pryout")
        elif check_name == "Tension-shear interaction":
            self._draw_interaction_code_panel(canvas, 42, 52, w - 84, h - 72)
            return
        else:
            canvas.create_text(
                18,
                56,
                text="该项目暂不绘制破坏模式图示，请以上方公式与代入值为准。",
                anchor="nw",
                fill=grey,
                font=("Microsoft YaHei UI", 10),
            )

    def _draw_interaction_code_panel(self, canvas: tk.Canvas, x: float, y: float, bw: float, bh: float) -> None:
        black = "#111827"
        muted = "#475569"
        blue = "#1D4ED8"
        panel = "#FFFFFF"
        rule = "#CBD5E1"
        light = "#EFF6FF"
        eta_n = self.last_results.governing_tension_ratio if self.last_results else 0.0
        eta_v = self.last_results.governing_shear_ratio if self.last_results else 0.0
        interaction_sum = self.last_results.values.get("interaction_sum") if self.last_results else None
        same_anchor_group = bool(self.last_results.values.get("interaction_same_anchor_group", True)) if self.last_results else True

        canvas.create_rectangle(x, y, x + bw, y + bh, fill=panel, outline=rule, width=1)
        canvas.create_rectangle(x, y, x + bw, y + 30, fill=light, outline=rule, width=1)
        canvas.create_text(x + 14, y + 15, text="ACI 318-19 17.8 - Tension and shear interaction", anchor="w", fill=black, font=("Arial", 11, "bold"))

        left = x + 18
        col2 = x + bw * 0.54
        row_y = y + 48
        canvas.create_text(left, row_y, text="17.8.1  Scope", anchor="w", fill=blue, font=("Arial", 10, "bold"))
        canvas.create_text(
            left + 96,
            row_y,
            text="Anchors resisting both tension and shear shall satisfy 17.8.2 and 17.8.3.",
            anchor="w",
            fill=black,
            font=("Arial", 10),
        )

        row_y += 30
        canvas.create_line(left, row_y - 10, x + bw - 18, row_y - 10, fill=rule)
        canvas.create_text(left, row_y, text="17.8.2  Neglect criteria", anchor="w", fill=blue, font=("Arial", 10, "bold"))
        canvas.create_text(left + 20, row_y + 24, text="(a)  Nua / (φNn) ≤ 0.2", anchor="w", fill=black, font=("Arial", 11))
        canvas.create_text(left + 20, row_y + 48, text="(b)  Vua / (φVn) ≤ 0.2", anchor="w", fill=black, font=("Arial", 11))
        canvas.create_text(
            col2,
            row_y + 24,
            text=f"Current: eta_N = {eta_n:.3f}",
            anchor="w",
            fill=muted,
            font=("Arial", 10),
        )
        canvas.create_text(
            col2,
            row_y + 48,
            text=f"Current: eta_V = {eta_v:.3f}",
            anchor="w",
            fill=muted,
            font=("Arial", 10),
        )

        row_y += 88
        canvas.create_line(left, row_y - 10, x + bw - 18, row_y - 10, fill=rule)
        canvas.create_text(left, row_y, text="17.8.3  General interaction equation", anchor="w", fill=blue, font=("Arial", 10, "bold"))
        canvas.create_text(left + 20, row_y + 30, text="Nua / (φNn) + Vua / (φVn) ≤ 1.2", anchor="w", fill=black, font=("Arial", 12, "bold"))
        if interaction_sum is None:
            if not same_anchor_group:
                result_text = "Current case: shear-resisting anchors and tension anchors are different rows; interaction is not applicable."
            else:
                result_text = "Interaction is not required when one force component is not present or may be neglected by 17.8.2."
        else:
            result_text = f"Current: eta_N + eta_V = {interaction_sum:.3f} ≤ 1.2"
        canvas.create_text(col2, row_y + 30, text=result_text, anchor="w", fill=muted, font=("Arial", 10), width=max(220, bw * 0.42))

    def _draw_arrow_small(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, color: str, width: int = 3) -> None:
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow=tk.LAST, arrowshape=(11, 13, 5))

    def _draw_failure_thumbnail(self, canvas: tk.Canvas, x: float, y: float, mode: str, label: str) -> None:
        canvas.create_rectangle(x - 70, y - 28, x + 70, y + 36, fill="#D1D5DB", outline="#111827")
        canvas.create_rectangle(x - 34, y - 42, x + 34, y - 28, fill="#94A3B8", outline="#111827")
        canvas.create_line(x, y - 54, x, y + 20, fill="#F97316", width=8)
        if mode == "tension":
            canvas.create_polygon(x - 58, y - 28, x, y + 34, x + 58, y - 28, fill="#9CA3AF", outline="#64748B")
            self._draw_arrow_small(canvas, x, y - 52, x, y - 76, "#2563EB")
        else:
            canvas.create_polygon(x - 70, y - 28, x + 30, y + 36, x - 70, y + 36, fill="#9CA3AF", outline="#64748B")
            self._draw_arrow_small(canvas, x + 8, y - 44, x + 52, y - 44, "#16A34A")
        canvas.create_text(x, y + 56, text=label, fill="#111827", font=("Arial", 9))

    def _draw_anchor_section(self, canvas: tk.Canvas, x: float, y: float, bw: float, bh: float, mode: str) -> None:
        black = "#111827"
        blue = "#2563EB"
        green = "#16A34A"
        orange = "#F97316"
        concrete = "#D1D5DB"
        plate = "#94A3B8"
        grey = "#9CA3AF"
        red = "#DC2626"

        canvas.create_rectangle(x, y + 28, x + bw, y + bh, fill=concrete, outline=black, width=2)
        ax = x + bw * 0.5
        if mode != "pullout":
            canvas.create_rectangle(x + bw * 0.28, y + 14, x + bw * 0.72, y + 28, fill=plate, outline=black, width=1)
            canvas.create_line(ax, y + 6, ax, y + bh - 18, fill=orange, width=8)
            canvas.create_rectangle(ax - 11, y + 3, ax + 11, y + 15, fill=orange, outline=black)
            canvas.create_rectangle(ax - 6, y - 10, ax + 6, y + 4, fill=orange, outline=black)

        if mode == "steel_tension":
            self._draw_arrow_small(canvas, ax, y - 2, ax, y - 32, blue, 4)
            canvas.create_text(ax + 20, y - 24, text="Nua", anchor="w", fill=blue, font=("Arial", 10, "bold"))
            crack_y = y + 34
            canvas.create_line(ax - 17, crack_y + 8, ax + 17, crack_y - 8, fill=red, width=3)
            canvas.create_line(ax - 14, crack_y + 13, ax + 14, crack_y - 3, fill="#F8FAFC", width=3)
            canvas.create_text(x + bw + 26, y + 50, text="Steel failure", anchor="w", fill=black, font=("Arial", 10))
        elif mode == "tension_breakout":
            cone_left = x + bw * 0.18
            cone_right = x + bw * 0.82
            cone_tip_y = y + bh - 4
            cyan = "#06B6D4"
            canvas.create_polygon(cone_left, y + 28, ax, cone_tip_y, cone_right, y + 28, fill=grey, outline="#64748B")
            canvas.create_line(cone_left, y + 28, ax, cone_tip_y, fill=cyan, width=2)
            canvas.create_line(cone_right, y + 28, ax, cone_tip_y, fill=cyan, width=2)
            canvas.create_line(ax, y + 6, ax, cone_tip_y, fill=orange, width=8)
            canvas.create_rectangle(ax - 11, y + 3, ax + 11, y + 15, fill=orange, outline=black)
            canvas.create_rectangle(ax - 6, y - 10, ax + 6, y + 4, fill=orange, outline=black)
            self._draw_arrow_small(canvas, ax, y - 10, ax, y - 42, blue, 4)
            canvas.create_text(ax + 18, y - 35, text="Nua", anchor="w", fill=blue, font=("Arial", 10, "bold"))
        elif mode == "pullout":
            cyan = "#06B6D4"
            concrete_top = y + 28
            rod_bottom = y + 74
            void_top = rod_bottom
            void_bottom = min(y + bh - 8, y + 104)
            anchor_half_width = 4
            pulled_plate_top = y + 7
            pulled_plate_bottom = y + 20
            canvas.create_rectangle(x + bw * 0.28, pulled_plate_top, x + bw * 0.72, pulled_plate_bottom, fill=plate, outline=black, width=1)
            canvas.create_line(ax, y - 2, ax, rod_bottom, fill=orange, width=8)
            canvas.create_rectangle(ax - 11, y - 5, ax + 11, y + 7, fill=orange, outline=black)
            canvas.create_rectangle(ax - 6, y - 18, ax + 6, y - 5, fill=orange, outline=black)
            canvas.create_line(ax - anchor_half_width, concrete_top, ax - anchor_half_width, void_bottom, fill=cyan, width=1)
            canvas.create_line(ax + anchor_half_width, concrete_top, ax + anchor_half_width, void_bottom, fill=cyan, width=1)
            canvas.create_line(ax - anchor_half_width, void_bottom, ax + anchor_half_width, void_bottom, fill=cyan, width=1)
            canvas.create_rectangle(
                ax - anchor_half_width,
                void_top,
                ax + anchor_half_width,
                void_bottom,
                fill="#F8FAFC",
                outline=cyan,
                width=1,
            )
            self._draw_arrow_small(canvas, ax, y - 12, ax, y - 40, blue, 4)
            canvas.create_text(ax + 18, y - 30, text="Nua", anchor="w", fill=blue, font=("Arial", 10, "bold"))
            canvas.create_text(x + bw + 24, y + 48, text="Pullout", anchor="w", fill=black, font=("Arial", 10))
            canvas.create_line(ax + anchor_half_width, void_top + 12, x + bw + 22, y + 86, fill=cyan, width=1)
            canvas.create_text(x + bw + 28, y + 78, text="void after\npullout", anchor="w", fill=black, font=("Arial", 9))
        elif mode == "steel_shear":
            self._draw_arrow_small(canvas, ax + 10, y + 10, ax + 74, y + 10, green, 4)
            canvas.create_line(ax - 16, y + 31, ax + 16, y + 55, fill=red, width=3)
            canvas.create_text(x + bw + 20, y + 56, text="Steel shear", anchor="w", fill=black, font=("Arial", 10))
        elif mode == "shear_breakout":
            edge_x = x + bw
            crack_start = (ax + 2, y + 28)
            crack_end = (edge_x, y + bh - 10)
            canvas.create_polygon(
                crack_start[0],
                crack_start[1],
                edge_x,
                y + 28,
                edge_x,
                y + bh,
                crack_end[0],
                crack_end[1],
                fill=grey,
                outline="#64748B",
            )
            canvas.create_line(crack_start[0], crack_start[1], crack_end[0], crack_end[1], fill="#FFFFFF", width=3)
            self._draw_arrow_small(canvas, ax + 10, y + 10, ax + 76, y + 10, green, 4)
        elif mode == "pryout":
            large_left_top = x + bw * 0.12
            anchor_bottom = (ax, y + bh - 18)
            small_right_top = x + bw * 0.72
            canvas.create_polygon(
                large_left_top,
                y + 28,
                anchor_bottom[0],
                anchor_bottom[1],
                ax,
                y + 28,
                fill=grey,
                outline="#64748B",
            )
            canvas.create_polygon(
                ax,
                y + 52,
                small_right_top,
                y + 28,
                ax,
                y + 28,
                fill="#B8BFC7",
                outline="#64748B",
            )
            canvas.create_line(large_left_top, y + 28, anchor_bottom[0], anchor_bottom[1], fill="#FFFFFF", width=3)
            canvas.create_line(ax, y + 52, small_right_top, y + 28, fill="#FFFFFF", width=2)
            canvas.create_line(ax, y + 6, ax, y + bh - 18, fill=orange, width=8)
            self._draw_arrow_small(canvas, ax + 10, y + 10, ax + 76, y + 10, green, 4)
            canvas.create_text(x + bw + 20, y + 56, text="Concrete pryout", anchor="w", fill=black, font=("Arial", 10))

    def _draw_local_bearing(self, canvas: tk.Canvas, x: float, y: float, bw: float, bh: float) -> None:
        black = "#111827"
        blue = "#2563EB"
        concrete = "#D1D5DB"
        plate = "#94A3B8"
        orange = "#F97316"
        canvas.create_rectangle(x, y + 36, x + bw, y + bh, fill=concrete, outline=black, width=2)
        canvas.create_rectangle(x + 42, y + 18, x + bw - 42, y + 36, fill=plate, outline=black, width=2)
        canvas.create_polygon(x + 42, y + 36, x + bw - 42, y + 36, x + bw - 42, y + 82, fill="#9CA3AF", outline="#64748B")
        for idx in range(6):
            px = x + 62 + idx * ((bw - 124) / 5)
            py2 = y + 42 + idx * 7
            self._draw_arrow_small(canvas, px, py2 + 18, px, py2, "#FFFFFF", 1)
        for dx in (90, bw - 90):
            bolt_x = x + dx
            canvas.create_line(bolt_x, y + 4, bolt_x, y + bh - 18, fill=orange, width=7)
            canvas.create_rectangle(bolt_x - 9, y + 6, bolt_x + 9, y + 18, fill=orange, outline=black, width=1)
            canvas.create_rectangle(bolt_x - 4, y - 6, bolt_x + 4, y + 6, fill=orange, outline=black, width=1)
        self._draw_arrow_small(canvas, x + bw / 2, y - 8, x + bw / 2, y + 30, blue, 4)
        canvas.create_text(x + bw + 28, y + 38, text="σmax ≤ fc\nConcrete local bearing", anchor="w", fill=black, font=("Arial", 10))

    def _draw_friction_shear(self, canvas: tk.Canvas, x: float, y: float, bw: float, bh: float) -> None:
        black = "#111827"
        green = "#16A34A"
        blue = "#2563EB"
        concrete = "#D1D5DB"
        plate = "#94A3B8"
        orange = "#F97316"
        canvas.create_rectangle(x, y + 34, x + bw, y + bh, fill=concrete, outline=black, width=2)
        canvas.create_rectangle(x + 45, y + 18, x + bw - 45, y + 34, fill=plate, outline=black, width=2)
        for bolt_x in (x + bw / 2 - 58, x + bw / 2 + 58):
            canvas.create_line(bolt_x, y + 6, bolt_x, y + bh - 16, fill=orange, width=7)
            canvas.create_rectangle(bolt_x - 9, y + 6, bolt_x + 9, y + 18, fill=orange, outline=black, width=1)
            canvas.create_rectangle(bolt_x - 4, y - 6, bolt_x + 4, y + 6, fill=orange, outline=black, width=1)
        self._draw_arrow_small(canvas, x + bw / 2 - 36, y - 18, x + bw / 2 + 44, y - 18, blue, 4)
        canvas.create_text(x + bw / 2 - 50, y - 31, text="V", fill=blue, font=("Arial", 11, "bold"))
        self._draw_arrow_small(canvas, x + bw / 2 + 44, y + 58, x + bw / 2 - 36, y + 58, green, 4)
        canvas.create_text(x + bw / 2 + 50, y + 51, text="Vfb", fill=green, font=("Arial", 11, "bold"), anchor="w")
        if self.last_results:
            vfb = self.last_results.values["friction_force"]
            v = self.last_results.inputs.v
            vua = self.last_results.values["vua"]
            text = (
                f"V = Vfb + 2Vua\nV/Vfb = {v / vfb:.3f}; Vua = {vua:.3f} kN"
                if vfb > 0
                else "Friction unavailable"
            )
        else:
            text = "Friction check"
        canvas.create_text(x + bw + 26, y + 38, text=text, anchor="w", fill=black, font=("Arial", 10))

    def _draw_tension_rebar(self, canvas: tk.Canvas, x: float, y: float, bw: float, bh: float) -> None:
        black = "#111827"
        concrete = "#D1D5DB"
        plate = "#94A3B8"
        blue = "#2563EB"
        orange = "#F97316"
        cyan = "#06B6D4"
        red = "#DC2626"
        canvas.create_rectangle(x, y + 30, x + bw, y + bh, fill=concrete, outline=black, width=2)
        failure_bh = 112
        cone_left = x + bw * 0.09
        cone_right = x + bw * 0.91
        canvas.create_rectangle(x + 52, y + 16, x + bw - 52, y + 30, fill=plate, outline=black, width=1)
        left_anchor = x + bw * 0.37
        right_anchor = x + bw * 0.63
        bottom_y = y + failure_bh - 12
        canvas.create_polygon(
            cone_left,
            y + 30,
            left_anchor,
            bottom_y,
            right_anchor,
            bottom_y,
            cone_right,
            y + 30,
            fill="#9CA3AF",
            outline="#64748B",
        )
        canvas.create_line(cone_left, y + 30, left_anchor, bottom_y, fill=cyan, width=2)
        canvas.create_line(left_anchor, bottom_y, right_anchor, bottom_y, fill=cyan, width=2)
        canvas.create_line(right_anchor, bottom_y, cone_right, y + 30, fill=cyan, width=2)
        mesh_y = y + 39
        canvas.create_line(x + 8, mesh_y, x + bw - 8, mesh_y, fill=blue, width=4)
        for dot_x in (x + bw * 0.08, x + bw * 0.25, left_anchor + 11, right_anchor - 11, x + bw * 0.75, x + bw * 0.92):
            canvas.create_oval(dot_x - 5, mesh_y + 5, dot_x + 5, mesh_y + 15, fill=blue, outline=blue)
        for ax in (left_anchor, right_anchor):
            canvas.create_line(ax, y + 3, ax, y + failure_bh - 10, fill=orange, width=7)
            canvas.create_rectangle(ax - 10, y + 3, ax + 10, y + 15, fill=orange, outline=black)
            canvas.create_rectangle(ax - 5, y - 8, ax + 5, y + 4, fill=orange, outline=black)
        self._draw_arrow_small(canvas, x + bw / 2, y + 8, x + bw / 2, y - 22, blue, 4)
        canvas.create_text(x + bw / 2 + 18, y - 17, text="Nua", anchor="w", fill=blue, font=("Arial", 10, "bold"))
        u_left = x + bw * 0.30
        u_right = x + bw * 0.70
        u_top = mesh_y
        u_bottom = y + bh - 4
        radius = 18
        canvas.create_line(u_left, u_bottom, u_left, u_top + radius, fill=red, width=5, capstyle=tk.ROUND)
        canvas.create_arc(
            u_left,
            u_top,
            u_left + 2 * radius,
            u_top + 2 * radius,
            start=180,
            extent=-90,
            style=tk.ARC,
            outline=red,
            width=5,
        )
        canvas.create_line(u_left + radius, u_top, u_right - radius, u_top, fill=red, width=5)
        canvas.create_arc(
            u_right - 2 * radius,
            u_top,
            u_right,
            u_top + 2 * radius,
            start=90,
            extent=-90,
            style=tk.ARC,
            outline=red,
            width=5,
        )
        canvas.create_line(u_right, u_top + radius, u_right, u_bottom, fill=red, width=5, capstyle=tk.ROUND)
        canvas.create_line(u_right - 2, u_top + 42, x + bw + 28, y + 88, fill=red, width=1)
        area = self.last_results.tension_rebar_area if self.last_results else 0.0
        canvas.create_text(x + bw + 34, y + 78, text=f"Anchor reinforcement\nAs,N,req = {area:.2f} mm2", anchor="w", fill=black, font=("Arial", 10))

    def _draw_shear_rebar(self, canvas: tk.Canvas, x: float, y: float, bw: float, bh: float) -> None:
        black = "#111827"
        concrete = "#D1D5DB"
        green = "#16A34A"
        orange = "#F97316"
        plate = "#94A3B8"
        red = "#DC2626"
        cyan = "#06B6D4"
        canvas.create_rectangle(x, y + 24, x + bw, y + bh, fill=concrete, outline=black, width=2)
        edge_x = x + bw
        ax = x + bw * 0.42
        crack_start = (ax + 4, y + 24)
        crack_end = (edge_x, y + bh - 8)
        canvas.create_polygon(
            crack_start[0],
            crack_start[1],
            edge_x,
            y + 24,
            edge_x,
            y + bh,
            crack_end[0],
            crack_end[1],
            fill="#9CA3AF",
            outline="#64748B",
        )
        canvas.create_line(crack_start[0], crack_start[1], crack_end[0], crack_end[1], fill=cyan, width=2)
        canvas.create_rectangle(x + bw * 0.22, y + 10, x + bw * 0.72, y + 24, fill=plate, outline=black, width=1)
        canvas.create_line(ax, y - 4, ax, y + bh - 26, fill=orange, width=7)
        canvas.create_rectangle(ax - 10, y - 3, ax + 10, y + 9, fill=orange, outline=black)
        canvas.create_rectangle(ax - 5, y - 16, ax + 5, y - 3, fill=orange, outline=black)
        self._draw_arrow_small(canvas, ax + 26, y + 7, ax + 86, y + 7, green, 4)
        canvas.create_text(ax + 91, y - 5, text="Vua", anchor="w", fill=green, font=("Arial", 10, "bold"))
        rebar_y = y + 42
        rebar_right = x + bw - 20
        rebar_bottom = y + bh - 18
        radius = 16
        canvas.create_line(x + 18, rebar_y, rebar_right - radius, rebar_y, fill=red, width=5, capstyle=tk.ROUND)
        canvas.create_arc(
            rebar_right - 2 * radius,
            rebar_y,
            rebar_right,
            rebar_y + 2 * radius,
            start=90,
            extent=-90,
            style=tk.ARC,
            outline=red,
            width=5,
        )
        canvas.create_line(rebar_right, rebar_y + radius, rebar_right, rebar_bottom, fill=red, width=5, capstyle=tk.ROUND)
        dot_x = rebar_right - 10
        dot_y = rebar_y + radius - 2
        canvas.create_oval(dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5, fill="#22C55E", outline="")
        canvas.create_line(rebar_right - 2, rebar_y + radius + 8, x + bw + 16, y + 70, fill=red, width=1)
        area = self.last_results.shear_rebar_area if self.last_results else 0.0
        canvas.create_text(x + bw + 22, y + 62, text=f"Anchor reinforcement\nAs,V,req = {area:.2f} mm2", anchor="w", fill=black, font=("Arial", 10))

    def export_word(self) -> None:
        if self.last_results is None:
            self.calculate()
        if self.last_results is None:
            return
        initial = "Anchor_Bolt_Calculation_Report.docx"
        path = filedialog.asksaveasfilename(
            title="保存英文计算书",
            defaultextension=".docx",
            initialfile=initial,
            filetypes=[("Word Document", "*.docx")],
        )
        if not path:
            return
        try:
            output = write_calculation_report(
                self.last_results,
                path,
                project_name=self.project_var.get().strip() or "Photovoltaic Tracker Support",
                prepared_by=self.prepared_by_var.get().strip() or "Engineer",
            )
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return
        messagebox.showinfo("导出完成", f"英文计算书已保存:\n{output}")

    def draw_diagram(self) -> None:
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 720)
        h = max(canvas.winfo_height(), 520)
        results = self.last_results
        inputs = results.inputs if results else AnchorInputs()
        concrete = "#D1D5DB"
        concrete_dark = "#9CA3AF"
        plate = "#CBD5E1"
        orange = "#F97316"
        red = "#EF4444"
        blue = "#2563EB"
        green = "#16A34A"
        black = "#111827"
        white = "#FFFFFF"

        # Plan view: horizontal dimension is B, vertical dimension is L.
        px, py = 55, 78
        max_plan_w = max(w * 0.43 - 90, 260)
        max_plan_h = max(h - 150, 260)
        plan_scale = min(max_plan_w / inputs.pedestal_b, max_plan_h / inputs.pedestal_l)
        p_w = inputs.pedestal_b * plan_scale
        p_h = inputs.pedestal_l * plan_scale
        canvas.create_text(px, py - 34, text="Plan View", anchor="w", fill=black, font=("Microsoft YaHei UI", 12, "bold"))
        canvas.create_rectangle(px, py, px + p_w, py + p_h, fill=concrete, outline=black, width=2)
        cx, cy = px + p_w / 2, py + p_h / 2
        plate_w = inputs.plate_b * plan_scale
        plate_h = inputs.plate_l * plan_scale
        canvas.create_rectangle(cx - plate_w / 2, cy - plate_h / 2, cx + plate_w / 2, cy + plate_h / 2, fill=plate, outline=black, width=2)
        s_x = inputs.s2 * plan_scale
        s_y = inputs.s1 * plan_scale
        ax1, ax2 = cx - s_x / 2, cx + s_x / 2
        ay1, ay2 = cy - s_y / 2, cy + s_y / 2
        canvas.create_line(cx, py + 15, cx, py + p_h - 15, fill=green, width=2, dash=(7, 5))
        canvas.create_line(px + 15, cy, px + p_w - 15, cy, fill=green, width=2, dash=(7, 5))

        if inputs.shear_case == 1:
            selected_y = ay2
            released_y = None
            selected_label = "Case 1：近边圆孔承压"
        else:
            selected_y = ay1
            released_y = ay2
            selected_label = "Case 2：远边承压；近边长圆孔释放"
        edge_y = py + p_h
        edge_distance = max(edge_y - selected_y, 10)
        spread = 1.5 * edge_distance
        x_left = max(px, ax1 - spread)
        x_right = min(px + p_w, ax2 + spread)
        canvas.create_line(ax1, selected_y, x_left, edge_y, fill=white, width=4)
        canvas.create_line(ax2, selected_y, x_right, edge_y, fill=white, width=4)
        canvas.create_line(x_left, edge_y, x_right, edge_y, fill=white, width=4)
        canvas.create_line(px + 10, selected_y, px + p_w - 10, selected_y, fill=blue, width=2, dash=(6, 4))
        for y in (ay1, ay2):
            for x in (ax1, ax2):
                is_released = released_y is not None and abs(y - released_y) < 0.1
                is_resisting = abs(y - selected_y) < 0.1
                self._draw_plan_anchor_hole(canvas, x, y, slotted=is_released, resisting=is_resisting, bolt_color=red)
        arrow_x = cx
        self._draw_arrow(canvas, arrow_x, selected_y - 58, arrow_x, selected_y + 58, blue)
        canvas.create_text(arrow_x + 22, selected_y + 4, text="V", fill=blue, font=("Arial", 11, "bold"), anchor="w")
        moment_r = max(28, min(50, plate_w * 0.16, plate_h * 0.16))
        self._draw_moment(canvas, cx - moment_r * 0.6, cy + moment_r * 0.15, moment_r, blue)
        canvas.create_text(px, py + p_h + 96, text=selected_label, anchor="w", fill=blue, font=("Arial", 9, "bold"))
        if released_y is not None:
            canvas.create_text(
                cx,
                released_y + 32,
                text="长圆孔释放剪力",
                anchor="center",
                fill=MUTED,
                font=("Microsoft YaHei UI", 8),
            )

        plate_left = cx - plate_w / 2
        plate_right = cx + plate_w / 2
        plate_top = cy - plate_h / 2
        plate_bottom = cy + plate_h / 2
        self._dimension(canvas, px, py + p_h + 28, px + p_w, py + p_h + 28, self._dim_label("B", inputs.pedestal_b))
        self._dimension(canvas, px + p_w + 30, py, px + p_w + 30, py + p_h, self._dim_label("L", inputs.pedestal_l), vertical=True)
        self._dimension(canvas, ax1, py + p_h + 62, ax2, py + p_h + 62, self._dim_label("s2", inputs.s2))
        self._dimension(canvas, px + p_w + 110, ay1, px + p_w + 110, ay2, self._dim_label("s1", inputs.s1), vertical=True)
        self._dimension(canvas, plate_left, plate_top - 32, plate_right, plate_top - 32, self._dim_label("b", inputs.plate_b))
        self._dimension(canvas, plate_left - 28, plate_top, plate_left - 28, plate_bottom, self._dim_label("l", inputs.plate_l), vertical=True)
        canvas.create_text(px + 12, py + 16, text="Concrete pedestal", anchor="w", fill=black, font=("Arial", 9))
        canvas.create_text(plate_left + 14, plate_top + 12, text="Steel plate", anchor="w", fill=black, font=("Arial", 9))

        # Elevation view: horizontal dimension follows B and b, vertical dimension follows ha.
        ex, ey = w * 0.60, 95
        max_elev_w = max(w * 0.28, 250)
        max_elev_h = max(h - 180, 300)
        elev_scale = min(max_elev_w / inputs.pedestal_b, max_elev_h / inputs.ha)
        ew = inputs.pedestal_b * elev_scale
        elev_h = inputs.ha * elev_scale
        steel_w = inputs.plate_b * elev_scale
        steel_thk = 14
        canvas.create_text(ex, ey - 48, text="Elevation View", anchor="w", fill=black, font=("Microsoft YaHei UI", 12, "bold"))
        pedestal_top = ey + 45
        pedestal_bottom = pedestal_top + elev_h
        canvas.create_rectangle(ex, pedestal_top, ex + ew, pedestal_bottom, fill=concrete, outline=black, width=2)
        steel_x1 = ex + ew / 2 - steel_w / 2
        steel_x2 = ex + ew / 2 + steel_w / 2
        canvas.create_rectangle(steel_x1, pedestal_top - steel_thk, steel_x2, pedestal_top, fill=concrete_dark, outline=black, width=2)
        elev_s2 = inputs.s2 * elev_scale
        bolt_xs = (ex + ew / 2 - elev_s2 / 2, ex + ew / 2 + elev_s2 / 2)
        embed_len = min(inputs.hef * elev_scale, elev_h)
        hook_len = max(22.0, min(48.0, inputs.eh * elev_scale))
        hook_y = pedestal_top + embed_len
        hook_radius = max(10.0, min(18.0, hook_len * 0.35))
        for idx, x in enumerate(bolt_xs):
            hook_dir = -1 if idx == 0 else 1
            self._draw_elevation_anchor(
                canvas,
                x=x,
                top_y=pedestal_top - steel_thk - 14,
                plate_top_y=pedestal_top - steel_thk,
                hook_y=hook_y,
                hook_len=hook_len,
                hook_radius=hook_radius,
                hook_dir=hook_dir,
                shaft_width=10,
                nut_color=orange,
                outline=black,
                washer_fill="#CBD5E1",
            )
        canvas.create_line(ex + ew / 2, ey, ex + ew / 2, pedestal_bottom + 25, fill=green, width=2, dash=(7, 5))
        self._draw_arrow(canvas, ex + ew / 2, ey - 10, ex + ew / 2, ey + 70, blue)
        canvas.create_text(ex + ew / 2 + 20, ey + 18, text="N", fill=blue, anchor="w", font=("Arial", 11, "bold"))
        self._dimension(canvas, ex + ew + 40, pedestal_top, ex + ew + 40, pedestal_top + embed_len, self._dim_label("hef", inputs.hef), vertical=True)
        self._dimension(canvas, ex + ew + 86, pedestal_top, ex + ew + 86, pedestal_bottom, self._dim_label("ha", inputs.ha), vertical=True)
        self._dimension(canvas, steel_x1, pedestal_top - steel_thk - 42, steel_x2, pedestal_top - steel_thk - 42, self._dim_label("b", inputs.plate_b))
        canvas.create_text(ex + 15, pedestal_top + elev_h * 0.55, text="Concrete pedestal", anchor="w", fill=black, font=("Arial", 9))
        canvas.create_text(steel_x1, pedestal_top - steel_thk - 64, text="Steel plate", anchor="w", fill=black, font=("Arial", 9))
        canvas.create_text(
            48,
            h - 35,
            text="图示随左侧几何参数与剪力 Case 更新；详细 Nua/Vua 需求请查看“结果”页。",
            anchor="w",
            fill=MUTED,
            font=("Microsoft YaHei UI", 9),
        )

    def _draw_arrow(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, color: str) -> None:
        canvas.create_line(x1, y1, x2, y2, fill=color, width=5, arrow=tk.LAST, arrowshape=(16, 18, 6))

    def _dim_label(self, symbol: str, value: float) -> str:
        return f"{symbol}={_fmt(value, 1)}"

    def _draw_plan_anchor_hole(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        *,
        slotted: bool,
        resisting: bool,
        bolt_color: str,
    ) -> None:
        if slotted:
            slot_w = 20
            slot_len = 42
            canvas.create_line(
                x,
                y - slot_len / 2 + slot_w / 2,
                x,
                y + slot_len / 2 - slot_w / 2,
                fill="#111827",
                width=slot_w + 4,
                capstyle=tk.ROUND,
            )
            canvas.create_line(
                x,
                y - slot_len / 2 + slot_w / 2,
                x,
                y + slot_len / 2 - slot_w / 2,
                fill="#FFFFFF",
                width=slot_w,
                capstyle=tk.ROUND,
            )
        else:
            canvas.create_oval(x - 12, y - 12, x + 12, y + 12, fill="#FFFFFF", outline="#111827", width=2)
        if resisting:
            canvas.create_oval(x - 17, y - 17, x + 17, y + 17, outline="#2563EB", width=3)
        canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill=bolt_color, outline="#111827", width=1)

    def _draw_elevation_anchor(
        self,
        canvas: tk.Canvas,
        *,
        x: float,
        top_y: float,
        plate_top_y: float,
        hook_y: float,
        hook_len: float,
        hook_radius: float,
        hook_dir: int,
        shaft_width: int,
        nut_color: str,
        outline: str,
        washer_fill: str,
    ) -> None:
        shaft_top = top_y - 16
        canvas.create_line(x, shaft_top, x, hook_y - hook_radius, fill=outline, width=shaft_width, capstyle=tk.ROUND)
        if hook_dir < 0:
            center_x = x - hook_radius
            angle_start, angle_end = 0.0, math.pi / 2.0
        else:
            center_x = x + hook_radius
            angle_start, angle_end = math.pi, math.pi / 2.0
        center_y = hook_y - hook_radius
        steps = 10
        arc_points: list[float] = []
        for step in range(steps + 1):
            t = step / steps
            angle = angle_start + (angle_end - angle_start) * t
            arc_points.extend((center_x + hook_radius * math.cos(angle), center_y + hook_radius * math.sin(angle)))
        canvas.create_line(*arc_points, fill=outline, width=shaft_width, smooth=True, splinesteps=18, capstyle=tk.ROUND)
        canvas.create_line(x + hook_dir * hook_radius, hook_y, x + hook_dir * hook_len, hook_y, fill=outline, width=shaft_width, capstyle=tk.ROUND)

        washer_w, washer_h = 28, 6
        washer_y1 = plate_top_y - washer_h
        canvas.create_rectangle(x - washer_w / 2, washer_y1, x + washer_w / 2, plate_top_y, fill=washer_fill, outline=outline, width=1)
        nut_w, nut_h = 22, 16
        nut_top = washer_y1 - nut_h
        canvas.create_rectangle(x - 4, nut_top - 15, x + 4, nut_top, fill=nut_color, outline=outline, width=1)
        canvas.create_rectangle(x - nut_w * 0.32, nut_top, x + nut_w * 0.32, washer_y1, fill=nut_color, outline=outline, width=1)
        canvas.create_polygon(
            x - nut_w / 2,
            washer_y1 - 2,
            x + nut_w / 2,
            washer_y1 - 2,
            x + nut_w * 0.38,
            washer_y1 + 5,
            x - nut_w * 0.38,
            washer_y1 + 5,
            fill=nut_color,
            outline=outline,
            width=1,
        )

    def _dimension(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, label: str, vertical: bool = False) -> None:
        canvas.create_line(x1, y1, x2, y2, fill=TEXT, width=1)
        if vertical:
            canvas.create_line(x1 - 7, y1, x1 + 7, y1, fill=TEXT)
            canvas.create_line(x2 - 7, y2, x2 + 7, y2, fill=TEXT)
            canvas.create_text(x1 + 18, (y1 + y2) / 2, text=label, fill=TEXT, font=("Arial", 9), angle=90)
        else:
            canvas.create_line(x1, y1 - 7, x1, y1 + 7, fill=TEXT)
            canvas.create_line(x2, y2 - 7, x2, y2 + 7, fill=TEXT)
            canvas.create_text((x1 + x2) / 2, y1 + 14, text=label, fill=TEXT, font=("Arial", 9))

    def _draw_moment(self, canvas: tk.Canvas, x: float, y: float, r: float, color: str) -> None:
        points: list[float] = []
        for step in range(24):
            angle = math.radians(270 - 180 * step / 23)
            points.extend((x + r * math.cos(angle), y + r * math.sin(angle)))
        canvas.create_line(
            *points,
            fill=color,
            width=5,
            smooth=True,
            splinesteps=24,
            arrow=tk.LAST,
            arrowshape=(15, 18, 6),
            capstyle=tk.ROUND,
        )
        canvas.create_text(x + r * 0.55, y + r * 0.82, text="M", fill=color, font=("Arial", 13, "bold"))


def _fmt(value: float, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "--self-test-report":
        results = calculate_anchor(AnchorInputs())
        write_calculation_report(results, sys.argv[2], project_name="Packaged Smoke Test", prepared_by="QA")
        return
    app = AnchorBoltApp()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
