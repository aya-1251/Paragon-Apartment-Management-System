"""
views_admin.py — Administrator UI
Location-scoped: staff management, apartment management, lease tracking, reports, commune view.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable

from .views import (
    DARK_BG, PANEL_BG, CARD_BG, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    TEXT, TEXT_DIM, TEXT_MUTED, BORDER, HOVER_BG,
    FONT_HEAD, FONT_TITLE, FONT_SUB, FONT_BODY, FONT_SMALL,
    sc, badge, mkbtn, entry_var, combo_var, scrollable, sec_hdr, info_grid,
    ApartmentDetailWindow, export_bar, BaseAppShell, DataExplorerView,
)
from models import Apartment, Staff

ROLES = ["Front Desk", "Finance Manager", "Maintenance Staff", "Administrator"]


# ── shared helpers ────────────────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════
#  SHELL
# ══════════════════════════════════════════════════════════════════

class AdminAppShell(BaseAppShell):
    def __init__(self, parent, staff, db):
        super().__init__(parent, staff, db)
        self._nav("commune", "commune")

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
        badge(uc, self.staff.role, ACCENT).pack(anchor="w", pady=(4, 0))
        locs = {l.id: l.city for l in self.db.get_all_locations()}
        tk.Label(uc, text=f"📍 {locs.get(self.staff.location_id,'?')}",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        self._nbtn = {}
        self._nbar = {}
        for key, label, dest in [
            ("commune",    "🏠  Apartments",       "commune"),
            ("staff",      "👥  Staff Accounts",   "staff"),
            ("apartments", "🏗  Manage Apartments","apartments"),
            ("leases",     "📄  Lease Tracker",    "leases"),
            ("reports",    "📊  Reports",          "reports"),
            ("explorer",   "🔍  Data Explorer",   "explorer"),
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
        if   dest == "commune":    AdminCommuneView(self.content, self.staff, self.db)
        elif dest == "staff":      StaffView(self.content, self.staff, self.db)
        elif dest == "apartments": ApartmentsManageView(self.content, self.staff, self.db)
        elif dest == "leases":     LeaseTrackerView(self.content, self.staff, self.db)
        elif dest == "reports":    AdminReportsView(self.content, self.staff, self.db)
        elif dest == "explorer":   DataExplorerView(self.content, self.staff, self.db)


# ══════════════════════════════════════════════════════════════════
#  COMMUNE VIEW (admin — read-only, no add buttons, but full record access)
# ══════════════════════════════════════════════════════════════════

class AdminCommuneView(tk.Frame):
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
        tk.Label(lft, text="Full view of all units at your location — click any card for complete records.",
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
        tk.Label(fbar, text="  Filter:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left", padx=(12, 8))
        self._fbtns = {}
        for s, c in [("All", TEXT_DIM), ("Available", SUCCESS), ("Occupied", ACCENT), ("Under Maintenance", WARNING)]:
            btn = tk.Button(fbar, text=s, font=FONT_SMALL, relief="flat", bd=0,
                            padx=10, pady=4, cursor="hand2", highlightthickness=1,
                            command=lambda s=s: self._set_filter(s))
            btn.pack(side="left", padx=(0, 4))
            self._fbtns[s] = (btn, c)
        self._refresh_filter_btns()

        outer, self.grid_inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 16))

    def _load(self):
        self._all = self.db.get_all_apartments(self.staff.location_id)
        self._render_stats()
        self._filter()

    def _render_stats(self):
        for w in self.stat_row.winfo_children(): w.destroy()
        stats = self.db.get_dashboard_stats(self.staff.location_id)
        for label, key, col in [("Total", "total_apartments", TEXT),
                                  ("Occupied", "occupied_apartments", ACCENT),
                                  ("Available", "available_apartments", SUCCESS),
                                  ("Open Issues", "open_maintenance", WARNING)]:
            stat_pill(self.stat_row, label, stats[key], col)

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
        tk.Label(body, text=f"{apt.apartment_type}  •  {apt.num_bedrooms}bd  •  Floor {apt.floor}",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))
        tk.Label(body, text=f"£{apt.monthly_rent:,.0f}/mo",
                 font=("Segoe UI", 13, "bold"), bg=CARD_BG, fg=ACCENT).pack(anchor="w", pady=(8, 0))

        def click(e=None, a=apt): ApartmentDetailWindow(self, a, self.staff, self.db)
        def _bind(w):
            try: w.bind("<Button-1>", click)
            except Exception: pass
            for child in w.winfo_children(): _bind(child)
        _bind(outer)
        outer.bind("<Enter>", lambda e: outer.config(highlightbackground=ACCENT, highlightthickness=2))
        outer.bind("<Leave>", lambda e: outer.config(highlightbackground=BORDER, highlightthickness=1))


# ══════════════════════════════════════════════════════════════════
#  STAFF MANAGEMENT
# ══════════════════════════════════════════════════════════════════

class StaffView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._staff_list = []
        self.pack(fill="both", expand=True)
        page_header(self, "Staff Accounts",
                    "Manage all staff accounts at your location — create, edit, deactivate.")
        top_bar = tk.Frame(self, bg=DARK_BG)
        top_bar.pack(fill="x", padx=28, pady=(0, 8))
        mkbtn(top_bar, "➕  Add Staff Account",
              lambda: StaffDialog(self, self.staff, self.db, on_save=self._load),
              small=True).pack(side="right")
        export_bar(top_bar, "Staff Accounts", self._get_export_staff).pack(side="left")
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._load()

    def _get_export_staff(self):
        cols = ["ID", "Name", "Username", "Role", "Email", "Phone", "Active"]
        rows = [(s.id, s.full_name, s.username, s.role,
                 s.email or "", s.phone or "",
                 "Yes" if s.is_active else "No")
                for s in self._staff_list]
        return cols, rows

    def _load(self):
        for w in self.table.winfo_children(): w.destroy()
        staff_list = self.db.get_staff_for_location(self.staff.location_id)
        self._staff_list = staff_list

        # Summary pills
        pills = tk.Frame(self.table, bg=DARK_BG)
        pills.pack(fill="x", padx=24, pady=(8, 12))
        for role in ROLES + ["Administrator"]:
            count = sum(1 for s in staff_list if s.role == role)
            if count:
                p = tk.Frame(pills, bg=CARD_BG, padx=12, pady=6)
                p.pack(side="left", padx=(0, 6))
                tk.Label(p, text=str(count), font=("Segoe UI", 13, "bold"), bg=CARD_BG, fg=ACCENT).pack()
                tk.Label(p, text=role, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

        COLS = [("ID", 4), ("Name", 18), ("Username", 14), ("Role", 16),
                ("Email", 22), ("Phone", 13), ("Active", 7), ("Actions", 20)]
        col_headers(self.table, COLS)

        for s in staff_list:
            row = tk.Frame(self.table, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            active_col = SUCCESS if s.is_active else DANGER
            active_txt = "✓ Yes" if s.is_active else "✗ No"
            for val, w in [(str(s.id), 4), (s.full_name, 18), (s.username, 14),
                           (s.role, 16), (s.email or "—", 22), (s.phone or "—", 13)]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
            tk.Label(row, text=active_txt, font=FONT_BODY, bg=CARD_BG, fg=active_col,
                     width=7, anchor="w").pack(side="left", padx=4)
            act = tk.Frame(row, bg=CARD_BG)
            act.pack(side="left", padx=4)
            mkbtn(act, "Edit",
                  lambda s=s: StaffDialog(self, self.staff, self.db, edit_staff=s, on_save=self._load),
                  small=True).pack(side="left", padx=(0, 4))
            toggle_txt = "Deactivate" if s.is_active else "Activate"
            toggle_col = WARNING if s.is_active else SUCCESS
            if s.id != self.staff.id and s.role != "Manager":
                mkbtn(act, toggle_txt, lambda sid=s.id: self._toggle(sid),
                      color=toggle_col, small=True).pack(side="left", padx=(0, 4))
            mkbtn(act, "Reset PW", lambda sid=s.id: self._reset_pw(sid),
                  color=ACCENT2, small=True).pack(side="left")
            divider(self.table)

    def _toggle(self, staff_id):
        new_state = self.db.toggle_staff_active(staff_id)
        self._load()

    def _reset_pw(self, staff_id):
        new_pw = tk.simpledialog.askstring("Reset Password",
                                            "Enter new password for this staff member:",
                                            parent=self, show="*")
        if new_pw and len(new_pw) >= 6:
            self.db.reset_staff_password(staff_id, new_pw)
            messagebox.showinfo("Password Reset", "Password has been updated.", parent=self)
        elif new_pw:
            messagebox.showwarning("Too Short", "Password must be at least 6 characters.", parent=self)


# ── Staff Create / Edit Dialog ────────────────────────────────────────────────

class StaffDialog(tk.Toplevel):
    def __init__(self, parent, admin_staff, db, edit_staff=None, on_save=None):
        super().__init__(parent)
        self.admin_staff = admin_staff
        self.db = db
        self.edit_staff = edit_staff
        self.on_save = on_save
        mode = "Edit Staff Account" if edit_staff else "Add Staff Account"
        self.title(mode)
        self.geometry("520x460")
        self.configure(bg=DARK_BG)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Edit Staff" if self.edit_staff else "New Staff Account",
                 font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")

        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        s = self.edit_staff
        self.v_fn   = entry_var(form, "First Name *",  0, 0, s.first_name if s else "", width=22)
        self.v_ln   = entry_var(form, "Last Name *",   0, 1, s.last_name  if s else "", width=22)

        if not s:  # username only on create
            self.v_un = entry_var(form, "Username *", 2, 0, width=22)
            tk.Label(form, text="Password *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                     ).grid(row=2, column=1, sticky="w", padx=6, pady=(8, 2))
            self.v_pw = tk.StringVar()
            tk.Entry(form, textvariable=self.v_pw, show="●", font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                     insertbackground=TEXT, relief="flat", bd=0, width=22,
                     highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER
                     ).grid(row=3, column=1, sticky="ew", padx=6, pady=(0, 4))

        self.v_role = combo_var(form, "Role *", ROLES, 4, 0, default=s.role if s else ROLES[0], width=20)
        self.v_em   = entry_var(form, "Email",    4, 1, s.email if s else "", width=22)
        self.v_ph   = entry_var(form, "Phone",    6, 0, s.phone if s else "", width=22)

        # Location — admin can only assign to their own location
        locs = self.db.get_all_locations()
        loc_labels = [f"{l.city} — {l.address}" for l in locs]
        loc_map = {lbl: l.id for lbl, l in zip(loc_labels, locs)}
        default_loc = next((lbl for lbl, lid in loc_map.items()
                            if lid == self.admin_staff.location_id), loc_labels[0])
        self.v_loc = combo_var(form, "Location", loc_labels, 6, 1, default=default_loc, width=26)
        self._loc_map = loc_map

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=8, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Save ✓", self._save, color=SUCCESS).pack(side="right")

    def _save(self):
        fn = self.v_fn.get().strip()
        ln = self.v_ln.get().strip()
        role = self.v_role.get()
        email = self.v_em.get().strip()
        phone = self.v_ph.get().strip()
        loc_id = self._loc_map.get(self.v_loc.get(), self.admin_staff.location_id)

        if not fn or not ln:
            messagebox.showwarning("Missing", "First and last name required.", parent=self)
            return

        if self.edit_staff:
            self.db.update_staff(self.edit_staff.id, fn, ln, role, email, phone, loc_id)
            messagebox.showinfo("Saved", f"{fn} {ln}'s account updated.", parent=self)
        else:
            un = self.v_un.get().strip()
            pw = self.v_pw.get()
            if not un or not pw:
                messagebox.showwarning("Missing", "Username and password required.", parent=self)
                return
            if len(pw) < 6:
                messagebox.showwarning("Weak", "Password must be at least 6 characters.", parent=self)
                return
            if self.db.username_exists(un):
                messagebox.showwarning("Taken", f"Username '{un}' is already in use.", parent=self)
                return
            self.db.create_staff(un, pw, fn, ln, role, email, phone, loc_id)
            messagebox.showinfo("Created", f"Account for {fn} {ln} created.\nUsername: {un}", parent=self)

        if self.on_save: self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  APARTMENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════

class ApartmentsManageView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._apts = []
        self.pack(fill="both", expand=True)
        page_header(self, "Manage Apartments",
                    "Add, edit and remove apartments at your location.")
        top_bar = tk.Frame(self, bg=DARK_BG)
        top_bar.pack(fill="x", padx=28, pady=(0, 8))
        mkbtn(top_bar, "➕  Add Apartment",
              lambda: ApartmentDialog(self, self.staff, self.db, on_save=self._load),
              small=True).pack(side="right")
        export_bar(top_bar, "Apartments", self._get_export_apts).pack(side="left")
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._load()

    def _get_export_apts(self):
        cols = ["Unit", "Type", "Beds", "Baths", "Floor",
                "Rent (£)", "Size (sqft)", "Furnished", "Parking", "Status"]
        rows = [(a.unit_number, a.apartment_type, a.num_bedrooms, a.num_bathrooms,
                 a.floor, f"{a.monthly_rent:.2f}",
                 f"{a.size_sqft:.0f}" if a.size_sqft else "",
                 "Yes" if a.furnished else "No",
                 "Yes" if a.parking else "No",
                 a.status)
                for a in self._apts]
        return cols, rows

    def _load(self):
        for w in self.table.winfo_children(): w.destroy()
        apts = self.db.get_all_apartments(self.staff.location_id)
        self._apts = apts

        pills = tk.Frame(self.table, bg=DARK_BG)
        pills.pack(fill="x", padx=24, pady=(8, 12))
        for label, val, col in [
            ("Total", len(apts), TEXT),
            ("Occupied", sum(1 for a in apts if a.status=="Occupied"), ACCENT),
            ("Available", sum(1 for a in apts if a.status=="Available"), SUCCESS),
            ("Maintenance", sum(1 for a in apts if a.status=="Under Maintenance"), WARNING),
        ]:
            stat_pill(pills, label, val, col)

        COLS = [("Unit", 8), ("Type", 12), ("Beds", 5), ("Baths", 5), ("Floor", 6),
                ("Rent", 9), ("Size", 8), ("Status", 14), ("Actions", 20)]
        col_headers(self.table, COLS)

        for apt in apts:
            row = tk.Frame(self.table, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w in [
                (apt.unit_number, 8), (apt.apartment_type, 12),
                (str(apt.num_bedrooms), 5), (str(apt.num_bathrooms), 5),
                (str(apt.floor), 6), (f"£{apt.monthly_rent:,.0f}", 9),
                (f"{apt.size_sqft:.0f}" if apt.size_sqft else "—", 8),
                (apt.status, 14),
            ]:
                col = sc(val) if val == apt.status else TEXT
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)
            act = tk.Frame(row, bg=CARD_BG)
            act.pack(side="left", padx=4)
            mkbtn(act, "Edit",
                  lambda a=apt: ApartmentDialog(self, self.staff, self.db, edit_apt=a, on_save=self._load),
                  small=True).pack(side="left", padx=(0, 4))
            mkbtn(act, "Delete", lambda a=apt: self._delete(a),
                  color=DANGER, small=True).pack(side="left")
            divider(self.table)

    def _delete(self, apt):
        if not messagebox.askyesno("Delete", f"Delete Unit {apt.unit_number}?\nThis cannot be undone.", parent=self):
            return
        ok = self.db.delete_apartment(apt.id)
        if ok:
            messagebox.showinfo("Deleted", f"Unit {apt.unit_number} removed.", parent=self)
            self._load()
        else:
            messagebox.showwarning("Cannot Delete",
                                   f"Unit {apt.unit_number} has an active lease and cannot be deleted.", parent=self)


# ── Apartment Create / Edit Dialog ────────────────────────────────────────────

class ApartmentDialog(tk.Toplevel):
    def __init__(self, parent, staff, db, edit_apt=None, on_save=None):
        super().__init__(parent)
        self.staff = staff
        self.db = db
        self.edit_apt = edit_apt
        self.on_save = on_save
        self.title("Edit Apartment" if edit_apt else "Add Apartment")
        self.geometry("580x540")
        self.configure(bg=DARK_BG)
        self.grab_set()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Edit Apartment" if self.edit_apt else "New Apartment",
                 font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")

        outer, inner = scrollable(self, CARD_BG)
        outer.pack(fill="both", expand=True)
        form = inner
        form.config(padx=28, pady=20)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        a = self.edit_apt
        self.v_unit  = entry_var(form, "Unit Number *", 0, 0, a.unit_number if a else "", width=14)
        apt_types    = ["Studio", "Flat", "Maisonette", "Penthouse", "House", "Bungalow"]
        self.v_type  = combo_var(form, "Type *", apt_types, 0, 1,
                                  default=a.apartment_type if a else "Flat", width=14)
        statuses     = ["Available", "Occupied", "Under Maintenance"]
        self.v_stat  = combo_var(form, "Status *", statuses, 0, 2,
                                  default=a.status if a else "Available", width=14)

        self.v_beds  = entry_var(form, "Bedrooms *",  2, 0, str(a.num_bedrooms) if a else "1", width=10)
        self.v_baths = entry_var(form, "Bathrooms *", 2, 1, str(a.num_bathrooms) if a else "1", width=10)
        self.v_floor = entry_var(form, "Floor",       2, 2, str(a.floor) if a else "0", width=10)

        self.v_rent  = entry_var(form, "Monthly Rent (£) *", 4, 0, f"{a.monthly_rent:.2f}" if a else "", width=14)
        self.v_sqft  = entry_var(form, "Size (sq ft)",       4, 1, f"{a.size_sqft:.0f}" if a and a.size_sqft else "", width=14)

        # Checkboxes
        self.v_furn = tk.BooleanVar(value=a.furnished if a else False)
        self.v_park = tk.BooleanVar(value=a.parking if a else False)
        cb_row = tk.Frame(form, bg=CARD_BG)
        cb_row.grid(row=6, column=0, columnspan=3, sticky="w", padx=6, pady=(8, 4))
        tk.Checkbutton(cb_row, text="Furnished", variable=self.v_furn,
                       bg=CARD_BG, fg=TEXT, selectcolor=PANEL_BG, font=FONT_BODY).pack(side="left", padx=(0, 16))
        tk.Checkbutton(cb_row, text="Parking included", variable=self.v_park,
                       bg=CARD_BG, fg=TEXT, selectcolor=PANEL_BG, font=FONT_BODY).pack(side="left")

        tk.Label(form, text="Description", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=7, column=0, columnspan=3, sticky="w", padx=6, pady=(8, 2))
        self.v_desc = tk.Text(form, font=FONT_BODY, bg=PANEL_BG, fg=TEXT, insertbackground=TEXT,
                               relief="flat", bd=0, width=58, height=4,
                               highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        self.v_desc.grid(row=8, column=0, columnspan=3, sticky="ew", padx=6)
        if a and a.description:
            self.v_desc.insert("1.0", a.description)

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=9, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Save ✓", self._save, color=SUCCESS).pack(side="right")

    def _save(self):
        unit = self.v_unit.get().strip()
        if not unit:
            messagebox.showwarning("Missing", "Unit number required.", parent=self)
            return
        try:
            rent  = float(self.v_rent.get().strip())
            beds  = int(self.v_beds.get().strip())
            baths = int(self.v_baths.get().strip())
            floor = int(self.v_floor.get().strip() or "0")
            sqft  = float(self.v_sqft.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("Invalid", "Check numeric fields (rent, beds, baths, floor, sqft).", parent=self)
            return

        apt = self.edit_apt or Apartment()
        apt.unit_number   = unit
        apt.location_id   = self.staff.location_id
        apt.apartment_type= self.v_type.get()
        apt.num_bedrooms  = beds
        apt.num_bathrooms = baths
        apt.floor         = floor
        apt.monthly_rent  = rent
        apt.size_sqft     = sqft
        apt.furnished     = self.v_furn.get()
        apt.parking       = self.v_park.get()
        apt.status        = self.v_stat.get()
        apt.description   = self.v_desc.get("1.0", "end-1c").strip()

        if self.edit_apt:
            self.db.update_apartment(apt)
            messagebox.showinfo("Saved", f"Unit {apt.unit_number} updated.", parent=self)
        else:
            new_id = self.db.create_apartment(apt)
            messagebox.showinfo("Created", f"Unit {apt.unit_number} created (ID #{new_id}).", parent=self)

        if self.on_save: self.on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  LEASE TRACKER
# ══════════════════════════════════════════════════════════════════

class LeaseTrackerView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._leases = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _get_export_leases(self):
        cols = ["Lease #", "Tenant", "Unit", "Location",
                "Start Date", "End Date", "Days Left", "Rent (£)", "Status"]
        rows = [(f"#{l.id}", l.tenant_name, l.apartment_unit, l.location_city,
                 l.start_date, l.end_date,
                 getattr(l, "days_remaining", ""),
                 f"{l.monthly_rent:.2f}", l.status)
                for l in self._leases]
        return cols, rows

    def _build(self):
        page_header(self, "Lease Tracker",
                    "Monitor upcoming and expired lease agreements at your location.")
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
        for label, val in [("Expired","expired"),("30 days","30"),("60 days","60"),
                           ("90 days","90"),("180 days","180"),("All","all")]:
            b = tk.Button(fbar, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                          command=lambda d=val: _set_win(d))
            b.pack(side="left", padx=2)
            self._day_btns[val] = b
        self._day_btns["30"].config(bg=ACCENT, fg="white")
        export_bar(fbar, "Leases", self._get_export_leases).pack(side="right")

        self.sum_row = tk.Frame(self, bg=DARK_BG)
        self.sum_row.pack(fill="x", padx=28, pady=(0, 6))
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)

    def _load(self):
        for w in self.sum_row.winfo_children(): w.destroy()
        for w in self.table.winfo_children(): w.destroy()

        all_leases = self.db.get_expiring_leases(3650, self.staff.location_id)

        expired   = [l for l in all_leases if getattr(l, "days_remaining", 0) < 0]
        critical  = [l for l in all_leases if 0 <= getattr(l, "days_remaining", 0) <= 30]
        warning   = [l for l in all_leases if 30 < getattr(l, "days_remaining", 0) <= 90]
        upcoming  = [l for l in all_leases if getattr(l, "days_remaining", 0) > 90]

        for label, lst, col in [("Expired", expired, DANGER),
                                  ("< 30 days", critical, WARNING),
                                  ("31–90 days", warning, ACCENT),
                                  ("90+ days", upcoming, SUCCESS)]:
            stat_pill(self.sum_row, label, len(lst), col)

        win = self._win_v.get()
        if win == "expired":
            leases = expired
        elif win == "all":
            leases = all_leases
        else:
            n = int(win)
            leases = [l for l in all_leases if 0 <= getattr(l, "days_remaining", 0) <= n]
        self._leases = leases

        if not leases:
            tk.Label(self.table, text="No leases in this window.",
                     font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(pady=30)
            return

        COLS = [("Lease #", 8), ("Tenant", 18), ("Unit", 8), ("Start", 11),
                ("End Date", 11), ("Days Left", 12), ("Rent", 9), ("Status", 10), ("Actions", 20)]
        col_headers(self.table, COLS)

        for i, l in enumerate(leases):
            days_left = getattr(l, "days_remaining", 0)
            row_bg = CARD_BG if i % 2 == 0 else HOVER_BG
            row = tk.Frame(self.table, bg=row_bg)
            row.pack(fill="x", padx=24)

            days_col = (DANGER if days_left < 0 else
                        WARNING if days_left <= 30 else
                        ACCENT if days_left <= 90 else SUCCESS)
            days_str = f"{days_left}d" if days_left >= 0 else f"Expired {abs(days_left)}d ago"
            status_label = "Expired" if days_left < 0 else l.status
            status_col = DANGER if days_left < 0 else sc(l.status)

            for val, w, col in [
                (f"#{l.id}", 8, TEXT), (l.tenant_name, 18, TEXT),
                (l.apartment_unit, 8, TEXT), (l.start_date, 11, TEXT),
                (l.end_date, 11, TEXT), (days_str, 12, days_col),
                (f"£{l.monthly_rent:,.0f}", 9, TEXT), (status_label, 10, status_col),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=row_bg, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=7)

            act = tk.Frame(row, bg=row_bg)
            act.pack(side="left", padx=4)
            mkbtn(act, "View Details", lambda l=l: self._open_detail(l),
                  small=True).pack(side="left", padx=(0, 4))
            if l.status == "Active":
                mkbtn(act, "Mark Expired", lambda l=l: self._expire(l),
                      color=DANGER, small=True).pack(side="left")
            divider(self.table)

    def _open_detail(self, lease):
        win = tk.Toplevel(self)
        win.title(f"Lease #{lease.id} — {lease.tenant_name}")
        win.geometry("700x500")
        win.configure(bg=DARK_BG)
        outer, inner = scrollable(win, CARD_BG)
        outer.pack(fill="both", expand=True, padx=0)
        sec_hdr(inner, "Lease Details")
        info_grid(inner, [
            ("Lease ID", f"#{lease.id}"), ("Status", lease.status),
            ("Tenant", lease.tenant_name), ("Email", lease.tenant_email),
            ("Phone", lease.tenant_phone), ("Apartment", lease.apartment_unit),
            ("Type", lease.apartment_type), ("City", lease.location_city),
            ("Start Date", lease.start_date), ("End Date", lease.end_date),
            ("Monthly Rent", f"£{lease.monthly_rent:,.2f}"),
            ("Deposit", f"£{lease.deposit_amount:,.2f}"),
        ], cols=3)
        days = getattr(lease, "days_remaining", None)
        if days is not None:
            col = DANGER if days < 0 else WARNING if days <= 30 else SUCCESS
            sec_hdr(inner, "Expiry Status")
            msg = f"Expired {abs(days)} days ago" if days < 0 else f"{days} days remaining"
            tk.Label(inner, text=msg, font=FONT_TITLE, bg=CARD_BG, fg=col).pack(padx=28, pady=8, anchor="w")

    def _expire(self, lease):
        if messagebox.askyesno("Confirm", f"Mark Lease #{lease.id} as Expired?", parent=self):
            self.db.update_lease_status(lease.id, "Expired")
            self._load()


# ══════════════════════════════════════════════════════════════════
#  ADMIN REPORTS
# ══════════════════════════════════════════════════════════════════

class AdminReportsView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        page_header(self, "Location Reports",
                    f"Operational reports for your location.")
        self._nb_style()
        nb = ttk.Notebook(self, style="A.TNotebook")
        nb.pack(fill="both", expand=True)
        self._tab_summary(nb)
        self._tab_leases(nb)
        self._tab_financial(nb)
        self._tab_maintenance(nb)

    def _nb_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("A.TNotebook", background=DARK_BG, borderwidth=0, tabmargins=0)
        s.configure("A.TNotebook.Tab", background=PANEL_BG, foreground=TEXT_DIM,
                    font=FONT_BODY, padding=[16, 8])
        s.map("A.TNotebook.Tab", background=[("selected", CARD_BG)], foreground=[("selected", TEXT)])

    def _tab(self, nb, title):
        f = tk.Frame(nb, bg=CARD_BG)
        nb.add(f, text=f"  {title}  ")
        return f

    def _tab_summary(self, nb):
        frame = self._tab(nb, "Overview")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        stats  = self.db.get_dashboard_stats(self.staff.location_id)
        fin    = self.db.get_financial_summary(self.staff.location_id)
        maint  = self.db.get_maintenance_stats(self.staff.location_id)
        locs   = {l.id: l.city for l in self.db.get_all_locations()}
        city   = locs.get(self.staff.location_id, "")

        sec_hdr(inner, f"Summary — {city}")
        kpi = tk.Frame(inner, bg=CARD_BG)
        kpi.pack(fill="x", padx=24, pady=(0, 16))
        for label, val, col in [
            ("Total Apartments", stats["total_apartments"],       TEXT),
            ("Occupied",         stats["occupied_apartments"],    ACCENT),
            ("Available",        stats["available_apartments"],   SUCCESS),
            ("Active Leases",    stats["active_leases"],          ACCENT2),
            ("Revenue Collected",f"£{fin['total_collected']:,.0f}", SUCCESS),
            ("Outstanding",      f"£{fin['overdue']:,.0f}",        DANGER),
            ("Open Jobs",        stats["open_maintenance"],        WARNING),
            ("Open Complaints",  stats["open_complaints"],         WARNING),
        ]:
            tile = tk.Frame(kpi, bg=PANEL_BG, padx=18, pady=14)
            tile.pack(side="left", padx=(0, 8), pady=4)
            tk.Label(tile, text=str(val), font=("Segoe UI", 16, "bold"), bg=PANEL_BG, fg=col).pack()
            tk.Label(tile, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack()

        sec_hdr(inner, "Staff at This Location")
        staff_list = self.db.get_staff_for_location(self.staff.location_id)
        col_headers(inner, [("Name",16),("Role",18),("Username",14),("Email",24),("Active",8)])
        for s in staff_list:
            row = tk.Frame(inner, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w in [(s.full_name,16),(s.role,18),(s.username,14),(s.email or "—",24)]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            active_col = SUCCESS if s.is_active else DANGER
            tk.Label(row, text="✓" if s.is_active else "✗", font=FONT_BODY, bg=CARD_BG,
                     fg=active_col, width=8, anchor="w").pack(side="left", padx=4)
            divider(inner)

    def _tab_leases(self, nb):
        frame = self._tab(nb, "Lease Agreements")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        all_leases = self.db.get_all_leases(location_id=self.staff.location_id)
        exp = self.db.get_expiring_leases(90, self.staff.location_id)

        sec_hdr(inner, f"All Leases  ({len(all_leases)} total)")
        COLS = [("ID",6),("Tenant",18),("Unit",8),("Start",11),("End",11),
                ("Rent",9),("Deposit",9),("Status",10)]
        col_headers(inner, COLS)
        for l in all_leases:
            row = tk.Frame(inner, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w in [(f"#{l.id}",6),(l.tenant_name,18),(l.apartment_unit,8),
                           (l.start_date,11),(l.end_date,11),
                           (f"£{l.monthly_rent:,.0f}",9),(f"£{l.deposit_amount:,.0f}",9),
                           (l.status,10)]:
                col = sc(val) if val == l.status else TEXT
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            divider(inner)

        if exp:
            sec_hdr(inner, f"Expiring Within 90 Days  ({len(exp)})")
            for l in exp:
                days = getattr(l, "days_remaining", 0)
                days_col = DANGER if days < 0 else WARNING if days <= 30 else ACCENT
                card = tk.Frame(inner, bg=PANEL_BG, padx=16, pady=10)
                card.pack(fill="x", padx=24, pady=3)
                top = tk.Frame(card, bg=PANEL_BG)
                top.pack(fill="x")
                tk.Label(top, text=f"{l.tenant_name}  —  Unit {l.apartment_unit}",
                         font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
                days_str = f"{days}d remaining" if days >= 0 else f"Expired {abs(days)}d ago"
                tk.Label(top, text=days_str, font=FONT_SMALL, bg=PANEL_BG, fg=days_col).pack(side="right")
                tk.Label(card, text=f"End date: {l.end_date}  •  £{l.monthly_rent:,.0f}/mo  •  {l.tenant_email}",
                         font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")

    def _tab_financial(self, nb):
        frame = self._tab(nb, "Financial")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)
        fin = self.db.get_financial_summary(self.staff.location_id)
        rev = self.db.get_monthly_revenue(self.staff.location_id, months=12)

        sec_hdr(inner, "Revenue Summary")
        info_grid(inner, [
            ("Total Billed",     f"£{fin['total_billed']:,.2f}"),
            ("Collected",        f"£{fin['total_collected']:,.2f}"),
            ("Pending",          f"£{fin['pending']:,.2f}"),
            ("Overdue",          f"£{fin['overdue']:,.2f}"),
            ("Maintenance Spend",f"£{fin['maintenance_cost']:,.2f}"),
            ("Net Revenue",      f"£{fin['total_collected']-fin['maintenance_cost']:,.2f}"),
            ("Paid Invoices",    str(fin['paid_count'])),
            ("Overdue Invoices", str(fin['overdue_count'])),
            ("Occupancy Rate",   f"{fin['occupancy_rate']:.1f}%"),
        ], cols=3)

        sec_hdr(inner, "Monthly Revenue")
        if not rev:
            tk.Label(inner, text="No revenue data.", font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM).pack(padx=28)
        else:
            COLS = [("Month",12),("Collected",14)]
            col_headers(inner, COLS)
            for r in rev:
                row = tk.Frame(inner, bg=CARD_BG)
                row.pack(fill="x", padx=24)
                tk.Label(row, text=r["month"] or "—", font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         width=12, anchor="w").pack(side="left", padx=4, pady=5)
                tk.Label(row, text=f"£{r['collected']:,.2f}", font=FONT_BODY, bg=CARD_BG, fg=SUCCESS,
                         width=14, anchor="w").pack(side="left", padx=4)
                divider(inner)

    def _tab_maintenance(self, nb):
        frame = self._tab(nb, "Maintenance")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)
        mc = self.db.get_maintenance_cost_report(self.staff.location_id)
        maint = self.db.get_maintenance_stats(self.staff.location_id)

        sec_hdr(inner, "Maintenance Overview")
        info_grid(inner, [
            ("Open",          str(maint.get("open", 0))),
            ("In Progress",   str(maint.get("in_progress", 0))),
            ("Resolved",      str(maint.get("resolved", 0))),
            ("Total Cost",    f"£{maint.get('total_cost', 0):,.2f}"),
        ], cols=4)

        sec_hdr(inner, "Cost by Category")
        if not mc:
            tk.Label(inner, text="No maintenance data.", font=FONT_BODY, bg=CARD_BG, fg=TEXT_DIM).pack(padx=28)
        else:
            COLS = [("Category",16),("Jobs",6),("Total Cost",13),("Avg Cost",12),("Hours",8)]
            col_headers(inner, COLS)
            for d in mc:
                row = tk.Frame(inner, bg=CARD_BG)
                row.pack(fill="x", padx=24)
                for val, w in [(d["category"] or "—",16),(str(d["count"]),6),
                               (f"£{d['total_cost']:,.2f}",13),(f"£{d['avg_cost']:,.2f}",12),
                               (f"{d['total_hours']:.1f}h",8)]:
                    tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                             width=w, anchor="w").pack(side="left", padx=4, pady=5)
                divider(inner)