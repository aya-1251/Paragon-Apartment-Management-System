"""
Integration tests for db_manager.py — PAMS Group 17
Module: UFCF8S-30-2 Advanced Software Development

Each test gets its own temporary SQLite file so tests never interfere with
each other or with the live property_management.db.

Techniques: state-based testing, equivalence class, boundary value analysis.

Run from project root:
    pytest tests/test_db_manager.py -v
"""
import os
import sqlite3
import tempfile
import pytest

from db_manager import DatabaseManager
from models import (
    Apartment, Tenant, Lease, Payment, MaintenanceRequest, Complaint,
    ApartmentStatus, LeaseStatus, PaymentStatus, MaintenanceStatus,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def db(tmp_path):
    """Full DatabaseManager with seeded demo data."""
    path = str(tmp_path / "test_seeded.db")
    manager = DatabaseManager(db_path=path)
    yield manager
    manager.close()


@pytest.fixture
def clean_db(tmp_path):
    """DatabaseManager with schema only — no seed data for isolated CRUD tests."""
    path = str(tmp_path / "test_clean.db")
    manager = DatabaseManager.__new__(DatabaseManager)
    manager.db_path = path
    manager.connection = None
    manager.connect()
    manager.initialize_schema()
    yield manager
    manager.close()


# =============================================================================
# Helper factories (used by clean_db tests)
# =============================================================================

def _add_location(db, city="TestCity", address="1 Test St", postcode="TS1 1AA"):
    return db.add_location(city, address, postcode)


def _add_apartment(db, location_id, unit="T101", rent=1000.0):
    apt = Apartment(
        unit_number=unit, location_id=location_id, apartment_type="Flat",
        num_bedrooms=2, num_bathrooms=1, monthly_rent=rent,
        floor=1, size_sqft=600.0, furnished=False, parking=False,
    )
    return db.create_apartment(apt)


def _add_tenant(db, ni="NI999999A", first="Test", last="Tenant"):
    tenant = Tenant(
        ni_number=ni, first_name=first, last_name=last,
        phone="07700000001", email="test@pams.test", occupation="Tester",
    )
    return db.create_tenant(tenant)


def _add_lease(db, tenant_id, apartment_id, start="2025-01-01", end="2026-01-01"):
    lease = Lease(
        tenant_id=tenant_id, apartment_id=apartment_id,
        start_date=start, end_date=end,
        monthly_rent=1000.0, deposit_amount=1000.0,
        status=LeaseStatus.ACTIVE.value,
    )
    return db.create_lease(lease)


def _setup_lease(db):
    """Return (lease_id, apt_id, tenant_id) with full chain in clean_db."""
    loc_id = _add_location(db)
    apt_id = _add_apartment(db, loc_id)
    tid    = _add_tenant(db)
    lid    = _add_lease(db, tid, apt_id)
    return lid, apt_id, tid


# =============================================================================
# 1. Initialisation
# =============================================================================

class TestInit:
    def test_creates_all_tables(self, db):
        cursor = db.get_cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r["name"] for r in cursor.fetchall()}
        for expected in ("locations", "staff", "apartments", "tenants",
                         "leases", "payments", "maintenance_requests",
                         "complaints", "workers", "maintenance_types",
                         "worker_assignments"):
            assert expected in tables, f"Missing table: {expected}"

    def test_seeds_four_locations(self, db):
        assert len(db.get_all_locations()) == 4

    def test_seeds_staff(self, db):
        assert len(db.get_all_staff()) == 17

    def test_seeds_apartments(self, db):
        assert len(db.get_all_apartments()) == 17

    def test_seeds_tenants(self, db):
        assert len(db.get_all_tenants()) == 8

    def test_seed_is_idempotent(self, db):
        db.seed_demo_data()
        db.seed_demo_data()
        assert len(db.get_all_locations()) == 4

    def test_uses_row_factory(self, db):
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM locations LIMIT 1")
        row = cursor.fetchone()
        assert row["city"] is not None

    def test_foreign_keys_enabled(self, db):
        cursor = db.get_cursor()
        cursor.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1


# =============================================================================
# 2. Authentication
# =============================================================================

