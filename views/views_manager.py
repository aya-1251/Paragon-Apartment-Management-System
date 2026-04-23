"""
views_manager.py — Manager UI
Cross-city oversight: all cities' occupancy, performance reports, city expansion.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from .views import (
    DARK_BG, PANEL_BG, CARD_BG, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    TEXT, TEXT_DIM, TEXT_MUTED, BORDER, HOVER_BG,
    FONT_HEAD, FONT_TITLE, FONT_SUB, FONT_BODY, FONT_SMALL,
    sc, badge, mkbtn, entry_var, combo_var, scrollable, sec_hdr, info_grid,
    ApartmentDetailWindow, export_bar, BaseAppShell, DataExplorerView,
)


def col_headers(parent, cols, bg=HOVER_BG):
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", padx=24, pady=(4, 0))
    for label, w in cols:
        tk.Label(row, text=label, font=("Segoe UI", 9, "bold"), bg=bg, fg=TEXT,
                 width=w, anchor="w").pack(side="left", padx=4, pady=8)
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24)

def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24)

def page_header(parent, title, subtitle=""):
    hdr = tk.Frame(parent, bg=DARK_BG, padx=28, pady=20)
    hdr.pack(fill="x")
    tk.Label(hdr, text=title, font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
    if subtitle:
        tk.Label(hdr, text=subtitle, font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")

def stat_pill(parent, label, val, color):
    p = tk.Frame(parent, bg=CARD_BG, padx=16, pady=10,
                 highlightbackground=BORDER, highlightthickness=1)
    p.pack(side="left", padx=(0, 8))
    tk.Label(p, text=str(val), font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=color).pack()
    tk.Label(p, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

def progress_bar(parent, pct, label="", color=ACCENT, bg=CARD_BG):
    pct = max(0, min(100, pct))
    if label:
        tk.Label(parent, text=label, font=FONT_SMALL, bg=bg, fg=TEXT_DIM).pack(anchor="w")
    canvas = tk.Canvas(parent, bg=PANEL_BG, height=12, highlightthickness=0)
    canvas.pack(fill="x", pady=(2, 8))
    def draw(e, p=pct, c=color):
        w = canvas.winfo_width()
        canvas.delete("all")
        canvas.create_rectangle(0, 0, int(w * p / 100), 12, fill=c, outline="")
    canvas.bind("<Configure>", draw)


# ══════════════════════════════════════════════════════════════════
#  SHELL
# ══════════════════════════════════════════════════════════════════

class ManagerAppShell(BaseAppShell):
    def __init__(self, parent, staff, db):
        super().__init__(parent, staff, db)
        self._nav("overview", "overview")

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=PANEL_BG, width=220,
                         highlightbackground=BORDER, highlightthickness=1)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Label(sb, text="🏢  PAMS", font=("Segoe UI", 12, "bold"),
                 bg=PANEL_BG, fg=TEXT).pack(padx=20, pady=(22, 10), anchor="w")

        uc = tk.Frame(sb, bg=HOVER_BG, padx=14, pady=10)
        uc.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(uc, text=self.staff.full_name, font=FONT_SUB, bg=HOVER_BG, fg=TEXT).pack(anchor="w")
        badge(uc, self.staff.role, ACCENT2).pack(anchor="w", pady=(4, 0))
        tk.Label(uc, text="🌍  All Locations", font=FONT_SMALL, bg=HOVER_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        self._nbtn = {}
        self._nbar = {}
        for key, label, dest in [
            ("overview",  "📈  Portfolio Overview", "overview"),
            ("occupancy", "🏠  Occupancy",          "occupancy"),
            ("financial", "💰  Financial Reports",  "financial"),
            ("leases",    "📄  Lease Tracker",      "leases"),
            ("perf",      "📊  Performance",        "perf"),
            ("expand",    "🌆  Expand Business",    "expand"),
            ("staff",     "👥  Staff Accounts",     "staff"),
            ("explorer",  "🔍  Data Explorer",      "explorer"),
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
        if   dest == "overview":  OverviewView(self.content, self.staff, self.db)
        elif dest == "occupancy": OccupancyView(self.content, self.staff, self.db)
        elif dest == "financial": FinancialView(self.content, self.staff, self.db)
        elif dest == "leases":    AllLeasesView(self.content, self.staff, self.db)
        elif dest == "perf":      PerformanceView(self.content, self.staff, self.db)
        elif dest == "expand":    ExpandView(self.content, self.staff, self.db)
        elif dest == "staff":     ManagerStaffView(self.content, self.staff, self.db)
        elif dest == "explorer":  DataExplorerView(self.content, self.staff, self.db)


# ══════════════════════════════════════════════════════════════════
#  PORTFOLIO OVERVIEW — one card per city, all KPIs
# ══════════════════════════════════════════════════════════════════

class OverviewView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Portfolio Overview", "Live summary across all cities.")
        self._build()

    def _build(self):
        summary = self.db.get_cross_city_summary()

        # Top-level totals
        totals_row = tk.Frame(self, bg=DARK_BG)
        totals_row.pack(fill="x", padx=28, pady=(0, 16))
        total_apts  = sum(s["total_apts"] for s in summary)
        total_occ   = sum(s["occupied"] for s in summary)
        total_rev   = sum(s["collected"] for s in summary)
        total_over  = sum(s["overdue"] for s in summary)
        total_staff = sum(s["staff_count"] for s in summary)
        for label, val, col in [
            ("Cities",    len(summary),              ACCENT2),
            ("Total Units",total_apts,               TEXT),
            ("Occupied",  total_occ,                 ACCENT),
            ("Available", total_apts - total_occ,    SUCCESS),
            ("Revenue",   f"£{total_rev:,.0f}",      SUCCESS),
            ("Overdue",   f"£{total_over:,.0f}",     DANGER),
            ("Staff",     total_staff,               TEXT_DIM),
        ]:
            stat_pill(totals_row, label, val, col)

        # City cards — scrollable
        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        for s in summary:
            occ_pct = s["occupancy_pct"]
            badge_color = SUCCESS if occ_pct >= 80 else WARNING if occ_pct >= 50 else DANGER
            bar_color   = SUCCESS if occ_pct >= 80 else ACCENT  if occ_pct >= 50 else DANGER

            card = tk.Frame(inner, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=(0, 10))
            tk.Frame(card, bg=bar_color, height=4).pack(fill="x")
            body = tk.Frame(card, bg=CARD_BG, padx=24, pady=16)
            body.pack(fill="both", expand=True)

            # City header
            hdr = tk.Frame(body, bg=CARD_BG)
            hdr.pack(fill="x")
            tk.Label(hdr, text=f"📍 {s['city']}", font=FONT_TITLE, bg=CARD_BG, fg=TEXT).pack(side="left")
            tk.Label(hdr, text=s["address"], font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=12)
            occ_badge = badge(hdr, f"{occ_pct:.0f}% occupied", color=badge_color)
            occ_badge.pack(side="right")

            # KPI row
            kpi = tk.Frame(body, bg=CARD_BG)
            kpi.pack(fill="x", pady=(12, 8))
            for label, val, col in [
                ("Units",        s["total_apts"],            TEXT),
                ("Occupied",     s["occupied"],              ACCENT),
                ("Available",    s["available"],             SUCCESS),
                ("Collected",    f"£{s['collected']:,.0f}",  SUCCESS),
                ("Pending",      f"£{s['pending']:,.0f}",    WARNING),
                ("Overdue",      f"£{s['overdue']:,.0f}",    DANGER if s["overdue"] > 0 else TEXT_DIM),
                ("Open Jobs",    s["maint_open"],            WARNING if s["maint_open"] > 0 else TEXT_DIM),
                ("Maint Cost",   f"£{s['maint_cost']:,.0f}", WARNING),
                ("Staff",        s["staff_count"],           TEXT_DIM),
            ]:
                tile = tk.Frame(kpi, bg=PANEL_BG, padx=14, pady=10,
                                highlightbackground=BORDER, highlightthickness=1)
                tile.pack(side="left", padx=(0, 6))
                tk.Label(tile, text=str(val), font=("Segoe UI", 14, "bold"), bg=PANEL_BG, fg=col).pack()
                tk.Label(tile, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack()

            # Occupancy bar
            progress_bar(body, occ_pct,
                         f"Occupancy: {s['occupied']}/{s['total_apts']} units ({occ_pct:.1f}%)",
                         color=bar_color)

            # Drill-down button
            mkbtn(card, f"View {s['city']} Apartments →",
                  lambda lid=s["location_id"], city=s["city"]: self._open_city(lid, city),
                  small=True).pack(anchor="e")

    def _open_city(self, location_id, city):
        win = tk.Toplevel(self)
        win.title(f"Apartments — {city}")
        win.geometry("1100x700")
        win.configure(bg=DARK_BG)
        CityApartmentView(win, self.staff, self.db, location_id, city)


# ══════════════════════════════════════════════════════════════════
#  CITY APARTMENT VIEW (drill-down from overview)
# ══════════════════════════════════════════════════════════════════

class CityApartmentView(tk.Frame):
    def __init__(self, parent, staff, db, location_id, city):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.location_id = location_id
        self.city = city
        self.pack(fill="both", expand=True)
        page_header(self, f"📍 {city}", "All apartments — click to view full records.")
        apts = self.db.get_all_apartments(location_id)
        outer, grid = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28)
        COLS = 3
        for i, apt in enumerate(apts):
            r, c = divmod(i, COLS)
            self._apt_card(grid, apt, r, c)
        for c in range(COLS):
            grid.columnconfigure(c, weight=1, uniform="col")

    def _apt_card(self, parent, apt, row, col):
        color = sc(apt.status)
        outer = tk.Frame(parent, bg=CARD_BG, cursor="hand2",
                         highlightbackground=BORDER, highlightthickness=1)
        outer.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        tk.Frame(outer, bg=color, height=4).pack(fill="x")
        body = tk.Frame(outer, bg=CARD_BG, padx=16, pady=14)
        body.pack(fill="both", expand=True)
        head = tk.Frame(body, bg=CARD_BG)
        head.pack(fill="x")
        tk.Label(head, text=f"Unit {apt.unit_number}", font=FONT_SUB, bg=CARD_BG, fg=TEXT).pack(side="left")
        badge(head, apt.status).pack(side="right")
        tk.Label(body, text=f"{apt.apartment_type}  •  {apt.num_bedrooms}bd  •  Floor {apt.floor}",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        # Active lease info
        lease = self.db.get_active_lease_for_apartment(apt.id)
        if lease:
            tk.Label(body, text=f"👤 {lease.tenant_name}", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
            tk.Label(body, text=f"Ends: {lease.end_date}", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")

        tk.Label(body, text=f"£{apt.monthly_rent:,.0f}/mo",
                 font=("Segoe UI", 13, "bold"), bg=CARD_BG, fg=ACCENT).pack(anchor="w", pady=(8, 0))

        # Pass a fake staff object with correct location_id for ApartmentDetailWindow
        import types
        fake_staff = types.SimpleNamespace(
            id=self.staff.id, full_name=self.staff.full_name,
            role=self.staff.role, location_id=self.location_id)

        def click(e=None, a=apt, fs=fake_staff): ApartmentDetailWindow(self, a, fs, self.db)
        for w in [outer, body, head]:
            try: w.bind("<Button-1>", click)
            except Exception: pass
        outer.bind("<Enter>", lambda e: outer.config(highlightbackground=ACCENT, highlightthickness=2))
        outer.bind("<Leave>", lambda e: outer.config(highlightbackground=BORDER, highlightthickness=1))


# ══════════════════════════════════════════════════════════════════
#  OCCUPANCY VIEW — bar chart + table per city
# ══════════════════════════════════════════════════════════════════

class OccupancyView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Occupancy Levels", "Apartment occupancy across all locations.")
        self._build()

    def _build(self):
        occ = self.db.get_occupancy_by_city()
        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        # Bar chart
        sec_hdr(inner, "Occupancy by City", bg=DARK_BG)
        chart = tk.Canvas(inner, bg=PANEL_BG, height=320, highlightthickness=0)
        chart.pack(fill="x", padx=24, pady=(4, 16))

        def draw_chart(e):
            chart.delete("all")
            w = chart.winfo_width()
            n = len(occ)
            if n == 0: return
            bar_w = max(60, (w - 120) // n - 24)
            H = 240          # bar drawing height
            top_pad = 30     # space above bars for % labels
            bot_pad = 28     # space below bars for city labels
            y_base = top_pad + H
            max_total = max(s["total"] for s in occ) or 1
            for i, s in enumerate(occ):
                x = 60 + i * (bar_w + 24)
                occ_h   = int((s["occupied"]              / max_total) * H)
                avail_h = int((s["available"]             / max_total) * H)
                maint_h = int((s.get("maintenance", 0)   / max_total) * H)

                bar_top = y_base - occ_h - avail_h - maint_h

                # Stacked bars — occupied (bottom), available (middle), maintenance (top)
                chart.create_rectangle(x, y_base - occ_h, x + bar_w, y_base,
                                       fill=ACCENT, outline="")
                chart.create_rectangle(x, y_base - occ_h - avail_h, x + bar_w,
                                       y_base - occ_h, fill=SUCCESS, outline="")
                if maint_h:
                    chart.create_rectangle(x, bar_top, x + bar_w,
                                           y_base - occ_h - avail_h, fill=ACCENT2, outline="")

                # % label above bar with breathing room
                pct = s["occupied"] / s["total"] * 100 if s["total"] else 0
                chart.create_text(x + bar_w // 2, bar_top - 6,
                                  text=f"{pct:.0f}%", fill=TEXT,
                                  font=("Segoe UI", 10, "bold"), anchor="s")
                # City label below bar
                chart.create_text(x + bar_w // 2, y_base + 8,
                                  text=s["city"], fill=TEXT_DIM,
                                  font=("Segoe UI", 9), anchor="n")

            # Legend — centred below bars
            legend_items = [("Occupied", ACCENT), ("Available", SUCCESS), ("Maintenance", ACCENT2)]
            item_w = 100
            total_legend_w = len(legend_items) * item_w
            legend_x = max(60, (w - total_legend_w) // 2)
            legend_y = y_base + bot_pad - 4
            for label, col in legend_items:
                chart.create_rectangle(legend_x, legend_y, legend_x + 12, legend_y + 12,
                                       fill=col, outline="")
                chart.create_text(legend_x + 16, legend_y + 1, text=label, fill=TEXT_DIM,
                                  font=("Segoe UI", 9), anchor="nw")
                legend_x += item_w

        chart.bind("<Configure>", draw_chart)

        # Detail table
        sec_hdr(inner, "City Breakdown", bg=DARK_BG)
        COLS = [("City", 14), ("Total", 7), ("Occupied", 10), ("Available", 10),
                ("Maintenance", 12), ("Occ %", 8), ("Revenue", 12), ("Overdue", 10)]
        col_headers(inner, COLS)

        locs = {l.city: l.id for l in self.db.get_all_locations()}
        for s in occ:
            fin = self.db.get_financial_summary(locs.get(s["city"]))
            occ_pct = s["occupied"] / s["total"] * 100 if s["total"] else 0
            occ_col = SUCCESS if occ_pct >= 80 else WARNING if occ_pct >= 50 else DANGER
            row = tk.Frame(inner, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w, col in [
                (s["city"],           14, TEXT),
                (str(s["total"]),      7, TEXT),
                (str(s["occupied"]),  10, ACCENT),
                (str(s["available"]), 10, SUCCESS),
                (str(s.get("maintenance",0)), 12, WARNING),
                (f"{occ_pct:.1f}%",    8, occ_col),
                (f"£{fin['total_collected']:,.0f}", 12, SUCCESS),
                (f"£{fin['overdue']:,.0f}", 10, DANGER if fin["overdue"]>0 else TEXT_DIM),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
            divider(inner)

        # Per-city apartment list
        sec_hdr(inner, "Apartment Status List", bg=DARK_BG)
        for s in occ:
            loc_id = locs.get(s["city"])
            apts = self.db.get_all_apartments(loc_id) if loc_id else []
            tk.Label(inner, text=f"  {s['city']}  ({len(apts)} units)",
                     font=FONT_SUB, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w", padx=24, pady=(12, 4))
            for apt in apts:
                lease = self.db.get_active_lease_for_apartment(apt.id)
                ar = tk.Frame(inner, bg=CARD_BG, padx=14, pady=7)
                ar.pack(fill="x", padx=24, pady=1)
                tk.Label(ar, text=f"Unit {apt.unit_number}", font=FONT_SUB, bg=CARD_BG,
                         fg=TEXT, width=10, anchor="w").pack(side="left")
                badge_f = tk.Frame(ar, bg=CARD_BG, width=120)
                badge_f.pack(side="left", padx=6)
                badge_f.pack_propagate(False)
                badge(badge_f, apt.status).pack(anchor="w", pady=3)
                tk.Label(ar, text=apt.apartment_type, font=FONT_SMALL, bg=CARD_BG,
                         fg=TEXT_DIM, width=12, anchor="w").pack(side="left")
                tk.Label(ar, text=f"£{apt.monthly_rent:,.0f}/mo", font=FONT_SMALL, bg=CARD_BG,
                         fg=ACCENT, width=10, anchor="w").pack(side="left")
                if lease:
                    tk.Label(ar, text=f"👤 {lease.tenant_name}  •  ends {lease.end_date}",
                             font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
                divider(inner)


# ══════════════════════════════════════════════════════════════════
#  FINANCIAL VIEW — cross-city financial report
# ══════════════════════════════════════════════════════════════════

class FinancialView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Financial Reports", "Revenue, collections and outstanding balances by city.")
        self._build()

    def _build(self):
        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        # Portfolio totals
        all_fin = self.db.get_financial_summary()
        sec_hdr(inner, "Portfolio Totals", bg=DARK_BG)
        kpi = tk.Frame(inner, bg=CARD_BG)
        kpi.pack(fill="x", padx=24, pady=(0, 16))
        for label, val, col in [
            ("Total Billed",  f"£{all_fin['total_billed']:,.0f}",      TEXT),
            ("Collected",     f"£{all_fin['total_collected']:,.0f}",    SUCCESS),
            ("Pending",       f"£{all_fin['pending']:,.0f}",            WARNING),
            ("Overdue",       f"£{all_fin['overdue']:,.0f}",            DANGER),
            ("Maint Spend",   f"£{all_fin['maintenance_cost']:,.0f}",   WARNING),
            ("Net Revenue",   f"£{all_fin['total_collected']-all_fin['maintenance_cost']:,.0f}", ACCENT),
        ]:
            t = tk.Frame(kpi, bg=PANEL_BG, padx=18, pady=14)
            t.pack(side="left", padx=(0, 8))
            tk.Label(t, text=val, font=("Segoe UI", 16, "bold"), bg=PANEL_BG, fg=col).pack()
            tk.Label(t, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack()

        progress_bar(inner,
                     (all_fin["total_collected"]/all_fin["total_billed"]*100) if all_fin["total_billed"] else 0,
                     f"Collection rate: {all_fin['total_collected']:,.0f} / {all_fin['total_billed']:,.0f}",
                     color=SUCCESS, bg=DARK_BG)

        # Per-city breakdown
        sec_hdr(inner, "By City", bg=DARK_BG)
        COLS = [("City",14),("Billed",12),("Collected",12),("Pending",12),
                ("Overdue",10),("Maint",10),("Rate",8)]
        col_headers(inner, COLS)

        locs = self.db.get_all_locations()
        for loc in locs:
            fin = self.db.get_financial_summary(loc.id)
            rate = (fin["total_collected"]/fin["total_billed"]*100) if fin["total_billed"] else 0
            row = tk.Frame(inner, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w, col in [
                (loc.city, 14, TEXT),
                (f"£{fin['total_billed']:,.0f}",     12, TEXT),
                (f"£{fin['total_collected']:,.0f}",  12, SUCCESS),
                (f"£{fin['pending']:,.0f}",           12, WARNING),
                (f"£{fin['overdue']:,.0f}",           10, DANGER if fin["overdue"]>0 else TEXT_DIM),
                (f"£{fin['maintenance_cost']:,.0f}",  10, WARNING),
                (f"{rate:.1f}%",                       8, SUCCESS if rate >= 90 else WARNING),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
            divider(inner)

        # Monthly revenue per city
        sec_hdr(inner, "Monthly Revenue by City  (last 6 months)", bg=DARK_BG)
        all_months = set()
        city_rev = {}
        for loc in locs:
            rev = self.db.get_monthly_revenue(loc.id, months=6)
            city_rev[loc.city] = {r["month"]: r["collected"] for r in rev}
            all_months.update(r["month"] for r in rev)
        months = sorted(all_months)

        if months:
            # Header
            hdr_row = tk.Frame(inner, bg=HOVER_BG)
            hdr_row.pack(fill="x", padx=24, pady=(4, 0))
            tk.Label(hdr_row, text="City", font=("Segoe UI", 9, "bold"), bg=HOVER_BG, fg=TEXT,
                     width=14, anchor="w").pack(side="left", padx=4, pady=8)
            for m in months:
                tk.Label(hdr_row, text=m[5:] if m else "—", font=("Segoe UI", 9, "bold"),
                         bg=HOVER_BG, fg=TEXT, width=11, anchor="w").pack(side="left", padx=4)
            tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=24)

            for loc in locs:
                row = tk.Frame(inner, bg=CARD_BG)
                row.pack(fill="x", padx=24)
                tk.Label(row, text=loc.city, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         width=14, anchor="w").pack(side="left", padx=4, pady=5)
                for m in months:
                    val = city_rev[loc.city].get(m, 0)
                    col = SUCCESS if val > 0 else TEXT_MUTED
                    tk.Label(row, text=f"£{val:,.0f}" if val else "—", font=FONT_BODY,
                             bg=CARD_BG, fg=col, width=11, anchor="w").pack(side="left", padx=4)
                divider(inner)


# ══════════════════════════════════════════════════════════════════
#  ALL LEASES VIEW — cross-city lease tracker
# ══════════════════════════════════════════════════════════════════

class AllLeasesView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._leases = []
        self.pack(fill="both", expand=True)
        page_header(self, "Lease Tracker",
                    "Upcoming and expired lease agreements across every city.")
        self._build()

    def _get_export_leases(self):
        cols = ["City", "Unit", "Tenant", "End Date",
                "Days Left", "Rent (£)", "Status"]
        rows = [(l.location_city, l.apartment_unit, l.tenant_name,
                 l.end_date, getattr(l, "days_remaining", ""),
                 f"{l.monthly_rent:.2f}", l.status)
                for l in self._leases]
        return cols, rows

    def _build(self):
        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0, 8))
        tk.Label(fbar, text="Show:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left", padx=(0,4))
        self._win_v = tk.StringVar(value="30")
        self._day_btns = {}
        def _set_win(v):
            self._win_v.set(v)
            for k, b in self._day_btns.items():
                b.config(bg=ACCENT if k==v else PANEL_BG, fg="white" if k==v else TEXT_DIM)
            self._load()
        for label, val in [("Expired","expired"),("30d","30"),("60d","60"),
                           ("90d","90"),("180d","180"),("All","all")]:
            b = tk.Button(fbar, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                          command=lambda v=val: _set_win(v))
            b.pack(side="left", padx=2)
            self._day_btns[val] = b
        self._day_btns["30"].config(bg=ACCENT, fg="white")
        export_bar(fbar, "All Leases", self._get_export_leases).pack(side="right")

        self.sum_row = tk.Frame(self, bg=DARK_BG)
        self.sum_row.pack(fill="x", padx=28, pady=(0, 6))
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._load()

    def _load(self):
        for w in self.sum_row.winfo_children(): w.destroy()
        for w in self.table.winfo_children(): w.destroy()

        all_leases = self.db.get_expiring_leases(3650)

        expired  = [l for l in all_leases if getattr(l,"days_remaining",0) < 0]
        critical = [l for l in all_leases if 0 <= getattr(l,"days_remaining",0) <= 30]
        warning  = [l for l in all_leases if 30 < getattr(l,"days_remaining",0) <= 90]
        beyond   = [l for l in all_leases if getattr(l,"days_remaining",0) > 90]

        for label, lst, col in [("Expired",expired,DANGER),("< 30d",critical,WARNING),
                                  ("31–90d",warning,ACCENT),("90d+",beyond,SUCCESS)]:
            stat_pill(self.sum_row, label, len(lst), col)

        win = self._win_v.get()
        if win == "expired":
            leases = expired
        elif win == "all":
            leases = all_leases
        else:
            n = int(win)
            leases = [l for l in all_leases if 0 <= getattr(l,"days_remaining",0) <= n]
        self._leases = leases

        if not leases:
            tk.Label(self.table, text="No leases in this window.", font=FONT_BODY,
                     bg=DARK_BG, fg=TEXT_DIM).pack(pady=30)
            return

        COLS = [("City",12),("Unit",8),("Tenant",20),("End Date",12),
                ("Days Left",11),("Rent",10),("Status",10)]
        col_headers(self.table, COLS)

        for i, l in enumerate(leases):
            days_left = getattr(l, "days_remaining", 0)
            days_col = (DANGER if days_left < 0 else
                        WARNING if days_left <= 30 else
                        ACCENT if days_left <= 90 else SUCCESS)
            days_str = f"{days_left}d" if days_left >= 0 else f"Exp {abs(days_left)}d"
            status_label = "Expired" if days_left < 0 else l.status
            status_col = DANGER if days_left < 0 else sc(l.status)
            row_bg = CARD_BG if i % 2 == 0 else HOVER_BG
            row = tk.Frame(self.table, bg=row_bg)
            row.pack(fill="x", padx=24)
            for val, w, col in [
                (l.location_city, 12, TEXT),
                (l.apartment_unit, 8, TEXT),
                (l.tenant_name,   20, TEXT),
                (l.end_date,      12, TEXT),
                (days_str,        11, days_col),
                (f"£{l.monthly_rent:,.0f}", 10, TEXT),
                (status_label,    10, status_col),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=row_bg, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=7)
            divider(self.table)


# ══════════════════════════════════════════════════════════════════
#  PERFORMANCE VIEW — comparative report by city
# ══════════════════════════════════════════════════════════════════

class PerformanceView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Performance Reports",
                    "Comparative performance metrics across all cities.")
        self._nb_style()
        nb = ttk.Notebook(self, style="P.TNotebook")
        nb.pack(fill="both", expand=True)
        self._tab_comparison(nb)
        self._tab_maintenance(nb)
        self._tab_staff(nb)

    def _nb_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("P.TNotebook", background=DARK_BG, borderwidth=0, tabmargins=0)
        s.configure("P.TNotebook.Tab", background=PANEL_BG, foreground=TEXT_DIM,
                    font=FONT_BODY, padding=[16, 8])
        s.map("P.TNotebook.Tab", background=[("selected", CARD_BG)], foreground=[("selected", TEXT)])

    def _tab(self, nb, title):
        f = tk.Frame(nb, bg=CARD_BG)
        nb.add(f, text=f"  {title}  ")
        return f

    def _tab_comparison(self, nb):
        frame = self._tab(nb, "City Comparison")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        summary = self.db.get_cross_city_summary()
        sec_hdr(inner, "Key Performance Indicators")

        COLS = [("City",14),("Units",6),("Occ%",7),("Revenue",12),("Overdue",10),
                ("Maint Cost",11),("Open Jobs",10),("Staff",6),("Net",12)]
        col_headers(inner, COLS)

        for s in summary:
            net = s["collected"] - s["maint_cost"]
            occ_col = SUCCESS if s["occupancy_pct"] >= 80 else WARNING if s["occupancy_pct"] >= 50 else DANGER
            row = tk.Frame(inner, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w, col in [
                (s["city"],                              14, TEXT),
                (str(s["total_apts"]),                    6, TEXT),
                (f"{s['occupancy_pct']:.1f}%",            7, occ_col),
                (f"£{s['collected']:,.0f}",              12, SUCCESS),
                (f"£{s['overdue']:,.0f}",                10, DANGER if s["overdue"]>0 else TEXT_DIM),
                (f"£{s['maint_cost']:,.0f}",             11, WARNING),
                (str(s["maint_open"]),                   10, WARNING if s["maint_open"]>0 else TEXT_DIM),
                (str(s["staff_count"]),                   6, TEXT_DIM),
                (f"£{net:,.0f}",                         12, SUCCESS if net >= 0 else DANGER),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
            divider(inner)

        # Occupancy bars per city
        sec_hdr(inner, "Occupancy Rate")
        bars_frame = tk.Frame(inner, bg=CARD_BG, padx=24, pady=12)
        bars_frame.pack(fill="x", padx=24, pady=(0, 8))
        for s in summary:
            occ_col = SUCCESS if s["occupancy_pct"] >= 80 else ACCENT if s["occupancy_pct"] >= 50 else DANGER
            card = tk.Frame(bars_frame, bg=PANEL_BG, padx=16, pady=10,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=(0, 8))
            progress_bar(card, s["occupancy_pct"],
                         f"{s['city']}: {s['occupied']}/{s['total_apts']} ({s['occupancy_pct']:.1f}%)",
                         color=occ_col, bg=PANEL_BG)

    def _tab_maintenance(self, nb):
        frame = self._tab(nb, "Maintenance")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        sec_hdr(inner, "Maintenance Cost by City")
        COLS = [("City",14),("Category",14),("Jobs",6),("Total Cost",12),("Avg Cost",12),("Hours",8)]
        col_headers(inner, COLS)

        locs = self.db.get_all_locations()
        for loc in locs:
            mc = self.db.get_maintenance_cost_report(loc.id)
            if not mc: continue
            tk.Label(inner, text=f"  📍 {loc.city}", font=FONT_SUB, bg=CARD_BG, fg=TEXT_DIM
                     ).pack(anchor="w", padx=24, pady=(10, 4))
            for d in mc:
                row = tk.Frame(inner, bg=CARD_BG)
                row.pack(fill="x", padx=24)
                for val, w in [("", 14), (d["category"] or "—", 14), (str(d["count"]), 6),
                               (f"£{d['total_cost']:,.2f}", 12), (f"£{d['avg_cost']:,.2f}", 12),
                               (f"{d['total_hours']:.1f}h", 8)]:
                    tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                             width=w, anchor="w").pack(side="left", padx=4, pady=4)
                divider(inner)

    def _tab_staff(self, nb):
        frame = self._tab(nb, "Staff Directory")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        sec_hdr(inner, "All Staff")
        all_staff = self.db.get_all_staff()
        COLS = [("City",12),("Name",18),("Role",18),("Username",14),("Email",22),("Active",7)]
        col_headers(inner, COLS)

        locs = {l.id: l.city for l in self.db.get_all_locations()}
        for s in all_staff:
            row = tk.Frame(inner, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            active_col = SUCCESS if s.is_active else DANGER
            for val, w, col in [
                (getattr(s,"city","?"), 12, TEXT_DIM),
                (s.full_name,          18, TEXT),
                (s.role,               18, TEXT),
                (s.username,           14, TEXT_DIM),
                (s.email or "—",       22, TEXT_DIM),
                ("✓" if s.is_active else "✗", 7, active_col),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            divider(inner)


# ══════════════════════════════════════════════════════════════════
#  EXPAND VIEW — add new city / location
# ══════════════════════════════════════════════════════════════════

class ExpandView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Expand Business",
                    "Open a new city location to grow the portfolio.")
        self._build()

    def _build(self):
        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28)

        # Current locations
        locs = self.db.get_all_locations()
        sec_hdr(inner, f"Current Locations  ({len(locs)})", bg=DARK_BG)
        loc_frame = tk.Frame(inner, bg=DARK_BG)
        loc_frame.pack(fill="x", padx=24, pady=(0, 16))
        for loc in locs:
            apts = self.db.get_all_apartments(loc.id)
            staff_count = len(self.db.get_staff_for_location(loc.id))
            card = tk.Frame(loc_frame, bg=CARD_BG,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=(0, 8))
            tk.Frame(card, bg=ACCENT, height=4).pack(fill="x")
            body = tk.Frame(card, bg=CARD_BG, padx=20, pady=12)
            body.pack(fill="both", expand=True)
            top = tk.Frame(body, bg=CARD_BG)
            top.pack(fill="x")
            tk.Label(top, text=f"📍 {loc.city}", font=FONT_TITLE, bg=CARD_BG, fg=TEXT).pack(side="left")
            tk.Label(top, text=loc.address, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=12)
            tk.Label(top, text=f"{loc.postcode}  •  {loc.country}", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT_MUTED).pack(side="right")
            tk.Label(body, text=f"{len(apts)} apartments  •  {staff_count} staff",
                     font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(6, 0))

        # Add new location form
        sec_hdr(inner, "Add New City Location", bg=DARK_BG)
        form = tk.Frame(inner, bg=CARD_BG, padx=32, pady=24)
        form.pack(fill="x", pady=(0, 16))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        tk.Label(form, text="Opening a new location will add it to the system immediately. "
                            "You can then assign apartments and staff from the Admin panel.",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM, wraplength=700, justify="left"
                 ).grid(row=0, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 16))

        self.v_city    = entry_var(form, "City Name *",      1, 0, width=22,
                                   placeholder="e.g. Birmingham")
        self.v_address = entry_var(form, "Office Address *", 1, 1, width=24,
                                   placeholder="e.g. 12 High Street")
        self.v_post    = entry_var(form, "Postcode *",       1, 2, width=14,
                                   placeholder="e.g. B1 1AA")

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=3, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Open New Location ✓", self._submit, color=SUCCESS).pack(side="right")

    def _submit(self):
        city    = self.v_city.get().strip()
        address = self.v_address.get().strip()
        postcode= self.v_post.get().strip()
        if not city or not address or not postcode:
            messagebox.showwarning("Missing", "City, address and postcode are required.", parent=self)
            return
        if messagebox.askyesno("Confirm",
                               f"Add new location:\n\n{city}\n{address}\n{postcode}, UK\n\nProceed?",
                               parent=self):
            loc_id = self.db.add_location(city, address, postcode, "UK")
            messagebox.showinfo("Location Added ✓",
                                f"📍 {city} has been added to the portfolio.\n"
                                f"Location ID: #{loc_id}\n\n"
                                f"You can now add apartments and assign staff from the Administrator panel.",
                                parent=self)
            # Refresh
            for w in self.winfo_children(): w.destroy()
            self._build()


# ══════════════════════════════════════════════════════════════════
#  MANAGER STAFF VIEW — read-only view of all staff across all cities
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
#  MANAGER STAFF VIEW — full edit/reset/deactivate across all cities
# ══════════════════════════════════════════════════════════════════

class _StaffEditDialog(tk.Toplevel):
    """Modal dialog to edit a staff member's name, email, phone and role.

    caller_role: the role of the logged-in staff performing the action.
    Administrators are not permitted to edit Manager accounts.
    """
    def __init__(self, parent, staff_member, db, on_save=None, caller_role=""):
        super().__init__(parent)
        # ── Access guard ──────────────────────────────────────────────
        if caller_role == "Administrator" and staff_member.role == "Manager":
            self.destroy()
            messagebox.showerror(
                "Access Denied",
                "Administrators cannot edit Manager accounts.\n"
                "Please contact the Manager directly.",
                parent=parent,
            )
            return
        # ─────────────────────────────────────────────────────────────
        self.sm = staff_member
        self.db = db
        self.on_save = on_save
        self.title(f"Edit Staff — {staff_member.full_name}")
        self.geometry("480x420")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=ACCENT2, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✏  Edit Staff Account", font=FONT_TITLE,
                 bg=ACCENT2, fg="white").pack(anchor="w")
        tk.Label(hdr, text=f"@{self.sm.username}  •  {self.sm.role}",
                 font=FONT_SMALL, bg=ACCENT2, fg="#EDE9FE").pack(anchor="w")

        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        fn = getattr(self.sm, "first_name", "") or self.sm.full_name.split()[0]
        ln = getattr(self.sm, "last_name",  "") or (self.sm.full_name.split()[1] if " " in self.sm.full_name else "")
        self.v_fn   = entry_var(form, "First Name *", 0, 0, default=fn)
        self.v_ln   = entry_var(form, "Last Name *",  0, 1, default=ln)
        self.v_em   = entry_var(form, "Email",        2, 0, default=self.sm.email or "", colspan=2, width=40)
        self.v_ph   = entry_var(form, "Phone",        4, 0, default=getattr(self.sm, "phone", "") or "")

        ROLES = ["Front Desk", "Finance Manager", "Administrator", "Maintenance"]
        self.v_role = combo_var(form, "Role *", ROLES, 4, 1,
                                default=self.sm.role if self.sm.role in ROLES else ROLES[0])

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=6, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Save Changes ✓", self._save, color=ACCENT2).pack(side="right")

    def _save(self):
        fn = self.v_fn.get().strip()
        ln = self.v_ln.get().strip()
        if not fn or not ln:
            messagebox.showwarning("Missing", "First and last name are required.", parent=self)
            return
        self.db.update_staff(
            self.sm.id, fn, ln,
            self.v_role.get(),
            self.v_em.get().strip(),
            getattr(self, "v_ph", None) and self.v_ph.get().strip() or "",
        )
        messagebox.showinfo("Saved ✓", f"{fn} {ln}'s account has been updated.", parent=self)
        if self.on_save:
            self.on_save()
        self.destroy()


class _StaffResetDialog(tk.Toplevel):
    """Modal dialog to reset a staff member's password.

    caller_role: the role of the logged-in staff performing the action.
    Administrators are not permitted to reset Manager passwords.
    """
    def __init__(self, parent, staff_member, db, on_save=None, caller_role=""):
        super().__init__(parent)
        # ── Access guard ──────────────────────────────────────────────
        if caller_role == "Administrator" and staff_member.role == "Manager":
            self.destroy()
            messagebox.showerror(
                "Access Denied",
                "Administrators cannot reset a Manager's password.\n"
                "Please contact the Manager directly.",
                parent=parent,
            )
            return
        # ─────────────────────────────────────────────────────────────
        self.sm = staff_member
        self.db = db
        self.on_save = on_save
        self.title(f"Reset Password — {staff_member.full_name}")
        self.geometry("420x260")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=WARNING, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔑  Reset Password", font=FONT_TITLE,
                 bg=WARNING, fg="white").pack(anchor="w")
        tk.Label(hdr, text=f"{self.sm.full_name}  •  @{self.sm.username}",
                 font=FONT_SMALL, bg=WARNING, fg="#FEF3C7").pack(anchor="w")

        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="New Password *", font=FONT_SMALL,
                 bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
        self._pw = tk.Entry(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                            show="●", insertbackground=TEXT, relief="flat", bd=0,
                            highlightthickness=1, highlightcolor=ACCENT,
                            highlightbackground=BORDER)
        self._pw.pack(fill="x", pady=(4, 12), ipady=5)

        tk.Label(form, text="Confirm Password *", font=FONT_SMALL,
                 bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
        self._pw2 = tk.Entry(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                             show="●", insertbackground=TEXT, relief="flat", bd=0,
                             highlightthickness=1, highlightcolor=ACCENT,
                             highlightbackground=BORDER)
        self._pw2.pack(fill="x", pady=(4, 16), ipady=5)

        nav = tk.Frame(form, bg=CARD_BG)
        nav.pack(fill="x")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Reset Password ✓", self._reset, color=WARNING).pack(side="right")

    def _reset(self):
        pw  = self._pw.get()
        pw2 = self._pw2.get()
        if len(pw) < 6:
            messagebox.showwarning("Too Short", "Password must be at least 6 characters.", parent=self)
            return
        if pw != pw2:
            messagebox.showwarning("Mismatch", "Passwords do not match.", parent=self)
            return
        self.db.reset_staff_password(self.sm.id, pw)
        messagebox.showinfo("Done ✓", f"Password reset for {self.sm.full_name}.", parent=self)
        if self.on_save:
            self.on_save()
        self.destroy()


class ManagerStaffView(tk.Frame):
    """Full staff management for Manager — edit / reset password / deactivate
    across ALL cities."""

    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._staff_list = []
        self._shown = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _get_export_data(self):
        cols = ["ID", "Name", "Username", "Role", "City", "Email", "Phone", "Active"]
        rows = [(s.id, s.full_name, s.username, s.role, getattr(s, "city", ""),
                 s.email or "", getattr(s, "phone", "") or "", "Yes" if s.is_active else "No")
                for s in self._shown]
        return cols, rows

    def _build(self):
        hdr = tk.Frame(self, bg=DARK_BG, padx=28, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Staff Accounts", font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text="Manage all staff across every location — edit, reset passwords and deactivate accounts.",
                 font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")

        bar = tk.Frame(self, bg=DARK_BG)
        bar.pack(fill="x", padx=28, pady=(0, 8))

        # Search
        self._q = tk.StringVar()
        self._q.trace_add("write", lambda *_: self._filter())
        srch = tk.Entry(bar, textvariable=self._q, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                        insertbackground=TEXT, relief="flat", bd=0, width=32,
                        highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        srch.pack(side="left", ipady=5, padx=(0, 12))
        _ph = "Search name, username, role…"
        srch.insert(0, _ph); srch.config(fg=TEXT_MUTED)
        srch.bind("<FocusIn>",  lambda e: (srch.delete(0,"end"), srch.config(fg=TEXT)) if srch.get()==_ph else None)
        srch.bind("<FocusOut>", lambda e: (srch.insert(0,_ph), srch.config(fg=TEXT_MUTED)) if not srch.get() else None)

        export_bar(bar, "All_Staff", self._get_export_data).pack(side="right")

        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)

    def _load(self):
        self._staff_list = self.db.get_all_staff()
        self._shown = list(self._staff_list)
        self._render()

    def _filter(self):
        q = self._q.get().strip().lower()
        placeholder = "search name, username, role…"
        if not q or q == placeholder:
            self._shown = list(self._staff_list)
        else:
            self._shown = [s for s in self._staff_list
                           if q in s.full_name.lower() or q in s.username.lower()
                           or q in s.role.lower() or q in (getattr(s, "city", "") or "").lower()]
        self._render()

    def _render(self):
        for w in self.table.winfo_children():
            w.destroy()

        # Summary pills by role
        pills = tk.Frame(self.table, bg=DARK_BG)
        pills.pack(fill="x", padx=24, pady=(8, 12))
        from collections import Counter
        counts = Counter(s.role for s in self._staff_list)
        for role, count in sorted(counts.items()):
            p = tk.Frame(pills, bg=CARD_BG, padx=12, pady=6)
            p.pack(side="left", padx=(0, 6))
            tk.Label(p, text=str(count), font=("Segoe UI", 13, "bold"),
                     bg=CARD_BG, fg=ACCENT2).pack()
            tk.Label(p, text=role, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

        COLS = [("ID", 4), ("Name", 16), ("Username", 12), ("Role", 16),
                ("City", 12), ("Email", 20), ("Active", 6), ("Actions", 28)]
        _mgr_col_headers(self.table, COLS)

        current_city = None
        for s in self._shown:
            city = getattr(s, "city", "") or "—"
            if city != current_city:
                current_city = city
                sec = tk.Frame(self.table, bg=DARK_BG)
                sec.pack(fill="x", padx=24, pady=(10, 2))
                tk.Label(sec, text=f"📍  {city}", font=FONT_SUB,
                         bg=DARK_BG, fg=TEXT).pack(side="left")

            row_bg = CARD_BG
            row = tk.Frame(self.table, bg=row_bg)
            row.pack(fill="x", padx=24)

            active_col = SUCCESS if s.is_active else DANGER
            active_txt = "✓" if s.is_active else "✗"
            for val, w in [(str(s.id), 4), (s.full_name, 16), (s.username, 12),
                           (s.role, 16), (city, 12), (s.email or "—", 20)]:
                tk.Label(row, text=val, font=FONT_BODY, bg=row_bg, fg=TEXT,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
            tk.Label(row, text=active_txt, font=FONT_BODY, bg=row_bg,
                     fg=active_col, width=6, anchor="w").pack(side="left", padx=4)

            # Action buttons
            act = tk.Frame(row, bg=row_bg)
            act.pack(side="left", padx=4)

            caller_role = self.staff.role
            mkbtn(act, "Edit",
                  lambda sm=s: _StaffEditDialog(
                      self, sm, self.db, on_save=self._load, caller_role=caller_role),
                  color=ACCENT2, small=True).pack(side="left", padx=(0, 4))
            mkbtn(act, "Reset PW",
                  lambda sm=s: _StaffResetDialog(
                      self, sm, self.db, on_save=self._load, caller_role=caller_role),
                  color=WARNING, small=True).pack(side="left", padx=(0, 4))

            toggle_label = "Deactivate" if s.is_active else "Activate"
            toggle_color  = DANGER if s.is_active else SUCCESS
            mkbtn(act, toggle_label,
                  lambda sm=s: self._toggle(sm),
                  color=toggle_color, small=True).pack(side="left")

            tk.Frame(self.table, bg=BORDER, height=1).pack(fill="x", padx=24)

    def _toggle(self, staff_member):
        action = "deactivate" if staff_member.is_active else "activate"
        if messagebox.askyesno("Confirm",
                               f"Are you sure you want to {action} {staff_member.full_name}?",
                               parent=self):
            self.db.toggle_staff_active(staff_member.id)
            self._load()


def _mgr_col_headers(parent, cols, bg=HOVER_BG):
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", padx=24, pady=(4, 0))
    for label, w in cols:
        tk.Label(row, text=label, font=("Segoe UI", 9, "bold"), bg=bg, fg=TEXT,
                 width=w, anchor="w").pack(side="left", padx=4, pady=8)
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24)