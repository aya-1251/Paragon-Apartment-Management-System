"""
Unit tests for models.py — PAMS Group 17
Module: UFCF8S-30-2 Advanced Software Development

Tests all dataclasses and Enum types without touching the database.
Technique: black-box equivalence class + boundary value analysis.

Run from project root:
    pytest tests/test_models.py -v
"""
import pytest
from models import (
    LeaseStatus, ApartmentStatus, MaintenanceStatus, MaintenancePriority,
    ComplaintStatus, PaymentStatus,
    Location, Apartment, Tenant, Lease, Payment,
    MaintenanceRequest, Complaint, Staff,
)


# =============================================================================
# 1. Enum correctness
# =============================================================================

class TestLeaseStatusEnum:
    def test_active_value(self):
        assert LeaseStatus.ACTIVE.value == "Active"

    def test_pending_value(self):
        assert LeaseStatus.PENDING.value == "Pending"

    def test_terminated_value(self):
        assert LeaseStatus.TERMINATED.value == "Terminated"

    def test_expired_value(self):
        assert LeaseStatus.EXPIRED.value == "Expired"

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            LeaseStatus("NotAStatus")

    def test_member_count(self):
        assert len(LeaseStatus) == 4


class TestApartmentStatusEnum:
    def test_available_value(self):
        assert ApartmentStatus.AVAILABLE.value == "Available"

    def test_occupied_value(self):
        assert ApartmentStatus.OCCUPIED.value == "Occupied"

    def test_maintenance_value(self):
        assert ApartmentStatus.MAINTENANCE.value == "Under Maintenance"

    def test_member_count(self):
        assert len(ApartmentStatus) == 3

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            ApartmentStatus("Vacant")


class TestMaintenanceStatusEnum:
    def test_open_value(self):
        assert MaintenanceStatus.OPEN.value == "Open"

    def test_in_progress_value(self):
        assert MaintenanceStatus.IN_PROGRESS.value == "In Progress"

    def test_resolved_value(self):
        assert MaintenanceStatus.RESOLVED.value == "Resolved"

    def test_closed_value(self):
        assert MaintenanceStatus.CLOSED.value == "Closed"

    def test_member_count(self):
        assert len(MaintenanceStatus) == 4


class TestMaintenancePriorityEnum:
    def test_low_value(self):
        assert MaintenancePriority.LOW.value == "Low"

    def test_medium_value(self):
        assert MaintenancePriority.MEDIUM.value == "Medium"

    def test_high_value(self):
        assert MaintenancePriority.HIGH.value == "High"

    def test_urgent_value(self):
        assert MaintenancePriority.URGENT.value == "Urgent"

    def test_member_count(self):
        assert len(MaintenancePriority) == 4

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            MaintenancePriority("Critical")


class TestComplaintStatusEnum:
    def test_open_value(self):
        assert ComplaintStatus.OPEN.value == "Open"

    def test_under_review_value(self):
        assert ComplaintStatus.UNDER_REVIEW.value == "Under Review"

    def test_resolved_value(self):
        assert ComplaintStatus.RESOLVED.value == "Resolved"

    def test_closed_value(self):
        assert ComplaintStatus.CLOSED.value == "Closed"

    def test_member_count(self):
        assert len(ComplaintStatus) == 4


class TestPaymentStatusEnum:
    def test_pending_value(self):
        assert PaymentStatus.PENDING.value == "Pending"

    def test_paid_value(self):
        assert PaymentStatus.PAID.value == "Paid"

    def test_overdue_value(self):
        assert PaymentStatus.OVERDUE.value == "Overdue"

    def test_partial_value(self):
        assert PaymentStatus.PARTIAL.value == "Partial"

    def test_member_count(self):
        assert len(PaymentStatus) == 4

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            PaymentStatus("Late")


# =============================================================================
# 2. Location dataclass
# =============================================================================

