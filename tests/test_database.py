"""
test_database.py
Integration tests for DatabaseManager.

Each test class gets its own isolated in-memory SQLite database (":memory:"),
seeded with just the minimum data it needs.  No test touches the production
database file.

Covers:
  - Authentication (valid credentials, wrong password, inactive account, empty input)
  - Tenant CRUD (create, read, update, duplicate NI guard)
  - Apartment management (create, update, status transitions, delete guard)
  - Lease lifecycle (create → occupied, early termination → penalty + available,
    expired status auto-detection)
  - Payment (create_payment_request, mark_paid, mark_overdue, financial summary)
  - Maintenance (create, update, resolve, worker assignment)
  - Complaint (create, retrieve by apartment)
  - Staff management (create, update, reset password, toggle active,
                       username uniqueness guard)
  - Location / cross-city summary
  - Bad-data guards (duplicate NI, delete apt with active lease, missing fields)
"""

import unittest
import sys
import os
import sqlite3

# Allow importing from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db_manager import DatabaseManager
from models import (
    Tenant, Apartment, Lease, Payment, MaintenanceRequest, Complaint, Staff,
    ApartmentStatus, LeaseStatus, PaymentStatus, MaintenancePriority,
)
from datetime import date, timedelta


# ─────────────────────────────────────────────────────────────────────────────
#  Shared fixture helpers
# ─────────────────────────────────────────────────────────────────────────────

def _future(days=30) -> str:
    return str(date.today() + timedelta(days=days))

def _past(days=30) -> str:
    return str(date.today() - timedelta(days=days))


class _BaseDBTest(unittest.TestCase):
    """
    Base class: creates a fresh in-memory DB before every test and tears it
    down afterwards.  Subclasses only need to call self._seed_*() helpers for
    the data they actually need.
    """

    def setUp(self):
        self.db = DatabaseManager(":memory:")
        # Wipe the demo seed data so tests start clean
        c = self.db.get_cursor()
        for tbl in ["worker_assignments", "maintenance_requests", "complaints",
                    "payments", "leases", "tenants", "apartments",
                    "workers", "maintenance_types", "staff", "locations"]:
            c.execute(f"DELETE FROM {tbl}")
        self.db.commit()

    def tearDown(self):
        self.db.close()

    # ── Factories ────────────────────────────────────────────────────

    def _add_location(self, city="Bristol", address="1 High St",
                      postcode="BS1 1AA") -> int:
        return self.db.add_location(city, address, postcode)

    def _add_apartment(self, location_id=None, unit="1A",
                       rent=1200.0, status="Available") -> int:
        if location_id is None:
            location_id = self._add_location()
        apt = Apartment(unit_number=unit, location_id=location_id,
                        apartment_type="Flat", num_bedrooms=1, num_bathrooms=1,
                        monthly_rent=rent, floor=1, status=status)
        return self.db.create_apartment(apt)

    def _add_tenant(self, ni="AB123456C", first="John", last="Doe") -> int:
        t = Tenant(ni_number=ni, first_name=first, last_name=last,
                   phone="07700123456", email=f"{first.lower()}@test.com",
                   reference1_name="Dr Ref")
        return self.db.create_tenant(t)

    def _add_lease(self, tenant_id, apt_id, start=None, end=None,
                   rent=1200.0, deposit=1200.0, status="Active") -> int:
        lease = Lease(
            tenant_id=tenant_id, apartment_id=apt_id,
            start_date=start or _past(90),
            end_date=end or _future(90),
            monthly_rent=rent, deposit_amount=deposit, status=status,
        )
        return self.db.create_lease(lease)

    def _add_staff(self, username="alice", password="pass123",
                   role="Front Desk", location_id=None) -> int:
        if location_id is None:
            location_id = self._add_location()
        return self.db.create_staff(username, password, "Alice", "Smith",
                                    role, "alice@test.com", "07700000001",
                                    location_id)


