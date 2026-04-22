"""
Views module — all Tkinter UI classes for the Property Management System.
Commune page: apartment grid → apartment detail (tabbed: overview, lease+tenant, payments, maintenance, complaints)
"""
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from typing import Optional, Callable, List
from abc import ABC, abstractmethod
from models import (
    Tenant, Lease, Apartment, Payment, Complaint, MaintenanceRequest,
    LeaseStatus, ApartmentStatus, ComplaintStatus, MaintenancePriority
)

# ─────────────────────────── PALETTE (light mode) ──────────────────────────
DARK_BG    = "#E8ECF0"   # page background — slate-blue-gray
PANEL_BG   = "#FFFFFF"   # sidebar / panels — pure white
CARD_BG    = "#FFFFFF"   # cards — white, pops against DARK_BG
ACCENT     = "#2563EB"   # primary blue (indigo-600)
ACCENT2    = "#6D28D9"   # secondary violet
SUCCESS    = "#0D6E43"   # forest green — readable, not neon
WARNING    = "#92540B"   # amber-brown
DANGER     = "#991B1B"   # deep red
TEXT       = "#111827"   # near-black
TEXT_DIM   = "#4B5563"   # slate-600
TEXT_MUTED = "#9CA3AF"   # slate-400
BORDER     = "#E5E7EB"   # slate-200
HOVER_BG   = "#F3F4F6"   # slate-100

FONT_HEAD  = ("Segoe UI", 22, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUB   = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)

STATUS_COLORS = {
    "Active": SUCCESS, "Pending": WARNING, "Terminated": DANGER,
    "Expired": DANGER, "Available": SUCCESS, "Occupied": ACCENT,
    "Under Maintenance": WARNING, "Open": WARNING, "Resolved": SUCCESS,
    "Closed": TEXT_DIM, "Paid": SUCCESS, "Overdue": DANGER,
    "In Progress": ACCENT, "Under Review": ACCENT2, "Partial": WARNING,
    "High": DANGER, "Urgent": DANGER, "Medium": WARNING, "Low": SUCCESS,
}

def sc(status): return STATUS_COLORS.get(status, TEXT_DIM)

def _darken(hex_color):
    try:
        h = hex_color.lstrip("#")
        r, g, b_ = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{max(0,r-30):02x}{max(0,g-30):02x}{max(0,b_-30):02x}"
    except Exception:
        return hex_color

# Tinted badge bg for light mode
_BADGE_TINTS = {
    "#2563EB": "#DBEAFE",  # blue -> blue-100
    "#6D28D9": "#EDE9FE",  # violet -> violet-100
    "#0D6E43": "#D1FAE5",  # green -> emerald-100
    "#92540B": "#FEF3C7",  # amber -> amber-100
    "#991B1B": "#FEE2E2",  # red -> red-100
    "#4B5563": "#F3F4F6",  # dim -> slate-100
    "#9CA3AF": "#F9FAFB",  # muted -> slate-50
}

def badge(parent, text, color=None):
    c = color or sc(text)
    bg = _BADGE_TINTS.get(c, HOVER_BG)
    return tk.Label(parent, text=f"  {text}  ", font=FONT_SMALL,
                    bg=bg, fg=c, relief="flat", padx=4, pady=2)

def mkbtn(parent, text, cmd, color=ACCENT, small=False, width=None):
    f = FONT_SMALL if small else FONT_BODY
    b = tk.Button(parent, text=text, command=cmd, bg=color, fg="white",
                  font=f, relief="flat", bd=0, cursor="hand2",
                  padx=10 if small else 16, pady=5 if small else 9,
                  activebackground=color, activeforeground="white")
    if width: b.config(width=width)
    b.bind("<Enter>", lambda e: b.config(bg=_darken(color)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def export_bar(parent, title: str, get_data_fn, bg=DARK_BG):
    """Compact export toolbar with Export CSV and Export PDF buttons.
    get_data_fn() must return (columns: list[str], rows: list[tuple]).
    """
    from tkinter import filedialog

    frame = tk.Frame(parent, bg=bg)

    def _do(fmt):
        from exporters import get_exporter, default_filename
        try:
            cols, rows = get_data_fn()
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc), parent=parent)
            return
        if not rows:
            messagebox.showinfo("Nothing to Export",
                                "No data to export.", parent=parent)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[("CSV files", "*.csv")] if fmt == "csv"
                      else [("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_filename(title.replace(" ", "_"), fmt),
            title=f"Export as {fmt.upper()}",
        )
        if not path:
            return
        try:
            get_exporter(fmt).export(title, cols, rows, path)
            messagebox.showinfo("Exported", f"Saved to:\n{path}",
                                parent=parent)
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc), parent=parent)

    mkbtn(frame, "⬇ CSV", lambda: _do("csv"),
          color=SUCCESS, small=True).pack(side="left", padx=(0, 4))
    mkbtn(frame, "⬇ PDF", lambda: _do("pdf"),
          color=ACCENT2, small=True).pack(side="left")
    return frame

