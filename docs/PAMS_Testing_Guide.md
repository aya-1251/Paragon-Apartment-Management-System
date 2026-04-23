# PAMS — Testing Guide

Module: UFCF8S-30-2 Advanced Software Development | Group 17

---

## Test Plan

### Goals
1. Confirm that all functional requirements (FR-01 – FR-37) behave as specified.
2. Confirm that non-functional requirements (NFR-01 – NFR-13) are met.
3. Demonstrate correct use of input validation and verification across all forms.
4. Verify cross-table data consistency for multi-step operations (integration tests).

### Test Levels Covered

| Level | Type | How |
|---|---|---|
| System / Validation | Manual black-box | Follow Sections 1–16 of this guide |
| Integration | Manual black-box | Sections 15–16 — cross-table consistency checks |
| **Unit / Integration** | **Automated (white-box)** | **Section 18 — `test_models.py` & `test_database.py`** |

### Testing Techniques Used

| Technique | Where applied |
|---|---|
| Equivalence class | Authentication (valid vs invalid credentials), Sections 1–2 |
| Boundary value | Empty-field validation, TC-03/04/05/16/22/28; date edge cases TC-17 |
| State-based | Lease lifecycle TC-23 → TC-26 → TC-28; payment lifecycle TC-32 → TC-35 |
| Cause-effect | Lease creation sets Occupied TC-23→TC-24; termination creates penalty invoice TC-26→TC-28 |
| Black-box navigation | Role access control — each role is tested as an independent equivalence class |

### Responsibilities
- **Any team member** — follow the manual test cases in Sections 1–16 for system validation.

### Pass Criteria
- Every manual TC produces the stated **Expected** outcome with no console errors.
- All integration tests confirm consistent state across all affected tables.

---

## How to Run the App

No setup scripts are needed. On first launch the database is created and seeded automatically:

```
python main.py
```

The file `property_management.db` will be created in the same directory on first run. To reset the demo data, delete `property_management.db` and re-launch.

---

## Test Accounts

All accounts share the password: **`password123`**

| Username | Role | Location |
|---|---|---|
| `admin1` | Administrator | Bristol |
| `admin2` | Administrator | Cardiff |
| `admin3` | Administrator | London |
| `admin4` | Administrator | Manchester |
| `frontdesk1` | Front Desk | Bristol |
| `frontdesk2` | Front Desk | Manchester |
| `frontdesk3` | Front Desk | London |
| `frontdesk4` | Front Desk | Cardiff |
| `finance1` | Finance Manager | Bristol |
| `finance2` | Finance Manager | Cardiff |
| `finance3` | Finance Manager | London |
| `finance4` | Finance Manager | Manchester |
| `maint1` | Maintenance Staff | Bristol |
| `maint2` | Maintenance Staff | Cardiff |
| `maint3` | Maintenance Staff | London |
| `maint4` | Maintenance Staff | Manchester |
| `manager1` | Manager | All cities |

---

## Section 1 — Authentication (FR-01, FR-02, FR-03)

*Technique: equivalence class (valid credentials vs invalid credentials) and boundary value (empty fields).*

### TC-01 — Valid login
1. Launch the app. The login screen appears.
2. Enter `admin1` / `password123`.
3. Click **Login** (or press Enter).
4. **Expected:** Administrator dashboard loads. Sidebar shows: Apartments, Staff Accounts, Manage Apartments, Lease Tracker, Reports.

### TC-02 — Wrong password
1. Enter `admin1` / `wrongpass`.
2. Click **Login**.
3. **Expected:** Error dialog — "Invalid username or password." No detail about which field is wrong (NFR-01).

### TC-03 — Empty username
1. Leave the username field blank. Enter any password.
2. Click **Login**.
3. **Expected:** Warning dialog prompting both fields. Login is not attempted.

### TC-04 — Empty password
1. Enter `admin1` in username. Leave password blank.
2. Click **Login**.
3. **Expected:** Same warning dialog as TC-03.

### TC-05 — Both fields empty
1. Click **Login** without filling in either field.
2. **Expected:** Warning dialog. No database query is executed.

### TC-06 — Enter key triggers login
1. Type `admin1` / `password123`.
2. Press **Enter** (do not click the button).
3. **Expected:** Dashboard loads (same as TC-01).

---

