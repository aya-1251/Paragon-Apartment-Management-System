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