def entry_var(parent, label, row, col=0, default="", width=24, colspan=1, placeholder=""):
    tk.Label(parent, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
             ).grid(row=row, column=col, sticky="w", padx=6, pady=(8,2))
    e = tk.Entry(parent, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=width,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
    e.grid(row=row+1, column=col, columnspan=colspan, sticky="ew", padx=6, pady=(0,4))
    _ph = [False]
    if default:
        e.insert(0, default)
    elif placeholder:
        e.insert(0, placeholder)
        e.config(fg=TEXT_MUTED)
        _ph[0] = True
    if placeholder:
        def _fin(ev):
            if _ph[0]: e.delete(0, "end"); e.config(fg=TEXT); _ph[0] = False
        def _fout(ev):
            if not e.get(): e.insert(0, placeholder); e.config(fg=TEXT_MUTED); _ph[0] = True
        e.bind("<FocusIn>", _fin)
        e.bind("<FocusOut>", _fout)
    class _Var:
        def get(self_): return "" if _ph[0] else e.get()
        def set(self_, v):
            e.delete(0, "end"); _ph[0] = False
            if v: e.insert(0, v); e.config(fg=TEXT)
            elif placeholder: e.insert(0, placeholder); e.config(fg=TEXT_MUTED); _ph[0] = True
    return _Var()

def combo_var(parent, label, opts, row, col=0, default=None, width=22):
    tk.Label(parent, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
             ).grid(row=row, column=col, sticky="w", padx=6, pady=(8,2))
    var = tk.StringVar(value=default or (opts[0] if opts else ""))
    cb = ttk.Combobox(parent, textvariable=var, values=opts, font=FONT_BODY,
                      width=width, state="readonly")
    cb.grid(row=row+1, column=col, sticky="ew", padx=6, pady=(0,4))
    return var

def scrollable(parent, bg=CARD_BG):
    """Returns (outer, inner). Pack outer.

    Two-finger touchpad scroll and mouse wheel work over any child widget
    because _bind_tree propagates <MouseWheel> down the full widget tree
    each time a child is added (triggered by <Configure>).
    """
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
    sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def _scroll(e):
        canvas.yview_scroll(-1 * (e.delta // 120), "units")

    def _bind_tree(widget):
        widget.bind("<MouseWheel>", _scroll)
        for child in widget.winfo_children():
            _bind_tree(child)

    def _on_configure(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
        _bind_tree(inner)

    inner.bind("<Configure>", _on_configure)
    canvas.bind("<MouseWheel>", _scroll)
    return outer, inner

def sec_hdr(parent, title, bg=None):
    bg = bg if bg is not None else parent.cget("bg")
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", padx=24, pady=(20,6))
    tk.Label(row, text=title, font=FONT_SUB, bg=bg, fg=TEXT).pack(side="left")
    tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(10,0), pady=5)

def info_grid(parent, fields, cols=3, bg=CARD_BG):
    g = tk.Frame(parent, bg=bg)
    g.pack(fill="x", padx=28, pady=(0,8))
    for i, (lbl, val) in enumerate(fields):
        r, c = divmod(i, cols)
        tk.Label(g, text=lbl, font=FONT_SMALL, bg=bg, fg=TEXT_DIM
                 ).grid(row=r*2, column=c, sticky="w", padx=10, pady=(6,0))
        tk.Label(g, text=str(val) if val else "—", font=FONT_BODY, bg=bg, fg=TEXT, wraplength=220
                 ).grid(row=r*2+1, column=c, sticky="w", padx=10)
    return g


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  DATA EXPLORER  — Treeview + row-detail panel (ported from prototype)
# ══════════════════════════════════════════════════════════════════════════════

class DataExplorerView(tk.Frame):
    _TABLES = [
        ("apartments",         "Apartments"),
        ("tenants",            "Tenants"),
        ("leases",             "Leases"),
        ("payments",           "Payments"),
        ("maintenance_requests","Maintenance"),
        ("complaints",         "Complaints"),
        ("staff",              "Staff"),
        ("workers",            "Workers"),
    ]
    _MASKED = {"password_hash"}
    _STATUS_COLOURS = {
        "active": SUCCESS, "available": SUCCESS, "paid": SUCCESS, "resolved": SUCCESS,
        "occupied": ACCENT, "in progress": ACCENT,
        "pending": WARNING, "open": WARNING, "under maintenance": WARNING,
        "under review": ACCENT2, "partial": WARNING, "medium": WARNING,
        "overdue": DANGER, "terminated": DANGER, "expired": DANGER,
        "high": DANGER, "urgent": DANGER,
        "closed": TEXT_DIM, "low": SUCCESS,
    }

    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db    = db
        self._columns: list = []
        self._rows:    list = []
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        # ── header ──────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=DARK_BG, padx=28, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Data Explorer", font=FONT_HEAD,
                 bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text="Choose a table, then click any row to inspect every field as a detail card.",
                 font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")

        # ── table selector pills + export bar ────────────────────────
        pill_row = tk.Frame(self, bg=DARK_BG, padx=28)
        pill_row.pack(fill="x", pady=(0, 10))
        self._pill_btns = {}
        for key, label in self._TABLES:
            b = tk.Button(pill_row, text=label, font=FONT_SMALL,
                          relief="flat", bd=0, cursor="hand2",
                          padx=14, pady=6,
                          command=lambda k=key: self._load_table(k))
            b.pack(side="left", padx=(0, 6))
            self._pill_btns[key] = b
        self._refresh_pills(None)
        export_bar(pill_row, "PAMS_Data",
                   lambda: (self._columns, self._rows),
                   bg=DARK_BG).pack(side="right")

        # ── detail panel (fixed height, anchored to bottom) ──────────
        det = tk.Frame(self, bg=CARD_BG,
                       highlightbackground=BORDER, highlightthickness=1,
                       height=210)
        det.pack(side="bottom", fill="x", padx=20, pady=(0, 14))
        det.pack_propagate(False)

        det_hdr = tk.Frame(det, bg=HOVER_BG, height=32)
        det_hdr.pack(fill="x")
        det_hdr.pack_propagate(False)
        tk.Label(det_hdr, text="  ROW DETAIL",
                 font=("Segoe UI", 9, "bold"), bg=HOVER_BG, fg=TEXT_DIM
                 ).pack(side="left", pady=8)
        tk.Frame(det, bg=BORDER, height=1).pack(fill="x")

        self._detail_host = tk.Frame(det, bg=CARD_BG)
        self._detail_host.pack(fill="both", expand=True)
        self._detail_placeholder("Select a table above, then click a row to see its fields here.")

        # ── treeview area (fills remaining space) ────────────────────
        self._tree_area = tk.Frame(self, bg=DARK_BG)
        self._tree_area.pack(fill="both", expand=True, padx=20, pady=(0, 6))

    # ── pills ────────────────────────────────────────────────────────

    def _refresh_pills(self, active):
        for key, b in self._pill_btns.items():
            if key == active:
                b.config(bg=ACCENT, fg="white",
                         activebackground=ACCENT, activeforeground="white")
            else:
                b.config(bg=CARD_BG, fg=TEXT_DIM,
                         activebackground=HOVER_BG, activeforeground=TEXT)

    # ── detail panel helpers ─────────────────────────────────────────

    def _detail_placeholder(self, msg):
        for w in self._detail_host.winfo_children():
            w.destroy()
        tk.Label(self._detail_host, text=msg, font=FONT_BODY,
                 bg=CARD_BG, fg=TEXT_MUTED).pack(pady=24, padx=24, anchor="w")

    def _show_row_detail(self, columns, values):
        for w in self._detail_host.winfo_children():
            w.destroy()

        # Horizontally scrollable row of cards
        canvas = tk.Canvas(self._detail_host, bg=CARD_BG, highlightthickness=0)
        xsb = ttk.Scrollbar(self._detail_host, orient="horizontal",
                             command=canvas.xview)
        xsb.pack(side="bottom", fill="x")
        canvas.pack(fill="both", expand=True)
        canvas.configure(xscrollcommand=xsb.set)

        inner = tk.Frame(canvas, bg=CARD_BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, height=e.height))

        for col, raw in zip(columns, values):
            if col in self._MASKED:
                display, colour = "••••••••", TEXT_MUTED
            elif raw in (None, "", "None"):
                display, colour = "—", TEXT_MUTED
            else:
                display = str(raw)
                colour = self._STATUS_COLOURS.get(display.lower(), TEXT)

            card = tk.Frame(inner, bg=PANEL_BG,
                            highlightbackground=BORDER, highlightthickness=1,
                            width=165, height=130)
            card.pack(side="left", padx=8, pady=8)
            card.pack_propagate(False)

            tk.Label(card, text=col.replace("_", " ").upper(),
                     font=("Segoe UI", 8, "bold"), bg=PANEL_BG, fg=TEXT_MUTED
                     ).place(x=12, y=10)
            tk.Frame(card, bg=BORDER, height=1).place(x=12, y=32, width=141)
            tk.Label(card, text=display,
                     font=("Segoe UI", 11, "bold"), bg=PANEL_BG, fg=colour,
                     wraplength=141, justify="left"
                     ).place(x=12, y=42)

    # ── load table ───────────────────────────────────────────────────

    def _load_table(self, table_name):
        self._refresh_pills(table_name)
        self._detail_placeholder("Click a row to inspect it.")

        for w in self._tree_area.winfo_children():
            w.destroy()

        loc_id = None if self.staff.is_manager() else self.staff.location_id
        try:
            columns, rows = self.db.get_table_data(table_name, location_id=loc_id)
        except Exception as ex:
            self._columns, self._rows = [], []
            tk.Label(self._tree_area, text=f"Error loading table: {ex}",
                     font=FONT_BODY, bg=DARK_BG, fg=DANGER).pack(pady=30)
            return

        self._columns, self._rows = columns, rows

        if not rows:
            tk.Label(self._tree_area, text="No records found for this table.",
                     font=FONT_BODY, bg=DARK_BG, fg=TEXT_MUTED).pack(pady=30)
            return

        # Card wrapper for the treeview
        card = tk.Frame(self._tree_area, bg=CARD_BG,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ysb = ttk.Scrollbar(card, orient="vertical")
        ysb.pack(side="right", fill="y")
        xsb = ttk.Scrollbar(card, orient="horizontal")
        xsb.pack(side="bottom", fill="x")

        tree = ttk.Treeview(card, columns=columns, show="headings",
                            yscrollcommand=ysb.set, xscrollcommand=xsb.set,
                            selectmode="browse")
        tree.pack(fill="both", expand=True)
        ysb.config(command=tree.yview)
        xsb.config(command=tree.xview)

        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=130, anchor="w", minwidth=70, stretch=True)

        for row in rows:
            tree.insert("", "end", values=row)

        tree.bind("<<TreeviewSelect>>",
                  lambda e, t=tree, c=columns: self._on_select(t, c))

    def _on_select(self, tree, columns):
        sel = tree.selection()
        if not sel:
            return
        values = tree.item(sel[0], "values")
        self._show_row_detail(columns, values)


class LoginView(tk.Frame):
    _NAVY  = "#0F172A"
    _NAVY2 = "#1E293B"
    _PALE  = "#94A3B8"
    _DIM   = "#BFDBFE"

    def __init__(self, parent, on_login):
        super().__init__(parent, bg=self._NAVY)
        self.on_login = on_login
        self.pack(fill="both", expand=True)
        self._build_left()
        self._build_right()

    # ── left panel ───────────────────────────────────────────────────
    def _build_left(self):
        N, N2, P = self._NAVY, self._NAVY2, self._PALE
        pnl = tk.Frame(self, bg=N, width=390)
        pnl.pack(side="left", fill="y")
        pnl.pack_propagate(False)

        top = tk.Frame(pnl, bg=N, padx=44)
        top.pack(fill="x", pady=(64, 0))
        logo = tk.Frame(top, bg=ACCENT, width=52, height=52)
        logo.pack(anchor="w")
        logo.pack_propagate(False)
        tk.Label(logo, text="🏢", font=("Segoe UI Emoji", 22), bg=ACCENT, fg="white").pack(expand=True)

        tk.Label(pnl, text="PAMS", font=("Segoe UI", 27, "bold"),
                 bg=N, fg="white").pack(anchor="w", padx=44, pady=(18, 2))
        tk.Label(pnl, text="Paragon Apartment\nManagement System",
                 font=("Segoe UI", 10), bg=N, fg=P, justify="left").pack(anchor="w", padx=44)

        tk.Frame(pnl, bg=N2, height=1).pack(fill="x", padx=44, pady=30)

        features = [
            ("🏠", "Apartment Grid Overview",  "All units across every location"),
            ("📋", "Lease & Tenant Records",    "Full lifecycle management"),
            ("💳", "Payment & Billing",          "Invoices, overdue and reports"),
            ("🔧", "Maintenance & Complaints",  "Log, assign and resolve issues"),
        ]
        for icon, title, sub in features:
            row = tk.Frame(pnl, bg=N, padx=44)
            row.pack(fill="x", pady=10)
            ib = tk.Frame(row, bg=N2, width=40, height=40)
            ib.pack(side="left", padx=(0, 14))
            ib.pack_propagate(False)
            tk.Label(ib, text=icon, font=("Segoe UI Emoji", 16),
                     bg=N2, fg="white").pack(expand=True)
            col = tk.Frame(row, bg=N)
            col.pack(side="left", fill="x", expand=True)
            tk.Label(col, text=title, font=("Segoe UI", 10, "bold"),
                     bg=N, fg="white").pack(anchor="w")
            tk.Label(col, text=sub, font=("Segoe UI", 9),
                     bg=N, fg=P).pack(anchor="w", pady=(1, 0))

        tk.Frame(pnl, bg=N).pack(fill="both", expand=True)
        bar = tk.Frame(pnl, bg=ACCENT, padx=44, pady=22)
        bar.pack(fill="x")
        tk.Label(bar, text="Trusted by property managers",
                 font=("Segoe UI", 10, "bold"), bg=ACCENT, fg="white").pack(anchor="w")
        tk.Label(bar, text="Bristol  ·  Cardiff  ·  London  ·  Manchester",
                 font=("Segoe UI", 9), bg=ACCENT, fg=self._DIM).pack(anchor="w", pady=(4, 0))

    # ── right panel ──────────────────────────────────────────────────
    def _build_right(self):
        right = tk.Frame(self, bg="#F1F5F9")
        right.pack(side="left", fill="both", expand=True)

        # Wrapper gives the card a solid blue top edge
        wrap = tk.Frame(right, bg=ACCENT,
                        highlightbackground="#CBD5E1", highlightthickness=1)
        wrap.place(relx=0.5, rely=0.5, anchor="center")
        tk.Frame(wrap, bg=ACCENT, height=5).pack(fill="x")

        card = tk.Frame(wrap, bg=PANEL_BG, padx=52, pady=44)
        card.pack()

        tk.Label(card, text="Welcome back",
                 font=FONT_HEAD, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text="Sign in to your PAMS account",
                 font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 28))

        def field(lbl, show=None):
            tk.Label(card, text=lbl, font=("Segoe UI", 9, "bold"),
                     bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
            var = tk.StringVar()
            kw = {"show": show} if show else {}
            e = tk.Entry(card, textvariable=var, font=FONT_BODY, bg="#F8FAFC", fg=TEXT,
                         insertbackground=TEXT, relief="flat", bd=0, width=30,
                         highlightthickness=1, highlightcolor=ACCENT,
                         highlightbackground="#CBD5E1", **kw)
            e.pack(fill="x", pady=(6, 18), ipady=10, padx=2)
            return var, e

        self.v_user, self.e_user = field("USERNAME")
        self.v_pass, self.e_pass = field("PASSWORD", show="●")

        self.err = tk.Label(card, text="", font=FONT_SMALL, bg=PANEL_BG, fg=DANGER)
        self.err.pack(anchor="w", pady=(0, 8))

        btn = tk.Button(card, text="Sign In  →", command=self._go,
                        bg=ACCENT, fg="white", font=("Segoe UI", 11, "bold"),
                        relief="flat", bd=0, cursor="hand2",
                        padx=16, pady=13,
                        activebackground="#1D4ED8", activeforeground="white", width=28)
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg="#1D4ED8"))
        btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT))

        tk.Label(card, text="Demo  ·  frontdesk1 / password123",
                 font=("Segoe UI", 8), bg=PANEL_BG, fg=TEXT_MUTED).pack(pady=(16, 0))

        self.e_user.bind("<Return>", lambda e: self.e_pass.focus())
        self.e_pass.bind("<Return>", lambda e: self._go())
        self.e_user.focus()

    def _go(self): self.on_login(self.v_user.get().strip(), self.v_pass.get())
    def show_error(self, msg): self.err.config(text=msg)


# ══════════════════════════════════════════════════════════════════════════════
#  BASE APP SHELL  (abstract)
# ══════════════════════════════════════════════════════════════════════════════

class BaseAppShell(tk.Frame, ABC):
    """
    Abstract base class for all role-specific application shells.

    Enforces a consistent layout: sidebar (role-specific) + content area.
    Concrete subclasses must implement:
      - _build_sidebar() : construct the navigation panel for their role
      - _go(dest)        : map destination string to the correct view class

    Shared behaviour provided here:
      - _nav()    : highlight the active button and delegate to _go()
      - _clear()  : wipe the content area before loading a new view
      - _logout() : confirm and return to the login screen
    """

    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._nbtn: dict = {}
        self._nbar: dict = {}
        self.pack(fill="both", expand=True)
        self._build_sidebar()
        self.content = tk.Frame(self, bg=DARK_BG)
        self.content.pack(side="left", fill="both", expand=True)

    @abstractmethod
    def _build_sidebar(self):
        """Build the role-specific navigation sidebar."""

    @abstractmethod
    def _go(self, dest: str):
        """Load the view that corresponds to the given destination key."""

    def _nav(self, key: str, dest: str):
        """Highlight the active nav button then navigate to dest."""
        for k, b in self._nbtn.items():
            b.config(bg=PANEL_BG, fg=TEXT_DIM)
            self._nbar[k].config(bg=PANEL_BG)
        self._nbtn[key].config(bg=HOVER_BG, fg=TEXT)
        self._nbar[key].config(bg=ACCENT)
        self._go(dest)

    def _clear(self):
        """Remove all widgets from the content area."""
        for w in self.content.winfo_children():
            w.destroy()

    def _logout(self):
        if messagebox.askyesno("Sign Out", "Sign out of PAMS?", parent=self):
            self.destroy()
            self.master.show_login()