class TestLocation:
    def test_defaults(self):
        loc = Location()
        assert loc.id is None
        assert loc.city == ""
        assert loc.address == ""
        assert loc.postcode == ""
        assert loc.country == "UK"

    def test_country_defaults_to_uk(self):
        loc = Location(city="Cardiff", address="Bay Rd", postcode="CF10 1AA")
        assert loc.country == "UK"

    def test_explicit_values_stored(self):
        loc = Location(id=3, city="London", address="Canary Wharf", postcode="E14 5AB", country="UK")
        assert loc.id == 3
        assert loc.city == "London"
        assert loc.postcode == "E14 5AB"

    def test_non_uk_country(self):
        loc = Location(city="Dublin", address="1 St Stephen", postcode="D02", country="IE")
        assert loc.country == "IE"

    def test_empty_strings_allowed(self):
        loc = Location(city="", address="", postcode="")
        assert loc.city == ""


# =============================================================================
# 3. Apartment dataclass
# =============================================================================

class TestApartment:
    def test_defaults(self):
        apt = Apartment()
        assert apt.id is None
        assert apt.unit_number == ""
        assert apt.location_id is None
        assert apt.apartment_type == ""
        assert apt.num_bedrooms == 1
        assert apt.num_bathrooms == 1
        assert apt.monthly_rent == 0.0
        assert apt.floor == 0
        assert apt.size_sqft == 0.0
        assert apt.furnished is False
        assert apt.parking is False
        assert apt.description == ""

    def test_default_status_is_available(self):
        """FR: new apartments default to Available status."""
        apt = Apartment()
        assert apt.status == ApartmentStatus.AVAILABLE.value
        assert apt.status == "Available"

    def test_explicit_assignment(self):
        apt = Apartment(
            id=10, unit_number="LN301", location_id=3,
            apartment_type="Studio", num_bedrooms=0, num_bathrooms=1,
            monthly_rent=1450.0, floor=5, size_sqft=380.0,
            furnished=True, parking=False, status="Occupied",
            description="High floor studio"
        )
        assert apt.unit_number == "LN301"
        assert apt.monthly_rent == 1450.0
        assert apt.furnished is True
        assert apt.parking is False
        assert apt.status == "Occupied"
        assert apt.description == "High floor studio"

    def test_zero_bedrooms_allowed(self):
        apt = Apartment(num_bedrooms=0)
        assert apt.num_bedrooms == 0

    def test_zero_rent_allowed(self):
        apt = Apartment(monthly_rent=0.0)
        assert apt.monthly_rent == 0.0

    def test_large_rent(self):
        apt = Apartment(monthly_rent=9999999.99)
        assert apt.monthly_rent == 9999999.99

    def test_high_floor(self):
        apt = Apartment(floor=50)
        assert apt.floor == 50

    def test_joined_fields_default_empty(self):
        apt = Apartment()
        assert apt.location_city == ""
        assert apt.location_address == ""

    def test_furnished_and_parking_booleans(self):
        apt = Apartment(furnished=True, parking=True)
        assert apt.furnished is True
        assert apt.parking is True


# =============================================================================
# 4. Tenant dataclass
# =============================================================================

class TestTenant:
    def test_defaults(self):
        t = Tenant()
        assert t.id is None
        assert t.ni_number == ""
        assert t.first_name == ""
        assert t.last_name == ""
        assert t.phone == ""
        assert t.email == ""
        assert t.occupation == ""
        assert t.notes == ""

    def test_optional_fields_default_none(self):
        t = Tenant()
        assert t.date_of_birth is None
        assert t.created_at is None

    def test_full_name_property(self):
        t = Tenant(first_name="Alice", last_name="Smith")
        assert t.full_name == "Alice Smith"

    def test_full_name_empty_strings(self):
        t = Tenant(first_name="", last_name="")
        assert t.full_name == " "

    def test_full_name_only_first(self):
        t = Tenant(first_name="Cher", last_name="")
        assert t.full_name == "Cher "

    def test_full_name_only_last(self):
        t = Tenant(first_name="", last_name="Prince")
        assert t.full_name == " Prince"

    def test_reference_fields_default_empty(self):
        t = Tenant()
        assert t.reference1_name == ""
        assert t.reference1_phone == ""
        assert t.reference1_email == ""
        assert t.reference2_name == ""

    def test_emergency_contact_defaults_empty(self):
        t = Tenant()
        assert t.emergency_contact_name == ""
        assert t.emergency_contact_phone == ""

    def test_explicit_values(self):
        t = Tenant(
            id=5, ni_number="NI100001A", first_name="James",
            last_name="Taylor", phone="07811100001",
            email="james@email.com", occupation="Engineer",
            date_of_birth="1988-04-15"
        )
        assert t.ni_number == "NI100001A"
        assert t.full_name == "James Taylor"
        assert t.date_of_birth == "1988-04-15"