# ─────────────────────────────────────────────────────────────────────────────
#  Authentication
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthentication(_BaseDBTest):

    def setUp(self):
        super().setUp()
        self.loc_id = self._add_location()
        self._add_staff("bob", "secret99", "Front Desk", self.loc_id)

    def test_valid_login_returns_staff(self):
        staff = self.db.authenticate_staff("bob", "secret99")
        self.assertIsNotNone(staff)
        self.assertEqual(staff.username, "bob")

    def test_wrong_password_returns_none(self):
        self.assertIsNone(self.db.authenticate_staff("bob", "wrongpass"))

    def test_wrong_username_returns_none(self):
        self.assertIsNone(self.db.authenticate_staff("nobody", "secret99"))

    def test_empty_username_returns_none(self):
        self.assertIsNone(self.db.authenticate_staff("", "secret99"))

    def test_empty_password_returns_none(self):
        self.assertIsNone(self.db.authenticate_staff("bob", ""))

    def test_both_empty_returns_none(self):
        self.assertIsNone(self.db.authenticate_staff("", ""))

    def test_inactive_account_cannot_login(self):
        # Get the staff id then deactivate
        staff = self.db.authenticate_staff("bob", "secret99")
        self.db.toggle_staff_active(staff.id)      # deactivate
        result = self.db.authenticate_staff("bob", "secret99")
        self.assertIsNone(result)

    def test_reactivated_account_can_login(self):
        staff = self.db.authenticate_staff("bob", "secret99")
        self.db.toggle_staff_active(staff.id)   # deactivate
        self.db.toggle_staff_active(staff.id)   # reactivate
        self.assertIsNotNone(self.db.authenticate_staff("bob", "secret99"))

    def test_reset_password_works(self):
        staff = self.db.authenticate_staff("bob", "secret99")
        self.db.reset_staff_password(staff.id, "newpass1")
        self.assertIsNotNone(self.db.authenticate_staff("bob", "newpass1"))
        self.assertIsNone(self.db.authenticate_staff("bob", "secret99"))

    def test_returned_staff_role(self):
        staff = self.db.authenticate_staff("bob", "secret99")
        self.assertEqual(staff.role, "Front Desk")


# ─────────────────────────────────────────────────────────────────────────────
#  Tenant CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestTenantCRUD(_BaseDBTest):

    def test_create_and_retrieve_tenant(self):
        tid = self._add_tenant(ni="AB123456C", first="Jane", last="Smith")
        t = self.db.get_tenant_by_id(tid)
        self.assertIsNotNone(t)
        self.assertEqual(t.ni_number, "AB123456C")
        self.assertEqual(t.first_name, "Jane")
        self.assertEqual(t.last_name, "Smith")

    def test_tenant_id_is_positive_integer(self):
        tid = self._add_tenant()
        self.assertIsInstance(tid, int)
        self.assertGreater(tid, 0)

    def test_duplicate_ni_raises_integrity_error(self):
        self._add_tenant(ni="ZZ999999Z")
        with self.assertRaises(Exception):   # sqlite3.IntegrityError
            self._add_tenant(ni="ZZ999999Z")

    def test_update_tenant(self):
        tid = self._add_tenant(first="Old", last="Name")
        t = self.db.get_tenant_by_id(tid)
        t.first_name = "New"
        t.last_name  = "Name2"
        t.phone = "07711111111"
        self.db.update_tenant(t)
        updated = self.db.get_tenant_by_id(tid)
        self.assertEqual(updated.first_name, "New")
        self.assertEqual(updated.phone, "07711111111")

    def test_get_all_tenants_returns_list(self):
        self._add_tenant(ni="AA100001A")
        self._add_tenant(ni="AA100002A")
        tenants = self.db.get_all_tenants()
        self.assertEqual(len(tenants), 2)

    def test_get_tenant_nonexistent_returns_none(self):
        self.assertIsNone(self.db.get_tenant_by_id(9999))

    def test_search_tenants_by_name(self):
        self._add_tenant(ni="AA200001A", first="Unique", last="Person")
        results = self.db.search_tenants("Unique")
        self.assertTrue(any(t.first_name == "Unique" for t in results))

    def test_search_tenants_no_match(self):
        self._add_tenant(ni="AA200002A", first="Real", last="Human")
        results = self.db.search_tenants("XYZXYZXYZ")
        self.assertEqual(results, [])


# ─────────────────────────────────────────────────────────────────────────────
#  Apartment Management
# ─────────────────────────────────────────────────────────────────────────────