# ══════════════════════════════════════════════════════════════════════════════
#  APP SHELL  — Front-Desk / default role
# ══════════════════════════════════════════════════════════════════════════════

class AppShell(BaseAppShell):
    """Concrete shell for Front-Desk staff."""

    def __init__(self, parent, staff, db):
        super().__init__(parent, staff, db)
        self._nav("commune", "commune")

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=PANEL_BG, width=210,
                      highlightbackground=BORDER, highlightthickness=1)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Label(sb, text="🏢  PAMS", font=("Segoe UI", 12, "bold"),
                 bg=PANEL_BG, fg=TEXT).pack(padx=20, pady=(22, 10), anchor="w")
        uc = tk.Frame(sb, bg=HOVER_BG, padx=14, pady=10)
        uc.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(uc, text=self.staff.full_name, font=FONT_SUB, bg=HOVER_BG, fg=TEXT).pack(anchor="w")
        badge(uc, self.staff.role, ACCENT).pack(anchor="w", pady=(4, 0))

        for key, label, dest in [
            ("commune",        "🏠  Apartments",           "commune"),
            ("reg_tenant",     "👤  Register Tenant",      "reg_tenant"),
            ("tenant_records", "📋  Tenant Records",       "tenant_records"),
            ("log_complaint",  "💬  Log Complaint",        "log_complaint"),
            ("log_maint",      "🔧  Log Maintenance",      "log_maint"),
            ("maint_requests", "🛠  Maintenance Requests", "maint_requests"),
        ]:
            row = tk.Frame(sb, bg=PANEL_BG)
            row.pack(fill="x")
            bar = tk.Frame(row, bg=PANEL_BG, width=3)
            bar.pack(side="left", fill="y")
            b = tk.Button(row, text=label, font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, anchor="w", padx=15, pady=11,
                          cursor="hand2", activebackground=HOVER_BG, activeforeground=TEXT,
                          command=lambda d=dest, k=key: self._nav(k, d))
            b.pack(side="left", fill="x", expand=True)
            self._nbtn[key] = b
            self._nbar[key] = bar

        tk.Frame(sb, bg=PANEL_BG).pack(fill="both", expand=True)
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=10)
        _so = tk.Button(sb, text="⬅  Sign Out", font=FONT_SMALL, bg=PANEL_BG, fg=DANGER,
                        relief="flat", bd=0, anchor="w", padx=18, pady=12,
                        cursor="hand2", activebackground="#FEE2E2", activeforeground=DANGER,
                        command=self._logout)
        _so.pack(fill="x")
        _so.bind("<Enter>", lambda e: _so.config(bg="#FEE2E2"))
        _so.bind("<Leave>", lambda e: _so.config(bg=PANEL_BG))

    def _go(self, dest: str):
        self._clear()
        if dest == "commune":
            CommuneView(self.content, self.staff, self.db)
        elif dest == "reg_tenant":
            RegisterTenantView(self.content, self.staff, self.db,
                               on_complete=lambda: self._nav("tenant_records", "tenant_records"))
        elif dest == "tenant_records":
            TenantRecordsView(self.content, self.staff, self.db)
        elif dest == "log_complaint":
            LogComplaintView(self.content, self.staff, self.db,
                             on_complete=lambda: self._nav("commune", "commune"))
        elif dest == "log_maint":
            from views.views_maintenance import AddRequestView
            AddRequestView(self.content, self.staff, self.db,
                           on_complete=lambda: self._nav("maint_requests", "maint_requests"))
        elif dest == "maint_requests":
            from views.views_maintenance import RequestsView
            RequestsView(self.content, self.staff, self.db)


