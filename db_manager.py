"""
Database Manager for the Property Management System.
Handles all SQLite operations using OOP principles.
"""
import sqlite3
import hashlib
import os
from datetime import datetime, date
from typing import Optional, List, Tuple, Any
from models import (
    Location, Apartment, Tenant, Lease, Payment,
    MaintenanceRequest, Complaint, Staff,
    ApartmentStatus, LeaseStatus, PaymentStatus
)


class DatabaseManager:
    """Manages all database operations for the property management system."""

    def __init__(self, db_path: str = "property_management.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.initialize_schema()
        self.seed_demo_data()

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def get_cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()

    # ─────────────────────────── SCHEMA ────────────────────────────

    def initialize_schema(self):
        cursor = self.get_cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                address TEXT NOT NULL,
                postcode TEXT NOT NULL,
                country TEXT DEFAULT 'UK'
            );

            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                location_id INTEGER REFERENCES locations(id),
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS apartments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_number TEXT NOT NULL,
                location_id INTEGER NOT NULL REFERENCES locations(id),
                apartment_type TEXT NOT NULL,
                num_bedrooms INTEGER DEFAULT 1,
                num_bathrooms INTEGER DEFAULT 1,
                monthly_rent REAL NOT NULL,
                floor INTEGER DEFAULT 0,
                size_sqft REAL,
                furnished INTEGER DEFAULT 0,
                parking INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Available',
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ni_number TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                occupation TEXT,
                date_of_birth TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                reference1_name TEXT,
                reference1_phone TEXT,
                reference1_email TEXT,
                reference2_name TEXT,
                reference2_phone TEXT,
                reference2_email TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS leases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                apartment_id INTEGER NOT NULL REFERENCES apartments(id),
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                monthly_rent REAL NOT NULL,
                deposit_amount REAL NOT NULL,
                status TEXT DEFAULT 'Active',
                early_termination_requested INTEGER DEFAULT 0,
                early_termination_date TEXT,
                notice_given_date TEXT,
                created_by INTEGER REFERENCES staff(id),
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lease_id INTEGER NOT NULL REFERENCES leases(id),
                amount_due REAL NOT NULL,
                amount_paid REAL DEFAULT 0,
                due_date TEXT NOT NULL,
                paid_date TEXT,
                status TEXT DEFAULT 'Pending',
                payment_method TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS maintenance_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lease_id INTEGER REFERENCES leases(id),
                apartment_id INTEGER REFERENCES apartments(id),
                tenant_id INTEGER REFERENCES tenants(id),
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                reported_date TEXT DEFAULT (date('now')),
                scheduled_date TEXT,
                resolved_date TEXT,
                resolution_notes TEXT,
                cost REAL DEFAULT 0,
                time_taken_hours REAL DEFAULT 0,
                assigned_staff_id INTEGER REFERENCES staff(id),
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lease_id INTEGER REFERENCES leases(id),
                tenant_id INTEGER REFERENCES tenants(id),
                apartment_id INTEGER REFERENCES apartments(id),
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                status TEXT DEFAULT 'Open',
                reported_date TEXT DEFAULT (date('now')),
                resolved_date TEXT,
                resolution_notes TEXT,
                created_by INTEGER REFERENCES staff(id),
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                specialties TEXT,
                hourly_rate REAL DEFAULT 0,
                location_id INTEGER REFERENCES locations(id),
                availability TEXT DEFAULT 'Available',
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS maintenance_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                typical_cost_min REAL DEFAULT 0,
                typical_cost_max REAL DEFAULT 0,
                typical_hours REAL DEFAULT 1,
                required_specialty TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS worker_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maintenance_id INTEGER NOT NULL REFERENCES maintenance_requests(id),
                worker_id INTEGER NOT NULL REFERENCES workers(id),
                assigned_date TEXT DEFAULT (date('now')),
                assigned_by INTEGER REFERENCES staff(id),
                notes TEXT
            );
        """)
        self.commit()

    # ─────────────────────────── SEED DATA ─────────────────────────

    def seed_demo_data(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM locations")
        if cursor.fetchone()[0] > 0:
            return  # Already seeded

        # ── Locations: Bristol=1, Cardiff=2, London=3, Manchester=4 ──────────
        cursor.executemany("INSERT INTO locations (city, address, postcode) VALUES (?,?,?)", [
            ("Bristol",    "8 Harbourside Place",  "BS1 5TR"),
            ("Cardiff",    "22 Cardiff Bay Road",  "CF10 4PA"),
            ("London",     "101 Canary Wharf Lane","E14 5AB"),
            ("Manchester", "45 Oxford Road",       "M1 2HB"),
        ])
        self.commit()

        # ── Staff (password: password123) ────────────────────────────────────
        # Each account gets its own unique salt via _make_password_hash.
        _p = "password123"
        staff_data = [
            # Front Desk — one per city
            ("frontdesk1", self._make_password_hash(_p), "Alice",   "Johnson",  "Front Desk",       "alice@property.com",   "07700111111", 1),
            ("frontdesk2", self._make_password_hash(_p), "Bob",     "Smith",    "Front Desk",       "bob@property.com",     "07700222222", 4),
            ("frontdesk3", self._make_password_hash(_p), "Priya",   "Patel",    "Front Desk",       "priya@property.com",   "07700223344", 3),
            ("frontdesk4", self._make_password_hash(_p), "Gareth",  "Hughes",   "Front Desk",       "gareth@property.com",  "07700334455", 2),
            # Finance Managers — one per city
            ("finance1",   self._make_password_hash(_p), "David",   "Brown",    "Finance Manager",  "david@property.com",   "07700444444", 1),
            ("finance2",   self._make_password_hash(_p), "Sophie",  "Chen",     "Finance Manager",  "sophie@property.com",  "07700444445", 2),
            ("finance3",   self._make_password_hash(_p), "Marcus",  "Webb",     "Finance Manager",  "marcus@property.com",  "07700444446", 3),
            ("finance4",   self._make_password_hash(_p), "Nadia",   "Okonkwo",  "Finance Manager",  "nadia@property.com",   "07700444447", 4),
            # Administrators — one per city
            ("admin1",     self._make_password_hash(_p), "Carol",   "Williams", "Administrator",    "carol@property.com",   "07700333333", 1),
            ("admin2",     self._make_password_hash(_p), "Owen",    "Davies",   "Administrator",    "owen@property.com",    "07700333334", 2),
            ("admin3",     self._make_password_hash(_p), "Nina",    "Shah",     "Administrator",    "nina@property.com",    "07700333335", 3),
            ("admin4",     self._make_password_hash(_p), "Ryan",    "Fletcher", "Administrator",    "ryan@property.com",    "07700333336", 4),
            # Maintenance Staff — one per city
            ("maint1",     self._make_password_hash(_p), "Eve",     "Davis",    "Maintenance Staff","eve@property.com",     "07700555555", 1),
            ("maint2",     self._make_password_hash(_p), "Rhys",    "Morgan",   "Maintenance Staff","rhys@property.com",    "07700555556", 2),
            ("maint3",     self._make_password_hash(_p), "Aisha",   "Nwosu",    "Maintenance Staff","aisha@property.com",   "07700555557", 3),
            ("maint4",     self._make_password_hash(_p), "Callum",  "Reid",     "Maintenance Staff","callum@property.com",  "07700555558", 4),
            # Manager
            ("manager1",   self._make_password_hash(_p), "Frank",   "Miller",   "Manager",          "frank@property.com",   "07700666666", 1),
        ]
        cursor.executemany(
            "INSERT INTO staff (username,password_hash,first_name,last_name,role,email,phone,location_id) VALUES (?,?,?,?,?,?,?,?)",
            staff_data)
        self.commit()

        # ── Apartments ───────────────────────────────────────────────────────
        # (unit, loc, type, beds, baths, rent, floor, sqft, furnished, parking, status, desc)
        apartments = [
            # Bristol (loc 1)
            ("BR101", 1, "Studio",     0, 1,  795.0, 1,  420.0, 0, 0, "Occupied",           "Compact studio, harbour views"),
            ("BR102", 1, "Flat",       1, 1,  975.0, 2,  560.0, 1, 0, "Occupied",           "Modern 1-bed, furnished"),
            ("BR103", 1, "Flat",       2, 1, 1250.0, 3,  740.0, 1, 1, "Available",          "Spacious 2-bed with parking"),
            ("BR104", 1, "Maisonette", 3, 2, 1650.0, 0, 1100.0, 0, 1, "Occupied",           "3-bed maisonette with garden"),
            ("BR105", 1, "Flat",       1, 1,  920.0, 1,  540.0, 0, 0, "Under Maintenance",  "1-bed refurb in progress"),
            # Cardiff (loc 2)
            ("CF201", 2, "Studio",     0, 1,  695.0, 1,  400.0, 0, 0, "Available",          "Budget studio, bay area"),
            ("CF202", 2, "Flat",       1, 1,  870.0, 2,  510.0, 1, 0, "Occupied",           "1-bed furnished flat"),
            ("CF203", 2, "Flat",       2, 1, 1100.0, 2,  680.0, 0, 1, "Occupied",           "2-bed with parking, quiet street"),
            ("CF204", 2, "Flat",       3, 2, 1450.0, 4,  900.0, 1, 1, "Available",          "Top floor 3-bed, city views"),
            # London (loc 3)
            ("LN301", 3, "Studio",     0, 1, 1450.0, 5,  380.0, 1, 0, "Occupied",           "Premium studio, Canary Wharf"),
            ("LN302", 3, "Flat",       1, 1, 1900.0, 8,  520.0, 1, 0, "Occupied",           "1-bed, high floor, river views"),
            ("LN303", 3, "Flat",       2, 2, 2600.0,10,  780.0, 1, 1, "Available",          "Luxury 2-bed, concierge"),
            ("LN304", 3, "Penthouse",  3, 2, 4200.0,15, 1400.0, 1, 2, "Occupied",           "Penthouse with roof terrace"),
            # Manchester (loc 4)
            ("MN401", 4, "Studio",     0, 1,  720.0, 1,  410.0, 0, 0, "Available",          "Studio near Piccadilly"),
            ("MN402", 4, "Flat",       1, 1,  950.0, 2,  570.0, 1, 0, "Occupied",           "1-bed, modern build"),
            ("MN403", 4, "Flat",       2, 1, 1150.0, 3,  720.0, 1, 1, "Occupied",           "2-bed with parking"),
            ("MN404", 4, "Maisonette", 3, 2, 1550.0, 0, 1050.0, 0, 1, "Available",          "3-bed maisonette, MediaCity"),
        ]
        cursor.executemany(
            "INSERT INTO apartments (unit_number,location_id,apartment_type,num_bedrooms,num_bathrooms,"
            "monthly_rent,floor,size_sqft,furnished,parking,status,description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            apartments)
        self.commit()

        # ── Tenants ──────────────────────────────────────────────────────────
        # (ni, first, last, phone, email, occupation, dob, ec_name, ec_phone, r1n, r1p, r1e, r2n, r2p, r2e, notes)
        tenants = [
            ("NI100001A","James",   "Taylor",  "07811100001","james.taylor@email.com",  "Engineer",      "1988-04-15","Sarah Taylor",   "07811100010","Mark Brown",  "07811100020","mark@ref.com",   "","","","Long-term preferred"),
            ("NI100002B","Lucy",    "Harris",  "07811200001","lucy.harris@email.com",   "Teacher",       "1993-07-22","Tom Harris",     "07811200010","Anna White",  "07811200020","anna@ref.com",   "","","","Excellent references"),
            ("NI100003C","Mohammed","Al-Amin", "07811300001","m.alamin@email.com",      "Accountant",    "1985-11-03","Fatima Al-Amin", "07811300010","Tariq Said",  "07811300020","tariq@ref.com",  "","","","Reliable, never late"),
            ("NI100004D","Elena",   "Popescu", "07811400001","elena.p@email.com",       "Nurse",         "1990-06-17","Ion Popescu",    "07811400010","Ioana Marin", "07811400020","ioana@ref.com",  "","","",""),
            ("NI100005E","Kwame",   "Asante",  "07811500001","k.asante@email.com",      "Software Dev",  "1995-02-28","Ama Asante",     "07811500010","Samuel Osei", "07811500020","samuel@ref.com", "","","","Young professional"),
            ("NI100006F","Chloe",   "Bernstein","07811600001","chloe.b@email.com",      "Solicitor",     "1987-09-12","Paul Bernstein", "07811600010","Ruth Klein",  "07811600020","ruth@ref.com",   "","","","High-earner, reliable"),
            ("NI100007G","Yusuf",   "Karimi",  "07811700001","y.karimi@email.com",      "Architect",     "1991-03-05","Maryam Karimi",  "07811700010","Ali Hassan",  "07811700020","ali@ref.com",    "","","",""),
            ("NI100008H","Sandra",  "O'Brien", "07811800001","sandra.ob@email.com",     "Marketing Mgr", "1984-12-30","Patrick O'Brien","07811800010","Siobhan Ryan","07811800020","siob@ref.com",   "","","","Long-term tenant"),
        ]
        cursor.executemany(
            "INSERT INTO tenants (ni_number,first_name,last_name,phone,email,occupation,date_of_birth,"
            "emergency_contact_name,emergency_contact_phone,reference1_name,reference1_phone,reference1_email,"
            "reference2_name,reference2_phone,reference2_email,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            tenants)
        self.commit()

        # ── Leases ───────────────────────────────────────────────────────────
        # (tenant_id, apartment_id, start, end, rent, deposit, status, created_by_staff_id)
        leases = [
            (1, 1,  "2024-03-01", "2025-02-28", 795.0,  1590.0, "Active", 1),   # James → BR101
            (2, 2,  "2024-05-01", "2025-04-30", 975.0,  1950.0, "Active", 1),   # Lucy  → BR102
            (3, 4,  "2023-09-01", "2024-08-31", 1650.0, 3300.0, "Expired",1),   # Mohammed → BR104 (expired)
            (3, 4,  "2024-09-01", "2025-08-31", 1650.0, 3300.0, "Active", 1),   # Mohammed renewed
            (4, 7,  "2024-01-01", "2024-12-31", 870.0,  1740.0, "Active", 4),   # Elena → CF202
            (5, 8,  "2024-04-01", "2025-03-31", 1100.0, 2200.0, "Active", 4),   # Kwame → CF203
            (6, 10, "2024-02-01", "2025-01-31", 1450.0, 2900.0, "Active", 3),   # Chloe → LN301
            (7, 11, "2024-06-01", "2025-05-31", 1900.0, 3800.0, "Active", 3),   # Yusuf → LN302
            (8, 13, "2023-07-01", "2025-06-30", 4200.0, 8400.0, "Active", 3),   # Sandra → LN304
            (1, 15, "2024-07-01", "2025-06-30", 950.0,  1900.0, "Active", 2),   # James also MN402
            (5, 16, "2024-10-01", "2025-09-30", 1150.0, 2300.0, "Active", 2),   # Kwame → MN403
        ]
        for l in leases:
            cursor.execute(
                "INSERT INTO leases (tenant_id,apartment_id,start_date,end_date,monthly_rent,deposit_amount,status,created_by) VALUES (?,?,?,?,?,?,?,?)", l)
        self.commit()

        # ── Payments — rich history (paid, pending, overdue) ─────────────────
        # Helper: insert payment
        def pay(lease_id, due, amount_due, paid=None, status="Paid", method="Bank Transfer", ref=None):
            ref = ref or f"REF-{lease_id:02d}-{due.replace('-','')}"
            amt_paid = amount_due if status == "Paid" else 0.0
            paid_date = paid if status == "Paid" else None
            cursor.execute(
                "INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,paid_date,status,payment_method,reference_number) VALUES (?,?,?,?,?,?,?,?)",
                (lease_id, amount_due, amt_paid, due, paid_date, status, method if status=="Paid" else "", ref))

        # Lease 1 – James/BR101 – 795/mo, mostly paid, one overdue
        pay(1, "2024-03-01", 795.0,  "2024-03-03")
        pay(1, "2024-04-01", 795.0,  "2024-04-02")
        pay(1, "2024-05-01", 795.0,  "2024-05-04")
        pay(1, "2024-06-01", 795.0,  "2024-06-01")
        pay(1, "2024-07-01", 795.0,  "2024-07-03")
        pay(1, "2024-08-01", 795.0,  "2024-08-02")
        pay(1, "2024-09-01", 795.0,  "2024-09-03")
        pay(1, "2024-10-01", 795.0,  "2024-10-01")
        pay(1, "2024-11-01", 795.0,  "2024-11-04")
        pay(1, "2024-12-01", 795.0,  "2024-12-02")
        pay(1, "2025-01-01", 795.0,  None, status="Overdue")
        pay(1, "2025-02-01", 795.0,  None, status="Pending")

        # Lease 2 – Lucy/BR102 – 975/mo, all paid
        pay(2, "2024-05-01", 975.0,  "2024-05-02")
        pay(2, "2024-06-01", 975.0,  "2024-06-01")
        pay(2, "2024-07-01", 975.0,  "2024-07-03")
        pay(2, "2024-08-01", 975.0,  "2024-08-02")
        pay(2, "2024-09-01", 975.0,  "2024-09-01")
        pay(2, "2024-10-01", 975.0,  "2024-10-04")
        pay(2, "2024-11-01", 975.0,  "2024-11-03")
        pay(2, "2024-12-01", 975.0,  "2024-12-02")
        pay(2, "2025-01-01", 975.0,  "2025-01-03")
        pay(2, "2025-02-01", 975.0,  None, status="Pending")

        # Lease 3 – Mohammed/BR104 expired – 1650/mo paid
        pay(3, "2023-09-01", 1650.0, "2023-09-02")
        pay(3, "2023-10-01", 1650.0, "2023-10-01")
        pay(3, "2023-11-01", 1650.0, "2023-11-03")
        pay(3, "2023-12-01", 1650.0, "2023-12-02")
        pay(3, "2024-01-01", 1650.0, "2024-01-04")
        pay(3, "2024-02-01", 1650.0, "2024-02-02")
        pay(3, "2024-03-01", 1650.0, "2024-03-01")
        pay(3, "2024-04-01", 1650.0, "2024-04-03")
        pay(3, "2024-05-01", 1650.0, "2024-05-02")
        pay(3, "2024-06-01", 1650.0, "2024-06-01")
        pay(3, "2024-07-01", 1650.0, "2024-07-04")
        pay(3, "2024-08-01", 1650.0, "2024-08-02")

        # Lease 4 – Mohammed renewed – 1650/mo, one overdue
        pay(4, "2024-09-01", 1650.0, "2024-09-03")
        pay(4, "2024-10-01", 1650.0, "2024-10-02")
        pay(4, "2024-11-01", 1650.0, "2024-11-04")
        pay(4, "2024-12-01", 1650.0, "2024-12-03")
        pay(4, "2025-01-01", 1650.0, None, status="Overdue")
        pay(4, "2025-02-01", 1650.0, None, status="Pending")

        # Lease 5 – Elena/CF202 – 870/mo, late payer
        pay(5, "2024-01-01", 870.0,  "2024-01-10")  # paid late
        pay(5, "2024-02-01", 870.0,  "2024-02-12")
        pay(5, "2024-03-01", 870.0,  "2024-03-08")
        pay(5, "2024-04-01", 870.0,  "2024-04-15")
        pay(5, "2024-05-01", 870.0,  "2024-05-09")
        pay(5, "2024-06-01", 870.0,  "2024-06-11")
        pay(5, "2024-07-01", 870.0,  "2024-07-07")
        pay(5, "2024-08-01", 870.0,  "2024-08-13")
        pay(5, "2024-09-01", 870.0,  "2024-09-10")
        pay(5, "2024-10-01", 870.0,  "2024-10-14")
        pay(5, "2024-11-01", 870.0,  "2024-11-12")
        pay(5, "2024-12-01", 870.0,  None, status="Overdue")

        # Lease 6 – Kwame/CF203 – 1100/mo
        pay(6, "2024-04-01", 1100.0, "2024-04-02")
        pay(6, "2024-05-01", 1100.0, "2024-05-01")
        pay(6, "2024-06-01", 1100.0, "2024-06-03")
        pay(6, "2024-07-01", 1100.0, "2024-07-02")
        pay(6, "2024-08-01", 1100.0, "2024-08-01")
        pay(6, "2024-09-01", 1100.0, "2024-09-04")
        pay(6, "2024-10-01", 1100.0, "2024-10-01")
        pay(6, "2024-11-01", 1100.0, "2024-11-03")
        pay(6, "2024-12-01", 1100.0, "2024-12-02")
        pay(6, "2025-01-01", 1100.0, "2025-01-03")
        pay(6, "2025-02-01", 1100.0, None, status="Pending")

        # Lease 7 – Chloe/LN301 – 1450/mo
        pay(7, "2024-02-01", 1450.0, "2024-02-02")
        pay(7, "2024-03-01", 1450.0, "2024-03-01")
        pay(7, "2024-04-01", 1450.0, "2024-04-03")
        pay(7, "2024-05-01", 1450.0, "2024-05-02")
        pay(7, "2024-06-01", 1450.0, "2024-06-01")
        pay(7, "2024-07-01", 1450.0, "2024-07-04")
        pay(7, "2024-08-01", 1450.0, "2024-08-02")
        pay(7, "2024-09-01", 1450.0, "2024-09-01")
        pay(7, "2024-10-01", 1450.0, "2024-10-03")
        pay(7, "2024-11-01", 1450.0, "2024-11-02")
        pay(7, "2024-12-01", 1450.0, "2024-12-01")
        pay(7, "2025-01-01", 1450.0, None, status="Overdue")

        # Lease 8 – Yusuf/LN302 – 1900/mo
        pay(8, "2024-06-01", 1900.0, "2024-06-02")
        pay(8, "2024-07-01", 1900.0, "2024-07-01")
        pay(8, "2024-08-01", 1900.0, "2024-08-03")
        pay(8, "2024-09-01", 1900.0, "2024-09-02")
        pay(8, "2024-10-01", 1900.0, "2024-10-01")
        pay(8, "2024-11-01", 1900.0, "2024-11-04")
        pay(8, "2024-12-01", 1900.0, "2024-12-03")
        pay(8, "2025-01-01", 1900.0, "2025-01-02")
        pay(8, "2025-02-01", 1900.0, None, status="Pending")

        # Lease 9 – Sandra/LN304 – 4200/mo penthouse
        pay(9, "2023-07-01", 4200.0, "2023-07-01")
        pay(9, "2023-08-01", 4200.0, "2023-08-02")
        pay(9, "2023-09-01", 4200.0, "2023-09-01")
        pay(9, "2023-10-01", 4200.0, "2023-10-03")
        pay(9, "2023-11-01", 4200.0, "2023-11-02")
        pay(9, "2023-12-01", 4200.0, "2023-12-01")
        pay(9, "2024-01-01", 4200.0, "2024-01-02")
        pay(9, "2024-02-01", 4200.0, "2024-02-01")
        pay(9, "2024-03-01", 4200.0, "2024-03-03")
        pay(9, "2024-04-01", 4200.0, "2024-04-02")
        pay(9, "2024-05-01", 4200.0, "2024-05-01")
        pay(9, "2024-06-01", 4200.0, "2024-06-04")
        pay(9, "2024-07-01", 4200.0, "2024-07-03")
        pay(9, "2024-08-01", 4200.0, "2024-08-02")
        pay(9, "2024-09-01", 4200.0, "2024-09-01")
        pay(9, "2024-10-01", 4200.0, "2024-10-03")
        pay(9, "2024-11-01", 4200.0, "2024-11-01")
        pay(9, "2024-12-01", 4200.0, "2024-12-02")
        pay(9, "2025-01-01", 4200.0, "2025-01-03")
        pay(9, "2025-02-01", 4200.0, None, status="Pending")

        # Lease 10 – James/MN402 – 950/mo
        pay(10, "2024-07-01", 950.0, "2024-07-02")
        pay(10, "2024-08-01", 950.0, "2024-08-01")
        pay(10, "2024-09-01", 950.0, "2024-09-03")
        pay(10, "2024-10-01", 950.0, "2024-10-02")
        pay(10, "2024-11-01", 950.0, "2024-11-04")
        pay(10, "2024-12-01", 950.0, "2024-12-03")
        pay(10, "2025-01-01", 950.0, None, status="Pending")

        # Lease 11 – Kwame/MN403 – 1150/mo
        pay(11, "2024-10-01", 1150.0, "2024-10-02")
        pay(11, "2024-11-01", 1150.0, "2024-11-01")
        pay(11, "2024-12-01", 1150.0, "2024-12-03")
        pay(11, "2025-01-01", 1150.0, None, status="Overdue")
        pay(11, "2025-02-01", 1150.0, None, status="Pending")

        self.commit()

        # ── Maintenance with costs ────────────────────────────────────────────
        maintenance = [
            (1, 1, 1, "Leaking tap in kitchen",       "Dripping for 2 days.",             "Plumbing",    "Medium", "Resolved","2024-11-10","2024-11-12","2024-11-13","Tap washer replaced.",      85.0,  2.0),
            (4, 4, 3, "Boiler service required",       "Annual boiler service due.",        "Heating",     "High",   "Resolved","2024-10-05","2024-10-08","2024-10-09","Service completed, cert issued.",200.0, 3.5),
            (6, 8, 5, "Window latch broken",           "Bedroom window won't close fully.", "General",     "Low",    "Resolved","2024-12-01","2024-12-05","2024-12-06","New latch fitted.",         45.0,  1.0),
            (7, 10, 6,"AC unit not cooling",           "AC ineffective in summer.",         "HVAC",        "High",   "Open",    "2025-01-15", None,         None,        "",                        0.0,   0.0),
            (9, 13, 8,"Roof terrace drainage blocked", "Water pooling after rain.",         "Drainage",    "Urgent", "In Progress","2025-01-20","2025-01-22",None,       "Contractors booked.",     320.0, 0.0),
            (2, 2, 2, "Front door intercom faulty",    "Intercom crackles intermittently.", "Electrical",  "Low",    "Resolved","2024-09-18","2024-09-22","2024-09-23","New intercom panel fitted.", 130.0, 2.5),
            (None,5,None,"Flat BR105 full refurb",     "Complete refurbishment pre-letting.","Renovation",  "High",   "In Progress","2024-12-01",None,       None,        "",                       2400.0,0.0),
        ]
        for m in maintenance:
            cursor.execute("""
                INSERT INTO maintenance_requests (lease_id,apartment_id,tenant_id,title,description,category,
                priority,status,reported_date,scheduled_date,resolved_date,resolution_notes,cost,time_taken_hours)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", m)
        self.commit()

        # ── Complaints ────────────────────────────────────────────────────────
        complaints = [
            (1, 1, 1, "Noisy neighbours",           "Loud music after midnight from floor above.","Noise",           "Open",   "2025-01-08", None, "", 1),
            (5, 4, 7, "Heating unresponsive",        "Radiators cold despite thermostat on.",      "Maintenance",      "Resolved","2024-10-06","2024-10-10","Boiler serviced, issue resolved.",4),
            (7, 6, 10,"Parking space dispute",       "Neighbour using my assigned bay.",            "Parking",          "Open",   "2025-01-18", None, "", 3),
            (9, 8, 13,"Noise from building works",   "Construction noise 7am weekdays.",            "Noise",            "Under Review","2025-01-10",None,"Liaising with contractors.",3),
        ]
        for c in complaints:
            cursor.execute("""
                INSERT INTO complaints (lease_id,tenant_id,apartment_id,title,description,category,status,
                reported_date,resolved_date,resolution_notes,created_by) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", c)
        self.commit()

        # ── Workers (field operatives, per city) ──────────────────────────────
        # (first, last, phone, email, specialties, hourly_rate, location_id, availability, notes)
        workers = [
            # Bristol (loc 1)
            ("Tom",     "Hargreaves", "07811900001","tom.h@workers.com",   "Plumbing,Drainage",          28.0, 1, "Available",  "Licensed plumber, 10yrs exp"),
            ("Derek",   "Simmons",    "07811900002","derek.s@workers.com", "Electrical,General",         32.0, 1, "Available",  "Part P certified"),
            ("Barry",   "Frost",      "07811900003","barry.f@workers.com", "Heating,HVAC",               35.0, 1, "Busy",       "Gas Safe registered"),
            ("Sharon",  "Okafor",     "07811900004","sharon.o@workers.com","Renovation,General,Painting", 25.0, 1, "Available",  "Skilled decorator"),
            # Cardiff (loc 2)
            ("Ieuan",   "Griffiths",  "07811900011","ieuan.g@workers.com", "Plumbing,Heating",           27.0, 2, "Available",  "Gas Safe registered"),
            ("Ceri",    "Walters",    "07811900012","ceri.w@workers.com",  "Electrical,General",         30.0, 2, "On Leave",   "Available from next week"),
            ("Dylan",   "Price",      "07811900013","dylan.p@workers.com", "Renovation,Drainage",        26.0, 2, "Available",  "Multi-trade"),
            # London (loc 3)
            ("Jerome",  "Bailey",     "07811900021","jerome.b@workers.com","Electrical,HVAC",            42.0, 3, "Available",  "Electrical supervisor"),
            ("Fatou",   "Diallo",     "07811900022","fatou.d@workers.com", "Plumbing,Drainage",          38.0, 3, "Available",  "Licensed plumber"),
            ("Hassan",  "Rashid",     "07811900023","hassan.r@workers.com","Renovation,General",         36.0, 3, "Busy",       "Currently on BR105 refurb"),
            ("Mei",     "Lin",        "07811900024","mei.l@workers.com",   "Heating,HVAC,General",       40.0, 3, "Available",  "Building services engineer"),
            # Manchester (loc 4)
            ("Sean",    "Murphy",     "07811900031","sean.m@workers.com",  "Plumbing,Heating,Drainage",  29.0, 4, "Available",  "Senior plumber"),
            ("Blessing","Adeyemi",    "07811900032","blessing.a@workers.com","General,Renovation",       24.0, 4, "Available",  "Multi-skilled operative"),
            ("Connor",  "Walsh",      "07811900033","connor.w@workers.com","Electrical,HVAC",            31.0, 4, "Busy",       "On site until end Feb"),
        ]
        cursor.executemany("""
            INSERT INTO workers (first_name,last_name,phone,email,specialties,hourly_rate,
            location_id,availability,notes) VALUES (?,?,?,?,?,?,?,?,?)""", workers)
        self.commit()

        # ── Maintenance Types / Catalogue ────────────────────────────────────
        # (category, name, description, cost_min, cost_max, typical_hours, required_specialty, notes)
        maint_types = [
            ("Plumbing", "Tap Repair",            "Fix leaking or dripping taps",                 40,  120, 1.0, "Plumbing",    "Replace washer or cartridge"),
            ("Plumbing", "Pipe Leak Repair",       "Locate and repair leaking pipes",              80,  350, 2.5, "Plumbing",    "May require opening walls"),
            ("Plumbing", "Toilet Repair",          "Fix running or blocked toilet",                60,  200, 1.5, "Plumbing",    ""),
            ("Plumbing", "Boiler Pressure Issue",  "Re-pressurise or bleed radiators",             50,  150, 1.0, "Plumbing",    "Check system pressure"),
            ("Heating",  "Boiler Service",         "Annual gas boiler service",                   120,  250, 3.0, "Heating",     "Gas Safe cert issued"),
            ("Heating",  "Boiler Repair",          "Diagnose and repair faulty boiler",           150,  600, 4.0, "Heating",     "Gas Safe required"),
            ("Heating",  "Radiator Replacement",   "Replace faulty radiator",                      80,  250, 2.0, "Heating",     "Drain system first"),
            ("Electrical","Consumer Unit Upgrade", "Replace consumer unit/fuse board",            300,  700, 5.0, "Electrical",  "Requires Building Control notification"),
            ("Electrical","Socket/Switch Repair",  "Replace broken socket or light switch",        40,  120, 1.0, "Electrical",  "Part P if near water"),
            ("Electrical","Intercom System",       "Repair or replace door intercom",              80,  300, 2.5, "Electrical",  ""),
            ("HVAC",     "AC Service",             "Annual service of air conditioning unit",      80,  200, 2.0, "HVAC",        "Check refrigerant levels"),
            ("HVAC",     "AC Repair",              "Diagnose and repair faulty AC unit",          120,  500, 3.5, "HVAC",        "F-gas cert may be required"),
            ("HVAC",     "Ventilation Check",      "Inspect and clean ventilation system",         60,  150, 1.5, "HVAC",        ""),
            ("Drainage", "Drain Unblocking",       "Clear blocked sink, shower or drain",          60,  200, 1.5, "Drainage",    "CCTV survey if recurring"),
            ("Drainage", "Gutter Clearing",        "Clear and flush gutters and downpipes",        80,  180, 2.0, "Drainage",    "Roof access may be required"),
            ("General",  "Door/Window Lock",       "Repair or replace lock mechanism",             40,  150, 1.0, "General",     ""),
            ("General",  "Plastering",             "Patch and skim plaster repair",                50,  300, 3.0, "General",     "Allow 24h drying time"),
            ("General",  "Pest Control",           "Professional pest treatment",                 100,  400, 2.0, "General",     "Follow-up visit may be needed"),
            ("Renovation","Full Flat Refurb",      "Complete renovation of empty unit",          2000, 8000,40.0, "Renovation",  "Multiple trades required"),
            ("Renovation","Kitchen Fit",           "Install new kitchen units and worktops",      800, 3000,16.0, "Renovation",  "Plumber + electrician also needed"),
            ("Renovation","Bathroom Fit",          "Install new bathroom suite",                  600, 2500,14.0, "Renovation",  "Plumber + electrician also needed"),
            ("Painting",  "Full Flat Decoration",  "Paint all rooms of an apartment",             300, 1000, 8.0, "General",     "Price per room available"),
            ("Painting",  "Single Room",           "Paint one room including ceiling",             80,  250, 3.0, "General",     ""),
        ]
        cursor.executemany("""
            INSERT INTO maintenance_types (category,name,description,typical_cost_min,typical_cost_max,
            typical_hours,required_specialty,notes) VALUES (?,?,?,?,?,?,?,?)""", maint_types)
        self.commit()

        # ── Worker assignments for existing resolved requests ─────────────────
        # Update maintenance assigned_staff_id and add worker_assignments
        # req 1 (Plumbing, Bristol) → Tom Hargreaves (worker_id=1), maint1 (staff_id=10)
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=10 WHERE id=1")
        cursor.execute("INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes) VALUES (?,?,?,?,?)",
                       (1, 1, "2024-11-11", 10, "Tom to replace kitchen tap washer."))
        # req 2 (Heating, Bristol) → Barry Frost (worker_id=3)
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=10 WHERE id=2")
        cursor.execute("INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes) VALUES (?,?,?,?,?)",
                       (2, 3, "2024-10-06", 10, "Barry to carry out annual boiler service."))
        # req 3 (General, Cardiff) → Dylan Price (worker_id=7)
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=11 WHERE id=3")
        cursor.execute("INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes) VALUES (?,?,?,?,?)",
                       (3, 7, "2024-12-02", 11, "Dylan to replace window latch."))
        # req 5 (Drainage, London) → Fatou Diallo (worker_id=9), in progress
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=12 WHERE id=5")
        cursor.execute("INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes) VALUES (?,?,?,?,?)",
                       (5, 9, "2025-01-21", 12, "Fatou to investigate roof terrace drainage."))
        # req 6 (Electrical, Bristol) → Derek Simmons (worker_id=2)
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=10 WHERE id=6")
        cursor.execute("INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes) VALUES (?,?,?,?,?)",
                       (6, 2, "2024-09-19", 10, "Derek to replace intercom panel."))
        # req 7 (Renovation, Bristol) → Hassan Rashid (worker_id=10)
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=10 WHERE id=7")
        cursor.execute("INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes) VALUES (?,?,?,?,?)",
                       (7, 10, "2024-12-02", 10, "Hassan on full refurb, multi-week project."))
        self.commit()

    # ─────────────────────────── AUTH ──────────────────────────────

    def _make_password_hash(self, password: str) -> str:
        """Return a salted hash as 'SALT:HASH' using a fresh random 16-byte salt."""
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}:{hashed}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash. Accepts 'SALT:HASH' or legacy unsalted format."""
        if ":" not in stored_hash:
            # Legacy unsalted format — accept for backward compatibility
            return hashlib.sha256(password.encode()).hexdigest() == stored_hash
        salt, expected = stored_hash.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == expected

    def authenticate_staff(self, username: str, password: str) -> Optional[Staff]:
        if not username or not password:
            return None
        cursor = self.get_cursor()
        cursor.execute(
            "SELECT * FROM staff WHERE username=? AND is_active=1",
            (username,)
        )
        row = cursor.fetchone()
        if row and self._verify_password(password, row["password_hash"]):
            return self._row_to_staff(row)
        return None

    def _row_to_staff(self, row) -> Staff:
        return Staff(
            id=row["id"], username=row["username"],
            password_hash=row["password_hash"],
            first_name=row["first_name"], last_name=row["last_name"],
            role=row["role"], email=row["email"], phone=row["phone"],
            location_id=row["location_id"], is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )

    # ─────────────────────────── LOCATIONS ─────────────────────────

    def get_all_locations(self) -> List[Location]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM locations")
        return [Location(id=r["id"], city=r["city"], address=r["address"],
                         postcode=r["postcode"], country=r["country"])
                for r in cursor.fetchall()]

    # ─────────────────────────── APARTMENTS ────────────────────────

    def get_available_apartments(self, location_id: Optional[int] = None) -> List[Apartment]:
        cursor = self.get_cursor()
        if location_id:
            cursor.execute(
                "SELECT a.*, l.city, l.address FROM apartments a JOIN locations l ON a.location_id=l.id "
                "WHERE a.status='Available' AND a.location_id=?", (location_id,)
            )
        else:
            cursor.execute(
                "SELECT a.*, l.city, l.address FROM apartments a JOIN locations l ON a.location_id=l.id "
                "WHERE a.status='Available'"
            )
        return [self._row_to_apartment(r) for r in cursor.fetchall()]

    def get_all_apartments(self, location_id: Optional[int] = None) -> List[Apartment]:
        cursor = self.get_cursor()
        if location_id:
            cursor.execute(
                "SELECT a.*, l.city, l.address FROM apartments a JOIN locations l ON a.location_id=l.id "
                "WHERE a.location_id=?", (location_id,)
            )
        else:
            cursor.execute(
                "SELECT a.*, l.city, l.address FROM apartments a JOIN locations l ON a.location_id=l.id"
            )
        return [self._row_to_apartment(r) for r in cursor.fetchall()]

    def get_apartment_by_id(self, apt_id: int) -> Optional[Apartment]:
        cursor = self.get_cursor()
        cursor.execute(
            "SELECT a.*, l.city, l.address FROM apartments a JOIN locations l ON a.location_id=l.id WHERE a.id=?",
            (apt_id,)
        )
        row = cursor.fetchone()
        return self._row_to_apartment(row) if row else None

    def _row_to_apartment(self, row) -> Apartment:
        a = Apartment(
            id=row["id"], unit_number=row["unit_number"],
            location_id=row["location_id"], apartment_type=row["apartment_type"],
            num_bedrooms=row["num_bedrooms"], num_bathrooms=row["num_bathrooms"],
            monthly_rent=row["monthly_rent"], floor=row["floor"],
            size_sqft=row["size_sqft"], furnished=bool(row["furnished"]),
            parking=bool(row["parking"]), status=row["status"],
            description=row["description"] or ""
        )
        try:
            a.location_city = row["city"]
            a.location_address = row["address"]
        except (IndexError, KeyError):
            pass
        return a

    def update_apartment_status(self, apt_id: int, status: str):
        cursor = self.get_cursor()
        cursor.execute("UPDATE apartments SET status=? WHERE id=?", (status, apt_id))
        self.commit()

    # ─────────────────────────── TENANTS ───────────────────────────

    def create_tenant(self, tenant: Tenant) -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO tenants (ni_number,first_name,last_name,phone,email,occupation,date_of_birth,
            emergency_contact_name,emergency_contact_phone,
            reference1_name,reference1_phone,reference1_email,
            reference2_name,reference2_phone,reference2_email,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            tenant.ni_number, tenant.first_name, tenant.last_name,
            tenant.phone, tenant.email, tenant.occupation, tenant.date_of_birth,
            tenant.emergency_contact_name, tenant.emergency_contact_phone,
            tenant.reference1_name, tenant.reference1_phone, tenant.reference1_email,
            tenant.reference2_name, tenant.reference2_phone, tenant.reference2_email,
            tenant.notes
        ))
        self.commit()
        return cursor.lastrowid

    def update_tenant(self, tenant: Tenant):
        cursor = self.get_cursor()
        cursor.execute("""
            UPDATE tenants SET first_name=?,last_name=?,phone=?,email=?,occupation=?,date_of_birth=?,
            emergency_contact_name=?,emergency_contact_phone=?,
            reference1_name=?,reference1_phone=?,reference1_email=?,
            reference2_name=?,reference2_phone=?,reference2_email=?,notes=?
            WHERE id=?
        """, (
            tenant.first_name, tenant.last_name, tenant.phone, tenant.email,
            tenant.occupation, tenant.date_of_birth,
            tenant.emergency_contact_name, tenant.emergency_contact_phone,
            tenant.reference1_name, tenant.reference1_phone, tenant.reference1_email,
            tenant.reference2_name, tenant.reference2_phone, tenant.reference2_email,
            tenant.notes, tenant.id
        ))
        self.commit()

    def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,))
        row = cursor.fetchone()
        return self._row_to_tenant(row) if row else None

    def search_tenants(self, query: str) -> List[Tenant]:
        cursor = self.get_cursor()
        q = f"%{query}%"
        cursor.execute("""
            SELECT * FROM tenants WHERE first_name LIKE ? OR last_name LIKE ?
            OR email LIKE ? OR ni_number LIKE ? OR phone LIKE ?
        """, (q, q, q, q, q))
        return [self._row_to_tenant(r) for r in cursor.fetchall()]

    def get_all_tenants(self) -> List[Tenant]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM tenants ORDER BY last_name, first_name")
        return [self._row_to_tenant(r) for r in cursor.fetchall()]

    def _row_to_tenant(self, row) -> Tenant:
        return Tenant(
            id=row["id"], ni_number=row["ni_number"],
            first_name=row["first_name"], last_name=row["last_name"],
            phone=row["phone"] or "", email=row["email"] or "",
            occupation=row["occupation"] or "",
            date_of_birth=row["date_of_birth"],
            emergency_contact_name=row["emergency_contact_name"] or "",
            emergency_contact_phone=row["emergency_contact_phone"] or "",
            reference1_name=row["reference1_name"] or "",
            reference1_phone=row["reference1_phone"] or "",
            reference1_email=row["reference1_email"] or "",
            reference2_name=row["reference2_name"] or "",
            reference2_phone=row["reference2_phone"] or "",
            reference2_email=row["reference2_email"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"]
        )

    # ─────────────────────────── LEASES ────────────────────────────

    def create_lease(self, lease: Lease) -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO leases (tenant_id,apartment_id,start_date,end_date,monthly_rent,deposit_amount,status,created_by)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            lease.tenant_id, lease.apartment_id, lease.start_date, lease.end_date,
            lease.monthly_rent, lease.deposit_amount, lease.status, lease.created_by
        ))
        self.commit()
        lease_id = cursor.lastrowid
        self.update_apartment_status(lease.apartment_id, ApartmentStatus.OCCUPIED.value)
        return lease_id

    def get_lease_by_id(self, lease_id: int) -> Optional[Lease]:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT l.*, t.first_name||' '||t.last_name as tenant_name,
                   t.email as tenant_email, t.phone as tenant_phone,
                   a.unit_number as apartment_unit, a.apartment_type,
                   loc.city as location_city, loc.address as location_address
            FROM leases l
            JOIN tenants t ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE l.id=?
        """, (lease_id,))
        row = cursor.fetchone()
        return self._row_to_lease(row) if row else None

    def get_all_leases(self, location_id: Optional[int] = None) -> List[Lease]:
        cursor = self.get_cursor()
        base = """
            SELECT l.*, t.first_name||' '||t.last_name as tenant_name,
                   t.email as tenant_email, t.phone as tenant_phone,
                   a.unit_number as apartment_unit, a.apartment_type,
                   loc.city as location_city, loc.address as location_address
            FROM leases l
            JOIN tenants t ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
        """
        if location_id:
            cursor.execute(base + " WHERE a.location_id=? ORDER BY l.created_at DESC", (location_id,))
        else:
            cursor.execute(base + " ORDER BY l.created_at DESC")
        return [self._row_to_lease(r) for r in cursor.fetchall()]

    def search_apartments(self, query: str, location_id: Optional[int] = None) -> List[Apartment]:
        cursor = self.get_cursor()
        q = f"%{query}%"
        base = """
            SELECT a.*, l.city, l.address FROM apartments a
            JOIN locations l ON a.location_id=l.id
            WHERE (a.unit_number LIKE ? OR a.apartment_type LIKE ?
                   OR l.city LIKE ? OR a.status LIKE ? OR a.description LIKE ?)
        """
        if location_id:
            cursor.execute(base + " AND a.location_id=?", (q, q, q, q, q, location_id))
        else:
            cursor.execute(base, (q, q, q, q, q))
        return [self._row_to_apartment(r) for r in cursor.fetchall()]

    def get_active_lease_for_apartment(self, apartment_id: int) -> Optional[Lease]:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT l.*, t.first_name||' '||t.last_name as tenant_name,
                   t.email as tenant_email, t.phone as tenant_phone,
                   a.unit_number as apartment_unit, a.apartment_type,
                   loc.city as location_city, loc.address as location_address
            FROM leases l
            JOIN tenants t ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE l.apartment_id=? AND l.status='Active'
            ORDER BY l.created_at DESC LIMIT 1
        """, (apartment_id,))
        row = cursor.fetchone()
        return self._row_to_lease(row) if row else None

    def get_all_leases_for_apartment(self, apartment_id: int) -> List[Lease]:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT l.*, t.first_name||' '||t.last_name as tenant_name,
                   t.email as tenant_email, t.phone as tenant_phone,
                   a.unit_number as apartment_unit, a.apartment_type,
                   loc.city as location_city, loc.address as location_address
            FROM leases l
            JOIN tenants t ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE l.apartment_id=? ORDER BY l.created_at DESC
        """, (apartment_id,))
        return [self._row_to_lease(r) for r in cursor.fetchall()]

    def get_payments_for_apartment(self, apartment_id: int) -> list:
        """Get all payments across all leases for this apartment."""
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT p.*, l.start_date as lease_start, l.end_date as lease_end
            FROM payments p
            JOIN leases l ON p.lease_id=l.id
            WHERE l.apartment_id=? ORDER BY p.due_date DESC
        """, (apartment_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            pay = self._row_to_payment(r)
            pay._lease_start = r["lease_start"]
            pay._lease_end = r["lease_end"]
            result.append(pay)
        return result

    def get_complaints_for_apartment(self, apartment_id: int) -> list:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT c.*, t.first_name||' '||t.last_name as tenant_name,
                   a.unit_number as apartment_unit
            FROM complaints c
            LEFT JOIN tenants t ON c.tenant_id=t.id
            LEFT JOIN apartments a ON c.apartment_id=a.id
            WHERE c.apartment_id=? ORDER BY c.reported_date DESC
        """, (apartment_id,))
        return [self._row_to_complaint(r) for r in cursor.fetchall()]

    def get_maintenance_for_apartment(self, apartment_id: int) -> list:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT m.*, t.first_name||' '||t.last_name as tenant_name,
                   a.unit_number as apartment_unit, loc.city as location_city
            FROM maintenance_requests m
            LEFT JOIN tenants t ON m.tenant_id=t.id
            LEFT JOIN apartments a ON m.apartment_id=a.id
            LEFT JOIN locations loc ON a.location_id=loc.id
            WHERE m.apartment_id=? ORDER BY m.reported_date DESC
        """, (apartment_id,))
        return [self._row_to_maintenance(r) for r in cursor.fetchall()]

    def search_leases(self, query: str, location_id: Optional[int] = None) -> List[Lease]:
        cursor = self.get_cursor()
        q = f"%{query}%"
        base = """
            SELECT l.*, t.first_name||' '||t.last_name as tenant_name,
                   t.email as tenant_email, t.phone as tenant_phone,
                   a.unit_number as apartment_unit, a.apartment_type,
                   loc.city as location_city, loc.address as location_address
            FROM leases l
            JOIN tenants t ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE (t.first_name LIKE ? OR t.last_name LIKE ? OR a.unit_number LIKE ?
                   OR loc.city LIKE ? OR t.email LIKE ?)
        """
        if location_id:
            cursor.execute(base + " AND a.location_id=?", (q, q, q, q, q, location_id))
        else:
            cursor.execute(base, (q, q, q, q, q))
        return [self._row_to_lease(r) for r in cursor.fetchall()]

    def _row_to_lease(self, row) -> Lease:
        from datetime import date as _date
        status = row["status"]
        end_date = row["end_date"]
        if status == "Active" and end_date and end_date < str(_date.today()):
            status = "Expired"
        return Lease(
            id=row["id"], tenant_id=row["tenant_id"], apartment_id=row["apartment_id"],
            start_date=row["start_date"], end_date=end_date,
            monthly_rent=row["monthly_rent"], deposit_amount=row["deposit_amount"],
            status=status,
            early_termination_requested=bool(row["early_termination_requested"]),
            early_termination_date=row["early_termination_date"],
            notice_given_date=row["notice_given_date"],
            created_by=row["created_by"], created_at=row["created_at"],
            tenant_name=row["tenant_name"] or "",
            tenant_email=row["tenant_email"] or "",
            tenant_phone=row["tenant_phone"] or "",
            apartment_unit=row["apartment_unit"] or "",
            apartment_type=row["apartment_type"] or "",
            location_city=row["location_city"] or "",
            location_address=row["location_address"] or ""
        )

    # ─────────────────────────── PAYMENTS ──────────────────────────

    def create_payment_request(self, payment: Payment) -> int:
        """Create a payment request — emulates billing by marking it Paid immediately."""
        cursor = self.get_cursor()
        import random, string
        ref = "REF-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("""
            INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,paid_date,
                                  status,payment_method,reference_number,notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (payment.lease_id, payment.amount_due, payment.amount_due,
              payment.due_date, str(date.today()),
              PaymentStatus.PAID.value, "Payment Request", ref, payment.notes))
        self.commit()
        return cursor.lastrowid

    def get_payments_for_lease(self, lease_id: int) -> List[Payment]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM payments WHERE lease_id=? ORDER BY due_date DESC", (lease_id,))
        return [self._row_to_payment(r) for r in cursor.fetchall()]

    def _row_to_payment(self, row) -> Payment:
        return Payment(
            id=row["id"], lease_id=row["lease_id"],
            amount_due=row["amount_due"], amount_paid=row["amount_paid"],
            due_date=row["due_date"], paid_date=row["paid_date"],
            status=row["status"], payment_method=row["payment_method"] or "",
            reference_number=row["reference_number"] or "",
            notes=row["notes"] or "", created_at=row["created_at"]
        )

    # ─────────────────────────── MAINTENANCE ───────────────────────

    def create_maintenance_request(self, req: MaintenanceRequest) -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO maintenance_requests (lease_id,apartment_id,tenant_id,title,description,
            category,priority,status,reported_date)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (req.lease_id, req.apartment_id, req.tenant_id, req.title, req.description,
              req.category, req.priority, req.status,
              req.reported_date or str(date.today())))
        self.commit()
        return cursor.lastrowid

    def get_maintenance_for_lease(self, lease_id: int) -> List[MaintenanceRequest]:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT m.*, t.first_name||' '||t.last_name as tenant_name,
                   a.unit_number as apartment_unit, loc.city as location_city
            FROM maintenance_requests m
            LEFT JOIN tenants t ON m.tenant_id=t.id
            LEFT JOIN apartments a ON m.apartment_id=a.id
            LEFT JOIN locations loc ON a.location_id=loc.id
            WHERE m.lease_id=? ORDER BY m.reported_date DESC
        """, (lease_id,))
        return [self._row_to_maintenance(r) for r in cursor.fetchall()]

    def _row_to_maintenance(self, row) -> MaintenanceRequest:
        m = MaintenanceRequest(
            id=row["id"], lease_id=row["lease_id"],
            apartment_id=row["apartment_id"], tenant_id=row["tenant_id"],
            title=row["title"], description=row["description"] or "",
            category=row["category"] or "", priority=row["priority"],
            status=row["status"], reported_date=row["reported_date"],
            scheduled_date=row["scheduled_date"],
            resolved_date=row["resolved_date"],
            resolution_notes=row["resolution_notes"] or "",
            cost=row["cost"] or 0.0, time_taken_hours=row["time_taken_hours"] or 0.0,
            assigned_staff_id=row["assigned_staff_id"],
            created_at=row["created_at"]
        )
        try:
            m.tenant_name = row["tenant_name"] or ""
            m.apartment_unit = row["apartment_unit"] or ""
            m.location_city = row["location_city"] or ""
        except (IndexError, KeyError):
            pass
        return m

    # ─────────────────────────── COMPLAINTS ────────────────────────

    def create_complaint(self, complaint: Complaint) -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO complaints (lease_id,tenant_id,apartment_id,title,description,
            category,status,reported_date,created_by)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (complaint.lease_id, complaint.tenant_id, complaint.apartment_id,
              complaint.title, complaint.description, complaint.category,
              complaint.status, complaint.reported_date or str(date.today()),
              complaint.created_by))
        self.commit()
        return cursor.lastrowid

    def get_complaints_for_lease(self, lease_id: int) -> List[Complaint]:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT c.*, t.first_name||' '||t.last_name as tenant_name,
                   a.unit_number as apartment_unit
            FROM complaints c
            LEFT JOIN tenants t ON c.tenant_id=t.id
            LEFT JOIN apartments a ON c.apartment_id=a.id
            WHERE c.lease_id=? ORDER BY c.reported_date DESC
        """, (lease_id,))
        return [self._row_to_complaint(r) for r in cursor.fetchall()]

    def _row_to_complaint(self, row) -> Complaint:
        c = Complaint(
            id=row["id"], lease_id=row["lease_id"],
            tenant_id=row["tenant_id"], apartment_id=row["apartment_id"],
            title=row["title"], description=row["description"] or "",
            category=row["category"] or "", status=row["status"],
            reported_date=row["reported_date"],
            resolved_date=row["resolved_date"],
            resolution_notes=row["resolution_notes"] or "",
            created_by=row["created_by"], created_at=row["created_at"]
        )
        try:
            c.tenant_name = row["tenant_name"] or ""
            c.apartment_unit = row["apartment_unit"] or ""
        except (IndexError, KeyError):
            pass
        return c

    # ─────────────────────────── FINANCE METHODS ───────────────────

    def get_all_payments(self, location_id: Optional[int] = None,
                         status: Optional[str] = None) -> list:
        """All payments, optionally filtered by location and/or status."""
        cursor = self.get_cursor()
        wheres = []
        params = []
        if location_id:
            wheres.append("loc.id=?");  params.append(location_id)
        if status:
            wheres.append("p.status=?"); params.append(status)
        where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
        cursor.execute(f"""
            SELECT p.*,
                   t.first_name||' '||t.last_name  AS tenant_name,
                   t.email                          AS tenant_email,
                   a.unit_number                    AS unit_number,
                   loc.city                         AS city,
                   l.monthly_rent
            FROM payments p
            JOIN leases l   ON p.lease_id   = l.id
            JOIN tenants t  ON l.tenant_id  = t.id
            JOIN apartments a ON l.apartment_id = a.id
            JOIN locations loc ON a.location_id = loc.id
            {where_sql}
            ORDER BY p.due_date DESC
        """, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            pay = self._row_to_payment(r)
            pay.tenant_name  = r["tenant_name"]  or ""
            pay.tenant_email = r["tenant_email"] or ""
            pay.unit_number  = r["unit_number"]  or ""
            pay.city         = r["city"]         or ""
            result.append(pay)
        return result

    def mark_payment_paid(self, payment_id: int, method: str = "Bank Transfer",
                          paid_date: Optional[str] = None) -> None:
        cursor = self.get_cursor()
        pd = paid_date or str(date.today())
        cursor.execute("""
            UPDATE payments
            SET status='Paid', amount_paid=amount_due, paid_date=?, payment_method=?
            WHERE id=?
        """, (pd, method, payment_id))
        self.commit()

    def mark_payment_overdue(self, payment_id: int) -> None:
        cursor = self.get_cursor()
        cursor.execute("UPDATE payments SET status='Overdue' WHERE id=? AND status='Pending'",
                       (payment_id,))
        self.commit()

    def send_late_notification(self, payment_id: int) -> dict:
        """Emulate sending a late-payment notification; returns notification record."""
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT p.*, t.first_name||' '||t.last_name AS tenant_name, t.email,
                   a.unit_number, loc.city
            FROM payments p
            JOIN leases l   ON p.lease_id=l.id
            JOIN tenants t  ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE p.id=?
        """, (payment_id,))
        r = cursor.fetchone()
        if not r:
            return {}
        return {
            "payment_id": payment_id,
            "tenant": r["tenant_name"],
            "email":  r["email"],
            "unit":   r["unit_number"],
            "city":   r["city"],
            "amount": r["amount_due"],
            "due":    r["due_date"],
            "sent_at": str(datetime.now()),
        }

    def create_invoice(self, lease_id: int, amount: float, due_date: str,
                       description: str = "", created_by: Optional[int] = None) -> int:
        """Create a new payment/invoice record and mark it Paid immediately (emulated)."""
        import random, string
        ref = "INV-" + ''.join(random.choices(string.digits, k=6))
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,paid_date,
                                  status,payment_method,reference_number,notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (lease_id, amount, amount, due_date, str(date.today()),
              "Paid", "Invoice", ref, description))
        self.commit()
        return cursor.lastrowid

    def get_financial_summary(self, location_id: Optional[int] = None) -> dict:
        cursor = self.get_cursor()
        params = (location_id,) if location_id else ()
        loc_join  = "JOIN locations loc ON a.location_id=loc.id" 
        loc_where = "AND loc.id=?" if location_id else ""

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(p.amount_due),  0) AS total_billed,
                COALESCE(SUM(p.amount_paid), 0) AS total_collected,
                COALESCE(SUM(CASE WHEN p.status='Pending' THEN p.amount_due ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN p.status='Overdue' THEN p.amount_due ELSE 0 END), 0) AS overdue,
                COUNT(CASE WHEN p.status='Paid'    THEN 1 END) AS paid_count,
                COUNT(CASE WHEN p.status='Pending' THEN 1 END) AS pending_count,
                COUNT(CASE WHEN p.status='Overdue' THEN 1 END) AS overdue_count,
                COUNT(*)                                        AS total_invoices
            FROM payments p
            JOIN leases l ON p.lease_id=l.id
            JOIN apartments a ON l.apartment_id=a.id
            {loc_join}
            WHERE 1=1 {loc_where}
        """, params)
        fin = dict(cursor.fetchone())

        cursor.execute(f"""
            SELECT COALESCE(SUM(m.cost), 0) AS maintenance_cost
            FROM maintenance_requests m
            JOIN apartments a ON m.apartment_id=a.id
            {loc_join}
            WHERE 1=1 {loc_where}
        """, params)
        fin["maintenance_cost"] = cursor.fetchone()["maintenance_cost"] or 0

        cursor.execute(f"""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN a.status='Available' THEN 1 ELSE 0 END) as available,
                   SUM(CASE WHEN a.status='Occupied'  THEN 1 ELSE 0 END) as occupied
            FROM apartments a {loc_join}
            WHERE 1=1 {loc_where}
        """, params)
        apt = cursor.fetchone()
        fin["total_apts"]     = apt["total"]     or 0
        fin["available_apts"] = apt["available"] or 0
        fin["occupied_apts"]  = apt["occupied"]  or 0
        fin["occupancy_rate"] = (apt["occupied"] / apt["total"] * 100) if apt["total"] else 0

        return fin

    def get_monthly_revenue(self, location_id: Optional[int] = None,
                            months: int = 12) -> list:
        """Revenue collected per month for the last N months."""
        cursor = self.get_cursor()
        params = (location_id,) if location_id else ()
        loc_where = "AND loc.id=?" if location_id else ""
        cursor.execute(f"""
            SELECT strftime('%Y-%m', p.paid_date) AS month,
                   SUM(p.amount_paid) AS collected
            FROM payments p
            JOIN leases l ON p.lease_id=l.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE p.status='Paid' {loc_where}
            GROUP BY month ORDER BY month DESC LIMIT ?
        """, params + (months,))
        rows = cursor.fetchall()
        return [{"month": r["month"], "collected": r["collected"]} for r in reversed(rows)]

    def get_occupancy_by_city(self) -> list:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT loc.city,
                   COUNT(*) as total,
                   SUM(CASE WHEN a.status='Occupied'  THEN 1 ELSE 0 END) as occupied,
                   SUM(CASE WHEN a.status='Available' THEN 1 ELSE 0 END) as available,
                   SUM(CASE WHEN a.status='Under Maintenance' THEN 1 ELSE 0 END) as maintenance
            FROM apartments a JOIN locations loc ON a.location_id=loc.id
            GROUP BY loc.city ORDER BY loc.city
        """)
        return [dict(r) for r in cursor.fetchall()]

    def get_maintenance_cost_report(self, location_id: Optional[int] = None) -> list:
        cursor = self.get_cursor()
        params = (location_id,) if location_id else ()
        loc_where = "AND loc.id=?" if location_id else ""
        cursor.execute(f"""
            SELECT m.category,
                   COUNT(*) as count,
                   SUM(m.cost) as total_cost,
                   AVG(m.cost) as avg_cost,
                   SUM(m.time_taken_hours) as total_hours
            FROM maintenance_requests m
            JOIN apartments a ON m.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE 1=1 {loc_where}
            GROUP BY m.category ORDER BY total_cost DESC
        """, params)
        return [dict(r) for r in cursor.fetchall()]

    def get_late_payments(self, location_id: Optional[int] = None) -> list:
        return self.get_all_payments(location_id=location_id, status="Overdue")

    # ─────────────────────────── MAINTENANCE MANAGEMENT ────────────

    def get_all_maintenance(self, location_id: Optional[int] = None,
                            status: Optional[str] = None) -> List[MaintenanceRequest]:
        cursor = self.get_cursor()
        wheres, params = ["1=1"], []
        if location_id:
            wheres.append("loc.id=?"); params.append(location_id)
        if status:
            wheres.append("m.status=?"); params.append(status)
        cursor.execute(f"""
            SELECT m.*,
                   t.first_name||' '||t.last_name AS tenant_name,
                   a.unit_number                  AS apartment_unit,
                   loc.city                       AS location_city
            FROM maintenance_requests m
            LEFT JOIN tenants t    ON m.tenant_id=t.id
            LEFT JOIN apartments a ON m.apartment_id=a.id
            LEFT JOIN locations loc ON a.location_id=loc.id
            WHERE {' AND '.join(wheres)}
            ORDER BY
                CASE m.priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2
                                WHEN 'Medium' THEN 3 ELSE 4 END,
                m.reported_date ASC
        """, params)
        return [self._row_to_maintenance(r) for r in cursor.fetchall()]

    def get_maintenance_by_id(self, maint_id: int) -> Optional[MaintenanceRequest]:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT m.*,
                   t.first_name||' '||t.last_name AS tenant_name,
                   a.unit_number                  AS apartment_unit,
                   loc.city                       AS location_city
            FROM maintenance_requests m
            LEFT JOIN tenants t    ON m.tenant_id=t.id
            LEFT JOIN apartments a ON m.apartment_id=a.id
            LEFT JOIN locations loc ON a.location_id=loc.id
            WHERE m.id=?
        """, (maint_id,))
        row = cursor.fetchone()
        return self._row_to_maintenance(row) if row else None

    def update_maintenance(self, req: MaintenanceRequest) -> None:
        cursor = self.get_cursor()
        cursor.execute("""
            UPDATE maintenance_requests
            SET title=?, description=?, category=?, priority=?, status=?,
                scheduled_date=?, resolved_date=?, resolution_notes=?,
                cost=?, time_taken_hours=?, assigned_staff_id=?
            WHERE id=?
        """, (req.title, req.description, req.category, req.priority, req.status,
              req.scheduled_date, req.resolved_date, req.resolution_notes,
              req.cost, req.time_taken_hours, req.assigned_staff_id, req.id))
        self.commit()

    # ─────────────────────────── WORKERS ────────────────────────────

    def get_workers(self, location_id: Optional[int] = None,
                    availability: Optional[str] = None,
                    specialty: Optional[str] = None) -> list:
        cursor = self.get_cursor()
        wheres, params = ["w.is_active=1"], []
        if location_id:
            wheres.append("w.location_id=?"); params.append(location_id)
        if availability:
            wheres.append("w.availability=?"); params.append(availability)
        cursor.execute(f"""
            SELECT w.*, l.city
            FROM workers w
            LEFT JOIN locations l ON w.location_id=l.id
            WHERE {' AND '.join(wheres)}
            ORDER BY w.availability, w.last_name
        """, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            w = self._row_to_worker(r)
            if specialty and specialty.lower() not in w.specialties.lower():
                continue
            result.append(w)
        return result

    def get_worker_by_id(self, worker_id: int):
        cursor = self.get_cursor()
        cursor.execute("SELECT w.*, l.city FROM workers w LEFT JOIN locations l ON w.location_id=l.id WHERE w.id=?",
                       (worker_id,))
        row = cursor.fetchone()
        return self._row_to_worker(row) if row else None

    def _row_to_worker(self, row):
        from dataclasses import dataclass
        class Worker:
            pass
        w = Worker()
        w.id           = row["id"]
        w.first_name   = row["first_name"]
        w.last_name    = row["last_name"]
        w.phone        = row["phone"] or ""
        w.email        = row["email"] or ""
        w.specialties  = row["specialties"] or ""
        w.hourly_rate  = row["hourly_rate"] or 0.0
        w.location_id  = row["location_id"]
        w.availability = row["availability"] or "Available"
        w.notes        = row["notes"] or ""
        w.is_active    = bool(row["is_active"])
        try:    w.city = row["city"] or ""
        except: w.city = ""
        w.full_name = f"{row['first_name']} {row['last_name']}"
        return w

    def update_worker_availability(self, worker_id: int, availability: str) -> None:
        cursor = self.get_cursor()
        cursor.execute("UPDATE workers SET availability=? WHERE id=?", (availability, worker_id))
        self.commit()

    def add_worker(self, first_name, last_name, phone, email, specialties,
                   hourly_rate, location_id, availability="Available", notes="") -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO workers (first_name,last_name,phone,email,specialties,hourly_rate,
            location_id,availability,notes) VALUES (?,?,?,?,?,?,?,?,?)
        """, (first_name, last_name, phone, email, specialties, hourly_rate, location_id, availability, notes))
        self.commit()
        return cursor.lastrowid

    # ─────────────────────────── WORKER ASSIGNMENTS ─────────────────

    def get_assignments_for_maintenance(self, maintenance_id: int) -> list:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT wa.*, w.first_name||' '||w.last_name AS worker_name,
                   w.specialties, w.hourly_rate, w.phone AS worker_phone
            FROM worker_assignments wa
            JOIN workers w ON wa.worker_id=w.id
            WHERE wa.maintenance_id=?
            ORDER BY wa.assigned_date DESC
        """, (maintenance_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            a = type("Assignment", (), {})()
            a.id = r["id"]; a.maintenance_id = r["maintenance_id"]
            a.worker_id = r["worker_id"]; a.worker_name = r["worker_name"]
            a.specialties = r["specialties"] or ""
            a.hourly_rate = r["hourly_rate"] or 0.0
            a.worker_phone = r["worker_phone"] or ""
            a.assigned_date = r["assigned_date"]; a.assigned_by = r["assigned_by"]
            a.notes = r["notes"] or ""
            result.append(a)
        return result

    def assign_worker(self, maintenance_id: int, worker_id: int,
                      assigned_by: int, notes: str = "") -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO worker_assignments (maintenance_id,worker_id,assigned_date,assigned_by,notes)
            VALUES (?,?,?,?,?)
        """, (maintenance_id, worker_id, str(date.today()), assigned_by, notes))
        # Update maintenance assigned_staff_id to the assigning staff
        cursor.execute("UPDATE maintenance_requests SET assigned_staff_id=? WHERE id=?",
                       (assigned_by, maintenance_id))
        # Set worker to Busy
        cursor.execute("UPDATE workers SET availability='Busy' WHERE id=?", (worker_id,))
        self.commit()
        return cursor.lastrowid

    def remove_assignment(self, assignment_id: int, worker_id: int) -> None:
        cursor = self.get_cursor()
        cursor.execute("DELETE FROM worker_assignments WHERE id=?", (assignment_id,))
        # Free worker if no other active assignments
        cursor.execute("""
            SELECT COUNT(*) FROM worker_assignments wa
            JOIN maintenance_requests m ON wa.maintenance_id=m.id
            WHERE wa.worker_id=? AND m.status NOT IN ('Resolved','Closed')
        """, (worker_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("UPDATE workers SET availability='Available' WHERE id=?", (worker_id,))
        self.commit()

    # ─────────────────────────── MAINTENANCE TYPES ──────────────────

    def get_maintenance_types(self, category: Optional[str] = None) -> list:
        cursor = self.get_cursor()
        if category:
            cursor.execute("SELECT * FROM maintenance_types WHERE category=? ORDER BY name", (category,))
        else:
            cursor.execute("SELECT * FROM maintenance_types ORDER BY category, name")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            mt = type("MaintenanceType", (), {})()
            mt.id = r["id"]; mt.category = r["category"]; mt.name = r["name"]
            mt.description = r["description"] or ""; mt.typical_cost_min = r["typical_cost_min"]
            mt.typical_cost_max = r["typical_cost_max"]; mt.typical_hours = r["typical_hours"]
            mt.required_specialty = r["required_specialty"] or ""; mt.notes = r["notes"] or ""
            result.append(mt)
        return result

    def get_maintenance_categories(self) -> list:
        cursor = self.get_cursor()
        cursor.execute("SELECT DISTINCT category FROM maintenance_types ORDER BY category")
        return [r["category"] for r in cursor.fetchall()]

    def get_maintenance_stats(self, location_id: Optional[int] = None) -> dict:
        cursor = self.get_cursor()
        params = (location_id,) if location_id else ()
        loc_join  = "LEFT JOIN apartments a ON m.apartment_id=a.id LEFT JOIN locations loc ON a.location_id=loc.id"
        loc_where = "AND loc.id=?" if location_id else ""
        cursor.execute(f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN m.status='Open'        THEN 1 ELSE 0 END) AS open_count,
                SUM(CASE WHEN m.status='In Progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN m.status='Resolved'    THEN 1 ELSE 0 END) AS resolved,
                SUM(CASE WHEN m.priority='Urgent'    THEN 1 ELSE 0 END) AS urgent,
                SUM(CASE WHEN m.priority='High'      THEN 1 ELSE 0 END) AS high,
                COALESCE(SUM(m.cost),0)              AS total_cost,
                COALESCE(AVG(m.time_taken_hours),0)  AS avg_hours
            FROM maintenance_requests m
            {loc_join}
            WHERE 1=1 {loc_where}
        """, params)
        return dict(cursor.fetchone())

    def get_dashboard_stats(self, location_id: Optional[int] = None) -> dict:
        cursor = self.get_cursor()
        loc_filter = "WHERE a.location_id=?" if location_id else ""
        params = (location_id,) if location_id else ()

        cursor.execute(f"""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN a.status='Available' THEN 1 ELSE 0 END) as available,
                   SUM(CASE WHEN a.status='Occupied' THEN 1 ELSE 0 END) as occupied
            FROM apartments a {loc_filter}
        """, params)
        apt_stats = cursor.fetchone()

        cursor.execute(f"""
            SELECT COUNT(*) as active_leases
            FROM leases l JOIN apartments a ON l.apartment_id=a.id
            WHERE l.status='Active' {'AND a.location_id=?' if location_id else ''}
        """, params)
        lease_count = cursor.fetchone()

        cursor.execute(f"""
            SELECT COUNT(*) as open_complaints
            FROM complaints c JOIN apartments a ON c.apartment_id=a.id
            WHERE c.status='Open' {'AND a.location_id=?' if location_id else ''}
        """, params)
        complaints = cursor.fetchone()

        cursor.execute(f"""
            SELECT COUNT(*) as open_maintenance
            FROM maintenance_requests m JOIN apartments a ON m.apartment_id=a.id
            WHERE m.status='Open' {'AND a.location_id=?' if location_id else ''}
        """, params)
        maintenance = cursor.fetchone()

        return {
            "total_apartments": apt_stats["total"] or 0,
            "available_apartments": apt_stats["available"] or 0,
            "occupied_apartments": apt_stats["occupied"] or 0,
            "active_leases": lease_count["active_leases"] or 0,
            "open_complaints": complaints["open_complaints"] or 0,
            "open_maintenance": maintenance["open_maintenance"] or 0,
        }
    # ─────────────────────────── ADMIN / MANAGER METHODS ───────────

    # ── Staff Management ──────────────────────────────────────────────────────

    def get_staff_for_location(self, location_id: int) -> list:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT s.*, l.city FROM staff s
            LEFT JOIN locations l ON s.location_id=l.id
            WHERE s.location_id=? ORDER BY s.role, s.last_name
        """, (location_id,))
        return [self._row_to_staff_rich(r) for r in cursor.fetchall()]

    def get_all_staff(self) -> list:
        cursor = self.get_cursor()
        cursor.execute("""
            SELECT s.*, l.city FROM staff s
            LEFT JOIN locations l ON s.location_id=l.id
            ORDER BY s.location_id, s.role, s.last_name
        """)
        return [self._row_to_staff_rich(r) for r in cursor.fetchall()]

    def _row_to_staff_rich(self, row) -> Staff:
        s = self._row_to_staff(row)
        try: s.city = row["city"] or ""
        except Exception: s.city = ""
        return s

    def create_staff(self, username: str, password: str, first_name: str, last_name: str,
                     role: str, email: str, phone: str, location_id: int) -> int:
        cursor = self.get_cursor()
        pw = self._make_password_hash(password)
        cursor.execute("""
            INSERT INTO staff (username,password_hash,first_name,last_name,role,email,phone,location_id)
            VALUES (?,?,?,?,?,?,?,?)
        """, (username, pw, first_name, last_name, role, email, phone, location_id))
        self.commit()
        return cursor.lastrowid

    def update_staff(self, staff_id: int, first_name: str, last_name: str,
                     role: str, email: str, phone: str, location_id: int) -> None:
        cursor = self.get_cursor()
        cursor.execute("""
            UPDATE staff SET first_name=?,last_name=?,role=?,email=?,phone=?,location_id=?
            WHERE id=?
        """, (first_name, last_name, role, email, phone, location_id, staff_id))
        self.commit()

    def reset_staff_password(self, staff_id: int, new_password: str) -> None:
        cursor = self.get_cursor()
        cursor.execute("UPDATE staff SET password_hash=? WHERE id=?",
                       (self._make_password_hash(new_password), staff_id))
        self.commit()

    def toggle_staff_active(self, staff_id: int) -> bool:
        """Toggle is_active; returns new state."""
        cursor = self.get_cursor()
        cursor.execute("SELECT is_active FROM staff WHERE id=?", (staff_id,))
        row = cursor.fetchone()
        if not row: return False
        new_state = 0 if row["is_active"] else 1
        cursor.execute("UPDATE staff SET is_active=? WHERE id=?", (new_state, staff_id))
        self.commit()
        return bool(new_state)

    def username_exists(self, username: str) -> bool:
        cursor = self.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM staff WHERE username=?", (username,))
        return cursor.fetchone()[0] > 0

    # ── Apartment Management ──────────────────────────────────────────────────

    def create_apartment(self, apt: "Apartment") -> int:
        cursor = self.get_cursor()
        cursor.execute("""
            INSERT INTO apartments (unit_number,location_id,apartment_type,num_bedrooms,
            num_bathrooms,monthly_rent,floor,size_sqft,furnished,parking,status,description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (apt.unit_number, apt.location_id, apt.apartment_type, apt.num_bedrooms,
              apt.num_bathrooms, apt.monthly_rent, apt.floor, apt.size_sqft or 0,
              1 if apt.furnished else 0, 1 if apt.parking else 0,
              apt.status or "Available", apt.description or ""))
        self.commit()
        return cursor.lastrowid

    def update_apartment(self, apt: "Apartment") -> None:
        cursor = self.get_cursor()
        cursor.execute("""
            UPDATE apartments SET unit_number=?,apartment_type=?,num_bedrooms=?,
            num_bathrooms=?,monthly_rent=?,floor=?,size_sqft=?,furnished=?,
            parking=?,status=?,description=? WHERE id=?
        """, (apt.unit_number, apt.apartment_type, apt.num_bedrooms, apt.num_bathrooms,
              apt.monthly_rent, apt.floor, apt.size_sqft or 0,
              1 if apt.furnished else 0, 1 if apt.parking else 0,
              apt.status, apt.description or "", apt.id))
        self.commit()

    def delete_apartment(self, apt_id: int) -> bool:
        """Only deletes if no active leases."""
        cursor = self.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM leases WHERE apartment_id=? AND status='Active'", (apt_id,))
        if cursor.fetchone()[0] > 0:
            return False
        cursor.execute("DELETE FROM apartments WHERE id=?", (apt_id,))
        self.commit()
        return True

    # ── Lease Tracking ────────────────────────────────────────────────────────

    def get_expiring_leases(self, days: int = 60,
                             location_id: Optional[int] = None) -> list:
        cursor = self.get_cursor()
        params = [location_id] if location_id else []
        loc_filter = "AND a.location_id=?" if location_id else ""
        cursor.execute(f"""
            SELECT l.*,
                   t.first_name||' '||t.last_name AS tenant_name,
                   t.email AS tenant_email, t.phone AS tenant_phone,
                   a.unit_number AS apartment_unit, a.apartment_type,
                   loc.city AS location_city, loc.address AS location_address,
                   CAST(julianday(l.end_date) - julianday('now') AS INTEGER) AS days_remaining
            FROM leases l
            JOIN tenants t  ON l.tenant_id=t.id
            JOIN apartments a ON l.apartment_id=a.id
            JOIN locations loc ON a.location_id=loc.id
            WHERE l.status='Active'
              AND julianday(l.end_date) - julianday('now') >= 0
              AND julianday(l.end_date) - julianday('now') <= ?
              {loc_filter}
            ORDER BY l.end_date ASC
        """, [days] + params)
        return [self._row_to_lease_rich(r) for r in cursor.fetchall()]

    def _row_to_lease_rich(self, row) -> "Lease":
        l = self._row_to_lease(row)
        try: l.days_remaining = row["days_remaining"]
        except Exception: l.days_remaining = None
        return l

    def update_lease_status(self, lease_id: int, status: str) -> None:
        cursor = self.get_cursor()
        cursor.execute("UPDATE leases SET status=? WHERE id=?", (status, lease_id))
        self.commit()

    def request_early_termination(self, lease_id: int, apartment_id: int,
                                   notice_date: str, termination_date: str) -> None:
        cursor = self.get_cursor()
        cursor.execute("""
            UPDATE leases
               SET early_termination_requested = 1,
                   notice_given_date           = ?,
                   early_termination_date      = ?,
                   status                      = 'Terminated'
             WHERE id = ?
        """, (notice_date, termination_date, lease_id))
        # FR-17: create a Pending penalty invoice (5% of monthly rent)
        cursor.execute("SELECT monthly_rent FROM leases WHERE id=?", (lease_id,))
        row = cursor.fetchone()
        if row:
            penalty = round(row["monthly_rent"] * 0.05, 2)
            reference = f"PENALTY-{lease_id}"
            cursor.execute("""
                INSERT INTO payments
                    (lease_id, amount_due, amount_paid, due_date, status, reference_number, notes)
                VALUES (?, ?, 0, ?, 'Pending', ?,
                        'Early termination penalty (5% of monthly rent)')
            """, (lease_id, penalty, termination_date, reference))
        self.commit()
        self.update_apartment_status(apartment_id, ApartmentStatus.AVAILABLE.value)

    # ── Location / City Management (Manager only) ─────────────────────────────

    def add_location(self, city: str, address: str, postcode: str,
                     country: str = "UK") -> int:
        cursor = self.get_cursor()
        cursor.execute("INSERT INTO locations (city,address,postcode,country) VALUES (?,?,?,?)",
                       (city, address, postcode, country))
        self.commit()
        return cursor.lastrowid

    def update_location(self, loc_id: int, city: str, address: str,
                        postcode: str, country: str = "UK") -> None:
        cursor = self.get_cursor()
        cursor.execute("UPDATE locations SET city=?,address=?,postcode=?,country=? WHERE id=?",
                       (city, address, postcode, country, loc_id))
        self.commit()

    # ── Cross-city reports (Manager) ──────────────────────────────────────────

    def get_cross_city_summary(self) -> list:
        """One row per city with financial + occupancy + maintenance summary."""
        cursor = self.get_cursor()
        locs = self.get_all_locations()
        result = []
        for loc in locs:
            fin   = self.get_financial_summary(loc.id)
            maint = self.get_maintenance_stats(loc.id)
            staff_count = len(self.get_staff_for_location(loc.id))
            result.append({
                "location_id":  loc.id,
                "city":         loc.city,
                "address":      loc.address,
                "total_apts":   fin["total_apts"],
                "occupied":     fin["occupied_apts"],
                "available":    fin["available_apts"],
                "occupancy_pct":fin["occupancy_rate"],
                "collected":    fin["total_collected"],
                "pending":      fin["pending"],
                "overdue":      fin["overdue"],
                "maint_open":   maint.get("open", 0),
                "maint_cost":   fin["maintenance_cost"],
                "staff_count":  staff_count,
            })
        return result

    def get_table_data(self, table_name: str,
                       location_id: Optional[int] = None) -> tuple:
        """Return (column_names, rows) for the Data Explorer.

        location_id scopes the result to a single city where possible.
        password_hash is masked automatically.
        Only whitelisted tables are accessible to prevent SQL injection.
        """
        _ALLOWED = {
            "apartments", "tenants", "leases", "payments",
            "maintenance_requests", "complaints", "locations",
            "staff", "workers",
        }
        if table_name not in _ALLOWED:
            raise ValueError(f"Table not available: {table_name}")

        _MASKED = {"password_hash"}

        cursor = self.get_cursor()

        if location_id:
            if table_name == "apartments":
                cursor.execute("SELECT * FROM apartments WHERE location_id=?", (location_id,))
            elif table_name == "staff":
                cursor.execute("SELECT * FROM staff WHERE location_id=?", (location_id,))
            elif table_name == "workers":
                cursor.execute("SELECT * FROM workers WHERE location_id=?", (location_id,))
            elif table_name == "leases":
                cursor.execute("""
                    SELECT l.* FROM leases l
                    JOIN apartments a ON l.apartment_id = a.id
                    WHERE a.location_id = ?""", (location_id,))
            elif table_name == "payments":
                cursor.execute("""
                    SELECT p.* FROM payments p
                    JOIN leases l ON p.lease_id = l.id
                    JOIN apartments a ON l.apartment_id = a.id
                    WHERE a.location_id = ?""", (location_id,))
            elif table_name == "maintenance_requests":
                cursor.execute("""
                    SELECT m.* FROM maintenance_requests m
                    JOIN apartments a ON m.apartment_id = a.id
                    WHERE a.location_id = ?""", (location_id,))
            elif table_name == "complaints":
                cursor.execute("""
                    SELECT c.* FROM complaints c
                    JOIN apartments a ON c.apartment_id = a.id
                    WHERE a.location_id = ?""", (location_id,))
            else:
                cursor.execute(f"SELECT * FROM {table_name}")  # noqa: S608 — table_name is whitelisted above
        else:
            cursor.execute(f"SELECT * FROM {table_name}")  # noqa: S608

        rows = cursor.fetchall()
        if not rows:
            cursor.execute(f"PRAGMA table_info({table_name})")  # noqa: S608
            columns = [r["name"] for r in cursor.fetchall()]
            return columns, []

        columns = list(rows[0].keys())
        result = [
            tuple("••••••••" if col in _MASKED else row[col] for col in columns)
            for row in rows
        ]
        return columns, result

    def get_performance_report(self, location_id: Optional[int] = None) -> dict:
        """Comprehensive performance data for a location or all locations."""
        fin   = self.get_financial_summary(location_id)
        maint = self.get_maintenance_stats(location_id)
        occ   = self.get_occupancy_by_city() if not location_id else None
        rev   = self.get_monthly_revenue(location_id, months=6)
        mc    = self.get_maintenance_cost_report(location_id)
        exp   = self.get_expiring_leases(90, location_id)
        return {
            "financial":    fin,
            "maintenance":  maint,
            "occupancy":    occ,
            "monthly_rev":  rev,
            "maint_costs":  mc,
            "expiring":     exp,
        }