## Section 2 — Role-Based Access Control (FR-04, NFR-01)

*Technique: equivalence class — each role is a separate equivalence class with its own permitted navigation surface.*

### TC-07 — Administrator sees only Admin nav items
1. Log in as `admin1`.
2. Check the sidebar.
3. **Expected items visible:** Apartments, Staff Accounts, Manage Apartments, Lease Tracker, Reports, Data Explorer.
4. **Expected items NOT visible:** Payments, Create Invoice, Late Payments, Maintenance Jobs, Workers, Job Types (Finance/Maintenance items).

### TC-08 — Front Desk sees only Front Desk nav items
1. Log in as `frontdesk1`.
2. **Expected items:** Apartments (commune view), Register Tenant, Tenant Records, Log Complaint, Log Maintenance, Maintenance Requests.
3. No apartment management, lease creation, payment, or staff management options visible.

### TC-09 — Finance Manager sees only Finance nav items
1. Log in as `finance1`.
2. **Expected items:** Apartments, Payments, Create Invoice, Late Payments, Reports.
3. No maintenance, staff, or lease creation options visible.

### TC-10 — Maintenance Staff sees only Maintenance nav items
1. Log in as `maint1`.
2. **Expected items:** Apartments, Maintenance Jobs, Workers, Job Types & Prices, Add Request.
3. No tenant, payment, lease, or staff management options visible.

### TC-11 — Manager sees cross-city nav items
1. Log in as `manager1`.
2. **Expected items:** Portfolio Overview, Occupancy, Financial Reports, Lease Tracker, Performance, Expand Business, Data Explorer.
3. The Portfolio Overview shows all four cities. No apartment edit, payment processing, or staff management options visible.

---

## Section 3 — Apartment Grid and Detail (FR-12)

*Technique: cause-effect — mock data apartment statuses cause specific card colours and detail tab content.*

### TC-12 — Apartment grid loads with status colours
1. Log in as `admin1`.
2. **Expected:** Apartments screen loads showing unit cards. Each card has a coloured top bar: blue = Occupied, green = Available, amber = Under Maintenance.
3. With demo data: Bristol should show BR101 (Occupied), BR102 (Occupied), BR103 (Available), BR104 (Occupied), BR105 (Under Maintenance).

### TC-13 — Apartment card opens tabbed detail window
1. Click any apartment card.
2. **Expected:** A detail window opens with five tabs: Overview, Lease & Tenant, Payments, Maintenance, Complaints.
3. Each tab loads the relevant records for that unit.

### TC-14 — Search and filter on apartment grid
1. In the search box, type `BR1`.
2. **Expected:** Only Bristol units matching BR1 appear.
3. Select filter "Occupied".
4. **Expected:** Only Occupied units remain visible. Click "All" to restore the full view.

---

## Section 4 — Tenant Registration (FR-05, FR-06, NFR-09)

*Technique: equivalence class (valid NI vs duplicate NI vs empty required field) and boundary value (empty NI).*

Log in as `frontdesk1` for these tests.

### TC-15 — Register a new tenant (valid data)
1. Click **Register Tenant** in the sidebar.
2. Fill in all required fields:
   - NI Number: `AB999999Z`
   - First Name: `Test`, Last Name: `Tenant`
   - Phone: `07700000001`
   - Email: `test@example.com`
   - Occupation: `Engineer`
   - Reference 1 Name: `John Ref`
3. Click **Register Tenant**.
4. **Expected:** Success dialog. The new tenant appears in the Tenant Records table.

### TC-15b — Invalid NI number format rejected (NFR-14)
1. Open **Register Tenant**.
2. Enter NI Number `INVALID123` (wrong format — must be 2 letters, 6 digits, 1 letter).
3. Fill all other fields with valid data.
4. Click **Register Tenant** (or Next on the first step).
5. **Expected:** Warning dialog — "NI Number must be 2 letters, 6 digits, then 1 letter (e.g. AB123456C)." No record inserted.

### TC-15c — Invalid UK phone number rejected (NFR-14)
1. Open **Register Tenant**.
2. Enter a valid NI Number (`AB999998Z`) and fill other fields.
3. Enter Phone: `12345` (too short / wrong format).
4. Click **Register Tenant** / Next.
5. **Expected:** Warning dialog — "Phone must be a valid UK number (e.g. 07700 123456 or +44 7700 123456)." No record inserted.
6. Retry with `+44 7700 900123` — **Expected:** Accepted and registration proceeds.

