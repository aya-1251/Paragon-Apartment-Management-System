"""
views_manager.py — Manager UI
Cross-city oversight: all cities' occupancy, performance reports, city expansion.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from views import (
    DARK_BG, PANEL_BG, CARD_BG, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    TEXT, TEXT_DIM, TEXT_MUTED, BORDER, HOVER_BG,
    FONT_HEAD, FONT_TITLE, FONT_SUB, FONT_BODY, FONT_SMALL,
    sc, badge, mkbtn, entry_var, combo_var, scrollable, sec_hdr, info_grid,
    ApartmentDetailWindow,
)


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

def stat_pill(parent, label, val, color):
    p = tk.Frame(parent, bg=CARD_BG, padx=16, pady=10)
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

class ManagerAppShell(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        self._build_sidebar()
        self.content = tk.Frame(self, bg=DARK_BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._go("overview")

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=PANEL_BG, width=220,
                         highlightbackground=BORDER, highlightthickness=1)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Label(sb, text="🏢  PropManage", font=("Segoe UI", 12, "bold"),
                 bg=PANEL_BG, fg=TEXT).pack(padx=20, pady=(22, 10), anchor="w")

        uc = tk.Frame(sb, bg=HOVER_BG, padx=14, pady=10)
        uc.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(uc, text=self.staff.full_name, font=FONT_SUB, bg=HOVER_BG, fg=TEXT).pack(anchor="w")
        badge(uc, self.staff.role, ACCENT2).pack(anchor="w", pady=(4, 0))
        tk.Label(uc, text="🌍  All Locations", font=FONT_SMALL, bg=HOVER_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        self._nbtn = {}
        for key, label, dest in [
            ("overview",  "📈  Portfolio Overview", "overview"),
            ("occupancy", "🏠  Occupancy",          "occupancy"),
            ("financial", "💰  Financial Reports",  "financial"),
            ("leases",    "📄  Lease Tracker",      "leases"),
            ("perf",      "📊  Performance",        "perf"),
            ("expand",    "🌆  Expand Business",    "expand"),
        ]:
            b = tk.Button(sb, text=label, font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, anchor="w", padx=18, pady=11,
                          cursor="hand2", activebackground=HOVER_BG, activeforeground=TEXT,
                          command=lambda d=dest, k=key: self._nav(k, d))
            b.pack(fill="x")
            self._nbtn[key] = b

        tk.Frame(sb, bg=PANEL_BG).pack(fill="both", expand=True)
        tk.Button(sb, text="⬅  Sign Out", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_MUTED,
                  relief="flat", bd=0, anchor="w", padx=18, pady=10,
                  cursor="hand2", command=self._logout).pack(fill="x")

    def _nav(self, key, dest):
        for k, b in self._nbtn.items(): b.config(bg=PANEL_BG, fg=TEXT_DIM)
        self._nbtn[key].config(bg=HOVER_BG, fg=TEXT)
        self._go(dest)

    def _clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def _go(self, dest):
        self._clear()
        if   dest == "overview":  OverviewView(self.content, self.staff, self.db)
        elif dest == "occupancy": OccupancyView(self.content, self.staff, self.db)
        elif dest == "financial": FinancialView(self.content, self.staff, self.db)
        elif dest == "leases":    AllLeasesView(self.content, self.staff, self.db)
        elif dest == "perf":      PerformanceView(self.content, self.staff, self.db)
        elif dest == "expand":    ExpandView(self.content, self.staff, self.db)

    def _logout(self):
        if messagebox.askyesno("Sign Out", "Sign out?"):
            self.destroy()
            self.master.show_login()


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
            color = SUCCESS if occ_pct >= 80 else WARNING if occ_pct >= 50 else DANGER

            card = tk.Frame(inner, bg=CARD_BG, padx=24, pady=18)
            card.pack(fill="x", pady=(0, 10))

            # City header
            hdr = tk.Frame(card, bg=CARD_BG)
            hdr.pack(fill="x")
            tk.Label(hdr, text=f"📍 {s['city']}", font=FONT_TITLE, bg=CARD_BG, fg=TEXT).pack(side="left")
            tk.Label(hdr, text=s["address"], font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=12)
            occ_badge = tk.Label(hdr, text=f"  {occ_pct:.0f}% occupied  ", font=FONT_SMALL,
                                 bg=color, fg=color)
            occ_badge.pack(side="right")

            # KPI row
            kpi = tk.Frame(card, bg=CARD_BG)
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
                tile = tk.Frame(kpi, bg=PANEL_BG, padx=14, pady=10)
                tile.pack(side="left", padx=(0, 6))
                tk.Label(tile, text=str(val), font=("Segoe UI", 14, "bold"), bg=PANEL_BG, fg=col).pack()
                tk.Label(tile, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack()

            # Occupancy bar
            progress_bar(card, occ_pct,
                         f"Occupancy: {s['occupied']}/{s['total_apts']} units ({occ_pct:.1f}%)",
                         color=color)

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
        sec_hdr(inner, "Occupancy by City")
        chart = tk.Canvas(inner, bg=PANEL_BG, height=220, highlightthickness=0)
        chart.pack(fill="x", padx=24, pady=(4, 16))

        def draw_chart(e):
            chart.delete("all")
            w = chart.winfo_width()
            n = len(occ)
            if n == 0: return
            bar_w = max(40, (w - 80) // n - 20)
            H = 180
            max_total = max(s["total"] for s in occ) or 1
            for i, s in enumerate(occ):
                x = 40 + i * (bar_w + 20)
                occ_h = int((s["occupied"] / max_total) * H)
                avail_h = int((s["available"] / max_total) * H)
                maint_h = int((s.get("maintenance", 0) / max_total) * H)

                # Stacked bars
                y_base = H + 10
                chart.create_rectangle(x, y_base - occ_h, x + bar_w, y_base,
                                       fill=ACCENT, outline="")
                chart.create_rectangle(x, y_base - occ_h - avail_h, x + bar_w,
                                       y_base - occ_h, fill=SUCCESS, outline="")
                if maint_h:
                    chart.create_rectangle(x, y_base - occ_h - avail_h - maint_h, x + bar_w,
                                           y_base - occ_h - avail_h, fill=WARNING, outline="")

                pct = s["occupied"] / s["total"] * 100 if s["total"] else 0
                chart.create_text(x + bar_w // 2, y_base - occ_h - avail_h - maint_h - 8,
                                  text=f"{pct:.0f}%", fill=TEXT, font=("Segoe UI", 9), anchor="s")
                chart.create_text(x + bar_w // 2, y_base + 8,
                                  text=s["city"], fill=TEXT_DIM, font=("Segoe UI", 9), anchor="n")

            # Legend
            legend_y = 8
            for label, col in [("Occupied", ACCENT), ("Available", SUCCESS), ("Maintenance", WARNING)]:
                chart.create_rectangle(w - 140, legend_y, w - 126, legend_y + 10, fill=col, outline="")
                chart.create_text(w - 122, legend_y + 1, text=label, fill=TEXT_DIM,
                                  font=("Segoe UI", 8), anchor="nw")
                legend_y += 16

        chart.bind("<Configure>", draw_chart)

        # Detail table
        sec_hdr(inner, "City Breakdown")
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
        sec_hdr(inner, "Apartment Status List")
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
                badge(ar, apt.status).pack(side="left", padx=6)
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
        sec_hdr(inner, "Portfolio Totals")
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
        sec_hdr(inner, "By City")
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
        sec_hdr(inner, "Monthly Revenue by City  (last 6 months)")
        all_months = set()
        city_rev = {}
        for loc in locs:
            rev = self.db.get_monthly_revenue(loc.id, months=6)
            city_rev[loc.city] = {r["month"]: r["collected"] for r in rev}
            all_months.update(r["month"] for r in rev)
        months = sorted(all_months)

        if months:
            # Header
            hdr_row = tk.Frame(inner, bg=PANEL_BG)
            hdr_row.pack(fill="x", padx=24, pady=(4, 0))
            tk.Label(hdr_row, text="City", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                     width=14, anchor="w").pack(side="left", padx=4, pady=6)
            for m in months:
                tk.Label(hdr_row, text=m[5:] if m else "—", font=FONT_SMALL, bg=PANEL_BG,
                         fg=TEXT_DIM, width=11, anchor="w").pack(side="left", padx=4)

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
        self.pack(fill="both", expand=True)
        page_header(self, "Lease Tracker", "All active lease agreements across every city.")
        self._build()

    def _build(self):
        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0, 8))
        tk.Label(fbar, text="Expiring within:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self._days_v = tk.StringVar(value="90")
        for label, val in [("30d","30"),("60d","60"),("90d","90"),("180d","180"),("All","3650")]:
            tk.Radiobutton(fbar, text=label, variable=self._days_v, value=val, font=FONT_SMALL,
                           bg=DARK_BG, fg=TEXT_DIM, selectcolor=DARK_BG, activebackground=DARK_BG,
                           relief="flat", bd=0, cursor="hand2",
                           command=self._load).pack(side="left", padx=6)

        self.sum_row = tk.Frame(self, bg=DARK_BG)
        self.sum_row.pack(fill="x", padx=28, pady=(0, 6))
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._load()

    def _load(self):
        for w in self.sum_row.winfo_children(): w.destroy()
        for w in self.table.winfo_children(): w.destroy()

        days = int(self._days_v.get())
        leases = self.db.get_expiring_leases(days)  # all cities

        expired  = [l for l in leases if getattr(l,"days_remaining",0) < 0]
        critical = [l for l in leases if 0 <= getattr(l,"days_remaining",0) <= 30]
        warning  = [l for l in leases if 30 < getattr(l,"days_remaining",0) <= 90]
        beyond   = [l for l in leases if getattr(l,"days_remaining",0) > 90]

        for label, lst, col in [("Expired",expired,DANGER),("< 30d",critical,WARNING),
                                  ("31–90d",warning,ACCENT),("90d+",beyond,SUCCESS)]:
            stat_pill(self.sum_row, label, len(lst), col)

        if not leases:
            tk.Label(self.table, text="No leases in this window.", font=FONT_BODY,
                     bg=DARK_BG, fg=TEXT_DIM).pack(pady=30)
            return

        COLS = [("City",12),("Unit",8),("Tenant",18),("End Date",11),
                ("Days Left",10),("Rent",9),("Status",10)]
        col_headers(self.table, COLS)

        for l in leases:
            days_left = getattr(l, "days_remaining", 0)
            days_col = (DANGER if days_left < 0 else
                        WARNING if days_left <= 30 else
                        ACCENT if days_left <= 90 else SUCCESS)
            days_str = f"{days_left}d" if days_left >= 0 else f"Exp {abs(days_left)}d"
            row = tk.Frame(self.table, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w, col in [
                (l.location_city, 12, TEXT),
                (l.apartment_unit, 8, TEXT),
                (l.tenant_name,   18, TEXT),
                (l.end_date,      11, TEXT),
                (days_str,        10, days_col),
                (f"£{l.monthly_rent:,.0f}", 9, TEXT),
                (l.status,        10, sc(l.status)),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
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
        for s in summary:
            occ_col = SUCCESS if s["occupancy_pct"] >= 80 else WARNING if s["occupancy_pct"] >= 50 else DANGER
            progress_bar(inner, s["occupancy_pct"],
                         f"{s['city']}: {s['occupied']}/{s['total_apts']} ({s['occupancy_pct']:.1f}%)",
                         color=occ_col, bg=CARD_BG)

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
        sec_hdr(inner, f"Current Locations  ({len(locs)})")
        loc_frame = tk.Frame(inner, bg=DARK_BG)
        loc_frame.pack(fill="x", padx=24, pady=(0, 16))
        for loc in locs:
            apts = self.db.get_all_apartments(loc.id)
            staff_count = len(self.db.get_staff_for_location(loc.id))
            card = tk.Frame(loc_frame, bg=CARD_BG, padx=20, pady=14)
            card.pack(fill="x", pady=(0, 8))
            top = tk.Frame(card, bg=CARD_BG)
            top.pack(fill="x")
            tk.Label(top, text=f"📍 {loc.city}", font=FONT_TITLE, bg=CARD_BG, fg=TEXT).pack(side="left")
            tk.Label(top, text=loc.address, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left", padx=12)
            tk.Label(top, text=f"{loc.postcode}  •  {loc.country}", font=FONT_SMALL,
                     bg=CARD_BG, fg=TEXT_MUTED).pack(side="right")
            tk.Label(card, text=f"{len(apts)} apartments  •  {staff_count} staff",
                     font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(6, 0))

        # Add new location form
        sec_hdr(inner, "Add New City Location")
        form = tk.Frame(inner, bg=CARD_BG, padx=32, pady=24)
        form.pack(fill="x", pady=(0, 16))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        tk.Label(form, text="Opening a new location will add it to the system immediately. "
                            "You can then assign apartments and staff from the Admin panel.",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM, wraplength=700, justify="left"
                 ).grid(row=0, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 16))

        self.v_city    = entry_var(form, "City Name *",      1, 0, width=22)
        self.v_address = entry_var(form, "Office Address *", 1, 1, width=24)
        self.v_post    = entry_var(form, "Postcode *",       1, 2, width=14)
        countries = ["UK", "Ireland", "France", "Germany", "Spain", "Netherlands"]
        self.v_country = combo_var(form, "Country", countries, 3, 0, default="UK", width=14)

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=4, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Open New Location ✓", self._submit, color=SUCCESS).pack(side="right")

    def _submit(self):
        city    = self.v_city.get().strip()
        address = self.v_address.get().strip()
        postcode= self.v_post.get().strip()
        country = self.v_country.get()
        if not city or not address or not postcode:
            messagebox.showwarning("Missing", "City, address and postcode are required.", parent=self)
            return
        if messagebox.askyesno("Confirm",
                               f"Add new location:\n\n{city}\n{address}\n{postcode}, {country}\n\nProceed?",
                               parent=self):
            loc_id = self.db.add_location(city, address, postcode, country)
            messagebox.showinfo("Location Added ✓",
                                f"📍 {city} has been added to the portfolio.\n"
                                f"Location ID: #{loc_id}\n\n"
                                f"You can now add apartments and assign staff from the Administrator panel.",
                                parent=self)
            # Refresh
            for w in self.winfo_children(): w.destroy()
            self._build()