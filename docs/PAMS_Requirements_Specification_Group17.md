# PAMS

## Paragon Apartment Management System

### Requirements Specification

Module: UFCF8S-30-2 Advanced Software Development
**Group 17**
Date: 20 April 2026

Paragon Apartment Management System | Group 17 | Requirements Specification

PAMS — Requirements Specification | Module: UFCF8S-30-2 | Group 17

# 1. Introduction

## 1.1 Project Overview

PAMS (Paragon Apartment Management System) is a desktop application developed for the Paragon apartment management company. Paragon operates across multiple UK cities — Bristol, Cardiff, London, and Manchester — and requires a consolidated, secure, and scalable software solution to replace its existing paper-based, decentralised processes.

The system supports role-based access control across five distinct user roles, manages tenant and apartment lifecycles, processes billing and payments, handles maintenance requests and complaints, and provides management-level reporting and cross-city oversight.

## 1.2 Scope

This document defines the functional and non-functional requirements for PAMS. It covers:
* User account and role management (5 roles)
* Tenant registration and lifecycle management
* Apartment registration, occupancy tracking, and lease management
* Payment and billing processing (emulated — no live payment gateway)
* Maintenance request logging, worker assignment, and resolution tracking
* Complaint logging and resolution tracking
* Operational reporting (occupancy, financial summaries, maintenance costs)
* Multi-city support across Bristol, Cardiff, London, and Manchester
* CSV and PDF export of all major data views

## 1.3 Stakeholders and User Roles

The following table defines the five user roles and their primary responsibilities within PAMS.

<table>
  <thead>
    <tr>
      <th>Role</th>
      <th>Responsibilities</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>Administrator</b></td>
      <td>Full access for their assigned city: manage staff accounts, apartments, leases, and location-specific reports.</td>
    </tr>
    <tr>
      <td><b>Front Desk Staff</b></td>
      <td>Register new tenants, handle tenant inquiries, log maintenance requests and complaints.</td>
    </tr>
    <tr>
      <td><b>Finance Manager</b></td>
      <td>Manage invoices and payments, flag late payments, generate financial summaries and reports.</td>
    </tr>
    <tr>
      <td><b>Maintenance Staff</b></td>
      <td>View and manage maintenance job queue, assign workers, schedule jobs, log time, cost, and resolution details.</td>
    </tr>
    <tr>
      <td><b>Manager</b></td>
      <td>Oversee all city operations via cross-city portfolio, generate performance and occupancy reports, expand business to new cities.</td>
    </tr>
  </tbody>
</table>

## 1.4 Technical Stack

The system is implemented as a desktop application using the following technologies:

*   Programming Language: Python 3.10+
*   GUI Framework: Tkinter with ttk (light theme)
*   Database: SQLite (relational, local file — `property_management.db`)
*   Architecture: MVC — models (`models.py`), views (`views.py`, `views_admin.py`, `views_finance.py`, `views_maintenance.py`, `views_manager.py`), database manager (`db_manager.py`)
*   Export: Strategy pattern (`exporters.py`) — CSV (stdlib) and PDF (`reportlab`)

## 2. Functional Requirements