### TC-16 — Duplicate NI number rejected (FR-06)
1. Open **Register Tenant** again.
2. Enter NI Number `NI100001A` (James Taylor's NI from demo data) with any other values.
3. Click **Register Tenant**.
4. **Expected:** Error dialog indicating the NI number already exists. No record inserted.

### TC-17 — Empty required fields blocked (NFR-09)
1. Open **Register Tenant**.
2. Leave NI Number blank, fill in all other fields.
3. Click **Register Tenant**.
4. **Expected:** Warning dialog. No database write occurs.

---

## Section 5 — Apartment Management (FR-09, FR-10, FR-11, NFR-09)

*Technique: equivalence class (valid input vs missing required field) and boundary value (empty rent field).*

Log in as `admin1` for these tests.

### TC-18 — Add a new apartment (valid data)
1. Click **Manage Apartments** in the sidebar, then **➕ Add Apartment**.
2. Fill in:
   - Unit Number: `BR999`
   - Type: `Studio`
   - Monthly Rent: `850`
   - Bedrooms: `0`, Bathrooms: `1`, Floor: `1`
3. Click **Save ✓**.
4. **Expected:** Success dialog. The new apartment appears in the list with status `Available`.

### TC-19 — New apartment defaults to Available (FR-10)
1. After TC-18, find `BR999` in the apartments list.
2. **Expected:** Status column shows `Available`.

### TC-20 — Administrator location scoped to their city (FR-11)
1. Open **Add Apartment**.
2. **Expected:** The location is automatically set to Bristol (admin1's city) and no other city can be selected.

### TC-21 — Missing required fields blocked
1. Open **Add Apartment**.
2. Leave Monthly Rent blank. Fill all other fields.
3. Click **Save ✓**.
4. **Expected:** Warning dialog — check numeric fields. No record inserted.

---

## Section 6 — Lease Management (FR-13, FR-14, FR-15)

*Technique: state-based — apartment moves from Available → Occupied when a lease is created.*

Log in as `admin1`.

### TC-22 — Lease Tracker loads with expiry filters
1. Click **Lease Tracker** in the sidebar.
2. **Expected:** Summary pills show Expired / < 30 days / 31–90 days / 90+ day counts.
3. Click each radio button (30 days, 60 days, 90 days, 180 days, All active) — the table updates accordingly.

### TC-23 — Create a lease (valid data)
1. Navigate to the apartment detail for a unit with status `Available` (e.g., BR103).
2. Open the **Lease & Tenant** tab and click **Create Lease** (or use the admin's lease creation form).
3. Select a tenant with no current active lease, set start date, end date, and deposit.
4. Click **Save**.
5. **Expected:** Success dialog. BR103 now shows status `Occupied` in the apartment grid.

### TC-24 — Lease creation sets apartment to Occupied (FR-14)
1. After TC-23, click back to the Apartments view.
2. **Expected:** The apartment used in TC-23 now shows the `Occupied` status badge.

### TC-25 — Mark lease as Expired
1. In **Lease Tracker**, find a lease with status Active but an end date in the past.
2. Click **Mark Expired** on that row.
3. **Expected:** Confirmation prompt. After confirming, the row status changes to `Expired`.

---

## Section 7 — Early Lease Termination (FR-16, FR-17)

*Technique: state-based (lease → Terminated) and cause-effect (termination creates penalty invoice).*

Log in as `frontdesk1` for these tests.

### TC-26 — Terminate an active lease
1. Click any Occupied apartment card to open its detail window.
2. Go to the **Lease & Tenant** tab.
3. Click **⚠ Early Termination** (visible on the right of the action bar for active leases).
4. The dialog shows: original end date, monthly rent, 30-day notice period, and the penalty (5% of monthly rent). As you edit the notice date, the Earliest Exit Date updates automatically (notice date + 30 days).
5. Enter a notice date (e.g., today's date in `YYYY-MM-DD` format) and click **Confirm Termination**.
6. A confirmation prompt shows the exact notice date, termination date, and penalty amount — click **Yes**.
7. **Expected:** Success dialog stating lease is terminated and penalty owed. The apartment detail window closes automatically.

### TC-27 — Apartment reverts to Available after termination (FR-17)
1. After TC-26, return to the Apartments view.
2. **Expected:** The apartment from the terminated lease now shows status `Available` (green card).

### TC-28 — Penalty invoice created on termination (FR-17)
1. After TC-26, log out and log in as `finance1`.
2. Click **Payments** and look for the terminated tenant.
3. **Expected:** A new `Pending` invoice exists with amount = 5% of the tenant's monthly rent and notes reading "Early termination penalty (5% of monthly rent)".

### TC-28b — Early Termination button hidden after termination
1. Log back in as `frontdesk1`.
2. Open the same apartment (now Available, with no active lease).
3. **Expected:** No active lease is shown in the Lease & Tenant tab; the **⚠ Early Termination** button is not visible.

---

## Section 8 — Payments & Billing (FR-18, FR-19, FR-20, FR-21)

*Technique: state-based (Pending → Paid, Pending → Overdue → Paid) and cause-effect.*

Log in as `finance1` for these tests.

### TC-29 — Payments Ledger loads correctly (FR-18)
1. Click **Payments** in the sidebar.
2. **Expected:** Table shows all payment records for Bristol with columns: Reference, Tenant, Unit, City, Due Date, Amount Due, Paid, Status.
3. Demo data includes Paid, Pending, and Overdue records. Summary pills show totals.

### TC-30 — Filter payments by status
1. Click the "Overdue" radio button in the filter bar.
2. **Expected:** Only Overdue records remain. Export CSV shows only these records.
3. Click "All" to restore the full view.

### TC-31 — Search payments
1. Type a tenant name (e.g., `James`) in the search box.
2. **Expected:** Only records for James Taylor appear.

### TC-32 — Mark a Pending invoice as Paid (FR-19)
1. Find a Pending payment in the list.
2. Click **Mark Paid** on that row.
3. In the dialog, select payment method `Bank Transfer` and confirm today's date.
4. Click **Confirm ✓**.
5. **Expected:** Success dialog. The payment now shows status `Paid` with a **Receipt** button.

### TC-33 — Receipt dialog displays correctly
1. Click **Receipt** on a Paid payment.
2. **Expected:** A receipt window opens showing reference number, tenant, unit, dates, method, amount paid, and status.

### TC-34 — Create an invoice (FR-20)
1. Click **Create Invoice** in the sidebar.
2. Select an active lease from the dropdown.
3. **Expected:** Amount field auto-fills with the lease monthly rent.
4. Set due date to today and click **Create Invoice ✓**.
5. **Expected:** Success dialog. The new invoice appears in the Recent Invoices table below.

### TC-35 — Flag overdue payments (FR-21)
1. Click **Late Payments** in the sidebar.
2. **Expected:** All Overdue payments for Bristol are listed with Notify and Mark Paid buttons.
3. Click **Notify** on one record.
4. **Expected:** Confirmation dialog saying notification has been sent to the tenant.

---

## Section 9 — Financial Reporting (FR-23)

*Technique: cause-effect — paying invoices in earlier TCs causes the summary totals to change.*

Log in as `finance1` or `manager1`.

### TC-36 — Finance Reports page loads (FR-23)
1. Click **Reports** in the sidebar.
2. **Expected:** Page shows top-level KPI pills (Total Billed, Collected, Pending, Overdue), a per-city breakdown table, and a monthly revenue grid (last 6 months).

### TC-37 — Financial summary reflects payments just processed
1. Note the current **Collected** figure.
2. Complete TC-32 (mark one payment as Paid).
3. Navigate back to **Reports**.
4. **Expected:** Collected has increased by the invoice amount. Pending has decreased by the same amount. Total Billed is unchanged.

---

## Section 10 — Maintenance Jobs (FR-26, FR-27, FR-28)

*Technique: state-based (Open → In Progress → Resolved → Closed) and boundary value (empty title).*

### TC-38 — Log a new maintenance request (FR-26)
Log in as `frontdesk1`.
1. Click **Log Maintenance** (or navigate to **Add Request** if in Maintenance shell).
2. Fill in:
   - Apartment: select any occupied unit
   - Title: `Broken window latch`
   - Description: `The window in the bedroom will not latch securely.`
   - Category: `Windows`
   - Priority: `Medium`
3. Click **Submit**.
4. **Expected:** Success dialog. Status defaults to `Open`.

### TC-39 — Empty title blocked
1. Open the log maintenance form.
2. Leave Title blank. Fill all other fields.
3. Click **Submit**.
4. **Expected:** Warning dialog. No record inserted.

### TC-40 — View job queue with filters (FR-27)
Log in as `maint1`.
1. Click **Maintenance Jobs** in the sidebar.
2. **Expected:** All requests for Bristol appear. Summary pills show Open, In Progress, Resolved, Total counts.
3. Click the "Open" status filter — only Open jobs remain.
4. Click the "Urgent" priority filter — only Urgent jobs remain. Click "All" to reset.

### TC-41 — Click row opens job detail window
1. Click any row in the job queue.
2. **Expected:** A detail window opens with full information: title, description, category, priority, status, tenant, scheduled date, resolution notes, cost, time taken.

### TC-42 — Assign worker and schedule job (FR-28)
1. In a job detail window for an Open request, select a worker from the dropdown.
2. Set a scheduled date.
3. Click **Save / Update**.
4. **Expected:** Status changes to `In Progress`. The worker and scheduled date are saved.

### TC-43 — Resolve a maintenance request (FR-28)
1. Open an In Progress job.
2. Fill in Resolution Notes, Cost (e.g., `120.00`), and Time Taken (e.g., `2.5` hours).
3. Click **Mark Resolved**.
4. **Expected:** Status changes to `Resolved`. Cost and time are saved.

---

## Section 11 — Workers and Job Types (FR-29, FR-30)

Log in as `maint1`.

### TC-44 — View worker roster (FR-29)
1. Click **Workers** in the sidebar.
2. **Expected:** A table of workers at Bristol appears showing name, phone, email, specialties, hourly rate, and availability.

### TC-45 — Add a worker
1. Click **➕ Add Worker**.
2. Fill in name, phone, hourly rate, and availability.
3. Click **Save**.
4. **Expected:** Success dialog. New worker appears in the roster.

### TC-46 — View job types catalogue (FR-30)
1. Click **Job Types & Prices** in the sidebar.
2. **Expected:** A table of job categories appears with typical cost min/max, typical hours, and required specialty.

---

## Section 12 — Complaints (FR-31, FR-32)

Log in as `frontdesk1`.

### TC-47 — Log a complaint (FR-31)
1. Click **Log Complaint** in the sidebar.
2. Fill in:
   - Apartment: select any occupied unit
   - Title: `Noise from upstairs`
   - Description: `Excessive noise after 11pm.`
   - Category: `Noise`
3. Click **Submit**.
4. **Expected:** Success dialog. Status defaults to `Open`.

### TC-48 — Complaint appears in apartment detail (FR-32)
1. Click the apartment card for the unit used in TC-47.
2. Click the **Complaints** tab.
3. **Expected:** The complaint logged in TC-47 appears with its title, status (Open), and reported date.

---

## Section 13 — Staff Management (FR-37)

Log in as `admin1`.

### TC-49 — View staff accounts
1. Click **Staff Accounts** in the sidebar.
2. **Expected:** A list of all staff at Bristol appears, with role pills showing counts per role.

### TC-50 — Add a new staff account
1. Click **➕ Add Staff Account**.
2. Fill in first name, last name, username (`newstaff_test`), password, role (`Front Desk`), and email.
3. Click **Save ✓**.
4. **Expected:** Success dialog. New account appears in the staff list as Active.
5. Log out and log in as `newstaff_test` / (your chosen password) — Front Desk dashboard loads.

### TC-51 — Deactivate a staff account
1. Find a staff member (not yourself) in the list.
2. Click **Deactivate**.
3. **Expected:** The row's Active indicator changes to `✗ No`. The account can no longer log in.

### TC-52 — Duplicate username rejected
1. Click **➕ Add Staff Account**.
2. Enter username `admin1` (already exists).
3. Click **Save ✓**.
4. **Expected:** Error dialog. No duplicate record inserted.

---

## Section 14 — CSV and PDF Export (FR-35, FR-36)

*These tests apply to any view with ⬇ CSV / ⬇ PDF buttons.*

### TC-53 — Export Apartments as CSV
Log in as `admin1`, open **Manage Apartments**.
1. Click **⬇ CSV**.
2. Choose a save location and confirm.
3. **Expected:** A `.csv` file is created. Open it — it contains a header row (Unit, Type, Beds, Baths, Floor, Rent, Size, Furnished, Parking, Status) and one data row per apartment.

### TC-54 — Export respects active filter
Log in as `finance1`, open **Payments**.
1. Filter to "Overdue" status.
2. Click **⬇ CSV**.
3. **Expected:** The exported file contains only Overdue records, not all payments.

### TC-55 — Export PDF (requires reportlab)
Log in as `maint1`, open **Maintenance Jobs**.
1. Click **⬇ PDF**.
2. Choose a save location and confirm.
3. **Expected:** A landscape A4 PDF is created with a styled table (blue header row, alternating white/light-grey rows).
4. If reportlab is not installed: **Expected:** Error dialog with install instructions. No crash.

### TC-56 — CSV injection sanitisation (FR-36, NFR-04)
1. Register a tenant with NI number `=CMD` (starts with `=`).
2. Export Tenant Records as CSV.
3. Open the CSV in a text editor.
4. **Expected:** The NI field is prefixed with `'` (apostrophe), producing `'=CMD` — the formula character is neutralised.

### TC-57 — Export with no data shows message
1. In any table view, apply a filter that returns zero records.
2. Click **⬇ CSV**.
3. **Expected:** Info dialog — "No data to export." No empty file is created.

---

## Section 14b — Data Explorer (Admin and Manager)

*Technique: equivalence class — Admin sees location-scoped data; Manager sees all cities.*

### TC-57b — Admin Data Explorer is location-scoped
1. Log in as `admin1` (Bristol).
2. Click **Data Explorer** in the sidebar.
3. Select the `tenants` table from the pill row.
4. **Expected:** A Treeview loads showing only Bristol tenant records. No Cardiff, London, or Manchester tenants appear.

### TC-57c — Manager Data Explorer shows all cities
1. Log in as `manager1`.
2. Click **Data Explorer** in the sidebar.
3. Select the `leases` table.
4. **Expected:** Leases from all four cities appear. The table includes a `location_city` or similar column confirming cross-city data.

### TC-57d — Password column is masked
1. In Data Explorer (admin or manager), select the `staff` table.
2. **Expected:** The `password_hash` column shows `••••••••` for every row — the real hash is never visible in the UI.

### TC-57e — Row detail panel
1. In Data Explorer, click any row in the Treeview.
2. **Expected:** A horizontally scrollable detail panel appears at the bottom showing one card per column, with the column name and value. Status values (Active, Overdue, etc.) are colour-coded.

### TC-57f — Export from Data Explorer
1. In Data Explorer, select any table and load data.
2. Click **⬇ CSV**.
3. **Expected:** A CSV file is created containing the table data. The `password_hash` column contains `••••••••` (not the real hash) in the exported file.

---

## Section 15 — Manager Cross-City Views (FR-24, FR-25, FR-33, FR-34)

Log in as `manager1`.

### TC-58 — Portfolio Overview shows all four cities
1. The Portfolio Overview loads on login.
2. **Expected:** Summary pills show totals across all cities. One city card per location (Bristol, Cardiff, London, Manchester).

### TC-59 — Occupancy chart and table (FR-24)
1. Click **Occupancy** in the sidebar.
2. **Expected:** A stacked bar chart shows Occupied / Available / Maintenance segments per city. The City Breakdown table lists exact counts and percentages.

### TC-60 — Manager Lease Tracker is cross-city
1. Click **Lease Tracker** in the sidebar.
2. **Expected:** Leases from all four cities appear. The City column distinguishes locations.
3. Export CSV — confirms all-city data is present in the file.

### TC-61 — Expand Business registers a new city (FR-34)
1. Click **Expand Business** in the sidebar.
2. Fill in city name, address, and postcode.
3. Click **Register Location**.
4. **Expected:** Success dialog. The new city appears in the Portfolio Overview on the next view load.

---

## Section 16 — Integration Tests

Integration tests verify that **multi-step operations produce consistent state across all affected tables**. These are manual tests — check each table listed after performing the action.

*Technique: cause-effect across module boundaries.*

### IT-01 — Lease creation is atomic across leases and apartments tables
**Precondition:** at least one Available apartment and one tenant with no active lease exist.

1. Note an apartment with status `Available` and record its ID.
2. Complete TC-23 (Create Lease) using that apartment.
3. After the success dialog, check the following:
   - **Lease Tracker (admin1)** — a new active lease row exists for that apartment.
   - **Apartments grid** — the same apartment now shows status `Occupied`.
4. **Expected:** Both changes are present simultaneously. A missing change indicates the lease creation was not atomic.

### IT-02 — Lease termination is consistent across three tables
**Precondition:** an active lease exists (from IT-01 or demo data).

1. Complete TC-26 (Terminate Lease) for an active lease.
2. Check all three affected tables:
   - **Lease Tracker** — the lease status is `Terminated`.
   - **Apartments grid** — the apartment's status is `Available`.
   - **Payments (finance1)** — a new `Pending` invoice exists for the correct tenant with amount = 5% of monthly rent.
3. **Expected:** All three changes are present. A missing change indicates `terminate_lease()` did not execute all database updates correctly.

### IT-03 — Financial summary reflects payments processed in the same session
**Precondition:** at least one Pending invoice exists.

1. Note the current **Collected** total in **Reports** (TC-36).
2. Complete TC-32 (Mark a Pending invoice as Paid) and record the invoice amount.
3. Navigate back to **Reports** without restarting the app.
4. **Expected:**
   - Collected has increased by exactly the invoice amount from step 2.
   - Pending has decreased by the same amount.
   - Total Billed is unchanged.
   - This confirms the Finance view reads live data rather than a cached snapshot.

### IT-04 — Maintenance job cost rolls into financial reporting
**Precondition:** a maintenance request has been resolved with a cost (from TC-43).

1. Note the maintenance cost entered in TC-43.
2. Log in as `finance1`, open **Reports**.
3. Check the per-city row for Bristol in the city breakdown table.
4. **Expected:** The `Maint Cost` column reflects the cost entered during TC-43. If other jobs also have costs, the value is the sum of all resolved costs for Bristol.

---

## Section 17 — Non-Functional Requirements

### TC-62 — Salted password hashing (NFR-02)
1. After registering any new staff account (TC-50), open `property_management.db` in a SQLite viewer (e.g., DB Browser for SQLite).
2. Inspect the `staff` table `password_hash` column for the new account.
3. **Expected:** The value is in `SALT:HASH` format — a 32-character hex salt, a colon, then a 64-character SHA-256 hex hash (total ~97 characters). The plaintext password is never stored.
4. Create a second staff account with the **same password**. Compare both `password_hash` values.
5. **Expected:** The two stored values are **different** (unique salt per account) — demonstrating rainbow-table resistance.

### TC-63 — SQL injection protection (NFR-03)
1. In the login username field, enter: `' OR '1'='1`.
2. Enter any password and click **Login**.
3. **Expected:** Error dialog — "Invalid username or password." The injected SQL is treated as a literal string; no bypass occurs.

### TC-64 — Error dialogs visible on all failures (NFR-06)
1. Trigger a validation error on any form (e.g., empty required field, duplicate NI).
2. **Expected:** A dialog box appears with a clear message. The error is not silently ignored or printed only to the console.

### TC-65 — Light theme consistent across all screens (NFR-05)
1. Log in and navigate through every screen (Login, all sidebar items, all forms and dialogs).
2. **Expected:** All screens use the consistent light-mode palette (off-white background, white panels, blue accent) with no default grey tkinter widgets breaking the theme.

### TC-66 — Logout clears session and returns to login
1. Log in as any user.
2. Click **⬅ Sign Out** at the bottom of the sidebar and confirm.
3. **Expected:** Login screen appears. No cached session data is accessible.

---

## Regression Testing

After any code change, re-test the relevant sections to confirm existing functionality has not broken.

| Area changed | Re-run these TCs |
|---|---|
| Login / authentication logic | TC-01 – TC-06 |
| Sidebar / role navigation | TC-07 – TC-11 |
| Apartment grid and detail | TC-12 – TC-14 |
| Tenant registration | TC-15 – TC-17, TC-15b, TC-15c |
| Apartment creation | TC-18 – TC-21 |
| Lease creation | TC-22 – TC-25, IT-01 |
| Lease termination / penalty | TC-26 – TC-28b, IT-02 |
| Payment processing | TC-29 – TC-35 |
| Financial reporting | TC-36 – TC-37, IT-03 |
| Maintenance jobs | TC-38 – TC-43, IT-04 |
| Workers and job types | TC-44 – TC-46 |
| Complaints | TC-47 – TC-48 |
| Staff management | TC-49 – TC-52 |
| CSV / PDF export | TC-53 – TC-57 |
| Data Explorer | TC-57b – TC-57f |
| Manager cross-city views | TC-58 – TC-61 |
| Database schema changes | IT-01 – IT-04 + TC-62 |

---

## Section 18 — Automated Testing Suite

In addition to the manual tests above, PAMS includes a fully automated test suite that validates the **model layer** and **database integration** without any UI interaction. These tests run in isolation (they never touch the production `property_management.db`) and are ideal for regression testing during development.

### 18.1 – Unit Tests: `tests/test_models.py`

**Purpose:** Test every model class in complete isolation — no database, no I/O.  
**Number of tests:** ~70 assertions (each test method covers a small unit of logic).

| Class | What's tested |
|-------|----------------|
| **Enums** | Every status string value matches what the DB and UI expect (e.g. `"Under Maintenance"` not `"Maintenance"`). |
| **Location** | `display_name()`, default country, empty city edge case. |
| **Apartment** | `is_available()`, `is_occupied()`, `annual_rent()`, all status combinations, zero/large rent. |
| **Tenant** | `full_name`, `has_references()`, `has_emergency_contact()` with all missing‑field combos. |
| **Lease** | `is_active`/`is_expired`, `days_until_expiry()` (future/past/`None`/invalid date), `early_termination_penalty()` at 5% for multiple rent levels, zero rent, notice days constant. |
| **Payment** | `balance_due()` (full/partial/overpaid), `is_overdue()` (past/future/paid/no date/invalid), `is_paid()`. |
| **MaintenanceRequest** | `is_open`/`is_resolved`/`is_urgent()`, default priority/status/cost/hours, empty title allowed by model. |
| **Complaint** | `is_open`/`is_resolved()` for all statuses including *Under Review*. |
| **Staff** | `full_name`, `is_manager()`/`is_admin()`, `has_location_access()`, active/inactive flags. |

### 18.2 – Integration Tests: `tests/test_database.py`

**Purpose:** Test the `DatabaseManager` class against a real SQLite database, but **every test uses a fresh `:memory:` database** – no side effects on the real file.  
**Number of tests:** 79 individual test methods.

| Class | What's tested |
|-------|----------------|
| **Authentication** | Valid login, wrong password, wrong username, empty credentials, inactive account blocks login, reactivation restores login, password reset. |
| **TenantCRUD** | Create/retrieve, positive ID, duplicate NI rejected, update fields, get all, search by name, no‑match search. |
| **ApartmentManagement** | Create/retrieve, default *Available* status, status update, field update, filter by location, available‑only filter, delete with/without lease (delete‑with‑active‑lease guard), search. |
| **LeaseLifecycle** | Create marks apartment *Occupied*, active lease query, no‑lease returns `None`, joined tenant name and unit, get by ID, status update, expired auto‑detection, history query. |
| **Early termination** | Status → *Terminated*, flag set, apartment freed → *Available*, penalty payment created at correct 5% amount, penalty status is *Pending*. |
| **Payments** | `create_payment_request` returns ID and marks *Paid*, `amount_paid` equals `amount_due`, `mark_paid`, `mark_overdue`, overdue doesn't affect already‑Paid, payments for apartment, financial summary, `create_invoice`. |
| **Maintenance** | Create, retrieve for apartment/lease, update status/schedule, resolve with cost+hours+notes, filter by status, not‑found returns `None`, stats open count. |
| **Complaints** | Create (respecting staff FK), retrieve for apartment/lease, multiple complaints, empty list, joined tenant name. |
| **StaffManagement** | Create, duplicate username blocked, `username_exists`, toggle active/inactive, update fields, location‑scoped query, all‑staff query, manager/admin role flags, admin‑vs‑manager guard logic. |
| **LocationManagement** | Add, get all, update, cross‑city summary structure. |
| **Full lifecycle** | One end‑to‑end scenario: register tenant → create lease → pay → log maintenance → log complaint → early terminate → verify all downstream state. |