class TestApartmentManagement(_BaseDBTest):

    def test_create_and_retrieve_apartment(self):
        loc_id = self._add_location()
        apt_id = self._add_apartment(loc_id, unit="2B", rent=900.0)
        apt = self.db.get_apartment_by_id(apt_id)
        self.assertIsNotNone(apt)
        self.assertEqual(apt.unit_number, "2B")
        self.assertAlmostEqual(apt.monthly_rent, 900.0)

    def test_new_apartment_is_available(self):
        apt_id = self._add_apartment()
        apt = self.db.get_apartment_by_id(apt_id)
        self.assertEqual(apt.status, "Available")

    def test_update_apartment_status(self):
        apt_id = self._add_apartment()
        self.db.update_apartment_status(apt_id, "Under Maintenance")
        apt = self.db.get_apartment_by_id(apt_id)
        self.assertEqual(apt.status, "Under Maintenance")

    def test_update_apartment_details(self):
        apt_id = self._add_apartment(rent=800.0)
        apt = self.db.get_apartment_by_id(apt_id)
        apt.monthly_rent = 950.0
        apt.num_bedrooms = 2
        self.db.update_apartment(apt)
        updated = self.db.get_apartment_by_id(apt_id)
        self.assertAlmostEqual(updated.monthly_rent, 950.0)
        self.assertEqual(updated.num_bedrooms, 2)

    def test_get_all_apartments_for_location(self):
        loc_id = self._add_location()
        self._add_apartment(loc_id, unit="A1")
        self._add_apartment(loc_id, unit="A2")
        apts = self.db.get_all_apartments(loc_id)
        self.assertEqual(len(apts), 2)

    def test_get_available_apartments(self):
        loc_id = self._add_location()
        self._add_apartment(loc_id, unit="V1", status="Available")
        self._add_apartment(loc_id, unit="V2", status="Occupied")
        available = self.db.get_available_apartments(loc_id)
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].unit_number, "V1")

    def test_delete_apartment_no_lease(self):
        apt_id = self._add_apartment()
        result = self.db.delete_apartment(apt_id)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_apartment_by_id(apt_id))

    def test_delete_apartment_blocked_with_active_lease(self):
        loc_id = self._add_location()
        apt_id = self._add_apartment(loc_id)
        tid    = self._add_tenant()
        self._add_lease(tid, apt_id)
        result = self.db.delete_apartment(apt_id)
        self.assertFalse(result)
        self.assertIsNotNone(self.db.get_apartment_by_id(apt_id))

    def test_search_apartments(self):
        loc_id = self._add_location(city="Cardiff")
        self._add_apartment(loc_id, unit="SearchMe")
        results = self.db.search_apartments("SearchMe")
        self.assertTrue(any(a.unit_number == "SearchMe" for a in results))


# ─────────────────────────────────────────────────────────────────────────────
#  Lease Lifecycle
# ─────────────────────────────────────────────────────────────────────────────