<table>
  <thead>
    <tr>
      <th>Req ID</th>
      <th>Component</th>
      <th>Requirement Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>FR-01</td>
      <td>Authentication</td>
      <td>System shall validate username and password (salted SHA-256) against the staff table on login. Passwords are stored in SALT:HASH format; each account has a unique random salt.</td>
    </tr>
    <tr>
      <td>FR-02</td>
      <td>Authentication</td>
      <td>Invalid credentials shall display a generic error message; no specific reason disclosed (security).</td>
    </tr>
    <tr>
      <td>FR-03</td>
      <td>Authentication</td>
      <td>Empty username or password fields shall trigger a validation warning before login is attempted.</td>
    </tr>
    <tr>
      <td>FR-04</td>
      <td>Role Access</td>
      <td>Each user role shall be granted access only to features assigned to that role (RBAC). Each role loads a dedicated shell with only its permitted navigation items.</td>
    </tr>
    <tr>
      <td>FR-05</td>
      <td>Tenant Mgmt</td>
      <td>Front Desk staff shall register new tenants with: NI number (unique), first name, last name, phone, email, occupation, date of birth, emergency contact (name and phone), two references (name, phone, email each), and notes.</td>
    </tr>
    <tr>
      <td>FR-06</td>
      <td>Tenant Mgmt</td>
      <td>The system shall reject duplicate NI numbers with a specific error message; no record shall be inserted.</td>
    </tr>
    <tr>
      <td>FR-07</td>
      <td>Tenant Mgmt</td>
      <td>Front Desk staff shall be able to update existing tenant records via the tenant detail view.</td>
    </tr>
    <tr>
      <td>FR-08</td>
      <td>Tenant Mgmt</td>
      <td>The system shall track each tenant's lease agreements, payment history, maintenance requests, and complaints, accessible from the apartment detail window.</td>
    </tr>
    <tr>
      <td>FR-09</td>
      <td>Apartment Mgmt</td>
      <td>Administrator shall register apartments with: unit number, location (city), type, monthly rent, bedrooms, bathrooms, floor, size (sqft), furnished flag, and parking flag.</td>
    </tr>
    <tr>
      <td>FR-10</td>
      <td>Apartment Mgmt</td>
      <td>Newly registered apartments shall default to status 'Available'.</td>
    </tr>
    <tr>
      <td>FR-11</td>
      <td>Apartment Mgmt</td>
      <td>Administrator shall only be able to manage apartments at their assigned location.</td>
    </tr>
    <tr>
      <td>FR-12</td>
      <td>Apartment Mgmt</td>
      <td>Clicking any apartment card shall open a tabbed detail window showing: Overview, Lease &amp; Tenant, Payments, Maintenance, and Complaints.</td>
    </tr>
    <tr>
      <td>FR-13</td>
      <td>Lease Mgmt</td>
      <td>Administrator shall create a lease by selecting a tenant, an Available apartment, start date, end date, monthly rent, and deposit amount.</td>
    </tr>
    <tr>
      <td>FR-14</td>
      <td>Lease Mgmt</td>
      <td>Creating a lease shall update the apartment status to 'Occupied' and set lease status to 'Active'.</td>
    </tr>
    <tr>
      <td>FR-15</td>
      <td>Lease Mgmt</td>
      <td>Administrator shall view all lease agreements with expiry date filtering (30 / 60 / 90 / 180 days / all active) and be able to mark leases as Expired.</td>
    </tr>
    <tr>
      <td>FR-16</td>
      <td>Early Termination</td>
      <td>A tenant may leave before contract end: 1 month (30 days) notice required; penalty = 5% of monthly rent. Front Desk staff initiate the request via the Early Termination dialog on the Lease &amp; Tenant tab.</td>
    </tr>
    <tr>
      <td>FR-17</td>
      <td>Early Termination</td>
      <td>Early termination shall: set lease status to Terminated, revert apartment to 'Available', and create a Pending invoice for the 5% penalty amount.</td>
    </tr>
    <tr>
      <td>FR-18</td>
      <td>Payments</td>
      <td>Finance Manager shall view all payment records with reference number, tenant, unit, city, due date, amount due, amount paid, and status (Pending / Overdue / Paid).</td>
    </tr>
    <tr>
      <td>FR-19</td>
      <td>Payments</td>
      <td>Finance Manager shall mark a Pending or Overdue invoice as Paid by selecting a payment method and date; a printable receipt shall be generated.</td>
    </tr>
    <tr>
      <td>FR-20</td>
      <td>Payments</td>
      <td>Finance Manager shall create invoices against any active lease, with amount, due date, and description.</td>
    </tr>
    <tr>
      <td>FR-21</td>
      <td>Payments</td>
      <td>System shall flag overdue invoices: Pending invoices past their due_date shall be updated to 'Overdue' when Finance Manager triggers the check.</td>
    </tr>
    <tr>
      <td>FR-22</td>
      <td>Payments</td>
      <td>Overdue tenants shall receive a simulated notification when Finance Manager clicks "Notify" on a late payment record.</td>
    </tr>
    <tr>
      <td>FR-23</td>
      <td>Reporting</td>
      <td>Finance Manager shall view a financial summary showing: total billed, collected, pending, and overdue amounts, plus a per-city breakdown and monthly revenue trend (last 6 months).</td>
    </tr>
    <tr>
      <td>FR-24</td>
      <td>Reporting</td>
      <td>Manager shall generate occupancy reports by city with stacked bar chart and city-level breakdown table.</td>
    </tr>
    <tr>
      <td>FR-25</td>
      <td>Reporting</td>
      <td>Manager shall produce cross-city performance reports comparing KPIs: occupancy %, revenue, overdue, maintenance cost, open jobs, staff count, and net revenue.</td>
    </tr>
    <tr>
      <td>FR-26</td>
      <td>Maintenance</td>
      <td>Front Desk staff and Maintenance Staff shall log maintenance requests with: apartment, title, description, category, and priority (Low / Medium / High / Urgent); status defaults to 'Open'.</td>
    </tr>
    <tr>
      <td>FR-27</td>
      <td>Maintenance</td>
      <td>Maintenance Staff shall view the full job queue with status and priority filters, and click any row to open a detailed job management window.</td>
    </tr>
    <tr>
      <td>FR-28</td>
      <td>Maintenance</td>
      <td>Maintenance Staff shall assign a worker from the roster, set a scheduled date, log resolution notes, cost, and time taken; status shall progress Open → In Progress → Resolved → Closed.</td>
    </tr>
    <tr>
      <td>FR-29</td>
      <td>Maintenance</td>
      <td>Maintenance Staff shall manage a worker roster with name, phone, email, specialties, hourly rate, and availability status.</td>
    </tr>
    <tr>
      <td>FR-30</td>
      <td>Maintenance</td>
      <td>Maintenance Staff shall maintain a job-type catalogue with category, name, typical cost range, typical hours, and required specialty.</td>
    </tr>
    <tr>
      <td>FR-31</td>
      <td>Complaints</td>
      <td>Front Desk staff shall log tenant complaints with: title, description, category, and linked apartment; status defaults to 'Open'.</td>
    </tr>
    <tr>
      <td>FR-32</td>
      <td>Complaints</td>
      <td>Complaints shall be viewable in the apartment detail window (Complaints tab) and resolvable with resolution notes.</td>
    </tr>
    <tr>
      <td>FR-33</td>
      <td>Multi-City</td>
      <td>System shall support operations across four locations: Bristol, Cardiff, London, and Manchester, with data automatically seeded on first launch.</td>
    </tr>
    <tr>
      <td>FR-34</td>
      <td>Multi-City</td>
      <td>Manager shall be able to register new office locations (cities) within PAMS via the Expand Business screen.</td>
    </tr>
    <tr>
      <td>FR-35</td>
      <td>Export</td>
      <td>Every major table view shall provide Export CSV and Export PDF buttons that write the current (filtered) data to a user-chosen file path.</td>
    </tr>
    <tr>
      <td>FR-36</td>
      <td>Export</td>
      <td>CSV export shall sanitise leading formula characters (=, +, -, @) to prevent CSV injection in spreadsheet applications.</td>
    </tr>
    <tr>
      <td>FR-37</td>
      <td>Staff Mgmt</td>
      <td>Administrator shall create, edit, activate, and deactivate staff accounts at their location; password reset shall be supported.</td>
    </tr>
  </tbody>