# ══════════════════════════════════════════════════════════════════════════════
#  COMMUNE VIEW  — apartment grid with live filter
# ══════════════════════════════════════════════════════════════════════════════
class CommuneView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._all: List[Apartment] = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _build(self):
        # top bar
        top = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        top.pack(fill="x")
        lft = tk.Frame(top, bg=DARK_BG)
        lft.pack(side="left", fill="x", expand=True)
        tk.Label(lft, text="Apartments", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(lft, text="All units at your location — click any card to view full records.",
                 font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")
        self.stat_row = tk.Frame(top, bg=DARK_BG)
        self.stat_row.pack(side="right")

        # filter bar
        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0,10))
        self.sv = tk.StringVar()
        se = tk.Entry(fbar, textvariable=self.sv, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                      insertbackground=TEXT, relief="flat", bd=0, width=34,
                      highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        se.pack(side="left", ipady=7, ipadx=10)
        placeholder = "Search unit, type, city, status..."
        se.insert(0, placeholder)
        se.bind("<FocusIn>",  lambda e: se.delete(0,"end") if se.get()==placeholder else None)
        se.bind("<FocusOut>", lambda e: se.insert(0,placeholder) if se.get()=="" else None)
        self.sv.trace("w", lambda *a: self._filter())

        tk.Label(fbar, text="  Filter:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left", padx=(14,8))
        self._sf = tk.StringVar(value="All")
        self._fbtns = {}
        for s, c in [("All",TEXT_DIM),("Available",SUCCESS),("Occupied",ACCENT),("Under Maintenance",WARNING)]:
            btn = tk.Button(fbar, text=s, font=FONT_SMALL, relief="flat", bd=0,
                            padx=10, pady=4, cursor="hand2", highlightthickness=1,
                            command=lambda s=s: self._set_filter(s))
            btn.pack(side="left", padx=(0,4))
            self._fbtns[s] = (btn, c)
        self._refresh_filter_btns()

        # scrollable grid
        outer, self.grid_inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0,16))

    def _load(self):
        self._all = self.db.get_all_apartments(self.staff.location_id)
        self._render_stats()
        self._filter()

    def _render_stats(self):
        for w in self.stat_row.winfo_children(): w.destroy()
        tot = len(self._all)
        avail = sum(1 for a in self._all if a.status=="Available")
        occ   = sum(1 for a in self._all if a.status=="Occupied")
        maint = sum(1 for a in self._all if a.status=="Under Maintenance")
        for label, val, color in [("Total",tot,TEXT),("Available",avail,SUCCESS),
                                   ("Occupied",occ,ACCENT),("Maintenance",maint,WARNING)]:
            p = tk.Frame(self.stat_row, bg=CARD_BG, padx=14, pady=8,
                         highlightbackground=BORDER, highlightthickness=1)
            p.pack(side="left", padx=(0,8))
            tk.Label(p, text=str(val), font=("Segoe UI",16,"bold"), bg=CARD_BG, fg=color).pack()
            tk.Label(p, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

    def _set_filter(self, value):
        self._sf.set(value)
        self._refresh_filter_btns()
        self._filter()

    def _refresh_filter_btns(self):
        active = self._sf.get()
        for s, (btn, c) in self._fbtns.items():
            if s == active:
                btn.config(bg=c, fg="white", highlightbackground=c)
            else:
                btn.config(bg=DARK_BG, fg=c, highlightbackground=BORDER)

    def _filter(self):
        q = self.sv.get().strip().lower()
        if "search" in q: q = ""
        sf = self._sf.get()
        filtered = [
            a for a in self._all
            if (not q or q in a.unit_number.lower() or q in a.apartment_type.lower()
                or q in (a.location_city or "").lower() or q in (a.status or "").lower()
                or q in (a.description or "").lower())
            and (sf=="All" or a.status==sf)
        ]
        self._render_grid(filtered)

    def _render_grid(self, apts):
        for w in self.grid_inner.winfo_children(): w.destroy()
        if not apts:
            tk.Label(self.grid_inner, text="No apartments match your search.",
                     font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(pady=40)
            return
        COLS = 3
        for i, apt in enumerate(apts):
            r, c = divmod(i, COLS)
            self._apt_card(apt, r, c)
        for c in range(COLS):
            self.grid_inner.columnconfigure(c, weight=1, uniform="col")

    def _apt_card(self, apt: Apartment, row, col):
        color = sc(apt.status)
        outer = tk.Frame(self.grid_inner, bg=CARD_BG, cursor="hand2",
                         highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        tk.Frame(outer, bg=color, height=4).pack(fill="x")

        body = tk.Frame(outer, bg=CARD_BG, padx=16, pady=14)
        body.pack(fill="both", expand=True)

        head = tk.Frame(body, bg=CARD_BG)
        head.pack(fill="x")
        tk.Label(head, text=f"Unit {apt.unit_number}", font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        badge(head, apt.status).pack(side="right")

        tk.Label(body, text=f"📍 {apt.location_city}  •  {apt.location_address}",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4,0))

        specs = f"{apt.apartment_type}  •  {apt.num_bedrooms}bd/{apt.num_bathrooms}ba"
        if apt.size_sqft: specs += f"  •  {apt.size_sqft:.0f} sq ft"
        tk.Label(body, text=specs, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")

        pills = tk.Frame(body, bg=CARD_BG)
        pills.pack(anchor="w", pady=(6,0))
        if apt.furnished: tk.Label(pills, text=" Furnished ", font=FONT_SMALL, bg=ACCENT2, fg="white", padx=6, pady=2).pack(side="left", padx=(0,4))
        if apt.parking:   tk.Label(pills, text=" Parking ",   font=FONT_SMALL, bg=ACCENT,  fg="white", padx=6, pady=2).pack(side="left")

        foot = tk.Frame(body, bg=CARD_BG)
        foot.pack(fill="x", pady=(10,0))
        tk.Label(foot, text=f"£{apt.monthly_rent:,.0f}/mo", font=("Segoe UI",13,"bold"),
                 bg=CARD_BG, fg=ACCENT).pack(side="left")
        tk.Label(foot, text=f"Floor {apt.floor}", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MUTED).pack(side="right")

        def click(e=None, a=apt): ApartmentDetailWindow(self, a, self.staff, self.db)
        def _bind(w):
            try: w.bind("<Button-1>", click)
            except Exception: pass
            for child in w.winfo_children(): _bind(child)
        _bind(outer)

        outer.bind("<Enter>", lambda e: outer.config(highlightbackground=ACCENT, highlightthickness=2))
        outer.bind("<Leave>", lambda e: outer.config(highlightbackground=BORDER, highlightthickness=1))


# ══════════════════════════════════════════════════════════════════════════════
#  APARTMENT DETAIL WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class ApartmentDetailWindow(tk.Toplevel):
    def __init__(self, parent, apt: Apartment, staff, db):
        super().__init__(parent)
        self.apt = apt
        self.staff = staff
        self.db = db
        self.title(f"Unit {apt.unit_number}  —  {apt.location_city}")
        self.geometry("1000x700")
        self.configure(bg=DARK_BG)
        self._nb_style()
        self._build()

    def _nb_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("D.TNotebook", background=DARK_BG, borderwidth=0, tabmargins=0)
        s.configure("D.TNotebook.Tab", background=PANEL_BG, foreground=TEXT_DIM,
                    font=FONT_BODY, padding=[18,8])
        s.map("D.TNotebook.Tab", background=[("selected",CARD_BG)],
              foreground=[("selected",TEXT)])

    def _build(self):
        color = sc(self.apt.status)
        # Header
        hdr = tk.Frame(self, bg=PANEL_BG)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=color, height=4).pack(fill="x")
        ih = tk.Frame(hdr, bg=PANEL_BG, padx=28, pady=18)
        ih.pack(fill="x")
        lh = tk.Frame(ih, bg=PANEL_BG)
        lh.pack(side="left")
        tk.Label(lh, text=f"Unit {self.apt.unit_number}", font=FONT_HEAD, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(lh, text=f"📍 {self.apt.location_city}  •  {self.apt.location_address}  •  {self.apt.apartment_type}",
                 font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
        rh = tk.Frame(ih, bg=PANEL_BG)
        rh.pack(side="right")
        badge(rh, self.apt.status).pack()
        tk.Label(rh, text=f"£{self.apt.monthly_rent:,.0f}/mo",
                 font=("Segoe UI",15,"bold"), bg=PANEL_BG, fg=ACCENT).pack(pady=(6,0))

        nb = ttk.Notebook(self, style="D.TNotebook")
        nb.pack(fill="both", expand=True)
        self._tab_overview(nb)
        self._tab_lease(nb)
        self._tab_payments(nb)
        self._tab_maintenance(nb)
        self._tab_complaints(nb)

    def _tab(self, nb, title):
        f = tk.Frame(nb, bg=CARD_BG)
        nb.add(f, text=f"  {title}  ")
        return f

    # ── Overview ──────────────────────────────────────────────────────────────
    def _tab_overview(self, nb):
        frame = self._tab(nb, "Overview")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)
        a = self.apt
        sec_hdr(inner, "Apartment Details")
        info_grid(inner, [
            ("Unit", a.unit_number), ("Type", a.apartment_type), ("Status", a.status),
            ("Bedrooms", a.num_bedrooms), ("Bathrooms", a.num_bathrooms), ("Floor", a.floor),
            ("Size", f"{a.size_sqft:.0f} sq ft" if a.size_sqft else "—"),
            ("Monthly Rent", f"£{a.monthly_rent:,.2f}"),
            ("Furnished", "Yes" if a.furnished else "No"),
            ("Parking", "Yes" if a.parking else "No"),
        ], cols=4)
        sec_hdr(inner, "Location")
        info_grid(inner, [("City", a.location_city), ("Address", a.location_address)], cols=3)
        if a.description:
            sec_hdr(inner, "Description")
            tk.Label(inner, text=a.description, font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM,
                     wraplength=800, justify="left").pack(anchor="w", padx=28, pady=(0,16))

    # ── Lease & Tenant ────────────────────────────────────────────────────────
    def _tab_lease(self, nb):
        frame = self._tab(nb, "Lease & Tenant")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        active = self.db.get_active_lease_for_apartment(self.apt.id)
        all_ls = self.db.get_all_leases_for_apartment(self.apt.id)

        sec_hdr(inner, "Current Lease")
        if not active:
            tk.Label(inner, text="No active lease for this apartment.",
                     font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM).pack(padx=28, pady=8, anchor="w")
        else:
            l = active
            info_grid(inner, [
                ("Lease ID", f"#{l.id}"), ("Start Date", l.start_date),
                ("End Date", l.end_date), ("Monthly Rent", f"£{l.monthly_rent:,.2f}"),
                ("Deposit", f"£{l.deposit_amount:,.2f}"), ("Status", l.status),
            ], cols=3)

            is_frontdesk = self.staff.role == "Front Desk"
            ar = tk.Frame(inner, bg=CARD_BG)
            ar.pack(fill="x", padx=28, pady=(0,8))
            if is_frontdesk:
                mkbtn(ar, "Register Complaint",
                      lambda: ComplaintDialog(self, l, self.staff, self.db), color=WARNING, small=True).pack(side="left", padx=(0,8))
                mkbtn(ar, "Send Payment Request",
                      lambda: PaymentRequestDialog(self, l, self.staff, self.db), small=True).pack(side="left")
                if not l.early_termination_requested:
                    mkbtn(ar, "⚠  Early Termination",
                          lambda lease=l: EarlyTerminationDialog(
                              self, lease, self.db, on_save=self.destroy
                          ),
                          color=DANGER, small=True).pack(side="right")

            tenant = self.db.get_tenant_by_id(l.tenant_id)
            if tenant:
                sec_hdr(inner, "Current Tenant")
                er = tk.Frame(inner, bg=CARD_BG)
                er.pack(fill="x", padx=28, pady=(0,4))
                if is_frontdesk:
                    mkbtn(er, "✏  Edit Tenant",
                          lambda t=tenant: EditTenantDialog(self, t, self.db), color=ACCENT2, small=True).pack(side="right")
                info_grid(inner, [
                    ("Full Name", tenant.full_name), ("NI Number", tenant.ni_number),
                    ("Date of Birth", tenant.date_of_birth or "—"),
                    ("Phone", tenant.phone), ("Email", tenant.email), ("Occupation", tenant.occupation),
                    ("Emergency Contact", tenant.emergency_contact_name or "—"),
                    ("Emergency Phone",   tenant.emergency_contact_phone or "—"),
                ], cols=3)
                for i, (n, p, e) in enumerate([
                    (tenant.reference1_name, tenant.reference1_phone, tenant.reference1_email),
                    (tenant.reference2_name, tenant.reference2_phone, tenant.reference2_email),
                ]):
                    if n:
                        if i == 0: sec_hdr(inner, "References")
                        rf = tk.Frame(inner, bg=CARD_BG)
                        rf.pack(fill="x", padx=28, pady=2)
                        tk.Label(rf, text=f"Ref {i+1}:", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
                        tk.Label(rf, text=f"  {n}  |  {p or '—'}  |  {e or '—'}",
                                 font=FONT_BODY, bg=CARD_BG, fg=TEXT).pack(side="left")
                if tenant.notes:
                    sec_hdr(inner, "Tenant Notes")
                    tk.Label(inner, text=tenant.notes, font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM,
                             wraplength=800, justify="left").pack(anchor="w", padx=28, pady=(0,16))

        history = [l for l in all_ls if not active or l.id != active.id]
        if history:
            sec_hdr(inner, "Lease History")
            for hl in history:
                hc = tk.Frame(inner, bg=PANEL_BG, padx=16, pady=10)
                hc.pack(fill="x", padx=24, pady=3)
                t = tk.Frame(hc, bg=PANEL_BG)
                t.pack(fill="x")
                tk.Label(t, text=f"Lease #{hl.id}  —  {hl.tenant_name}", font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
                badge(t, hl.status).pack(side="right")
                tk.Label(hc, text=f"{hl.start_date}  →  {hl.end_date}  •  £{hl.monthly_rent:,.0f}/mo",
                         font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")

    # ── Payments ──────────────────────────────────────────────────────────────
    def _tab_payments(self, nb):
        frame = self._tab(nb, "Payments")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        active = self.db.get_active_lease_for_apartment(self.apt.id)
        ar = tk.Frame(inner, bg=CARD_BG)
        ar.pack(fill="x", padx=24, pady=(16,4))
        if active and self.staff.role == "Front Desk":
            mkbtn(ar, "＋  Send Payment Request",
                  lambda: PaymentRequestDialog(self, active, self.staff, self.db,
                                               on_save=lambda: self._repaint_payments(inner)),
                  small=True).pack(side="right")

        self._repaint_payments(inner)

    def _repaint_payments(self, inner):
        for w in inner.winfo_children():
            if getattr(w, "_pr", False): w.destroy()

        payments = self.db.get_payments_for_apartment(self.apt.id)
        if not payments:
            lbl = tk.Label(inner, text="No payment records for this apartment.",
                           font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM)
            lbl._pr = True
            lbl.pack(pady=20)
            return

        sh = tk.Frame(inner, bg=CARD_BG); sh._pr = True
        sh.pack(fill="x", padx=24, pady=(20,6))
        tk.Label(sh, text=f"Payment History  ({len(payments)} records)",
                 font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        tk.Frame(sh, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(10,0), pady=5)

        hdrf = tk.Frame(inner, bg=PANEL_BG); hdrf._pr = True
        hdrf.pack(fill="x", padx=24, pady=(4,0))
        for col_text, w in [("Reference",14),("Due Date",12),("Amount Due",12),
                              ("Paid",12),("Status",12),("Paid On",12),("Notes",20)]:
            tk.Label(hdrf, text=col_text, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                     width=w, anchor="w").pack(side="left", padx=4, pady=6)

        for pay in payments:
            row = tk.Frame(inner, bg=CARD_BG); row._pr = True
            row.pack(fill="x", padx=24)
            for val, w in [(pay.reference_number or "—",14),(pay.due_date or "—",12),
                           (f"£{pay.amount_due:,.2f}",12),(f"£{pay.amount_paid:,.2f}",12),
                           (pay.status,12),(pay.paid_date or "—",12),(pay.notes or "—",20)]:
                color = sc(val) if val == pay.status else TEXT
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=color,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            sep = tk.Frame(inner, bg=BORDER, height=1); sep._pr = True
            sep.pack(fill="x", padx=24)

        # summary
        total_due  = sum(p.amount_due for p in payments)
        total_paid = sum(p.amount_paid for p in payments)
        pending    = sum(p.amount_due - p.amount_paid for p in payments if p.status != "Paid")
        sr = tk.Frame(inner, bg=PANEL_BG, padx=24, pady=10); sr._pr = True
        sr.pack(fill="x", padx=24, pady=(4,0))
        for lbl, val, col in [("Total Billed:", f"£{total_due:,.2f}", TEXT),
                               ("Collected:", f"£{total_paid:,.2f}", SUCCESS),
                               ("Outstanding:", f"£{pending:,.2f}", DANGER if pending>0 else TEXT_DIM)]:
            tk.Label(sr, text=lbl, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(side="left", padx=(0,4))
            tk.Label(sr, text=val, font=FONT_SUB,   bg=PANEL_BG, fg=col).pack(side="left", padx=(0,20))

    # ── Maintenance ───────────────────────────────────────────────────────────
    def _tab_maintenance(self, nb):
        frame = self._tab(nb, "Maintenance")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        reqs = self.db.get_maintenance_for_apartment(self.apt.id)
        sec_hdr(inner, f"Maintenance Requests  ({len(reqs)} records)")
        if not reqs:
            tk.Label(inner, text="No maintenance requests for this apartment.",
                     font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM).pack(padx=28, pady=8, anchor="w")
            return

        for req in reqs:
            card = tk.Frame(inner, bg=PANEL_BG, padx=16, pady=12)
            card.pack(fill="x", padx=24, pady=4)
            top = tk.Frame(card, bg=PANEL_BG)
            top.pack(fill="x")
            tk.Label(top, text=req.title, font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
            badge(top, req.status).pack(side="right")
            badge(top, req.priority).pack(side="right", padx=(0,6))

            meta = []
            if req.category:       meta.append(req.category)
            if req.reported_date:  meta.append(f"Reported: {req.reported_date}")
            if req.scheduled_date: meta.append(f"Scheduled: {req.scheduled_date}")
            if req.resolved_date:  meta.append(f"Resolved: {req.resolved_date}")
            if meta:
                tk.Label(card, text="  •  ".join(meta), font=FONT_SMALL,
                         bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4,0))
            if req.description:
                tk.Label(card, text=req.description, font=FONT_BODY, bg=PANEL_BG,
                         fg=TEXT, wraplength=750).pack(anchor="w", pady=(4,0))
            if req.cost or req.time_taken_hours:
                cr = tk.Frame(card, bg=PANEL_BG)
                cr.pack(anchor="w", pady=(4,0))
                if req.cost:
                    tk.Label(cr, text=f"💷 £{req.cost:,.2f}", font=FONT_SMALL,
                             bg=PANEL_BG, fg=TEXT_DIM).pack(side="left", padx=(0,16))
                if req.time_taken_hours:
                    tk.Label(cr, text=f"⏱ {req.time_taken_hours:.1f} hrs", font=FONT_SMALL,
                             bg=PANEL_BG, fg=TEXT_DIM).pack(side="left")
            if req.resolution_notes:
                tk.Label(card, text=f"Resolution: {req.resolution_notes}", font=FONT_SMALL,
                         bg=PANEL_BG, fg=SUCCESS, wraplength=750).pack(anchor="w", pady=(4,0))

    # ── Complaints ────────────────────────────────────────────────────────────
    def _tab_complaints(self, nb):
        frame = self._tab(nb, "Complaints")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        active = self.db.get_active_lease_for_apartment(self.apt.id)
        ar = tk.Frame(inner, bg=CARD_BG)
        ar.pack(fill="x", padx=24, pady=(16,4))
        if active and self.staff.role == "Front Desk":
            mkbtn(ar, "＋  Register Complaint",
                  lambda: ComplaintDialog(self, active, self.staff, self.db,
                                          on_save=lambda: self._repaint_complaints(inner)),
                  color=WARNING, small=True).pack(side="right")

        self._repaint_complaints(inner)

    def _repaint_complaints(self, inner):
        for w in inner.winfo_children():
            if getattr(w, "_cp", False): w.destroy()

        complaints = self.db.get_complaints_for_apartment(self.apt.id)
        sh = tk.Frame(inner, bg=CARD_BG); sh._cp = True
        sh.pack(fill="x", padx=24, pady=(20,6))
        tk.Label(sh, text=f"Complaints  ({len(complaints)} records)",
                 font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        tk.Frame(sh, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(10,0), pady=5)

        if not complaints:
            lbl = tk.Label(inner, text="No complaints registered for this apartment.",
                           font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM)
            lbl._cp = True
            lbl.pack(padx=28, pady=8, anchor="w")
            return

        for c in complaints:
            card = tk.Frame(inner, bg=PANEL_BG, padx=16, pady=12); card._cp = True
            card.pack(fill="x", padx=24, pady=4)
            top = tk.Frame(card, bg=PANEL_BG)
            top.pack(fill="x")
            tk.Label(top, text=c.title, font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
            badge(top, c.status).pack(side="right")
            meta = []
            if c.category:     meta.append(c.category)
            if c.tenant_name:  meta.append(f"By: {c.tenant_name}")
            if c.reported_date:meta.append(f"Reported: {c.reported_date}")
            if c.resolved_date:meta.append(f"Resolved: {c.resolved_date}")
            if meta:
                tk.Label(card, text="  •  ".join(meta), font=FONT_SMALL,
                         bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4,0))
            if c.description:
                tk.Label(card, text=c.description, font=FONT_BODY, bg=PANEL_BG,
                         fg=TEXT, wraplength=750).pack(anchor="w", pady=(4,0))
            if c.resolution_notes:
                tk.Label(card, text=f"Resolution: {c.resolution_notes}", font=FONT_SMALL,
                         bg=PANEL_BG, fg=SUCCESS, wraplength=750).pack(anchor="w", pady=(4,0))


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE LEASE WIZARD
# ══════════════════════════════════════════════════════════════════════════════
class CreateLeaseWizard(tk.Frame):
    def __init__(self, parent, staff, db, on_complete=None):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.on_complete = on_complete
        self.step = 0
        self.tenant_data = {}
        self.selected_apt: Optional[Apartment] = None
        self.lease_start = ""
        self.lease_end = ""
        self.pack(fill="both", expand=True)
        self._shell()
        self._show(0)

    def _shell(self):
        hdr = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Create New Lease", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        self.step_row = tk.Frame(hdr, bg=DARK_BG)
        self.step_row.pack(anchor="w", pady=(14,0))
        self._step_widgets = []
        self._step_connectors = []
        for i, s in enumerate(["Tenant Info", "Select Apartment", "Confirm & Send"]):
            col = tk.Frame(self.step_row, bg=DARK_BG)
            col.pack(side="left")
            circ = tk.Canvas(col, width=28, height=28, bg=DARK_BG, highlightthickness=0)
            circ.pack()
            lbl = tk.Label(col, text=s, font=FONT_SMALL, bg=DARK_BG, fg=TEXT_MUTED)
            lbl.pack(pady=(4,0))
            self._step_widgets.append((circ, lbl))
            if i < 2:
                gap = tk.Frame(self.step_row, bg=DARK_BG)
                gap.pack(side="left", padx=6)
                conn = tk.Frame(gap, bg=BORDER, height=2, width=52)
                conn.pack(pady=(0,20))
                self._step_connectors.append(conn)
        self.body = tk.Frame(self, bg=DARK_BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=4)

    def _update_steps(self):
        for i, (circ, lbl) in enumerate(self._step_widgets):
            circ.delete("all")
            if i < self.step:
                circ.create_oval(2, 2, 26, 26, fill=SUCCESS, outline="")
                circ.create_text(14, 14, text="✓", fill="white", font=("Segoe UI", 10, "bold"))
                lbl.config(fg=SUCCESS)
            elif i == self.step:
                circ.create_oval(2, 2, 26, 26, fill=ACCENT, outline="")
                circ.create_text(14, 14, text=str(i+1), fill="white", font=("Segoe UI", 10, "bold"))
                lbl.config(fg=ACCENT)
            else:
                circ.create_oval(2, 2, 26, 26, fill="", outline=BORDER, width=2)
                circ.create_text(14, 14, text=str(i+1), fill=TEXT_MUTED, font=("Segoe UI", 9))
                lbl.config(fg=TEXT_MUTED)
        for i, conn in enumerate(self._step_connectors):
            conn.config(bg=SUCCESS if self.step > i else BORDER)

    def _show(self, s):
        self.step = s
        self._update_steps()
        for w in self.body.winfo_children(): w.destroy()
        [self._s1, self._s2, self._s3][s]()

    # Step 1 ──────────────────────────────────────────────────────────────────
    def _s1(self):
        outer, inner = scrollable(self.body, CARD_BG)
        outer.pack(fill="both", expand=True)
        inner.config(padx=32, pady=24)

        tk.Label(inner, text="Tenant Information", font=FONT_TITLE, bg=CARD_BG, fg=TEXT
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,16))

        def slbl(row, txt):
            wrap = tk.Frame(inner, bg=CARD_BG)
            wrap.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(20,6), padx=6)
            tk.Frame(wrap, bg=ACCENT, width=3).pack(side="left", fill="y", padx=(0,8))
            tk.Label(wrap, text=txt, font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")

        slbl(1, "Personal Details")
        td = self.tenant_data
        self.ni  = entry_var(inner, "NI Number *",   2, 0, td.get("ni_number",""),   placeholder="e.g. AB123456C")
        self.fn  = entry_var(inner, "First Name *",  2, 1, td.get("first_name",""),  placeholder="e.g. John")
        self.ln  = entry_var(inner, "Last Name *",   2, 2, td.get("last_name",""),   placeholder="e.g. Smith")
        self.dob = entry_var(inner, "Date of Birth", 4, 0, td.get("date_of_birth",""),placeholder="YYYY-MM-DD")
        self.ph  = entry_var(inner, "Phone *",       4, 1, td.get("phone",""),       placeholder="e.g. 07700 123456")
        self.em  = entry_var(inner, "Email *",       4, 2, td.get("email",""),       placeholder="e.g. john@email.com")
        self.oc  = entry_var(inner, "Occupation",    6, 0, td.get("occupation",""),  placeholder="e.g. Software Engineer")

        slbl(8, "Emergency Contact")
        self.ecn = entry_var(inner, "Contact Name",  9, 0, td.get("emergency_contact_name",""),  placeholder="e.g. Jane Smith")
        self.ecp = entry_var(inner, "Contact Phone", 9, 1, td.get("emergency_contact_phone",""), placeholder="e.g. 07700 654321")

        slbl(11, "References")
        self.r1n = entry_var(inner, "Ref 1 Name",  12, 0, td.get("reference1_name",""),  placeholder="e.g. Dr. Brown")
        self.r1p = entry_var(inner, "Ref 1 Phone", 12, 1, td.get("reference1_phone",""), placeholder="e.g. 07700 111222")
        self.r1e = entry_var(inner, "Ref 1 Email", 12, 2, td.get("reference1_email",""), placeholder="e.g. ref@email.com")
        self.r2n = entry_var(inner, "Ref 2 Name",  14, 0, td.get("reference2_name",""),  placeholder="e.g. Dr. Jones")
        self.r2p = entry_var(inner, "Ref 2 Phone", 14, 1, td.get("reference2_phone",""), placeholder="e.g. 07700 333444")
        self.r2e = entry_var(inner, "Ref 2 Email", 14, 2, td.get("reference2_email",""), placeholder="e.g. ref2@email.com")

        slbl(16, "Notes")
        self.nt = tk.Text(inner, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                           relief="flat", bd=0, width=72, height=4,
                           highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.nt.grid(row=17, column=0, columnspan=3, sticky="ew", padx=6)
        if td.get("notes"): self.nt.insert("1.0", td["notes"])

        nav = tk.Frame(inner, bg=CARD_BG, pady=16)
        nav.grid(row=18, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Cancel", lambda: self.on_complete and self.on_complete(), color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Next: Select Apartment →", self._s1_next).pack(side="right")
        for c in range(3): inner.columnconfigure(c, weight=1)

    def _s1_next(self):
        ni, fn, ln, ph, em = (self.ni.get().strip(), self.fn.get().strip(),
                               self.ln.get().strip(), self.ph.get().strip(), self.em.get().strip())
        if not all([ni, fn, ln, ph, em]):
            messagebox.showwarning("Missing Fields", "Please fill in all required (*) fields.")
            return
        ni = ni.upper()
        if not re.fullmatch(r"[A-Z]{2}\d{6}[A-Z]", ni):
            messagebox.showwarning("Invalid NI Number",
                "NI Number must be 2 letters, 6 digits, then 1 letter (e.g. AB123456C).")
            return
        ph_digits = re.sub(r"[\s\-]", "", ph)
        if not re.fullmatch(r"(\+44|0)\d{9,10}", ph_digits):
            messagebox.showwarning("Invalid Phone Number",
                "Phone must be a valid UK number (e.g. 07700 123456 or +44 7700 123456).")
            return
        self.tenant_data = {
            "ni_number": ni, "first_name": fn, "last_name": ln,
            "date_of_birth": self.dob.get().strip(), "phone": ph, "email": em,
            "occupation": self.oc.get().strip(),
            "emergency_contact_name":  self.ecn.get().strip(),
            "emergency_contact_phone": self.ecp.get().strip(),
            "reference1_name":  self.r1n.get().strip(), "reference1_phone": self.r1p.get().strip(),
            "reference1_email": self.r1e.get().strip(), "reference2_name":  self.r2n.get().strip(),
            "reference2_phone": self.r2p.get().strip(), "reference2_email": self.r2e.get().strip(),
            "notes": self.nt.get("1.0", "end-1c").strip(),
        }
        self._show(1)

    # Step 2 ──────────────────────────────────────────────────────────────────
    def _s2(self):
        locs = {l.id: l.city for l in self.db.get_all_locations()}
        loc_name = locs.get(self.staff.location_id, "Your Location")

        tk.Label(self.body, text=f"Available Apartments  —  {loc_name}", font=FONT_TITLE,
                 bg=DARK_BG, fg=TEXT).pack(anchor="w", pady=(0,4))
        tk.Label(self.body, text="Only available apartments at your location are shown. Select one to assign.",
                 font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w", pady=(0,10))

        # Date bar
        db_ = tk.Frame(self.body, bg=CARD_BG, padx=24, pady=14)
        db_.pack(fill="x", pady=(0,10))
        tk.Label(db_, text="Lease Period:", font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        tk.Label(db_, text="  Start Date *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        self.v_start = tk.StringVar(value=self.lease_start or str(date.today()))
        tk.Entry(db_, textvariable=self.v_start, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=13,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", padx=(4,20), ipady=5)
        tk.Label(db_, text="End Date *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        self.v_end = tk.StringVar(value=self.lease_end or str(date.today().replace(year=date.today().year+1)))
        tk.Entry(db_, textvariable=self.v_end, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=13,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", padx=(4,0), ipady=5)

        apts = self.db.get_available_apartments(self.staff.location_id)
        outer, apt_inner = scrollable(self.body, DARK_BG)
        outer.pack(fill="both", expand=True)

        self._sel_var = tk.IntVar(value=-1)
        self._apt_cards = {}
        self._apt_indicators = {}
        self.selected_apt = None
        if not apts:
            tk.Label(apt_inner, text="No available apartments at your location.",
                     font=FONT_BODY, bg=DARK_BG, fg=DANGER).pack(pady=30)
        else:
            for apt in apts: self._wizard_card(apt_inner, apt)

        nav = tk.Frame(self.body, bg=DARK_BG, pady=10)
        nav.pack(fill="x")
        mkbtn(nav, "← Back", lambda: self._show(0), color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Next: Confirm →", self._s2_next).pack(side="right")

    def _wizard_card(self, parent, apt: Apartment):
        color = sc(apt.status)
        card = tk.Frame(parent, bg=CARD_BG, cursor="hand2",
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0,6))
        tk.Frame(card, bg=color, height=3).pack(fill="x")
        body = tk.Frame(card, bg=CARD_BG, padx=16, pady=12)
        body.pack(fill="both")

        ind = tk.Canvas(body, width=22, height=22, bg=CARD_BG, highlightthickness=0)
        ind.create_oval(2, 2, 20, 20, outline=BORDER, width=2)
        ind.pack(side="left", padx=(0,14))
        self._apt_indicators[apt.id] = ind
        self._apt_cards[apt.id] = card

        info = tk.Frame(body, bg=CARD_BG)
        info.pack(side="left", fill="x", expand=True)
        top = tk.Frame(info, bg=CARD_BG)
        top.pack(fill="x")
        tk.Label(top, text=f"Unit {apt.unit_number}", font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        tk.Label(top, text=f"{apt.apartment_type}  •  {apt.num_bedrooms}bd/{apt.num_bathrooms}ba",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=12)
        extras = [x for x in [("Furnished" if apt.furnished else ""), ("Parking" if apt.parking else ""),
                               (f"{apt.size_sqft:.0f} sq ft" if apt.size_sqft else "")] if x]
        if extras: tk.Label(info, text="  |  ".join(extras), font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(body, text=f"£{apt.monthly_rent:,.0f}/mo", font=("Segoe UI",13,"bold"),
                 bg=CARD_BG, fg=ACCENT).pack(side="right")

        def click(e=None, a=apt):
            self._sel_var.set(a.id); self.selected_apt = a
            self._refresh_apt_selection()
        def _bind(w):
            try: w.bind("<Button-1>", click)
            except Exception: pass
            for child in w.winfo_children(): _bind(child)
        _bind(card)
        card.bind("<Enter>", lambda e, a=apt: card.config(
            highlightbackground=ACCENT if self._sel_var.get()==a.id else "#93C5FD", highlightthickness=2))
        card.bind("<Leave>", lambda e, a=apt: card.config(
            highlightbackground=ACCENT if self._sel_var.get()==a.id else BORDER,
            highlightthickness=2 if self._sel_var.get()==a.id else 1))

    def _refresh_apt_selection(self):
        sel = self._sel_var.get()
        for apt_id, card in self._apt_cards.items():
            selected = (apt_id == sel)
            card.config(highlightbackground=ACCENT if selected else BORDER,
                        highlightthickness=2 if selected else 1)
        for apt_id, ind in self._apt_indicators.items():
            ind.delete("all")
            if apt_id == sel:
                ind.create_oval(2, 2, 20, 20, fill=ACCENT, outline="")
                ind.create_text(11, 11, text="✓", fill="white", font=("Segoe UI", 9, "bold"))
            else:
                ind.create_oval(2, 2, 20, 20, outline=BORDER, width=2)

    def _s2_next(self):
        if not self.selected_apt or self._sel_var.get() < 0:
            messagebox.showwarning("No Selection", "Please select an apartment.")
            return
        s, e = self.v_start.get().strip(), self.v_end.get().strip()
        if not s or not e:
            messagebox.showwarning("Missing Dates", "Please enter both lease dates.")
            return
        self.lease_start, self.lease_end = s, e
        self._show(2)

    # Step 3 ──────────────────────────────────────────────────────────────────
    def _s3(self):
        td, apt = self.tenant_data, self.selected_apt
        outer, inner = scrollable(self.body, DARK_BG)
        outer.pack(fill="both", expand=True)
        inner.config(padx=8)

        sc_wrap = tk.Frame(inner, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        sc_wrap.pack(fill="x", pady=(0,12))
        tk.Frame(sc_wrap, bg=SUCCESS, height=4).pack(fill="x")
        sc_ = tk.Frame(sc_wrap, bg=CARD_BG, padx=28, pady=20)
        sc_.pack(fill="both")
        tk.Label(sc_, text="Lease Summary", font=FONT_TITLE, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0,12))
        info_grid(sc_, [
            ("Tenant",       f"{td['first_name']} {td['last_name']}"),
            ("Email",        td["email"]), ("Phone", td["phone"]),
            ("Apartment",    f"Unit {apt.unit_number}"), ("Location", apt.location_city),
            ("Type",         apt.apartment_type),
            ("Period",       f"{self.lease_start}  →  {self.lease_end}"),
            ("Monthly Rent", f"£{apt.monthly_rent:,.2f}"),
            ("Deposit",      f"£{apt.monthly_rent*2:,.2f}  (2 months)"),
        ], cols=3, bg=CARD_BG)

        pc_wrap = tk.Frame(inner, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        pc_wrap.pack(fill="x", pady=(0,12))
        tk.Frame(pc_wrap, bg=ACCENT, height=4).pack(fill="x")
        pc = tk.Frame(pc_wrap, bg=CARD_BG, padx=28, pady=16)
        pc.pack(fill="both")
        tk.Label(pc, text="Initial Payment Request", font=FONT_TITLE, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0,10))
        pr = tk.Frame(pc, bg=CARD_BG)
        pr.pack(fill="x")
        tk.Label(pr, text="Amount (£):", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        self.v_amount = tk.StringVar(value=f"{apt.monthly_rent:.2f}")
        tk.Entry(pr, textvariable=self.v_amount, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=14,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", padx=(4,24), ipady=5)
        tk.Label(pr, text="Due Date:", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        self.v_due = tk.StringVar(value=self.lease_start)
        tk.Entry(pr, textvariable=self.v_due, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=13,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).pack(side="left", padx=(4,0), ipady=5)
        tk.Label(pc, text=f"📧  Payment request emailed to: {td['email']}  (emulated — no real email sent)",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(10,0))

        nav = tk.Frame(inner, bg=DARK_BG, pady=12)
        nav.pack(fill="x")
        mkbtn(nav, "← Back", lambda: self._show(1), color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "✓  Create Lease & Send Request", self._confirm, color=SUCCESS).pack(side="right")

    def _confirm(self):
        td, apt = self.tenant_data, self.selected_apt
        tenant = Tenant(**td)
        try:
            tid = self.db.create_tenant(tenant)
        except Exception as ex:
            messagebox.showerror("Error", f"Could not create tenant:\n{ex}")
            return
        lease = Lease(tenant_id=tid, apartment_id=apt.id,
                      start_date=self.lease_start, end_date=self.lease_end,
                      monthly_rent=apt.monthly_rent, deposit_amount=apt.monthly_rent*2,
                      status=LeaseStatus.ACTIVE.value, created_by=self.staff.id)
        lid = self.db.create_lease(lease)
        try: amount = float(self.v_amount.get().strip())
        except ValueError: amount = apt.monthly_rent
        self.db.create_payment_request(
            Payment(lease_id=lid, amount_due=amount, due_date=self.v_due.get().strip()))
        messagebox.showinfo("Lease Created ✓",
                            f"Lease created!\n\nTenant: {td['first_name']} {td['last_name']}\n"
                            f"Unit: {apt.unit_number}  •  {apt.location_city}\n"
                            f"Period: {self.lease_start} → {self.lease_end}\n"
                            f"Rent: £{apt.monthly_rent:,.2f}/mo\n\n"
                            f"📧 Payment request (£{amount:,.2f}) sent to {td['email']}")
        if self.on_complete: self.on_complete()


# ══════════════════════════════════════════════════════════════════════════════
#  DIALOGS
# ══════════════════════════════════════════════════════════════════════════════
class EditTenantDialog(tk.Toplevel):
    def __init__(self, parent, tenant: Tenant, db, on_save=None):
        super().__init__(parent)
        self.tenant = tenant; self.db = db; self.on_save = on_save
        self.title(f"Edit Tenant — {tenant.full_name}")
        self.geometry("700x600")
        self.configure(bg=DARK_BG)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Editing: {self.tenant.full_name}", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text=f"NI: {self.tenant.ni_number}", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")

        outer, inner = scrollable(self, CARD_BG)
        outer.pack(fill="both", expand=True)
        inner.config(padx=28, pady=20)
        t = self.tenant
        self.fn  = entry_var(inner, "First Name *",   0, 0, t.first_name,           placeholder="e.g. John")
        self.ln  = entry_var(inner, "Last Name *",    0, 1, t.last_name,            placeholder="e.g. Smith")
        self.dob = entry_var(inner, "Date of Birth",  0, 2, t.date_of_birth or "",  placeholder="YYYY-MM-DD")
        self.ph  = entry_var(inner, "Phone *",        2, 0, t.phone,                placeholder="e.g. 07700 123456")
        self.em  = entry_var(inner, "Email *",        2, 1, t.email,                placeholder="e.g. john@email.com")
        self.oc  = entry_var(inner, "Occupation",     2, 2, t.occupation,           placeholder="e.g. Engineer")
        tk.Label(inner, text="Emergency Contact", font=FONT_SUB, bg=CARD_BG, fg=ACCENT
                 ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(16,0), padx=6)
        self.ecn = entry_var(inner, "Name",  5, 0, t.emergency_contact_name,  placeholder="e.g. Jane Smith")
        self.ecp = entry_var(inner, "Phone", 5, 1, t.emergency_contact_phone, placeholder="e.g. 07700 654321")
        tk.Label(inner, text="References", font=FONT_SUB, bg=CARD_BG, fg=ACCENT
                 ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(16,0), padx=6)
        self.r1n = entry_var(inner, "Ref 1 Name",  8, 0, t.reference1_name,  placeholder="e.g. Dr. Brown")
        self.r1p = entry_var(inner, "Ref 1 Phone", 8, 1, t.reference1_phone, placeholder="e.g. 07700 111222")
        self.r1e = entry_var(inner, "Ref 1 Email", 8, 2, t.reference1_email, placeholder="e.g. ref@email.com")
        self.r2n = entry_var(inner, "Ref 2 Name",  10, 0, t.reference2_name,  placeholder="e.g. Dr. Jones")
        self.r2p = entry_var(inner, "Ref 2 Phone", 10, 1, t.reference2_phone, placeholder="e.g. 07700 333444")
        self.r2e = entry_var(inner, "Ref 2 Email", 10, 2, t.reference2_email, placeholder="e.g. ref2@email.com")
        tk.Label(inner, text="Notes", font=FONT_SUB, bg=CARD_BG, fg=ACCENT
                 ).grid(row=12, column=0, columnspan=3, sticky="w", pady=(16,0), padx=6)
        self.nt = tk.Text(inner, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                           relief="flat", bd=0, width=68, height=4,
                           highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.nt.grid(row=13, column=0, columnspan=3, sticky="ew", padx=6)
        if t.notes: self.nt.insert("1.0", t.notes)

        nav = tk.Frame(inner, bg=CARD_BG, pady=14)
        nav.grid(row=14, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Save Changes ✓", self._save, color=SUCCESS).pack(side="right")
        for c in range(3): inner.columnconfigure(c, weight=1)

    def _save(self):
        t = self.tenant
        t.first_name = self.fn.get().strip(); t.last_name = self.ln.get().strip()
        t.phone = self.ph.get().strip(); t.email = self.em.get().strip()
        t.occupation = self.oc.get().strip(); t.date_of_birth = self.dob.get().strip()
        t.emergency_contact_name  = self.ecn.get().strip()
        t.emergency_contact_phone = self.ecp.get().strip()
        t.reference1_name  = self.r1n.get().strip(); t.reference1_phone = self.r1p.get().strip()
        t.reference1_email = self.r1e.get().strip(); t.reference2_name  = self.r2n.get().strip()
        t.reference2_phone = self.r2p.get().strip(); t.reference2_email = self.r2e.get().strip()
        t.notes = self.nt.get("1.0", "end-1c").strip()
        if not all([t.first_name, t.last_name, t.phone, t.email]):
            messagebox.showwarning("Missing", "Please fill in required fields.", parent=self)
            return
        self.db.update_tenant(t)
        messagebox.showinfo("Saved", "Tenant updated successfully.", parent=self)
        if self.on_save: self.on_save()
        self.destroy()


class ComplaintDialog(tk.Toplevel):
    def __init__(self, parent, lease: Lease, staff, db, on_save=None):
        super().__init__(parent)
        self.lease = lease; self.staff = staff; self.db = db; self.on_save = on_save
        self.title(f"Register Complaint — {lease.tenant_name}")
        self.geometry("540x460")
        self.configure(bg=DARK_BG)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Register Complaint", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text=f"Tenant: {self.lease.tenant_name}  •  Unit {self.lease.apartment_unit}",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)
        self.v_title = entry_var(form, "Complaint Title *", 0, 0, colspan=2, width=48)
        self.v_cat = combo_var(form, "Category *",
                               ["Noise","Property Damage","Maintenance",
                                "Neighbour Dispute","Billing","Staff Conduct","Other"], 2, 0)
        self.v_pri = combo_var(form, "Priority", [p.value for p in MaintenancePriority], 2, 1, default="Medium")
        tk.Label(form, text="Date Reported *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=4, column=0, sticky="w", padx=6, pady=(8,2))
        self.v_date = tk.StringVar(value=str(date.today()))
        tk.Entry(form, textvariable=self.v_date, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=16,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).grid(row=5, column=0, sticky="w", padx=6, ipady=4)
        tk.Label(form, text="Description *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=6, column=0, columnspan=2, sticky="w", padx=6, pady=(8,2))
        self.desc = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                             relief="flat", bd=0, width=52, height=7,
                             highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.desc.grid(row=7, column=0, columnspan=2, sticky="ew", padx=6)
        nav = tk.Frame(form, bg=CARD_BG, pady=14)
        nav.grid(row=8, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Submit Complaint ✓", self._submit, color=WARNING).pack(side="right")

    def _submit(self):
        title = self.v_title.get().strip()
        desc  = self.desc.get("1.0","end-1c").strip()
        if not title or not desc:
            messagebox.showwarning("Missing", "Please fill in title and description.", parent=self)
            return
        self.db.create_complaint(Complaint(
            lease_id=self.lease.id, tenant_id=self.lease.tenant_id,
            apartment_id=self.lease.apartment_id, title=title, description=desc,
            category=self.v_cat.get(), status=ComplaintStatus.OPEN.value,
            reported_date=self.v_date.get().strip(), created_by=self.staff.id))
        messagebox.showinfo("Registered", "Complaint registered successfully.", parent=self)
        if self.on_save: self.on_save()
        self.destroy()


class PaymentRequestDialog(tk.Toplevel):
    def __init__(self, parent, lease: Lease, staff, db, on_save=None):
        super().__init__(parent)
        self.lease = lease; self.staff = staff; self.db = db; self.on_save = on_save
        self.title("Send Payment Request")
        self.geometry("460x320")
        self.configure(bg=DARK_BG)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Send Payment Request", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text=f"{self.lease.tenant_name}  •  {self.lease.tenant_email}",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)
        self.v_amt = entry_var(form, "Amount Due (£) *", 0, 0, f"{self.lease.monthly_rent:.2f}", 18)
        self.v_due = entry_var(form, "Due Date *",       0, 1, str(date.today()), 18)
        tk.Label(form, text="Notes", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(8,2))
        self.notes = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                              relief="flat", bd=0, width=44, height=4,
                              highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.notes.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6)
        nav = tk.Frame(form, bg=CARD_BG, pady=14)
        nav.grid(row=4, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Send Request ✓", self._send).pack(side="right")

    def _send(self):
        try: amount = float(self.v_amt.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid", "Enter a valid amount.", parent=self); return
        due = self.v_due.get().strip()
        if not due:
            messagebox.showwarning("Missing", "Enter a due date.", parent=self); return
        self.db.create_payment_request(
            Payment(lease_id=self.lease.id, amount_due=amount, due_date=due,
                    notes=self.notes.get("1.0","end-1c").strip()))
        messagebox.showinfo("Sent ✓", f"Payment request (£{amount:,.2f}) sent to {self.lease.tenant_email}.\nDue: {due}", parent=self)
        if self.on_save: self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  EARLY TERMINATION DIALOG
# ══════════════════════════════════════════════════════════════════════════════
class EarlyTerminationDialog(tk.Toplevel):
    def __init__(self, parent, lease: Lease, db, on_save=None):
        super().__init__(parent)
        self.lease = lease
        self.db = db
        self.on_save = on_save
        self.title("Request Early Termination")
        self.geometry("500x420")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=DANGER, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚠  Request Early Termination", font=FONT_TITLE,
                 bg=DANGER, fg="white").pack(anchor="w")
        tk.Label(hdr, text=f"{self.lease.tenant_name}  •  Unit {self.lease.apartment_unit}",
                 font=FONT_SMALL, bg=DANGER, fg="#FECACA").pack(anchor="w")

        body = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        body.pack(fill="both", expand=True)

        # Lease summary
        penalty = self.lease.early_termination_penalty()
        earliest_exit = date.today() + timedelta(days=self.lease.REQUIRED_NOTICE_DAYS)

        info_grid(body, [
            ("Original End Date", self.lease.end_date or "—"),
            ("Monthly Rent",      f"£{self.lease.monthly_rent:,.2f}"),
            ("Notice Period",     f"{self.lease.REQUIRED_NOTICE_DAYS} days"),
            ("Penalty (5%)",      f"£{penalty:,.2f}"),
        ], cols=2)

        # Policy note
        note = tk.Frame(body, bg="#FEF3C7", padx=14, pady=10)
        note.pack(fill="x", pady=(12, 16))
        tk.Label(note, text="Policy: tenant must give 30 days' notice and pay a penalty of\n"
                             f"5% of monthly rent (£{penalty:,.2f}) upon early exit.",
                 font=FONT_SMALL, bg="#FEF3C7", fg=WARNING, justify="left").pack(anchor="w")

        # Notice date entry
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.v_notice = entry_var(body, "Notice Given Date *", 3, 0,
                                  str(date.today()), placeholder="YYYY-MM-DD")
        self.v_notice.trace_add("write", self._update_exit_date)

        # Earliest exit date (auto-computed, read-only display)
        tk.Label(body, text="Earliest Exit Date", font=FONT_SMALL,
                 bg=CARD_BG, fg=TEXT_DIM).grid(row=3, column=1, sticky="w", padx=6, pady=(8, 2))
        self._exit_var = tk.StringVar(value=str(earliest_exit))
        exit_lbl = tk.Label(body, textvariable=self._exit_var,
                             font=FONT_SUB, bg=CARD_BG, fg=DANGER)
        exit_lbl.grid(row=4, column=1, sticky="w", padx=6)

        # Buttons
        nav = tk.Frame(body, bg=CARD_BG, pady=18)
        nav.grid(row=5, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Confirm Termination", self._confirm, color=DANGER).pack(side="right")

    def _update_exit_date(self, *_):
        try:
            nd = date.fromisoformat(self.v_notice.get().strip())
            self._exit_var.set(str(nd + timedelta(days=self.lease.REQUIRED_NOTICE_DAYS)))
        except ValueError:
            self._exit_var.set("—")

    def _confirm(self):
        notice_str = self.v_notice.get().strip()
        try:
            notice_date = date.fromisoformat(notice_str)
        except ValueError:
            messagebox.showwarning("Invalid Date",
                                   "Enter notice date as YYYY-MM-DD.", parent=self)
            return
        termination_date = notice_date + timedelta(days=self.lease.REQUIRED_NOTICE_DAYS)
        penalty = self.lease.early_termination_penalty()
        confirm = messagebox.askyesno(
            "Confirm Early Termination",
            f"This will terminate the lease for {self.lease.tenant_name}.\n\n"
            f"  Notice date:      {notice_date}\n"
            f"  Termination date: {termination_date}\n"
            f"  Penalty owed:     £{penalty:,.2f}\n\n"
            "Proceed?",
            parent=self,
        )
        if not confirm:
            return
        self.db.request_early_termination(
            self.lease.id, self.lease.apartment_id,
            str(notice_date), str(termination_date),
        )
        messagebox.showinfo(
            "Termination Recorded",
            f"Early termination recorded.\n"
            f"Lease ends: {termination_date}\n"
            f"Penalty due: £{penalty:,.2f}",
            parent=self,
        )
        if self.on_save:
            self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER TENANT VIEW  — Front-Desk standalone tenant registration
# ══════════════════════════════════════════════════════════════════════════════

class RegisterTenantView(tk.Frame):
    def __init__(self, parent, staff, db, on_complete=None):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.on_complete = on_complete
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        top.pack(fill="x")
        tk.Label(top, text="Register Tenant", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(top, text="Create a new tenant record.", font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")

        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        inner.config(bg=CARD_BG)
        form = tk.Frame(inner, bg=CARD_BG, padx=32, pady=24)
        form.pack(fill="x")
        for c in range(3): form.columnconfigure(c, weight=1)

        def slbl(r, txt):
            wrap = tk.Frame(form, bg=CARD_BG)
            wrap.grid(row=r, column=0, columnspan=3, sticky="ew", pady=(18, 4), padx=6)
            tk.Frame(wrap, bg=ACCENT, width=3).pack(side="left", fill="y", padx=(0, 8))
            tk.Label(wrap, text=txt, font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")

        slbl(0, "Personal Details")
        self.ni  = entry_var(form, "NI Number *",   1, 0, placeholder="e.g. AB123456C")
        self.fn  = entry_var(form, "First Name *",  1, 1, placeholder="e.g. John")
        self.ln  = entry_var(form, "Last Name *",   1, 2, placeholder="e.g. Smith")
        self.dob = entry_var(form, "Date of Birth", 3, 0, placeholder="YYYY-MM-DD")
        self.ph  = entry_var(form, "Phone *",       3, 1, placeholder="e.g. 07700 123456")
        self.em  = entry_var(form, "Email *",       3, 2, placeholder="e.g. john@email.com")
        self.oc  = entry_var(form, "Occupation",    5, 0, placeholder="e.g. Engineer")

        slbl(7, "Emergency Contact")
        self.ecn = entry_var(form, "Contact Name",  8, 0, placeholder="e.g. Jane Smith")
        self.ecp = entry_var(form, "Contact Phone", 8, 1, placeholder="e.g. 07700 654321")

        slbl(10, "References")
        self.r1n = entry_var(form, "Ref 1 Name *",  11, 0, placeholder="e.g. Dr. Brown")
        self.r1p = entry_var(form, "Ref 1 Phone",   11, 1, placeholder="e.g. 07700 111222")
        self.r1e = entry_var(form, "Ref 1 Email",   11, 2, placeholder="e.g. ref@email.com")
        self.r2n = entry_var(form, "Ref 2 Name",    13, 0, placeholder="e.g. Dr. Jones")
        self.r2p = entry_var(form, "Ref 2 Phone",   13, 1, placeholder="e.g. 07700 333444")
        self.r2e = entry_var(form, "Ref 2 Email",   13, 2, placeholder="e.g. ref2@email.com")

        slbl(15, "Notes")
        self.nt = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                          relief="flat", bd=0, width=70, height=4,
                          highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.nt.grid(row=16, column=0, columnspan=3, sticky="ew", padx=6)

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=17, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Cancel", lambda: self.on_complete and self.on_complete(),
              color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Register Tenant ✓", self._submit, color=SUCCESS).pack(side="right")

    def _submit(self):
        import sqlite3
        ni = self.ni.get().strip().upper()
        fn = self.fn.get().strip()
        ln = self.ln.get().strip()
        ph = self.ph.get().strip()
        em = self.em.get().strip()
        r1n = self.r1n.get().strip()
        if not all([ni, fn, ln, ph, em]):
            messagebox.showwarning("Missing Fields",
                                   "Please fill in all required (*) fields.", parent=self)
            return
        if not re.fullmatch(r"[A-Z]{2}\d{6}[A-Z]", ni):
            messagebox.showwarning("Invalid NI Number",
                "NI Number must be 2 letters, 6 digits, then 1 letter (e.g. AB123456C).",
                parent=self)
            return
        ph_digits = re.sub(r"[\s\-]", "", ph)
        if not re.fullmatch(r"(\+44|0)\d{9,10}", ph_digits):
            messagebox.showwarning("Invalid Phone Number",
                "Phone must be a valid UK number (e.g. 07700 123456 or +44 7700 123456).",
                parent=self)
            return
        if not r1n:
            messagebox.showwarning("Missing Fields",
                                   "At least one reference name is required.", parent=self)
            return
        t = Tenant(
            ni_number=ni, first_name=fn, last_name=ln,
            phone=ph, email=em, occupation=self.oc.get().strip(),
            date_of_birth=self.dob.get().strip(),
            emergency_contact_name=self.ecn.get().strip(),
            emergency_contact_phone=self.ecp.get().strip(),
            reference1_name=r1n,
            reference1_phone=self.r1p.get().strip(),
            reference1_email=self.r1e.get().strip(),
            reference2_name=self.r2n.get().strip(),
            reference2_phone=self.r2p.get().strip(),
            reference2_email=self.r2e.get().strip(),
            notes=self.nt.get("1.0", "end-1c").strip(),
        )
        try:
            tid = self.db.create_tenant(t)
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate NI Number",
                                 f"A tenant with NI number {ni} already exists.", parent=self)
            return
        messagebox.showinfo("Registered ✓",
                            f"Tenant {fn} {ln} registered (ID #{tid}).", parent=self)
        if self.on_complete:
            self.on_complete()


# ══════════════════════════════════════════════════════════════════════════════
#  TENANT RECORDS VIEW  — searchable tenant table for Front-Desk
# ══════════════════════════════════════════════════════════════════════════════

class TenantRecordsView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._all: List[Tenant] = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _get_export_data(self):
        cols = ["NI Number", "Full Name", "Phone", "Email", "Occupation"]
        rows = [(t.ni_number, t.full_name, t.phone, t.email, t.occupation or "")
                for t in self._shown]
        return cols, rows

    def _build(self):
        top = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        top.pack(fill="x")
        lft = tk.Frame(top, bg=DARK_BG)
        lft.pack(side="left", fill="x", expand=True)
        tk.Label(lft, text="Tenant Records", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(lft, text="All tenants — search by name, NI number, phone or email.",
                 font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")

        bar = tk.Frame(self, bg=DARK_BG, padx=28, pady=(0, 8))
        bar.pack(fill="x")
        self._q = tk.StringVar()
        self._q.trace_add("write", lambda *_: self._filter())
        srch = tk.Entry(bar, textvariable=self._q, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                        insertbackground=TEXT, relief="flat", bd=0, width=40,
                        highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        srch.pack(side="left", ipady=5, padx=(0, 12))
        srch.insert(0, "Search name, NI, phone, email…")
        srch.config(fg=TEXT_MUTED)
        def _fin(e):
            if srch.get() == "Search name, NI, phone, email…":
                srch.delete(0, "end"); srch.config(fg=TEXT)
        def _fout(e):
            if not srch.get(): srch.insert(0, "Search name, NI, phone, email…"); srch.config(fg=TEXT_MUTED)
        srch.bind("<FocusIn>", _fin); srch.bind("<FocusOut>", _fout)

        export_bar(bar, "Tenant_Records", self._get_export_data).pack(side="right")

        # Treeview
        frame = tk.Frame(self, bg=DARK_BG, padx=28, pady=(0, 20))
        frame.pack(fill="both", expand=True)
        cols = ("ni", "name", "phone", "email", "occupation")
        self._tv = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        for cid, lbl, w in [("ni","NI Number",110),("name","Full Name",180),
                             ("phone","Phone",120),("email","Email",200),("occupation","Occupation",130)]:
            self._tv.heading(cid, text=lbl)
            self._tv.column(cid, width=w, anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tv.yview)
        self._tv.configure(yscrollcommand=sb.set)
        self._tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _load(self):
        self._all = self.db.get_all_tenants()
        self._shown = list(self._all)
        self._refresh()

    def _filter(self):
        q = self._q.get().strip().lower()
        placeholder = "search name, ni, phone, email…"
        if not q or q == placeholder:
            self._shown = list(self._all)
        else:
            self._shown = [t for t in self._all if
                           q in t.full_name.lower() or q in t.ni_number.lower() or
                           q in (t.phone or "").lower() or q in (t.email or "").lower()]
        self._refresh()

    def _refresh(self):
        self._tv.delete(*self._tv.get_children())
        for t in self._shown:
            self._tv.insert("", "end", values=(
                t.ni_number, t.full_name, t.phone or "—",
                t.email or "—", t.occupation or "—"))


# ══════════════════════════════════════════════════════════════════════════════
#  LOG COMPLAINT VIEW  — Front-Desk standalone complaint form
# ══════════════════════════════════════════════════════════════════════════════

class LogComplaintView(tk.Frame):
    def __init__(self, parent, staff, db, on_complete=None):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.on_complete = on_complete
        self._active_lease = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        top.pack(fill="x")
        tk.Label(top, text="Log Complaint", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(top, text="Register a tenant complaint against an occupied unit.",
                 font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")

        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        inner.config(bg=CARD_BG)
        form = tk.Frame(inner, bg=CARD_BG, padx=32, pady=24)
        form.pack(fill="x")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)

        # Apartment picker
        apts = self.db.get_all_apartments(self.staff.location_id)
        occupied = [a for a in apts if a.status == "Occupied"]
        apt_labels = [f"Unit {a.unit_number}  ({a.apartment_type})" for a in occupied]
        self._apt_map = {lbl: a for lbl, a in zip(apt_labels, occupied)}

        tk.Label(form, text="Apartment *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 2))
        self.v_apt = tk.StringVar(value=apt_labels[0] if apt_labels else "")
        cb_apt = ttk.Combobox(form, textvariable=self.v_apt, values=apt_labels,
                              font=FONT_BODY, width=45, state="readonly")
        cb_apt.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))
        cb_apt.bind("<<ComboboxSelected>>", self._on_apt_change)

        self._tenant_lbl = tk.Label(form, text="", font=FONT_SMALL, bg=CARD_BG, fg=ACCENT)
        self._tenant_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        self.v_title = entry_var(form, "Complaint Title *", 3, 0, colspan=2, width=48)
        self.v_cat = combo_var(form, "Category *",
                               ["Noise", "Property Damage", "Maintenance",
                                "Neighbour Dispute", "Billing", "Staff Conduct", "Other"], 5, 0)
        self.v_pri = combo_var(form, "Priority", [p.value for p in MaintenancePriority], 5, 1, default="Medium")

        tk.Label(form, text="Date Reported *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=7, column=0, sticky="w", padx=6, pady=(8, 2))
        self.v_date = tk.StringVar(value=str(date.today()))
        tk.Entry(form, textvariable=self.v_date, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=16,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).grid(row=8, column=0, sticky="w", padx=6, ipady=4)

        tk.Label(form, text="Description *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=9, column=0, columnspan=2, sticky="w", padx=6, pady=(8, 2))
        self.v_desc = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                              relief="flat", bd=0, width=60, height=6,
                              highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.v_desc.grid(row=10, column=0, columnspan=2, sticky="ew", padx=6)

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=11, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", lambda: self.on_complete and self.on_complete(),
              color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Submit Complaint ✓", self._submit, color=WARNING).pack(side="right")

        if apt_labels:
            self._on_apt_change(None)

    def _on_apt_change(self, _event):
        apt = self._apt_map.get(self.v_apt.get())
        if not apt:
            self._active_lease = None
            self._tenant_lbl.config(text="")
            return
        lease = self.db.get_active_lease_for_apartment(apt.id)
        self._active_lease = lease
        if lease:
            self._tenant_lbl.config(text=f"Tenant: {lease.tenant_name}")
        else:
            self._tenant_lbl.config(text="No active lease for this unit.")

    def _submit(self):
        apt = self._apt_map.get(self.v_apt.get())
        if not apt:
            messagebox.showwarning("Missing", "Select an apartment.", parent=self)
            return
        lease = self._active_lease
        if not lease:
            messagebox.showwarning("No Lease",
                                   "Selected apartment has no active lease.", parent=self)
            return
        title = self.v_title.get().strip()
        desc = self.v_desc.get("1.0", "end-1c").strip()
        if not title or not desc:
            messagebox.showwarning("Missing Fields",
                                   "Please fill in title and description.", parent=self)
            return
        self.db.create_complaint(Complaint(
            lease_id=lease.id, tenant_id=lease.tenant_id,
            apartment_id=lease.apartment_id, title=title, description=desc,
            category=self.v_cat.get(), status=ComplaintStatus.OPEN.value,
            reported_date=self.v_date.get().strip(), created_by=self.staff.id))
        messagebox.showinfo("Registered ✓", "Complaint registered successfully.", parent=self)
        if self.on_complete:
            self.on_complete()