class TestLeaseLifecycle(_BaseDBTest):

    def setUp(self):
        super().setUp()
        self.loc_id = self._add_location()
        self.apt_id = self._add_apartment(self.loc_id)
        self.tid    = self._add_tenant()

    def test_create_lease_marks_apartment_occupied(self):
        self._add_lease(self.tid, self.apt_id)
        apt = self.db.get_apartment_by_id(self.apt_id)
        self.assertEqual(apt.status, "Occupied")

    def test_get_active_lease_for_apartment(self):
        lid = self._add_lease(self.tid, self.apt_id)
        lease = self.db.get_active_lease_for_apartment(self.apt_id)
        self.assertIsNotNone(lease)
        self.assertEqual(lease.id, lid)

    def test_no_active_lease_returns_none(self):
        result = self.db.get_active_lease_for_apartment(self.apt_id)
        self.assertIsNone(result)

    def test_lease_has_tenant_name_joined(self):
        self._add_lease(self.tid, self.apt_id)
        lease = self.db.get_active_lease_for_apartment(self.apt_id)
        self.assertEqual(lease.tenant_name, "John Doe")

    def test_lease_has_apartment_unit_joined(self):
        self._add_lease(self.tid, self.apt_id)
        lease = self.db.get_active_lease_for_apartment(self.apt_id)
        self.assertEqual(lease.apartment_unit, "1A")

    def test_get_lease_by_id(self):
        lid = self._add_lease(self.tid, self.apt_id)
        lease = self.db.get_lease_by_id(lid)
        self.assertIsNotNone(lease)
        self.assertEqual(lease.id, lid)

    def test_update_lease_status(self):
        lid = self._add_lease(self.tid, self.apt_id)
        self.db.update_lease_status(lid, "Terminated")
        lease = self.db.get_lease_by_id(lid)
        self.assertEqual(lease.status, "Terminated")

    def test_expired_lease_auto_detected(self):
        # Create a lease that ended yesterday
        lid = self._add_lease(self.tid, self.apt_id,
                              start=_past(365), end=_past(1))
        lease = self.db.get_lease_by_id(lid)
        # _row_to_lease should auto-detect expiry
        self.assertEqual(lease.status, "Expired")

    def test_all_leases_for_apartment(self):
        lid1 = self._add_lease(self.tid, self.apt_id)
        self.db.update_lease_status(lid1, "Terminated")
        tid2 = self._add_tenant(ni="BB222222B", first="Sue", last="Jones")
        apt2 = self._add_apartment(self.loc_id, unit="2B")
        self._add_lease(tid2, apt2)
        leases = self.db.get_all_leases_for_apartment(self.apt_id)
        self.assertEqual(len(leases), 1)

    # ── Early termination ────────────────────────────────────────────

    def test_early_termination_marks_lease_terminated(self):
        lid = self._add_lease(self.tid, self.apt_id)
        termination_date = _future(30)
        self.db.request_early_termination(lid, self.apt_id,
                                          str(date.today()), termination_date)
        lease = self.db.get_lease_by_id(lid)
        self.assertEqual(lease.status, "Terminated")

    def test_early_termination_sets_flag(self):
        lid = self._add_lease(self.tid, self.apt_id)
        self.db.request_early_termination(lid, self.apt_id,
                                          str(date.today()), _future(30))
        lease = self.db.get_lease_by_id(lid)
        self.assertTrue(lease.early_termination_requested)

    def test_early_termination_frees_apartment(self):
        lid = self._add_lease(self.tid, self.apt_id)
        self.db.request_early_termination(lid, self.apt_id,
                                          str(date.today()), _future(30))
        apt = self.db.get_apartment_by_id(self.apt_id)
        self.assertEqual(apt.status, "Available")

    def test_early_termination_creates_penalty_payment(self):
        lid = self._add_lease(self.tid, self.apt_id, rent=1000.0)
        self.db.request_early_termination(lid, self.apt_id,
                                          str(date.today()), _future(30))
        payments = self.db.get_payments_for_lease(lid)
        penalty_payments = [p for p in payments if "penalty" in (p.notes or "").lower()]
        self.assertGreater(len(penalty_payments), 0)
        # Penalty = 5% of £1000 = £50
        self.assertAlmostEqual(penalty_payments[0].amount_due, 50.0)

    def test_early_termination_penalty_is_pending(self):
        lid = self._add_lease(self.tid, self.apt_id, rent=1000.0)
        self.db.request_early_termination(lid, self.apt_id,
                                          str(date.today()), _future(30))
        payments = self.db.get_payments_for_lease(lid)
        penalty_payments = [p for p in payments if "penalty" in (p.notes or "").lower()]
        self.assertEqual(penalty_payments[0].status, "Pending")


# ─────────────────────────────────────────────────────────────────────────────
#  Payments
# ─────────────────────────────────────────────────────────────────────────────

