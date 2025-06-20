"""
Data models for the delivery system.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Union

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

@dataclass
class DeliveryAsset:
    """Base class for a delivery asset with common attributes."""
    asset_id: str
    name: str
    status: AssetStatus = AssetStatus.IDLE
    current_location: Union[str, int] = "clubhouse"
    destination: Union[str, int, None] = None  # Where the asset is heading
    current_orders: List = field(default_factory=list)

@dataclass
class BeverageCart(DeliveryAsset):
    """Represents a beverage cart that is restricted to a specific loop."""
    loop: str = "front_9"  # "front_9" or "back_9"

@dataclass
class DeliveryStaff(DeliveryAsset):
    """Represents a delivery staff member who can roam the entire course."""
    pass

@dataclass
class OrderItem:
    """Represents an item in an order."""
    name: str
    quantity: int = 1
    complexity: str = 'medium'  # 'simple', 'medium', or 'complex'
    price: float = 0.0

@dataclass
class Order:
    """Represents a customer order."""
    order_id: str
    hole_number: int
    status: OrderStatus = OrderStatus.PENDING
    assigned_to: Optional[DeliveryAsset] = None
    items: List[OrderItem] = field(default_factory=list)
    value: float = 0.0
    time_of_day: Optional[str] = None  # 'morning', 'noon', 'afternoon' 