# =============================================================================
# 5. Lease dataclass
# =============================================================================

class TestLease:
    def test_defaults(self):
        lease = Lease()
        assert lease.id is None
        assert lease.tenant_id is None
        assert lease.apartment_id is None
        assert lease.monthly_rent == 0.0
        assert lease.deposit_amount == 0.0
        assert lease.early_termination_requested is False

    def test_default_status_is_active(self):
        """FR: new leases default to Active status."""
        lease = Lease()
        assert lease.status == LeaseStatus.ACTIVE.value
        assert lease.status == "Active"

    def test_optional_date_fields_default_none(self):
        lease = Lease()
        assert lease.start_date is None
        assert lease.end_date is None
        assert lease.early_termination_date is None
        assert lease.notice_given_date is None
        assert lease.created_at is None

    def test_joined_fields_default_empty(self):
        lease = Lease()
        assert lease.tenant_name == ""
        assert lease.tenant_email == ""
        assert lease.tenant_phone == ""
        assert lease.apartment_unit == ""
        assert lease.apartment_type == ""
        assert lease.location_city == ""
        assert lease.location_address == ""

    def test_explicit_values(self):
        lease = Lease(
            id=1, tenant_id=3, apartment_id=7,
            start_date="2025-01-01", end_date="2026-01-01",
            monthly_rent=1250.0, deposit_amount=1250.0,
            status="Active"
        )
        assert lease.monthly_rent == 1250.0
        assert lease.deposit_amount == 1250.0
        assert lease.start_date == "2025-01-01"

    def test_early_termination_flag(self):
        lease = Lease(early_termination_requested=True,
                      early_termination_date="2025-06-01")
        assert lease.early_termination_requested is True
        assert lease.early_termination_date == "2025-06-01"


# =============================================================================
# 6. Payment dataclass
# =============================================================================

class TestPayment:
    def test_defaults(self):
        p = Payment()
        assert p.id is None
        assert p.lease_id is None
        assert p.amount_due == 0.0
        assert p.amount_paid == 0.0
        assert p.payment_method == ""
        assert p.reference_number == ""
        assert p.notes == ""

    def test_default_status_is_pending(self):
        """FR: payment records default to Pending status."""
        p = Payment()
        assert p.status == PaymentStatus.PENDING.value
        assert p.status == "Pending"

    def test_optional_date_fields_none(self):
        p = Payment()
        assert p.due_date is None
        assert p.paid_date is None
        assert p.created_at is None

    def test_partial_payment_fields(self):
        p = Payment(
            amount_due=1000.0, amount_paid=500.0,
            status=PaymentStatus.PARTIAL.value
        )
        assert p.amount_paid < p.amount_due
        assert p.status == "Partial"

    def test_overpayment_stored(self):
        p = Payment(amount_due=500.0, amount_paid=600.0)
        assert p.amount_paid > p.amount_due

    def test_zero_amounts(self):
        p = Payment(amount_due=0.0, amount_paid=0.0)
        assert p.amount_due == 0.0
        assert p.amount_paid == 0.0


# =============================================================================
# 7. MaintenanceRequest dataclass
# =============================================================================