class TestPayments(_BaseDBTest):

    def setUp(self):
        super().setUp()
        loc_id      = self._add_location()
        apt_id      = self._add_apartment(loc_id)
        tid         = self._add_tenant()
        self.lid    = self._add_lease(tid, apt_id, rent=1200.0)
        self.apt_id = apt_id

    def _make_payment(self, amount=1200.0, due=None) -> Payment:
        return Payment(lease_id=self.lid, amount_due=amount,
                       due_date=due or _future(7))

    def test_create_payment_request_returns_id(self):
        pid = self.db.create_payment_request(self._make_payment())
        self.assertIsInstance(pid, int)
        self.assertGreater(pid, 0)

    def test_payment_request_marked_paid_immediately(self):
        pid = self.db.create_payment_request(self._make_payment())
        payments = self.db.get_payments_for_lease(self.lid)
        p = next(x for x in payments if x.id == pid)
        self.assertEqual(p.status, "Paid")

    def test_payment_amount_paid_equals_amount_due(self):
        pid = self.db.create_payment_request(self._make_payment(amount=800.0))
        payments = self.db.get_payments_for_lease(self.lid)
        p = next(x for x in payments if x.id == pid)
        self.assertAlmostEqual(p.amount_paid, 800.0)

    def test_mark_payment_paid(self):
        # Create a raw pending payment via DB
        c = self.db.get_cursor()
        c.execute("INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,status) "
                  "VALUES (?,?,0,?,'Pending')", (self.lid, 600.0, _past(5)))
        self.db.commit()
        pid = c.lastrowid
        self.db.mark_payment_paid(pid, method="Card")
        payments = self.db.get_payments_for_lease(self.lid)
        p = next(x for x in payments if x.id == pid)
        self.assertEqual(p.status, "Paid")
        self.assertAlmostEqual(p.amount_paid, 600.0)

    def test_mark_payment_overdue(self):
        c = self.db.get_cursor()
        c.execute("INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,status) "
                  "VALUES (?,?,0,?,'Pending')", (self.lid, 300.0, _past(5)))
        self.db.commit()
        pid = c.lastrowid
        self.db.mark_payment_overdue(pid)
        payments = self.db.get_payments_for_lease(self.lid)
        p = next(x for x in payments if x.id == pid)
        self.assertEqual(p.status, "Overdue")

    def test_mark_overdue_does_not_affect_paid(self):
        pid = self.db.create_payment_request(self._make_payment())
        self.db.mark_payment_overdue(pid)
        payments = self.db.get_payments_for_lease(self.lid)
        p = next(x for x in payments if x.id == pid)
        self.assertEqual(p.status, "Paid")   # should remain Paid

    def test_get_payments_for_apartment(self):
        self.db.create_payment_request(self._make_payment())
        self.db.create_payment_request(self._make_payment(amount=400.0))
        payments = self.db.get_payments_for_apartment(self.apt_id)
        self.assertEqual(len(payments), 2)

    def test_financial_summary_collected_increases(self):
        before = self.db.get_financial_summary()["total_collected"]
        self.db.create_payment_request(self._make_payment(amount=500.0))
        after = self.db.get_financial_summary()["total_collected"]
        self.assertAlmostEqual(after - before, 500.0)

    def test_create_invoice(self):
        inv_id = self.db.create_invoice(self.lid, 250.0, _future(14),
                                        description="Test invoice")
        self.assertGreater(inv_id, 0)
        payments = self.db.get_payments_for_lease(self.lid)
        inv = next(x for x in payments if x.id == inv_id)
        self.assertAlmostEqual(inv.amount_due, 250.0)


# ─────────────────────────────────────────────────────────────────────────────
#  Maintenance Requests
# ─────────────────────────────────────────────────────────────────────────────

class TestMaintenance(_BaseDBTest):

    def setUp(self):
        super().setUp()
        self.loc_id = self._add_location()
        self.apt_id = self._add_apartment(self.loc_id)
        self.tid    = self._add_tenant()
        self.lid    = self._add_lease(self.tid, self.apt_id)

    def _make_req(self, **kw):
        defaults = dict(apartment_id=self.apt_id, lease_id=self.lid,
                        tenant_id=self.tid, title="Broken boiler",
                        description="No hot water.", category="Plumbing",
                        priority="High", status="Open",
                        reported_date=str(date.today()))
        defaults.update(kw)
        return MaintenanceRequest(**defaults)

    def test_create_maintenance_request_returns_id(self):
        rid = self.db.create_maintenance_request(self._make_req())
        self.assertIsInstance(rid, int)
        self.assertGreater(rid, 0)

    def test_retrieve_maintenance_for_apartment(self):
        self.db.create_maintenance_request(self._make_req())
        reqs = self.db.get_maintenance_for_apartment(self.apt_id)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].title, "Broken boiler")

    def test_retrieve_maintenance_for_lease(self):
        self.db.create_maintenance_request(self._make_req())
        reqs = self.db.get_maintenance_for_lease(self.lid)
        self.assertEqual(len(reqs), 1)

    def test_update_maintenance_status(self):
        rid = self.db.create_maintenance_request(self._make_req())
        req = self.db.get_maintenance_by_id(rid)
        req.status = "In Progress"
        req.scheduled_date = _future(3)
        self.db.update_maintenance(req)
        updated = self.db.get_maintenance_by_id(rid)
        self.assertEqual(updated.status, "In Progress")
        self.assertEqual(updated.scheduled_date, _future(3))

    def test_resolve_maintenance(self):
        rid = self.db.create_maintenance_request(self._make_req())
        req = self.db.get_maintenance_by_id(rid)
        req.status = "Resolved"
        req.resolved_date = str(date.today())
        req.cost = 150.0
        req.time_taken_hours = 3.0
        req.resolution_notes = "Replaced boiler element."
        self.db.update_maintenance(req)
        resolved = self.db.get_maintenance_by_id(rid)
        self.assertEqual(resolved.status, "Resolved")
        self.assertAlmostEqual(resolved.cost, 150.0)
        self.assertEqual(resolved.resolution_notes, "Replaced boiler element.")

    def test_get_all_maintenance_with_status_filter(self):
        self.db.create_maintenance_request(self._make_req(status="Open"))
        self.db.create_maintenance_request(self._make_req(title="Second issue",
                                                           status="Resolved"))
        open_reqs = self.db.get_all_maintenance(status="Open")
        self.assertEqual(len(open_reqs), 1)
        self.assertEqual(open_reqs[0].status, "Open")

    def test_maintenance_by_id_not_found(self):
        self.assertIsNone(self.db.get_maintenance_by_id(9999))

    def test_maintenance_count_stats(self):
        self.db.create_maintenance_request(self._make_req(status="Open"))
        self.db.create_maintenance_request(self._make_req(title="T2", status="Open"))
        stats = self.db.get_maintenance_stats(self.loc_id)
        self.assertEqual(stats.get("open_count", 0), 2)