</table>

# 3. Non-Functional Requirements

<table>
  <thead>
    <tr>
      <th>Req ID</th>
      <th>Category</th>
      <th>Requirement</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>NFR-01</td>
      <td>Security</td>
      <td>Role-based access control: each role loads a dedicated shell; no features from other roles are accessible.</td>
    </tr>
    <tr>
      <td>NFR-02</td>
      <td>Security</td>
      <td>Passwords shall be stored as salted SHA-256 hashes in SALT:HASH format. Each account receives a unique 16-byte random salt so that identical passwords produce different stored values, defeating rainbow-table attacks. Plaintext passwords are never persisted.</td>
    </tr>
    <tr>
      <td>NFR-03</td>
      <td>Security</td>
      <td>All SQL queries shall use parameterised inputs to protect against SQL injection attacks.</td>
    </tr>
    <tr>
      <td>NFR-04</td>
      <td>Security</td>
      <td>CSV export shall sanitise formula-injection characters; PDF export filenames shall not contain path-traversal sequences.</td>
    </tr>
    <tr>
      <td>NFR-05</td>
      <td>Usability</td>
      <td>The GUI shall use a consistent light theme with a clear sidebar navigation and readable typography across all screens.</td>
    </tr>
    <tr>
      <td>NFR-06</td>
      <td>Usability</td>
      <td>All error and success messages shall be displayed in clear dialog boxes visible to the user; no silent failures.</td>
    </tr>
    <tr>
      <td>NFR-07</td>
      <td>Scalability</td>
      <td>Code shall be split into role-specific view modules following MVC principles, so new roles or screens can be added independently.</td>
    </tr>
    <tr>
      <td>NFR-08</td>
      <td>Scalability</td>
      <td>The export system shall be open for extension: new formats are added by subclassing Exporter and registering in _REGISTRY without modifying call sites.</td>
    </tr>
    <tr>
      <td>NFR-09</td>
      <td>Reliability</td>
      <td>All form inputs shall be validated before any database operations are performed; invalid data shall never reach the database.</td>
    </tr>
    <tr>
      <td>NFR-14</td>
      <td>Reliability</td>
      <td>NI numbers shall match the UK format: 2 uppercase letters, 6 digits, 1 uppercase letter (regex: [A-Z]{2}\d{6}[A-Z]). UK phone numbers shall match: leading 0 or +44 followed by 9–10 digits, with spaces and hyphens permitted. Both are validated in the Register Tenant wizard before any database write.</td>
    </tr>
    <tr>
      <td>NFR-10</td>
      <td>Reliability</td>
      <td>The database schema shall be created automatically on first launch; no manual setup scripts are required.</td>
    </tr>
    <tr>
      <td>NFR-11</td>
      <td>Portability</td>
      <td>Application shall run on Python 3.10+ with only tkinter (stdlib) required for core functionality; reportlab is optional for PDF export.</td>
    </tr>
    <tr>
      <td>NFR-12</td>
      <td>Data Integrity</td>
      <td>The database shall enforce unique constraints (e.g., NI number, username), foreign key relationships, and referential integrity across all 11 tables.</td>
    </tr>
    <tr>
      <td>NFR-13</td>
      <td>Performance</td>
      <td>Data views shall load within an acceptable response time under normal load with the seeded demo dataset.</td>
    </tr>
  </tbody>
