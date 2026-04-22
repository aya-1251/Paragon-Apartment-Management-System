"""
Data models for the Paragon Apartment Management System (PAMS).

OOP design:
  - BaseModel   : abstract base dataclass (id, created_at shared by all entities)
  - Domain classes inherit BaseModel and add business-logic methods
  - Enum classes enforce type-safe status values throughout the system
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


# ─────────────────────────── STATUS ENUMS ───────────────────────────

class LeaseStatus(Enum):
    ACTIVE      = "Active"
    PENDING     = "Pending"
    TERMINATED  = "Terminated"
    EXPIRED     = "Expired"


class ApartmentStatus(Enum):
    AVAILABLE   = "Available"
    OCCUPIED    = "Occupied"
    MAINTENANCE = "Under Maintenance"


class MaintenanceStatus(Enum):
    OPEN        = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED    = "Resolved"
    CLOSED      = "Closed"


class MaintenancePriority(Enum):
    LOW    = "Low"
    MEDIUM = "Medium"
    HIGH   = "High"
    URGENT = "Urgent"


class ComplaintStatus(Enum):
    OPEN         = "Open"
    UNDER_REVIEW = "Under Review"
    RESOLVED     = "Resolved"
    CLOSED       = "Closed"


class PaymentStatus(Enum):
    PENDING = "Pending"
    PAID    = "Paid"
    OVERDUE = "Overdue"
    PARTIAL = "Partial"


# ─────────────────────────── BASE MODEL ─────────────────────────────

@dataclass
class BaseModel:
    """
    Abstract base for all domain entities.
    Provides the common id and created_at fields so subclasses
    do not need to repeat them.
    """
    id:         Optional[int] = None
    created_at: Optional[str] = None


# ─────────────────────────── DOMAIN MODELS ──────────────────────────

@dataclass
class Location(BaseModel):
    city:     str = ""
    address:  str = ""
    postcode: str = ""
    country:  str = "UK"

    def display_name(self) -> str:
        """Return a human-readable label for the location."""
        return f"{self.city} — {self.address}"


@dataclass
class Apartment(BaseModel):
    unit_number:      str   = ""
    location_id:      Optional[int] = None
    apartment_type:   str   = ""
    num_bedrooms:     int   = 1
    num_bathrooms:    int   = 1
    monthly_rent:     float = 0.0
    floor:            int   = 0
    size_sqft:        float = 0.0
    furnished:        bool  = False
    parking:          bool  = False
    status:           str   = ApartmentStatus.AVAILABLE.value
    description:      str   = ""
    # Joined fields (populated by DB queries)
    location_city:    str   = ""
    location_address: str   = ""

    # ── Business logic ──────────────────────────────────────────────

    def is_available(self) -> bool:
        """True when the apartment can be leased."""
        return self.status == ApartmentStatus.AVAILABLE.value

    def is_occupied(self) -> bool:
        return self.status == ApartmentStatus.OCCUPIED.value

    def annual_rent(self) -> float:
        """Projected annual rent at current monthly rate."""
        return self.monthly_rent * 12


@dataclass
class Tenant(BaseModel):
    ni_number:               str  = ""
    first_name:              str  = ""
    last_name:               str  = ""
    phone:                   str  = ""
    email:                   str  = ""
    occupation:              str  = ""
    date_of_birth:           Optional[str] = None
    emergency_contact_name:  str  = ""
    emergency_contact_phone: str  = ""
    reference1_name:         str  = ""
    reference1_phone:        str  = ""
    reference1_email:        str  = ""
    reference2_name:         str  = ""
    reference2_phone:        str  = ""
    reference2_email:        str  = ""
    notes:                   str  = ""

    # ── Business logic ──────────────────────────────────────────────

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def has_emergency_contact(self) -> bool:
        """True when an emergency contact name and phone are provided."""
        return bool(self.emergency_contact_name and self.emergency_contact_phone)

    def has_references(self) -> bool:
        """True when at least one reference is on record."""
        return bool(self.reference1_name)


@dataclass
class Lease(BaseModel):
    """
    Represents a lease agreement between a tenant and an apartment.

    Business rules encoded here:
      - Early termination requires REQUIRED_NOTICE_DAYS days notice.
      - Early termination incurs a penalty of EARLY_TERMINATION_PENALTY_RATE
        applied to the monthly rent.
    """

    REQUIRED_NOTICE_DAYS:            int   = field(default=30,   init=False, repr=False)
    EARLY_TERMINATION_PENALTY_RATE:  float = field(default=0.05, init=False, repr=False)

    tenant_id:                    Optional[int] = None
    apartment_id:                 Optional[int] = None
    start_date:                   Optional[str] = None
    end_date:                     Optional[str] = None
    monthly_rent:                 float = 0.0
    deposit_amount:               float = 0.0
    status:                       str   = LeaseStatus.ACTIVE.value
    early_termination_requested:  bool  = False
    early_termination_date:       Optional[str] = None
    notice_given_date:            Optional[str] = None
    created_by:                   Optional[int] = None
    # Joined fields (populated by DB queries)
    tenant_name:     str = ""
    tenant_email:    str = ""
    tenant_phone:    str = ""
    apartment_unit:  str = ""
    apartment_type:  str = ""
    location_city:   str = ""
    location_address:str = ""

    # ── Business logic ──────────────────────────────────────────────

    def is_active(self) -> bool:
        return self.status == LeaseStatus.ACTIVE.value

    def days_until_expiry(self) -> Optional[int]:
        """Days remaining until end_date. Negative means already expired."""
        if not self.end_date:
            return None
        try:
            end = date.fromisoformat(self.end_date)
            return (end - date.today()).days
        except ValueError:
            return None

    def early_termination_penalty(self) -> float:
        """
        Calculate the financial penalty for early termination.
        Per company policy: 5% of monthly rent.
        """
        return round(self.monthly_rent * self.EARLY_TERMINATION_PENALTY_RATE, 2)

    def is_expired(self) -> bool:
        days = self.days_until_expiry()
        return days is not None and days < 0


@dataclass
class Payment(BaseModel):
    lease_id:         Optional[int] = None
    amount_due:       float = 0.0
    amount_paid:      float = 0.0
    due_date:         Optional[str] = None
    paid_date:        Optional[str] = None
    status:           str  = PaymentStatus.PENDING.value
    payment_method:   str  = ""
    reference_number: str  = ""
    notes:            str  = ""

    # ── Business logic ──────────────────────────────────────────────

    def balance_due(self) -> float:
        """Outstanding amount still owed."""
        return round(self.amount_due - self.amount_paid, 2)

    def is_overdue(self) -> bool:
        """True when the due date has passed and the payment is not fully paid."""
        if self.status == PaymentStatus.PAID.value:
            return False
        if not self.due_date:
            return False
        try:
            return date.fromisoformat(self.due_date) < date.today()
        except ValueError:
            return False

    def is_paid(self) -> bool:
        return self.status == PaymentStatus.PAID.value


@dataclass
class MaintenanceRequest(BaseModel):
    lease_id:         Optional[int] = None
    apartment_id:     Optional[int] = None
    tenant_id:        Optional[int] = None
    title:            str   = ""
    description:      str   = ""
    category:         str   = ""
    priority:         str   = MaintenancePriority.MEDIUM.value
    status:           str   = MaintenanceStatus.OPEN.value
    reported_date:    Optional[str] = None
    scheduled_date:   Optional[str] = None
    resolved_date:    Optional[str] = None
    resolution_notes: str   = ""
    cost:             float = 0.0
    time_taken_hours: float = 0.0
    assigned_staff_id:Optional[int] = None
    # Joined fields
    tenant_name:    str = ""
    apartment_unit: str = ""
    location_city:  str = ""

    # ── Business logic ──────────────────────────────────────────────

    def is_open(self) -> bool:
        return self.status == MaintenanceStatus.OPEN.value

    def is_resolved(self) -> bool:
        return self.status in (
            MaintenanceStatus.RESOLVED.value,
            MaintenanceStatus.CLOSED.value,
        )

    def is_urgent(self) -> bool:
        return self.priority == MaintenancePriority.URGENT.value


@dataclass
class Complaint(BaseModel):
    lease_id:         Optional[int] = None
    tenant_id:        Optional[int] = None
    apartment_id:     Optional[int] = None
    title:            str  = ""
    description:      str  = ""
    category:         str  = ""
    status:           str  = ComplaintStatus.OPEN.value
    reported_date:    Optional[str] = None
    resolved_date:    Optional[str] = None
    resolution_notes: str  = ""
    created_by:       Optional[int] = None
    # Joined fields
    tenant_name:    str = ""
    apartment_unit: str = ""

    # ── Business logic ──────────────────────────────────────────────

    def is_open(self) -> bool:
        return self.status == ComplaintStatus.OPEN.value

    def is_resolved(self) -> bool:
        return self.status in (
            ComplaintStatus.RESOLVED.value,
            ComplaintStatus.CLOSED.value,
        )


@dataclass
class Staff(BaseModel):
    username:    str  = ""
    password_hash: str = ""
    first_name:  str  = ""
    last_name:   str  = ""
    role:        str  = ""
    email:       str  = ""
    phone:       str  = ""
    location_id: Optional[int] = None
    is_active:   bool = True

    # ── Business logic ──────────────────────────────────────────────

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def has_location_access(self, location_id: int) -> bool:
        """True when the staff member is assigned to the given location."""
        return self.location_id == location_id

    def is_manager(self) -> bool:
        return self.role == "Manager"

    def is_admin(self) -> bool:
        return self.role == "Administrator"