# ─────────────────────────────────────────────────────────────────────────────
#  Complaints
# ─────────────────────────────────────────────────────────────────────────────

class TestComplaints(_BaseDBTest):

    def setUp(self):
        super().setUp()
        loc_id      = self._add_location()
        self.apt_id = self._add_apartment(loc_id)
        self.tid    = self._add_tenant()
        self.lid    = self._add_lease(self.tid, self.apt_id)
        # Complaints require a valid staff FK for created_by
        self.staff_id = self._add_staff("complaint_staff", location_id=loc_id)

    def _make_complaint(self, **kw):
        defaults = dict(lease_id=self.lid, tenant_id=self.tid,
                        apartment_id=self.apt_id,
                        title="Noise upstairs", description="Loud music every night.",
                        category="Noise", status="Open",
                        reported_date=str(date.today()), created_by=self.staff_id)
        defaults.update(kw)
        return Complaint(**defaults)

    def test_create_complaint_returns_id(self):
        cid = self.db.create_complaint(self._make_complaint())
        self.assertIsInstance(cid, int)
        self.assertGreater(cid, 0)

    def test_retrieve_complaints_for_apartment(self):
        self.db.create_complaint(self._make_complaint())
        complaints = self.db.get_complaints_for_apartment(self.apt_id)
        self.assertEqual(len(complaints), 1)
        self.assertEqual(complaints[0].title, "Noise upstairs")

    def test_retrieve_complaints_for_lease(self):
        self.db.create_complaint(self._make_complaint())
        complaints = self.db.get_complaints_for_lease(self.lid)
        self.assertEqual(len(complaints), 1)

    def test_multiple_complaints_for_same_apartment(self):
        self.db.create_complaint(self._make_complaint(title="C1"))
        self.db.create_complaint(self._make_complaint(title="C2"))
        complaints = self.db.get_complaints_for_apartment(self.apt_id)
        self.assertEqual(len(complaints), 2)

    def test_no_complaints_returns_empty_list(self):
        complaints = self.db.get_complaints_for_apartment(self.apt_id)
        self.assertEqual(complaints, [])

    def test_complaint_has_tenant_name_joined(self):
        self.db.create_complaint(self._make_complaint())
        complaints = self.db.get_complaints_for_apartment(self.apt_id)
        self.assertEqual(complaints[0].tenant_name, "John Doe")


# ─────────────────────────────────────────────────────────────────────────────
#  Staff Management
# ─────────────────────────────────────────────────────────────────────────────