</table>

# 4. Constraints and Assumptions

## 4.1 Constraints

* The application must be a desktop application; web-based development is not permitted per the assessment brief.
* No live payment processing system is required; billing is emulated through invoice generation.
* The system must run on Python 3.10+ with standard library packages; reportlab is an optional dependency for PDF export only.
* Each Administrator is constrained to manage only their assigned city's data.
* The Manager role has cross-city read access; write operations (e.g., registering new cities) are the only write action available to a Manager.

## 4.2 Assumptions

* All users will access the system from a machine with Python 3.10+ installed.
* The database (`property_management.db`) is local to the machine; no networked database server is required.
* Demo data is pre-seeded automatically on first launch for testing and demonstration purposes.
* Date validation for lease start/end dates is enforced at the application level.
* The system does not need to integrate with external APIs (e.g., payment gateways, email services).

## 5. Requirement Traceability Summary

The requirements in this document map directly to the use case diagram (FR-01 to FR-37) and should be cross-checked against all UML diagrams produced by the team. The table below provides a high-level traceability summary by component.

<table>
  <thead>
    <tr>
      <th>Component</th>
      <th>Requirement IDs</th>
      <th>Responsible Role(s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Authentication</td>
      <td>FR-01, FR-02, FR-03, FR-04</td>
      <td>All roles</td>
    </tr>
    <tr>
      <td>Tenant Management</td>
      <td>FR-05, FR-06, FR-07, FR-08</td>
      <td>Front Desk</td>
    </tr>
    <tr>
      <td>Apartment Management</td>
      <td>FR-09, FR-10, FR-11, FR-12</td>
      <td>Administrator</td>
    </tr>
    <tr>
      <td>Lease Management</td>
      <td>FR-13, FR-14, FR-15</td>
      <td>Front Desk</td>
    </tr>
    <tr>
      <td>Early Termination</td>
      <td>FR-16, FR-17</td>
      <td>Front Desk</td>
    </tr>
    <tr>
      <td>Payments &amp; Billing</td>
      <td>FR-18, FR-19, FR-20, FR-21, FR-22</td>
      <td>Finance Manager</td>
    </tr>
    <tr>
      <td>Reporting</td>
      <td>FR-23, FR-24, FR-25</td>
      <td>Finance Manager, Manager, Administator</td>
    </tr>
    <tr>
      <td>Maintenance</td>
      <td>FR-26, FR-27, FR-28, FR-29, FR-30</td>
      <td>Front Desk, Maintenance Staff</td>
    </tr>
    <tr>
      <td>Complaints</td>
      <td>FR-31, FR-32</td>
      <td>Front Desk</td>
    </tr>
    <tr>
      <td>Multi-City Operations</td>
      <td>FR-33, FR-34</td>
      <td>Manager</td>
    </tr>
    <tr>
      <td>Export</td>
      <td>FR-35, FR-36</td>
      <td>All roles</td>
    </tr>
    <tr>
      <td>Staff Management</td>
      <td>FR-37</td>
      <td>Administrator, Management</td>
    </tr>
  </tbody>
</table>
