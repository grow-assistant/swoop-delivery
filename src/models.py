"""
Data models for the delivery system.
"""
from enum import Enum
from dataclasses import dataclass, field

class AssetStatus(Enum):
    """Represents the detailed status of a delivery asset."""
    IDLE = "idle"  # Asset is available and not assigned to any order
    EN_ROUTE_TO_PICKUP = "en_route_to_pickup"  # Asset is heading to clubhouse to pick up order
    WAITING_FOR_ORDER = "waiting_for_order"  # Asset has arrived at pickup but order not ready
    EN_ROUTE_TO_DROPOFF = "en_route_to_dropoff"  # Asset is delivering order to customer
    INACTIVE = "inactive"  # Asset is off duty
    
    # Legacy statuses for backward compatibility
    AVAILABLE = "idle"  # Maps to IDLE
    ON_DELIVERY = "en_route_to_dropoff"  # Maps to EN_ROUTE_TO_DROPOFF

class OrderStatus(Enum):
    """Represents the status of an order."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DeliveryAsset:
    """Base class for a delivery asset. Not a dataclass itself."""
    pass

@dataclass
class BeverageCart(DeliveryAsset):
    """Represents a beverage cart that is restricted to a specific loop."""
    asset_id: str
    name: str
    loop: str  # "front_9" or "back_9"
    status: AssetStatus = AssetStatus.IDLE
    current_location: any = "clubhouse"
    destination: any = None  # Where the asset is heading (hole number or "clubhouse")
    current_orders: list = field(default_factory=list)

@dataclass
class DeliveryStaff(DeliveryAsset):
    """Represents a delivery staff member who can roam the entire course."""
    asset_id: str
    name: str
    status: AssetStatus = AssetStatus.IDLE
    current_location: any = "clubhouse"
    destination: any = None  # Where the asset is heading (hole number or "clubhouse")
    current_orders: list = field(default_factory=list)

@dataclass
class Order:
    """Represents a customer order."""
    order_id: str
    hole_number: int
    status: OrderStatus = OrderStatus.PENDING
    assigned_to: DeliveryAsset = None 