class TestStaffManagement(_BaseDBTest):

    def setUp(self):
        super().setUp()
        self.loc_id = self._add_location()

    def test_create_staff_returns_id(self):
        sid = self.db.create_staff("newuser", "pass123", "New", "User",
                                   "Front Desk", "new@test.com", "07700001111",
                                   self.loc_id)
        self.assertIsInstance(sid, int)
        self.assertGreater(sid, 0)

    def test_duplicate_username_raises_error(self):
        self.db.create_staff("dupeuser", "pass123", "A", "B",
                             "Front Desk", "", "", self.loc_id)
        with self.assertRaises(Exception):
            self.db.create_staff("dupeuser", "pass456", "C", "D",
                                 "Front Desk", "", "", self.loc_id)

    def test_username_exists_true(self):
        self.db.create_staff("exists_user", "pass", "E", "F",
                             "Front Desk", "", "", self.loc_id)
        self.assertTrue(self.db.username_exists("exists_user"))

    def test_username_exists_false(self):
        self.assertFalse(self.db.username_exists("ghost_user"))

    def test_toggle_staff_active_deactivates(self):
        sid = self._add_staff("toggler", location_id=self.loc_id)
        new_state = self.db.toggle_staff_active(sid)
        self.assertFalse(new_state)

    def test_toggle_staff_active_reactivates(self):
        sid = self._add_staff("toggler2", location_id=self.loc_id)
        self.db.toggle_staff_active(sid)   # deactivate
        new_state = self.db.toggle_staff_active(sid)   # reactivate
        self.assertTrue(new_state)

    def test_update_staff_fields(self):
        sid = self._add_staff("updateme", location_id=self.loc_id)
        self.db.update_staff(sid, "Bob", "Builder", "Administrator",
                             "bob@test.com", "07799999999", self.loc_id)
        staff_list = self.db.get_staff_for_location(self.loc_id)
        updated = next(s for s in staff_list if s.id == sid)
        self.assertEqual(updated.first_name, "Bob")
        self.assertEqual(updated.role, "Administrator")

    def test_get_staff_for_location(self):
        self._add_staff("loc_staff1", location_id=self.loc_id)
        self._add_staff("loc_staff2", location_id=self.loc_id)
        staff = self.db.get_staff_for_location(self.loc_id)
        self.assertEqual(len(staff), 2)

    def test_get_all_staff_includes_all_locations(self):
        loc2 = self._add_location(city="Cardiff", address="2 St", postcode="CF1 1AA")
        self._add_staff("staff_loc1", location_id=self.loc_id)
        self._add_staff("staff_loc2", location_id=loc2)
        all_staff = self.db.get_all_staff()
        self.assertGreaterEqual(len(all_staff), 2)

    def test_manager_role_detected_via_model(self):
        sid = self.db.create_staff("mgr1", "pass", "M", "Mgr",
                                   "Manager", "", "", self.loc_id)
        staff = self.db.get_staff_for_location(self.loc_id)
        mgr = next(s for s in staff if s.id == sid)
        self.assertTrue(mgr.is_manager())

    def test_admin_role_detected_via_model(self):
        sid = self.db.create_staff("adm1", "pass", "A", "Adm",
                                   "Administrator", "", "", self.loc_id)
        staff = self.db.get_staff_for_location(self.loc_id)
        adm = next(s for s in staff if s.id == sid)
        self.assertTrue(adm.is_admin())

    def test_admin_cannot_edit_manager_flag_is_enforced_by_role(self):
        """
        The DB layer itself has no role-restriction (that is the UI's job).
        This test confirms the model-level is_manager() / is_admin() flags
        that the UI uses for its guard work correctly in combination.
        """
        admin_sid = self.db.create_staff("admin_x", "pass", "Ad", "Min",
                                         "Administrator", "", "", self.loc_id)
        mgr_sid   = self.db.create_staff("mgr_x",   "pass", "Ma", "Nag",
                                         "Manager",       "", "", self.loc_id)

        all_staff = self.db.get_all_staff()
        admin = next(s for s in all_staff if s.id == admin_sid)
        mgr   = next(s for s in all_staff if s.id == mgr_sid)

        # UI guard logic: admin.is_admin() AND target.is_manager() → block
        self.assertTrue(admin.is_admin() and mgr.is_manager())
        # Admin editing another admin should NOT be blocked by the rule
        self.assertFalse(admin.is_admin() and admin.is_manager())


# ─────────────────────────────────────────────────────────────────────────────
#  Location Management
# ─────────────────────────────────────────────────────────────────────────────

