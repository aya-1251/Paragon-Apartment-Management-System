"""
Main entry point for the Property Management System.
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db_manager import DatabaseManager
from views import LoginView, AppShell


class PropertyManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PropManage — Property Management System")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(bg="#0F1117")
        self._apply_styles()
        db_path = os.path.join(os.path.dirname(__file__), "property_management.db")
        self.db = DatabaseManager(db_path)
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1280) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"1280x800+{x}+{y}")
        self.show_login()

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScrollbar", troughcolor="#F3F4F6", background="#D1D5DB",
                        bordercolor="#F3F4F6", arrowcolor="#6B7280")
        style.configure("Vertical.TScrollbar", troughcolor="#F3F4F6", background="#D1D5DB")
        style.configure("TCombobox", fieldbackground="#F9FAFB", background="#FFFFFF",
                        foreground="#111827", selectbackground="#DBEAFE",
                        selectforeground="#1D4ED8", bordercolor="#E5E7EB")
        style.map("TCombobox", fieldbackground=[("readonly", "#F9FAFB")])

    def show_login(self):
        for w in self.winfo_children():
            w.destroy()
        LoginView(self, on_login=self._handle_login)

    def _handle_login(self, username: str, password: str):
        staff = self.db.authenticate_staff(username, password)
        if staff:
            self._launch_app(staff)
        else:
            for w in self.winfo_children():
                if isinstance(w, LoginView):
                    w.show_error("Invalid username or password.")

    def _launch_app(self, staff):
        for w in self.winfo_children():
            w.destroy()
        if staff.role == "Finance Manager":
            from views.views_finance import FinanceAppShell
            FinanceAppShell(self, staff, self.db)
        elif staff.role == "Maintenance Staff":
            from views.views_maintenance import MaintenanceAppShell
            MaintenanceAppShell(self, staff, self.db)
        elif staff.role == "Administrator":
            from views.views_admin import AdminAppShell
            AdminAppShell(self, staff, self.db)
        elif staff.role == "Manager":
            from views.views_manager import ManagerAppShell
            ManagerAppShell(self, staff, self.db)
        else:
            AppShell(self, staff, self.db)

    def on_closing(self):
        if self.db:
            self.db.close()
        self.destroy()


def main():
    app = PropertyManagementApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()