class TestAuthentication:
    def test_valid_credentials_return_staff(self, db):
        staff = db.authenticate_staff("admin1", "password123")
        assert staff is not None
        assert staff.username == "admin1"

    def test_wrong_password_returns_none(self, db):
        assert db.authenticate_staff("admin1", "wrongpass") is None

    def test_unknown_username_returns_none(self, db):
        assert db.authenticate_staff("nobody", "password123") is None

    def test_empty_username_returns_none(self, db):
        assert db.authenticate_staff("", "password123") is None

    def test_empty_password_returns_none(self, db):
        assert db.authenticate_staff("admin1", "") is None

    def test_correct_role_returned(self, db):
        staff = db.authenticate_staff("admin1", "password123")
        assert staff.role == "Administrator"

    def test_finance_staff_authenticates(self, db):
        staff = db.authenticate_staff("finance1", "password123")
        assert staff is not None
        assert staff.role == "Finance Manager"

    def test_manager_authenticates(self, db):
        staff = db.authenticate_staff("manager1", "password123")
        assert staff is not None
        assert staff.role == "Manager"

    def test_deactivated_staff_cannot_login(self, db):
        all_staff = db.get_all_staff()
        target = all_staff[0]
        db.toggle_staff_active(target.id)
        assert db.authenticate_staff(target.username, "password123") is None

    def test_salted_hash_verifies_correctly(self, db):
        stored = db._make_password_hash("samepassword")
        assert db._verify_password("samepassword", stored)

    def test_unique_salts_produce_different_stored_hashes(self, db):
        """Same password hashed twice should differ because each call uses a fresh salt."""
        h1 = db._make_password_hash("samepassword")
        h2 = db._make_password_hash("samepassword")
        assert h1 != h2

    def test_different_passwords_do_not_cross_verify(self, db):
        stored = db._make_password_hash("pass1")
        assert not db._verify_password("pass2", stored)


# =============================================================================
# 3. Locations
# =============================================================================

class TestLocations:
    def test_get_all_locations_returns_list(self, db):
        locs = db.get_all_locations()
        assert isinstance(locs, list)
        assert len(locs) == 4

    def test_seeded_cities_present(self, db):
        cities = {l.city for l in db.get_all_locations()}
        assert cities == {"Bristol", "Cardiff", "London", "Manchester"}

    def test_bristol_postcode(self, db):
        locs = db.get_all_locations()
        bristol = next(l for l in locs if l.city == "Bristol")
        assert bristol.postcode == "BS1 5TR"
        assert bristol.country == "UK"

    def test_add_location_returns_id(self, clean_db):
        loc_id = clean_db.add_location("Edinburgh", "1 Royal Mile", "EH1 1AA")
        assert isinstance(loc_id, int)
        assert loc_id > 0

    def test_add_location_persisted(self, clean_db):
        clean_db.add_location("Edinburgh", "1 Royal Mile", "EH1 1AA")
        locs = clean_db.get_all_locations()
        assert len(locs) == 1
        assert locs[0].city == "Edinburgh"

    def test_update_location(self, clean_db):
        loc_id = clean_db.add_location("Old City", "Old St", "OC1 1AA")
        clean_db.update_location(loc_id, "New City", "New St", "NC1 1AA")
        locs = clean_db.get_all_locations()
        updated = locs[0]
        assert updated.city == "New City"
        assert updated.postcode == "NC1 1AA"


# =============================================================================
# 4. Apartments
# =============================================================================

