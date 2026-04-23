"""
test_models.py
Unit tests for every model class in models.py.

Covers:
  - Default field values and dataclass construction
  - Property methods (full_name, display_name, annual_rent …)
  - Business-logic methods (is_available, is_overdue, early_termination_penalty …)
  - Edge-case / bad-data resilience (missing dates, zero amounts, empty strings)
  - Enum values match what the rest of the system expects
"""

import unittest
from datetime import date, timedelta
from models import (
    Location, Apartment, Tenant, Lease, Payment,
    MaintenanceRequest, Complaint, Staff,
    LeaseStatus, ApartmentStatus, MaintenanceStatus,
    MaintenancePriority, ComplaintStatus, PaymentStatus,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _future(days=30) -> str:
    return str(date.today() + timedelta(days=days))

def _past(days=30) -> str:
    return str(date.today() - timedelta(days=days))


# ─────────────────────────────────────────────────────────────────────────────
#  Enum Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEnums(unittest.TestCase):
    """Ensure enum string values are exactly what the DB and UI expect."""

    def test_lease_statuses(self):
        self.assertEqual(LeaseStatus.ACTIVE.value,     "Active")
        self.assertEqual(LeaseStatus.PENDING.value,    "Pending")
        self.assertEqual(LeaseStatus.TERMINATED.value, "Terminated")
        self.assertEqual(LeaseStatus.EXPIRED.value,    "Expired")

    def test_apartment_statuses(self):
        self.assertEqual(ApartmentStatus.AVAILABLE.value,   "Available")
        self.assertEqual(ApartmentStatus.OCCUPIED.value,    "Occupied")
        self.assertEqual(ApartmentStatus.MAINTENANCE.value, "Under Maintenance")

    def test_maintenance_statuses(self):
        self.assertEqual(MaintenanceStatus.OPEN.value,        "Open")
        self.assertEqual(MaintenanceStatus.IN_PROGRESS.value, "In Progress")
        self.assertEqual(MaintenanceStatus.RESOLVED.value,    "Resolved")
        self.assertEqual(MaintenanceStatus.CLOSED.value,      "Closed")

    def test_maintenance_priorities(self):
        self.assertEqual(MaintenancePriority.LOW.value,    "Low")
        self.assertEqual(MaintenancePriority.MEDIUM.value, "Medium")
        self.assertEqual(MaintenancePriority.HIGH.value,   "High")
        self.assertEqual(MaintenancePriority.URGENT.value, "Urgent")

    def test_complaint_statuses(self):
        self.assertEqual(ComplaintStatus.OPEN.value,         "Open")
        self.assertEqual(ComplaintStatus.UNDER_REVIEW.value, "Under Review")
        self.assertEqual(ComplaintStatus.RESOLVED.value,     "Resolved")
        self.assertEqual(ComplaintStatus.CLOSED.value,       "Closed")

    def test_payment_statuses(self):
        self.assertEqual(PaymentStatus.PENDING.value, "Pending")
        self.assertEqual(PaymentStatus.PAID.value,    "Paid")
        self.assertEqual(PaymentStatus.OVERDUE.value, "Overdue")
        self.assertEqual(PaymentStatus.PARTIAL.value, "Partial")


# ─────────────────────────────────────────────────────────────────────────────
#  Location
# ─────────────────────────────────────────────────────────────────────────────

class TestLocation(unittest.TestCase):

    def test_display_name(self):
        loc = Location(city="Bristol", address="1 High St")
        self.assertEqual(loc.display_name(), "Bristol — 1 High St")

    def test_default_country(self):
        loc = Location(city="Leeds", address="2 Low St", postcode="LS1 1AA")
        self.assertEqual(loc.country, "UK")

    def test_empty_city_display_name(self):
        loc = Location(city="", address="Unknown")
        self.assertEqual(loc.display_name(), " — Unknown")

    def test_id_defaults_none(self):
        loc = Location()
        self.assertIsNone(loc.id)


# ─────────────────────────────────────────────────────────────────────────────
#  Apartment
# ─────────────────────────────────────────────────────────────────────────────

class TestApartment(unittest.TestCase):

    def _make(self, **kw) -> Apartment:
        defaults = dict(unit_number="1A", monthly_rent=1000.0,
                        status=ApartmentStatus.AVAILABLE.value)
        defaults.update(kw)
        return Apartment(**defaults)

    def test_is_available_true(self):
        apt = self._make(status="Available")
        self.assertTrue(apt.is_available())

    def test_is_available_false_when_occupied(self):
        apt = self._make(status="Occupied")
        self.assertFalse(apt.is_available())

    def test_is_occupied_true(self):
        apt = self._make(status="Occupied")
        self.assertTrue(apt.is_occupied())

    def test_is_occupied_false_when_available(self):
        apt = self._make(status="Available")
        self.assertFalse(apt.is_occupied())

    def test_annual_rent(self):
        apt = self._make(monthly_rent=1200.0)
        self.assertAlmostEqual(apt.annual_rent(), 14400.0)

    def test_annual_rent_zero(self):
        apt = self._make(monthly_rent=0.0)
        self.assertEqual(apt.annual_rent(), 0.0)

    def test_default_status_is_available(self):
        apt = Apartment(unit_number="2B", monthly_rent=800.0)
        self.assertEqual(apt.status, ApartmentStatus.AVAILABLE.value)

    def test_default_furnished_false(self):
        apt = Apartment()
        self.assertFalse(apt.furnished)

    def test_default_parking_false(self):
        apt = Apartment()
        self.assertFalse(apt.parking)

    def test_under_maintenance_not_available(self):
        apt = self._make(status="Under Maintenance")
        self.assertFalse(apt.is_available())
        self.assertFalse(apt.is_occupied())

    def test_large_rent(self):
        apt = self._make(monthly_rent=999_999.99)
        self.assertAlmostEqual(apt.annual_rent(), 11_999_999.88, places=1)


# ─────────────────────────────────────────────────────────────────────────────
#  Tenant
# ─────────────────────────────────────────────────────────────────────────────

class TestTenant(unittest.TestCase):

    def _make(self, **kw) -> Tenant:
        defaults = dict(first_name="Jane", last_name="Doe",
                        ni_number="AB123456C", phone="07700123456", email="jane@test.com",
                        reference1_name="Dr Smith")
        defaults.update(kw)
        return Tenant(**defaults)

    def test_full_name(self):
        t = self._make(first_name="Jane", last_name="Doe")
        self.assertEqual(t.full_name, "Jane Doe")

    def test_full_name_single_word_last(self):
        t = self._make(first_name="Cher", last_name="")
        self.assertEqual(t.full_name, "Cher ")

    def test_has_references_true(self):
        t = self._make(reference1_name="Dr Brown")
        self.assertTrue(t.has_references())

    def test_has_references_false_when_empty(self):
        t = self._make(reference1_name="")
        self.assertFalse(t.has_references())

    def test_has_emergency_contact_true(self):
        t = self._make(emergency_contact_name="Bob", emergency_contact_phone="07700999888")
        self.assertTrue(t.has_emergency_contact())

    def test_has_emergency_contact_false_missing_phone(self):
        t = self._make(emergency_contact_name="Bob", emergency_contact_phone="")
        self.assertFalse(t.has_emergency_contact())

    def test_has_emergency_contact_false_missing_name(self):
        t = self._make(emergency_contact_name="", emergency_contact_phone="07700999888")
        self.assertFalse(t.has_emergency_contact())

    def test_default_notes_empty(self):
        t = Tenant()
        self.assertEqual(t.notes, "")

    def test_optional_date_of_birth_none(self):
        t = self._make()
        self.assertIsNone(t.date_of_birth)


# ─────────────────────────────────────────────────────────────────────────────
#  Lease
# ─────────────────────────────────────────────────────────────────────────────

class TestLease(unittest.TestCase):

    def _make(self, **kw) -> Lease:
        defaults = dict(tenant_id=1, apartment_id=1, monthly_rent=1200.0,
                        deposit_amount=1200.0, start_date=_past(90),
                        end_date=_future(90), status="Active")
        defaults.update(kw)
        return Lease(**defaults)

    # ── is_active ────────────────────────────────────────────────────

    def test_is_active_true(self):
        self.assertTrue(self._make(status="Active").is_active())

    def test_is_active_false_terminated(self):
        self.assertFalse(self._make(status="Terminated").is_active())

    def test_is_active_false_expired(self):
        self.assertFalse(self._make(status="Expired").is_active())

    # ── days_until_expiry ────────────────────────────────────────────

    def test_days_until_expiry_future(self):
        lease = self._make(end_date=_future(30))
        days = lease.days_until_expiry()
        # Allow ±1 day for test-run timing
        self.assertAlmostEqual(days, 30, delta=1)

    def test_days_until_expiry_past_is_negative(self):
        lease = self._make(end_date=_past(10))
        self.assertLess(lease.days_until_expiry(), 0)

    def test_days_until_expiry_no_end_date(self):
        lease = self._make(end_date=None)
        self.assertIsNone(lease.days_until_expiry())

    def test_days_until_expiry_invalid_date_string(self):
        lease = self._make(end_date="not-a-date")
        self.assertIsNone(lease.days_until_expiry())

    # ── is_expired ───────────────────────────────────────────────────

    def test_is_expired_true(self):
        lease = self._make(end_date=_past(1))
        self.assertTrue(lease.is_expired())

    def test_is_expired_false_future(self):
        lease = self._make(end_date=_future(1))
        self.assertFalse(lease.is_expired())

    def test_is_expired_no_end_date(self):
        lease = self._make(end_date=None)
        self.assertFalse(lease.is_expired())

    # ── early_termination_penalty ────────────────────────────────────

    def test_penalty_calculation(self):
        lease = self._make(monthly_rent=1000.0)
        self.assertAlmostEqual(lease.early_termination_penalty(), 50.0)

    def test_penalty_rate_is_five_percent(self):
        for rent in [500, 1200, 2000, 3750]:
            expected = round(rent * 0.05, 2)
            self.assertAlmostEqual(
                self._make(monthly_rent=float(rent)).early_termination_penalty(),
                expected,
                places=2,
                msg=f"Wrong penalty for rent={rent}"
            )

    def test_penalty_zero_rent(self):
        lease = self._make(monthly_rent=0.0)
        self.assertEqual(lease.early_termination_penalty(), 0.0)

    def test_required_notice_days_constant(self):
        lease = self._make()
        self.assertEqual(lease.REQUIRED_NOTICE_DAYS, 30)

    # ── default fields ───────────────────────────────────────────────

    def test_default_early_termination_requested_false(self):
        self.assertFalse(self._make().early_termination_requested)

    def test_default_tenant_name_empty(self):
        self.assertEqual(self._make().tenant_name, "")


# ─────────────────────────────────────────────────────────────────────────────
#  Payment
# ─────────────────────────────────────────────────────────────────────────────

class TestPayment(unittest.TestCase):

    def _make(self, **kw) -> Payment:
        defaults = dict(lease_id=1, amount_due=1200.0, amount_paid=0.0,
                        due_date=_future(10), status="Pending")
        defaults.update(kw)
        return Payment(**defaults)

    # ── balance_due ──────────────────────────────────────────────────

    def test_balance_due_full(self):
        p = self._make(amount_due=1200.0, amount_paid=0.0)
        self.assertAlmostEqual(p.balance_due(), 1200.0)

    def test_balance_due_partial(self):
        p = self._make(amount_due=1200.0, amount_paid=400.0)
        self.assertAlmostEqual(p.balance_due(), 800.0)

    def test_balance_due_fully_paid(self):
        p = self._make(amount_due=1200.0, amount_paid=1200.0)
        self.assertAlmostEqual(p.balance_due(), 0.0)

    def test_balance_due_overpaid(self):
        # Overpayment yields a negative balance — valid edge case
        p = self._make(amount_due=1000.0, amount_paid=1100.0)
        self.assertAlmostEqual(p.balance_due(), -100.0)

    # ── is_overdue ───────────────────────────────────────────────────

    def test_is_overdue_past_due_pending(self):
        p = self._make(due_date=_past(5), status="Pending")
        self.assertTrue(p.is_overdue())

    def test_is_overdue_false_future_due(self):
        p = self._make(due_date=_future(5), status="Pending")
        self.assertFalse(p.is_overdue())

    def test_is_overdue_false_when_paid(self):
        p = self._make(due_date=_past(5), status="Paid")
        self.assertFalse(p.is_overdue())

    def test_is_overdue_false_no_due_date(self):
        p = self._make(due_date=None, status="Pending")
        self.assertFalse(p.is_overdue())

    def test_is_overdue_invalid_date_string(self):
        p = self._make(due_date="not-a-date", status="Pending")
        self.assertFalse(p.is_overdue())

    # ── is_paid ──────────────────────────────────────────────────────

    def test_is_paid_true(self):
        self.assertTrue(self._make(status="Paid").is_paid())

    def test_is_paid_false_pending(self):
        self.assertFalse(self._make(status="Pending").is_paid())

    def test_is_paid_false_overdue(self):
        self.assertFalse(self._make(status="Overdue").is_paid())

    # ── default fields ───────────────────────────────────────────────

    def test_default_status_pending(self):
        p = Payment(lease_id=1, amount_due=100.0)
        self.assertEqual(p.status, PaymentStatus.PENDING.value)

    def test_default_reference_number_empty(self):
        p = Payment()
        self.assertEqual(p.reference_number, "")


# ─────────────────────────────────────────────────────────────────────────────
#  MaintenanceRequest
# ─────────────────────────────────────────────────────────────────────────────

class TestMaintenanceRequest(unittest.TestCase):

    def _make(self, **kw) -> MaintenanceRequest:
        defaults = dict(title="Boiler fault", category="Plumbing",
                        priority=MaintenancePriority.MEDIUM.value,
                        status=MaintenanceStatus.OPEN.value)
        defaults.update(kw)
        return MaintenanceRequest(**defaults)

    def test_is_open_true(self):
        self.assertTrue(self._make(status="Open").is_open())

    def test_is_open_false_in_progress(self):
        self.assertFalse(self._make(status="In Progress").is_open())

    def test_is_resolved_true_resolved(self):
        self.assertTrue(self._make(status="Resolved").is_resolved())

    def test_is_resolved_true_closed(self):
        self.assertTrue(self._make(status="Closed").is_resolved())

    def test_is_resolved_false_open(self):
        self.assertFalse(self._make(status="Open").is_resolved())

    def test_is_urgent_true(self):
        req = self._make(priority=MaintenancePriority.URGENT.value)
        self.assertTrue(req.is_urgent())

    def test_is_urgent_false_medium(self):
        req = self._make(priority=MaintenancePriority.MEDIUM.value)
        self.assertFalse(req.is_urgent())

    def test_default_priority_medium(self):
        req = MaintenanceRequest()
        self.assertEqual(req.priority, MaintenancePriority.MEDIUM.value)

    def test_default_status_open(self):
        req = MaintenanceRequest()
        self.assertEqual(req.status, MaintenanceStatus.OPEN.value)

    def test_default_cost_zero(self):
        req = MaintenanceRequest()
        self.assertEqual(req.cost, 0.0)

    def test_default_hours_zero(self):
        req = MaintenanceRequest()
        self.assertEqual(req.time_taken_hours, 0.0)

    def test_empty_title_allowed_by_model(self):
        # The model itself does not enforce non-empty title — that is UI validation
        req = MaintenanceRequest(title="")
        self.assertEqual(req.title, "")


# ─────────────────────────────────────────────────────────────────────────────
#  Complaint
# ─────────────────────────────────────────────────────────────────────────────

class TestComplaint(unittest.TestCase):

    def _make(self, **kw) -> Complaint:
        defaults = dict(title="Noise complaint", status=ComplaintStatus.OPEN.value)
        defaults.update(kw)
        return Complaint(**defaults)

    def test_is_open_true(self):
        self.assertTrue(self._make(status="Open").is_open())

    def test_is_open_false(self):
        self.assertFalse(self._make(status="Resolved").is_open())

    def test_is_resolved_resolved(self):
        self.assertTrue(self._make(status="Resolved").is_resolved())

    def test_is_resolved_closed(self):
        self.assertTrue(self._make(status="Closed").is_resolved())

    def test_is_resolved_false_under_review(self):
        self.assertFalse(self._make(status="Under Review").is_resolved())

    def test_default_status_open(self):
        c = Complaint()
        self.assertEqual(c.status, ComplaintStatus.OPEN.value)

    def test_default_resolution_notes_empty(self):
        c = Complaint()
        self.assertEqual(c.resolution_notes, "")


# ─────────────────────────────────────────────────────────────────────────────
#  Staff
# ─────────────────────────────────────────────────────────────────────────────

class TestStaff(unittest.TestCase):

    def _make(self, **kw) -> Staff:
        defaults = dict(username="alice", first_name="Alice", last_name="Smith",
                        role="Front Desk", is_active=True)
        defaults.update(kw)
        return Staff(**defaults)

    def test_full_name(self):
        s = self._make(first_name="Alice", last_name="Smith")
        self.assertEqual(s.full_name, "Alice Smith")

    def test_is_manager_true(self):
        s = self._make(role="Manager")
        self.assertTrue(s.is_manager())

    def test_is_manager_false(self):
        s = self._make(role="Front Desk")
        self.assertFalse(s.is_manager())

    def test_is_admin_true(self):
        s = self._make(role="Administrator")
        self.assertTrue(s.is_admin())

    def test_is_admin_false(self):
        s = self._make(role="Finance Manager")
        self.assertFalse(s.is_admin())

    def test_has_location_access_true(self):
        s = self._make(location_id=2)
        self.assertTrue(s.has_location_access(2))

    def test_has_location_access_false(self):
        s = self._make(location_id=2)
        self.assertFalse(s.has_location_access(3))

    def test_has_location_access_none_location(self):
        s = self._make(location_id=None)
        self.assertFalse(s.has_location_access(1))

    def test_default_is_active(self):
        s = Staff()
        self.assertTrue(s.is_active)

    def test_inactive_staff(self):
        s = self._make(is_active=False)
        self.assertFalse(s.is_active)


if __name__ == "__main__":
    unittest.main(verbosity=2)