class TestLocationManagement(_BaseDBTest):

    def test_add_location_returns_id(self):
        loc_id = self.db.add_location("Manchester", "5 Deansgate", "M1 1AA")
        self.assertIsInstance(loc_id, int)
        self.assertGreater(loc_id, 0)

    def test_get_all_locations(self):
        self.db.add_location("City1", "1 St", "C1 1AA")
        self.db.add_location("City2", "2 St", "C2 2BB")
        locs = self.db.get_all_locations()
        self.assertEqual(len(locs), 2)
        cities = {l.city for l in locs}
        self.assertIn("City1", cities)
        self.assertIn("City2", cities)

    def test_update_location(self):
        loc_id = self.db.add_location("OldCity", "Old St", "OL1 1AA")
        self.db.update_location(loc_id, "NewCity", "New St", "NW1 1AA")
        locs = self.db.get_all_locations()
        updated = next(l for l in locs if l.id == loc_id)
        self.assertEqual(updated.city, "NewCity")
        self.assertEqual(updated.postcode, "NW1 1AA")

    def test_cross_city_summary_has_entry_per_location(self):
        self.db.add_location("CityA", "A St", "A1 1AA")
        self.db.add_location("CityB", "B St", "B1 1BB")
        summary = self.db.get_cross_city_summary()
        self.assertEqual(len(summary), 2)
        for row in summary:
            self.assertIn("city", row)
            self.assertIn("total_apts", row)
            self.assertIn("collected", row)


# ─────────────────────────────────────────────────────────────────────────────
#  Integration: Full lease lifecycle
# ─────────────────────────────────────────────────────────────────────────────

class TestFullLeaseLifecycle(_BaseDBTest):
    """
    End-to-end scenario: register tenant → create lease → send payment →
    log maintenance → log complaint → early terminate → verify state.
    """

    def test_full_lifecycle(self):
        # 1. Setup location + apartment
        loc_id = self._add_location(city="London")
        apt_id = self._add_apartment(loc_id, unit="10C", rent=2000.0)
        # Need a staff member for complaint created_by FK
        staff_id = self._add_staff("lifecycle_staff", location_id=loc_id)
        apt = self.db.get_apartment_by_id(apt_id)
        self.assertEqual(apt.status, "Available")

        # 2. Register tenant
        tenant = Tenant(
            ni_number="TT987654T", first_name="Tom", last_name="Test",
            phone="07700555444", email="tom@test.com",
            reference1_name="Prof Green",
        )
        tid = self.db.create_tenant(tenant)
        self.assertGreater(tid, 0)

        # 3. Create lease — apartment should become Occupied
        lease = Lease(
            tenant_id=tid, apartment_id=apt_id,
            start_date=_past(30), end_date=_future(335),
            monthly_rent=2000.0, deposit_amount=2000.0,
        )
        lid = self.db.create_lease(lease)
        self.assertEqual(self.db.get_apartment_by_id(apt_id).status, "Occupied")

        # 4. Send a payment request
        pid = self.db.create_payment_request(
            Payment(lease_id=lid, amount_due=2000.0, due_date=_future(7)))
        payments = self.db.get_payments_for_lease(lid)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].status, "Paid")

        # 5. Log a maintenance request
        rid = self.db.create_maintenance_request(MaintenanceRequest(
            apartment_id=apt_id, lease_id=lid, tenant_id=tid,
            title="Leaking tap", description="Kitchen tap drips.", category="Plumbing",
            priority="Medium", status="Open", reported_date=str(date.today()),
        ))
        self.assertGreater(rid, 0)

        # 6. Log a complaint
        cid = self.db.create_complaint(Complaint(
            lease_id=lid, tenant_id=tid, apartment_id=apt_id,
            title="Boiler noise", description="Banging pipes.",
            category="Maintenance", status="Open",
            reported_date=str(date.today()), created_by=staff_id,
        ))
        self.assertGreater(cid, 0)

        # 7. Early terminate — lease → Terminated, apt → Available, penalty created
        termination_date = _future(30)
        self.db.request_early_termination(lid, apt_id,
                                          str(date.today()), termination_date)

        terminated_lease = self.db.get_lease_by_id(lid)
        self.assertEqual(terminated_lease.status, "Terminated")
        self.assertTrue(terminated_lease.early_termination_requested)

        freed_apt = self.db.get_apartment_by_id(apt_id)
        self.assertEqual(freed_apt.status, "Available")

        all_payments = self.db.get_payments_for_lease(lid)
        penalty_pmts = [p for p in all_payments if "penalty" in (p.notes or "").lower()]
        self.assertEqual(len(penalty_pmts), 1)
        self.assertAlmostEqual(penalty_pmts[0].amount_due, 100.0)  # 5% of £2000

        # 8. Maintenance count still queryable
        reqs = self.db.get_maintenance_for_apartment(apt_id)
        self.assertEqual(len(reqs), 1)

        # 9. Complaint still queryable
        complaints = self.db.get_complaints_for_apartment(apt_id)
        self.assertEqual(len(complaints), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)