class TestApartments:
    def test_get_all_apartments_count(self, db):
        assert len(db.get_all_apartments()) == 17

    def test_available_apartments_status(self, db):
        for apt in db.get_available_apartments():
            assert apt.status == "Available"

    def test_available_filter_by_location(self, db):
        bristol = db.get_available_apartments(location_id=1)
        assert all(apt.location_id == 1 for apt in bristol)

    def test_get_all_apartments_by_location(self, db):
        bristol_apts = db.get_all_apartments(location_id=1)
        assert len(bristol_apts) == 5
        assert all(apt.location_city == "Bristol" for apt in bristol_apts)

    def test_get_apartment_by_id(self, db):
        apts = db.get_all_apartments()
        first = apts[0]
        fetched = db.get_apartment_by_id(first.id)
        assert fetched is not None
        assert fetched.id == first.id
        assert fetched.unit_number == first.unit_number

    def test_get_apartment_nonexistent_returns_none(self, db):
        assert db.get_apartment_by_id(99999) is None

    def test_get_apartment_zero_id_returns_none(self, db):
        assert db.get_apartment_by_id(0) is None

    def test_create_apartment_returns_id(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        assert isinstance(apt_id, int) and apt_id > 0

    def test_created_apartment_default_available(self, clean_db):
        """FR: new apartments must default to Available."""
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        assert clean_db.get_apartment_by_id(apt_id).status == "Available"

    def test_create_apartment_furnished_parking(self, clean_db):
        loc_id = _add_location(clean_db)
        apt = Apartment(
            unit_number="P001", location_id=loc_id, apartment_type="Penthouse",
            num_bedrooms=3, num_bathrooms=2, monthly_rent=4000.0,
            floor=15, size_sqft=1400.0, furnished=True, parking=True,
        )
        apt_id = clean_db.create_apartment(apt)
        fetched = clean_db.get_apartment_by_id(apt_id)
        assert fetched.furnished is True
        assert fetched.parking is True

    def test_update_apartment_status(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        clean_db.update_apartment_status(apt_id, "Under Maintenance")
        assert clean_db.get_apartment_by_id(apt_id).status == "Under Maintenance"

    def test_update_apartment_fields(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id, rent=1000.0)
        apt = clean_db.get_apartment_by_id(apt_id)
        apt.monthly_rent = 1500.0
        apt.num_bedrooms = 3
        apt.description = "Newly renovated"
        clean_db.update_apartment(apt)
        updated = clean_db.get_apartment_by_id(apt_id)
        assert updated.monthly_rent == 1500.0
        assert updated.num_bedrooms == 3
        assert updated.description == "Newly renovated"

    def test_delete_apartment_no_lease(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        assert clean_db.delete_apartment(apt_id) is True
        assert clean_db.get_apartment_by_id(apt_id) is None

    def test_delete_apartment_with_active_lease_blocked(self, clean_db):
        """Business rule: apartments with active leases cannot be deleted."""
        lid, apt_id, _ = _setup_lease(clean_db)
        assert clean_db.delete_apartment(apt_id) is False
        assert clean_db.get_apartment_by_id(apt_id) is not None

    def test_delete_nonexistent_apartment(self, clean_db):
        # No active leases → returns True even when id doesn't exist (0 rows deleted)
        assert clean_db.delete_apartment(99999) is True

    def test_search_apartments_by_unit(self, db):
        results = db.search_apartments("BR101")
        assert len(results) == 1
        assert results[0].unit_number == "BR101"

    def test_search_apartments_by_city(self, db):
        results = db.search_apartments("London")
        assert all(apt.location_city == "London" for apt in results)
        assert len(results) > 0

    def test_search_apartments_by_type(self, db):
        results = db.search_apartments("Penthouse")
        assert all(apt.apartment_type == "Penthouse" for apt in results)

    def test_search_apartments_no_match(self, db):
        assert db.search_apartments("ZZZ_NO_MATCH_XYZ") == []

    def test_search_apartments_empty_query_returns_all(self, db):
        results = db.search_apartments("")
        assert len(results) == len(db.get_all_apartments())


# =============================================================================
# 5. Tenants
# =============================================================================

class TestTenants:
    def test_get_all_tenants_count(self, db):
        assert len(db.get_all_tenants()) == 8

    def test_create_tenant_returns_id(self, clean_db):
        tid = _add_tenant(clean_db)
        assert isinstance(tid, int) and tid > 0

    def test_create_tenant_persisted(self, clean_db):
        tid = _add_tenant(clean_db, first="Alice", last="Wonder")
        t = clean_db.get_tenant_by_id(tid)
        assert t.first_name == "Alice"
        assert t.last_name == "Wonder"
        assert t.ni_number == "NI999999A"

    def test_duplicate_ni_number_raises_integrity_error(self, clean_db):
        """FR: NI numbers must be unique across tenants."""
        _add_tenant(clean_db, ni="NI111111A")
        with pytest.raises(sqlite3.IntegrityError):
            _add_tenant(clean_db, ni="NI111111A")

    def test_get_tenant_by_id(self, db):
        tenants = db.get_all_tenants()
        t = tenants[0]
        fetched = db.get_tenant_by_id(t.id)
        assert fetched.id == t.id
        assert fetched.ni_number == t.ni_number

    def test_get_tenant_nonexistent_returns_none(self, db):
        assert db.get_tenant_by_id(99999) is None

    def test_get_tenant_negative_id_returns_none(self, db):
        assert db.get_tenant_by_id(-1) is None

    def test_update_tenant(self, clean_db):
        tid = _add_tenant(clean_db)
        t = clean_db.get_tenant_by_id(tid)
        t.first_name = "Updated"
        t.phone = "07999999999"
        t.occupation = "Manager"
        clean_db.update_tenant(t)
        updated = clean_db.get_tenant_by_id(tid)
        assert updated.first_name == "Updated"
        assert updated.phone == "07999999999"
        assert updated.occupation == "Manager"

    def test_search_tenants_by_name(self, db):
        results = db.search_tenants("James")
        assert any(t.first_name == "James" for t in results)

    def test_search_tenants_by_last_name(self, db):
        results = db.search_tenants("Taylor")
        assert any(t.last_name == "Taylor" for t in results)

    def test_search_tenants_by_email(self, db):
        results = db.search_tenants("james.taylor@email.com")
        assert len(results) >= 1

    def test_search_tenants_by_ni(self, db):
        results = db.search_tenants("NI100001A")
        assert len(results) == 1
        assert results[0].ni_number == "NI100001A"

    def test_search_tenants_no_match(self, db):
        assert db.search_tenants("ZZZ_NO_MATCH_XYZ") == []

    def test_search_tenants_empty_returns_all(self, db):
        results = db.search_tenants("")
        assert len(results) == len(db.get_all_tenants())

    def test_tenant_full_name(self, db):
        tenants = db.get_all_tenants()
        james = next(t for t in tenants if t.first_name == "James")
        assert james.full_name == "James Taylor"


# =============================================================================
# 6. Leases
# =============================================================================

class TestLeases:
    def test_create_lease_returns_id(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        assert isinstance(lid, int) and lid > 0

    def test_create_lease_marks_apartment_occupied(self, clean_db):
        """FR: creating a lease must mark the apartment Occupied."""
        lid, apt_id, _ = _setup_lease(clean_db)
        apt = clean_db.get_apartment_by_id(apt_id)
        assert apt.status == ApartmentStatus.OCCUPIED.value

    def test_get_lease_by_id(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        lease = clean_db.get_lease_by_id(lid)
        assert lease is not None
        assert lease.id == lid
        assert lease.tenant_id == tid
        assert lease.apartment_id == apt_id

    def test_get_lease_nonexistent_returns_none(self, db):
        assert db.get_lease_by_id(99999) is None

    def test_lease_has_joined_tenant_name(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        tid    = _add_tenant(clean_db, first="Bob", last="Builder")
        lid    = _add_lease(clean_db, tid, apt_id)
        lease  = clean_db.get_lease_by_id(lid)
        assert lease.tenant_name == "Bob Builder"

    def test_lease_has_joined_apartment_unit(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id, unit="UNIT99")
        tid    = _add_tenant(clean_db)
        lid    = _add_lease(clean_db, tid, apt_id)
        lease  = clean_db.get_lease_by_id(lid)
        assert lease.apartment_unit == "UNIT99"

    def test_get_all_leases(self, db):
        leases = db.get_all_leases()
        assert isinstance(leases, list)
        assert len(leases) > 0

    def test_get_all_leases_by_location(self, db):
        all_leases     = db.get_all_leases()
        bristol_leases = db.get_all_leases(location_id=1)
        assert len(bristol_leases) <= len(all_leases)
        for lease in bristol_leases:
            assert lease.location_city == "Bristol"

    def test_get_active_lease_for_apartment(self, clean_db):
        lid, apt_id, _ = _setup_lease(clean_db)
        lease = clean_db.get_active_lease_for_apartment(apt_id)
        assert lease is not None
        assert lease.id == lid
        assert lease.status == "Active"

    def test_no_active_lease_for_available_apartment(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        assert clean_db.get_active_lease_for_apartment(apt_id) is None

    def test_update_lease_status(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        clean_db.update_lease_status(lid, "Terminated")
        assert clean_db.get_lease_by_id(lid).status == "Terminated"

    def test_update_lease_to_expired(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        clean_db.update_lease_status(lid, "Expired")
        assert clean_db.get_lease_by_id(lid).status == "Expired"

    def test_get_expiring_leases_far_future(self, clean_db):
        """Leases ending > 9999 days away should not appear with days=30."""
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        tid    = _add_tenant(clean_db)
        _add_lease(clean_db, tid, apt_id, start="2025-01-01", end="2099-12-31")
        expiring = clean_db.get_expiring_leases(days=30)
        assert len(expiring) == 0

    def test_get_expiring_leases_past_end_date(self, clean_db):
        """Leases already ended should appear as expiring (days_remaining <= 0)."""
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        tid    = _add_tenant(clean_db)
        _add_lease(clean_db, tid, apt_id, start="2020-01-01", end="2021-01-01")
        expiring = clean_db.get_expiring_leases(days=9999)
        assert len(expiring) == 1

    def test_search_leases_by_tenant_name(self, db):
        results = db.search_leases("James")
        assert isinstance(results, list)

    def test_search_leases_no_match(self, db):
        assert db.search_leases("ZZZ_NO_MATCH_XYZ") == []

    def test_get_all_leases_for_apartment(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        tid    = _add_tenant(clean_db)
        lid    = _add_lease(clean_db, tid, apt_id)
        results = clean_db.get_all_leases_for_apartment(apt_id)
        assert len(results) == 1
        assert results[0].id == lid


# =============================================================================
# 7. Payments
# =============================================================================

class TestPayments:
    def test_create_payment_request_returns_id(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        p = Payment(lease_id=lid, amount_due=1000.0, due_date="2025-02-01")
        pid = clean_db.create_payment_request(p)
        assert isinstance(pid, int) and pid > 0

    def test_create_payment_auto_marks_paid(self, clean_db):
        """create_payment_request immediately marks payment as Paid (billing flow)."""
        lid, _, _ = _setup_lease(clean_db)
        p = Payment(lease_id=lid, amount_due=750.0, due_date="2025-02-01")
        clean_db.create_payment_request(p)
        payments = clean_db.get_payments_for_lease(lid)
        assert payments[0].status == PaymentStatus.PAID.value

    def test_create_payment_amount_recorded(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        p = Payment(lease_id=lid, amount_due=1250.0, due_date="2025-03-01")
        clean_db.create_payment_request(p)
        payments = clean_db.get_payments_for_lease(lid)
        assert payments[0].amount_due == 1250.0
        assert payments[0].amount_paid == 1250.0

    def test_get_payments_for_lease_multiple(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        for i in range(3):
            p = Payment(lease_id=lid, amount_due=1000.0, due_date=f"2025-0{i+1}-01")
            clean_db.create_payment_request(p)
        assert len(clean_db.get_payments_for_lease(lid)) == 3

    def test_get_payments_nonexistent_lease(self, clean_db):
        assert clean_db.get_payments_for_lease(99999) == []

    def test_mark_payment_paid(self, clean_db):
        lid, _, _ = _setup_lease(clean_db)
        cursor = clean_db.get_cursor()
        cursor.execute(
            "INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,status,payment_method)"
            " VALUES (?,?,?,?,?,?)",
            (lid, 800.0, 0.0, "2025-04-01", "Pending", ""),
        )
        clean_db.commit()
        pid = cursor.lastrowid
        clean_db.mark_payment_paid(pid, method="Bank Transfer")
        paid = clean_db.get_payments_for_lease(lid)[-1]
        assert paid.status == "Paid"
        assert paid.payment_method == "Bank Transfer"

    def test_mark_payment_overdue(self, clean_db):
        """State transition: Pending → Overdue."""
        lid, _, _ = _setup_lease(clean_db)
        cursor = clean_db.get_cursor()
        cursor.execute(
            "INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,status,payment_method)"
            " VALUES (?,?,?,?,?,?)",
            (lid, 600.0, 0.0, "2024-01-01", "Pending", ""),
        )
        clean_db.commit()
        pid = cursor.lastrowid
        clean_db.mark_payment_overdue(pid)
        payments = clean_db.get_payments_for_lease(lid)
        overdue = next(p for p in payments if p.id == pid)
        assert overdue.status == "Overdue"

    def test_mark_overdue_does_not_affect_paid(self, clean_db):
        """mark_payment_overdue must not change an already-Paid record."""
        lid, _, _ = _setup_lease(clean_db)
        cursor = clean_db.get_cursor()
        cursor.execute(
            "INSERT INTO payments (lease_id,amount_due,amount_paid,due_date,status,payment_method)"
            " VALUES (?,?,?,?,?,?)",
            (lid, 400.0, 400.0, "2025-01-01", "Paid", "Bank Transfer"),
        )
        clean_db.commit()
        pid = cursor.lastrowid
        clean_db.mark_payment_overdue(pid)
        payments = clean_db.get_payments_for_lease(lid)
        paid_rec = next(p for p in payments if p.id == pid)
        assert paid_rec.status == "Paid"

    def test_get_all_payments(self, db):
        payments = db.get_all_payments()
        assert isinstance(payments, list)

    def test_get_payments_for_apartment(self, clean_db):
        lid, apt_id, _ = _setup_lease(clean_db)
        p = Payment(lease_id=lid, amount_due=900.0, due_date="2025-05-01")
        clean_db.create_payment_request(p)
        apt_payments = clean_db.get_payments_for_apartment(apt_id)
        assert len(apt_payments) == 1

    def test_send_late_notification_returns_dict(self, db):
        payments = db.get_all_payments()
        if payments:
            result = db.send_late_notification(payments[0].id)
            assert isinstance(result, dict)


# =============================================================================
# 8. Maintenance requests
# =============================================================================

class TestMaintenanceRequests:
    def test_create_request_returns_id(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid,
            title="Broken boiler", category="Heating",
        )
        mid = clean_db.create_maintenance_request(req)
        assert isinstance(mid, int) and mid > 0

    def test_new_request_status_is_open(self, clean_db):
        """FR: every new maintenance request must start with status Open."""
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid, title="Dripping tap",
        )
        mid = clean_db.create_maintenance_request(req)
        assert clean_db.get_maintenance_by_id(mid).status == "Open"

    def test_new_request_default_priority_medium(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid, title="Sticky door",
        )
        mid = clean_db.create_maintenance_request(req)
        assert clean_db.get_maintenance_by_id(mid).priority == "Medium"

    def test_get_maintenance_for_lease(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid,
            title="Broken lock", category="Doors",
        )
        clean_db.create_maintenance_request(req)
        results = clean_db.get_maintenance_for_lease(lid)
        assert len(results) == 1
        assert results[0].title == "Broken lock"

    def test_get_maintenance_nonexistent_lease(self, clean_db):
        assert clean_db.get_maintenance_for_lease(99999) == []

    def test_update_maintenance_status(self, clean_db):
        """State transition: Open → In Progress."""
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid, title="Mould on wall",
        )
        mid = clean_db.create_maintenance_request(req)
        m = clean_db.get_maintenance_by_id(mid)
        m.status = MaintenanceStatus.IN_PROGRESS.value
        m.resolution_notes = "Treatment scheduled"
        clean_db.update_maintenance(m)
        updated = clean_db.get_maintenance_by_id(mid)
        assert updated.status == "In Progress"
        assert updated.resolution_notes == "Treatment scheduled"

    def test_resolve_maintenance_request(self, clean_db):
        """State transition: Open → Resolved."""
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid, title="Leaking pipe",
        )
        mid = clean_db.create_maintenance_request(req)
        m = clean_db.get_maintenance_by_id(mid)
        m.status = MaintenanceStatus.RESOLVED.value
        m.cost = 150.0
        m.time_taken_hours = 2.0
        m.resolved_date = "2025-06-01"
        clean_db.update_maintenance(m)
        updated = clean_db.get_maintenance_by_id(mid)
        assert updated.status == "Resolved"
        assert updated.cost == 150.0

    def test_get_all_maintenance(self, db):
        maint = db.get_all_maintenance()
        assert isinstance(maint, list)

    def test_get_maintenance_by_id_nonexistent(self, db):
        assert db.get_maintenance_by_id(99999) is None

    def test_get_maintenance_stats_keys(self, db):
        stats = db.get_maintenance_stats()
        assert isinstance(stats, dict)
        for key in ("total", "open_count", "in_progress", "resolved",
                    "urgent", "high", "total_cost", "avg_hours"):
            assert key in stats

    def test_get_maintenance_for_apartment(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        req = MaintenanceRequest(
            lease_id=lid, apartment_id=apt_id, tenant_id=tid, title="Damp wall",
        )
        clean_db.create_maintenance_request(req)
        results = clean_db.get_maintenance_for_apartment(apt_id)
        assert len(results) == 1


# =============================================================================
# 9. Complaints
# =============================================================================

class TestComplaints:
    def test_create_complaint_returns_id(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        c = Complaint(
            lease_id=lid, tenant_id=tid, apartment_id=apt_id,
            title="Noisy neighbours", category="Noise",
        )
        cid = clean_db.create_complaint(c)
        assert isinstance(cid, int) and cid > 0

    def test_new_complaint_status_is_open(self, clean_db):
        """FR: every new complaint must default to Open."""
        lid, apt_id, tid = _setup_lease(clean_db)
        c = Complaint(
            lease_id=lid, tenant_id=tid, apartment_id=apt_id,
            title="Water pressure", category="Plumbing",
        )
        clean_db.create_complaint(c)
        complaints = clean_db.get_complaints_for_lease(lid)
        assert complaints[0].status == "Open"

    def test_get_complaints_for_lease(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        for i in range(2):
            c = Complaint(
                lease_id=lid, tenant_id=tid, apartment_id=apt_id,
                title=f"Complaint {i}", category="Other",
            )
            clean_db.create_complaint(c)
        complaints = clean_db.get_complaints_for_lease(lid)
        assert len(complaints) == 2

    def test_get_complaints_nonexistent_lease(self, clean_db):
        assert clean_db.get_complaints_for_lease(99999) == []

    def test_complaint_has_joined_tenant_name(self, clean_db):
        loc_id = _add_location(clean_db)
        apt_id = _add_apartment(clean_db, loc_id)
        tid    = _add_tenant(clean_db, first="Sandra", last="Lee")
        lid    = _add_lease(clean_db, tid, apt_id)
        c = Complaint(
            lease_id=lid, tenant_id=tid, apartment_id=apt_id,
            title="Broken window", category="Structural",
        )
        clean_db.create_complaint(c)
        complaints = clean_db.get_complaints_for_lease(lid)
        assert complaints[0].tenant_name == "Sandra Lee"

    def test_get_complaints_for_apartment(self, clean_db):
        lid, apt_id, tid = _setup_lease(clean_db)
        c = Complaint(
            lease_id=lid, tenant_id=tid, apartment_id=apt_id,
            title="Cold radiator", category="Heating",
        )
        clean_db.create_complaint(c)
        results = clean_db.get_complaints_for_apartment(apt_id)
        assert len(results) == 1


# =============================================================================
# 10. Staff management
# =============================================================================

class TestStaffManagement:
    def test_get_all_staff_count(self, db):
        assert len(db.get_all_staff()) == 17

    def test_create_staff_and_authenticate(self, db):
        db.create_staff(
            username="newstaff99", password="securepass99",
            first_name="New", last_name="Staff",
            role="Front Desk", email="new@pams.test",
            phone="07700000099", location_id=1,
        )
        staff = db.authenticate_staff("newstaff99", "securepass99")
        assert staff is not None
        assert staff.role == "Front Desk"

    def test_duplicate_username_raises_integrity_error(self, db):
        """FR: usernames must be unique."""
        with pytest.raises(sqlite3.IntegrityError):
            db.create_staff(
                username="admin1", password="anypass",
                first_name="Dup", last_name="User",
                role="Front Desk", email="dup@pams.test",
                phone="", location_id=1,
            )

    def test_username_exists_true(self, db):
        assert db.username_exists("admin1") is True

    def test_username_exists_false(self, db):
        assert db.username_exists("nobody_here_xyz") is False

    def test_update_staff_fields(self, db):
        all_staff = db.get_all_staff()
        s = all_staff[0]
        db.update_staff(s.id, "Updated", "Name", "Front Desk", "upd@test.com", "07799999999", 1)
        updated = next(st for st in db.get_all_staff() if st.id == s.id)
        assert updated.first_name == "Updated"
        assert updated.last_name == "Name"

    def test_reset_password_allows_new_login(self, db):
        all_staff = db.get_all_staff()
        s = all_staff[0]
        db.reset_staff_password(s.id, "brandnewpass456")
        assert db.authenticate_staff(s.username, "brandnewpass456") is not None

    def test_reset_password_invalidates_old(self, db):
        all_staff = db.get_all_staff()
        s = all_staff[0]
        db.reset_staff_password(s.id, "brandnewpass456")
        assert db.authenticate_staff(s.username, "password123") is None

    def test_toggle_staff_active_deactivates(self, db):
        all_staff = db.get_all_staff()
        s = next(st for st in all_staff if st.is_active)
        new_state = db.toggle_staff_active(s.id)
        assert new_state is False
        assert db.authenticate_staff(s.username, "password123") is None

    def test_toggle_staff_active_reactivates(self, db):
        all_staff = db.get_all_staff()
        s = all_staff[0]
        db.toggle_staff_active(s.id)   # deactivate
        db.toggle_staff_active(s.id)   # reactivate
        assert db.authenticate_staff(s.username, "password123") is not None

    def test_get_staff_for_location(self, db):
        bristol_staff = db.get_staff_for_location(1)
        assert isinstance(bristol_staff, list)
        assert len(bristol_staff) > 0


# =============================================================================
# 11. Financial & reporting
# =============================================================================

class TestReporting:
    def test_financial_summary_returns_dict(self, db):
        assert isinstance(db.get_financial_summary(), dict)

    def test_financial_summary_keys(self, db):
        summary = db.get_financial_summary()
        for key in ("total_billed", "total_collected", "pending", "overdue",
                    "maintenance_cost", "total_apts", "occupancy_rate"):
            assert key in summary, f"Missing key: {key}"

    def test_financial_summary_by_location(self, db):
        summary = db.get_financial_summary(location_id=1)
        assert isinstance(summary, dict)
        assert summary["total_apts"] == 5

    def test_dashboard_stats_returns_dict(self, db):
        assert isinstance(db.get_dashboard_stats(), dict)

    def test_dashboard_stats_keys(self, db):
        stats = db.get_dashboard_stats()
        for key in ("total_apartments", "available_apartments", "occupied_apartments",
                    "active_leases", "open_complaints", "open_maintenance"):
            assert key in stats, f"Missing key: {key}"

    def test_dashboard_stats_total_matches_seed(self, db):
        assert db.get_dashboard_stats()["total_apartments"] == 17

    def test_get_occupancy_by_city(self, db):
        result = db.get_occupancy_by_city()
        assert isinstance(result, list)
        cities = [r["city"] for r in result]
        assert "Bristol" in cities
        assert "London" in cities

    def test_occupancy_by_city_has_four_rows(self, db):
        result = db.get_occupancy_by_city()
        assert len(result) == 4

    def test_get_monthly_revenue(self, db):
        result = db.get_monthly_revenue()
        assert isinstance(result, list)

    def test_get_monthly_revenue_by_location(self, db):
        result = db.get_monthly_revenue(location_id=1)
        assert isinstance(result, list)

    def test_get_late_payments(self, db):
        assert isinstance(db.get_late_payments(), list)

    def test_get_maintenance_cost_report(self, db):
        assert isinstance(db.get_maintenance_cost_report(), list)

    def test_get_cross_city_summary(self, db):
        result = db.get_cross_city_summary()
        assert isinstance(result, list)
        assert len(result) == 4
        for row in result:
            assert "city" in row
            assert "total_apts" in row

    def test_get_performance_report(self, db):
        report = db.get_performance_report()
        assert isinstance(report, dict)
        for key in ("financial", "maintenance", "monthly_rev", "maint_costs", "expiring"):
            assert key in report

    def test_get_performance_report_by_location(self, db):
        report = db.get_performance_report(location_id=1)
        assert isinstance(report, dict)
        assert report["financial"]["total_apts"] == 5

    def test_maintenance_stats_keys(self, db):
        stats = db.get_maintenance_stats()
        for key in ("total", "open_count", "in_progress", "resolved", "urgent", "high"):
            assert key in stats
