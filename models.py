"""
Data models for the Property Management System.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


class LeaseStatus(Enum):
    ACTIVE = "Active"
    PENDING = "Pending"
    TERMINATED = "Terminated"
    EXPIRED = "Expired"


class ApartmentStatus(Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Under Maintenance"


class MaintenanceStatus(Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class MaintenancePriority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class ComplaintStatus(Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class PaymentStatus(Enum):
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"
    PARTIAL = "Partial"


@dataclass
class Location:
    id: Optional[int] = None
    city: str = ""
    address: str = ""
    postcode: str = ""
    country: str = "UK"


@dataclass
class Apartment:
    id: Optional[int] = None
    unit_number: str = ""
    location_id: Optional[int] = None
    apartment_type: str = ""
    num_bedrooms: int = 1
    num_bathrooms: int = 1
    monthly_rent: float = 0.0
    floor: int = 0
    size_sqft: float = 0.0
    furnished: bool = False
    parking: bool = False
    status: str = ApartmentStatus.AVAILABLE.value
    description: str = ""
    location_city: str = ""
    location_address: str = ""


@dataclass
class Tenant:
    id: Optional[int] = None
    ni_number: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    email: str = ""
    occupation: str = ""
    date_of_birth: Optional[str] = None
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    reference1_name: str = ""
    reference1_phone: str = ""
    reference1_email: str = ""
    reference2_name: str = ""
    reference2_phone: str = ""
    reference2_email: str = ""
    notes: str = ""
    created_at: Optional[str] = None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@dataclass
class Lease:
    id: Optional[int] = None
    tenant_id: Optional[int] = None
    apartment_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    monthly_rent: float = 0.0
    deposit_amount: float = 0.0
    status: str = LeaseStatus.ACTIVE.value
    early_termination_requested: bool = False
    early_termination_date: Optional[str] = None
    notice_given_date: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    # Joined fields
    tenant_name: str = ""
    tenant_email: str = ""
    tenant_phone: str = ""
    apartment_unit: str = ""
    apartment_type: str = ""
    location_city: str = ""
    location_address: str = ""


@dataclass
class Payment:
    id: Optional[int] = None
    lease_id: Optional[int] = None
    amount_due: float = 0.0
    amount_paid: float = 0.0
    due_date: Optional[str] = None
    paid_date: Optional[str] = None
    status: str = PaymentStatus.PENDING.value
    payment_method: str = ""
    reference_number: str = ""
    notes: str = ""
    created_at: Optional[str] = None


@dataclass
class MaintenanceRequest:
    id: Optional[int] = None
    lease_id: Optional[int] = None
    apartment_id: Optional[int] = None
    tenant_id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: str = ""
    priority: str = MaintenancePriority.MEDIUM.value
    status: str = MaintenanceStatus.OPEN.value
    reported_date: Optional[str] = None
    scheduled_date: Optional[str] = None
    resolved_date: Optional[str] = None
    resolution_notes: str = ""
    cost: float = 0.0
    time_taken_hours: float = 0.0
    assigned_staff_id: Optional[int] = None
    created_at: Optional[str] = None
    # Joined fields
    tenant_name: str = ""
    apartment_unit: str = ""
    location_city: str = ""


@dataclass
class Complaint:
    id: Optional[int] = None
    lease_id: Optional[int] = None
    tenant_id: Optional[int] = None
    apartment_id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: str = ""
    status: str = ComplaintStatus.OPEN.value
    reported_date: Optional[str] = None
    resolved_date: Optional[str] = None
    resolution_notes: str = ""
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    # Joined fields
    tenant_name: str = ""
    apartment_unit: str = ""


@dataclass
class Staff:
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    first_name: str = ""
    last_name: str = ""
    role: str = ""
    email: str = ""
    phone: str = ""
    location_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[str] = None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"