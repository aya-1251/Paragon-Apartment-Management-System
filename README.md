# Paragon Apartment Management System (PAMS)

**Module:** Advanced Software Development (UFCF8S-30-2)  
**Group:** Group 17

---

## 1. Project Description

PAMS is an Object-Oriented desktop application built with Python and Tkinter (light-themed GUI) to manage the multi-city operations of the Paragon apartment management company.

The system features:
- A fully relational **SQLite** database (`property_management.db`) — auto-created and seeded on first launch
- **Role-Based Access Control (RBAC)** with five distinct roles, each with a dedicated shell and restricted UI surface
- A clean **MVC-style architecture** split across dedicated modules, with `@dataclass` models and `Enum`-based status types
- **CSV and PDF export** on every major table view (Strategy pattern via `exporters.py`)

---

## 2. Architecture Overview

| File | Responsibility |
| :--- | :--- |
| `main.py` | App entry point — owns the root window and dispatches to the correct role shell on login |
| `views.py` | Shared UI classes and helpers: `LoginView`, `CommuneView` (apartment grid), `ApartmentDetailWindow`, `DataExplorerView`, `EarlyTerminationDialog`, palette constants, `export_bar` |
| `views_admin.py` | Administrator shell — staff management, apartment management, lease tracker, reports |
| `views_finance.py` | Finance Manager shell — payments ledger, invoice creation, late payments, financial reports |
| `views_maintenance.py` | Maintenance Staff shell — job queue, worker roster, job-type catalogue, add request |
| `views_manager.py` | Manager shell — cross-city portfolio overview, occupancy charts, financial reports, lease tracker, performance, city expansion |
| `models.py` | `@dataclass` models with `Enum` status types — `Location`, `Apartment`, `Tenant`, `Lease`, `Payment`, `MaintenanceRequest`, `Complaint`, `Staff` |
| `db_manager.py` | All SQLite operations — single point of contact with the database; creates schema and seeds demo data on first run |
| `exporters.py` | Strategy-pattern CSV / PDF exporters used by table views |

---

## 3. Prerequisites & Dependencies

- **Python Version:** Python 3.10 or higher recommended
- **External Packages:**
  - `reportlab` — required only for PDF export; CSV export works without it

Install the optional PDF dependency with:
```bash
pip install reportlab
```

> All other dependencies (`sqlite3`, `tkinter`, `datetime`, `hashlib`, `dataclasses`, `enum`) are part of the Python standard library.

---

## 4. Installation & Setup Instructions

There is only **one step** — no separate database setup or mock-data script is needed:

```bash
python main.py
```

On the very first launch, `DatabaseManager` automatically:
1. Creates `property_management.db` with the full schema (11 tables)
2. Seeds realistic multi-city demo data — locations, staff, apartments, tenants, leases, payments, maintenance requests, and complaints

Subsequent launches skip the seed step (detected via row count on the `locations` table).

---

## 5. System Access & Test Credentials

All accounts share the same password: **`password123`**

### Administrator (one per city)
| Username | Location |
| :--- | :--- |
| `admin1` | Bristol |
| `admin2` | Cardiff |
| `admin3` | London |
| `admin4` | Manchester |

### Front Desk Staff
| Username | Location |
| :--- | :--- |
| `frontdesk1` | Bristol |
| `frontdesk2` | Manchester |
| `frontdesk3` | London |
| `frontdesk4` | Cardiff |

### Finance Manager
| Username | Location |
| :--- | :--- |
| `finance1` | Bristol |
| `finance2` | Cardiff |
| `finance3` | London |
| `finance4` | Manchester |

### Maintenance Staff
| Username | Location |
| :--- | :--- |
| `maint1` | Bristol |
| `maint2` | Cardiff |
| `maint3` | London |
| `maint4` | Manchester |

### Manager (cross-city)
| Username | Scope |
| :--- | :--- |
| `manager1` | All cities |

---

## 6. Role Capabilities

| Feature | Admin | Front Desk | Finance | Maintenance | Manager |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Apartment grid (commune view) | ✅ | ✅ | ✅ | ✅ | ✅ (all cities) |
| Apartment detail (tabbed) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Add / Edit / Delete Apartment | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage Staff Accounts | ✅ | ❌ | ❌ | ❌ | ❌ |
| Lease Tracker | ✅ | ❌ | ❌ | ❌ | ✅ (all cities) |
| Register / Update Tenant | ❌ | ✅ | ❌ | ❌ | ❌ |
| Log Complaint | ❌ | ✅ | ❌ | ❌ | ❌ |
| Request Early Termination | ❌ | ✅ | ❌ | ❌ | ❌ |
| Payments Ledger | ❌ | ❌ | ✅ | ❌ | ❌ |
| Create Invoice | ❌ | ❌ | ✅ | ❌ | ❌ |
| Late Payments / Notify | ❌ | ❌ | ✅ | ❌ | ❌ |
| Financial Reports | ❌ | ❌ | ✅ | ❌ | ✅ (all cities) |
| Maintenance Job Queue | ❌ | ❌ | ❌ | ✅ | ❌ |
| Manage Workers | ❌ | ❌ | ❌ | ✅ | ❌ |
| Job Types & Pricing Catalogue | ❌ | ❌ | ❌ | ✅ | ❌ |
| Portfolio Overview | ❌ | ❌ | ❌ | ❌ | ✅ |
| Occupancy Charts | ❌ | ❌ | ❌ | ❌ | ✅ |
| Performance Reports | ❌ | ❌ | ❌ | ❌ | ✅ |
| Expand Business (add city) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Data Explorer (raw tables) | ✅ | ❌ | ❌ | ❌ | ✅ |
| CSV / PDF Export | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 7. Feature Highlights

