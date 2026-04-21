from tkinter import ttk
from styles.colors import (
    LEFT_BG,
)


def apply_ttk_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    # Light premium palette for dashboard/module views.
    app_bg = LEFT_BG
    panel_bg = "#FFFFFF"
    panel_border = "#D8CDBD"
    accent = "#B6905C"
    accent_hover = "#CBA77A"
    accent_text = "#1E2A3A"
    heading_text = "#2A2A2A"
    muted_text = "#6F665E"
    input_bg = "#FBF9F6"
    input_border = "#CFC4B5"

    root.configure(bg=app_bg)

    style.configure(".", background=app_bg, foreground=heading_text)
    style.configure("TFrame", background=app_bg)
    style.configure("TLabelframe", background=panel_bg, foreground=heading_text, bordercolor=panel_border, relief="solid")
    style.configure("TLabelframe.Label", background=panel_bg, foreground=muted_text, font=("Segoe UI", 10, "bold"))
    style.configure("TLabel", background=app_bg, foreground=heading_text)

    style.configure(
        "TButton",
        background=accent,
        foreground=accent_text,
        borderwidth=0,
        padding=(12, 7),
        focusthickness=0,
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "TButton",
        background=[("active", accent_hover), ("pressed", accent_hover)],
        foreground=[("disabled", "#7A736B")],
    )

    style.configure(
        "TEntry",
        fieldbackground=input_bg,
        foreground=heading_text,
        bordercolor=input_border,
        lightcolor=input_border,
        darkcolor=input_border,
        insertcolor=accent,
        padding=6,
    )
    style.map("TEntry", bordercolor=[("focus", accent)], lightcolor=[("focus", accent)], darkcolor=[("focus", accent)])

    style.configure(
        "TCombobox",
        fieldbackground=input_bg,
        foreground=heading_text,
        bordercolor=input_border,
        arrowsize=16,
        padding=6,
    )

    style.configure("Treeview", background=panel_bg, foreground=heading_text, fieldbackground=panel_bg, rowheight=28)
    style.map("Treeview", background=[("selected", "#EFE7DC")], foreground=[("selected", "#2A2A2A")])
    style.configure("Treeview.Heading", background="#EFE7DC", foreground="#3E352B", font=("Segoe UI", 9, "bold"))
