"""
views_finance.py — Finance Manager UI
Tabs: Payments | Invoices | Late Payments | Reports
Shares the commune apartment grid from views.py (read-only for finance).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, List, Callable

# Re-use palette + helpers from views.py
from .views import (
    DARK_BG, PANEL_BG, CARD_BG, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    TEXT, TEXT_DIM, TEXT_MUTED, BORDER, HOVER_BG,
    FONT_HEAD, FONT_TITLE, FONT_SUB, FONT_BODY, FONT_SMALL,
    sc, badge, mkbtn, entry_var, combo_var, scrollable, sec_hdr, info_grid,
    CommuneView,           # read-only commune grid
    export_bar,
)


# ═══════════════════════════════════════════════════════════════════
#  FINANCE APP SHELL
# ═══════════════════════════════════════════════════════════════════

class FinanceAppShell(tk.Frame):
    """Top-level shell for Finance Manager — sidebar + content area."""

    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        self._build_sidebar()
        self.content = tk.Frame(self, bg=DARK_BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._go("commune")

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=PANEL_BG, width=218,
                         highlightbackground=BORDER, highlightthickness=1)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Label(sb, text="🏢  PropManage", font=("Segoe UI", 12, "bold"),
                 bg=PANEL_BG, fg=TEXT).pack(padx=20, pady=(22, 10), anchor="w")

        uc = tk.Frame(sb, bg=HOVER_BG, padx=14, pady=10)
        uc.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(uc, text=self.staff.full_name, font=FONT_SUB, bg=HOVER_BG, fg=TEXT).pack(anchor="w")
        badge(uc, self.staff.role, ACCENT).pack(anchor="w", pady=(4, 0))
        locs = {l.id: l.city for l in self.db.get_all_locations()}
        city = locs.get(self.staff.location_id, "All")
        tk.Label(uc, text=f"📍 {city}", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        self._nbtn = {}
        nav_items = [
            ("commune",   "🏠  Apartments",     "commune"),
            ("payments",  "💳  Payments",        "payments"),
            ("invoices",  "🧾  Create Invoice",  "invoices"),
            ("late",      "⚠  Late Payments",   "late"),
            ("reports",   "📊  Reports",         "reports"),
        ]
        for key, label, dest in nav_items:
            b = tk.Button(sb, text=label, font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM,
                          relief="flat", bd=0, anchor="w", padx=18, pady=11,
                          cursor="hand2", activebackground=HOVER_BG, activeforeground=TEXT,
                          command=lambda d=dest, k=key: self._nav(k, d))
            b.pack(fill="x")
            self._nbtn[key] = b

        tk.Frame(sb, bg=PANEL_BG).pack(fill="both", expand=True)
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=10)
        _so = tk.Button(sb, text="⬅  Sign Out", font=FONT_SMALL, bg=PANEL_BG, fg=DANGER,
                        relief="flat", bd=0, anchor="w", padx=18, pady=12,
                        cursor="hand2", activebackground="#FEE2E2", activeforeground=DANGER,
                        command=self._logout)
        _so.pack(fill="x")
        _so.bind("<Enter>", lambda e: _so.config(bg="#FEE2E2"))
        _so.bind("<Leave>", lambda e: _so.config(bg=PANEL_BG))

    def _nav(self, key, dest):
        for k, b in self._nbtn.items():
            b.config(bg=PANEL_BG, fg=TEXT_DIM)
        self._nbtn[key].config(bg=HOVER_BG, fg=TEXT)
        self._go(dest)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _go(self, dest):
        self._clear()
        if dest == "commune":
            self._nbtn["commune"].config(bg=HOVER_BG, fg=TEXT)
            CommuneView(self.content, self.staff, self.db)
        elif dest == "payments":
            PaymentsView(self.content, self.staff, self.db)
        elif dest == "invoices":
            InvoiceView(self.content, self.staff, self.db)
        elif dest == "late":
            LatePaymentsView(self.content, self.staff, self.db)
        elif dest == "reports":
            ReportsView(self.content, self.staff, self.db)

    def _logout(self):
        if messagebox.askyesno("Sign Out", "Sign out?"):
            self.destroy()
            self.master.show_login()


# ═══════════════════════════════════════════════════════════════════
#  SHARED: column header row
# ═══════════════════════════════════════════════════════════════════

def col_headers(parent, cols: list, bg=PANEL_BG):
    """cols = [(label, width), ...]"""
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", padx=24, pady=(4, 0))
    for label, w in cols:
        tk.Label(row, text=label, font=FONT_SMALL, bg=bg, fg=TEXT_DIM,
                 width=w, anchor="w").pack(side="left", padx=4, pady=6)
    return row


def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24)


def page_header(parent, title: str, subtitle: str = ""):
    hdr = tk.Frame(parent, bg=DARK_BG, padx=28, pady=20)
    hdr.pack(fill="x")
    tk.Label(hdr, text=title, font=FONT_HEAD, bg=DARK_BG, fg=TEXT).pack(anchor="w")
    if subtitle:
        tk.Label(hdr, text=subtitle, font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(anchor="w")
    return hdr


# ═══════════════════════════════════════════════════════════════════
#  PAYMENTS VIEW — full ledger, mark paid, filter
# ═══════════════════════════════════════════════════════════════════

class PaymentsView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._payments = []
        self._shown = []
        self.pack(fill="both", expand=True)
        self._build()
        self._load()

    def _get_export_payments(self):
        cols = ["Reference", "Tenant", "Unit", "City",
                "Due Date", "Amount Due (£)", "Paid (£)", "Status"]
        rows = [(p.reference_number or "", p.tenant_name or "",
                 getattr(p, "unit_number", ""), getattr(p, "city", ""),
                 p.due_date or "", f"{p.amount_due:.2f}",
                 f"{p.amount_paid:.2f}", p.status)
                for p in self._shown]
        return cols, rows

    def _build(self):
        page_header(self, "Payments Ledger",
                    "All payment records for your location — mark as paid, filter by status.")

        # Filter bar
        fbar = tk.Frame(self, bg=DARK_BG)
        fbar.pack(fill="x", padx=28, pady=(0, 10))

        tk.Label(fbar, text="Status:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left")
        self._status_f = tk.StringVar(value="All")
        for s, c in [("All", TEXT_DIM), ("Paid", SUCCESS), ("Pending", WARNING),
                     ("Overdue", DANGER)]:
            tk.Radiobutton(fbar, text=s, variable=self._status_f, value=s,
                           font=FONT_SMALL, bg=DARK_BG, fg=c, selectcolor=DARK_BG,
                           activebackground=DARK_BG, relief="flat", bd=0, cursor="hand2",
                           command=self._apply_filter).pack(side="left", padx=6)

        tk.Label(fbar, text="  Search:", font=FONT_SMALL, bg=DARK_BG, fg=TEXT_DIM).pack(side="left", padx=(12, 4))
        self._sv = tk.StringVar()
        self._sv.trace("w", lambda *a: self._apply_filter())
        se = tk.Entry(fbar, textvariable=self._sv, font=FONT_BODY, bg=PANEL_BG, fg=TEXT,
                      insertbackground=TEXT, relief="flat", bd=0, width=22,
                      highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER)
        se.pack(side="left", ipady=5, ipadx=8)
        export_bar(fbar, "Payments", self._get_export_payments).pack(side="right")

        # Summary pills — rebuilt after load
        self.sum_row = tk.Frame(self, bg=DARK_BG, padx=28)
        self.sum_row.pack(fill="x", pady=(0, 8))

        # Scrollable table
        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=0)

    def _load(self):
        self._payments = self.db.get_all_payments(location_id=self.staff.location_id)
        self._render_summary()
        self._apply_filter()

    def _render_summary(self):
        for w in self.sum_row.winfo_children():
            w.destroy()
        pays = self._payments
        total   = sum(p.amount_due for p in pays)
        coll    = sum(p.amount_paid for p in pays)
        pending = sum(p.amount_due for p in pays if p.status == "Pending")
        overdue = sum(p.amount_due for p in pays if p.status == "Overdue")
        for label, val, col in [
            ("Total Billed",  f"£{total:,.0f}",   TEXT),
            ("Collected",     f"£{coll:,.0f}",    SUCCESS),
            ("Pending",       f"£{pending:,.0f}", WARNING),
            ("Overdue",       f"£{overdue:,.0f}", DANGER),
        ]:
            p = tk.Frame(self.sum_row, bg=CARD_BG, padx=16, pady=8)
            p.pack(side="left", padx=(0, 8))
            tk.Label(p, text=val,   font=("Segoe UI", 14, "bold"), bg=CARD_BG, fg=col).pack()
            tk.Label(p, text=label, font=FONT_SMALL,               bg=CARD_BG, fg=TEXT_DIM).pack()

    def _apply_filter(self):
        sf = self._status_f.get()
        q  = self._sv.get().strip().lower()
        filtered = [
            p for p in self._payments
            if (sf == "All" or p.status == sf)
            and (not q or q in (p.tenant_name or "").lower()
                 or q in (p.unit_number or "").lower()
                 or q in (p.reference_number or "").lower()
                 or q in (p.city or "").lower())
        ]
        self._shown = filtered
        self._render_table(filtered)

    def _render_table(self, pays):
        for w in self.table.winfo_children():
            w.destroy()

        if not pays:
            tk.Label(self.table, text="No payments match the filter.",
                     font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(pady=30)
            return

        COLS = [("Reference", 14), ("Tenant", 18), ("Unit", 8), ("City", 11),
                ("Due Date", 11), ("Amount Due", 12), ("Paid", 12), ("Status", 10), ("Actions", 14)]
        col_headers(self.table, COLS)

        for pay in pays:
            row = tk.Frame(self.table, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w in [
                (pay.reference_number or "—", 14),
                (pay.tenant_name or "—",      18),
                (getattr(pay, "unit_number", "—"), 8),
                (getattr(pay, "city", "—"),    11),
                (pay.due_date or "—",          11),
                (f"£{pay.amount_due:,.2f}",    12),
                (f"£{pay.amount_paid:,.2f}",   12),
                (pay.status,                   10),
            ]:
                color = sc(val) if val == pay.status else TEXT
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=color,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)

            act = tk.Frame(row, bg=CARD_BG, width=14*8)
            act.pack(side="left", padx=4)
            act.pack_propagate(False)
            if pay.status in ("Pending", "Overdue"):
                mkbtn(act, "Mark Paid", lambda p=pay: self._mark_paid(p),
                      color=SUCCESS, small=True).pack(side="left", pady=3)
            elif pay.status == "Paid":
                mkbtn(act, "Receipt", lambda p=pay: ReceiptWindow(self, p),
                      small=True).pack(side="left", pady=3)
            divider(self.table)

    def _mark_paid(self, pay):
        methods = ["Bank Transfer", "Standing Order", "Card", "Cash", "Cheque"]
        dlg = MarkPaidDialog(self, pay, methods, on_confirm=lambda m, d: self._do_mark(pay, m, d))

    def _do_mark(self, pay, method, paid_date):
        self.db.mark_payment_paid(pay.id, method, paid_date)
        messagebox.showinfo("Marked Paid", f"Payment {pay.reference_number} marked as Paid.\nMethod: {method}")
        self._load()


# ═══════════════════════════════════════════════════════════════════
#  MARK PAID DIALOG
# ═══════════════════════════════════════════════════════════════════

class MarkPaidDialog(tk.Toplevel):
    def __init__(self, parent, pay, methods: list, on_confirm: Callable):
        super().__init__(parent)
        self.pay = pay
        self.on_confirm = on_confirm
        self.title(f"Mark Payment as Paid — {pay.reference_number}")
        self.geometry("420x280")
        self.configure(bg=DARK_BG)
        self.grab_set()
        self._build(methods)

    def _build(self, methods):
        hdr = tk.Frame(self, bg=PANEL_BG, padx=24, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Mark as Paid", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text=f"{self.pay.reference_number}  •  {getattr(self.pay,'tenant_name','?')}  •  £{self.pay.amount_due:,.2f}",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor="w")

        form = tk.Frame(self, bg=CARD_BG, padx=28, pady=20)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        self.v_method = combo_var(form, "Payment Method *", methods, 0, 0, default=methods[0], width=18)
        self.v_date   = entry_var(form, "Payment Date *", 0, 1, default=str(date.today()), width=16)

        nav = tk.Frame(form, bg=CARD_BG, pady=14)
        nav.grid(row=2, column=0, columnspan=2, sticky="ew")
        mkbtn(nav, "Cancel", self.destroy, color=TEXT_MUTED).pack(side="left")
        mkbtn(nav, "Confirm ✓", self._confirm, color=SUCCESS).pack(side="right")

    def _confirm(self):
        method = self.v_method.get().strip()
        pd     = self.v_date.get().strip()
        if not pd:
            messagebox.showwarning("Missing", "Please enter payment date.", parent=self)
            return
        self.on_confirm(method, pd)
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  RECEIPT WINDOW
# ═══════════════════════════════════════════════════════════════════

class ReceiptWindow(tk.Toplevel):
    def __init__(self, parent, pay):
        super().__init__(parent)
        self.title(f"Receipt — {pay.reference_number}")
        self.geometry("500x440")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self._build(pay)

    def _build(self, pay):
        # Receipt card
        card = tk.Frame(self, bg=PANEL_BG, padx=36, pady=36,
                       highlightbackground=BORDER, highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="🏢  PropManage", font=("Segoe UI", 14, "bold"),
                 bg="white", fg=TEXT).pack(anchor="w")
        tk.Label(card, text="PAYMENT RECEIPT", font=("Segoe UI", 10),
                 bg="white", fg=TEXT_MUTED).pack(anchor="w", pady=(2, 16))

        tk.Frame(card, bg=BORDER, height=1, width=400).pack(fill="x", pady=(0, 16))

        for label, val in [
            ("Reference",      pay.reference_number or "—"),
            ("Tenant",         getattr(pay, "tenant_name", "—")),
            ("Unit",           getattr(pay, "unit_number", "—")),
            ("City",           getattr(pay, "city", "—")),
            ("Due Date",       pay.due_date or "—"),
            ("Paid Date",      pay.paid_date or "—"),
            ("Payment Method", pay.payment_method or "—"),
            ("Amount Paid",    f"£{pay.amount_paid:,.2f}"),
            ("Status",         pay.status),
        ]:
            row = tk.Frame(card, bg="white")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=FONT_SMALL, bg="white", fg=TEXT_MUTED,
                     width=16, anchor="w").pack(side="left")
            color = sc(val) if val == pay.status else TEXT
            tk.Label(row, text=val, font=FONT_BODY, bg="white", fg=color).pack(side="left")

        tk.Frame(card, bg=BORDER, height=1, width=400).pack(fill="x", pady=(16, 8))
        tk.Label(card, text="Thank you for your payment.", font=("Segoe UI", 9, "italic"),
                 bg="white", fg=TEXT_DIM).pack(anchor="w")

        mkbtn(self, "Close", self.destroy, color=TEXT_MUTED, small=True).pack(pady=(12, 0))


# ═══════════════════════════════════════════════════════════════════
#  INVOICE VIEW — create invoices against any active lease
# ═══════════════════════════════════════════════════════════════════

class InvoiceView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._leases = []
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Create Invoice",
                    "Raise a new invoice against an active lease — it will be marked as paid immediately.")

        outer, inner = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True, padx=28)
        inner.config(padx=0, pady=0)

        # Form card
        form = tk.Frame(inner, bg=CARD_BG, padx=32, pady=28)
        form.pack(fill="x", pady=(0, 16))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        tk.Label(form, text="Invoice Details", font=FONT_TITLE, bg=CARD_BG, fg=TEXT
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        # Lease picker — build label list
        self._leases = self.db.get_all_leases(location_id=self.staff.location_id)
        active_leases = [l for l in self._leases if l.status == "Active"]
        lease_labels  = [f"#{l.id}  {l.tenant_name}  —  Unit {l.apartment_unit}  ({l.location_city})"
                         for l in active_leases]
        self._lease_map = {lbl: l for lbl, l in zip(lease_labels, active_leases)}

        self.v_lease = combo_var(form, "Lease *", lease_labels, 1, 0, width=50)
        # patch colspan manually
        tk.Label(form, text="Lease *", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM
                 ).grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=(8, 2))
        self.v_lease = tk.StringVar(value=lease_labels[0] if lease_labels else "")
        cb = ttk.Combobox(form, textvariable=self.v_lease, values=lease_labels,
                          font=FONT_BODY, width=62, state="readonly")
        cb.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6, pady=(0, 4))
        cb.bind("<<ComboboxSelected>>", self._on_lease_select)

        self.v_amount  = entry_var(form, "Amount (£) *",  3, 0, "", 20)
        self.v_due     = entry_var(form, "Due Date *",    3, 1, str(date.today()), 16)
        self.v_desc    = entry_var(form, "Description",   3, 2, "Monthly Rent", 24)

        # Auto-fill hint
        self.hint_lbl = tk.Label(form, text="", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM)
        self.hint_lbl.grid(row=5, column=0, columnspan=3, sticky="w", padx=6)

        nav = tk.Frame(form, bg=CARD_BG, pady=16)
        nav.grid(row=6, column=0, columnspan=3, sticky="ew")
        mkbtn(nav, "Create Invoice ✓", self._create, color=SUCCESS).pack(side="right")

        # Recent invoices table
        sec_hdr(inner, "Recent Invoices  (this location)")
        self.inv_table = tk.Frame(inner, bg=DARK_BG)
        self.inv_table.pack(fill="x")
        self._load_recent()

        # pre-select first lease
        if lease_labels:
            self._on_lease_select(None)

    def _on_lease_select(self, _event):
        label = self.v_lease.get()
        lease = self._lease_map.get(label)
        if lease:
            self.v_amount.set(f"{lease.monthly_rent:.2f}")
            self.hint_lbl.config(text=f"Monthly rent: £{lease.monthly_rent:,.2f}  •  Deposit: £{lease.deposit_amount:,.2f}")

    def _create(self):
        label = self.v_lease.get()
        lease = self._lease_map.get(label)
        if not lease:
            messagebox.showwarning("No Lease", "Please select a lease.", parent=self)
            return
        try:
            amount = float(self.v_amount.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Amount", "Enter a valid amount.", parent=self)
            return
        due  = self.v_due.get().strip()
        desc = self.v_desc.get().strip()
        if not due:
            messagebox.showwarning("Missing", "Please enter a due date.", parent=self)
            return

        inv_id = self.db.create_invoice(lease.id, amount, due, desc, self.staff.id)

        # Fetch the newly created invoice from get_all_payments (which has tenant/unit/city)
        all_pays = self.db.get_all_payments(location_id=self.staff.location_id)
        new_pay  = next((p for p in all_pays if p.id == inv_id), None)
        if new_pay:
            ReceiptWindow(self, new_pay)

        messagebox.showinfo("Invoice Created ✓",
                            f"Invoice created and marked as paid.\nRef: INV-{inv_id:06d}\n"
                            f"Amount: £{amount:,.2f}  •  Lease #{lease.id}", parent=self)
        self._load_recent()

    def _load_recent(self):
        for w in self.inv_table.winfo_children():
            w.destroy()
        pays = self.db.get_all_payments(location_id=self.staff.location_id)
        inv_pays = [p for p in pays if (p.reference_number or "").startswith("INV-")][:20]
        if not inv_pays:
            tk.Label(self.inv_table, text="No invoices created yet. Use the form above to create one.",
                     font=FONT_BODY, bg=DARK_BG, fg=TEXT_DIM).pack(padx=28, pady=8, anchor="w")
            return
        COLS = [("Reference", 14), ("Tenant", 18), ("Unit", 8), ("City", 11),
                ("Date", 11), ("Amount", 12), ("Status", 10)]
        col_headers(self.inv_table, COLS)
        for pay in inv_pays:
            row = tk.Frame(self.inv_table, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w in [
                (pay.reference_number or "—", 14),
                (pay.tenant_name or "—",       18),
                (getattr(pay, "unit_number", "—"), 8),
                (getattr(pay, "city", "—"),     11),
                (pay.paid_date or "—",          11),
                (f"£{pay.amount_paid:,.2f}",    12),
                (pay.status,                    10),
            ]:
                color = sc(val) if val == pay.status else TEXT
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=color,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            mkbtn(row, "Receipt", lambda p=pay: ReceiptWindow(self, p),
                  small=True).pack(side="left", padx=6, pady=3)
            divider(self.inv_table)


# ═══════════════════════════════════════════════════════════════════
#  LATE PAYMENTS VIEW — overdue list with notifications
# ═══════════════════════════════════════════════════════════════════

class LatePaymentsView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self._overdue = []
        self.pack(fill="both", expand=True)
        self._build()

    def _get_export_late(self):
        cols = ["Reference", "Tenant", "Email", "Unit",
                "City", "Due Date", "Amount Due (£)"]
        rows = [(p.reference_number or "", p.tenant_name or "",
                 getattr(p, "tenant_email", ""),
                 getattr(p, "unit_number", ""), getattr(p, "city", ""),
                 p.due_date or "", f"{p.amount_due:.2f}")
                for p in self._overdue]
        return cols, rows

    def _build(self):
        page_header(self, "Late Payments",
                    "All overdue payments at your location — send notifications or mark as paid.")

        # Stats + export bar
        top = tk.Frame(self, bg=DARK_BG)
        top.pack(fill="x", padx=28, pady=(0, 12))
        self.stat_row = tk.Frame(top, bg=DARK_BG)
        self.stat_row.pack(side="left", fill="x", expand=True)
        export_bar(top, "Late Payments", self._get_export_late).pack(side="right", anchor="n")

        outer, self.table = scrollable(self, DARK_BG)
        outer.pack(fill="both", expand=True)
        self._load()

    def _load(self):
        for w in self.stat_row.winfo_children():
            w.destroy()
        for w in self.table.winfo_children():
            w.destroy()

        overdue = self.db.get_late_payments(location_id=self.staff.location_id)
        self._overdue = overdue
        total_overdue = sum(p.amount_due for p in overdue)

        for label, val, col in [
            ("Overdue Payments", str(len(overdue)), DANGER),
            ("Total Outstanding", f"£{total_overdue:,.2f}", DANGER),
        ]:
            p = tk.Frame(self.stat_row, bg=CARD_BG, padx=16, pady=10)
            p.pack(side="left", padx=(0, 8))
            tk.Label(p, text=val,   font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=col).pack()
            tk.Label(p, text=label, font=FONT_SMALL,               bg=CARD_BG, fg=TEXT_DIM).pack()

        if not overdue:
            tk.Label(self.table, text="✓  No overdue payments. All clear!",
                     font=FONT_TITLE, bg=DARK_BG, fg=SUCCESS).pack(pady=40)
            return

        COLS = [("Reference", 13), ("Tenant", 16), ("Email", 22), ("Unit", 7),
                ("City", 10), ("Due Date", 11), ("Amount", 11), ("Actions", 22)]
        col_headers(self.table, COLS)

        for pay in overdue:
            row = tk.Frame(self.table, bg=CARD_BG)
            row.pack(fill="x", padx=24)

            for val, w in [
                (pay.reference_number or "—",       13),
                (pay.tenant_name or "—",             16),
                (pay.tenant_email or "—",            22),
                (getattr(pay, "unit_number", "—"),    7),
                (getattr(pay, "city", "—"),           10),
                (pay.due_date or "—",                11),
                (f"£{pay.amount_due:,.2f}",          11),
            ]:
                color = DANGER if val == pay.status else TEXT
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=color,
                         width=w, anchor="w").pack(side="left", padx=4, pady=6)

            act = tk.Frame(row, bg=CARD_BG)
            act.pack(side="left", padx=4)
            mkbtn(act, "Notify",    lambda p=pay: self._notify(p),
                  color=WARNING, small=True).pack(side="left", padx=(0, 4))
            mkbtn(act, "Mark Paid", lambda p=pay: self._mark_paid(p),
                  color=SUCCESS, small=True).pack(side="left")

            divider(self.table)

    def _notify(self, pay):
        note = self.db.send_late_notification(pay.id)
        NotificationWindow(self, note)

    def _mark_paid(self, pay):
        MarkPaidDialog(self, pay, ["Bank Transfer", "Standing Order", "Card", "Cash"],
                       on_confirm=lambda m, d: self._do_pay(pay, m, d))

    def _do_pay(self, pay, method, paid_date):
        self.db.mark_payment_paid(pay.id, method, paid_date)
        messagebox.showinfo("Marked Paid", f"{pay.reference_number} marked as paid.")
        self._load()


# ═══════════════════════════════════════════════════════════════════
#  NOTIFICATION WINDOW — emulated late-payment email
# ═══════════════════════════════════════════════════════════════════

class NotificationWindow(tk.Toplevel):
    def __init__(self, parent, note: dict):
        super().__init__(parent)
        self.title("Late Payment Notification — Preview")
        self.geometry("560x440")
        self.configure(bg=DARK_BG)
        self._build(note)

    def _build(self, note):
        page_header(self, "Notification Preview",
                    "The following notification has been emulated (no real email sent).")

        card = tk.Frame(self, bg="white", padx=32, pady=28)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        tk.Label(card, text="📧  Late Payment Notice", font=("Segoe UI", 13, "bold"),
                 bg="white", fg=DANGER).pack(anchor="w")
        tk.Label(card, text="PropManage Property Services", font=FONT_SMALL,
                 bg="white", fg=TEXT_DIM).pack(anchor="w", pady=(2, 16))

        body = (
            f"Dear {note.get('tenant', 'Tenant')},\n\n"
            f"We write to inform you that a payment is outstanding on your tenancy "
            f"at Unit {note.get('unit', '—')}, {note.get('city', '—')}.\n\n"
            f"  Amount Outstanding: £{note.get('amount', 0):,.2f}\n"
            f"  Original Due Date:  {note.get('due', '—')}\n\n"
            f"Please arrange payment at your earliest convenience to avoid further action.\n"
            f"If you have already made payment, please disregard this notice.\n\n"
            f"Kind regards,\nPropManage Finance Team"
        )
        tk.Label(card, text=body, font=("Segoe UI", 10), bg="white", fg=TEXT,
                 justify="left", wraplength=460).pack(anchor="w")

        tk.Label(card, text=f"Sent at: {note.get('sent_at', '—')}", font=("Segoe UI", 8),
                 bg="white", fg=TEXT_DIM).pack(anchor="w", pady=(16, 0))

        mkbtn(self, "Close", self.destroy, color=TEXT_MUTED, small=True).pack(pady=(0, 8))


# ═══════════════════════════════════════════════════════════════════
#  REPORTS VIEW — occupancy, financial summary, maintenance costs
# ═══════════════════════════════════════════════════════════════════

class ReportsView(tk.Frame):
    def __init__(self, parent, staff, db):
        super().__init__(parent, bg=DARK_BG)
        self.staff = staff
        self.db = db
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Financial Reports",
                    "Occupancy, revenue, and maintenance cost analysis.")

        # Tab bar
        self._nb_style()
        nb = ttk.Notebook(self, style="R.TNotebook")
        nb.pack(fill="both", expand=True, padx=0)

        self._tab_financial(nb)
        self._tab_occupancy(nb)
        self._tab_revenue(nb)
        self._tab_maintenance(nb)

    def _nb_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("R.TNotebook", background=DARK_BG, borderwidth=0, tabmargins=0)
        s.configure("R.TNotebook.Tab", background=PANEL_BG, foreground=TEXT_DIM,
                    font=FONT_BODY, padding=[18, 8])
        s.map("R.TNotebook.Tab", background=[("selected", CARD_BG)],
              foreground=[("selected", TEXT)])

    def _tab(self, nb, title):
        f = tk.Frame(nb, bg=CARD_BG)
        nb.add(f, text=f"  {title}  ")
        return f

    # ── Financial Summary ─────────────────────────────────────────────────────
    def _tab_financial(self, nb):
        frame = self._tab(nb, "Financial Summary")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        # Location picker
        ctrl = tk.Frame(inner, bg=CARD_BG, padx=24, pady=14)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Location:", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        locs = self.db.get_all_locations()
        loc_labels = ["All Locations"] + [l.city for l in locs]
        self._fin_loc_v = tk.StringVar(value=
            next((l.city for l in locs if l.id == self.staff.location_id), "All Locations"))
        loc_map = {"All Locations": None, **{l.city: l.id for l in locs}}
        cb = ttk.Combobox(ctrl, textvariable=self._fin_loc_v, values=loc_labels,
                          font=FONT_BODY, width=20, state="readonly")
        cb.pack(side="left", padx=(6, 0))

        self._fin_frame = tk.Frame(inner, bg=CARD_BG)
        self._fin_frame.pack(fill="both", expand=True)

        def refresh(*_):
            loc_id = loc_map.get(self._fin_loc_v.get())
            self._render_financial(self._fin_frame, loc_id)

        cb.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def _render_financial(self, parent, location_id):
        for w in parent.winfo_children():
            w.destroy()

        s = self.db.get_financial_summary(location_id)

        sec_hdr(parent, "Revenue Overview")
        # Big KPI tiles
        kpi = tk.Frame(parent, bg=CARD_BG)
        kpi.pack(fill="x", padx=24, pady=(0, 16))
        for label, val, col, sub in [
            ("Total Billed",  f"£{s['total_billed']:,.0f}",   TEXT,    f"{s['total_invoices']} invoices"),
            ("Collected",     f"£{s['total_collected']:,.0f}", SUCCESS, f"{s['paid_count']} paid"),
            ("Pending",       f"£{s['pending']:,.0f}",         WARNING, f"{s['pending_count']} invoices"),
            ("Overdue",       f"£{s['overdue']:,.0f}",         DANGER,  f"{s['overdue_count']} invoices"),
            ("Maintenance",   f"£{s['maintenance_cost']:,.0f}",WARNING, "total spend"),
        ]:
            tile = tk.Frame(kpi, bg=PANEL_BG, padx=20, pady=16)
            tile.pack(side="left", padx=(0, 10))
            tk.Label(tile, text=val, font=("Segoe UI", 18, "bold"), bg=PANEL_BG, fg=col).pack()
            tk.Label(tile, text=label, font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack()
            tk.Label(tile, text=sub,   font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_MUTED).pack()

        sec_hdr(parent, "Collection Rate")
        bar_frame = tk.Frame(parent, bg=CARD_BG, padx=24, pady=8)
        bar_frame.pack(fill="x")
        rate = (s['total_collected'] / s['total_billed'] * 100) if s['total_billed'] else 0
        self._progress_bar(bar_frame, rate, f"{rate:.1f}% collected  (£{s['total_collected']:,.0f} of £{s['total_billed']:,.0f})")

        sec_hdr(parent, "Occupancy")
        occ_row = tk.Frame(parent, bg=CARD_BG, padx=24, pady=8)
        occ_row.pack(fill="x")
        self._progress_bar(occ_row, s['occupancy_rate'],
                           f"{s['occupancy_rate']:.1f}% occupied  ({s['occupied_apts']} of {s['total_apts']} units)",
                           color=ACCENT)

        sec_hdr(parent, "Revenue vs Expenses")
        net = s['total_collected'] - s['maintenance_cost']
        info_grid(parent, [
            ("Revenue Collected", f"£{s['total_collected']:,.2f}"),
            ("Maintenance Spend", f"£{s['maintenance_cost']:,.2f}"),
            ("Net",              f"£{net:,.2f}"),
        ], cols=3)

    def _progress_bar(self, parent, pct, label, color=SUCCESS):
        pct = max(0, min(100, pct))
        tk.Label(parent, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
        track = tk.Frame(parent, bg=PANEL_BG, height=14)
        track.pack(fill="x", pady=(4, 0))
        track.update_idletasks()
        # Draw bar via canvas
        canvas = tk.Canvas(parent, bg=PANEL_BG, height=14, highlightthickness=0)
        canvas.pack(fill="x")
        def draw(e, c=pct, col=color):
            w = canvas.winfo_width()
            canvas.delete("all")
            canvas.create_rectangle(0, 0, int(w * c / 100), 14, fill=col, outline="")
        canvas.bind("<Configure>", draw)

    # ── Occupancy Report ──────────────────────────────────────────────────────
    def _tab_occupancy(self, nb):
        frame = self._tab(nb, "Occupancy")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        sec_hdr(inner, "Occupancy by City")
        occ = self.db.get_occupancy_by_city()
        for row_data in occ:
            city = row_data["city"]
            total = row_data["total"] or 1
            occ_pct = row_data["occupied"] / total * 100

            city_card = tk.Frame(inner, bg=PANEL_BG, padx=20, pady=14)
            city_card.pack(fill="x", padx=24, pady=4)

            top = tk.Frame(city_card, bg=PANEL_BG)
            top.pack(fill="x")
            tk.Label(top, text=f"📍 {city}", font=FONT_SUB, bg=PANEL_BG, fg=TEXT).pack(side="left")
            tk.Label(top, text=f"{occ_pct:.0f}% occupied",
                     font=FONT_SMALL, bg=PANEL_BG, fg=sc("Active")).pack(side="right")

            stats = tk.Frame(city_card, bg=PANEL_BG)
            stats.pack(fill="x", pady=(6, 8))
            for label, val, col in [
                ("Total",       row_data["total"],       TEXT),
                ("Occupied",    row_data["occupied"],    ACCENT),
                ("Available",   row_data["available"],   SUCCESS),
                ("Maintenance", row_data["maintenance"], WARNING),
            ]:
                p = tk.Frame(stats, bg=CARD_BG, padx=12, pady=6)
                p.pack(side="left", padx=(0, 8))
                tk.Label(p, text=str(val),  font=("Segoe UI", 14, "bold"), bg=CARD_BG, fg=col).pack()
                tk.Label(p, text=label, font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack()

            # Mini occupancy bar
            bar_bg = tk.Canvas(city_card, bg=PANEL_BG, height=8, highlightthickness=0)
            bar_bg.pack(fill="x")
            def draw_bar(e, pct=occ_pct):
                w = bar_bg.winfo_width()
                bar_bg.delete("all")
                bar_bg.create_rectangle(0, 0, w, 8, fill=PANEL_BG, outline="")
                bar_bg.create_rectangle(0, 0, int(w * pct / 100), 8, fill=ACCENT, outline="")
            bar_bg.bind("<Configure>", draw_bar)

        sec_hdr(inner, "Apartment Detail by City")
        locs = self.db.get_all_locations()
        for loc in locs:
            apts = self.db.get_all_apartments(location_id=loc.id)
            if not apts: continue
            tk.Label(inner, text=f"  {loc.city}", font=FONT_SUB, bg=CARD_BG, fg=TEXT_DIM
                     ).pack(anchor="w", padx=24, pady=(12, 4))
            COLS = [("Unit", 8), ("Type", 12), ("Beds", 6), ("Rent", 10), ("Status", 14), ("Floor", 6)]
            col_headers(inner, COLS)
            for a in apts:
                row = tk.Frame(inner, bg=CARD_BG)
                row.pack(fill="x", padx=24)
                for val, w in [(a.unit_number, 8), (a.apartment_type, 12), (str(a.num_bedrooms), 6),
                               (f"£{a.monthly_rent:,.0f}", 10), (a.status, 14), (str(a.floor), 6)]:
                    col = sc(val) if val == a.status else TEXT
                    tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                             width=w, anchor="w").pack(side="left", padx=4, pady=4)
                divider(inner)

    # ── Revenue Chart ─────────────────────────────────────────────────────────
    def _tab_revenue(self, nb):
        frame = self._tab(nb, "Monthly Revenue")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        ctrl = tk.Frame(inner, bg=CARD_BG, padx=24, pady=14)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Location:", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        locs = self.db.get_all_locations()
        loc_labels = ["All Locations"] + [l.city for l in locs]
        self._rev_loc_v = tk.StringVar(value=
            next((l.city for l in locs if l.id == self.staff.location_id), "All Locations"))
        loc_map = {"All Locations": None, **{l.city: l.id for l in locs}}
        cb = ttk.Combobox(ctrl, textvariable=self._rev_loc_v, values=loc_labels,
                          font=FONT_BODY, width=18, state="readonly")
        cb.pack(side="left", padx=(6, 0))

        self._rev_frame = tk.Frame(inner, bg=CARD_BG)
        self._rev_frame.pack(fill="both", expand=True)

        def refresh(*_):
            loc_id = loc_map.get(self._rev_loc_v.get())
            self._render_revenue(self._rev_frame, loc_id)

        cb.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def _render_revenue(self, parent, location_id):
        for w in parent.winfo_children():
            w.destroy()

        data = self.db.get_monthly_revenue(location_id, months=12)
        if not data:
            tk.Label(parent, text="No revenue data.", font=FONT_BODY,
                     bg=CARD_BG, fg=TEXT_DIM).pack(pady=20)
            return

        sec_hdr(parent, "Monthly Collected Revenue  (last 12 months)")

        # Bar chart via canvas
        chart_frame = tk.Frame(parent, bg=CARD_BG, padx=24, pady=16)
        chart_frame.pack(fill="x")

        max_val = max(d["collected"] for d in data) if data else 1
        BAR_W   = 48
        GAP     = 12
        H       = 180
        total_w = len(data) * (BAR_W + GAP)

        canvas = tk.Canvas(chart_frame, bg=PANEL_BG, height=H + 60,
                           width=max(total_w + 40, 600), highlightthickness=0)
        canvas.pack(anchor="w")

        for i, d in enumerate(data):
            x = 24 + i * (BAR_W + GAP)
            bar_h = int((d["collected"] / max_val) * H) if max_val else 0
            y_top = H - bar_h + 10

            # Bar
            canvas.create_rectangle(x, y_top, x + BAR_W, H + 10,
                                     fill=ACCENT, outline="")
            # Value label
            canvas.create_text(x + BAR_W // 2, y_top - 6,
                                text=f"£{d['collected']:,.0f}",
                                fill=TEXT, font=("Segoe UI", 7), anchor="s")
            # Month label
            month_short = d["month"][5:] if d["month"] else "—"
            canvas.create_text(x + BAR_W // 2, H + 20,
                                text=month_short, fill=TEXT_DIM,
                                font=("Segoe UI", 8), anchor="n")

        # Table below chart
        sec_hdr(parent, "Data Table")
        COLS = [("Month", 10), ("Collected", 14), ("vs Previous", 14)]
        col_headers(parent, COLS)
        prev = None
        for d in data:
            row = tk.Frame(parent, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            diff = ""
            diff_col = TEXT
            if prev is not None:
                delta = d["collected"] - prev
                diff = f"{'▲' if delta >= 0 else '▼'} £{abs(delta):,.0f}"
                diff_col = SUCCESS if delta >= 0 else DANGER
            for val, w, col in [(d["month"] or "—", 10, TEXT),
                                  (f"£{d['collected']:,.2f}", 14, SUCCESS),
                                  (diff, 14, diff_col)]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=col,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            divider(parent)
            prev = d["collected"]

    # ── Maintenance Cost ──────────────────────────────────────────────────────
    def _tab_maintenance(self, nb):
        frame = self._tab(nb, "Maintenance Costs")
        outer, inner = scrollable(frame, CARD_BG)
        outer.pack(fill="both", expand=True)

        ctrl = tk.Frame(inner, bg=CARD_BG, padx=24, pady=14)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Location:", font=FONT_SMALL, bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
        locs = self.db.get_all_locations()
        loc_labels = ["All Locations"] + [l.city for l in locs]
        self._mc_loc_v = tk.StringVar(value=
            next((l.city for l in locs if l.id == self.staff.location_id), "All Locations"))
        loc_map = {"All Locations": None, **{l.city: l.id for l in locs}}
        cb = ttk.Combobox(ctrl, textvariable=self._mc_loc_v, values=loc_labels,
                          font=FONT_BODY, width=18, state="readonly")
        cb.pack(side="left", padx=(6, 0))

        self._mc_frame = tk.Frame(inner, bg=CARD_BG)
        self._mc_frame.pack(fill="both", expand=True)

        def refresh(*_):
            loc_id = loc_map.get(self._mc_loc_v.get())
            self._render_maintenance(self._mc_frame, loc_id)

        cb.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def _render_maintenance(self, parent, location_id):
        for w in parent.winfo_children():
            w.destroy()

        data = self.db.get_maintenance_cost_report(location_id)
        total = sum(d["total_cost"] for d in data)

        sec_hdr(parent, f"Maintenance Costs by Category  (Total: £{total:,.2f})")

        if not data:
            tk.Label(parent, text="No maintenance data.", font=FONT_BODY,
                     bg=CARD_BG, fg=TEXT_DIM).pack(padx=28, pady=12, anchor="w")
            return

        COLS = [("Category", 16), ("Jobs", 6), ("Total Cost", 13), ("Avg Cost", 12),
                ("Hours", 8), ("% of Budget", 14)]
        col_headers(parent, COLS)

        for d in data:
            pct = (d["total_cost"] / total * 100) if total else 0
            row = tk.Frame(parent, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            for val, w in [
                (d["category"] or "—",       16),
                (str(d["count"]),              6),
                (f"£{d['total_cost']:,.2f}",  13),
                (f"£{d['avg_cost']:,.2f}",    12),
                (f"{d['total_hours']:.1f}h",   8),
                (f"{pct:.1f}%",               14),
            ]:
                tk.Label(row, text=val, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         width=w, anchor="w").pack(side="left", padx=4, pady=5)
            divider(parent)

        # Cost by city breakdown
        sec_hdr(parent, "Cost by City")
        for loc in self.db.get_all_locations():
            city_data = self.db.get_maintenance_cost_report(loc.id)
            city_total = sum(d["total_cost"] for d in city_data)
            row = tk.Frame(parent, bg=CARD_BG)
            row.pack(fill="x", padx=24)
            tk.Label(row, text=f"📍 {loc.city}", font=FONT_BODY, bg=CARD_BG,
                     fg=TEXT, width=16, anchor="w").pack(side="left", padx=4, pady=5)
            tk.Label(row, text=f"£{city_total:,.2f}", font=FONT_SUB, bg=CARD_BG,
                     fg=WARNING, width=14, anchor="w").pack(side="left", padx=4)
            count = sum(d["count"] for d in city_data)
            tk.Label(row, text=f"{count} jobs", font=FONT_SMALL, bg=CARD_BG,
                     fg=TEXT_DIM).pack(side="left", padx=4)
            divider(parent)