### 7.1 Apartment Detail — Tabbed Record View
Clicking any apartment card opens a full-detail window with five tabs:
- **Overview** — unit specs, status, description
- **Lease & Tenant** — active lease summary, tenant contact and reference details
- **Payments** — full payment history for this unit with paid/overdue breakdown
- **Maintenance** — all maintenance requests linked to this unit
- **Complaints** — all complaint records, with status and resolution notes

### 7.2 CSV / PDF Export (Strategy Pattern)
Every major table view has **⬇ CSV** and **⬇ PDF** buttons. Exports respect the current filter (e.g. exporting the Payments ledger filtered to "Overdue" only exports overdue records). Implementation lives in `exporters.py` as a GoF Strategy:

- `CSVExporter` — stdlib only; sanitises leading `=/+/-/@` characters to neutralise CSV-injection in spreadsheet apps
- `PDFExporter` — uses `reportlab` (landscape A4, styled table with alternating rows); requires `pip install reportlab`
- Add new formats by subclassing `Exporter` and registering in `_REGISTRY` — zero changes to call sites (Open/Closed Principle)

Views with export buttons: Staff Accounts, Manage Apartments, Lease Tracker (Admin) · Payments Ledger, Late Payments (Finance) · Maintenance Jobs (Maintenance) · Lease Tracker (Manager)

### 7.3 Maintenance Workflow
The Maintenance shell supports the full job lifecycle:
1. Front Desk logs a request (title, description, category, priority)
2. Maintenance Staff sees it in the job queue, assigns a worker from their roster, sets a scheduled date, and communicates it to the tenant
3. On completion, staff logs resolution notes, cost, and time taken
4. The request is marked Resolved / Closed; cost rolls into financial reporting

Workers are managed separately (roster, specialties, hourly rate, availability). A job-type catalogue provides typical cost ranges and required specialties per category.

### 7.4 Early Termination Workflow
Front Desk can record an early lease exit from the **Lease & Tenant** tab on any apartment with an active lease. The dialog enforces the company policy encoded in `Lease`:
- **30 days' notice** required (`REQUIRED_NOTICE_DAYS`)
- **5% penalty** on monthly rent (`EARLY_TERMINATION_PENALTY_RATE`)

The earliest exit date auto-updates as the user edits the notice date. On confirmation the lease is marked Terminated, the apartment flips to Available, and the notice/termination dates plus the penalty owed are persisted.

### 7.5 Late Payment Notice
The Finance Manager can generate a formatted **Late Payment Notice** for any overdue payment. The notice template (sender, tenant address, amount outstanding, original due date) is rendered in-app and explicitly emulated — no real email is sent — satisfying the spec's "generates notification if the payment is late" requirement for a desktop application.

### 7.6 Data Explorer
Administrators (scoped to their city) and Managers (all cities) get a **Data Explorer** view that lets them browse the raw rows of any of 9 whitelisted tables in a Treeview. Clicking a row expands a horizontally scrollable detail panel of column-cards with status colouring. The `password_hash` column is masked as `••••••••` server-side in `get_table_data()`. Both CSV and PDF export are available from the same view.

### 7.7 Security
- Passwords are stored as **salted SHA-256** in `SALT:HASH` format — each account gets a unique 16-byte random salt, so identical passwords produce different stored hashes (defeats rainbow-table attacks). `_verify_password` accepts both salted and legacy unsalted hashes for backward compatibility.
- **Role-Based Access Control** — each role shell only renders the UI surface appropriate to that role; there are no hidden buttons that could be bypassed. Admin queries are additionally scoped to `location_id` at the DB layer.
- **Input validation** — NI number regex `[A-Z]{2}\d{6}[A-Z]` and UK phone regex `(\+44|0)\d{9,10}` are enforced in the Register Tenant wizard.
- **SQL injection prevention** — all queries use SQLite parameterised statements. The Data Explorer's table-name parameter is checked against a `_ALLOWED` whitelist before any f-string interpolation.
- **CSV injection prevention** — exported cells starting with `=`, `+`, `-`, or `@` are prefixed with `'` to neutralise spreadsheet formula execution.

### 7.8 Auto-Seeded Demo Data
On first launch the system creates **4 cities**, **17 staff accounts** (4 admins, 4 front desk, 4 finance, 4 maintenance, 1 manager), **17 apartments**, **8 tenants**, **11 leases**, a rich payment history (paid, pending, overdue), and several maintenance requests — no manual setup step required.

---

## 8. Database Schema

`property_management.db` contains **11 tables**:

| Table | Purpose |
| :--- | :--- |
| `locations` | Office/city records (Bristol, Cardiff, London, Manchester) |
| `staff` | System accounts with hashed passwords, roles and location assignment |
| `apartments` | Property listings with full attributes (type, rent, bedrooms, floor, size, furnished, parking, status) |
| `tenants` | Registered tenants with NI number, emergency contact, and two references |
| `leases` | Agreements linking tenants to apartments, with early-termination fields |
| `payments` | Invoices with paid/pending/overdue tracking, payment method, and reference numbers |
| `maintenance_requests` | Logged issues with priority, scheduling, worker assignment, cost, and time tracking |
| `complaints` | Tenant complaints with category, status, and resolution notes |
| `workers` | Maintenance worker roster with specialties, hourly rate and availability |
| `maintenance_types` | Job-type catalogue with typical cost ranges and required specialties |
| `worker_assignments` | Links workers to specific maintenance jobs |
