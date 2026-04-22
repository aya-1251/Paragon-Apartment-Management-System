"""
views_maintenance.py — Maintenance Staff UI
Sidebar: Apartments | Maintenance Jobs | Workers | Job Types & Prices | Add Request
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable, List

from .views import (
    DARK_BG, PANEL_BG, CARD_BG, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    TEXT, TEXT_DIM, TEXT_MUTED, BORDER, HOVER_BG,
    FONT_HEAD, FONT_TITLE, FONT_SUB, FONT_BODY, FONT_SMALL,
    sc, badge, mkbtn, entry_var, combo_var, scrollable, sec_hdr, info_grid,
    ApartmentDetailWindow, export_bar, BaseAppShell,
)

AVAIL_COLORS = {
    "Available": SUCCESS, "Busy": WARNING, "On Leave": ACCENT2, "Inactive": TEXT_MUTED,
}
PRIORITY_COLORS = {"Urgent": DANGER, "High": WARNING, "Medium": WARNING, "Low": SUCCESS}


def priority_badge(parent, priority):
    color = PRIORITY_COLORS.get(priority, TEXT_DIM)
    return tk.Label(parent, text=f"  {priority}  ", font=FONT_SMALL,
                    bg=color, fg=color, relief="flat", padx=3, pady=2)

def col_headers(parent, cols, bg=PANEL_BG):
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", padx=24, pady=(4, 0))
    for label, w in cols:
        tk.Label(row, text=label, font=FONT_SMALL, bg=bg, fg=TEXT_DIM,
                 width=w, anchor="w").pack(side="left", padx=4, pady=6)

def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24)

def page_header(parent, title, subtitle=""):
    hdr = tk.Frame(parent, bg=DARK_BG, padx=28, pady=20)
    hdr.pack(fill="x")
    tk.Label(hdr, text=title, font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
    if subtitle:
        tk.Label(hdr, text=subtitle, font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")


# ══════════════════════════════════════════════════════════════════
#  SHELL
# ══════════════════════════════════════════════════════════════════
class MaintenanceAppShell(BaseAppShell):
    def __init__(self, parent, staff, db):
        super().__init__(parent, staff, db)
        self._nav("requests", "requests")

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=PANEL_BG, width=218,
                         highlightbackground=BORDER, highlightthickness=1)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Label(sb, text="🏢  PAMS", font=("Segoe UI", 12, "bold"),
                 bg=PANEL_BG, fg=TEXT).pack(padx=20, pady=(22, 10), anchor="w")
        uc = tk.Frame(sb, bg=HOVER_BG, padx=14, pady=10)
        uc.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(uc, text=self.staff.full_name, font=FONT_SUB, bg=HOVER_BG, fg=TEXT).pack(anchor="w")
        badge(uc, self.staff.role, ACCENT).pack(anchor="w", pady=(4, 0))
        locs = {l.id: l.city for l in self.db.get_all_locations()}
        tk.Label(uc, text=f"📍 {locs.get(self.staff.location_id,'?')}", font=FONT_SMALL,
                 bg=HOVER_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))
        self._nbtn = {}
        self._nbar = {}
        for key, label, dest in [
            ("commune",  "🏠  Apartments",        "commune"),
            ("requests", "🔧  Maintenance Jobs",   "requests"),
            ("workers",  "👷  Workers",            "workers"),
            ("jobtypes", "📋  Job Types & Prices", "jobtypes"),
            ("add",      "➕  Add Request",        "add"),
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

    def _go(self, dest):
        self._clear()
        if   dest == "commune":  MaintCommuneView(self.content, self.staff, self.db)
        elif dest == "requests": RequestsView(self.content, self.staff, self.db)
        elif dest == "workers":  WorkersView(self.content, self.staff, self.db)
        elif dest == "jobtypes": JobTypesView(self.content, self.staff, self.db)
        elif dest == "add":
            AddRequestView(self.content, self.staff, self.db,
                           on_complete=lambda: self._nav("requests", "requests"))


# ══════════════════════════════════════════════════════════════════
#  COMMUNE VIEW (maintenance variant — read-only + add maint button)
# ══════════════════════════════════════════════════════════════════
class MaintCommuneView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._all = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _build(self):
        top = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        top.pack(fill="x")
        lft = tk.Frame(top, bg=DARK_BG)
        lft.pack(side="left", fill="x", expand=True)
        tk.Label(lft, text="Apartments", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(lft, text="Click a unit to view all records, or use  ➕  to log a new maintenance issue.",
                 font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")
        self.stat_row = tk.Frame(top, bg=DARK_BG)
        self.stat_row.pack(side="right")

        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0, 10))
        self.sv = tk.StringVar()
        placeholder = "Search unit, type, status..."
        se = tk.Entry(fbar, textvariable=self.sv, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                      insertbackground=TEXT, relief="flat", bd=0, width=32,
                      highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        se.pack(side="left", ipady=7, ipadx=10)
        se.insert(0, placeholder)
        se.bind("<FocusIn>",  lambda e: se.delete(0, "end") if se.get() == placeholder else None)
        se.bind("<FocusOut>", lambda e: se.insert(0, placeholder) if se.get() == "" else None)
        self.sv.trace("w", lambda *a: self._filter())
        self._sf = tk.StringVar(value="All")
        self._sf_btns = {}
        tk.Label(fbar, text="  Filter:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left", padx=(12, 4))
        def _set_sf(v):
            self._sf.set(v)
            for k, b in self._sf_btns.items():
                b.config(bg=ACCENT if k==v else PANEL_BG, fg="white" if k==v else TEXT_DIM)
            self._filter()
        for s in ["All", "Available", "Occupied", "Under Maintenance"]:
            b = tk.Button(fbar, text=s, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                          command=lambda v=s: _set_sf(v))
            b.pack(side="left", padx=2)
            self._sf_btns[s] = b
        self._sf_btns["All"].config(bg=ACCENT, fg="white")

        outer, self.grid_inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 16))

    def _load(self):
        self._all = self.db.get_all_apartments(self.staff.location_id)
        self._render_stats()
        self._filter()

    def _render_stats(self):
        for w in self.stat_row.winfo_children(): w.destroy()
        maint = sum(1 for a in self._all if a.status == "Under Maintenance")
        cursor = self.db.get_cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM maintenance_requests m JOIN apartments a ON m.apartment_id=a.id "
            "WHERE m.status IN ('Open','In Progress') AND a.location_id=?",
            (self.staff.location_id,))
        open_count = cursor.fetchone()[0]
        for label, val, color in [("Under Maintenance", maint, WARNING),
                                   ("Open Jobs", open_count, DANGER),
                                   ("Total Units", len(self._all), TEXT)]:
            p = tk.Frame(self.stat_row, bg=CARD_BG, padx=14, pady=8)
            p.pack(side="left", padx=(0, 8))
            tk.Label(p, text=str(val), font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=color).pack()
            tk.Label(p, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

    def _filter(self):
        q = self.sv.get().strip().lower()
        if "search" in q: q = ""
        sf = self._sf.get()
        filtered = [a for a in self._all
                    if (not q or q in a.unit_number.lower() or q in a.apartment_type.lower()
                        or q in (a.status or "").lower())
                    and (sf == "All" or a.status == sf)]
        self._render_grid(filtered)

    def _render_grid(self, apts):
        for w in self.grid_inner.winfo_children(): w.destroy()
        if not apts:
            tk.Label(self.grid_inner, text="No apartments match.", font=FONT_BODY,
                     bg=DARK_BG, fg=TEXT_DIM).pack(pady=30)
            return
        COLS = 3
        for i, apt in enumerate(apts):
            r, c = divmod(i, COLS)
            self._apt_card(apt, r, c)
        for c in range(COLS):
            self.grid_inner.columnconfigure(c, weight=1, uniform="col")

    def _apt_card(self, apt, row, col):
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

        cursor = self.db.get_cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM maintenance_requests WHERE apartment_id=? AND status IN ('Open','In Progress')",
            (apt.id,))
        open_n = cursor.fetchone()[0]
        if open_n:
            tk.Label(body, text=f"🔧 {open_n} open job{'s' if open_n > 1 else ''}",
                     font=FONT_SMALL, bg=CARD_BG, fg=WARNING).pack(anchor="w", pady=(4, 0))

        tk.Label(body, text=f"{apt.apartment_type}  •  {apt.num_bedrooms}bd  •  Floor {apt.floor}",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(2, 0))

        foot = tk.Frame(body, bg=CARD_BG)
        foot.pack(fill="x", pady=(10, 0))
        tk.Label(foot, text=f"£{apt.monthly_rent:,.0f}/mo", font=("Segoe UI", 12, "bold"),
                 bg=CARD_BG, fg=ACCENT).pack(side="left")
        mkbtn(foot, "+ Job", lambda a=apt: self._quick_add(a), color=WARNING, small=True).pack(side="right")

        def click(e=None, a=apt): ApartmentDetailWindow(self, a, self.staff, self.db)
        for w in [outer, body, head]:
            try: w.bind("<Button-1>", click)
            except Exception: pass
        outer.bind("<Enter>", lambda e: outer.config(highlightbackground=ACCENT, highlightthickness=2))
        outer.bind("<Leave>", lambda e: outer.config(highlightbackground=BORDER, highlightthickness=1))

    def _quick_add(self, apt):
        win = tk.Toplevel(self)
        win.title(f"Add Maintenance — Unit {apt.unit_number}")
        win.geometry("700x560")
        win.configure(bg=DARK_BG)
        AddRequestView(win, self.staff, self.db,
                       on_complete=lambda: (win.destroy(), self._load()),
                       preselect_apt=apt)


# ══════════════════════════════════════════════════════════════════
#  REQUESTS VIEW — full job list
# ══════════════════════════════════════════════════════════════════
class RequestsView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._requests = []
        self._shown = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _get_export_requests(self):
        cols = ["#", "Unit", "Title", "Category", "Priority",
                "Status", "Reported", "Cost (£)", "Time (hrs)", "Tenant"]
        rows = [(r.id, getattr(r, "unit_number", ""), r.title,
                 r.category or "", r.priority, r.status,
                 r.reported_date or "", f"{r.cost:.2f}",
                 f"{r.time_taken_hours:.1f}", getattr(r, "tenant_name", ""))
                for r in self._shown]
        return cols, rows

    def _build(self):
        page_header(self, "Maintenance Jobs",
                    "All requests at your location — click a row to manage, assign, schedule or resolve.")
        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0, 6))
        self._sf = tk.StringVar(value="All")
        self._sf_btns = {}
        tk.Label(fbar, text="Status:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        def _set_sf(v):
            self._sf.set(v)
            for k, b in self._sf_btns.items():
                b.config(bg=ACCENT if k==v else PANEL_BG, fg="white" if k==v else TEXT_DIM)
            self._filter()
        for s in ["All", "Open", "In Progress", "Resolved", "Closed"]:
            b = tk.Button(fbar, text=s, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                          command=lambda v=s: _set_sf(v))
            b.pack(side="left", padx=2)
            self._sf_btns[s] = b
        self._sf_btns["All"].config(bg=ACCENT, fg="white")
        self._pf = tk.StringVar(value="All")
        self._pf_btns = {}
        tk.Label(fbar, text="  Priority:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left", padx=(12, 4))
        def _set_pf(v):
            self._pf.set(v)
            for k, b in self._pf_btns.items():
                b.config(bg=ACCENT if k==v else PANEL_BG, fg="white" if k==v else TEXT_DIM)
            self._filter()
        for s in ["All", "Urgent", "High", "Medium", "Low"]:
            b = tk.Button(fbar, text=s, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                          command=lambda v=s: _set_pf(v))
            b.pack(side="left", padx=2)
            self._pf_btns[s] = b
        self._pf_btns["All"].config(bg=ACCENT, fg="white")
        export_bar(fbar, "Maintenance Jobs", self._get_export_requests).pack(side="right")
        self.sum_row = tk.Frame(self, bg=DARK_BG)
        self.sum_row.pack(fill="x", padx=28, pady=(0, 4))
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)

    def _load(self):
        self._requests = self._fetch_all()
        self._render_stats()
        self._filter()

    def _fetch_all(self):
        cursor = self.db.get_cursor()
        cursor.execute("""
            SELECT m.*, a.unit_number, a.apartment_type, loc.city,
                   t.first_name||' '||t.last_name AS tenant_name,
                   t.phone AS tenant_phone, t.email AS tenant_email
            FROM maintenance_requests m
            JOIN apartments a  ON m.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            LEFT JOIN tenants t ON m.tenant_id=t.id
            WHERE loc.id=?
            ORDER BY CASE m.priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
                     CASE m.status WHEN 'Open' THEN 1 WHEN 'In Progress' THEN 2 WHEN 'Resolved' THEN 3 ELSE 4 END,
                     m.reported_date DESC
        """, (self.staff.location_id,))
        result = []
        for r in cursor.fetchall():
            from models import MaintenanceRequest
            m = MaintenanceRequest(
                id=r["id"], lease_id=r["lease_id"], apartment_id=r["apartment_id"],
                tenant_id=r["tenant_id"], title=r["title"],
                description=r["description"] or "", category=r["category"] or "",
                priority=r["priority"], status=r["status"],
                reported_date=r["reported_date"], scheduled_date=r["scheduled_date"],
                resolved_date=r["resolved_date"], resolution_notes=r["resolution_notes"] or "",
                cost=r["cost"] or 0.0, time_taken_hours=r["time_taken_hours"] or 0.0,
                assigned_staff_id=r["assigned_staff_id"], created_at=r["created_at"])
            m.unit_number  = r["unit_number"]  or ""
            m.city         = r["city"]         or ""
            m.tenant_name  = r["tenant_name"]  or ""
            m.tenant_phone = r["tenant_phone"] or ""
            m.tenant_email = r["tenant_email"] or ""
            result.append(m)
        return result

    def _render_stats(self):
        for w in self.sum_row.winfo_children(): w.destroy()
        counts = {}
        for r in self._requests: counts[r.status] = counts.get(r.status, 0) + 1
        for label, key, col in [("Open","Open",DANGER),("In Progress","In Progress",ACCENT),
                                  ("Resolved","Resolved",SUCCESS),("Total",None,TEXT)]:
            val = len(self._requests) if key is None else counts.get(key, 0)
            p = tk.Frame(self.sum_row, bg=CARD_BG, padx=14, pady=8)
            p.pack(side="left", padx=(0, 8))
            tk.Label(p, text=str(val), font=("Segoe UI", 15, "bold"), bg=CARD_BG, fg=col).pack()
            tk.Label(p, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

    def _filter(self):
        sf, pf = self._sf.get(), self._pf.get()
        filtered = [r for r in self._requests
                    if (sf == "All" or r.status == sf) and (pf == "All" or r.priority == pf)]
        self._shown = filtered
        self._render_table(filtered)

    def _render_table(self, reqs):
        for w in self.table.winfo_children(): w.destroy()
        if not reqs:
            tk.Label(self.table, text="No requests match.", font=FONT_BODY,
                     bg=DARK_BG, fg=TEXT_DIM).pack(pady=30)
            return
        COLS = [("#", 4), ("Unit", 7), ("Title", 26), ("Category", 11),
                ("Priority", 9), ("Status", 11), ("Reported", 11), ("Cost", 8)]
        col_headers(self.table, COLS)
        for req in reqs:
            row = tk.Frame(self.table, bg=CARD_BG, cursor="hand2")
            row.pack(fill="x", padx=24)
            for val, w in [(str(req.id),4),(req.unit_number,7),(req.title[:34],26),
                           (req.category,11),(req.priority,9),(req.status,11),
                           (req.reported_date,11),(f"£{req.cost:,.0f}",8)]:
                col = (sc(val) if val == req.status else
                       PRIORITY_COLORS.get(val, TEXT_DIM) if val == req.priority else TEXT)
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=7)
            row.bind("<Button-1>", lambda e, r=req: RequestDetailWindow(self, r, self.staff, self.db, on_save=self._load))
            row.bind("<Enter>", lambda e, r=row: r.config(bg=HOVER_BG))
            row.bind("<Leave>", lambda e, r=row: r.config(bg=CARD_BG))
            divider(self.table)


# ══════════════════════════════════════════════════════════════════
#  REQUEST DETAIL WINDOW
# ══════════════════════════════════════════════════════════════════
class RequestDetailWindow(tk.Toplevel):
    def __init__(self, parent, req, staff, db, on_save=None):
        super().__init__(parent)
        self.req = req
        self.staff = staff
        self.db = db
        self.on_save = on_save
        self.title(f"Job #{req.id}  —  {req.title}  |  Unit {getattr(req,'unit_number','?')}")
        self.geometry("940x680")
        self.configure(bg=DARK_BG)
        self._nb_style()
        self._build()

    def _nb_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("M.TNotebook", background=DARK_BG, borderwidth=0, tabmargins=0)
        s.configure("M.TNotebook.Tab", background=PANEL_BG, foreground=TEXT_DIM,
                    font=FONT_BODY, padding=[16, 8])
        s.map("M.TNotebook.Tab", background=[("selected", CARD_BG)], foreground=[("selected", TEXT)])

    def _build(self):
        req = self.req
        pri_col = PRIORITY_COLORS.get(req.priority, TEXT_DIM)
        hdr = tk.Frame(self, bg=PANEL_BG)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=pri_col, height=4).pack(fill="x")
        ih = tk.Frame(hdr, bg=PANEL_BG, padx=28, pady=16)
        ih.pack(fill="x")
        lh = tk.Frame(ih, bg=PANEL_BG)
        lh.pack(side="left")
        tk.Label(lh, text=req.title, font=FONT_HEAD, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(lh, text=f"Unit {getattr(req,'unit_number','?')}  •  {req.category}  •  Reported: {req.reported_date}",
                 font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
        rh = tk.Frame(ih, bg=PANEL_BG)
        rh.pack(side="right")
        badge(rh, req.status).pack()
        priority_badge(rh, req.priority).pack(pady=(4, 0))

        nb = ttk.Notebook(self, style="M.TNotebook")
        nb.pack(fill="both", expand=True)
        self._tab_details(nb)
        self._tab_assign(nb)
        self._tab_schedule(nb)
        self._tab_resolve(nb)

    def _tab(self, nb, title):
        f = tk.Frame(nb, bg=CARD_BG)
        nb.add(f, text=f"  {title}  ")
        return f

    # ── Details ───────────────────────────────────────────────────
    def _tab_details(self, nb):
        frame = self._tab(nb, "Details")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)
        req = self.req

        sec_hdr(inner, "Request Information")
        info_grid(inner, [
            ("Job #",        f"#{req.id}"),
            ("Title",        req.title),
            ("Category",     req.category),
            ("Priority",     req.priority),
            ("Status",       req.status),
            ("Reported",     req.reported_date or "—"),
            ("Scheduled",    req.scheduled_date or "Not scheduled"),
            ("Resolved",     req.resolved_date or "—"),
            ("Cost",         f"£{req.cost:,.2f}" if req.cost else "—"),
            ("Hours",        f"{req.time_taken_hours:.1f} hrs" if req.time_taken_hours else "—"),
        ], cols=3)

        if req.description:
            sec_hdr(inner, "Description")
            tk.Label(inner, text=req.description, font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM,
                     wraplength=750, justify="left").pack(anchor="w", padx=28, pady=(0, 12))

        if req.resolution_notes:
            sec_hdr(inner, "Resolution Notes")
            tk.Label(inner, text=req.resolution_notes, font=FONT_BODY, bg=CARD_BG, fg=SUCCESS,
                     wraplength=750, justify="left").pack(anchor="w", padx=28, pady=(0, 12))

        if getattr(req, "tenant_name", ""):
            sec_hdr(inner, "Tenant")
            info_grid(inner, [("Name", req.tenant_name),
                               ("Phone", getattr(req,"tenant_phone","—")),
                               ("Email", getattr(req,"tenant_email","—"))], cols=3)

        # Assignments summary
        assignments = self.db.get_assignments_for_maintenance(req.id)
        sec_hdr(inner, f"Assigned Workers  ({len(assignments)})")
        if not assignments:
            tk.Label(inner, text="No workers assigned.", font=FONT_BODY,
                     bg=CARD_BG, fg=TEXT_DIM).pack(padx=28, pady=6, anchor="w")
        else:
            for a in assignments:
                wc = tk.Frame(inner, bg=PANEL_BG, padx=16, pady=10)
                wc.pack(fill="x", padx=24, pady=3)
                wt = tk.Frame(wc, bg=PANEL_BG)
                wt.pack(fill="x")
                tk.Label(wt, text=f"👷  {a.worker_name}", font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
                tk.Label(wt, text=f"Assigned: {a.assigned_date}", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(side="right")
                tk.Label(wc, text=f"📞 {a.worker_phone}  •  £{a.hourly_rate:.0f}/hr  •  {a.specialties}",
                         font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")
                if a.notes:
                    tk.Label(wc, text=a.notes, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w")

        # Quick update
        sec_hdr(inner, "Quick Update")
        qf = tk.Frame(inner, bg=CARD_BG, padx=28, pady=8)
        qf.pack(fill="x")
        qf.columnconfigure(0, weight=1); qf.columnconfigure(1, weight=1)
        self.vq_pri  = combo_var(qf, "Priority", ["Urgent","High","Medium","Low"],   0, 0, default=req.priority, width=14)
        self.vq_stat = combo_var(qf, "Status",   ["Open","In Progress","Resolved","Closed"], 0, 1, default=req.status, width=14)
        nav = tk.Frame(qf, bg=CARD_BG, pady=10)
        nav.grid(row=2, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Save", self._quick_save, small=True).pack(side="right")

    def _quick_save(self):
        req = self.db.get_maintenance_by_id(self.req.id)
        if req:
            req.priority = self.vq_pri.get()
            req.status   = self.vq_stat.get()
            self.db.update_maintenance(req)
            self.req.priority = req.priority
            self.req.status   = req.status
            messagebox.showinfo("Saved", "Priority and status updated.", parent=self)
            if self.on_save: self.on_save()

    # ── Assign Worker ─────────────────────────────────────────────
    def _tab_assign(self, nb):
        frame = self._tab(nb, "Assign Worker")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        sec_hdr(inner, "Current Assignments")
        self._asgn_frame = tk.Frame(inner, bg=CARD_BG)
        self._asgn_frame.pack(fill="x")
        self._render_assignments()

        sec_hdr(inner, f"Workers  (your location  —  category: {self.req.category})")
        workers = self.db.get_workers(location_id=self.staff.location_id)
        cat = self.req.category
        matching = [w for w in workers if w.availability == "Available" and cat in (w.specialties or "")]
        other    = [w for w in workers if w.availability == "Available" and cat not in (w.specialties or "")]
        unavail  = [w for w in workers if w.availability != "Available"]

        self._sel_worker = tk.IntVar(value=-1)
        self._worker_indicators = {}

        if matching:
            tk.Label(inner, text=f"✓  Specialists in {cat}", font=FONT_SMALL,
                     bg=CARD_BG, fg=SUCCESS).pack(anchor="w", padx=28, pady=(8, 4))
        for w in matching: self._worker_row(inner, w, highlight=True)
        if other:
            tk.Label(inner, text="Other available:", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", padx=28, pady=(10, 4))
        for w in other: self._worker_row(inner, w)
        if unavail:
            tk.Label(inner, text="Unavailable:", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=28, pady=(10, 4))
        for w in unavail: self._worker_row(inner, w, disabled=True)

        sec_hdr(inner, "Notes")
        self.assign_notes = tk.Text(inner, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                                     relief="flat", bd=0, width=70, height=3,
                                     highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.assign_notes.pack(padx=28, pady=(4, 0), anchor="w")
        nav = tk.Frame(inner, bg=CARD_BG, padx=28, pady=12)
        nav.pack(fill="x")
        mkbtn(nav, "Assign Selected Worker ✓", self._do_assign, color=SUCCESS).pack(side="right")

    def _worker_row(self, parent, w, highlight=False, disabled=False):
        bg = PANEL_BG if highlight else CARD_BG
        row = tk.Frame(parent, bg=bg, padx=16, pady=10)
        row.pack(fill="x", padx=24, pady=2)
        ind = tk.Canvas(row, width=22, height=22, bg=bg, highlightthickness=0)
        ind.create_oval(2, 2, 20, 20, outline=TEXT_MUTED if disabled else BORDER, width=2)
        ind.pack(side="left", padx=(0, 12))
        if not disabled:
            self._worker_indicators[w.id] = ind
        info = tk.Frame(row, bg=bg)
        info.pack(side="left", fill="x", expand=True)
        top = tk.Frame(info, bg=bg)
        top.pack(fill="x")
        tk.Label(top, text=f"{w.first_name} {w.last_name}", font=FONT_SUB,
                 bg=bg, fg=TEXT if not disabled else TEXT_MUTED).pack(side="left")
        avail_col = AVAIL_COLORS.get(w.availability, TEXT_DIM)
        tk.Label(top, text=f"  {w.availability}", font=FONT_SMALL, bg=bg, fg=avail_col).pack(side="left")
        for sp in (w.specialties or "").split(","):
            sp = sp.strip()
            if sp:
                col = SUCCESS if sp == self.req.category else TEXT_MUTED
                tk.Label(top, text=f" {sp} ", font=FONT_SMALL, bg=col+"22", fg=col).pack(side="left", padx=2)
        tk.Label(info, text=f"📞 {w.phone}  •  £{w.hourly_rate:.0f}/hr  •  {w.notes or ''}",
                 font=FONT_SMALL, bg=bg, fg=TEXT_DIM).pack(anchor="w")
        def click(e=None, wid=w.id):
            self._sel_worker.set(wid)
            self._refresh_worker_selection()
        for wdg in [row, info, top]:
            try: wdg.bind("<Button-1>", click)
            except Exception: pass

    def _refresh_worker_selection(self):
        sel = self._sel_worker.get()
        for wid, ind in self._worker_indicators.items():
            ind.delete("all")
            if wid == sel:
                ind.create_oval(2, 2, 20, 20, fill=ACCENT, outline="")
                ind.create_text(11, 11, text="✓", fill="white", font=("Segoe UI", 9, "bold"))
            else:
                ind.create_oval(2, 2, 20, 20, outline=BORDER, width=2)

    def _render_assignments(self):
        for w in self._asgn_frame.winfo_children(): w.destroy()
        assignments = self.db.get_assignments_for_maintenance(self.req.id)
        if not assignments:
            tk.Label(self._asgn_frame, text="No workers assigned yet.", font=FONT_BODY,
                     bg=CARD_BG, fg=TEXT_DIM).pack(padx=28, pady=6, anchor="w")
            return
        for a in assignments:
            row = tk.Frame(self._asgn_frame, bg=PANEL_BG, padx=16, pady=8)
            row.pack(fill="x", padx=24, pady=3)
            top = tk.Frame(row, bg=PANEL_BG)
            top.pack(fill="x")
            tk.Label(top, text=f"👷  {a.worker_name}", font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
            tk.Label(top, text=f"Assigned: {a.assigned_date}", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(side="left", padx=12)
            mkbtn(top, "Remove", lambda aid=a.id, wid=a.worker_id: self._remove_assignment(aid, wid),
                  color=DANGER, small=True).pack(side="right")
            tk.Label(row, text=f"£{a.hourly_rate:.0f}/hr  •  {a.specialties}",
                     font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")

    def _do_assign(self):
        wid = self._sel_worker.get()
        if wid < 0:
            messagebox.showwarning("No Selection", "Please select a worker.", parent=self)
            return
        notes = self.assign_notes.get("1.0", "end-1c").strip()
        self.db.assign_worker(self.req.id, wid, self.staff.id, notes)
        w = self.db.get_worker_by_id(wid)
        messagebox.showinfo("Assigned", f"{w.first_name} {w.last_name} assigned.\nStatus set to Busy.", parent=self)
        self._render_assignments()
        if self.on_save: self.on_save()

    def _remove_assignment(self, aid, wid):
        if not messagebox.askyesno("Remove", "Remove this worker?", parent=self): return
        self.db.remove_assignment(aid, wid)
        self._render_assignments()
        if self.on_save: self.on_save()

    # ── Schedule ──────────────────────────────────────────────────
    def _tab_schedule(self, nb):
        frame = self._tab(nb, "Schedule & Notify")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)
        req = self.req

        sec_hdr(inner, "Scheduling")
        form = tk.Frame(inner, bg=CARD_BG, padx=28, pady=12)
        form.pack(fill="x")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)
        self.v_sched = entry_var(form, "Scheduled Date * (YYYY-MM-DD)", 0, 0,
                                  default=req.scheduled_date or "", width=18)
        self.v_time  = entry_var(form, "Time (HH:MM)", 0, 1, default="09:00", width=12)

        sec_hdr(inner, "Tenant Notification  (emulated email)")
        nf = tk.Frame(inner, bg=CARD_BG, padx=28, pady=8)
        nf.pack(fill="x")
        tenant_line = ""
        if getattr(req, "tenant_name", ""):
            tenant_line = f"To: {req.tenant_name}  <{getattr(req,'tenant_email','')}>  📞 {getattr(req,'tenant_phone','')}"
        tk.Label(nf, text=tenant_line or "No tenant linked to this request.",
                 font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
        self.notif_txt = tk.Text(nf, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", bd=0, width=70, height=6,
                                  highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.notif_txt.pack(fill="x", pady=(8, 0))
        self.notif_txt.insert("1.0",
            f"Dear {getattr(req,'tenant_name','Tenant')},\n\n"
            f"A maintenance visit has been scheduled for Unit {getattr(req,'unit_number','—')} "
            f"to address: {req.title}.\n\n"
            f"Scheduled: [DATE] at [TIME].\n\n"
            f"Please ensure access is available. Contact us with any queries.\n\nKind regards,\nParagon Maintenance Team")

        nav = tk.Frame(inner, bg=CARD_BG, padx=28, pady=12)
        nav.pack(fill="x")
        mkbtn(nav, "Save Schedule & Preview Notification", self._save_schedule, color=ACCENT).pack(side="right")

    def _save_schedule(self):
        sched = self.v_sched.get().strip()
        time  = self.v_time.get().strip()
        if not sched:
            messagebox.showwarning("Missing", "Please enter a scheduled date.", parent=self)
            return
        req = self.db.get_maintenance_by_id(self.req.id)
        if req:
            req.scheduled_date = sched
            if req.status == "Open": req.status = "In Progress"
            self.db.update_maintenance(req)
            self.req.scheduled_date = sched
            self.req.status = req.status
        body = self.notif_txt.get("1.0","end-1c").replace("[DATE]",sched).replace("[TIME]",time)
        NotificationPreview(self, getattr(self.req,"tenant_name","Tenant"),
                            getattr(self.req,"tenant_email",""), sched, time, body)
        if self.on_save: self.on_save()

    # ── Resolve ───────────────────────────────────────────────────
    def _tab_resolve(self, nb):
        frame = self._tab(nb, "Resolve & Log")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)
        req = self.req

        sec_hdr(inner, "Resolution")
        form = tk.Frame(inner, bg=CARD_BG, padx=28, pady=12)
        form.pack(fill="x")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1); form.columnconfigure(2, weight=1)

        self.v_res_date = entry_var(form, "Resolution Date *", 0, 0,
                                     default=req.resolved_date or str(date.today()), width=16)
        self.v_cost     = entry_var(form, "Total Cost (£) *",  0, 1,
                                     default=str(req.cost) if req.cost else "", width=16)
        self.v_hours    = entry_var(form, "Hours Taken *",     0, 2,
                                     default=str(req.time_taken_hours) if req.time_taken_hours else "", width=14)

        tk.Label(form, text="Resolution Notes *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=2, column=0, columnspan=3, sticky="w", padx=6, pady=(10, 2))
        self.res_notes = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", bd=0, width=70, height=6,
                                  highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.res_notes.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6)
        if req.resolution_notes:
            self.res_notes.insert("1.0", req.resolution_notes)

        # Price reference from job types
        types = self.db.get_maintenance_types(category=req.category)
        if types:
            sec_hdr(inner, f"Price Reference  —  {req.category}")
            ref_frame = tk.Frame(inner, bg=CARD_BG, padx=28, pady=4)
            ref_frame.pack(fill="x")
            for mt in types[:4]:
                tr = tk.Frame(ref_frame, bg=PANEL_BG, padx=12, pady=8)
                tr.pack(fill="x", pady=2)
                tk.Label(tr, text=mt["name"], font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
                tk.Label(tr, text=f"£{mt['typical_cost_min']:.0f}–£{mt['typical_cost_max']:.0f}  |  ~{mt['typical_hours']:.1f} hrs",
                         font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(side="right")
                if mt["notes"]:
                    tk.Label(tr, text=mt["notes"], font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w")

        nav = tk.Frame(inner, bg=CARD_BG, padx=28, pady=12)
        nav.pack(fill="x")
        mkbtn(nav, "Mark Resolved & Log ✓", self._do_resolve, color=SUCCESS).pack(side="right")

    def _do_resolve(self):
        res_date = self.v_res_date.get().strip()
        notes    = self.res_notes.get("1.0","end-1c").strip()
        if not res_date or not notes:
            messagebox.showwarning("Missing", "Fill in resolution date and notes.", parent=self)
            return
        try:
            cost  = float(self.v_cost.get().strip() or "0")
            hours = float(self.v_hours.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("Invalid", "Cost and hours must be numbers.", parent=self)
            return
        req = self.db.get_maintenance_by_id(self.req.id)
        if req:
            req.status = "Resolved"; req.resolved_date = res_date
            req.resolution_notes = notes; req.cost = cost; req.time_taken_hours = hours
            self.db.update_maintenance(req)
        messagebox.showinfo("Resolved ✓",
                            f"Job #{self.req.id} marked Resolved.\nCost: £{cost:,.2f}  |  {hours:.1f} hrs",
                            parent=self)
        if self.on_save: self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATION PREVIEW
# ══════════════════════════════════════════════════════════════════
class NotificationPreview(tk.Toplevel):
    def __init__(self, parent, tenant_name, tenant_email, sched_date, sched_time, body):
        super().__init__(parent)
        self.title("Maintenance Notification — Preview")
        self.geometry("560x420")
        self.configure(bg=DARK_BG)
        page_header(self, "Notification Preview", "Emulated — no real email sent.")
        card = tk.Frame(self, bg=PANEL_BG, padx=32, pady=24,
                       highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 12))
        tk.Label(card, text="📅  Maintenance Appointment Scheduled",
                 font=("Segoe UI",13,"bold"), bg="white", fg=ACCENT).pack(anchor="w")
        tk.Label(card, text=f"To: {tenant_name}  <{tenant_email}>",
                 font=FONT_SMALL, bg="white", fg=TEXT_DIM).pack(anchor="w", pady=(2,12))
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(0,10))
        tk.Label(card, text=body, font=("Segoe UI",10), bg="white", fg=TEXT,
                 justify="left", wraplength=460).pack(anchor="w")
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(10,4))
        tk.Label(card, text=f"Scheduled: {sched_date} at {sched_time}",
                 font=FONT_SMALL, bg="white", fg=TEXT_MUTED).pack(anchor="w")
        mkbtn(self, "Close", self.destroy, color=TEXT_MUTED, small=True).pack(pady=(0,8))


# ══════════════════════════════════════════════════════════════════
#  WORKERS VIEW
# ══════════════════════════════════════════════════════════════════
class WorkersView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Workers", "Your location's maintenance workforce.")
        outer, self.inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._render()

    def _render(self):
        for w in self.inner.winfo_children(): w.destroy()
        workers = self.db.get_workers(location_id=self.staff.location_id)

        pills = tk.Frame(self.inner, bg=DARK_BG)
        pills.pack(fill="x", padx=28, pady=(8,12))
        avail = sum(1 for w in workers if w.availability=="Available")
        busy  = sum(1 for w in workers if w.availability=="Busy")
        leave = sum(1 for w in workers if w.availability=="On Leave")
        for label, val, col in [("Available",avail,SUCCESS),("Busy",busy,WARNING),
                                  ("On Leave",leave,ACCENT2),("Total",len(workers),TEXT)]:
            p = tk.Frame(pills, bg=CARD_BG, padx=14, pady=8)
            p.pack(side="left", padx=(0,8))
            tk.Label(p, text=str(val), font=("Segoe UI",15,"bold"), bg=CARD_BG, fg=col).pack()
            tk.Label(p, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

        add_row = tk.Frame(self.inner, bg=DARK_BG, padx=28)
        add_row.pack(fill="x", pady=(0,8))
        mkbtn(add_row, "➕  Add Worker",
              lambda: AddWorkerDialog(self, self.staff, self.db, on_save=self._render),
              small=True).pack(side="right")

        for group, color in [("Available",SUCCESS),("Busy",WARNING),("On Leave",ACCENT2)]:
            gw = [w for w in workers if w.availability==group]
            if not gw: continue
            sec_hdr(self.inner, f"{group}  ({len(gw)})")
            for w in gw: self._worker_card(w)

    def _worker_card(self, w):
        card = tk.Frame(self.inner, bg=CARD_BG, padx=20, pady=14)
        card.pack(fill="x", padx=24, pady=4)
        top = tk.Frame(card, bg=CARD_BG)
        top.pack(fill="x")
        tk.Label(top, text=f"{w.first_name} {w.last_name}", font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        badge(top, w.availability, AVAIL_COLORS.get(w.availability, TEXT_DIM)).pack(side="right")

        spec_row = tk.Frame(card, bg=CARD_BG)
        spec_row.pack(anchor="w", pady=(4,0))
        for sp in (w.specialties or "").split(","):
            sp = sp.strip()
            if sp:
                tk.Label(spec_row, text=f" {sp} ", font=FONT_SMALL,
                         bg="#DBEAFE", fg=ACCENT).pack(side="left", padx=(0,4))

        meta = tk.Frame(card, bg=CARD_BG)
        meta.pack(fill="x", pady=(6,0))
        tk.Label(meta, text=f"📞 {w.phone}", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=(0,14))
        tk.Label(meta, text=f"✉  {w.email}", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=(0,14))
        tk.Label(meta, text=f"£{w.hourly_rate:.0f}/hr", font=FONT_SMALL, bg=CARD_BG, fg=ACCENT).pack(side="left")
        if w.notes:
            tk.Label(meta, text=f"  •  {w.notes}", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MUTED).pack(side="left")

        avail_row = tk.Frame(card, bg=CARD_BG)
        avail_row.pack(anchor="e", pady=(8,0))
        tk.Label(avail_row, text="Set:", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=(0,6))
        for avail, col in [("Available",SUCCESS),("Busy",WARNING),("On Leave",ACCENT2)]:
            if avail != w.availability:
                mkbtn(avail_row, avail,
                      lambda a=avail, wid=w.id: self._set_avail(wid, a),
                      color=col, small=True).pack(side="left", padx=(0,4))

    def _set_avail(self, worker_id, avail):
        self.db.update_worker_availability(worker_id, avail)
        self._render()


# ══════════════════════════════════════════════════════════════════
#  ADD WORKER DIALOG
# ══════════════════════════════════════════════════════════════════
class AddWorkerDialog(tk.Toplevel):
    def __init__(self, parent, staff, db, on_save=None):
        super().__init__(parent)
        self.staff = staff; self.db = db; self.on_save = on_save
        self.title("Add New Worker")
        self.geometry("520x420")
        self.configure(bg=DARK_BG)
        self.grab_set()
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Add Worker to Team", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)
        self.v_fn   = entry_var(form, "First Name *",       0, 0, width=20)
        self.v_ln   = entry_var(form, "Last Name *",        0, 1, width=20)
        self.v_ph   = entry_var(form, "Phone *",            2, 0, width=20)
        self.v_em   = entry_var(form, "Email",              2, 1, width=20)
        self.v_rate = entry_var(form, "Hourly Rate (£) *",  4, 0, width=14)
        self.v_av   = combo_var(form, "Availability", ["Available","Busy","On Leave"], 4, 1, width=16)
        tk.Label(form, text="Specialties (comma-separated) *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=6, column=0, columnspan=2, sticky="w", padx=6, pady=(8,2))
        self.v_sp = tk.StringVar()
        tk.Entry(form, textvariable=self.v_sp, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0, width=44,
                 highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                 ).grid(row=7, column=0, columnspan=2, sticky="ew", padx=6, ipady=4)
        tk.Label(form, text="e.g.  Plumbing,Heating  or  Electrical,General",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_MUTED).grid(row=8, column=0, columnspan=2, sticky="w", padx=6)
        self.v_nt = entry_var(form, "Notes", 9, 0, colspan=2, width=44)
        nav = tk.Frame(form, bg=CARD_BG, pady=14)
        nav.grid(row=11, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Add Worker ✓", self._save, color=SUCCESS).pack(side="right")

    def _save(self):
        fn = self.v_fn.get().strip(); ln = self.v_ln.get().strip()
        ph = self.v_ph.get().strip(); sp = self.v_sp.get().strip()
        if not all([fn, ln, ph, sp]):
            messagebox.showwarning("Missing Fields", "Fill in required fields.", parent=self)
            return
        try: rate = float(self.v_rate.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid", "Enter a valid hourly rate.", parent=self)
            return
        self.db.add_worker(fn, ln, ph, self.v_em.get().strip(), sp, rate,
                           self.staff.location_id, self.v_av.get(), self.v_nt.get().strip())
        messagebox.showinfo("Added", f"{fn} {ln} added.", parent=self)
        if self.on_save: self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  JOB TYPES VIEW
# ══════════════════════════════════════════════════════════════════
class JobTypesView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff; self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Job Types & Price Guide",
                    "Standard job catalogue with typical costs, hours and required specialties.")
        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0,8))
        tk.Label(fbar, text="Category:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        cats = ["All"] + self.db.get_maintenance_categories()
        self._cat_v = tk.StringVar(value="All")
        self._cat_btns = {}
        def _set_cat(v):
            self._cat_v.set(v)
            for k, b in self._cat_btns.items():
                b.config(bg=ACCENT if k==v else PANEL_BG, fg="white" if k==v else TEXT_DIM)
            self._render()
        for cat in cats:
            b = tk.Button(fbar, text=cat, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                          command=lambda v=cat: _set_cat(v))
            b.pack(side="left", padx=2)
            self._cat_btns[cat] = b
        self._cat_btns["All"].config(bg=ACCENT, fg="white")
        outer, self.inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._render()

    def _render(self):
        for w in self.inner.winfo_children(): w.destroy()
        cat = self._cat_v.get()
        types = self.db.get_maintenance_types(category=None if cat=="All" else cat)
        cats_grouped = {}
        for mt in types: cats_grouped.setdefault(mt["category"], []).append(mt)
        for cat_name, items in cats_grouped.items():
            sec_hdr(self.inner, cat_name)
            COLS = [("Job Type",20),("Description",32),("Cost Range",14),
                    ("Hrs",7),("Specialty",15),("Notes",22)]
            col_headers(self.inner, COLS)
            for mt in items:
                row = tk.Frame(self.inner, bg=CARD_BG)
                row.pack(fill="x", padx=24)
                for val, w in [
                    (mt["name"], 20),
                    (mt["description"][:40], 32),
                    (f"£{mt['typical_cost_min']:.0f}–£{mt['typical_cost_max']:.0f}", 14),
                    (f"{mt['typical_hours']:.1f}", 7),
                    (mt["required_specialty"], 15),
                    ((mt["notes"] or "—")[:30], 22),
                ]:
                    tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                             width=w, anchor="w").pack(side="left", padx=4, pady=6)
                divider(self.inner)


# ══════════════════════════════════════════════════════════════════
#  ADD REQUEST VIEW
# ══════════════════════════════════════════════════════════════════
class AddRequestView(tk.Frame):
    def __init__(self, parent, staff, db, on_complete=None, preselect_apt=None):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff; self.db = db
        self.on_complete = on_complete
        self.preselect_apt = preselect_apt
        self._active_lease = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Add Maintenance Request", "Log a new issue for investigation and scheduling.")
        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28)
        form = tk.Frame(inner, bg=CARD_BG, padx=32, pady=24)
        form.pack(fill="x")
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1); form.columnconfigure(2, weight=1)

        tk.Label(form, text="New Maintenance Request", font=FONT_TITLE, bg=CARD_BG, fg=TEXT
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,16))

        # Apartment picker
        apts = self.db.get_all_apartments(self.staff.location_id)
        apt_labels = [f"Unit {a.unit_number}  ({a.apartment_type}, {a.location_city})" for a in apts]
        self._apt_map = {lbl: a for lbl, a in zip(apt_labels, apts)}

        default_lbl = ""
        if self.preselect_apt:
            default_lbl = next((lbl for lbl, a in self._apt_map.items()
                                if a.id == self.preselect_apt.id), "")

        tk.Label(form, text="Apartment *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(8,2))
        self.v_apt = tk.StringVar(value=default_lbl or (apt_labels[0] if apt_labels else ""))
        cb_apt = ttk.Combobox(form, textvariable=self.v_apt, values=apt_labels,
                               font=FONT_BODY, width=55, state="readonly")
        cb_apt.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6, pady=(0,4))
        cb_apt.bind("<<ComboboxSelected>>", self._on_apt_change)

        self.v_title = entry_var(form, "Title *",    3, 0, width=28)
        cats = self.db.get_maintenance_categories()
        self.v_cat   = combo_var(form, "Category *", cats,                         3, 1, width=16)
        self.v_pri   = combo_var(form, "Priority *", ["Urgent","High","Medium","Low"], 3, 2, default="Medium", width=12)
        self.v_date  = entry_var(form, "Date Reported *", 5, 0, default=str(date.today()), width=16)

        tk.Label(form, text="Tenant (if applicable)", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=5, column=1, sticky="w", padx=6, pady=(8,2))
        self.v_tenant = tk.StringVar(value="None")
        self.cb_tenant = ttk.Combobox(form, textvariable=self.v_tenant, values=["None"],
                                       font=FONT_BODY, width=26, state="readonly")
        self.cb_tenant.grid(row=6, column=1, columnspan=2, sticky="ew", padx=6, pady=(0,4))

        tk.Label(form, text="Description *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=7, column=0, columnspan=3, sticky="w", padx=6, pady=(8,2))
        self.v_desc = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                               relief="flat", bd=0, width=70, height=5,
                               highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.v_desc.grid(row=8, column=0, columnspan=3, sticky="ew", padx=6)

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=9, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Cancel", lambda: self.on_complete and self.on_complete(), color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Submit Request ✓", self._submit, color=SUCCESS).pack(side="right")

        if self.preselect_apt:
            self._on_apt_change(None)

    def _on_apt_change(self, _event):
        apt = self._apt_map.get(self.v_apt.get())
        if not apt: return
        lease = self.db.get_active_lease_for_apartment(apt.id)
        if lease:
            self.cb_tenant.config(values=[lease.tenant_name, "None"])
            self.v_tenant.set(lease.tenant_name)
            self._active_lease = lease
        else:
            self.cb_tenant.config(values=["None"])
            self.v_tenant.set("None")
            self._active_lease = None

    def _submit(self):
        from models import MaintenanceRequest
        apt = self._apt_map.get(self.v_apt.get())
        if not apt:
            messagebox.showwarning("Missing", "Select an apartment.", parent=self)
            return
        title = self.v_title.get().strip()
        desc  = self.v_desc.get("1.0","end-1c").strip()
        if not title or not desc:
            messagebox.showwarning("Missing", "Fill in title and description.", parent=self)
            return
        lease = self._active_lease
        tenant_id = lease.tenant_id if (lease and self.v_tenant.get() != "None") else None
        req = MaintenanceRequest(
            apartment_id=apt.id, lease_id=lease.id if lease else None,
            tenant_id=tenant_id, title=title, description=desc,
            category=self.v_cat.get(), priority=self.v_pri.get(),
            status="Open", reported_date=self.v_date.get().strip())
        req_id = self.db.create_maintenance_request(req)
        messagebox.showinfo("Submitted ✓",
                            f"Request #{req_id} created.\nUnit: {apt.unit_number}  •  Priority: {req.priority}",
                            parent=self)
        if self.on_complete: self.on_complete()