class TestMaintenanceRequest:
    def test_defaults(self):
        req = MaintenanceRequest()
        assert req.id is None
        assert req.lease_id is None
        assert req.apartment_id is None
        assert req.tenant_id is None
        assert req.title == ""
        assert req.description == ""
        assert req.category == ""
        assert req.cost == 0.0
        assert req.time_taken_hours == 0.0
        assert req.resolution_notes == ""

    def test_default_priority_is_medium(self):
        """FR: new maintenance requests default to Medium priority."""
        req = MaintenanceRequest()
        assert req.priority == MaintenancePriority.MEDIUM.value
        assert req.priority == "Medium"

    def test_default_status_is_open(self):
        """FR: new maintenance requests default to Open status."""
        req = MaintenanceRequest()
        assert req.status == MaintenanceStatus.OPEN.value
        assert req.status == "Open"

    def test_optional_dates_default_none(self):
        req = MaintenanceRequest()
        assert req.reported_date is None
        assert req.scheduled_date is None
        assert req.resolved_date is None
        assert req.created_at is None

    def test_urgent_priority(self):
        req = MaintenanceRequest(priority=MaintenancePriority.URGENT.value)
        assert req.priority == "Urgent"

    def test_cost_and_hours(self):
        req = MaintenanceRequest(cost=250.0, time_taken_hours=3.5)
        assert req.cost == 250.0
        assert req.time_taken_hours == 3.5

    def test_joined_fields_default_empty(self):
        req = MaintenanceRequest()
        assert req.tenant_name == ""
        assert req.apartment_unit == ""
        assert req.location_city == ""


# =============================================================================
# 8. Complaint dataclass
# =============================================================================

class TestComplaint:
    def test_defaults(self):
        c = Complaint()
        assert c.id is None
        assert c.lease_id is None
        assert c.tenant_id is None
        assert c.apartment_id is None
        assert c.title == ""
        assert c.description == ""
        assert c.category == ""
        assert c.resolution_notes == ""

    def test_default_status_is_open(self):
        """FR: new complaints default to Open status."""
        c = Complaint()
        assert c.status == ComplaintStatus.OPEN.value
        assert c.status == "Open"

    def test_optional_dates_default_none(self):
        c = Complaint()
        assert c.reported_date is None
        assert c.resolved_date is None
        assert c.created_at is None

    def test_joined_fields_default_empty(self):
        c = Complaint()
        assert c.tenant_name == ""
        assert c.apartment_unit == ""

    def test_explicit_values(self):
        c = Complaint(
            id=1, lease_id=2, tenant_id=3, apartment_id=4,
            title="Noisy neighbour", category="Noise",
            status=ComplaintStatus.UNDER_REVIEW.value
        )
        assert c.title == "Noisy neighbour"
        assert c.status == "Under Review"


# =============================================================================
# 9. Staff dataclass
# =============================================================================

class TestStaff:
    def test_defaults(self):
        s = Staff()
        assert s.id is None
        assert s.username == ""
        assert s.password_hash == ""
        assert s.first_name == ""
        assert s.last_name == ""
        assert s.role == ""
        assert s.email == ""
        assert s.phone == ""
        assert s.location_id is None

    def test_is_active_defaults_true(self):
        """FR: new staff accounts are active by default."""
        s = Staff()
        assert s.is_active is True

    def test_created_at_defaults_none(self):
        s = Staff()
        assert s.created_at is None

    def test_full_name_property(self):
        s = Staff(first_name="Frank", last_name="Miller")
        assert s.full_name == "Frank Miller"

    def test_full_name_empty(self):
        s = Staff(first_name="", last_name="")
        assert s.full_name == " "

    def test_full_name_only_first(self):
        s = Staff(first_name="Admin", last_name="")
        assert s.full_name == "Admin "

    def test_explicit_values(self):
        s = Staff(
            id=1, username="manager1", role="Manager",
            first_name="Frank", last_name="Miller",
            email="frank@property.com", phone="07700666666",
            location_id=1, is_active=True
        )
        assert s.username == "manager1"
        assert s.role == "Manager"
        assert s.full_name == "Frank Miller"
        assert s.is_active is True

    def test_inactive_staff(self):
        s = Staff(is_active=False)
        assert s.is_active is False
